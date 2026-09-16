from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, Request, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.models.usuario import Usuario


settings = get_settings()
password_hash = PasswordHash.recommended()

# Evita diferença perceptível de tempo entre e-mail inexistente e senha inválida.
DUMMY_PASSWORD_HASH = password_hash.hash("estacahub-dummy-password")

bearer_scheme = HTTPBearer(auto_error=False)

DatabaseSession = Annotated[Session, Depends(get_db)]
BearerCredentials = Annotated[
    HTTPAuthorizationCredentials | None,
    Depends(bearer_scheme),
]


def gerar_hash_senha(senha: str) -> str:
    return password_hash.hash(senha)


def verificar_senha(senha: str, senha_hash: str) -> bool:
    try:
        return password_hash.verify(senha, senha_hash)
    except (TypeError, ValueError):
        return False


def criar_token_acesso(usuario_id: int) -> str:
    agora = datetime.now(timezone.utc)
    expira_em = agora + timedelta(
        minutes=settings.access_token_expire_minutes,
    )

    payload = {
        "sub": str(usuario_id),
        "type": "access",
        "iat": agora,
        "exp": expira_em,
    }

    return jwt.encode(
        payload,
        settings.jwt_secret_key.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )


def definir_cookie_autenticacao(
    response: Response,
    token: str,
) -> None:
    response.set_cookie(
        key=settings.auth_cookie_name,
        value=token,
        max_age=settings.access_token_expire_minutes * 60,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/",
    )


def remover_cookie_autenticacao(response: Response) -> None:
    response.delete_cookie(
        key=settings.auth_cookie_name,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/",
    )


def _erro_credenciais() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Sessão inválida ou expirada.",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    request: Request,
    credentials: BearerCredentials,
    db: DatabaseSession,
) -> Usuario:
    token = (
        credentials.credentials
        if credentials is not None
        else request.cookies.get(settings.auth_cookie_name)
    )

    if not token:
        raise _erro_credenciais()

    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key.get_secret_value(),
            algorithms=[settings.jwt_algorithm],
        )
        subject = payload.get("sub")
        token_type = payload.get("type")

        if subject is None or token_type != "access":
            raise _erro_credenciais()

        usuario_id = int(subject)
    except (InvalidTokenError, TypeError, ValueError) as exc:
        raise _erro_credenciais() from exc

    usuario = db.get(Usuario, usuario_id)

    if usuario is None or not usuario.ativo:
        raise _erro_credenciais()

    return usuario


CurrentUser = Annotated[Usuario, Depends(get_current_user)]
