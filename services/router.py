from __future__ import annotations

import sys
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path

import pandas as pd


# --------------------------------------------------
# CONFIGURACIÓN DE RUTAS
# --------------------------------------------------

BASE = Path(__file__).resolve().parent.parent
CARPETA_SCRIPTS = BASE / "scripts"

if str(CARPETA_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(CARPETA_SCRIPTS))

from consultas import (  # noqa: E402
    buscar_estudio,
    buscar_medicos,
    buscar_precio,
    buscar_pregunta,
    costos,
    estudios,
    faq,
    medicos,
)


# --------------------------------------------------
# PALABRAS RELACIONADAS CON CADA MÓDULO
# --------------------------------------------------

PALABRAS_MEDICOS = {
    "medico",
    "medica",
    "doctor",
    "doctora",
    "doctores",
    "especialista",
    "especialistas",
    "consultorio",
    "cardiologo",
    "cardiologa",
    "pediatra",
    "traumatologo",
    "traumatologa",
    "ginecologo",
    "ginecologa",
    "dermatologo",
    "dermatologa",
    "neurologo",
    "neurologa",
}

PALABRAS_ESTUDIOS = {
    "estudio",
    "estudios",
    "analisis",
    "examen",
    "prueba",
    "laboratorio",
    "radiografia",
    "resonancia",
    "tomografia",
    "ultrasonido",
    "mastografia",
    "biometria",
    "sangre",
    "orina",
    "ayuno",
    "preparacion",
    "resultados",
    "orden medica",
}

PALABRAS_PRECIOS = {
    "precio",
    "precios",
    "cuanto cuesta",
    "cuanto sale",
    "costo",
    "costos",
    "tarifa",
    "valor",
    "pagar",
}

PALABRAS_FAQ = {
    "horario",
    "horarios",
    "abren",
    "cierran",
    "ubicacion",
    "direccion",
    "telefono",
    "contacto",
    "estacionamiento",
    "visitas",
    "visitantes",
    "factura",
    "facturacion",
    "tarjeta",
    "efectivo",
    "pago",
    "pagos",
    "cancelacion",
    "cancelar",
    "reembolso",
    "acompañante",
    "menores",
}



PALABRAS_SALUDOS = {
    "hola", "holi", "hey", "buenas", "buenos dias",
    "buenas tardes", "buenas noches", "que tal", "saludos",
}

PALABRAS_AGRADECIMIENTO = {
    "gracias", "muchas gracias", "te agradezco", "muy amable",
}

PALABRAS_DESPEDIDA = {
    "adios", "hasta luego", "nos vemos", "hasta pronto", "bye",
}

PALABRAS_AYUDA_GENERAL = {
    "ayuda", "menu", "opciones", "que puedes hacer",
    "como puedes ayudarme", "quien eres", "que haces",
}

PALABRAS_AGENDAR_CITA = {
    "agendar cita", "hacer una cita", "sacar una cita",
    "reservar cita", "quiero una cita", "necesito una cita",
}

PALABRAS_CONSULTAR_CITA = {
    "consultar cita", "ver mi cita", "buscar mi cita",
    "revisar mi cita", "tengo una cita",
}

PALABRAS_CANCELAR_CITA = {
    "cancelar cita", "cancelar mi cita", "eliminar cita", "anular cita",
}


# --------------------------------------------------
# FUNCIONES AUXILIARES
# --------------------------------------------------

