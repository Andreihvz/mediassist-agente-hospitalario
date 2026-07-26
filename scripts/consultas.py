from pathlib import Path
import unicodedata

import pandas as pd


# --------------------------------------------------
# CONFIGURACIÓN DEL ARCHIVO
# --------------------------------------------------

BASE = Path(__file__).resolve().parent.parent
ARCHIVO = BASE / "data" / "proyecto_hospital_normalizado.xlsx"


def cargar_datos() -> dict[str, pd.DataFrame]:
    """
    Lee las hojas necesarias del archivo Excel.

    Devuelve un diccionario donde cada elemento contiene
    una tabla de pandas.
    """

    if not ARCHIVO.exists():
        raise FileNotFoundError(
            f"No se encontró el archivo Excel en: {ARCHIVO}"
        )

    return {
        "medicos": pd.read_excel(
            ARCHIVO,
            sheet_name="Medicos"
        ),
        "costos": pd.read_excel(
            ARCHIVO,
            sheet_name="Costos"
        ),
        "estudios": pd.read_excel(
            ARCHIVO,
            sheet_name="Estudios"
        ),
        "faq": pd.read_excel(
            ARCHIVO,
            sheet_name="Preguntas_Frecuentes"
        ),
    }


DATOS = cargar_datos()

medicos = DATOS["medicos"]
costos = DATOS["costos"]
estudios = DATOS["estudios"]
faq = DATOS["faq"]


# --------------------------------------------------
# FUNCIONES AUXILIARES
# --------------------------------------------------

def limpiar_texto(valor) -> str:
    """
    Convierte un valor del Excel en texto limpio.
    Evita mostrar valores como 'nan'.
    """

    if pd.isna(valor):
        return "No disponible"

    return str(valor).strip()


def formatear_precio(valor) -> str:
    """
    Convierte un precio numérico al formato:
    $2,500.00 MXN
    """

    if pd.isna(valor):
        return "No disponible"

    try:
        precio = float(valor)
        return f"${precio:,.2f} MXN"
    except (TypeError, ValueError):
        return limpiar_texto(valor)


def obtener_precio_estudio(nombre_estudio: str) -> str:
    """
    Busca en la hoja Costos el precio correspondiente
    al nombre de un estudio.
    """

    nombre_estudio = nombre_estudio.strip()

    coincidencias = costos[
        costos["Servicio"]
        .astype(str)
        .str.contains(
            nombre_estudio,
            case=False,
            na=False,
            regex=False
        )
    ]

    # Si no encontró buscando el nombre completo,
    # intenta buscar al revés.
    if coincidencias.empty:
        coincidencias = costos[
            costos["Servicio"]
            .astype(str)
            .apply(
                lambda servicio: servicio.lower().strip()
                in nombre_estudio.lower().strip()
            )
        ]

    if coincidencias.empty:
        return "No disponible en la base de costos"

    registro = coincidencias.iloc[0]

    return formatear_precio(registro["Precio_MXN"])


# --------------------------------------------------
# CONSULTAR MÉDICOS
# --------------------------------------------------

def buscar_medicos(especialidad: str) -> str:
    """
    Busca médicos por especialidad.
    """

    especialidad = especialidad.strip()

    resultado = medicos[
        medicos["Especialidad"]
        .astype(str)
        .str.contains(
            especialidad,
            case=False,
            na=False,
            regex=False
        )
    ]

    if resultado.empty:
        return (
            f"No se encontraron médicos para la especialidad "
            f"'{especialidad}'."
        )

    disponibles = resultado[
        resultado["Estado"]
        .astype(str)
        .str.strip()
        .str.lower()
        == "disponible"
    ]

    if disponibles.empty:
        return (
            f"Se encontraron médicos de {especialidad}, "
            "pero ninguno aparece disponible actualmente."
        )

    respuesta = [
        f"Médicos disponibles en {especialidad}:"
    ]

    for _, medico in disponibles.iterrows():
        respuesta.append(
            f"- {limpiar_texto(medico['Nombre_Completo'])} | "
            f"Consultorio: "
            f"{limpiar_texto(medico['Consultorio'])}"
        )

    return "\n".join(respuesta)


# --------------------------------------------------
# CONSULTAR PRECIOS
# --------------------------------------------------

def buscar_precio(servicio: str) -> str:
    """
    Busca el precio de una consulta, estudio o servicio.
    """

    servicio = servicio.strip()

    resultado = costos[
        costos["Servicio"]
        .astype(str)
        .str.contains(
            servicio,
            case=False,
            na=False,
            regex=False
        )
    ]

    if resultado.empty:
        return (
            f"No se encontró información de precios para "
            f"'{servicio}'."
        )

    respuestas = []

    for _, registro in resultado.iterrows():
        respuestas.append(
            f"Servicio: "
            f"{limpiar_texto(registro['Servicio'])}\n"
            f"Precio: "
            f"{formatear_precio(registro['Precio_MXN'])}\n"
            f"Duración aproximada: "
            f"{limpiar_texto(registro['Duracion_Min'])} minutos\n"
            f"Requiere cita: "
            f"{limpiar_texto(registro['Requiere_Cita'])}\n"
            f"Incluye: "
            f"{limpiar_texto(registro['Incluye'])}"
        )

    return "\n\n".join(respuestas)


# --------------------------------------------------
# CONSULTAR ESTUDIOS
# --------------------------------------------------

