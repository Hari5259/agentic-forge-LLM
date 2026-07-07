"""
AgentForge - Diagnostic Test
Run this to check what's working and what's not.
"""
import sys
import os

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

print("=" * 50)
print("🔍 AgentForge Diagnostics")
print("=" * 50)

# Check Python version
print(f"\n✓ Python: {sys.version}")

# Check current directory
print(f"✓ Working Dir: {os.getcwd()}")

# Test basic imports
print("\n📦 Testing imports...")

errors = []

try:
    import streamlit
    print(f"  ✓ streamlit {streamlit.__version__}")
except ImportError as e:
    print(f"  ✗ streamlit: {e}")
    errors.append("pip install streamlit")

try:
    import langchain
    print(f"  ✓ langchain")
except ImportError as e:
    print(f"  ✗ langchain: {e}")
    errors.append("pip install langchain langchain-community")

try:
    import chromadb
    print(f"  ✓ chromadb")
except ImportError as e:
    print(f"  ✗ chromadb: {e}")
    errors.append("pip install chromadb")

try:
    import requests
    print(f"  ✓ requests")
except ImportError as e:
    print(f"  ✗ requests: {e}")
    errors.append("pip install requests")

# Test local modules
print("\n📁 Testing local modules...")

try:
    import ollama_config
    print("  ✓ ollama_config")
except Exception as e:
    print(f"  ✗ ollama_config: {e}")

try:
    import task_parser
    print("  ✓ task_parser")
except Exception as e:
    print(f"  ✗ task_parser: {e}")

try:
    import memory_manager
    print("  ✓ memory_manager")
except Exception as e:
    print(f"  ✗ memory_manager: {e}")

try:
    import guardrails
    print("  ✓ guardrails")
except Exception as e:
    print(f"  ✗ guardrails: {e}")

try:
    import tools
    print("  ✓ tools")
except Exception as e:
    print(f"  ✗ tools: {e}")

try:
    import rag_system
    print("  ✓ rag_system")
except Exception as e:
    print(f"  ✗ rag_system: {e}")

try:
    import agent_builder
    print("  ✓ agent_builder")
except Exception as e:
    print(f"  ✗ agent_builder: {e}")

try:
    import agent_executor
    print("  ✓ agent_executor")
except Exception as e:
    print(f"  ✗ agent_executor: {e}")

# Test Ollama connection
print("\n🤖 Testing Ollama connection...")
try:
    import requests
    response = requests.get("http://localhost:11434/api/tags", timeout=3)
    if response.status_code == 200:
        models = response.json().get("models", [])
        print(f"  ✓ Ollama running - {len(models)} models available")
        for m in models[:3]:
            print(f"    - {m.get('name', 'unknown')}")
    else:
        print("  ✗ Ollama not responding properly")
except Exception as e:
    print(f"  ✗ Ollama not running: {e}")
    print("  → Run: ollama serve")

print("\n" + "=" * 50)
if errors:
    print("❌ Fix missing packages:")
    for cmd in errors:
        print(f"   {cmd}")
else:
    print("✅ All checks passed!")
    print("\nRun: streamlit run streamlit_app.py")
print("=" * 50)
