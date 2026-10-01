import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from models.blueprint import CursoBlueprint
from models.contexto_curso import ContextoCurso
from services.documents import extraer_texto_pdf, construir_texto_documento

def generar_blueprint(texto_documento):
    """
    Analiza el contenido de un manual y genera
    un blueprint estructurado para un curso Moodle.
    """

    print("🧠 Analizando documento y generando blueprint...")

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


def generar_content_blueprint(contexto: ContextoCurso) -> Path:
    """Extrae el manual, genera el blueprint y guarda un resultado completo."""
    documento = extraer_texto_pdf(contexto.config.manual)
    texto = construir_texto_documento(documento)
    if not texto.strip():
        raise ValueError("El manual no contiene texto extraíble para generar el blueprint.")

    blueprint = generar_blueprint(texto)
    if not blueprint.secciones:
        raise ValueError("El Content Blueprint generado no contiene secciones.")

    identidad = {
        "nombre": contexto.config.nombre,
        "shortname": contexto.config.shortname,
    }
    if contexto.config.descripcion:
        identidad["descripcion"] = contexto.config.descripcion
    blueprint = blueprint.model_copy(update=identidad)

    salida = contexto.output_dir / "blueprint.json"
    temporal = salida.with_suffix(".json.tmp")
    try:
        temporal.write_text(blueprint.model_dump_json(indent=2), encoding="utf-8")
        temporal.replace(salida)
    finally:
        temporal.unlink(missing_ok=True)
    return salida
