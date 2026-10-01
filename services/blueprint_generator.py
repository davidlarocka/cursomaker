import os

from dotenv import load_dotenv
from openai import OpenAI

from models.blueprint import CursoBlueprint


load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

def generar_blueprint(texto_documento):
    """
    Analiza el contenido de un manual y genera
    un blueprint estructurado para un curso Moodle.
    """

    print("🧠 Analizando documento y generando blueprint...")

    response = client.responses.parse(
        model="gpt-5.6",
        input=[
            {
                "role": "system",
                "content": (
                    "Eres CursoMaker, especialista en diseño instruccional "
                    "y creación de cursos Moodle a partir de manuales de estudio. "
                    "Analiza exclusivamente la información proporcionada. "
                    "No inventes contenidos que no estén sustentados por el documento. "
                    "Organiza el curso respetando la estructura temática del manual. "
                    "Cada contenido debe indicar las páginas del documento utilizadas "
                    "como fuente. "
                    "El campo contenido debe contener HTML limpio y apropiado para "
                    "una página Moodle. "
                    "Por ahora, utiliza únicamente el tipo de contenido 'pagina'."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Genera un blueprint completo de curso Moodle a partir "
                    "del siguiente manual:\n\n"
                    f"{texto_documento}"
                ),
            },
        ],
        text_format=CursoBlueprint,
    )

    if response.output_parsed is None:
        raise RuntimeError(
            "El modelo no pudo generar un blueprint válido."
        )

    return response.output_parsed