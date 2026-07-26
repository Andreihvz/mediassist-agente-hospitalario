from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Any

import pandas as pd
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import URL_CHAT
from scripts.consultas import (
    cargar_datos,
    medicos,
    estudios,
    costos,
    buscar_precio,
    buscar_pregunta,
)


app = FastAPI(
    title="MediAssist API",
    description="Backend para la aplicación MediAssist",
    version="1.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class MensajeChat(BaseModel):
    mensaje: str
    sesion_id: str = "usuario-principal"


def extraer_texto_respuesta(respuesta_json: Any) -> str:
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


def consultar_n8n(
    pregunta: str,
    sesion_id: str,
) -> str:
    respuesta = requests.post(
        URL_CHAT,
        json={
            "mensaje": pregunta,
            "sesion_id": sesion_id,
        },
        timeout=60,
    )

    respuesta.raise_for_status()

    try:
        contenido_respuesta = respuesta.json()
        texto = extraer_texto_respuesta(contenido_respuesta)
    except ValueError:
        texto = respuesta.text

    texto = str(texto).strip()

    if not texto:
        raise ValueError("Gemini devolvió una respuesta vacía.")

    return texto


@app.get("/")
def inicio() -> dict[str, str]:
    return {
        "estado": "activo",
        "mensaje": "La API de MediAssist está funcionando.",
    }


@app.get("/api/salud")
def comprobar_salud() -> dict[str, object]:
    return {
        "ok": True,
        "servicio": "MediAssist",
        "mensaje": "React puede comunicarse con Python.",
    }


@app.get("/api/medicos")
def obtener_medicos(
    especialidad: str | None = None,
    solo_disponibles: bool = False,
) -> dict[str, Any]:
    resultado = medicos.copy()

    if especialidad:
        resultado = resultado[
            resultado["Especialidad"]
            .astype(str)
            .str.contains(
                especialidad.strip(),
                case=False,
                na=False,
                regex=False,
            )
        ]

    if solo_disponibles:
        resultado = resultado[
            resultado["Estado"]
            .astype(str)
            .str.strip()
            .str.lower()
            == "disponible"
        ]

    lista_medicos: list[dict[str, str]] = []

    for _, medico in resultado.iterrows():
        def valor_seguro(columna: str) -> str:
            valor = medico.get(columna)

            if pd.isna(valor):
                return "No disponible"

            return str(valor).strip()

        lista_medicos.append(
            {
                "id": valor_seguro("ID_Medico"),
                "nombre": valor_seguro("Nombre_Completo"),
                "especialidad": valor_seguro("Especialidad"),
                "consultorio": valor_seguro("Consultorio"),
                "telefono_interno": valor_seguro("Telefono_Interno"),
                "correo": valor_seguro("Correo"),
                "estado": valor_seguro("Estado"),
            }
        )

    especialidades = sorted(
        {
            medico["especialidad"]
            for medico in lista_medicos
            if medico["especialidad"] != "No disponible"
        }
    )

    return {
        "ok": True,
        "total": len(lista_medicos),
        "especialidades": especialidades,
        "medicos": lista_medicos,
    }


@app.get("/api/estudios")
def obtener_estudios() -> dict[str, Any]:
    lista_estudios: list[dict[str, str]] = []

    for _, estudio in estudios.iterrows():

        def valor_seguro(fila: pd.Series, columna: str) -> str:
            valor = fila.get(columna)

            if pd.isna(valor):
                return "No disponible"

            return str(valor).strip()

        nombre_estudio = valor_seguro(estudio, "Nombre_Estudio")

        nombre_busqueda = nombre_estudio.strip().lower()

        if nombre_busqueda == "ultrasonido abdominal":
            nombre_busqueda = "ultrasonido"

        costo_encontrado = costos[
            costos["Servicio"]
            .astype(str)
            .str.strip()
            .str.lower()
            == nombre_busqueda
        ]

        precio = "No disponible"

        if not costo_encontrado.empty:
            precio_valor = costo_encontrado.iloc[0].get("Precio_MXN")

            if not pd.isna(precio_valor):
                try:
                    precio = f"${float(precio_valor):,.2f} MXN"
                except (TypeError, ValueError):
                    precio = str(precio_valor).strip()

        duracion_valor = estudio.get("Duracion_Min")
        duracion = "No disponible"

        if not pd.isna(duracion_valor):
            try:
                duracion = f"{int(float(duracion_valor))} minutos"
            except (TypeError, ValueError):
                duracion = str(duracion_valor).strip()

        lista_estudios.append(
            {
                "id": valor_seguro(estudio, "ID_Estudio"),
                "nombre": nombre_estudio,
                "categoria": valor_seguro(estudio, "Categoria"),
                "precio": precio,
                "duracion": duracion,
                "preparacion": valor_seguro(estudio, "Preparacion"),
                "requiere_ayuno": valor_seguro(estudio, "Requiere_Ayuno"),
                "horas_ayuno": valor_seguro(estudio, "Horas_Ayuno"),
                "requiere_orden_medica": valor_seguro(
                    estudio, "Requiere_Orden_Medica"
                ),
                "entrega_resultados": valor_seguro(
                    estudio, "Entrega_Resultados"
                ),
                "recomendaciones": valor_seguro(estudio, "Recomendaciones"),
                "documentos_necesarios": valor_seguro(
                    estudio, "Documentos_Necesarios"
                ),
            }
        )

    return {
        "ok": True,
        "total": len(lista_estudios),
        "estudios": lista_estudios,
    }


@app.get("/api/precios")
def obtener_precio(servicio: str) -> dict[str, Any]:
    """
    Busca el precio de un servicio, estudio o consulta.
    Ejemplo de uso: /api/precios?servicio=resonancia
    """

    resultado = buscar_precio(servicio)

    return {
        "ok": True,
        "resultado": resultado,
    }


@app.get("/api/faq/buscar")
def buscar_en_faq(query: str) -> dict[str, Any]:
    """
    Busca en preguntas frecuentes.
    Ejemplo de uso: /api/faq/buscar?query=horario
    """

    resultado = buscar_pregunta(query)

    return {
        "ok": True,
        "resultado": resultado,
    }


@app.get("/api/faq")
def obtener_faq():
    datos = cargar_datos()
    faq = datos["faq"]

    preguntas = []

    for _, fila in faq.iterrows():
        preguntas.append({
            "id": str(fila.iloc[0]),
            "categoria": str(fila.iloc[1]),
            "pregunta": str(fila.iloc[2]),
            "respuesta": str(fila.iloc[3]),
        })

    return {
        "faq": preguntas
    }


@app.post("/api/chat")
def procesar_chat(datos: MensajeChat) -> dict[str, Any]:
    pregunta = datos.mensaje.strip()

    if not pregunta:
        raise HTTPException(
            status_code=400,
            detail="El mensaje no puede estar vacío.",
        )

    try:
        texto = consultar_n8n(
            pregunta,
            datos.sesion_id,
        )

        return {
            "ok": True,
            "respuesta": texto,
        }

    except requests.exceptions.Timeout as error:
        raise HTTPException(
            status_code=504,
            detail="La consulta tardó demasiado.",
        ) from error

    except requests.exceptions.ConnectionError as error:
        raise HTTPException(
            status_code=503,
            detail="No fue posible conectarse con n8n.",
        ) from error

    except requests.exceptions.HTTPError as error:
        raise HTTPException(
            status_code=502,
            detail="n8n respondió con un error.",
        ) from error

    except requests.exceptions.RequestException as error:
        raise HTTPException(
            status_code=502,
            detail="Ocurrió un problema al comunicarse con n8n.",
        ) from error

    except Exception as error:
        print(f"Error interno en /api/chat: {error}")

        raise HTTPException(
            status_code=500,
            detail="Ocurrió un error interno en MediAssist.",
        ) from error


@app.delete("/api/chat/{sesion_id}")
def reiniciar_chat(sesion_id: str) -> dict[str, object]:
    return {
        "ok": True,
        "mensaje": "La conversación fue reiniciada (la memoria ahora se maneja en n8n).",
    }


class CitaRequest(BaseModel):
    nombre: str
    telefono: str
    especialidad: str
    medico: str
    fecha: str
    hora: str


CITAS = []


@app.post("/api/citas")
def agendar_cita(cita: CitaRequest):
    folio = f"CIT-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    nueva_cita = {
        "folio": folio,
        "nombre": cita.nombre,
        "telefono": cita.telefono,
        "especialidad": cita.especialidad,
        "medico": cita.medico,
        "fecha": cita.fecha,
        "hora": cita.hora,
        "estado": "Confirmada",
    }

    CITAS.append(nueva_cita)

    return {
        "ok": True,
        "mensaje": "Cita registrada correctamente",
        "folio": folio,
        "cita": nueva_cita,
    }


@app.get("/api/citas/{folio}")
def consultar_cita(folio: str):
    for cita in CITAS:
        if cita["folio"] == folio:
            return {
                "ok": True,
                "cita": cita
            }

    return {
        "ok": False,
        "mensaje": "No se encontró ninguna cita con ese folio."
    }


@app.put("/api/citas/{folio}/cancelar")
def cancelar_cita(folio: str):
    for cita in CITAS:
        if cita["folio"] == folio:
            if cita["estado"] == "Cancelada":
                return {
                    "ok": False,
                    "mensaje": "Esa cita ya estaba cancelada.",
                }

            cita["estado"] = "Cancelada"

            return {
                "ok": True,
                "mensaje": "La cita fue cancelada correctamente.",
                "cita": cita,
            }

    return {
        "ok": False,
        "mensaje": "No se encontró ninguna cita con ese folio.",
    }