def buscar_estudio(nombre_estudio: str) -> str:
    """
    Busca la información oficial de un estudio médico.

    Además, consulta la hoja Costos para agregar
    el precio correspondiente.
    """

    nombre_estudio = nombre_estudio.strip()

    resultado = estudios[
        estudios["Nombre_Estudio"]
        .astype(str)
        .str.contains(
            nombre_estudio,
            case=False,
            na=False,
            regex=False
        )
    ]

    if resultado.empty:
        return (
            f"No se encontró el estudio "
            f"'{nombre_estudio}'."
        )

    respuestas = []

    for _, estudio in resultado.iterrows():
        nombre_oficial = limpiar_texto(
            estudio["Nombre_Estudio"]
        )

        precio = obtener_precio_estudio(nombre_oficial)

        respuestas.append(
            f"Estudio: {nombre_oficial}\n"
            f"Categoría: "
            f"{limpiar_texto(estudio['Categoria'])}\n"
            f"Precio: {precio}\n"
            f"Preparación: "
            f"{limpiar_texto(estudio['Preparacion'])}\n"
            f"Requiere ayuno: "
            f"{limpiar_texto(estudio['Requiere_Ayuno'])}\n"
            f"Horas de ayuno: "
            f"{limpiar_texto(estudio['Horas_Ayuno'])}\n"
            f"Duración aproximada: "
            f"{limpiar_texto(estudio['Duracion_Min'])} minutos\n"
            f"Entrega de resultados: "
            f"{limpiar_texto(estudio['Entrega_Resultados'])}\n"
            f"Requiere orden médica: "
            f"{limpiar_texto(estudio['Requiere_Orden_Medica'])}\n"
            f"Recomendaciones: "
            f"{limpiar_texto(estudio['Recomendaciones'])}\n"
            f"Documentos necesarios: "
            f"{limpiar_texto(estudio['Documentos_Necesarios'])}"
        )

    return "\n\n".join(respuestas)


# --------------------------------------------------
# CONSULTAR PREGUNTAS FRECUENTES
# --------------------------------------------------

def normalizar_texto(texto: object) -> str:
    """
    Convierte a minúsculas y elimina acentos,
    para comparar palabras sin importar tildes.
    """

    texto = str(texto).lower().strip()

    texto_normalizado = unicodedata.normalize("NFD", texto)

    texto_sin_acentos = "".join(
        caracter
        for caracter in texto_normalizado
        if unicodedata.category(caracter) != "Mn"
    )

    return texto_sin_acentos


def buscar_pregunta(texto: str) -> str:
    """
    Busca una respuesta en la FAQ comparando palabra por palabra,
    tolerando acentos y plurales simples (ej. "visita" / "visitas").
    """

    texto_normalizado = normalizar_texto(texto)

    palabras_ignoradas = {
        "que", "como", "cual", "cuales", "donde", "cuando",
        "para", "por", "con", "sin", "una", "unos", "unas",
        "del", "las", "los", "hay", "tiene", "tienen",
    }

    palabras_busqueda = [
        palabra.rstrip("s")
        for palabra in texto_normalizado.split()
        if len(palabra) >= 4 and palabra not in palabras_ignoradas
    ]

    if not palabras_busqueda:
        palabras_busqueda = [texto_normalizado]

    filas_encontradas = []

    for _, fila in faq.iterrows():
        contenido = normalizar_texto(
            f"{fila['Pregunta']} {fila['Palabras_Clave']} {fila['Categoria']}"
        )

        coincide = any(
            palabra in contenido or contenido.find(palabra[:-1] if len(palabra) > 4 else palabra) != -1
            for palabra in palabras_busqueda
        )

        if coincide:
            filas_encontradas.append(fila)

    if not filas_encontradas:
        return (
            "No encontré una respuesta relacionada "
            "en las preguntas frecuentes."
        )

    respuestas = []

    for fila in filas_encontradas[:3]:
        respuestas.append(
            f"Pregunta: {limpiar_texto(fila['Pregunta'])}\n"
            f"Respuesta: {limpiar_texto(fila['Respuesta'])}"
        )

    return "\n\n".join(respuestas)


# --------------------------------------------------
# MENÚ DE PRUEBA
# --------------------------------------------------

def mostrar_menu() -> None:
    """
    Muestra un menú para probar las consultas desde terminal.
    """

    while True:
        print("\n" + "=" * 50)
        print("MEDIASSIST AI - CONSULTAS")
        print("=" * 50)
        print("1. Buscar médicos")
        print("2. Consultar precio")
        print("3. Consultar estudio")
        print("4. Buscar pregunta frecuente")
        print("5. Salir")

        opcion = input(
            "\nSelecciona una opción: "
        ).strip()

        if opcion == "1":
            especialidad = input(
                "Escribe la especialidad: "
            ).strip()

            print(
                "\n" + buscar_medicos(especialidad)
            )

        elif opcion == "2":
            servicio = input(
                "Escribe la consulta, estudio o servicio: "
            ).strip()

            print(
                "\n" + buscar_precio(servicio)
            )

        elif opcion == "3":
            estudio = input(
                "Escribe el nombre del estudio: "
            ).strip()

            print(
                "\n" + buscar_estudio(estudio)
            )

        elif opcion == "4":
            pregunta = input(
                "Escribe una palabra o pregunta: "
            ).strip()

            print(
                "\n" + buscar_pregunta(pregunta)
            )

        elif opcion == "5":
            print("\nPrograma finalizado.")
            break

        else:
            print(
                "\nOpción no válida. Intenta nuevamente."
            )


if __name__ == "__main__":
    mostrar_menu()