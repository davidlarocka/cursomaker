import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from models.assessment_blueprint import AssessmentBlueprint
from models.contexto_curso import ContextoCurso
from services.documents import extraer_texto_pdf, construir_texto_documento
from services.blueprint_store import guardar_blueprint


def generar_assessment_blueprint(texto_documento):
    """
    Analiza un documento de evaluaciones y actividades
    y genera un blueprint estructurado.
    """

    print(
        "🧠 Analizando documento de actividades "
        "y evaluaciones..."
    )

    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("Falta OPENAI_API_KEY en el entorno o en el archivo .env.")
    client = OpenAI(api_key=api_key)

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


def generar_assessment_desde_actividades(contexto: ContextoCurso) -> Path:
    """Genera las actividades del documento configurado y guarda el blueprint."""
    documento = extraer_texto_pdf(contexto.config.actividades)
    texto = construir_texto_documento(documento)
    if not texto.strip():
        raise ValueError("El documento de actividades no contiene texto extraíble.")

    blueprint = generar_assessment_blueprint(texto)
    if not blueprint.modulos or not any(modulo.actividades for modulo in blueprint.modulos):
        raise ValueError("El Assessment Blueprint generado no contiene actividades.")
    blueprint = blueprint.model_copy(update={
        "curso": contexto.config.nombre,
        "documento_fuente": documento["archivo"],
    })
    return guardar_blueprint(contexto.output_dir / "assessment_blueprint.json", blueprint)
