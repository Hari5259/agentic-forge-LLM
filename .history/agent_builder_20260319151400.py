"""
Agent Builder Module
Automatically creates AI agents based on user descriptions.
Parses requirements, selects tools, and configures workflows.
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

# Import local modules
from task_parser import TaskParser, ParsedTask
from memory_manager import MemoryManager, AgentState
from ollama_config import get_llm, get_embeddings
from rag_system import RAGSystem
from tools import ToolRegistry
from guardrails import Guardrails


@dataclass
class AgentConfig:
    """Complete configuration for an agent."""
    agent_id: str
    name: str
    description: str
    agent_type: str
    tools: List[str]
    workflow: List[str]
    system_prompt: str
    uses_rag: bool
    temperature: float = 0.7
    created_at: str = ""


class AgentBuilder:
    """
    Builds AI agents from plain English descriptions.
    Handles the complete agent creation workflow.
    """
    
    def __init__(self, llm=None, memory_manager: MemoryManager = None):
        """
        Initialize the agent builder.
        
        Args:
            llm: LangChain LLM instance
            memory_manager: Memory manager for persistence
        """
        self.llm = llm or get_llm()
        self.memory_manager = memory_manager or MemoryManager()
        self.task_parser = TaskParser(self.llm)
        self.guardrails = Guardrails()
    
    def build_from_description(self, user_description: str) -> Dict:
        """
        Build an agent from a plain English description.
        
        Args:
            user_description: User's description of what they want
            
        Returns:
            Dict with agent config and any clarification questions
        """
        # Step 1: Safety check on input
        safety_check = self.guardrails.check_input(user_description)
        if not safety_check.is_safe:
            return {
                "success": False,
                "error": "Request blocked for safety reasons",
                "violations": safety_check.violations
            }
        
        # Step 2: Parse the request
        parsed = self.task_parser.parse_with_llm(user_description)
        
        # Step 3: Check if clarification is needed
        if parsed.needs_clarification:
            return {
                "success": True,
                "needs_clarification": True,
                "questions": parsed.clarification_questions,
                "partial_config": self._create_partial_config(parsed)
            }
        
        # Step 4: Build the complete agent configuration
        agent_config = self._build_agent_config(parsed)
        
        # Step 5: Save to memory
        self._save_agent(agent_config)
        
        return {
            "success": True,
            "needs_clarification": False,
            "agent_config": asdict(agent_config),
            "message": f"Agent '{agent_config.name}' created successfully!"
        }
    
    def build_with_answers(self, user_description: str, 
                           answers: Dict[str, str]) -> Dict:
        """
        Build agent after receiving clarification answers.
        
        Args:
            user_description: Original description
            answers: Answers to clarification questions
            
        Returns:
            Dict with agent config
        """
        # Enhance description with answers
        enhanced_description = user_description
        for question, answer in answers.items():
            enhanced_description += f"\n{question}: {answer}"
        
        # Parse again with enhanced description
        parsed = self.task_parser.parse_with_llm(enhanced_description)
        
        # Force no more clarification needed
        parsed.needs_clarification = False
        
        # Build and save
        agent_config = self._build_agent_config(parsed)
        self._save_agent(agent_config)
        
        return {
            "success": True,
            "agent_config": asdict(agent_config),
            "message": f"Agent '{agent_config.name}' created successfully!"
        }
    
    def _build_agent_config(self, parsed: ParsedTask) -> AgentConfig:
        """
        Build complete agent configuration from parsed task.
        
        Args:
            parsed: ParsedTask from the parser
            
        Returns:
            Complete AgentConfig
        """
        agent_id = str(uuid.uuid4())[:8]
        
        # Generate system prompt
        system_prompt = self._generate_system_prompt(parsed)
        
        return AgentConfig(
            agent_id=agent_id,
            name=parsed.agent_name,
            description=parsed.description,
            agent_type=parsed.agent_type,
            tools=parsed.required_tools,
            workflow=parsed.workflow_steps,
            system_prompt=system_prompt,
            uses_rag=parsed.needs_rag,
            temperature=0.7 if parsed.agent_type in ["email_assistant", "research_assistant"] else 0.3,
            created_at=datetime.now().isoformat()
        )
    
    def _generate_system_prompt(self, parsed: ParsedTask) -> str:
        """Generate a system prompt for the agent."""
        
        base_prompts = {
            "hr_assistant": """You are an expert HR assistant specialized in resume screening and candidate evaluation.
Your role is to:
- Analyze resumes and CVs objectively
- Compare candidates against job requirements
- Identify key qualifications and experience
- Provide fair and unbiased assessments
- Recommend top candidates with clear reasoning

Always be professional, thorough, and fair in your evaluations.""",
            
            "email_assistant": """You are a professional email composer assistant.
Your role is to:
- Draft clear, professional emails
- Match the appropriate tone (formal, casual, professional)
- Structure emails effectively
- Ensure proper grammar and etiquette
- Adapt to various business contexts

Always proofread and suggest improvements when needed.""",
            
            "document_analyst": """You are a document analysis expert.
Your role is to:
- Extract key information from documents
- Summarize content accurately
- Identify main themes and topics
- Highlight important points
- Answer questions about document content

Always cite sources and be precise in your analysis.""",
            
            "faq_chatbot": """You are a helpful FAQ assistant.
