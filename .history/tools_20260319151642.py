"""
Tools Module
Implements various tools that agents can use:
- Email Generator
- Resume Screener
- Document Summarizer
- FAQ Responder
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from abc import ABC, abstractmethod


@dataclass
class ToolResult:
    """Result from a tool execution."""
    success: bool
    output: str
    data: Optional[Dict] = None
    error: Optional[str] = None


class BaseTool(ABC):
    """Base class for all agent tools."""
    
    name: str = "base_tool"
    description: str = "Base tool"
    
    @abstractmethod
    def run(self, input_data: str, **kwargs) -> ToolResult:
        """Execute the tool."""
        pass
    
    def get_schema(self) -> Dict:
        """Return tool schema for LangChain."""
        return {
            "name": self.name,
            "description": self.description
        }


class EmailGeneratorTool(BaseTool):
    """
    Generates professional emails based on context and requirements.
    """
    
    name = "email_generator"
    description = "Generate professional emails. Input: JSON with 'purpose', 'recipient', 'tone' (formal/casual), and 'key_points'"
    
    def __init__(self, llm):
        self.llm = llm
    
    def run(self, input_data: str, **kwargs) -> ToolResult:
        """
        Generate an email based on the input specifications.
        
        Args:
            input_data: Description of the email to generate
            
        Returns:
            ToolResult with the generated email
        """
        try:
            prompt = f"""Generate a professional email based on these requirements:

{input_data}

Please write a complete email with:
- Subject line
- Greeting
- Body
- Closing

Email:"""
            
            response = self.llm.invoke(prompt)
            
            return ToolResult(
                success=True,
                output=response,
                data={"type": "email"}
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=str(e)
            )


class ResumeScreenerTool(BaseTool):
    """
    Screens resumes against job requirements.
    """
    
    name = "resume_screener"
    description = "Screen resumes against job requirements. Input: Resume text and job requirements"
    
    def __init__(self, llm):
        self.llm = llm
    
    def run(self, input_data: str, **kwargs) -> ToolResult:
        """
        Screen a resume against job requirements.
        
        Args:
            input_data: Resume text and requirements
            
        Returns:
            ToolResult with screening analysis
        """
        try:
            job_requirements = kwargs.get("job_requirements", "")
            
            prompt = f"""As an HR specialist, analyze this resume against the job requirements.

Resume:
{input_data}

Job Requirements:
{job_requirements if job_requirements else "General professional position"}

Provide:
1. Match Score (0-100)
2. Key Qualifications Met
3. Missing Qualifications
4. Overall Recommendation (Recommended / Maybe / Not Recommended)
5. Brief Summary

Analysis:"""
            
            response = self.llm.invoke(prompt)
            
            return ToolResult(
                success=True,
                output=response,
                data={"type": "resume_screening"}
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=str(e)
            )


class DocumentSummarizerTool(BaseTool):
    """
    Summarizes documents and extracts key information.
    """
    
    name = "document_summarizer"
    description = "Summarize documents and extract key points. Input: Document text"
    
    def __init__(self, llm):
        self.llm = llm
    
    def run(self, input_data: str, **kwargs) -> ToolResult:
        """
        Summarize a document.
        
        Args:
            input_data: Document text to summarize
            
        Returns:
            ToolResult with summary
        """
        try:
            summary_type = kwargs.get("summary_type", "comprehensive")
            max_length = kwargs.get("max_length", "medium")
            
            prompt = f"""Summarize the following document.
Summary type: {summary_type}
Length: {max_length}

Document:
{input_data}

Provide:
1. Executive Summary (2-3 sentences)
2. Key Points (bullet points)
3. Main Topics Covered
4. Any Action Items or Conclusions

