python -m app.main

# Rodar a aplicação 
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# Swagger
http://127.0.0.1:8000/docs?utm_source=chatgpt.com

# Criar ambiente 
pyhton -m venv venv 

# Instalar as bibliotecas 
pip install -r requirements.txt

# Usando metodos do powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/containers/" -Method GET

# POST
$body = @{
    image = "nginx:latest"
    name = "nginx_teste"
    ports = @{
        "80/tcp" = 8080
    }
    detach = $true
} | ConvertTo-Json

Invoke-RestMethod `
    -Uri "http://localhost:8000/api/containers/" `
    -Method POST `
    -ContentType "application/json" `
    -Body $body

Invoke-RestMethod `
    -Uri "http://localhost:8000/api/containers/nginx_teste/stop" `
    -Method POST

Invoke-RestMethod `
    -Uri "http://localhost:8000/api/containers/nginx_teste/logs" `
    -Method GET