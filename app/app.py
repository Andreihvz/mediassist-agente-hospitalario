from __future__ import annotations

import html
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel
import requests
import streamlit as st


# ==================================================
# CONFIGURACIÓN DE RUTAS
# ==================================================

BASE = Path(__file__).resolve().parent.parent
CARPETA_SCRIPTS = BASE / "scripts"

if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

if str(CARPETA_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(CARPETA_SCRIPTS))

from services.memoria import (  # noqa: E402
    actualizar_memoria,
    crear_memoria_vacia,
    resolver_pregunta_con_memoria,
)
from services.router import crear_contexto_oficial  # noqa: E402
from services.citas import (
    crear_estado_cita_vacio,
    procesar_agendamiento,
    usuario_quiere_agendar,
)
from services.citas_n8n import (  # noqa: E402
    consultar_cita,
    guardar_cita,
)


# ==================================================
# CONFIGURACIÓN DE N8N
# ==================================================

URL_N8N = (
    "https://andreeihvz.app.n8n.cloud/"
    "webhook/mediassist-chat"
)



# ==================================================
# CONFIGURACIÓN DE STREAMLIT
# ==================================================

st.set_page_config(
    page_title="MediAssist",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ==================================================
# IDENTIDAD VISUAL — "Clínica de barrio, con oficio"
# --------------------------------------------------
# Paleta:  tinta #0B2E29 · teal #0F766E · teal claro #14B8A6
#          papel #F7F9F8 · ámbar #B45309 · texto #10241F
# Tipos:   Fraunces (títulos) · Inter (cuerpo) · IBM Plex Mono (datos)
# Firma:   línea de pulso (ECG) como divisor y como estado "en línea"
# ==================================================

st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,500;0,9..144,600;1,9..144,500&family=Inter:wght@400;500;600;700&family=IBM+Plex+Mono:wght@500;600&display=swap');

        :root {
            --ink: #10241F;
            --teal-deep: #0B2E29;
            --teal: #0F766E;
            --teal-bright: #14B8A6;
            --teal-soft: #E6F3F1;
            --amber: #B45309;
            --amber-soft: #FDF3E7;
            --amber-border: #F2D8B0;
            --paper: #F7F9F8;
            --card: #FFFFFF;
            --muted: #5B6B68;
            --border: #E3E8E6;
            --cream: #F1F5F3;
        }

        html, body, [class*="css"] {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }

        .stApp {
            background: var(--paper);
            color: var(--ink);
        }

        header[data-testid="stHeader"] {
            background: rgba(247, 249, 248, 0.86);
            backdrop-filter: blur(10px);
            box-shadow: none;
        }

        .block-container {
            max-width: 900px;
            padding-top: 1rem;
            padding-bottom: 8rem;
        }

        *:focus-visible {
            outline: 2px solid var(--teal-bright);
            outline-offset: 2px;
        }

        ::-webkit-scrollbar { width: 10px; height: 10px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb {
            background: #C7D3D0;
            border-radius: 999px;
            border: 2px solid var(--paper);
        }

        /* ---------- SIDEBAR: tinta profunda ---------- */

        section[data-testid="stSidebar"] {
            background: var(--teal-deep);
            border-right: none;
        }

        section[data-testid="stSidebar"] > div {
            padding-top: 1.1rem;
        }

        section[data-testid="stSidebar"] * {
            color: var(--cream);
        }

        section[data-testid="stSidebar"] .stButton button {
            width: 100%;
            min-height: 42px;
            border-radius: 10px;
            border: 1px solid rgba(241, 245, 243, 0.16);
            background: rgba(241, 245, 243, 0.06);
            color: var(--cream);
            font-weight: 600;
            font-size: 13.5px;
            box-shadow: none;
            transition: all .15s ease;
        }

        section[data-testid="stSidebar"] .stButton button:hover {
            border-color: var(--teal-bright);
            background: rgba(20, 184, 166, 0.16);
            color: #FFFFFF;
        }

        .sb-brand {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 2px 4px 20px;
            border-bottom: 1px solid rgba(241, 245, 243, 0.14);
            margin-bottom: 18px;
        }

        .sb-brand-icon {
            width: 40px;
            height: 40px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 11px;
            background: var(--teal);
            font-size: 19px;
        }

        .sb-brand-title {
            margin: 0;
            font-family: 'Fraunces', serif;
            font-size: 18px;
            font-weight: 600;
            letter-spacing: -0.01em;
            color: #FFFFFF;
        }

        .sb-brand-subtitle {
            margin: 1px 0 0;
            color: #9FB6B1;
            font-size: 11.5px;
        }

        .sb-label {
            margin: 22px 2px 10px;
            color: #6E8B85;
            font-size: 10.5px;
            font-weight: 700;
            letter-spacing: .1em;
            text-transform: uppercase;
        }

        .sb-item {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 8px 6px;
            border-radius: 8px;
            color: #D4E3DF;
            font-size: 13.5px;
            font-weight: 500;
        }

        .sb-status {
            display: flex;
            align-items: center;
            gap: 9px;
            margin-top: 22px;
            padding: 11px 12px;
            border: 1px solid rgba(20, 184, 166, 0.35);
            border-radius: 10px;
            background: rgba(20, 184, 166, 0.12);
            color: #7EE8D2;
            font-size: 12.5px;
            font-weight: 600;
        }

        .pulse-dot {
            width: 8px;
            height: 8px;
            border-radius: 999px;
            background: var(--teal-bright);
            flex-shrink: 0;
            box-shadow: 0 0 0 0 rgba(20, 184, 166, .6);
            animation: pulse-ring 2s infinite;
        }

        @keyframes pulse-ring {
            0%   { box-shadow: 0 0 0 0 rgba(20, 184, 166, .55); }
            70%  { box-shadow: 0 0 0 7px rgba(20, 184, 166, 0); }
            100% { box-shadow: 0 0 0 0 rgba(20, 184, 166, 0); }
        }

        @media (prefers-reduced-motion: reduce) {
            .pulse-dot { animation: none; }
        }

        /* ---------- ENCABEZADO ---------- */

        .hero {
            padding: 10px 2px 0;
        }

        .hero-eyebrow {
            display: inline-flex;
            align-items: center;
            gap: 7px;
            color: var(--teal);
            font-size: 12px;
            font-weight: 650;
            letter-spacing: .07em;
            text-transform: uppercase;
            margin-bottom: 10px;
        }

        .hero-title {
            margin: 0;
            font-family: 'Fraunces', serif;
            font-style: italic;
            font-weight: 500;
            color: var(--ink);
            font-size: 34px;
            letter-spacing: -0.01em;
            line-height: 1.15;
        }

        .hero-subtitle {
            margin: 8px 0 0;
            color: var(--muted);
            font-size: 14.5px;
            max-width: 46ch;
        }

        .pulse-divider {
            width: 100%;
            height: 26px;
            margin: 18px 0 22px;
            color: var(--teal);
            opacity: 0.55;
        }

        /* ---------- ACCIONES RÁPIDAS ---------- */

        .quick-label {
            margin: 0 0 12px;
            color: var(--muted);
            font-size: 12.5px;
            font-weight: 650;
            letter-spacing: .04em;
            text-transform: uppercase;
        }

        div[data-testid="stVerticalBlockBorderWrapper"] {
            border-radius: 14px !important;
            border-color: var(--border) !important;
            transition: transform .15s ease, box-shadow .15s ease, border-color .15s ease;
        }

        div[data-testid="stVerticalBlockBorderWrapper"]:has(button):hover {
            transform: translateY(-3px);
            border-color: var(--teal-bright) !important;
            box-shadow: 0 10px 24px rgba(15, 118, 110, .12);
        }

        .qa-icon {
            width: 34px;
            height: 34px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 9px;
            background: var(--teal-soft);
            font-size: 17px;
            margin-bottom: 10px;
        }

        .qa-title {
            margin: 0;
            font-family: 'Fraunces', serif;
            color: var(--ink);
            font-size: 15px;
            font-weight: 600;
        }

        .qa-desc {
            margin: 3px 0 12px;
            color: var(--muted);
            font-size: 11.5px;
            line-height: 1.45;
            min-height: 32px;
        }

        div[data-testid="stVerticalBlock"] div[data-testid="stButton"] button {
            min-height: 36px;
            border-radius: 8px;
            border: 1px solid var(--border);
            background: var(--paper);
            color: var(--teal);
            font-weight: 650;
            font-size: 12.5px;
            box-shadow: none;
            transition: all .15s ease;
        }

        div[data-testid="stVerticalBlock"] div[data-testid="stButton"] button:hover {
            border-color: var(--teal);
            background: var(--teal);
            color: #FFFFFF;
        }

        /* ---------- CHAT ---------- */

        div[data-testid="stChatMessage"] {
            background: transparent;
            padding-top: .45rem;
            padding-bottom: .45rem;
            border: none;
        }

        div[data-testid="stChatMessage"] [data-testid="stChatMessageContent"] {
            max-width: 100%;
        }

        div[data-testid="stChatMessageAvatarUser"] {
            background: var(--teal-deep) !important;
        }

        div[data-testid="stChatMessageAvatarAssistant"] {
            background: var(--teal-soft) !important;
        }

        .bubble-user {
            background: var(--teal-deep);
            color: #F3F7F6;
            border-radius: 16px 16px 4px 16px;
            padding: 12px 16px;
            display: inline-block;
            max-width: 100%;
            line-height: 1.55;
            font-size: 14.5px;
        }

        /* ---------- TARJETA DE RESPUESTA ---------- */

        .response-card {
            background: var(--card);
            border: 1px solid var(--border);
            border-left: 3px solid var(--accent, var(--teal));
            border-radius: 4px 14px 14px 4px;
            padding: 17px 20px;
            margin-top: 2px;
            box-shadow: 0 3px 14px rgba(16, 36, 31, .05);
        }

        .response-header {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 9px;
        }

        .response-icon {
            width: 30px;
            height: 30px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 8px;
            background: var(--teal-soft);
            font-size: 15px;
            flex-shrink: 0;
        }

        .response-title {
            font-family: 'Fraunces', serif;
            color: var(--ink);
            font-size: 16.5px;
            font-weight: 600;
        }

        .response-message {
            color: #3D4B48;
            line-height: 1.6;
            font-size: 14.5px;
            margin-bottom: 8px;
        }

        .data-row {
            display: flex;
            gap: 9px;
            align-items: baseline;
            padding: 9px 0;
            border-top: 1px dashed var(--border);
            color: #2B3835;
            font-size: 13.5px;
        }

        .data-row .data-label {
            color: var(--muted);
            font-weight: 550;
        }

        .data-row .data-value {
            font-family: 'IBM Plex Mono', monospace;
            font-weight: 500;
            color: var(--ink);
            letter-spacing: -0.01em;
        }

        .warning-row {
            margin-top: 12px;
            padding: 11px 13px;
            border: 1px solid var(--amber-border);
            border-radius: 10px;
            background: var(--amber-soft);
            color: var(--amber);
            font-size: 13px;
            line-height: 1.5;
        }

        .final-question {
            margin-top: 13px;
            padding-top: 13px;
            border-top: 1px solid var(--border);
            color: var(--teal);
            font-weight: 600;
            font-size: 13.5px;
        }

        /* ---------- SPINNER ---------- */

        div[data-testid="stSpinner"] > div {
            color: var(--teal) !important;
            font-size: 13.5px;
        }

        /* ---------- INPUT DE CHAT ---------- */

        div[data-testid="stChatInput"] {
            border: 1px solid var(--border);
            border-radius: 18px;
            background: #FFFFFF;
            box-shadow: 0 8px 26px rgba(16, 36, 31, .09);
        }

        div[data-testid="stChatInput"]:focus-within {
            border-color: var(--teal-bright);
        }

        div[data-testid="stChatInput"] textarea {
            border-radius: 18px;
            color: var(--ink) !important;
            font-size: 14.5px;
        }

        div[data-testid="stChatInput"] textarea::placeholder {
            color: #93A6A2 !important;
        }

        div[data-testid="stChatInput"] button {
            background: var(--teal) !important;
            border-radius: 11px !important;
        }

        div[data-testid="stChatInput"] button:hover {
            background: var(--teal-deep) !important;
        }

        /* ---------- AVISO FINAL ---------- */

        .disclaimer {
            margin-top: 30px;
            padding: 14px 12px;
            color: #93A6A2;
            font-size: 11px;
            text-align: center;
            line-height: 1.6;
            border-top: 1px solid var(--border);
        }

        @media (max-width: 700px) {
            .block-container { padding-top: .8rem; }
            .hero-title { font-size: 27px; }
        }
    </style>
    """,
    unsafe_allow_html=True,
)


PULSO_ECG_SVG = """
<svg class="pulse-divider" viewBox="0 0 700 40" preserveAspectRatio="none" xmlns="http://www.w3.org/2000/svg">
    <polyline points="0,20 130,20 152,20 165,4 180,36 196,12 210,20 700,20"
        fill="none" stroke="currentColor" stroke-width="2"
        stroke-linecap="round" stroke-linejoin="round" />
</svg>
"""


# ==================================================
# FUNCIONES PARA LEER LA RESPUESTA DE N8N
# ==================================================

def extraer_texto_respuesta(respuesta_json: Any) -> str:
    """
    Extrae el texto generado por Gemini desde diferentes
    estructuras posibles de respuesta.
    """

    if isinstance(respuesta_json, str):
        return respuesta_json

    if isinstance(respuesta_json, list):
        for elemento in respuesta_json:
            texto = extraer_texto_respuesta(elemento)

            if texto:
                return texto

    if isinstance(respuesta_json, dict):
        for clave in (
            "texto",
            "text",
            "output",
            "response",
            "respuesta",
        ):
            valor = respuesta_json.get(clave)

            if isinstance(valor, str) and valor.strip():
                return valor.strip()

        contenido = respuesta_json.get("content")

        if isinstance(contenido, dict):
            partes = contenido.get("parts", [])

            if isinstance(partes, list):
                for parte in partes:
                    if not isinstance(parte, dict):
                        continue

                    texto = parte.get("text")

                    if isinstance(texto, str) and texto.strip():
                        return texto.strip()

        for valor in respuesta_json.values():
            texto = extraer_texto_respuesta(valor)

            if texto:
                return texto

    return ""


def limpiar_bloque_json(texto: str) -> str:
    """
    Elimina los bloques ```json y ``` que Gemini
    puede colocar alrededor de una respuesta.
    """

    texto = str(texto).strip()

    texto = re.sub(
        r"^```(?:json)?\s*",
        "",
        texto,
        flags=re.IGNORECASE,
    )

    texto = re.sub(
        r"\s*```$",
        "",
        texto,
    )

    return texto.strip()


def convertir_a_json(
    texto: str,
) -> dict[str, Any] | None:
    """
    Intenta convertir la respuesta de Gemini en JSON.
    """

    texto_limpio = limpiar_bloque_json(texto)

    try:
        datos = json.loads(texto_limpio)

        if isinstance(datos, dict):
            return datos

    except json.JSONDecodeError:
        return None

    return None


# ==================================================
# CONEXIÓN CON N8N
# ==================================================


def consultar_n8n(
    pregunta: str,
    contexto: str,
) -> tuple[str, dict[str, Any] | None]:
    """
    Envía la pregunta y el contexto oficial a n8n.
    """

    datos = {
        "mensaje": pregunta,
        "contexto": contexto,
    }

    respuesta = requests.post(
        URL_N8N,
        json=datos,
        timeout=60,
    )

    respuesta.raise_for_status()

    try:
        respuesta_json = respuesta.json()
        texto = extraer_texto_respuesta(
            respuesta_json
        )

    except ValueError:
        texto = respuesta.text

    respuesta_estructurada = convertir_a_json(
        texto
    )

    return texto, respuesta_estructurada


# ==================================================
# CONSULTA DE CITAS
# ==================================================

def usuario_quiere_consultar_cita(texto: str) -> bool:
    """Detecta solicitudes para consultar una cita existente."""

    texto_normalizado = str(texto).strip().lower()

    expresiones = (
        "consultar mi cita",
        "consultar una cita",
        "buscar mi cita",
        "buscar una cita",
        "ver mi cita",
        "revisar mi cita",
        "informacion de mi cita",
        "información de mi cita",
    )

    return any(
        expresion in texto_normalizado
        for expresion in expresiones
    )


def extraer_id_cita(texto: str) -> str | None:
    """Extrae identificadores con formato CITA-..."""

    coincidencia = re.search(
        r"\bCITA-[A-Za-z0-9_-]+\b",
        str(texto),
        flags=re.IGNORECASE,
    )

    if not coincidencia:
        return None

    return coincidencia.group(0).upper()


def convertir_cita_a_respuesta(
    resultado: dict[str, Any],
    id_solicitado: str,
) -> dict[str, Any]:
    """Convierte la respuesta de n8n en una tarjeta de MediAssist."""

    cita = resultado.get("cita")

    if not resultado.get("encontrada") or not isinstance(cita, dict):
        return {
            "tipo": "cita",
            "titulo": "Cita no encontrada",
            "mensaje": (
                "No encontré una cita registrada con ese ID."
            ),
            "datos": [
                {
                    "emoji": "🆔",
                    "etiqueta": "ID consultado",
                    "valor": id_solicitado,
                }
            ],
            "advertencia": (
                "Verifica que el ID esté escrito exactamente "
                "como aparece en tu comprobante."
            ),
            "pregunta_final": (
                "¿Quieres intentar con otro ID?"
            ),
        }

    def obtener(*claves: str, predeterminado: str = "No disponible") -> str:
        for clave in claves:
            valor = cita.get(clave)
            if valor not in (None, ""):
                return str(valor)
        return predeterminado

    return {
        "tipo": "cita",
        "titulo": "Información de tu cita",
        "mensaje": (
            "Encontré la siguiente cita en el registro del hospital."
        ),
        "datos": [
            {
                "emoji": "🩺",
                "etiqueta": "Especialidad",
                "valor": obtener("Especialidad", "especialidad"),
            },
            {
                "emoji": "📅",
                "etiqueta": "Fecha",
                "valor": obtener("Fecha Cita", "fecha", "Fecha"),
            },
            {
                "emoji": "🕐",
                "etiqueta": "Hora",
                "valor": obtener("Hora", "hora"),
            },
            {
                "emoji": "👤",
                "etiqueta": "Paciente",
                "valor": obtener("Paciente", "paciente"),
            },
            {
                "emoji": "📱",
                "etiqueta": "Teléfono",
                "valor": obtener("Teléfono", "Telefono", "telefono"),
            },
            {
                "emoji": "📌",
                "etiqueta": "Estado",
                "valor": obtener("Estado", "estado"),
            },
            {
                "emoji": "🆔",
                "etiqueta": "ID de cita",
                "valor": obtener("ID", "id", predeterminado=id_solicitado),
            },
        ],
        "pregunta_final": (
            "¿Puedo ayudarte con otra consulta?"
        ),
    }


# ==================================================
# FUNCIONES DE INTERFAZ
# ==================================================

def escapar_texto(valor: Any) -> str:
    """
    Evita que contenido recibido se interprete
    como HTML peligroso.
    """

    if valor is None:
        return ""

    return html.escape(
        str(valor),
        quote=True,
    )


def obtener_icono_modulo(tipo: str | None) -> str:
    """
    Devuelve un icono de acuerdo con el módulo utilizado.
    """

    iconos = {
        "estudio": "🧪",
        "medico": "🩺",
        "medicos_especialidad": "👨‍⚕️",
        "medicos_sin_especialidad": "👨‍⚕️",
        "precio": "💳",
        "precio_sin_servicio": "💳",
        "faq": "💬",
        "cita": "📅",
        "estudio_no_detectado": "🧪",
        "no_encontrado": "🔎",
    }

    return iconos.get(
        str(tipo),
        "🩺",
    )


def obtener_color_modulo(tipo: str | None) -> str:
    """
    Devuelve el color de acento (borde izquierdo) de la tarjeta
    según el módulo. Puramente visual, no afecta la lógica.
    """

    colores = {
        "estudio": "#0F766E",
        "estudio_no_detectado": "#0F766E",
        "medico": "#0F766E",
        "medicos_especialidad": "#0F766E",
        "medicos_sin_especialidad": "#0F766E",
        "precio": "#0F766E",
        "precio_sin_servicio": "#0F766E",
        "faq": "#0F766E",
        "cita": "#B45309",
        "no_encontrado": "#5B6B68",
    }

    return colores.get(
        str(tipo),
        "#0F766E",
    )


def nombre_amigable_modulo(tipo: str | None) -> str:
    """
    Convierte el nombre técnico del router en texto amigable.
    """

    nombres = {
        "estudio": "Estudios",
        "medico": "Médico",
        "medicos_especialidad": "Especialistas",
        "medicos_sin_especialidad": "Médicos",
        "precio": "Precios",
        "precio_sin_servicio": "Precios",
        "faq": "Preguntas frecuentes",
        "cita": "Agendamiento de citas",
        "estudio_no_detectado": "Estudios",
        "no_encontrado": "Búsqueda general",
    }

    return nombres.get(
        str(tipo),
        "Atención hospitalaria",
    )


def mostrar_respuesta_estructurada(
    respuesta: dict[str, Any],
    metadata: dict[str, Any] | None = None,
) -> None:
    """
    Muestra el JSON de Gemini como una tarjeta con acento clínico.
    'metadata' se conserva por compatibilidad con la lógica existente,
    pero solo se usa aquí para elegir icono/color; nunca se imprime
    información técnica (módulo, confianza, memoria) en la interfaz.
    """

    titulo = (
        respuesta.get("titulo")
        or respuesta.get("título")
        or "MediAssist"
    )

    mensaje = respuesta.get(
        "mensaje",
        "Aquí tienes la información disponible.",
    )

    datos = respuesta.get("datos", [])
    advertencia = respuesta.get("advertencia")
    pregunta_final = respuesta.get("pregunta_final")

    titulo_seguro = escapar_texto(titulo)
    mensaje_seguro = escapar_texto(mensaje)

    icono_tarjeta = "🩺"
    color_acento = "#0F766E"

    if metadata:
        icono_tarjeta = obtener_icono_modulo(metadata.get("tipo"))
        color_acento = obtener_color_modulo(metadata.get("tipo"))

    contenido = [
        f'<div class="response-card" style="--accent:{color_acento};">',
        '<div class="response-header">',
        f'<div class="response-icon">{icono_tarjeta}</div>',
        f'<div class="response-title">{titulo_seguro}</div>',
        "</div>",
        f'<div class="response-message">{mensaje_seguro}</div>',
    ]

    if isinstance(datos, list):
        for dato in datos:
            if not isinstance(dato, dict):
                continue

            emoji = escapar_texto(
                dato.get("emoji", "•")
            )

            etiqueta = escapar_texto(
                dato.get("etiqueta", "Información")
            )

            valor = escapar_texto(
                dato.get("valor", "No disponible")
            )

            contenido.append(
                '<div class="data-row">'
                f"<span>{emoji}</span> "
                f'<span class="data-label">{etiqueta}</span> '
                f'<span class="data-value">{valor}</span>'
                "</div>"
            )

    if advertencia:
        advertencia_segura = escapar_texto(
            advertencia
        )

        contenido.append(
            '<div class="warning-row">'
            "⚠️ <strong>Importante:</strong> "
            f"{advertencia_segura}"
            "</div>"
        )

    if pregunta_final:
        pregunta_segura = escapar_texto(
            pregunta_final
        )

        contenido.append(
            '<div class="final-question">'
            f"↳ {pregunta_segura}"
            "</div>"
        )

    contenido.append("</div>")

    st.markdown(
        "".join(contenido),
        unsafe_allow_html=True,
    )


def mostrar_respuesta_simple(
    texto: str,
    metadata: dict[str, Any] | None = None,
) -> None:
    """
    Muestra una respuesta normal cuando Gemini no devuelve un JSON
    válido. No se muestra información técnica adicional.
    """

    texto = limpiar_bloque_json(texto)

    color_acento = "#0F766E"

    if metadata:
        color_acento = obtener_color_modulo(metadata.get("tipo"))

    st.markdown(
        f'<div class="response-card" style="--accent:{color_acento};">'
        f'<div class="response-message" style="margin-bottom:0;">{texto}</div>'
        "</div>",
        unsafe_allow_html=True,
    )


def crear_mensaje_inicial() -> dict[str, Any]:
    """
    Devuelve el mensaje de bienvenida del chat.
    """

    return {
        "rol": "assistant",
        "texto": (
            "¡Hola! Soy **MediAssist**. 👋\n\n"
            "Puedo ayudarte a consultar estudios, precios, "
            "preparaciones, médicos disponibles, preguntas "
            "frecuentes, agendar citas y consultarlas por ID."
        ),
        "estructurada": None,
        "metadata": None,
    }


def reiniciar_conversacion() -> None:
    """
    Limpia mensajes, memoria y proceso de cita.
    """

    st.session_state.mensajes = [
        crear_mensaje_inicial()
    ]

    st.session_state.memoria_conversacion = (
        crear_memoria_vacia()
    )

    st.session_state.estado_cita = (
        crear_estado_cita_vacio()
    )

    st.session_state.pregunta_pendiente = None
    st.session_state.esperando_id_cita = False


# ==================================================
# INICIALIZAR ESTADO
# ==================================================

if "memoria_conversacion" not in st.session_state:
    st.session_state.memoria_conversacion = (
        crear_memoria_vacia()
    )

if "mensajes" not in st.session_state:
    st.session_state.mensajes = [
        crear_mensaje_inicial()
    ]

if "pregunta_pendiente" not in st.session_state:
    st.session_state.pregunta_pendiente = None

if "estado_cita" not in st.session_state:
    st.session_state.estado_cita = (
        crear_estado_cita_vacio()
    )

if "esperando_id_cita" not in st.session_state:
    st.session_state.esperando_id_cita = False


# ==================================================
# BARRA LATERAL
# ==================================================

with st.sidebar:
    st.markdown(
        """
        <div class="sb-brand">
            <div class="sb-brand-icon">🩺</div>
            <div>
                <p class="sb-brand-title">MediAssist</p>
                <p class="sb-brand-subtitle">Asistente hospitalario</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button(
        "＋  Nueva conversación",
        use_container_width=True,
    ):
        reiniciar_conversacion()
        st.rerun()

    st.markdown(
        '<div class="sb-label">Servicios</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="sb-item">🧪&nbsp;&nbsp;Estudios y preparación</div>
        <div class="sb-item">👨‍⚕️&nbsp;&nbsp;Médicos y especialidades</div>
        <div class="sb-item">💳&nbsp;&nbsp;Precios de servicios</div>
        <div class="sb-item">📅&nbsp;&nbsp;Agendar una cita</div>
        <div class="sb-item">🔎&nbsp;&nbsp;Consultar una cita</div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="sb-status">
            <span class="pulse-dot"></span>
            Sistema disponible
        </div>
        """,
        unsafe_allow_html=True,
    )


# ==================================================
# ENCABEZADO
# ==================================================

st.markdown(
    f"""
    <div class="hero">
        <div class="hero-eyebrow">
            <span class="pulse-dot"></span> MediAssist · en línea
        </div>
        <p class="hero-title">¿Cómo podemos ayudarte hoy?</p>
        <p class="hero-subtitle">
            Consulta información o escribe de forma natural para agendar tu cita.
        </p>
        {PULSO_ECG_SVG}
    </div>
    """,
    unsafe_allow_html=True,
)


# ==================================================
# ACCIONES RÁPIDAS
# ==================================================

st.markdown(
    '<p class="quick-label">Acciones rápidas</p>',
    unsafe_allow_html=True,
)

acciones_rapidas = [
    {
        "icono": "🧪",
        "titulo": "Estudios",
        "descripcion": "Preparación e información de estudios clínicos.",
        "pregunta": "Quiero consultar información de un estudio",
    },
    {
        "icono": "👨‍⚕️",
        "titulo": "Médicos",
        "descripcion": "Especialistas disponibles en el hospital.",
        "pregunta": "¿Qué médicos y especialidades están disponibles?",
    },
    {
        "icono": "💳",
        "titulo": "Precios",
        "descripcion": "Costos de servicios y procedimientos.",
        "pregunta": "Quiero consultar el precio de un servicio",
    },
    {
        "icono": "📅",
        "titulo": "Agendar cita",
        "descripcion": "Reserva tu cita médica en segundos.",
        "pregunta": "Quiero agendar una cita",
    },
    {
        "icono": "🔎",
        "titulo": "Consultar cita",
        "descripcion": "Busca una cita existente por su ID.",
        "pregunta": "Quiero consultar mi cita",
    },
]

columnas_acciones = st.columns(5)

for columna, accion in zip(columnas_acciones, acciones_rapidas):
    with columna:
        with st.container(border=True):
            st.markdown(
                f"""
                <div class="qa-icon">{accion['icono']}</div>
                <p class="qa-title">{accion['titulo']}</p>
                <p class="qa-desc">{accion['descripcion']}</p>
                """,
                unsafe_allow_html=True,
            )

            if st.button(
                "Usar",
                key=f"accion_{accion['titulo']}",
                use_container_width=True,
            ):
                st.session_state.pregunta_pendiente = accion["pregunta"]
                st.rerun()


# ==================================================
# HISTORIAL DEL CHAT
# ==================================================

for mensaje in st.session_state.mensajes:
    avatar = "🩺" if mensaje["rol"] == "assistant" else "🙂"

    with st.chat_message(
        mensaje["rol"],
        avatar=avatar,
    ):
        if mensaje.get("estructurada"):
            mostrar_respuesta_estructurada(
                mensaje["estructurada"],
                mensaje.get("metadata"),
            )
        elif mensaje["rol"] == "user":
            st.markdown(
                f'<div class="bubble-user">{escapar_texto(mensaje.get("texto", ""))}</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                mensaje.get(
                    "texto",
                    "",
                )
            )


# ==================================================
# ENTRADA DEL USUARIO
# ==================================================

pregunta_chat = st.chat_input(
    "Pregunta por estudios, médicos, precios o citas..."
)

pregunta_usuario = (
    pregunta_chat
    or st.session_state.pregunta_pendiente
)

if pregunta_usuario:
    st.session_state.pregunta_pendiente = None

    st.session_state.mensajes.append(
        {
            "rol": "user",
            "texto": pregunta_usuario,
            "estructurada": None,
            "metadata": None,
        }
    )

    with st.chat_message("user", avatar="🙂"):
        st.markdown(
            f'<div class="bubble-user">{escapar_texto(pregunta_usuario)}</div>',
            unsafe_allow_html=True,
        )

    with st.chat_message("assistant", avatar="🩺"):
        with st.spinner(
            "Consultando la información oficial del hospital..."
        ):
            try:
                id_en_mensaje = extraer_id_cita(
                    pregunta_usuario
                )

                quiere_consultar = (
                    usuario_quiere_consultar_cita(
                        pregunta_usuario
                    )
                )

                esperando_id = bool(
                    st.session_state.esperando_id_cita
                )

                # ==================================
                # CONSULTAR UNA CITA EXISTENTE
                # ==================================

                if quiere_consultar and not id_en_mensaje:
                    st.session_state.esperando_id_cita = True

                    respuesta_consulta = {
                        "tipo": "cita",
                        "titulo": "Consultar cita",
                        "mensaje": (
                            "Claro, puedo buscar tu cita en el "
                            "registro del hospital."
                        ),
                        "datos": [],
                        "pregunta_final": (
                            "Escribe el ID de tu cita, por ejemplo: "
                            "CITA-1784609876543."
                        ),
                    }

                    metadata = {
                        "tipo": "cita",
                        "termino_detectado": None,
                        "confianza": 1.0,
                        "uso_memoria": False,
                    }

                    mostrar_respuesta_estructurada(
                        respuesta_consulta,
                        metadata,
                    )

                    st.session_state.mensajes.append(
                        {
                            "rol": "assistant",
                            "texto": "",
                            "estructurada": respuesta_consulta,
                            "metadata": metadata,
                        }
                    )

                elif id_en_mensaje and (
                    esperando_id or quiere_consultar
                ):
                    resultado_consulta = consultar_cita(
                        id_en_mensaje
                    )

                    st.session_state.esperando_id_cita = False

                    respuesta_consulta = (
                        convertir_cita_a_respuesta(
                            resultado_consulta,
                            id_en_mensaje,
                        )
                    )

                    metadata = {
                        "tipo": "cita",
                        "termino_detectado": id_en_mensaje,
                        "confianza": 1.0,
                        "uso_memoria": esperando_id,
                    }

                    mostrar_respuesta_estructurada(
                        respuesta_consulta,
                        metadata,
                    )

                    st.session_state.mensajes.append(
                        {
                            "rol": "assistant",
                            "texto": "",
                            "estructurada": respuesta_consulta,
                            "metadata": metadata,
                        }
                    )

                else:
                    estado_cita = st.session_state.estado_cita

                    cita_activa = bool(
                        estado_cita.get("activa")
                    )

                    iniciar_cita = usuario_quiere_agendar(
                        pregunta_usuario
                    )

                    # ==================================
                    # FLUJO DE AGENDAMIENTO DE CITAS
                    # ==================================

                    if cita_activa or iniciar_cita:
                        respuesta_cita, nuevo_estado = (
                            procesar_agendamiento(
                                mensaje=pregunta_usuario,
                                estado=estado_cita,
                            )
                        )

                        st.session_state.estado_cita = (
                            nuevo_estado
                        )

                        if nuevo_estado.get("confirmada"):
                            resultado_guardado = guardar_cita(
                                nuevo_estado
                            )

                            if resultado_guardado.get("guardada"):
                                respuesta_cita["advertencia"] = (
                                    "La cita fue guardada correctamente "
                                    "en el registro del hospital."
                                )

                                id_cita = (
                                    resultado_guardado.get("id")
                                    or resultado_guardado.get("ID")
                                )

                                if id_cita:
                                    id_cita_limpio = (
                                        str(id_cita)
                                        .replace("}}", "")
                                        .strip()
                                        .upper()
                                    )

                                    respuesta_cita.setdefault(
                                        "datos",
                                        [],
                                    ).append(
                                        {
                                            "emoji": "🆔",
                                            "etiqueta": "ID de cita",
                                            "valor": id_cita_limpio,
                                        }
                                    )

                                    respuesta_cita["advertencia"] = (
                                        "Guarda este ID. Lo necesitarás "
                                        "para consultar tu cita más adelante."
                                    )
                            else:
                                respuesta_cita["advertencia"] = (
                                    "La cita fue confirmada, pero no pudo "
                                    "guardarse en Google Sheets."
                                )

                        metadata = {
                            "tipo": "cita",
                            "termino_detectado": (
                                nuevo_estado.get(
                                    "especialidad"
                                )
                            ),
                            "confianza": 1.0,
                            "uso_memoria": cita_activa,
                        }

                        mostrar_respuesta_estructurada(
                            respuesta_cita,
                            metadata,
                        )

                        st.session_state.mensajes.append(
                            {
                                "rol": "assistant",
                                "texto": "",
                                "estructurada": respuesta_cita,
                                "metadata": metadata,
                            }
                        )

                    # ==================================
                    # CONSULTAS NORMALES
                    # ==================================

                    else:
                        pregunta_para_router, uso_memoria = (
                            resolver_pregunta_con_memoria(
                                pregunta_usuario,
                                st.session_state.memoria_conversacion,
                            )
                        )

                        contexto, resultado_router = (
                            crear_contexto_oficial(
                                pregunta_para_router
                            )
                        )

                        st.session_state.memoria_conversacion = (
                            actualizar_memoria(
                                memoria=(
                                    st.session_state
                                    .memoria_conversacion
                                ),
                                resultado_router=resultado_router,
                                pregunta_original=pregunta_usuario,
                                pregunta_expandida=(
                                    pregunta_para_router
                                ),
                            )
                        )

                        tipo_consulta = resultado_router.get(
                            "tipo",
                            "no_encontrado",
                        )

                        termino_detectado = (
                            resultado_router.get(
                                "termino_detectado"
                            )
                        )

                        confianza = float(
                            resultado_router.get(
                                "confianza",
                                0.0,
                            )
                            or 0.0
                        )

                        texto_respuesta, respuesta_json = (
                            consultar_n8n(
                                pregunta_usuario,
                                contexto,
                            )
                        )

                        metadata = {
                            "tipo": tipo_consulta,
                            "termino_detectado": (
                                termino_detectado
                            ),
                            "confianza": confianza,
                            "uso_memoria": uso_memoria,
                        }

                        if respuesta_json:
                            mostrar_respuesta_estructurada(
                                respuesta_json,
                                metadata,
                            )
                        else:
                            mostrar_respuesta_simple(
                                texto_respuesta,
                                metadata,
                            )

                        st.session_state.mensajes.append(
                            {
                                "rol": "assistant",
                                "texto": texto_respuesta,
                                "estructurada": respuesta_json,
                                "metadata": metadata,
                            }
                        )

            except requests.exceptions.Timeout:
                mensaje_error = (
                    "La consulta tardó demasiado. "
                    "Inténtalo nuevamente en unos momentos. ⏱️"
                )

                st.error(mensaje_error)

                st.session_state.mensajes.append(
                    {
                        "rol": "assistant",
                        "texto": mensaje_error,
                        "estructurada": None,
                        "metadata": None,
                    }
                )

            except requests.exceptions.HTTPError as error:
                mensaje_error = (
                    "No fue posible obtener una respuesta. "
                    "Revisa que el workflow de n8n esté activo."
                )

                st.error(mensaje_error)

                with st.expander(
                    "Ver detalle técnico"
                ):
                    st.code(
                        str(error)
                    )

                st.session_state.mensajes.append(
                    {
                        "rol": "assistant",
                        "texto": mensaje_error,
                        "estructurada": None,
                        "metadata": None,
                    }
                )

            except requests.exceptions.ConnectionError:
                mensaje_error = (
                    "No fue posible conectarse con MediAssist. "
                    "Revisa tu conexión a internet."
                )

                st.error(mensaje_error)

                st.session_state.mensajes.append(
                    {
                        "rol": "assistant",
                        "texto": mensaje_error,
                        "estructurada": None,
                        "metadata": None,
                    }
                )

            except requests.exceptions.RequestException as error:
                mensaje_error = (
                    "Ocurrió un problema al comunicarse con n8n."
                )

                st.error(mensaje_error)

                with st.expander(
                    "Ver detalle técnico"
                ):
                    st.code(
                        str(error)
                    )

            except Exception as error:
                mensaje_error = (
                    "Ocurrió un error inesperado al procesar "
                    "la consulta."
                )

                st.error(mensaje_error)

                with st.expander(
                    "Ver detalle técnico"
                ):
                    st.code(
                        str(error)
                    )


# ==================================================
# AVISO FINAL
# ==================================================

st.markdown(
    """
    <div class="disclaimer">
        MediAssist proporciona información administrativa e informativa.
        No sustituye la valoración, diagnóstico ni indicaciones de un
        profesional de la salud.
    </div>
    """,
    unsafe_allow_html=True,
)