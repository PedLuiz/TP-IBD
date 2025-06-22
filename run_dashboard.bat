@echo off
echo 📊 Dashboard de Importações Brasil 2024
echo =======================================
echo.

REM Verificar se o banco de dados existe
if not exist "importacoes_brasil_2024.db" (
    echo ❌ Banco de dados não encontrado: importacoes_brasil_2024.db
    echo 💡 Execute primeiro o notebook migration.ipynb para criar o banco
    echo.
    pause
    exit /b 1
)

echo ✅ Banco de dados encontrado
echo 🚀 Iniciando dashboard...
echo.
echo 🌐 O dashboard abrirá automaticamente no seu navegador
echo 📍 URL: http://localhost:8501
echo.
echo 💡 Para parar o dashboard, pressione Ctrl+C no terminal
echo.

REM Executar o Streamlit
streamlit run streamlit.py

pause
