#!/usr/bin/env python
"""Test script to run setup and verify imports."""
import subprocess
import sys
import os

os.chdir(r"C:\Users\HP\OneDrive\Desktop\aim26")

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

print("=" * 60)
print("COMMAND 1: Running python setup.py")
print("=" * 60)
result1 = subprocess.run([sys.executable, "setup.py"], capture_output=True, text=True)
print(result1.stdout)
if result1.stderr:
    print("STDERR:", result1.stderr)
print("Return code:", result1.returncode)

print("\n" + "=" * 60)
print("COMMAND 2: Running import verification")
print("=" * 60)
result2 = subprocess.run(
    [sys.executable, "-c", "import task_parser; import memory_manager; import ollama_config; print('All imports successful!')"],
    capture_output=True,
    text=True
)
print(result2.stdout)
if result2.stderr:
    print("STDERR:", result2.stderr)
print("Return code:", result2.returncode)

print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print(f"Setup.py: {'✅ SUCCESS' if result1.returncode == 0 else '❌ FAILED'}")
print(f"Import verification: {'✅ SUCCESS' if result2.returncode == 0 else '❌ FAILED'}")
