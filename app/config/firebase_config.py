from __future__ import annotations

import os
from dotenv import load_dotenv

try:
    import firebase_admin
    from firebase_admin import credentials, firestore
except Exception:  # ambiente sem dependências
    firebase_admin = None  # type: ignore
    credentials = None  # type: ignore
    firestore = None  # type: ignore


def get_firestore_client():
    """Inicializa e retorna o cliente Firestore ou None se indisponível.

    Lê `FIREBASE_CREDENTIALS` do `.env` ou variáveis de ambiente.
    """
    load_dotenv()
    cred_path = os.getenv("FIREBASE_CREDENTIALS")

    # Se firebase_admin não está disponível, retorna None (modo offline)
    if firebase_admin is None or credentials is None or firestore is None:
        return None

    try:
        if not firebase_admin._apps:
            if cred_path and os.path.exists(cred_path):
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
            else:
                # Tenta inicializar com credenciais padrão do ambiente
                firebase_admin.initialize_app()
        return firestore.client()
    except Exception:
        # Fallback para modo offline
        return None
