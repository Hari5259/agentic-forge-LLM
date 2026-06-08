@echo off
cd /d "C:\Users\HP\OneDrive\Desktop\aim26"

echo.
echo ============================================================
echo Step 1: Running setup.py
echo ============================================================
python setup.py
echo.

echo ============================================================
echo Step 2: Installing dependencies
echo ============================================================
pip install streamlit langchain langchain-community chromadb pypdf python-docx docx2txt requests --quiet
echo.

echo ============================================================
echo Step 3: Starting Streamlit app
echo ============================================================
streamlit run streamlit_app.py
pause
