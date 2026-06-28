# Atajo para levantar la web localmente.
# Uso:  .\run.ps1     (desde la raíz del proyecto, en PowerShell)
# Luego abrí http://localhost:8000  ·  Frenar: Ctrl + C
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
