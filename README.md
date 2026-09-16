# EstacaHub API

Backend FastAPI com PostgreSQL e autenticação JWT por cookie `HttpOnly`.

## Configuração

1. Copie `.env.example` para `.env`.
2. Gere uma chave exclusiva com `openssl rand -hex 32` e defina `JWT_SECRET_KEY`.
3. Em produção, use `DEBUG=false` e `AUTH_COOKIE_SECURE=true`.
4. Instale as dependências com `pip install -r requirements.txt`.

O frontend oficial já está liberado no CORS:

- `https://www.estacahub.com`
- `https://estacahub.com`

## Execução

Com Docker Compose:

```bash
docker compose up --build
```

Ou, com o PostgreSQL já disponível:

```bash
uvicorn app.main:app --reload
```

Na inicialização, `init_db()` cria o schema `app` e qualquer tabela ausente. O
novo model cria automaticamente `app.usuarios`; nenhuma senha em texto puro é
armazenada.

## Rotas de autenticação

- `POST /api/auth/register` — cria a conta e inicia a sessão.
- `POST /api/auth/login` — autentica e inicia a sessão.
- `GET /api/auth/me` — retorna o usuário autenticado.
- `POST /api/auth/logout` — remove o cookie da sessão.

As rotas `/api/obras` exigem autenticação. Navegadores usam automaticamente o
cookie `HttpOnly`; outros clientes podem enviar o mesmo JWT em
`Authorization: Bearer <token>`.

Documentação interativa: `http://localhost:8000/docs`.
