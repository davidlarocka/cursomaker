import os

from dotenv import load_dotenv
from openai import OpenAI

from models.assessment_blueprint import ActividadEvaluacion
from models.assessment_qa import ResultadoActividadQA


load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)


def revisar_actividad(
    actividad: ActividadEvaluacion,
    texto_fuente: str,
) -> ResultadoActividadQA:
    """
    Compara una actividad extraída contra el texto
    original de sus páginas fuente.
    """

    print(
        f"🔎 Revisando: {actividad.id_logico}"
    )

    actividad_json = actividad.model_dump_json(
        indent=2
    )

    response = client.responses.parse(
        model="gpt-5.6",
        input=[
            {
                "role": "system",
                "content": (
                    "Eres el revisor semántico de CursoMaker. "
                    "Tu tarea es comparar una actividad de "
                    "evaluación generada contra su documento "
                    "fuente. "
                    "\n\n"
                    "Debes determinar si la actividad representa "
                    "fielmente la información proporcionada. "
                    "\n\n"
                    "Revisa especialmente: "
                    "enunciados, instrucciones, escenarios, "
                    "preguntas, alternativas, respuestas correctas, "
                    "retroalimentaciones, relaciones H5P, "
                    "situaciones, espacios en blanco, recursos "
                    "requeridos y cualquier otro dato evaluativo. "
                    "\n\n"
                    "No uses conocimiento externo. "
                    "No completes información ausente. "
                    "No inventes respuestas ni recursos. "
                    "No mejores pedagógicamente el contenido. "
                    "Evalúa únicamente la información que pertenece "
                    "a la actividad recibida. "
                    "El documento fuente puede contener contenido de "
                    "otras actividades o elementos del módulo dentro "
                    "de las mismas páginas. "
                    "No marques como omisión un elemento que no "
                    "pertenece semánticamente a la actividad evaluada. "
                    "En particular, una retroalimentación final del "
                    "módulo pertenece al módulo y no al quiz, aunque "
                    "aparezca inmediatamente después del test. "
                    "\n\n"
                    "Clasifica como 'aprobado' solamente cuando "
                    "la actividad sea fiel a la fuente. "
                    "\n\n"
                    "Usa 'requiere_correccion' cuando la fuente "
                    "permita determinar claramente que existe "
                    "una omisión, alteración, invención o respuesta "
                    "incorrecta y exista evidencia suficiente para "
                    "corregirla. "
                    "\n\n"
                    "Usa 'requiere_revision_humana' cuando la "
                    "fuente sea insuficiente, ambigua o requiera "
                    "un recurso que no está disponible. "
                    "\n\n"
                    "Una paráfrasis que cambie el significado, "
                    "el nivel de precisión o una condición "
                    "evaluativa debe considerarse un hallazgo. "
                    "Una diferencia puramente de formato no debe "
                    "considerarse un error."
                ),
            },
            {
                "role": "user",
                "content": (
                    "ACTIVIDAD GENERADA:\n\n"
                    f"{actividad_json}"
                    "\n\n"
                    "TEXTO ORIGINAL DE LAS PÁGINAS FUENTE:\n\n"
                    f"{texto_fuente}"
                ),
            },
        ],
        text_format=ResultadoActividadQA,
    )

    if response.output_parsed is None:
        raise RuntimeError(
            "El modelo no pudo generar un "
            "ResultadoActividadQA válido."
        )

    resultado = response.output_parsed

    # El revisor no puede cambiar la identidad
    # de la actividad que recibió.
    if resultado.id_logico != actividad.id_logico:
        raise RuntimeError(
            "El QA devolvió un id_logico diferente. "
            f"Esperado: {actividad.id_logico}. "
            f"Recibido: {resultado.id_logico}."
        )

    return resultado