Summary:"""
            
            response = self.llm.invoke(prompt)
            
            return ToolResult(
                success=True,
                output=response,
                data={"type": "summary"}
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=str(e)
            )


class FAQResponderTool(BaseTool):
    """
    Answers questions based on FAQ knowledge base.
    """
    
    name = "faq_responder"
    description = "Answer questions using the knowledge base. Input: User question"
    
    def __init__(self, llm, rag_system=None):
        self.llm = llm
        self.rag_system = rag_system
    
    def run(self, input_data: str, **kwargs) -> ToolResult:
        """
        Answer a question using the knowledge base.
        
        Args:
            input_data: User's question
            
        Returns:
            ToolResult with answer
        """
        try:
            agent_id = kwargs.get("agent_id")
            context = ""
            
            # Get context from RAG if available
            if self.rag_system:
                context = self.rag_system.get_context(input_data, k=3, agent_id=agent_id)
            
            if context and context != "No relevant information found in the knowledge base.":
                prompt = f"""Answer the user's question based on the provided context.
If the answer is not in the context, say so clearly.

Context:
{context}

Question: {input_data}

Answer:"""
            else:
                prompt = f"""Answer this question to the best of your ability.
If you're not sure, be honest about it.

Question: {input_data}

Answer:"""
            
            response = self.llm.invoke(prompt)
            
            return ToolResult(
                success=True,
                output=response,
                data={
                    "type": "faq_answer",
                    "has_context": bool(context)
                }
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=str(e)
            )


class GeneralResponderTool(BaseTool):
    """
    General purpose responder for any task.
    """
    
    name = "general_responder"
    description = "Handle general queries and tasks. Input: User request"
    
    def __init__(self, llm):
        self.llm = llm
    
    def run(self, input_data: str, **kwargs) -> ToolResult:
        """
        Handle a general request.
        
        Args:
            input_data: User's request
            
        Returns:
            ToolResult with response
        """
        try:
            context = kwargs.get("context", "")
            
            prompt = f"""You are a helpful AI assistant. Please help with the following request.

{f"Context: {context}" if context else ""}

Request: {input_data}

Response:"""
            
            response = self.llm.invoke(prompt)
            
            return ToolResult(
                success=True,
                output=response,
                data={"type": "general"}
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=str(e)
            )


class ToolRegistry:
    """
    Registry for managing available tools.
    """
    
    def __init__(self, llm, rag_system=None):
        """
        Initialize the tool registry.
        
        Args:
            llm: LangChain LLM instance
            rag_system: Optional RAG system for knowledge-based tools
        """
        self.llm = llm
        self.rag_system = rag_system
        self.tools: Dict[str, BaseTool] = {}
        self._register_default_tools()
    
    def _register_default_tools(self):
        """Register all default tools."""
        self.register(EmailGeneratorTool(self.llm))
        self.register(ResumeScreenerTool(self.llm))
        self.register(DocumentSummarizerTool(self.llm))
        self.register(FAQResponderTool(self.llm, self.rag_system))
        self.register(GeneralResponderTool(self.llm))
    
    def register(self, tool: BaseTool):
        """Register a tool."""
        self.tools[tool.name] = tool
    
    def get(self, tool_name: str) -> Optional[BaseTool]:
        """Get a tool by name."""
        return self.tools.get(tool_name)
    
    def list_tools(self) -> List[Dict]:
        """List all available tools."""
        return [
            {"name": tool.name, "description": tool.description}
            for tool in self.tools.values()
        ]
    
    def run_tool(self, tool_name: str, input_data: str, **kwargs) -> ToolResult:
        """
        Run a specific tool.
        
        Args:
            tool_name: Name of the tool to run
            input_data: Input for the tool
            **kwargs: Additional arguments
            
        Returns:
            ToolResult from the tool
        """
        tool = self.get(tool_name)
        if not tool:
            return ToolResult(
                success=False,
                output="",
                error=f"Tool '{tool_name}' not found"
            )
        
        return tool.run(input_data, **kwargs)


def get_langchain_tools(tool_registry: ToolRegistry) -> List:
    """
    Convert tools to LangChain tool format.
    
    Args:
        tool_registry: The tool registry
        
    Returns:
        List of LangChain tools
    """
    from langchain.tools import Tool
    
    langchain_tools = []
    for tool_name, tool in tool_registry.tools.items():
        langchain_tools.append(
            Tool(
                name=tool.name,
                func=lambda x, t=tool: t.run(x).output,
                description=tool.description
            )
        )
    
    return langchain_tools
