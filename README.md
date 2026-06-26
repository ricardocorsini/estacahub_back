# Backend Padrão com FastAPI

Estrutura inicial de backend em Python usando FastAPI.

## Estrutura

```text
.
├── app/
│   ├── core/
│   │   └── __init__.py
│   ├── models/
│   │   └── __init__.py
│   ├── routers/
│   │   ├── __init__.py
│   │   └── health.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── health.py
│   ├── services/
│   │   └── __init__.py
│   ├── __init__.py
│   └── main.py
├── .env
├── .gitignore
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## Como rodar localmente

Crie e ative um ambiente virtual:

```bash
python -m venv .venv
source .venv/bin/activate
```

No Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

Instale as dependências iniciais:

```bash
pip install fastapi uvicorn
```

Rode a aplicação:

```bash
uvicorn app.main:app --reload
```

A API ficará disponível em:

```text
http://localhost:8000
```

Documentação automática:

```text
http://localhost:8000/docs
```

## Rota inicial

Health check:

```http
GET /health
```

Resposta esperada:

```json
{
  "status": "ok",
  "service": "backend",
  "version": "0.1.0"
}
```

## Gerar requirements.txt depois

Como este ZIP não inclui `requirements.txt`, após instalar as dependências no ambiente virtual, gere o arquivo com:

```bash
pip freeze > requirements.txt
```
