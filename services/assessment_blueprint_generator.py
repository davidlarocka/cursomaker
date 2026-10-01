import os

from dotenv import load_dotenv
from openai import OpenAI

from models.assessment_blueprint import AssessmentBlueprint


load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)


def generar_assessment_blueprint(texto_documento):
    """
    Analiza un documento de evaluaciones y actividades
    y genera un blueprint estructurado.
    """

    print(
        "🧠 Analizando documento de actividades "
        "y evaluaciones..."
    )

    response = client.responses.parse(
        model="gpt-5.6",
        input=[
            {
                "role": "system",
                "content": (
                    "Eres CursoMaker, especialista en diseño "
                    "instruccional y creación de actividades "
                    "para Moodle. "
                    "Analiza exclusivamente la información "
                    "proporcionada. "
                    "No inventes contenidos, respuestas, recursos "
                    "ni instrucciones que no estén sustentados "
                    "por el documento. "
                    "Respeta la organización por módulos del "
                    "documento fuente. "
                    "Identifica actividades de desarrollo, "
                    "actividades de discusión, actividades H5P, "
                    "tests y retroalimentaciones finales. "
                    "Conserva las páginas fuente de cada actividad. "
                    "Cuando una respuesta correcta esté indicada "
                    "en el documento, consérvala. "
                    "No deduzcas una respuesta correcta cuando "
                    "el documento no la especifique. "
                    "No inventes recursos visuales faltantes. "
                    "Si una actividad H5P requiere una imagen "
                    "que no está disponible, representa ese "
                    "recurso como requerido y no disponible."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Genera el blueprint de actividades y "
                    "evaluaciones a partir del siguiente "
                    "documento:\n\n"
                    f"{texto_documento}"
                ),
            },
        ],
        text_format=AssessmentBlueprint,
    )

    if response.output_parsed is None:
        raise RuntimeError(
            "El modelo no pudo generar un "
            "AssessmentBlueprint válido."
        )

    return response.output_parsed