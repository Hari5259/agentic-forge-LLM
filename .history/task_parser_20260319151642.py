"""
Task Parser Module
Analyzes user's plain English request and determines:
- Agent type needed
- Required tools
- Workflow steps
- Clarification questions if needed
"""

import json
import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
from enum import Enum


class AgentType(Enum):
    """Predefined agent types the system can create."""
    HR_ASSISTANT = "hr_assistant"
    EMAIL_ASSISTANT = "email_assistant"
    DOCUMENT_ANALYST = "document_analyst"
    FAQ_CHATBOT = "faq_chatbot"
    RESEARCH_ASSISTANT = "research_assistant"
    GENERAL_ASSISTANT = "general_assistant"


@dataclass
class ParsedTask:
    """Structured representation of a parsed user request."""
    agent_type: str
    agent_name: str
    description: str
    required_tools: List[str]
    workflow_steps: List[str]
    needs_rag: bool
    needs_clarification: bool
    clarification_questions: List[str]
    confidence_score: float


# Keywords mapping to agent types and tools
AGENT_KEYWORDS = {
    "hr_assistant": ["hr", "resume", "hiring", "candidate", "recruit", "screen", "interview", "job"],
    "email_assistant": ["email", "mail", "compose", "draft", "reply", "send", "message"],
    "document_analyst": ["document", "analyze", "summarize", "summary", "extract", "report", "pdf"],
    "faq_chatbot": ["faq", "question", "answer", "support", "help", "chatbot", "customer"],
    "research_assistant": ["research", "find", "search", "investigate", "gather", "information"],
}

TOOL_KEYWORDS = {
    "resume_screener": ["resume", "cv", "candidate", "screening", "qualification", "hire"],
    "email_generator": ["email", "compose", "draft", "write", "message", "reply"],
    "document_summarizer": ["summarize", "summary", "extract", "key points", "analyze"],
    "faq_responder": ["faq", "answer", "question", "respond", "help"],
    "web_searcher": ["search", "find", "look up", "research", "web"],
}


