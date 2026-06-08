#!/usr/bin/env python
"""Run setup and then start streamlit app"""
import subprocess
import sys
import os

os.chdir('c:\\Users\\HP\\OneDrive\\Desktop\\aim26')

print("=" * 60)
print("Step 1: Running setup.py")
print("=" * 60)
result = subprocess.run([sys.executable, 'setup.py'], capture_output=False)
print(f"Setup.py exit code: {result.returncode}\n")

print("=" * 60)
print("Step 2: Installing dependencies")
print("=" * 60)
deps = [
    'streamlit', 'langchain', 'langchain-community', 'chromadb',
    'pypdf', 'python-docx', 'docx2txt', 'requests'
]
result = subprocess.run(
    [sys.executable, '-m', 'pip', 'install'] + deps + ['--quiet'],
    capture_output=False
)
print(f"Pip install exit code: {result.returncode}\n")

print("=" * 60)
print("Step 3: Starting Streamlit app")
print("=" * 60)
result = subprocess.run([sys.executable, '-m', 'streamlit', 'run', 'streamlit_app.py'])
sys.exit(result.returncode)
