"""
AgentForge - Streamlit UI
A No-Code Custom AI Agents Builder
Main application interface for creating and interacting with AI agents.
"""

import streamlit as st
import os
import sys
import tempfile
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import AgentForge modules
from ollama_config import check_ollama_connection, get_llm, get_embeddings, list_available_models
from agent_builder import AgentBuilder, QuickAgentBuilder
from agent_executor import AgentExecutorWrapper
from memory_manager import MemoryManager
from rag_system import RAGSystem


# ==================== Page Configuration ====================
st.set_page_config(
    page_title="AgentForge - AI Agent Builder",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== Custom CSS ====================
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0;
    }
    .sub-header {
        color: #666;
        font-size: 1.1rem;
        margin-top: 0;
    }
    .agent-card {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        border-left: 4px solid #667eea;
    }
    .chat-user {
        background: #e3f2fd;
        border-radius: 10px;
        padding: 10px;
        margin: 5px 0;
    }
    .chat-assistant {
        background: #f5f5f5;
        border-radius: 10px;
        padding: 10px;
        margin: 5px 0;
    }
    .status-online {
        color: #28a745;
        font-weight: bold;
    }
    .status-offline {
        color: #dc3545;
        font-weight: bold;
    }
    .tool-badge {
        background: #667eea;
        color: white;
        padding: 3px 8px;
        border-radius: 12px;
        font-size: 0.8rem;
        margin: 2px;
        display: inline-block;
    }
