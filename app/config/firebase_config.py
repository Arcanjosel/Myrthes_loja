from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv
try:
    # leitura opcional das configs do app
    from app.config import settings as app_settings  # type: ignore
except Exception:
    app_settings = None  # type: ignore

try:
    import firebase_admin
    from firebase_admin import credentials, firestore
except Exception:  # ambiente sem dependências
    firebase_admin = None  # type: ignore
    credentials = None  # type: ignore
    firestore = None  # type: ignore


def _resolve_credentials_path() -> str | None:
    """Resolve o caminho do arquivo de credenciais do Firebase.

    Ordem de busca:
    1) Variável de ambiente/arquivo .env: FIREBASE_CREDENTIALS
    2) Arquivo `myrthes.json` no diretório de trabalho atual
    3) Arquivo `myrthes.json` na raiz do projeto (duas pastas acima de `app/config`)
    """
    load_dotenv()

    # 0) Settings.json (se disponível)
    try:
        if app_settings is not None:
            set_path = getattr(app_settings, "FIREBASE_CREDENTIALS", None)
            if set_path and os.path.isfile(str(set_path)):
                return str(set_path)
    except Exception:
        pass

    env_path = os.getenv("FIREBASE_CREDENTIALS")
    if env_path and os.path.isfile(env_path):
        return env_path

    # 2) CWD
    cwd_candidate = Path.cwd() / "myrthes.json"
    if cwd_candidate.is_file():
        return str(cwd_candidate)

    # 3) Raiz do projeto relativa a este arquivo: app/config/ -> ../../
    project_root = Path(__file__).resolve().parents[2]
    root_candidate = project_root / "myrthes.json"
    if root_candidate.is_file():
        return str(root_candidate)

    return None


def get_firestore_client():
    """Inicializa e retorna o cliente Firestore ou None se indisponível.

    Procura automaticamente o segredo `myrthes.json` na raiz do projeto ou
    utiliza o caminho definido em `FIREBASE_CREDENTIALS`.
    """
    # Se firebase_admin não está disponível, retorna None (modo offline)
    if firebase_admin is None or credentials is None or firestore is None:
        return None

    try:
        if not firebase_admin._apps:
            cred_path = _resolve_credentials_path()
            if cred_path:
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
            else:
                # Tenta inicializar com credenciais padrão do ambiente
                firebase_admin.initialize_app()
        return firestore.client()
    except Exception:
        # Fallback para modo offline
        return None
