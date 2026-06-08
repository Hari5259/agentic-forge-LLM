# 🤖 AgentForge - No-Code Custom AI Agents Builder

A hackathon project that allows non-technical users to create AI agents using plain English descriptions. The entire system runs **locally** with no external API keys required.

![AgentForge Demo](https://img.shields.io/badge/Status-Hackathon%20Project-green)
![Python](https://img.shields.io/badge/Python-3.9+-blue)
![License](https://img.shields.io/badge/License-MIT-yellow)

## 🌟 Features

### 1. **Natural Language Agent Builder**
- Describe your agent in plain English
- System automatically determines required tools and workflow
- Smart clarification for vague requests

### 2. **Knowledge Base (RAG)**
- Upload documents: PDF, DOCX, TXT, CSV
- Automatic embedding and storage in ChromaDB
- Context-aware responses

### 3. **Persistent Memory**
- SQLite-based conversation history
- Action logging and tracking
- Agent state persistence

### 4. **Built-in Tools**
- 📧 Email Generator
- 📄 Resume Screener
- 📝 Document Summarizer
- ❓ FAQ Chatbot

### 5. **Safety Guardrails**
- Sensitive data detection and masking
- Harmful content filtering
- Action authorization checks

### 6. **Proactive Suggestions**
- Detects repetitive tasks
- Suggests creating dedicated agents

## 🚀 Quick Start

### Prerequisites

1. **Python 3.9+**
2. **Ollama** - Install from [ollama.ai](https://ollama.ai)

### Installation

```bash
# 1. Clone or navigate to the project
cd aim26

# 2. Run setup to create directories
python setup.py

# 3. Create virtual environment (recommended)
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 4. Install dependencies
pip install -r requirements.txt

# 5. Pull the Ollama model
ollama pull llama3

# 6. Make sure Ollama is running
ollama serve

# 7. Run the application
streamlit run streamlit_app.py
```

## 📁 Project Structure

```
aim26/
├── streamlit_app.py      # Main Streamlit UI
├── agent_builder.py      # Agent creation logic
├── agent_executor.py     # Agent execution engine
├── task_parser.py        # Natural language parsing
├── memory_manager.py     # SQLite memory management
├── rag_system.py         # ChromaDB RAG implementation
├── tools.py              # Agent tools (email, resume, etc.)
├── guardrails.py         # Safety and security
├── ollama_config.py      # Ollama LLM configuration
├── setup.py              # Directory setup script
├── requirements.txt      # Python dependencies
├── database/             # SQLite and ChromaDB storage
│   ├── memory.db
│   └── chroma_db/
└── uploads/              # Uploaded documents
```

## 💡 Usage Examples

### Creating an HR Assistant

```
User: "Create an HR assistant that screens resumes and selects top candidates based on Python and machine learning skills."

AgentForge will:
1. Parse the request
2. Identify agent type: HR Assistant
3. Select tools: resume_screener, document_summarizer
4. Enable RAG for document processing
5. Generate appropriate system prompt
6. Create the agent ready for use
```

### Using the Agent

```
User: "Here's a resume for John Doe..."

Agent Response:
Match Score: 85/100
Key Qualifications Met:
- 5 years Python experience ✓
- Machine learning projects ✓
- Computer Science degree ✓
Missing: Leadership experience
Recommendation: RECOMMENDED
```

## 🛠️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Streamlit UI                              │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   Agent Builder                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ Task Parser  │  │  Guardrails  │  │ Quick Templates  │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                  Agent Executor                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │    Tools     │  │  RAG System  │  │ Memory Manager   │  │
│  │  - Email     │  │  (ChromaDB)  │  │   (SQLite)       │  │
│  │  - Resume    │  │              │  │                  │  │
│  │  - Summary   │  │              │  │                  │  │
│  │  - FAQ       │  │              │  │                  │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                 Ollama (Local LLM)                           │
│                     llama3                                   │
└─────────────────────────────────────────────────────────────┘
```

## 🔧 Configuration

### Ollama Settings (ollama_config.py)

```python
DEFAULT_MODEL = "llama3"
OLLAMA_BASE_URL = "http://localhost:11434"
```

### Available Models

```bash
# List available models
ollama list

# Pull a different model
ollama pull mistral
ollama pull codellama
```

## 🎨 Quick Templates

Use pre-configured templates for common use cases:

| Template | Description |
|----------|-------------|
| HR Screener | Screen resumes and rank candidates |
| Email Writer | Compose professional emails |
| Doc Analyzer | Analyze and summarize documents |
| FAQ Bot | Answer questions from knowledge base |

## 🔒 Safety Features

- **Input Sanitization**: Removes potentially harmful patterns
- **Sensitive Data Detection**: Identifies SSN, credit cards, passwords
- **Output Filtering**: Masks sensitive information in responses
- **Action Authorization**: Blocks unauthorized system actions
- **Audit Logging**: Tracks all safety-related events

## 🐛 Troubleshooting

### Ollama Not Connecting

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama service
ollama serve
```

### Missing Model

```bash
# Pull the required model
ollama pull llama3
```

### Import Errors

```bash
# Make sure you're in the right directory
cd aim26

# Reinstall dependencies
pip install -r requirements.txt --upgrade
```

## 📝 API Reference

### AgentBuilder

```python
from agent_builder import AgentBuilder

builder = AgentBuilder()

# Create from description
result = builder.build_from_description(
    "Create an email assistant that writes professional emails"
)

# Create from template
from agent_builder import QuickAgentBuilder
result = QuickAgentBuilder.create_from_template("email_writer", builder)
```

### AgentExecutor

```python
from agent_executor import AgentExecutorWrapper

executor = AgentExecutorWrapper(agent_config)

# Execute a request
result = executor.execute("Write a thank you email")
print(result.response)

# Add knowledge
executor.add_document("company_info.pdf")
```

## 🏆 Hackathon Notes

This project was built for a hackathon with the following constraints:
- **100% Local**: No external API calls
- **No API Keys**: Uses Ollama for LLM
- **Simple Setup**: Minimal dependencies
- **Demo Ready**: Working end-to-end in minutes

## 📜 License

MIT License - Feel free to use, modify, and distribute.

## 🤝 Contributing

This is a hackathon project, but contributions are welcome!

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

---

**Built with ❤️ using Ollama, LangChain, ChromaDB, and Streamlit**