Your role is to:
- Answer questions accurately using available information
- Be friendly and helpful
- Admit when you don't know something
- Suggest related topics when appropriate
- Provide concise but complete answers

Always prioritize accuracy over speculation.""",
            
            "research_assistant": """You are a research assistant.
Your role is to:
- Gather and synthesize information
- Present findings clearly
- Cite sources when available
- Identify gaps in knowledge
- Suggest next steps for research

Always be thorough and objective in your research.""",
            
            "general_assistant": """You are a helpful AI assistant.
Your role is to:
- Help with various tasks as requested
- Be clear and concise
- Ask for clarification when needed
- Provide accurate information
- Be honest about limitations

Always strive to be helpful, harmless, and honest."""
        }
        
        base = base_prompts.get(parsed.agent_type, base_prompts["general_assistant"])
        
        # Add task-specific context
        if parsed.description:
            base += f"\n\nSpecific task: {parsed.description}"
        
        # Add tool information
        if parsed.required_tools:
            tools_str = ", ".join(parsed.required_tools)
            base += f"\n\nAvailable tools: {tools_str}"
        
        return base
    
    def _create_partial_config(self, parsed: ParsedTask) -> Dict:
        """Create a partial config for clarification."""
        return {
            "agent_type": parsed.agent_type,
            "suggested_name": parsed.agent_name,
            "suggested_tools": parsed.required_tools,
            "confidence": parsed.confidence_score
        }
    
    def _save_agent(self, config: AgentConfig):
        """Save agent to persistent storage."""
        agent_state = AgentState(
            agent_id=config.agent_id,
            agent_name=config.name,
            agent_type=config.agent_type,
            config=asdict(config),
            created_at=config.created_at,
            last_active=config.created_at,
            is_active=True
        )
        self.memory_manager.save_agent(agent_state)
    
    def get_agent(self, agent_id: str) -> Optional[AgentConfig]:
        """Retrieve an agent by ID."""
        agent_state = self.memory_manager.get_agent(agent_id)
        if agent_state and agent_state.config:
            return AgentConfig(**agent_state.config)
        return None
    
    def list_agents(self) -> List[Dict]:
        """List all available agents."""
        agents = self.memory_manager.list_agents()
        return [
            {
                "agent_id": a.agent_id,
                "name": a.agent_name,
                "type": a.agent_type,
                "created": a.created_at,
                "last_active": a.last_active
            }
            for a in agents
        ]
    
    def delete_agent(self, agent_id: str):
        """Delete an agent."""
        self.memory_manager.delete_agent(agent_id)
    
    def suggest_agent(self, user_actions: List[str]) -> Optional[Dict]:
        """
        Suggest creating an agent based on repetitive actions.
        
        Args:
            user_actions: List of recent user actions/queries
            
        Returns:
            Suggestion dict if applicable, None otherwise
        """
        if len(user_actions) < 3:
            return None
        
        # Simple pattern detection
        # Check if similar actions are being repeated
        action_types = {}
        for action in user_actions:
            action_lower = action.lower()
            for agent_type, keywords in self.task_parser.AGENT_KEYWORDS.items():
                if any(kw in action_lower for kw in keywords):
                    action_types[agent_type] = action_types.get(agent_type, 0) + 1
        
        # If one type appears frequently
        for agent_type, count in action_types.items():
            if count >= 3:
                return {
                    "suggestion": f"I noticed you're frequently doing {agent_type.replace('_', ' ')} tasks. Would you like me to create a dedicated agent for this?",
                    "agent_type": agent_type
                }
        
        return None


class QuickAgentBuilder:
    """
    Simplified builder for common agent types.
    Provides templates for quick agent creation.
    """
    
    TEMPLATES = {
        "hr_screener": {
            "name": "HR Resume Screener",
            "description": "Screen resumes and rank candidates",
            "agent_type": "hr_assistant",
            "tools": ["resume_screener", "document_summarizer"],
            "uses_rag": True
        },
        "email_writer": {
            "name": "Professional Email Writer",
            "description": "Compose professional emails",
            "agent_type": "email_assistant",
            "tools": ["email_generator"],
            "uses_rag": False
        },
        "doc_analyzer": {
            "name": "Document Analyzer",
            "description": "Analyze and summarize documents",
            "agent_type": "document_analyst",
            "tools": ["document_summarizer", "faq_responder"],
            "uses_rag": True
        },
        "faq_bot": {
            "name": "FAQ Chatbot",
            "description": "Answer questions from knowledge base",
            "agent_type": "faq_chatbot",
            "tools": ["faq_responder"],
            "uses_rag": True
        }
    }
    
    @classmethod
    def list_templates(cls) -> List[Dict]:
        """List available templates."""
        return [
            {"id": k, **v} for k, v in cls.TEMPLATES.items()
        ]
    
    @classmethod
    def create_from_template(cls, template_id: str, 
                            builder: AgentBuilder) -> Dict:
        """Create an agent from a template."""
        if template_id not in cls.TEMPLATES:
            return {"success": False, "error": f"Template '{template_id}' not found"}
        
        template = cls.TEMPLATES[template_id]
        return builder.build_from_description(
            f"Create a {template['name']} that can {template['description']}"
        )