def normalizar_texto(texto: object) -> str:
    """
    Convierte un texto a minúsculas, elimina acentos,
    signos y espacios repetidos.
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


def obtener_textos_columna(
    dataframe: pd.DataFrame,
    columna: str,
) -> list[str]:
    """
    Devuelve los valores válidos de una columna.
    """

    if columna not in dataframe.columns:
        return []

    valores = []

    for valor in dataframe[columna].dropna().tolist():
        texto = str(valor).strip()

        if texto and texto.lower() != "nan":
            valores.append(texto)

    return valores


def calcular_similitud(
    texto_a: str,
    texto_b: str,
) -> float:
    """
    Calcula qué tan parecidos son dos textos.
    """

    return SequenceMatcher(
        None,
        normalizar_texto(texto_a),
        normalizar_texto(texto_b),
    ).ratio()


def buscar_coincidencia_aproximada(
    pregunta: str,
    opciones: list[str],
    limite: float = 0.78,
) -> tuple[str | None, float]:
    """
    Busca una opción dentro de una pregunta.

    También permite errores ortográficos pequeños.
    """

    pregunta_normalizada = normalizar_texto(pregunta)
    palabras_pregunta = pregunta_normalizada.split()

    mejor_opcion = None
    mejor_puntaje = 0.0

    for opcion in opciones:
        opcion_normalizada = normalizar_texto(opcion)

        if not opcion_normalizada:
            continue

        # Coincidencia directa.
        if opcion_normalizada in pregunta_normalizada:
            return opcion, 1.0

        palabras_opcion = opcion_normalizada.split()
        cantidad_palabras = len(palabras_opcion)

        if cantidad_palabras == 0:
            continue

        # Compara fragmentos de la pregunta.
        for posicion in range(
            len(palabras_pregunta) - cantidad_palabras + 1
        ):
            fragmento = " ".join(
                palabras_pregunta[
                    posicion:
                    posicion + cantidad_palabras
                ]
            )

            puntaje = calcular_similitud(
                opcion_normalizada,
                fragmento,
            )

            if puntaje > mejor_puntaje:
                mejor_puntaje = puntaje
                mejor_opcion = opcion

    if mejor_puntaje >= limite:
        return mejor_opcion, mejor_puntaje

    return None, mejor_puntaje


def contiene_alguna_palabra(
    pregunta: str,
    palabras: set[str],
) -> bool:
    """
    Comprueba si la pregunta contiene alguna palabra
    relacionada con un módulo.
    """

    pregunta_normalizada = normalizar_texto(pregunta)

    return any(
        normalizar_texto(palabra) in pregunta_normalizada
        for palabra in palabras
    )


def coincide_expresion(
    pregunta: str,
    expresiones: set[str],
) -> bool:
    """Comprueba coincidencias conversacionales."""

    pregunta_normalizada = normalizar_texto(pregunta)

    for expresion in expresiones:
        expresion_normalizada = normalizar_texto(expresion)

        if (
            pregunta_normalizada == expresion_normalizada
            or expresion_normalizada in pregunta_normalizada
        ):
            return True

    return False


# --------------------------------------------------
# DETECTORES DE INFORMACIÓN
# --------------------------------------------------

def detectar_estudio(
    pregunta: str,
) -> tuple[str | None, float]:
    """
    Detecta un estudio registrado en el Excel.
    """

    opciones = obtener_textos_columna(
        estudios,
        "Nombre_Estudio",
    )

    return buscar_coincidencia_aproximada(
        pregunta,
        opciones,
        limite=0.76,
    )


def detectar_especialidad(
    pregunta: str,
) -> tuple[str | None, float]:
    """
    Detecta una especialidad médica registrada.
    """

    opciones = obtener_textos_columna(
        medicos,
        "Especialidad",
    )

    return buscar_coincidencia_aproximada(
        pregunta,
        opciones,
        limite=0.76,
    )


def detectar_medico(
    pregunta: str,
) -> tuple[str | None, float]:
    """
    Detecta el nombre de un médico registrado.
    """

    opciones = obtener_textos_columna(
        medicos,
        "Nombre_Completo",
    )

    return buscar_coincidencia_aproximada(
        pregunta,
        opciones,
        limite=0.74,
    )


def detectar_servicio(
    pregunta: str,
) -> tuple[str | None, float]:
    """
    Detecta un servicio registrado en la hoja Costos.
    """

    opciones = obtener_textos_columna(
        costos,
        "Servicio",
    )

    return buscar_coincidencia_aproximada(
        pregunta,
        opciones,
        limite=0.76,
    )


# --------------------------------------------------
# CONSULTA DE MÉDICO POR NOMBRE
# --------------------------------------------------

def buscar_medico_por_nombre(
    nombre_medico: str,
) -> str:
    """
    Devuelve la información disponible de un médico
    buscando por su nombre completo.
    """

    nombre_normalizado = normalizar_texto(nombre_medico)

    resultado = medicos[
        medicos["Nombre_Completo"]
        .astype(str)
        .apply(
            lambda valor: nombre_normalizado
            in normalizar_texto(valor)
        )
    ]

    if resultado.empty:
        return (
            f"No se encontró información del médico "
            f"'{nombre_medico}'."
        )

    respuestas = []

    for _, medico in resultado.iterrows():
        partes = [
            f"Médico: {medico.get('Nombre_Completo', 'No disponible')}",
            f"Especialidad: {medico.get('Especialidad', 'No disponible')}",
            f"Consultorio: {medico.get('Consultorio', 'No disponible')}",
            f"Estado: {medico.get('Estado', 'No disponible')}",
        ]

        columnas_opcionales = {
            "Horario": "Horario",
            "Dias_Atencion": "Días de atención",
            "Telefono": "Teléfono",
            "Correo": "Correo",
        }

        for columna, etiqueta in columnas_opcionales.items():
            if columna in medicos.columns:
                valor = medico.get(columna)

                if pd.notna(valor):
                    partes.append(
                        f"{etiqueta}: {str(valor).strip()}"
                    )

        respuestas.append("\n".join(partes))

    return "\n\n".join(respuestas)


# --------------------------------------------------
# ROUTER PRINCIPAL
# --------------------------------------------------

def filtrar_contexto_estudio(
    pregunta: str,
    contexto_completo: str,
) -> str:
    """
    Devuelve únicamente la información que el usuario pidió.

    Si no identifica un dato específico, devuelve la ficha completa.
    """

    pregunta_normalizada = normalizar_texto(pregunta)

    # Las intenciones más específicas van primero.
    mapa_campos = [
        (
            "Horas de ayuno",
            [
                "cuantas horas de ayuno",
                "horas de ayuno",
                "cuanto ayuno",
            ],
        ),
        (
            "Precio",
            [
                "cuanto cuesta",
                "precio",
                "costo",
                "cuanto sale",
                "cuanto vale",
            ],
        ),
        (
            "Preparación",
            [
                "preparacion",
                "como me preparo",
                "que preparacion necesito",
            ],
        ),
        (
            "Requiere ayuno",
            [
                "requiere ayuno",
                "necesita ayuno",
                "debo ir en ayuno",
                "ayuno",
            ],
        ),
        (
            "Duración aproximada",
            [
                "cuanto tarda",
                "duracion",
                "cuanto dura",
                "tiempo tarda",
            ],
        ),
        (
            "Entrega de resultados",
            [
                "cuando entregan",
                "entrega de resultados",
                "cuanto tardan los resultados",
                "resultados",
            ],
        ),
        (
            "Requiere orden médica",
            [
                "orden medica",
                "requiere orden",
                "necesita orden",
            ],
        ),
        (
            "Recomendaciones",
            [
                "recomendacion",
                "recomendaciones",
                "que me recomiendan",
            ],
        ),
        (
            "Documentos necesarios",
            [
                "documentos",
                "que necesito llevar",
                "que debo llevar",
            ],
        ),
    ]

    campo_detectado = None

    for campo, expresiones in mapa_campos:
        for expresion in expresiones:
            expresion_normalizada = normalizar_texto(
                expresion
            )

            if expresion_normalizada in pregunta_normalizada:
                campo_detectado = campo
                break

        if campo_detectado:
            break

    # Si la pregunta no solicita un dato específico,
    # se conserva toda la información.
    if campo_detectado is None:
        return contexto_completo

    lineas = [
        linea.strip()
        for linea in contexto_completo.splitlines()
        if linea.strip()
    ]

    nombre_estudio = "Estudio: No disponible"

    for linea in lineas:
        if normalizar_texto(linea).startswith("estudio"):
            nombre_estudio = linea
            break

    campo_normalizado = normalizar_texto(
        campo_detectado
    )

    for linea in lineas:
        etiqueta_linea = linea.split(":", 1)[0]
        etiqueta_normalizada = normalizar_texto(
            etiqueta_linea
        )

        if etiqueta_normalizada == campo_normalizado:
            return (
                f"{nombre_estudio}\n"
                f"{linea}"
            )

    return contexto_completo


def procesar_pregunta(pregunta: str) -> dict[str, object]:
    """
    Decide qué módulo debe atender la pregunta.

    Devuelve:
    - tipo
    - termino_detectado
    - confianza
    - contexto
    """

    pregunta = pregunta.strip()

    if not pregunta:
        return {
            "tipo": "sin_pregunta",
            "termino_detectado": None,
            "confianza": 0.0,
            "contexto": (
                "El usuario no escribió ninguna pregunta."
            ),
        }

    # ----------------------------------------------
    # 0. CONVERSACIÓN GENERAL Y ACCIONES DE CITAS
    # ----------------------------------------------
    #
    # El router no redacta respuestas sociales. Solo indica
    # si Gemini puede conversar libremente o si debe iniciar
    # una acción controlada por el sistema.

    if coincide_expresion(
        pregunta,
        PALABRAS_AGENDAR_CITA,
    ):
        return {
            "tipo": "agendar_cita",
            "termino_detectado": "agendar cita",
            "confianza": 1.0,
            "contexto": (
                "Intención detectada: el usuario desea agendar una cita. "
                "Todavía no existe confirmación de registro. Conversa de "
                "forma natural para reunir únicamente los datos faltantes: "
                "nombre del paciente, teléfono, especialidad o médico, "
                "fecha y hora. No inventes disponibilidad ni confirmes la "
                "cita hasta que el sistema devuelva un folio real."
            ),
        }

    if coincide_expresion(
        pregunta,
        PALABRAS_CONSULTAR_CITA,
    ):
        return {
            "tipo": "consultar_cita",
            "termino_detectado": "consultar cita",
            "confianza": 1.0,
            "contexto": (
                "Intención detectada: el usuario desea consultar una cita. "
                "Solicita de forma natural el folio requerido por el sistema. "
                "No inventes citas ni estados."
            ),
        }

    if coincide_expresion(
        pregunta,
        PALABRAS_CANCELAR_CITA,
    ):
        return {
            "tipo": "cancelar_cita",
            "termino_detectado": "cancelar cita",
            "confianza": 1.0,
            "contexto": (
                "Intención detectada: el usuario desea cancelar una cita. "
                "Primero solicita el identificador necesario. No afirmes "
                "que fue cancelada sin confirmación real del sistema."
            ),
        }

    # Mensajes sociales o conversacionales no necesitan consultar
    # el documento. Gemini decide la redacción y el tono.
    if (
        coincide_expresion(pregunta, PALABRAS_SALUDOS)
        or coincide_expresion(pregunta, PALABRAS_AGRADECIMIENTO)
        or coincide_expresion(pregunta, PALABRAS_DESPEDIDA)
        or coincide_expresion(pregunta, PALABRAS_AYUDA_GENERAL)
    ):
        return {
            "tipo": "conversacion_general",
            "termino_detectado": None,
            "confianza": 1.0,
            "contexto": (
                "No se requiere consultar el documento para este mensaje. "
                "Responde directamente de forma natural, profesional, breve "
                "y coherente con la conversación."
            ),
        }

    # ----------------------------------------------
    # 1. DETECTAR ESTUDIO
    # ----------------------------------------------

    estudio_detectado, puntaje_estudio = detectar_estudio(
        pregunta
    )

    if estudio_detectado:
        contexto_completo = buscar_estudio(
            estudio_detectado
        )

        contexto_filtrado = filtrar_contexto_estudio(
            pregunta,
            contexto_completo,
        )

        return {
            "tipo": "estudio",
            "termino_detectado": estudio_detectado,
            "confianza": round(puntaje_estudio, 3),
            "contexto": contexto_filtrado,
        }

    # ----------------------------------------------
    # 2. DETECTAR MÉDICO POR NOMBRE
    # ----------------------------------------------

    medico_detectado, puntaje_medico = detectar_medico(
        pregunta
    )

    if medico_detectado:
        contexto = buscar_medico_por_nombre(
            medico_detectado
        )

        return {
            "tipo": "medico",
            "termino_detectado": medico_detectado,
            "confianza": round(puntaje_medico, 3),
            "contexto": contexto,
        }

    # ----------------------------------------------
    # 3. DETECTAR ESPECIALIDAD
    # ----------------------------------------------

    especialidad_detectada, puntaje_especialidad = (
        detectar_especialidad(pregunta)
    )

    if especialidad_detectada:
        contexto = buscar_medicos(
            especialidad_detectada
        )

        return {
            "tipo": "medicos_especialidad",
            "termino_detectado": especialidad_detectada,
            "confianza": round(
                puntaje_especialidad,
                3,
            ),
            "contexto": contexto,
        }

    # ----------------------------------------------
    # 4. DETECTAR PRECIO O SERVICIO
    # ----------------------------------------------

    servicio_detectado, puntaje_servicio = detectar_servicio(
        pregunta
    )

    if servicio_detectado:
        contexto = buscar_precio(
            servicio_detectado
        )

        return {
            "tipo": "precio",
            "termino_detectado": servicio_detectado,
            "confianza": round(puntaje_servicio, 3),
            "contexto": contexto,
        }

    # ----------------------------------------------
    # 5. PREGUNTA RELACIONADA CON MÉDICOS
    # ----------------------------------------------

    if contiene_alguna_palabra(
        pregunta,
        PALABRAS_MEDICOS,
    ):
        return {
            "tipo": "medicos_sin_especialidad",
            "termino_detectado": None,
            "confianza": 0.5,
            "contexto": (
                "El usuario pregunta por médicos, pero no se "
                "detectó una especialidad ni un nombre registrado. "
                "Solicita que indique la especialidad o el nombre "
                "del médico que desea consultar."
            ),
        }

    # ----------------------------------------------
    # 6. PREGUNTA RELACIONADA CON ESTUDIOS
    # ----------------------------------------------

    if contiene_alguna_palabra(
        pregunta,
        PALABRAS_ESTUDIOS,
    ):
        return {
            "tipo": "estudio_no_detectado",
            "termino_detectado": None,
            "confianza": 0.5,
            "contexto": (
                "El usuario pregunta por un estudio, pero no se "
                "detectó un estudio registrado en la base de datos. "
                "Solicita que escriba el nombre del estudio."
            ),
        }

    # ----------------------------------------------
    # 7. PREGUNTA DE PRECIO SIN SERVICIO DETECTADO
    # ----------------------------------------------

    if contiene_alguna_palabra(
        pregunta,
        PALABRAS_PRECIOS,
    ):
        return {
            "tipo": "precio_sin_servicio",
            "termino_detectado": None,
            "confianza": 0.5,
            "contexto": (
                "El usuario solicita un precio, pero no se detectó "
                "el nombre de un estudio, consulta o servicio "
                "registrado. Solicita que indique el servicio."
            ),
        }

    # ----------------------------------------------
    # 8. PREGUNTAS FRECUENTES
    # ----------------------------------------------

    contexto_faq = buscar_pregunta(
        pregunta
    )

    if not contexto_faq.startswith(
        "No encontré una respuesta"
    ):
        return {
            "tipo": "faq",
            "termino_detectado": pregunta,
            "confianza": 0.7,
            "contexto": contexto_faq,
        }

    # Segundo intento usando palabras individuales.
    palabras = normalizar_texto(pregunta).split()

    palabras_ignoradas = {
        "que",
        "como",
        "cuando",
        "donde",
        "cual",
        "cuanto",
        "cuantos",
        "cuesta",
        "tienen",
        "tiene",
        "para",
        "una",
        "uno",
        "unos",
        "unas",
        "del",
        "las",
        "los",
        "por",
        "con",
        "sin",
        "hay",
    }

    for palabra in palabras:
        if (
            len(palabra) < 4
            or palabra in palabras_ignoradas
        ):
            continue

        resultado_faq = buscar_pregunta(
            palabra
        )

        if not resultado_faq.startswith(
            "No encontré una respuesta"
        ):
            return {
                "tipo": "faq",
                "termino_detectado": palabra,
                "confianza": 0.6,
                "contexto": resultado_faq,
            }

    # ----------------------------------------------
    # 9. CONSULTA NO ENCONTRADA
    # ----------------------------------------------

    return {
        "tipo": "consulta_general_no_encontrada",
        "termino_detectado": None,
        "confianza": 0.0,
        "contexto": (
            "No se encontró información oficial del hospital relacionada "
            "con la consulta. Responde de manera amable y pide al usuario "
            "que reformule o indique el médico, especialidad, estudio, "
            "servicio o trámite que desea consultar. No inventes precios, "
            "médicos, horarios, disponibilidad ni datos clínicos."
        ),
    }


def crear_contexto_oficial(
    pregunta: str,
) -> tuple[str, dict[str, object]]:
    """
    Crea el contexto que será enviado a Gemini.

    También devuelve los datos internos del router.
    """

    resultado = procesar_pregunta(
        pregunta
    )

    contexto = str(
        resultado["contexto"]
    ).strip()

    contexto_oficial = (
        "Información oficial disponible para responder:\n"
        f"{contexto}"
    )

    return contexto_oficial, resultado