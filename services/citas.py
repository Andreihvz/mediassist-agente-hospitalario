from __future__ import annotations

import re
import unicodedata
from datetime import datetime, timedelta
from typing import Any


# ==================================================
# CONFIGURACIÓN
# ==================================================

ESPECIALIDADES_DISPONIBLES = [
    "Cardiología",
    "Dermatología",
    "Ginecología",
    "Medicina General",
    "Neurología",
    "Oftalmología",
    "Ortopedia",
    "Pediatría",
    "Psicología",
    "Traumatología",
]

HORARIOS_DISPONIBLES = [
    "09:00",
    "10:00",
    "11:00",
    "12:00",
    "16:00",
    "17:00",
    "18:00",
]


# ==================================================
# ESTADO DE LA CITA
# ==================================================

def crear_estado_cita_vacio() -> dict[str, Any]:
    """
    Crea la estructura inicial del proceso de agendamiento.
    """

    return {
        "activa": False,
        "paso": None,
        "especialidad": None,
        "fecha": None,
        "hora": None,
        "paciente": None,
        "telefono": None,
        "confirmada": False,
    }


def iniciar_agendamiento(
    estado_actual: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Inicia un nuevo proceso de agendamiento.
    """

    estado = crear_estado_cita_vacio()

    estado["activa"] = True
    estado["paso"] = "especialidad"

    return estado


def cancelar_agendamiento() -> dict[str, Any]:
    """
    Cancela y limpia el proceso de cita.
    """

    return crear_estado_cita_vacio()


# ==================================================
# FUNCIONES DE TEXTO
# ==================================================

def normalizar_texto(texto: str) -> str:
    """
    Convierte texto a minúsculas y elimina acentos.
    """

    texto = str(texto).strip().lower()

    texto = unicodedata.normalize(
        "NFD",
        texto,
    )

    texto = "".join(
        caracter
        for caracter in texto
        if unicodedata.category(caracter) != "Mn"
    )

    texto = re.sub(
        r"\s+",
        " ",
        texto,
    )

    return texto.strip()


def usuario_quiere_agendar(texto: str) -> bool:
    """
    Detecta si el usuario quiere comenzar una cita.
    """

    texto_normalizado = normalizar_texto(texto)

    expresiones = [
        "agendar cita",
        "agendar una cita",
        "quiero una cita",
        "quiero agendar",
        "necesito una cita",
        "sacar una cita",
        "hacer una cita",
        "reservar cita",
        "reservar una cita",
        "programar cita",
        "programar una cita",
    ]

    return any(
        expresion in texto_normalizado
        for expresion in expresiones
    )


def usuario_quiere_cancelar(texto: str) -> bool:
    """
    Detecta si el usuario desea cancelar el proceso.
    """

    texto_normalizado = normalizar_texto(texto)

    expresiones = [
        "cancelar",
        "cancela",
        "ya no quiero",
        "detener",
        "salir",
        "olvidalo",
        "olvídalo",
    ]

    return any(
        expresion in texto_normalizado
        for expresion in expresiones
    )


def usuario_confirma(texto: str) -> bool:
    """
    Detecta respuestas afirmativas.
    """

    texto_normalizado = normalizar_texto(texto)

    respuestas = [
        "si",
        "sí",
        "confirmar",
        "confirmo",
        "correcto",
        "de acuerdo",
        "esta bien",
        "está bien",
        "acepto",
    ]

    return any(
        respuesta == texto_normalizado
        or respuesta in texto_normalizado
        for respuesta in respuestas
    )


def usuario_rechaza(texto: str) -> bool:
    """
    Detecta respuestas negativas.
    """

    texto_normalizado = normalizar_texto(texto)

    respuestas = [
        "no",
        "incorrecto",
        "cambiar",
        "modificar",
        "otra fecha",
        "otra hora",
    ]

    return any(
        respuesta == texto_normalizado
        or respuesta in texto_normalizado
        for respuesta in respuestas
    )


# ==================================================
# DETECCIÓN DE ESPECIALIDAD
# ==================================================

def detectar_especialidad(texto: str) -> str | None:
    """
    Busca una especialidad dentro del mensaje.
    """

    texto_normalizado = normalizar_texto(texto)

    alias = {
        "cardiologo": "Cardiología",
        "cardiologia": "Cardiología",
        "dermatologo": "Dermatología",
        "dermatologia": "Dermatología",
        "ginecologo": "Ginecología",
        "ginecologia": "Ginecología",
        "medicina general": "Medicina General",
        "medico general": "Medicina General",
        "neurologo": "Neurología",
        "neurologia": "Neurología",
        "oftalmologo": "Oftalmología",
        "oftalmologia": "Oftalmología",
        "ortopedia": "Ortopedia",
        "ortopedista": "Ortopedia",
        "pediatra": "Pediatría",
        "pediatria": "Pediatría",
        "psicologo": "Psicología",
        "psicologia": "Psicología",
        "traumatologo": "Traumatología",
        "traumatologia": "Traumatología",
    }

    for expresion, especialidad in alias.items():
        if expresion in texto_normalizado:
            return especialidad

    for especialidad in ESPECIALIDADES_DISPONIBLES:
        if normalizar_texto(especialidad) in texto_normalizado:
            return especialidad

    return None


# ==================================================
# DETECCIÓN DE FECHA
# ==================================================

def siguiente_dia_semana(
    numero_dia: int,
    fecha_base: datetime | None = None,
) -> datetime:
    """
    Devuelve la próxima fecha correspondiente al día indicado.

    Lunes = 0
    Domingo = 6
    """

    fecha_base = fecha_base or datetime.now()

    diferencia = (
        numero_dia - fecha_base.weekday()
    ) % 7

    if diferencia == 0:
        diferencia = 7

    return fecha_base + timedelta(
        days=diferencia
    )


def detectar_fecha(texto: str) -> str | None:
    """
    Detecta expresiones como:
    hoy
    mañana
    pasado mañana
    lunes
    viernes
    25/07/2026
    """

    texto_normalizado = normalizar_texto(texto)
    ahora = datetime.now()

    if "pasado manana" in texto_normalizado:
        fecha = ahora + timedelta(days=2)

        return fecha.strftime("%Y-%m-%d")

    if "manana" in texto_normalizado:
        fecha = ahora + timedelta(days=1)

        return fecha.strftime("%Y-%m-%d")

    if "hoy" in texto_normalizado:
        return ahora.strftime("%Y-%m-%d")

    dias_semana = {
        "lunes": 0,
        "martes": 1,
        "miercoles": 2,
        "jueves": 3,
        "viernes": 4,
        "sabado": 5,
        "domingo": 6,
    }

    for dia, numero_dia in dias_semana.items():
        if dia in texto_normalizado:
            fecha = siguiente_dia_semana(
                numero_dia
            )

            return fecha.strftime("%Y-%m-%d")

    patrones = [
        r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b",
        r"\b(\d{4})[/-](\d{1,2})[/-](\d{1,2})\b",
    ]

    coincidencia = re.search(
        patrones[0],
        texto_normalizado,
    )

    if coincidencia:
        dia = int(coincidencia.group(1))
        mes = int(coincidencia.group(2))
        anio = int(coincidencia.group(3))

        try:
            fecha = datetime(
                year=anio,
                month=mes,
                day=dia,
            )

            return fecha.strftime("%Y-%m-%d")

        except ValueError:
            return None

    coincidencia = re.search(
        patrones[1],
        texto_normalizado,
    )

    if coincidencia:
        anio = int(coincidencia.group(1))
        mes = int(coincidencia.group(2))
        dia = int(coincidencia.group(3))

        try:
            fecha = datetime(
                year=anio,
                month=mes,
                day=dia,
            )

            return fecha.strftime("%Y-%m-%d")

        except ValueError:
            return None

    return None


def fecha_es_valida(fecha_texto: str) -> bool:
    """
    Comprueba que la fecha exista y no esté en el pasado.
    """

    try:
        fecha = datetime.strptime(
            fecha_texto,
            "%Y-%m-%d",
        ).date()

    except ValueError:
        return False

    return fecha >= datetime.now().date()


def mostrar_fecha_amigable(
    fecha_texto: str | None,
) -> str:
    """
    Convierte 2026-07-24 en 24/07/2026.
    """

    if not fecha_texto:
        return "No definida"

    try:
        fecha = datetime.strptime(
            fecha_texto,
            "%Y-%m-%d",
        )

        return fecha.strftime("%d/%m/%Y")

    except ValueError:
        return fecha_texto


# ==================================================
# DETECCIÓN DE HORA
# ==================================================

def detectar_hora(texto: str) -> str | None:
    """
    Detecta horarios como:
    10
    10:00
    10 am
    4 pm
    16:00
    """

    texto_normalizado = normalizar_texto(texto)

    coincidencia = re.search(
        r"\b(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\b",
        texto_normalizado,
    )

    if not coincidencia:
        return None

    hora = int(coincidencia.group(1))
    minutos = int(
        coincidencia.group(2) or 0
    )

    periodo = coincidencia.group(3)

    if minutos not in (0, 30):
        return None

    if periodo == "pm" and hora < 12:
        hora += 12

    if periodo == "am" and hora == 12:
        hora = 0

    if hora > 23:
        return None

    hora_formateada = f"{hora:02d}:{minutos:02d}"

    if hora_formateada not in HORARIOS_DISPONIBLES:
        return None

    return hora_formateada


# ==================================================
# DETECCIÓN DE NOMBRE Y TELÉFONO
# ==================================================

def detectar_nombre(texto: str) -> str | None:
    """
    Limpia expresiones como:
    Me llamo Axel Domínguez
    Mi nombre es Axel Domínguez
    """

    nombre = str(texto).strip()

    patrones = [
        r"^me llamo\s+",
        r"^mi nombre es\s+",
        r"^soy\s+",
        r"^nombre\s*:\s*",
    ]

    for patron in patrones:
        nombre = re.sub(
            patron,
            "",
            nombre,
            flags=re.IGNORECASE,
        )

    nombre = nombre.strip()

    if len(nombre) < 3:
        return None

    if any(
        caracter.isdigit()
        for caracter in nombre
    ):
        return None

    palabras = nombre.split()

    if len(palabras) < 2:
        return None

    return " ".join(
        palabra.capitalize()
        for palabra in palabras
    )


def detectar_telefono(texto: str) -> str | None:
    """
    Extrae un teléfono mexicano de 10 dígitos desde una frase.

    Ejemplos aceptados:
    - 5567823411
    - Mi número es 5567823411
    - Mi teléfono es 556-782-3411
    - Puedes llamarme al 556 782 3411
    - +52 5567823411
    """

    texto = str(texto).strip()

    # Busca secuencias que puedan contener números,
    # espacios, guiones, paréntesis o el prefijo +52.
    candidatos = re.findall(
        r"(?:\+?52[\s\-]*)?"
        r"(?:\(?\d{2,3}\)?[\s\-]*)?"
        r"\d{3}[\s\-]*\d{4}",
        texto,
    )

    for candidato in candidatos:
        solo_numeros = re.sub(
            r"\D",
            "",
            candidato,
        )

        # Elimina el prefijo de México cuando viene incluido.
        if len(solo_numeros) == 12 and solo_numeros.startswith("52"):
            solo_numeros = solo_numeros[2:]

        if len(solo_numeros) == 10:
            return solo_numeros

    # Segunda búsqueda más flexible:
    # toma todos los bloques numéricos del mensaje.
    bloques = re.findall(
        r"\d+",
        texto,
    )

    numeros_unidos = "".join(
        bloques
    )

    if len(numeros_unidos) == 12 and numeros_unidos.startswith("52"):
        numeros_unidos = numeros_unidos[2:]

    if len(numeros_unidos) == 10:
        return numeros_unidos

    return None


# ==================================================
# RESPUESTAS
# ==================================================

def respuesta_cita(
    titulo: str,
    mensaje: str,
    datos: list[dict[str, str]] | None = None,
    pregunta_final: str | None = None,
    advertencia: str | None = None,
) -> dict[str, Any]:
    """
    Genera una respuesta compatible con las tarjetas
    estructuradas de MediAssist.
    """

    return {
        "tipo": "cita",
        "titulo": titulo,
        "mensaje": mensaje,
        "datos": datos or [],
        "advertencia": advertencia,
        "pregunta_final": pregunta_final,
    }


def resumen_cita(
    estado: dict[str, Any],
) -> list[dict[str, str]]:
    """
    Convierte los datos de la cita en filas visuales.
    """

    return [
        {
            "emoji": "🩺",
            "etiqueta": "Especialidad",
            "valor": str(
                estado.get("especialidad")
                or "No definida"
            ),
        },
        {
            "emoji": "📅",
            "etiqueta": "Fecha",
            "valor": mostrar_fecha_amigable(
                estado.get("fecha")
            ),
        },
        {
            "emoji": "🕐",
            "etiqueta": "Hora",
            "valor": str(
                estado.get("hora")
                or "No definida"
            ),
        },
        {
            "emoji": "👤",
            "etiqueta": "Paciente",
            "valor": str(
                estado.get("paciente")
                or "No definido"
            ),
        },
        {
            "emoji": "📱",
            "etiqueta": "Teléfono",
            "valor": str(
                estado.get("telefono")
                or "No definido"
            ),
        },
    ]


# ==================================================
# FLUJO CONVERSACIONAL
# ==================================================

def procesar_agendamiento(
    mensaje: str,
    estado: dict[str, Any] | None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """
    Procesa un turno completo de conversación.

    Devuelve:
    - respuesta estructurada
    - nuevo estado de la cita
    """

    if estado is None:
        estado = crear_estado_cita_vacio()

    if usuario_quiere_cancelar(mensaje):
        nuevo_estado = cancelar_agendamiento()

        respuesta = respuesta_cita(
            titulo="Agendamiento cancelado",
            mensaje=(
                "El proceso de agendamiento fue cancelado. "
                "No se guardó ninguna cita."
            ),
            pregunta_final=(
                "¿Puedo ayudarte con otra consulta?"
            ),
        )

        return respuesta, nuevo_estado

    if not estado.get("activa"):
        if not usuario_quiere_agendar(mensaje):
            respuesta = respuesta_cita(
                titulo="Citas médicas",
                mensaje=(
                    "Puedo ayudarte a reservar una cita "
                    "médica paso a paso."
                ),
                pregunta_final=(
                    "Escribe: Quiero agendar una cita."
                ),
            )

            return respuesta, estado

        estado = iniciar_agendamiento(
            estado
        )

        especialidad = detectar_especialidad(
            mensaje
        )

        if especialidad:
            estado["especialidad"] = especialidad
            estado["paso"] = "fecha"

            respuesta = respuesta_cita(
                titulo="Agendar cita",
                mensaje=(
                    f"Seleccionaste {especialidad}."
                ),
                datos=[
                    {
                        "emoji": "🩺",
                        "etiqueta": "Especialidad",
                        "valor": especialidad,
                    }
                ],
                pregunta_final=(
                    "¿Qué fecha prefieres para tu cita?"
                ),
            )

            return respuesta, estado

        respuesta = respuesta_cita(
            titulo="Agendar cita",
            mensaje=(
                "Comencemos con el agendamiento."
            ),
            datos=[
                {
                    "emoji": "🏥",
                    "etiqueta": "Especialidades",
                    "valor": ", ".join(
                        ESPECIALIDADES_DISPONIBLES
                    ),
                }
            ],
            pregunta_final=(
                "¿Qué especialidad necesitas?"
            ),
        )

        return respuesta, estado

    paso = estado.get("paso")

    # ----------------------------------------------
    # ESPECIALIDAD
    # ----------------------------------------------

    if paso == "especialidad":
        especialidad = detectar_especialidad(
            mensaje
        )

        if not especialidad:
            respuesta = respuesta_cita(
                titulo="Especialidad no identificada",
                mensaje=(
                    "No pude identificar la especialidad."
                ),
                datos=[
                    {
                        "emoji": "🏥",
                        "etiqueta": "Opciones",
                        "valor": ", ".join(
                            ESPECIALIDADES_DISPONIBLES
                        ),
                    }
                ],
                pregunta_final=(
                    "¿Qué especialidad necesitas?"
                ),
            )

            return respuesta, estado

        estado["especialidad"] = especialidad
        estado["paso"] = "fecha"

        respuesta = respuesta_cita(
            titulo="Especialidad seleccionada",
            mensaje=(
                f"Perfecto, la cita será para {especialidad}."
            ),
            pregunta_final=(
                "¿Qué fecha prefieres?"
            ),
        )

        return respuesta, estado

    # ----------------------------------------------
    # FECHA
    # ----------------------------------------------

    if paso == "fecha":
        fecha = detectar_fecha(
            mensaje
        )

        if not fecha:
            respuesta = respuesta_cita(
                titulo="Fecha no identificada",
                mensaje=(
                    "No pude reconocer la fecha indicada."
                ),
                pregunta_final=(
                    "Puedes escribir, por ejemplo: "
                    "mañana, viernes o 25/07/2026."
                ),
            )

            return respuesta, estado

        if not fecha_es_valida(fecha):
            respuesta = respuesta_cita(
                titulo="Fecha no disponible",
                mensaje=(
                    "La fecha indicada ya pasó."
                ),
                pregunta_final=(
                    "Selecciona una fecha futura."
                ),
            )

            return respuesta, estado

        estado["fecha"] = fecha
        estado["paso"] = "hora"

        respuesta = respuesta_cita(
            titulo="Fecha seleccionada",
            mensaje=(
                "La fecha fue registrada correctamente."
            ),
            datos=[
                {
                    "emoji": "📅",
                    "etiqueta": "Fecha",
                    "valor": mostrar_fecha_amigable(
                        fecha
                    ),
                },
                {
                    "emoji": "🕐",
                    "etiqueta": "Horarios",
                    "valor": ", ".join(
                        HORARIOS_DISPONIBLES
                    ),
                },
            ],
            pregunta_final=(
                "¿A qué hora prefieres la cita?"
            ),
        )

        return respuesta, estado

    # ----------------------------------------------
    # HORA
    # ----------------------------------------------

    if paso == "hora":
        hora = detectar_hora(
            mensaje
        )

        if not hora:
            respuesta = respuesta_cita(
                titulo="Horario no disponible",
                mensaje=(
                    "No reconocí el horario o no se encuentra "
                    "dentro de los horarios disponibles."
                ),
                datos=[
                    {
                        "emoji": "🕐",
                        "etiqueta": "Horarios disponibles",
                        "valor": ", ".join(
                            HORARIOS_DISPONIBLES
                        ),
                    }
                ],
                pregunta_final=(
                    "¿Qué horario prefieres?"
                ),
            )

            return respuesta, estado

        if estado.get("fecha") == datetime.now().strftime("%Y-%m-%d"):
            hora_cita = datetime.strptime(
                f"{estado['fecha']} {hora}",
                "%Y-%m-%d %H:%M",
            )

            if hora_cita <= datetime.now():
                respuesta = respuesta_cita(
                    titulo="Horario no disponible",
                    mensaje=(
                        "Ese horario ya pasó para la fecha de hoy."
                    ),
                    datos=[
                        {
                            "emoji": "🕐",
                            "etiqueta": "Horarios disponibles",
                            "valor": ", ".join(HORARIOS_DISPONIBLES),
                        }
                    ],
                    pregunta_final=(
                        "Selecciona un horario posterior."
                    ),
                )

                return respuesta, estado

        estado["hora"] = hora
        estado["paso"] = "paciente"

        respuesta = respuesta_cita(
            titulo="Horario seleccionado",
            mensaje=(
                f"Reservaremos provisionalmente el horario {hora}."
            ),
            pregunta_final=(
                "¿Cuál es el nombre completo del paciente?"
            ),
        )

        return respuesta, estado

    # ----------------------------------------------
    # PACIENTE
    # ----------------------------------------------

    if paso == "paciente":
        paciente = detectar_nombre(
            mensaje
        )

        if not paciente:
            respuesta = respuesta_cita(
                titulo="Nombre incompleto",
                mensaje=(
                    "Necesito el nombre y apellido del paciente."
                ),
                pregunta_final=(
                    "Escribe el nombre completo, por ejemplo: "
                    "Axel Domínguez."
                ),
            )

            return respuesta, estado

        estado["paciente"] = paciente
        estado["paso"] = "telefono"

        respuesta = respuesta_cita(
            titulo="Paciente registrado",
            mensaje=(
                f"Gracias, {paciente}."
            ),
            pregunta_final=(
                "¿Cuál es tu número de teléfono de 10 dígitos?"
            ),
        )

        return respuesta, estado

    # ----------------------------------------------
    # TELÉFONO
    # ----------------------------------------------

    if paso == "telefono":
        telefono = detectar_telefono(
            mensaje
        )

        if not telefono:
            respuesta = respuesta_cita(
                titulo="Teléfono no válido",
                mensaje=(
                    "No pude identificar un teléfono válido en tu mensaje. "
                    "Puedes escribirlo solo o dentro de una frase."
                ),
                pregunta_final=(
                    "Por ejemplo: Mi número es 5567823411."
                ),
            )

            return respuesta, estado

        estado["telefono"] = telefono
        estado["paso"] = "confirmacion"

        respuesta = respuesta_cita(
            titulo="Confirma tu cita",
            mensaje=(
                "Revisa los datos antes de confirmar."
            ),
            datos=resumen_cita(
                estado
            ),
            pregunta_final=(
                "¿Los datos son correctos? "
                "Responde Sí para confirmar o No para cancelar."
            ),
        )

        return respuesta, estado

    # ----------------------------------------------
    # CONFIRMACIÓN
    # ----------------------------------------------

    if paso == "confirmacion":
        if usuario_confirma(mensaje):
            estado["confirmada"] = True
            estado["activa"] = False
            estado["paso"] = "finalizada"

            respuesta = respuesta_cita(
                titulo="Cita confirmada",
                mensaje=(
                    "La cita fue registrada correctamente."
                ),
                datos=resumen_cita(
                    estado
                ),
                advertencia=(
                    "La cita se guardará en el registro del hospital "
                    "después de esta confirmación."
                ),
                pregunta_final=(
                    "¿Puedo ayudarte con otra consulta?"
                ),
            )

            return respuesta, estado

        if usuario_rechaza(mensaje):
            nuevo_estado = cancelar_agendamiento()

            respuesta = respuesta_cita(
                titulo="Cita no confirmada",
                mensaje=(
                    "La información fue descartada y no se "
                    "registró ninguna cita."
                ),
                pregunta_final=(
                    "Puedes comenzar nuevamente cuando quieras."
                ),
            )

            return respuesta, nuevo_estado

        respuesta = respuesta_cita(
            titulo="Confirmación pendiente",
            mensaje=(
                "Necesito que confirmes los datos."
            ),
            pregunta_final=(
                "Responde Sí para confirmar o No para cancelar."
            ),
        )

        return respuesta, estado

    respuesta = respuesta_cita(
        titulo="Citas médicas",
        mensaje=(
            "El proceso anterior ya terminó."
        ),
        pregunta_final=(
            "Escribe «Quiero agendar una cita» "
            "para comenzar otra."
        ),
    )

    return respuesta, estado