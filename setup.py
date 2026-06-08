"""
AgentForge - Setup Script
Run this script first to create all required directories.
"""
import os
import sys

# Base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Directories to create
DIRECTORIES = [
    "database", 
    "uploads"
]

def setup():
    """Create all required directories and verify installation."""
    print("=" * 50)
    print("🤖 AgentForge Setup")
    print("=" * 50)
    
    # Create directories
    for dir_name in DIRECTORIES:
        dir_path = os.path.join(BASE_DIR, dir_name)
        os.makedirs(dir_path, exist_ok=True)
        print(f"✓ Created directory: {dir_name}/")
    
    # Verify all module files exist
    required_files = [
        "ollama_config.py",
        "task_parser.py", 
        "memory_manager.py",
        "rag_system.py",
        "agent_builder.py",
        "agent_executor.py",
        "tools.py",
        "guardrails.py",
        "streamlit_app.py"
    ]
    
    print("\n📁 Checking required files...")
    missing = []
    for f in required_files:
        path = os.path.join(BASE_DIR, f)
        if os.path.exists(path):
            print(f"  ✓ {f}")
        else:
            print(f"  ✗ {f} (MISSING)")
            missing.append(f)
    
    if missing:
        print(f"\n❌ Missing files: {missing}")
        return False
    
    # Test imports
    print("\n🔍 Testing module imports...")
    try:
        sys.path.insert(0, BASE_DIR)
        import task_parser
        import memory_manager
        print("  ✓ Core modules import successfully")
    except ImportError as e:
        print(f"  ✗ Import error: {e}")
        print("  → Run: pip install -r requirements.txt")
        return False
    
    print("\n" + "=" * 50)
    print("✅ Setup complete!")
    print("=" * 50)
    print("\n📋 Next steps:")
    print("  1. pip install -r requirements.txt")
    print("  2. ollama pull llama3")
    print("  3. ollama serve  (in a separate terminal)")
    print("  4. streamlit run streamlit_app.py")
    print()
    return True

if __name__ == "__main__":
    setup()
