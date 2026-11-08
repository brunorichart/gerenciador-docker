python -m app.main

# Rodar a aplicação 
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# Swagger
http://127.0.0.1:8000/docs?utm_source=chatgpt.com

# Criar ambiente 
pyhton -m venv venv 

# Instalar as bibliotecas 
pip install -r requirements.txt