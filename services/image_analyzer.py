import base64
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from models.blueprint import AnalisisImagen


load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)


def analizar_imagen(
    ruta_imagen,
    numero_pagina,
    texto_pagina,
):
    """
    Analiza una imagen extraída del PDF junto con
    el texto original de la página donde aparece.
    """

    ruta = Path(ruta_imagen)

    if not ruta.exists():
        raise FileNotFoundError(
            f"No existe la imagen: {ruta}"
        )

    extension = ruta.suffix.lower().lstrip(".")

    if extension == "jpg":
        extension = "jpeg"

    mime_type = f"image/{extension}"

    imagen_base64 = base64.b64encode(
        ruta.read_bytes()
    ).decode("utf-8")

    imagen_data_url = (
        f"data:{mime_type};base64,{imagen_base64}"
    )

    print(
        f"👁️ Analizando imagen "
        f"{ruta.name} de la página {numero_pagina}..."
    )

    response = client.responses.parse(
        model="gpt-5.6",
        input=[
            {
                "role": "system",
                "content": (
                    "Eres el analista visual de CursoMaker. "
                    "Tu tarea es determinar si una imagen extraída "
                    "de un manual educativo aporta información "
                    "pedagógica útil al curso. "
                    "Debes analizar la imagen junto con el texto "
                    "original de la página donde aparece. "
                    "No uses conocimiento externo para completar "
                    "información ausente. "
                    "Logos, fondos, elementos de plantilla y "
                    "decoraciones deben descartarse. "
                    "Fotografías, diagramas, ilustraciones, tablas "
                    "o gráficos relacionados con el contenido "
                    "educativo normalmente deben incluirse."
                ),
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": (
                            f"PÁGINA DEL PDF: {numero_pagina}\n\n"
                            f"TEXTO ORIGINAL DE LA PÁGINA:\n"
                            f"{texto_pagina}"
                        ),
                    },
                    {
                        "type": "input_image",
                        "image_url": imagen_data_url,
                    },
                ],
            },
        ],
        text_format=AnalisisImagen,
    )

    return response.output_parsed