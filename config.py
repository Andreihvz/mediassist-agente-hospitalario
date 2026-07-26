# ============================
# CONFIGURACIÓN DE N8N
# ============================

import os
from dotenv import load_dotenv

load_dotenv()

URL_CHAT = os.getenv("URL_CHAT")
URL_GUARDAR_CITA = os.getenv("URL_GUARDAR_CITA")
URL_CONSULTAR_CITA = os.getenv("URL_CONSULTAR_CITA")

if not URL_CHAT:
    raise RuntimeError(
        "Falta configurar URL_CHAT en el archivo .env"
    )