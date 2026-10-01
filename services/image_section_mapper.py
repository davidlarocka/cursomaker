import os

from dotenv import load_dotenv
from openai import OpenAI

from models.render_blueprint import (
    AsignacionImagenSubseccion,
)


load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)


def asignar_imagen_subseccion(
    imagen,
    subsecciones,
):
    """
    Asigna una imagen a una de las subsecciones
    permitidas de un contenido.
    """

    if not subsecciones:
        raise ValueError(
            "No existen subsecciones candidatas."
        )

    opciones = []

    for indice, subseccion in enumerate(
        subsecciones
    ):
        opciones.append(
            f"[{indice}]\n"
            f"Título: {subseccion.titulo}\n"
            f"Contenido: {subseccion.contenido}"
        )

    texto_opciones = "\n\n".join(
        opciones
    )

    response = client.responses.parse(
        model="gpt-5.6",
        input=[
            {
                "role": "system",
                "content": (
                    "Eres el asignador visual de CursoMaker. "
                    "Debes determinar a cuál subsección de una "
                    "lección educativa corresponde mejor una "
                    "imagen. Solo puedes seleccionar una de las "
                    "subsecciones proporcionadas. Usa la "
                    "descripción objetiva de la imagen y el "
                    "contenido de cada subsección. No inventes "
                    "subsecciones ni información adicional."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"DESCRIPCIÓN DE LA IMAGEN:\n"
                    f"{imagen.descripcion}\n\n"
                    f"SUBSECCIONES PERMITIDAS:\n\n"
                    f"{texto_opciones}"
                ),
            },
        ],
        text_format=AsignacionImagenSubseccion,
    )

    resultado = response.output_parsed

    if not (
        0
        <= resultado.indice_subseccion
        < len(subsecciones)
    ):
        raise RuntimeError(
            "El modelo seleccionó una subsección "
            "fuera de los límites permitidos."
        )

    return resultado