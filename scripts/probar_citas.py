from __future__ import annotations

import sys
from pathlib import Path


BASE = Path(__file__).resolve().parent.parent

if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))


from services.citas import (  # noqa: E402
    crear_estado_cita_vacio,
    procesar_agendamiento,
)


def main() -> None:
    estado = crear_estado_cita_vacio()

    print("=" * 55)
    print("MEDIASSIST - PRUEBA DEL MÓDULO DE CITAS")
    print("=" * 55)
    print("Escribe 'salir' para terminar.\n")

    while True:
        mensaje = input("Usuario: ").strip()

        if mensaje.lower() == "salir":
            break

        respuesta, estado = procesar_agendamiento(
            mensaje,
            estado,
        )

        print("\nMediAssist:")
        print(respuesta.get("titulo"))
        print(respuesta.get("mensaje"))

        for dato in respuesta.get("datos", []):
            print(
                f"- {dato.get('etiqueta')}: "
                f"{dato.get('valor')}"
            )

        if respuesta.get("advertencia"):
            print(
                "Advertencia:",
                respuesta["advertencia"],
            )

        if respuesta.get("pregunta_final"):
            print(
                respuesta["pregunta_final"]
            )

        print()


if __name__ == "__main__":
    main()