import unicodedata
from difflib import SequenceMatcher

import requests

from consultas import buscar_estudio, estudios


# --------------------------------------------------
# CONFIGURACIÓN DE N8N
# --------------------------------------------------

URL_N8N = (
    "https://andreeihvz.app.n8n.cloud/"
    "webhook-test/mediassist-chat"
)


# --------------------------------------------------
# NORMALIZAR TEXTO
# --------------------------------------------------

def normalizar_texto(texto: str) -> str:
    """
    Convierte un texto a minúsculas, elimina acentos
    y quita signos innecesarios.

    Ejemplo:
    '¿Cuánto cuesta una Resonancia Magnética?'
    se convierte en:
    'cuanto cuesta una resonancia magnetica'
    """

    texto = str(texto).lower().strip()

    texto_normalizado = unicodedata.normalize(
        "NFD",
        texto
    )

    texto_sin_acentos = "".join(
        caracter
        for caracter in texto_normalizado
        if unicodedata.category(caracter) != "Mn"
    )

    caracteres_permitidos = []

    for caracter in texto_sin_acentos:
        if caracter.isalnum() or caracter.isspace():
            caracteres_permitidos.append(caracter)
        else:
            caracteres_permitidos.append(" ")

    texto_limpio = "".join(caracteres_permitidos)

    return " ".join(texto_limpio.split())


# --------------------------------------------------
# DETECTAR ESTUDIO
# --------------------------------------------------

def detectar_estudio(pregunta: str) -> str | None:
    """
    Detecta dentro de una pregunta el nombre de un estudio.

    También permite errores pequeños de escritura, por ejemplo:

    resonansia magnetica
    resonancia magnetica
    resonancia magnética
    """

    pregunta_normalizada = normalizar_texto(pregunta)

    mejor_estudio = None
    mejor_puntaje = 0.0

    for _, fila in estudios.iterrows():
        nombre_estudio = str(
            fila["Nombre_Estudio"]
        ).strip()

        nombre_normalizado = normalizar_texto(
            nombre_estudio
        )

        # Coincidencia exacta dentro de la pregunta.
        if nombre_normalizado in pregunta_normalizada:
            return nombre_estudio

        palabras_pregunta = pregunta_normalizada.split()
        palabras_estudio = nombre_normalizado.split()

        cantidad_palabras = len(palabras_estudio)

        # Compara fragmentos de la pregunta con el nombre
        # oficial del estudio.
        for posicion in range(
            len(palabras_pregunta) - cantidad_palabras + 1
        ):
            fragmento = " ".join(
                palabras_pregunta[
                    posicion:
                    posicion + cantidad_palabras
                ]
            )

            puntaje = SequenceMatcher(
                None,
                nombre_normalizado,
                fragmento
            ).ratio()

            if puntaje > mejor_puntaje:
                mejor_puntaje = puntaje
                mejor_estudio = nombre_estudio

    # Permite pequeñas faltas ortográficas.
    if mejor_estudio is not None and mejor_puntaje >= 0.78:
        print(
            "Coincidencia aproximada encontrada: "
            f"{mejor_puntaje:.0%}"
        )

        return mejor_estudio

    return None


# --------------------------------------------------
# CREAR CONTEXTO
# --------------------------------------------------

def crear_contexto(resultados: str | None) -> str:
    """
    Prepara la información del Excel para enviarla
    como contexto oficial a Gemini.
    """

    if resultados is None:
        return (
            "No se encontró información relacionada "
            "en la base de datos del hospital."
        )

    texto = str(resultados).strip()

    if not texto:
        return (
            "No se encontró información relacionada "
            "en la base de datos del hospital."
        )

    if texto.startswith("No se encontró"):
        return texto

    return (
        "Información oficial encontrada en la "
        "base de datos del hospital:\n\n"
        f"{texto}"
    )


# --------------------------------------------------
# CONSULTAR MEDIASSIST
# --------------------------------------------------

def consultar_mediassist(pregunta: str) -> None:
    """
    Detecta el estudio mencionado por el usuario,
    consulta el Excel y envía la información a n8n.
    """

    print("\nIniciando prueba...")
    print("Pregunta recibida:", pregunta)

    estudio_detectado = detectar_estudio(pregunta)

    if estudio_detectado is None:
        print(
            "No se detectó el nombre de un estudio "
            "registrado en el Excel."
        )

        resultados = (
            "No se encontró información relacionada "
            "con la pregunta en la base de datos "
            "del hospital."
        )

    else:
        print(
            "Estudio detectado:",
            estudio_detectado
        )

        resultados = buscar_estudio(
            estudio_detectado
        )

    print("\nResultado de la búsqueda:")
    print(resultados)

    contexto = crear_contexto(resultados)

    print("\nContexto enviado a n8n:")
    print(contexto)

    datos = {
        "mensaje": pregunta,
        "contexto": contexto,
    }

    try:
        print("\nEnviando datos a n8n...")

        respuesta = requests.post(
            URL_N8N,
            json=datos,
            timeout=60,
        )

        respuesta.raise_for_status()

        print("\nConexión exitosa con MediAssist.")
        print("Código HTTP:", respuesta.status_code)
        print("\nRespuesta recibida:")

        try:
            respuesta_json = respuesta.json()
            print(respuesta_json)

        except ValueError:
            print(respuesta.text)

    except requests.exceptions.Timeout:
        print(
            "\nLa conexión con n8n tardó demasiado "
            "y fue cancelada."
        )

    except requests.exceptions.ConnectionError:
        print(
            "\nNo fue posible conectarse con n8n. "
            "Revisa tu conexión a internet."
        )

    except requests.exceptions.HTTPError as error:
        print("\nEl webhook devolvió un error HTTP:")
        print(error)

        print("\nRespuesta enviada por n8n:")
        print(respuesta.text)

    except requests.exceptions.RequestException as error:
        print("\nOcurrió un error al conectar con n8n:")
        print(error)


# --------------------------------------------------
# INICIAR PROGRAMA
# --------------------------------------------------

if __name__ == "__main__":
    pregunta_usuario = input(
        "Escribe tu pregunta para MediAssist: "
    ).strip()

    if not pregunta_usuario:
        print(
            "Debes escribir una pregunta antes "
            "de continuar."
        )

    else:
        consultar_mediassist(
            pregunta_usuario
        )