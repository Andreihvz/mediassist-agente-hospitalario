from __future__ import annotations

import sys
from pathlib import Path


# --------------------------------------------------
# CONFIGURACIÓN DE RUTAS
# --------------------------------------------------

BASE = Path(__file__).resolve().parent.parent

if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

from services.router import crear_contexto_oficial


# --------------------------------------------------
# PROGRAMA DE PRUEBA
# --------------------------------------------------

def probar_router() -> None:
    print("\n" + "=" * 60)
    print("PRUEBA DEL ROUTER INTELIGENTE DE MEDIASSIST")
    print("=" * 60)

    while True:
        pregunta = input(
            "\nEscribe una pregunta o escribe 'salir': "
        ).strip()

        if pregunta.lower() == "salir":
            print("\nPrueba finalizada.")
            break

        if not pregunta:
            print("\nDebes escribir una pregunta.")
            continue

        contexto, resultado = crear_contexto_oficial(
            pregunta
        )

        print("\n" + "-" * 60)
        print("RESULTADO DEL ROUTER")
        print("-" * 60)

        print(
            "Tipo de consulta:",
            resultado["tipo"],
        )

        print(
            "Elemento detectado:",
            resultado["termino_detectado"],
        )

        print(
            "Confianza:",
            resultado["confianza"],
        )

        print("\nCONTEXTO GENERADO:")
        print(contexto)


if __name__ == "__main__":
    probar_router()