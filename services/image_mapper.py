import os

from dotenv import load_dotenv
from openai import OpenAI

from models.blueprint import ResolucionDestinoImagen


load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)


def resolver_destino_imagen(
    imagen,
    texto_pagina,
    destinos,
):
    """
    Elige el destino más apropiado para una imagen
    entre una lista cerrada de contenidos candidatos.
    """

    if len(destinos) < 2:
        raise ValueError(
            "La resolución semántica requiere "
            "al menos dos destinos candidatos."
        )

    opciones = []

    for indice, destino in enumerate(destinos):
        opciones.append(
            f"[{indice}]\n"
            f"Sección: {destino['seccion']}\n"
            f"Contenido: {destino['contenido']}"
        )

    texto_destinos = "\n\n".join(opciones)

    response = client.responses.parse(
        model="gpt-5.6",
        input=[
            {
                "role": "system",
                "content": (
                    "Eres el resolvedor de destinos visuales "
                    "de CursoMaker. "
                    "Debes determinar a cuál de los contenidos "
                    "candidatos pertenece mejor una imagen de "
                    "un manual educativo. "
                    "Solo puedes elegir uno de los destinos "
                    "proporcionados. "
                    "Usa exclusivamente la descripción visual, "
                    "la relación con el texto, el texto original "
                    "de la página y los títulos candidatos. "
                    "No inventes otros destinos."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"PÁGINA PDF:\n"
                    f"{imagen['pagina']}\n\n"

                    f"DESCRIPCIÓN DE LA IMAGEN:\n"
                    f"{imagen['descripcion']}\n\n"

                    f"RELACIÓN CON EL TEXTO:\n"
                    f"{imagen['relacion_con_texto']}\n\n"

                    f"TEXTO ORIGINAL DE LA PÁGINA:\n"
                    f"{texto_pagina}\n\n"

                    f"DESTINOS PERMITIDOS:\n\n"
                    f"{texto_destinos}"
                ),
            },
        ],
        text_format=ResolucionDestinoImagen,
    )

    resultado = response.output_parsed

    if not (
        0
        <= resultado.indice_destino
        < len(destinos)
    ):
        raise RuntimeError(
            "El modelo seleccionó un destino "
            "fuera de la lista permitida."
        )

    return resultado