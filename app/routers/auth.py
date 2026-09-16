from fastapi import APIRouter, HTTPException, Response, status

from app.core.security import (
    CurrentUser,
    DatabaseSession,
    criar_token_acesso,
    definir_cookie_autenticacao,
    remover_cookie_autenticacao,
)
from app.models.usuario import Usuario
from app.schemas.auth import (
    AuthResponse,
    LoginRequest,
    LogoutResponse,
    UsuarioCreate,
    UsuarioResponse,
)
from app.services.auth_service import (
    autenticar_usuario_service,
    criar_usuario_service,
)


router = APIRouter(
    prefix="/auth",
    tags=["autenticação"],
)


def _resposta_autenticacao(
    usuario: Usuario,
    token: str,
) -> AuthResponse:
    return AuthResponse(
        access_token=token,
        usuario=UsuarioResponse.model_validate(usuario),
    )


@router.post(
    "/register",
    response_model=AuthResponse,
    response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
)
def cadastrar(
    payload: UsuarioCreate,
    response: Response,
    db: DatabaseSession,
):
    usuario = criar_usuario_service(db, payload)
    token = criar_token_acesso(usuario.id)
    definir_cookie_autenticacao(response, token)
    return _resposta_autenticacao(usuario, token)


@router.post(
    "/login",
    response_model=AuthResponse,
    response_model_by_alias=True,
)
def login(
    payload: LoginRequest,
    response: Response,
    db: DatabaseSession,
):
    usuario = autenticar_usuario_service(
        db,
        str(payload.email),
        payload.senha,
    )

    if usuario is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha inválidos.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = criar_token_acesso(usuario.id)
    definir_cookie_autenticacao(response, token)
    return _resposta_autenticacao(usuario, token)


@router.get(
    "/me",
    response_model=UsuarioResponse,
    response_model_by_alias=True,
)
def obter_usuario_atual(usuario: CurrentUser):
    return usuario


@router.post(
    "/logout",
    response_model=LogoutResponse,
)
def logout(response: Response):
    remover_cookie_autenticacao(response)
    return {"message": "Sessão encerrada com sucesso."}
