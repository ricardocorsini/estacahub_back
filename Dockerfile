FROM python:3.12-slim

WORKDIR /app

# Este Dockerfile está preparado para uso futuro.
# Como o projeto inicial não inclui requirements.txt no ZIP,
# instale as dependências manualmente ou adicione um requirements.txt depois.
#
# COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
