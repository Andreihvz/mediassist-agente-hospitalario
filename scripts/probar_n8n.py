import requests


URL_N8N = "https://andreeihvz.app.n8n.cloud/webhook-test/mediassist-chat"


def probar_webhook() -> None:
    """
    Envía un mensaje de prueba al webhook de n8n.
    """

    datos = {
        "mensaje": "Hola desde Python y Streamlit"
    }

    try:
        respuesta = requests.post(
            URL_N8N,
            json=datos,
            timeout=15,
        )

        respuesta.raise_for_status()

        print("Conexión exitosa con n8n.")
        print("Código HTTP:", respuesta.status_code)
        print("Respuesta recibida:")
        print(respuesta.json())

    except requests.exceptions.ConnectionError:
        print(
            "No fue posible conectarse con n8n. "
            "Comprueba que esté abierto en localhost:5678."
        )

    except requests.exceptions.Timeout:
        print(
            "n8n tardó demasiado en responder."
        )

    except requests.exceptions.HTTPError as error:
        print(
            "n8n devolvió un error HTTP:",
            error,
        )

    except requests.exceptions.JSONDecodeError:
        print("n8n respondió, pero la respuesta no era JSON.")
        print("Contenido real recibido:")
        print(respuesta.text)


if __name__ == "__main__":
    probar_webhook()