</style>
""", unsafe_allow_html=True)


# ==================== Session State Initialization ====================
def init_session_state():
    """Initialize session state variables."""
    if "agents" not in st.session_state:
        st.session_state.agents = {}
    if "current_agent" not in st.session_state:
        st.session_state.current_agent = None
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "builder" not in st.session_state:
        st.session_state.builder = None
    if "executor" not in st.session_state:
        st.session_state.executor = None
    if "clarification_pending" not in st.session_state:
        st.session_state.clarification_pending = False
    if "pending_description" not in st.session_state:
        st.session_state.pending_description = ""
    if "clarification_questions" not in st.session_state:
        st.session_state.clarification_questions = []


# ==================== Helper Functions ====================
@st.cache_resource
def get_builder():
    """Get or create AgentBuilder instance."""
    try:
        llm = get_llm()
        return AgentBuilder(llm)
    except Exception as e:
        st.error(f"Error initializing builder: {e}")
        return None


def load_existing_agents():
    """Load existing agents from database."""
    memory = MemoryManager()
    agents = memory.list_agents()
    for agent in agents:
        st.session_state.agents[agent.agent_id] = agent.config


def create_executor(agent_config: dict):
    """Create an executor for an agent."""
    try:
        return AgentExecutorWrapper(agent_config)
    except Exception as e:
        st.error(f"Error creating executor: {e}")
        return None


# ==================== UI Components ====================
def render_header():
    """Render the application header."""
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown('<p class="main-header">🤖 AgentForge</p>', unsafe_allow_html=True)
        st.markdown('<p class="sub-header">No-Code Custom AI Agents Builder</p>', unsafe_allow_html=True)
    
    with col2:
        # Check Ollama connection
        is_connected, message = check_ollama_connection()
        if is_connected:
            st.markdown('<p class="status-online">● Ollama Connected</p>', unsafe_allow_html=True)
        else:
            st.markdown('<p class="status-offline">● Ollama Offline</p>', unsafe_allow_html=True)
            st.warning("Start Ollama to use AgentForge")


def render_sidebar():
    """Render the sidebar with agent list and options."""
    with st.sidebar:
        st.header("📋 Your Agents")
        
        # Load agents button
        if st.button("🔄 Refresh Agents"):
            load_existing_agents()
            st.rerun()
        
        st.divider()
        
        # List existing agents
        if st.session_state.agents:
            for agent_id, config in st.session_state.agents.items():
                col1, col2 = st.columns([3, 1])
                with col1:
                    name = config.get("name", "Unnamed Agent") if isinstance(config, dict) else "Agent"
                    if st.button(f"🤖 {name}", key=f"select_{agent_id}", use_container_width=True):
                        st.session_state.current_agent = agent_id
                        st.session_state.chat_history = []
                        st.session_state.executor = create_executor(config)
                        st.rerun()
                with col2:
                    if st.button("🗑️", key=f"delete_{agent_id}"):
                        memory = MemoryManager()
                        memory.delete_agent(agent_id)
                        del st.session_state.agents[agent_id]
                        if st.session_state.current_agent == agent_id:
                            st.session_state.current_agent = None
                        st.rerun()
        else:
            st.info("No agents yet. Create your first agent!")
        
        st.divider()
        
        # Quick templates
        st.subheader("⚡ Quick Templates")
        templates = QuickAgentBuilder.list_templates()
        
        for template in templates:
            if st.button(f"📝 {template['name']}", key=f"template_{template['id']}", use_container_width=True):
                with st.spinner("Creating from template..."):
                    builder = get_builder()
                    if builder:
                        result = QuickAgentBuilder.create_from_template(template['id'], builder)
                        if result.get("success"):
                            config = result.get("agent_config", {})
                            st.session_state.agents[config['agent_id']] = config
                            st.session_state.current_agent = config['agent_id']
                            st.success(f"Created: {config['name']}")
                            st.rerun()


def render_agent_builder():
    """Render the agent building interface."""
    st.header("🛠️ Create New Agent")
    
    # Description input
    st.markdown("**Describe your agent in plain English:**")
    description = st.text_area(
        "What should your agent do?",
        placeholder="Example: Create an HR assistant that screens resumes and selects top candidates based on skills and experience.",
        height=100,
        key="agent_description"
    )
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if st.button("🚀 Create Agent", type="primary", use_container_width=True):
            if description:
                with st.spinner("Analyzing your request..."):
                    builder = get_builder()
                    if builder:
                        result = builder.build_from_description(description)
                        
                        if result.get("success"):
                            if result.get("needs_clarification"):
                                st.session_state.clarification_pending = True
                                st.session_state.pending_description = description
                                st.session_state.clarification_questions = result.get("questions", [])
                                st.rerun()
                            else:
                                config = result.get("agent_config", {})
                                st.session_state.agents[config['agent_id']] = config
                                st.session_state.current_agent = config['agent_id']
                                st.success(result.get("message", "Agent created!"))
                                st.rerun()
                        else:
                            st.error(result.get("error", "Failed to create agent"))
            else:
                st.warning("Please describe what you want the agent to do.")
    
    with col2:
        if st.button("🎲 Example Prompts", use_container_width=True):
            st.info("""
            **Try these examples:**
            - "Create an HR assistant that screens resumes and selects top candidates"
            - "Build an email composer that writes professional business emails"
            - "Make a document analyzer that summarizes PDF reports"
            - "Create a FAQ bot that answers questions about our products"
            """)
    
    # Handle clarification questions
    if st.session_state.clarification_pending:
        st.divider()
        st.subheader("🤔 Need More Details")
        
        answers = {}
        for i, question in enumerate(st.session_state.clarification_questions):
            answers[question] = st.text_input(question, key=f"clarify_{i}")
        
        if st.button("Submit Answers", type="primary"):
            if all(answers.values()):
                with st.spinner("Creating agent..."):
                    builder = get_builder()
                    result = builder.build_with_answers(
                        st.session_state.pending_description,
                        answers
                    )
                    
                    if result.get("success"):
                        config = result.get("agent_config", {})
                        st.session_state.agents[config['agent_id']] = config
                        st.session_state.current_agent = config['agent_id']
                        st.session_state.clarification_pending = False
                        st.success("Agent created!")
                        st.rerun()
            else:
                st.warning("Please answer all questions.")


def render_agent_chat():
    """Render the chat interface for the current agent."""
    if not st.session_state.current_agent:
        st.info("👈 Select an agent from the sidebar or create a new one")
        return
    
    agent_id = st.session_state.current_agent
    config = st.session_state.agents.get(agent_id, {})
    
    # Agent header
    st.header(f"💬 {config.get('name', 'Agent')}")
    
    # Agent info expander
    with st.expander("ℹ️ Agent Details"):
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Type:** {config.get('agent_type', 'Unknown')}")
            st.write(f"**Uses RAG:** {'Yes' if config.get('uses_rag') else 'No'}")
        with col2:
            st.write(f"**ID:** {agent_id}")
            tools = config.get('tools', [])
            st.write("**Tools:**")
            for tool in tools:
                st.markdown(f'<span class="tool-badge">{tool}</span>', unsafe_allow_html=True)
    
    # Document upload for RAG agents
    if config.get('uses_rag'):
        with st.expander("📁 Add Knowledge"):
            uploaded_file = st.file_uploader(
                "Upload documents (PDF, DOCX, TXT, CSV)",
                type=['pdf', 'docx', 'txt', 'csv'],
                key="doc_upload"
            )
            
            if uploaded_file:
                with st.spinner("Processing document..."):
                    # Save to temp file
                    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp:
                        tmp.write(uploaded_file.getvalue())
                        tmp_path = tmp.name
                    
                    # Add to knowledge base
                    if st.session_state.executor:
                        result = st.session_state.executor.add_document(tmp_path)
                        if result.get('success'):
                            st.success(f"Added: {uploaded_file.name} ({result.get('chunks_created', 0)} chunks)")
                        else:
                            st.error(result.get('error', 'Failed to add document'))
                    
                    # Clean up
                    os.unlink(tmp_path)
            
            # Text input option
            text_input = st.text_area("Or paste text directly:", key="text_knowledge")
            if st.button("Add Text"):
                if text_input and st.session_state.executor:
                    result = st.session_state.executor.add_text_knowledge(text_input)
                    if result.get('success'):
                        st.success("Text added to knowledge base!")
                    else:
                        st.error(result.get('error', 'Failed to add text'))
    
    st.divider()
    
    # Chat history display
    chat_container = st.container()
    
    with chat_container:
        for message in st.session_state.chat_history:
            if message["role"] == "user":
                st.markdown(f'<div class="chat-user">👤 <strong>You:</strong> {message["content"]}</div>', 
                           unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="chat-assistant">🤖 <strong>{config.get("name", "Agent")}:</strong> {message["content"]}</div>', 
                           unsafe_allow_html=True)
                if message.get("sources"):
                    st.caption(f"📚 Sources: {', '.join(message['sources'])}")
    
    # Chat input
    st.divider()
    
    col1, col2 = st.columns([5, 1])
    
    with col1:
        user_input = st.text_input(
            "Message",
            placeholder="Type your message...",
            key="chat_input",
            label_visibility="collapsed"
        )
    
    with col2:
        send_button = st.button("Send", type="primary", use_container_width=True)
    
    if send_button and user_input:
        # Add user message to history
        st.session_state.chat_history.append({
            "role": "user",
            "content": user_input
        })
        
        # Get response
        with st.spinner("Thinking..."):
            if not st.session_state.executor:
                st.session_state.executor = create_executor(config)
            
            if st.session_state.executor:
                result = st.session_state.executor.execute(user_input)
                
                # Add response to history
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": result.response,
                    "tool_used": result.tool_used,
                    "sources": result.sources
                })
            else:
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": "Sorry, I couldn't process your request. Please check if Ollama is running."
                })
        
        st.rerun()
    
    # Clear chat button
    if st.button("🗑️ Clear Chat"):
        st.session_state.chat_history = []
        if st.session_state.executor:
            st.session_state.executor.clear_history()
        st.rerun()


def render_stats():
    """Render statistics and analytics."""
    st.header("📊 Statistics")
    
    if not st.session_state.current_agent or not st.session_state.executor:
        st.info("Select an agent to view statistics")
        return
    
    stats = st.session_state.executor.get_stats()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("💬 Conversations", stats.get("conversations", 0))
    with col2:
        st.metric("⚡ Actions", stats.get("actions", 0))
    with col3:
        st.metric("📚 Knowledge Sources", stats.get("knowledge_sources", 0))


# ==================== Main Application ====================
def main():
    """Main application entry point."""
    # Initialize
    init_session_state()
    load_existing_agents()
    
    # Render UI
    render_header()
    render_sidebar()
    
    # Main content area with tabs
    tab1, tab2, tab3 = st.tabs(["🛠️ Build Agent", "💬 Chat", "📊 Stats"])
    
    with tab1:
        render_agent_builder()
    
    with tab2:
        render_agent_chat()
    
    with tab3:
        render_stats()
    
    # Footer
    st.divider()
    st.caption("AgentForge - Built for Hackathon | Powered by Ollama + LangChain + ChromaDB")


if __name__ == "__main__":
    main()
