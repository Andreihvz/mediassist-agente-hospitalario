from __future__ import annotations

import unicodedata
from typing import Any


# --------------------------------------------------
# PALABRAS QUE INDICAN UNA PREGUNTA DE SEGUIMIENTO
# --------------------------------------------------

PALABRAS_SEGUIMIENTO = {
    "y cuanto",
    "y cuánto",
    "cuanto tarda",
    "cuánto tarda",
    "cuanto cuesta",
    "cuánto cuesta",
    "necesita ayuno",
    "requiere ayuno",
    "que necesito",
    "qué necesito",
    "que documentos",
    "qué documentos",
    "necesita orden",
    "requiere orden",
    "cuando entregan",
    "cuándo entregan",
    "donde esta",
    "dónde está",
    "en que consultorio",
    "en qué consultorio",
    "esta disponible",
    "está disponible",
    "que horario tiene",
    "qué horario tiene",
    "y el precio",
    "y la preparacion",
    "y la preparación",
    "y los resultados",
    "y su horario",
    "y su consultorio",
    "y esta disponible",
    "y está disponible",
}


# --------------------------------------------------
# FUNCIONES AUXILIARES
# --------------------------------------------------

def normalizar_texto(texto: object) -> str:
    """
    Convierte el texto a minúsculas y elimina acentos
    y signos especiales.
    """

    texto = str(texto).lower().strip()

    texto_normalizado = unicodedata.normalize(
        "NFD",
        texto,
    )

    texto_sin_acentos = "".join(
        caracter
        for caracter in texto_normalizado
        if unicodedata.category(caracter) != "Mn"
    )

    texto_limpio = "".join(
        caracter
        if caracter.isalnum() or caracter.isspace()
        else " "
        for caracter in texto_sin_acentos
    )

    return " ".join(texto_limpio.split())


def crear_memoria_vacia() -> dict[str, Any]:
    """
    Crea la estructura inicial de memoria.
    """

    return {
        "ultimo_tipo": None,
        "ultimo_termino": None,
        "ultima_pregunta": None,
        "pregunta_expandida": None,
    }


def es_pregunta_de_seguimiento(
    pregunta: str,
) -> bool:
    """
    Comprueba si la pregunta parece continuar
    una conversación anterior.
    """

    pregunta_normalizada = normalizar_texto(
        pregunta
    )

    if not pregunta_normalizada:
        return False

    # Frases comunes de seguimiento.
    for frase in PALABRAS_SEGUIMIENTO:
        frase_normalizada = normalizar_texto(
            frase
        )

        if frase_normalizada in pregunta_normalizada:
            return True

    palabras = pregunta_normalizada.split()

    # Preguntas cortas suelen depender del contexto anterior.
    if len(palabras) <= 5:
        palabras_contextuales = {
            "precio",
            "cuesta",
            "tarda",
            "duracion",
            "ayuno",
            "documentos",
            "orden",
            "preparacion",
            "resultados",
            "horario",
            "consultorio",
            "disponible",
            "ubicacion",
        }

        if any(
            palabra in palabras_contextuales
            for palabra in palabras
        ):
            return True

    # Preguntas que comienzan con conectores.
    comienzos_contextuales = (
        "y ",
        "entonces ",
        "tambien ",
        "también ",
        "pero ",
        "ademas ",
        "además ",
    )

    return pregunta_normalizada.startswith(
        comienzos_contextuales
    )


# --------------------------------------------------
# RESOLVER PREGUNTA CON MEMORIA
# --------------------------------------------------

def resolver_pregunta_con_memoria(
    pregunta: str,
    memoria: dict[str, Any],
) -> tuple[str, bool]:
    """
    Agrega el último elemento detectado cuando la pregunta
    depende del contexto anterior.

    Ejemplo:

    Pregunta original:
    ¿Y cuánto tarda?

    Pregunta expandida:
    ¿Y cuánto tarda? Sobre Resonancia Magnética
    """

    pregunta = pregunta.strip()

    ultimo_termino = memoria.get(
        "ultimo_termino"
    )

    if not ultimo_termino:
        return pregunta, False

    if not es_pregunta_de_seguimiento(
        pregunta
    ):
        return pregunta, False

    pregunta_normalizada = normalizar_texto(
        pregunta
    )

    termino_normalizado = normalizar_texto(
        ultimo_termino
    )

    # Evita agregar dos veces el mismo término.
    if termino_normalizado in pregunta_normalizada:
        return pregunta, False

    pregunta_expandida = (
        f"{pregunta} "
        f"Sobre {ultimo_termino}."
    )

    return pregunta_expandida, True


# --------------------------------------------------
# ACTUALIZAR MEMORIA
# --------------------------------------------------

def actualizar_memoria(
    memoria: dict[str, Any],
    resultado_router: dict[str, Any],
    pregunta_original: str,
    pregunta_expandida: str,
) -> dict[str, Any]:
    """
    Actualiza la memoria utilizando el resultado del router.
    """

    memoria_actualizada = dict(memoria)

    tipo = resultado_router.get(
        "tipo"
    )

    termino = resultado_router.get(
        "termino_detectado"
    )

    tipos_recordables = {
        "estudio",
        "medico",
        "medicos_especialidad",
        "precio",
    }

    if tipo in tipos_recordables and termino:
        memoria_actualizada["ultimo_tipo"] = tipo
        memoria_actualizada["ultimo_termino"] = termino

    memoria_actualizada["ultima_pregunta"] = (
        pregunta_original
    )

    memoria_actualizada["pregunta_expandida"] = (
        pregunta_expandida
    )

    return memoria_actualizada


def limpiar_memoria() -> dict[str, Any]:
    """
    Elimina el contexto conversacional guardado.
    """

    return crear_memoria_vacia()