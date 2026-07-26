from pathlib import Path

import pandas as pd


def main() -> None:
    """Lee el archivo Excel del hospital y muestra su contenido básico."""

    carpeta_proyecto = Path(__file__).resolve().parent.parent
    ruta_excel = carpeta_proyecto / "data" / "proyecto_hospital_normalizado.xlsx"

    if not ruta_excel.exists():
        print("ERROR: No se encontró el archivo Excel.")
        print(f"Ruta buscada: {ruta_excel}")
        return

    archivo_excel = pd.ExcelFile(ruta_excel)

    print("El archivo se abrió correctamente.")
    print("\nHojas encontradas:")

    for nombre_hoja in archivo_excel.sheet_names:
        print(f"- {nombre_hoja}")

    medicos = pd.read_excel(ruta_excel, sheet_name="Medicos")

    print("\nPrimeros médicos registrados:")
    print(
        medicos[
            ["ID_Medico", "Nombre_Completo", "Especialidad", "Estado"]
        ].head()
    )


if __name__ == "__main__":
    main()