class TaskParser:
    """
    Parses user requests using both rule-based matching and LLM analysis.
    Determines what kind of agent to create and what tools it needs.
    """
    
    def __init__(self, llm=None):
        """
        Initialize the parser.
        
        Args:
            llm: Optional LangChain LLM for advanced parsing
        """
        self.llm = llm
    
    def parse(self, user_request: str) -> ParsedTask:
        """
        Parse a user's plain English request into a structured task.
        
        Args:
            user_request: The user's description of what they want
            
        Returns:
            ParsedTask with all extracted information
        """
        # Step 1: Rule-based quick analysis
        agent_type = self._detect_agent_type(user_request)
        required_tools = self._detect_required_tools(user_request)
        
        # Step 2: Check if request is too vague
        needs_clarification, questions = self._check_clarity(user_request, agent_type)
        
        # Step 3: Generate workflow steps
        workflow_steps = self._generate_workflow(agent_type, required_tools)
        
        # Step 4: Determine if RAG is needed
        needs_rag = self._needs_knowledge_base(user_request)
        
        # Step 5: Generate agent name
        agent_name = self._generate_agent_name(user_request, agent_type)
        
        # Step 6: Calculate confidence score
        confidence = self._calculate_confidence(user_request, agent_type, required_tools)
        
        return ParsedTask(
            agent_type=agent_type,
            agent_name=agent_name,
            description=user_request,
            required_tools=required_tools,
            workflow_steps=workflow_steps,
            needs_rag=needs_rag,
            needs_clarification=needs_clarification,
            clarification_questions=questions,
            confidence_score=confidence
        )
    
    def _detect_agent_type(self, request: str) -> str:
        """Detect agent type from keywords in the request."""
        request_lower = request.lower()
        scores = {}
        
        for agent_type, keywords in AGENT_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in request_lower)
            scores[agent_type] = score
        
        best_match = max(scores, key=scores.get)
        if scores[best_match] > 0:
            return best_match
        return "general_assistant"
    
    def _detect_required_tools(self, request: str) -> List[str]:
        """Detect which tools are needed based on the request."""
        request_lower = request.lower()
        tools = []
        
        for tool, keywords in TOOL_KEYWORDS.items():
            if any(kw in request_lower for kw in keywords):
                tools.append(tool)
        
        # Always include at least one tool
        if not tools:
            tools = ["general_responder"]
        
        return tools
    
    def _check_clarity(self, request: str, agent_type: str) -> Tuple[bool, List[str]]:
        """
        Check if the request is clear enough or needs clarification.
        
        Returns:
            Tuple of (needs_clarification, list_of_questions)
        """
        questions = []
        
        # Check for minimum length
        if len(request.split()) < 5:
            questions.append("Could you provide more details about what this agent should do?")
        
        # Check for specific clarifications based on agent type
        if agent_type == "hr_assistant":
            if "criteria" not in request.lower() and "requirement" not in request.lower():
                questions.append("What criteria should be used to evaluate candidates?")
        
        elif agent_type == "email_assistant":
            if "tone" not in request.lower() and "style" not in request.lower():
                questions.append("What tone should the emails have? (formal/casual/professional)")
        
        elif agent_type == "document_analyst":
            if "type" not in request.lower() and "format" not in request.lower():
                questions.append("What type of documents will this agent analyze?")
        
        return len(questions) > 0, questions
    
    def _generate_workflow(self, agent_type: str, tools: List[str]) -> List[str]:
        """Generate workflow steps for the agent."""
        workflows = {
            "hr_assistant": [
                "1. Receive resume/candidate information",
                "2. Extract key qualifications and experience",
                "3. Compare against job requirements",
                "4. Score and rank candidates",
                "5. Generate summary report"
            ],
            "email_assistant": [
                "1. Understand email context and purpose",
                "2. Gather necessary information",
                "3. Draft email content",
                "4. Review for tone and clarity",
                "5. Provide final email for review"
            ],
            "document_analyst": [
                "1. Receive and parse document",
                "2. Extract key information",
                "3. Analyze content structure",
                "4. Generate summary/insights",
                "5. Present findings"
            ],
            "faq_chatbot": [
                "1. Receive user question",
                "2. Search knowledge base",
                "3. Find relevant answers",
                "4. Formulate response",
                "5. Provide answer with sources"
            ],
            "research_assistant": [
                "1. Understand research query",
                "2. Search available sources",
                "3. Gather relevant information",
                "4. Synthesize findings",
                "5. Present research summary"
            ],
            "general_assistant": [
                "1. Understand user request",
                "2. Determine required actions",
                "3. Execute task",
                "4. Provide results"
            ]
        }
        return workflows.get(agent_type, workflows["general_assistant"])
    
    def _needs_knowledge_base(self, request: str) -> bool:
        """Determine if the agent needs RAG/knowledge base."""
        rag_keywords = [
            "document", "file", "pdf", "knowledge", "database",
            "search", "find", "retrieve", "information", "data",
            "resume", "report", "faq", "upload"
        ]
        return any(kw in request.lower() for kw in rag_keywords)
    
    def _generate_agent_name(self, request: str, agent_type: str) -> str:
        """Generate a friendly name for the agent."""
        type_names = {
            "hr_assistant": "HR Helper",
            "email_assistant": "Email Composer",
            "document_analyst": "Doc Analyzer",
            "faq_chatbot": "FAQ Bot",
            "research_assistant": "Research Buddy",
            "general_assistant": "General Assistant"
        }
        
        # Try to extract a custom name from the request
        name_patterns = [
            r"create (?:a |an )?([a-zA-Z\s]+?) (?:that|which|to)",
            r"build (?:a |an )?([a-zA-Z\s]+?) (?:that|which|to)",
            r"make (?:a |an )?([a-zA-Z\s]+?) (?:that|which|to)"
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, request.lower())
            if match:
                custom_name = match.group(1).strip().title()
                if len(custom_name) > 3 and len(custom_name) < 30:
                    return custom_name
        
        return type_names.get(agent_type, "Custom Agent")
    
    def _calculate_confidence(self, request: str, agent_type: str, tools: List[str]) -> float:
        """Calculate confidence score for the parsing."""
        score = 0.5  # Base score
        
        # Add points for clear agent type match
        if agent_type != "general_assistant":
            score += 0.2
        
        # Add points for specific tools detected
        score += min(0.2, len(tools) * 0.1)
        
        # Add points for request length (more detail = more confidence)
        word_count = len(request.split())
        if word_count >= 10:
            score += 0.1
        
        return min(1.0, score)
    
    def parse_with_llm(self, user_request: str) -> ParsedTask:
        """
        Use LLM for advanced parsing when available.
        Falls back to rule-based parsing if LLM fails.
        """
        if not self.llm:
            return self.parse(user_request)
        
        try:
            prompt = f"""Analyze this request for creating an AI agent and respond in JSON format:

Request: "{user_request}"

Respond with ONLY valid JSON:
{{
    "agent_type": "hr_assistant|email_assistant|document_analyst|faq_chatbot|research_assistant|general_assistant",
    "agent_name": "A short friendly name for this agent",
    "required_tools": ["list", "of", "tools"],
    "needs_rag": true/false,
    "needs_clarification": true/false,
    "clarification_questions": ["questions if clarification needed"],
    "workflow_steps": ["step 1", "step 2", "..."]
}}

Available tools: resume_screener, email_generator, document_summarizer, faq_responder"""

            response = self.llm.invoke(prompt)
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                return ParsedTask(
                    agent_type=data.get("agent_type", "general_assistant"),
                    agent_name=data.get("agent_name", "Custom Agent"),
                    description=user_request,
                    required_tools=data.get("required_tools", ["general_responder"]),
                    workflow_steps=data.get("workflow_steps", []),
                    needs_rag=data.get("needs_rag", False),
                    needs_clarification=data.get("needs_clarification", False),
                    clarification_questions=data.get("clarification_questions", []),
                    confidence_score=0.85
                )
        except Exception as e:
            print(f"LLM parsing failed: {e}, falling back to rule-based parsing")
        
        return self.parse(user_request)
    
    def to_dict(self, parsed: ParsedTask) -> Dict:
        """Convert ParsedTask to dictionary."""
        return asdict(parsed)
