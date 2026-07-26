from __future__ import annotations

from typing import Any

import requests

from config import (
    URL_GUARDAR_CITA,
    URL_CONSULTAR_CITA,
)


def _leer_json_dict(
    respuesta: requests.Response,
) -> dict[str, Any]:
    """Devuelve un diccionario JSON o uno vacío."""

    try:
        contenido = respuesta.json()
    except ValueError:
        return {}

    return contenido if isinstance(contenido, dict) else {}


def _limpiar_id(valor: Any) -> str:
    """Normaliza un ID de cita antes de enviarlo o mostrarlo."""

    return (
        str(valor or "")
        .replace("}}", "")
        .strip()
        .upper()
    )


def guardar_cita(
    estado_cita: dict[str, Any],
) -> dict[str, Any]:
    """Guarda una cita confirmada mediante n8n y Google Sheets."""

    datos = {
        "especialidad": estado_cita.get("especialidad"),
        "fecha": estado_cita.get("fecha"),
        "hora": estado_cita.get("hora"),
        "paciente": estado_cita.get("paciente"),
        "telefono": estado_cita.get("telefono"),
    }

    respuesta = requests.post(
        URL_GUARDAR_CITA,
        json=datos,
        timeout=30,
    )
    respuesta.raise_for_status()

    contenido = _leer_json_dict(respuesta)

    if contenido:
        id_cita = contenido.get("id") or contenido.get("ID")

        if id_cita:
            contenido["id"] = _limpiar_id(id_cita)

        contenido.setdefault("guardada", True)
        return contenido

    return {
        "guardada": True,
        "mensaje": "Cita enviada correctamente.",
    }


def consultar_cita(
    id_cita: str,
) -> dict[str, Any]:
    """Busca una cita por ID mediante n8n y Google Sheets."""

    id_limpio = _limpiar_id(id_cita)

    respuesta = requests.post(
        URL_CONSULTAR_CITA,
        json={"id": id_limpio},
        timeout=30,
    )
    respuesta.raise_for_status()

    contenido = _leer_json_dict(respuesta)

    if contenido:
        cita = contenido.get("cita")

        if isinstance(cita, dict):
            cita["ID"] = _limpiar_id(
                cita.get("ID") or cita.get("id")
            )

        return contenido

    return {
        "encontrada": False,
        "cita": None,
        "mensaje": "n8n no devolvió un JSON válido.",
    }