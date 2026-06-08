"""
Agent Executor Module
Handles the execution of created agents.
Manages conversations, tool usage, and RAG queries.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass

# LangChain imports - updated for latest version
from langchain_classic.chains import ConversationChain, RetrievalQA
from langchain_classic.memory import ConversationBufferWindowMemory
from langchain_core.prompts import PromptTemplate
from langchain.agents import AgentExecutor, create_react_agent

# Local imports
from ollama_config import get_llm, get_embeddings
from memory_manager import MemoryManager
from rag_system import RAGSystem, RAGRetriever
from tools import ToolRegistry, get_langchain_tools
from guardrails import Guardrails, create_safe_prompt


@dataclass
class ExecutionResult:
    """Result from agent execution."""
    success: bool
    response: str
    tool_used: Optional[str] = None
    sources: Optional[List[str]] = None
    error: Optional[str] = None


class AgentExecutorWrapper:
    """
    Executes agent tasks with conversation memory and RAG support.
    """
    
    def __init__(self, agent_config: Dict, llm=None):
        """
        Initialize the executor with an agent configuration.
        
        Args:
            agent_config: Agent configuration dictionary
            llm: Optional LLM instance
        """
        self.config = agent_config
        self.agent_id = agent_config.get("agent_id", "default")
        self.agent_name = agent_config.get("name", "Assistant")
        self.system_prompt = agent_config.get("system_prompt", "You are a helpful assistant.")
        self.tools_list = agent_config.get("tools", [])
        self.uses_rag = agent_config.get("uses_rag", False)
        self.temperature = agent_config.get("temperature", 0.7)
        
        # Initialize components
        self.llm = llm or get_llm(temperature=self.temperature)
        self.memory_manager = MemoryManager()
        self.guardrails = Guardrails()
        
        # Initialize RAG if needed
        self.rag_system = None
        if self.uses_rag:
            embeddings = get_embeddings()
            self.rag_system = RAGSystem(embeddings, collection_name=f"agent_{self.agent_id}")
        
        # Initialize tool registry
        self.tool_registry = ToolRegistry(self.llm, self.rag_system)
        
        # Conversation memory (in-memory for quick access)
        self.conversation_memory = ConversationBufferWindowMemory(
            k=10,  # Remember last 10 exchanges
            return_messages=True
        )
        
        # Load conversation history from persistent storage
        self._load_conversation_history()
    
    def _load_conversation_history(self):
        """Load conversation history from database."""
        history = self.memory_manager.get_conversation_history(self.agent_id, limit=10)
        for msg in history:
            if msg.role == "user":
                self.conversation_memory.chat_memory.add_user_message(msg.content)
            else:
                self.conversation_memory.chat_memory.add_ai_message(msg.content)
    
    def execute(self, user_input: str) -> ExecutionResult:
        """
        Execute a user request.
        
        Args:
            user_input: The user's message
            
        Returns:
            ExecutionResult with the response
        """
        # Step 1: Safety check
        safety_check = self.guardrails.check_input(user_input)
        if not safety_check.is_safe:
            return ExecutionResult(
                success=False,
                response="I cannot process this request due to safety concerns.",
                error="; ".join(safety_check.violations)
            )
        
        # Step 2: Get context from RAG if applicable
        rag_context = ""
        sources = []
        if self.uses_rag and self.rag_system:
            rag_context = self.rag_system.get_context(user_input, k=3, agent_id=self.agent_id)
            if rag_context and "No relevant information" not in rag_context:
                results = self.rag_system.query(user_input, k=3, agent_id=self.agent_id)
                sources = [r.source for r in results]
        
        # Step 3: Get conversation context
        conv_context = self.memory_manager.get_conversation_context(self.agent_id, num_messages=5)
        
        # Step 4: Determine which tool to use
        tool_to_use = self._select_tool(user_input)
        
        # Step 5: Execute with appropriate method
        try:
            if tool_to_use and tool_to_use != "general_responder":
                response = self._execute_with_tool(user_input, tool_to_use, rag_context)
            else:
                response = self._execute_conversation(user_input, rag_context, conv_context)
            
            # Step 6: Safety check on output
            output_check = self.guardrails.check_output(response)
            if output_check.sanitized_content:
                response = output_check.sanitized_content
            
            # Step 7: Save to memory
            self._save_interaction(user_input, response, tool_to_use)
            
            return ExecutionResult(
                success=True,
                response=response,
                tool_used=tool_to_use,
                sources=sources if sources else None
            )
            
        except Exception as e:
            return ExecutionResult(
                success=False,
                response="I encountered an error processing your request.",
                error=str(e)
            )
    
    def _select_tool(self, user_input: str) -> Optional[str]:
        """Select the most appropriate tool for the request."""
        input_lower = user_input.lower()
        
        # Check available tools against input
        tool_keywords = {
            "resume_screener": ["resume", "cv", "candidate", "screen", "hire"],
            "email_generator": ["email", "compose", "draft", "write email", "message"],
            "document_summarizer": ["summarize", "summary", "key points", "analyze document"],
            "faq_responder": ["question", "what is", "how to", "explain", "tell me"]
        }
        
        for tool in self.tools_list:
            if tool in tool_keywords:
                if any(kw in input_lower for kw in tool_keywords[tool]):
                    return tool
        
        # Default to faq_responder if RAG is enabled and it's in tools
        if self.uses_rag and "faq_responder" in self.tools_list:
            return "faq_responder"
        
        return "general_responder"
    
    def _execute_with_tool(self, user_input: str, tool_name: str, 
                           context: str = "") -> str:
        """Execute using a specific tool."""
        result = self.tool_registry.run_tool(
            tool_name,
            user_input,
            context=context,
            agent_id=self.agent_id
        )
        
        if result.success:
            return result.output
        else:
            # Fallback to conversation
            return self._execute_conversation(user_input, context, "")
    
    def _execute_conversation(self, user_input: str, rag_context: str,
                             conv_context: str) -> str:
        """Execute as a conversation."""
        # Build the prompt
        prompt_parts = [self.system_prompt]
        
        if rag_context and "No relevant information" not in rag_context:
            prompt_parts.append(f"\nRelevant Information:\n{rag_context}")
        
        if conv_context:
            prompt_parts.append(f"\nPrevious Conversation:\n{conv_context}")
        
        prompt_parts.append(f"\nUser: {user_input}\n\nAssistant:")
        
        full_prompt = "\n".join(prompt_parts)
        
        # Get response from LLM
        response = self.llm.invoke(full_prompt)
        
        return response.strip()
    
    def _save_interaction(self, user_input: str, response: str, 
                         tool_used: Optional[str]):
        """Save the interaction to persistent memory."""
        # Save messages
        self.memory_manager.save_message(self.agent_id, "user", user_input)
        self.memory_manager.save_message(
            self.agent_id, 
            "assistant", 
            response,
            metadata={"tool_used": tool_used} if tool_used else {}
        )
        
        # Update agent activity
        self.memory_manager.update_agent_activity(self.agent_id)
        
        # Log action if tool was used
        if tool_used:
            self.memory_manager.log_action(
                self.agent_id,
                action_type=tool_used,
                action_data={"input_preview": user_input[:100]},
                result="success"
            )
        
        # Update conversation memory
        self.conversation_memory.chat_memory.add_user_message(user_input)
        self.conversation_memory.chat_memory.add_ai_message(response)
    
    def add_document(self, file_path: str) -> Dict:
        """
        Add a document to the agent's knowledge base.
        
        Args:
            file_path: Path to the document
            
        Returns:
            Dict with result
        """
        if not self.uses_rag or not self.rag_system:
            return {"success": False, "error": "This agent doesn't use RAG"}
        
        try:
            result = self.rag_system.add_document(file_path, self.agent_id)
            
            # Log to memory
            self.memory_manager.save_knowledge_source(
                self.agent_id,
                result["file_name"],
                file_path.split(".")[-1],
                file_path,
                result["chunks_created"]
            )
            
            return {"success": True, **result}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def add_text_knowledge(self, text: str, source: str = "user_input") -> Dict:
        """Add text directly to knowledge base."""
        if not self.uses_rag or not self.rag_system:
            return {"success": False, "error": "This agent doesn't use RAG"}
        
        try:
            result = self.rag_system.add_text(text, source, self.agent_id)
            return {"success": True, **result}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_stats(self) -> Dict:
        """Get agent statistics."""
        return self.memory_manager.get_agent_stats(self.agent_id)
    
    def get_history(self, limit: int = 20) -> List[Dict]:
        """Get conversation history."""
        history = self.memory_manager.get_conversation_history(self.agent_id, limit)
        return [
            {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp
            }
            for msg in history
        ]
    
    def clear_history(self):
        """Clear conversation history."""
        self.memory_manager.clear_conversation(self.agent_id)
        self.conversation_memory.clear()


class MultiAgentOrchestrator:
    """
    Orchestrates multiple agents for complex tasks.
    """
    
    def __init__(self):
        """Initialize the orchestrator."""
        self.agents: Dict[str, AgentExecutorWrapper] = {}
        self.llm = get_llm()
    
    def register_agent(self, agent_config: Dict):
        """Register an agent with the orchestrator."""
        agent_id = agent_config.get("agent_id")
        self.agents[agent_id] = AgentExecutorWrapper(agent_config, self.llm)
    
    def route_request(self, user_input: str) -> str:
        """
        Route a request to the most appropriate agent.
        
        Args:
            user_input: User's request
            
        Returns:
            Agent ID of the best match
        """
        if not self.agents:
            return None
        
        # Simple keyword-based routing
        input_lower = user_input.lower()
        
        for agent_id, agent in self.agents.items():
            agent_type = agent.config.get("agent_type", "")
            
            # Check for type matches
            type_keywords = {
                "hr_assistant": ["resume", "candidate", "hire", "hr"],
                "email_assistant": ["email", "compose", "draft"],
                "document_analyst": ["document", "summarize", "analyze"],
                "faq_chatbot": ["question", "help", "how", "what"]
            }
            
            if agent_type in type_keywords:
                if any(kw in input_lower for kw in type_keywords[agent_type]):
                    return agent_id
        
        # Return first agent as default
        return list(self.agents.keys())[0]
    
    def execute(self, user_input: str, agent_id: str = None) -> ExecutionResult:
        """
        Execute a request with automatic or specified routing.
        
        Args:
            user_input: User's request
            agent_id: Optional specific agent to use
            
        Returns:
            ExecutionResult
        """
        if not self.agents:
            return ExecutionResult(
                success=False,
                response="No agents available",
                error="No agents registered"
            )
        
        # Route to agent
        target_id = agent_id or self.route_request(user_input)
        
        if target_id not in self.agents:
            return ExecutionResult(
                success=False,
                response="Agent not found",
                error=f"Agent '{target_id}' not registered"
            )
        
        return self.agents[target_id].execute(user_input)
