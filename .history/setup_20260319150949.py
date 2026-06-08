"""
AgentForge - Setup Script
Run this script first to create all required directories.
"""
import os

# Base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Directories to create
DIRECTORIES = [
    "backend",
    "database", 
    "ui",
    "models",
    "uploads"
]

def setup():
    """Create all required directories."""
    for dir_name in DIRECTORIES:
        dir_path = os.path.join(BASE_DIR, dir_name)
        os.makedirs(dir_path, exist_ok=True)
        print(f"✓ Created: {dir_path}")
    
    # Create __init__.py files for Python packages
    for pkg in ["backend", "models"]:
        init_file = os.path.join(BASE_DIR, pkg, "__init__.py")
        if not os.path.exists(init_file):
            with open(init_file, "w") as f:
                f.write("# AgentForge Package\n")
            print(f"✓ Created: {init_file}")
    
    print("\n✅ Setup complete! Run: streamlit run ui/streamlit_app.py")

if __name__ == "__main__":
    setup()
