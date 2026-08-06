# ============================================================
# Imagem base
# ============================================================
FROM python:3.13-slim

# Evita criação de arquivos .pyc
ENV PYTHONDONTWRITEBYTECODE=1

# Faz o Python enviar logs imediatamente para o terminal
ENV PYTHONUNBUFFERED=1

# Diretório de trabalho dentro do container
WORKDIR /app

# ============================================================
# Dependências
# ============================================================

# Copia primeiro apenas o requirements.
# Isso permite aproveitar o cache do Docker quando o código
# muda, mas as dependências continuam iguais.
COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# ============================================================
# Aplicação
# ============================================================

# Copia o projeto para dentro do container
COPY . .

# Porta utilizada pelo Uvicorn/FastAPI
EXPOSE 8000

# ============================================================
# Inicialização
# ============================================================

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]