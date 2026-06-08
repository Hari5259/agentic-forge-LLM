@echo off
cd /d "C:\Users\HP\OneDrive\Desktop\aim26"
echo === Running setup.py ===
python setup.py
echo.
echo === Running import verification ===
python -c "import task_parser; import memory_manager; import ollama_config; print('All imports successful!')"
