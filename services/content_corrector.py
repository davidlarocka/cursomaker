import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)


def corregir_contenido(
    titulo,
    contenido,
    texto_fuente,
    validacion,
):
    """
    Corrige un contenido educativo utilizando exclusivamente
    la fuente original y los problemas detectados por el auditor.
    """

    print(f"🛠️ Corrigiendo contenido: {titulo}...")

    afirmaciones = "\n".join(
        f"- {item}"
        for item in validacion.afirmaciones_no_respaldadas
    ) or "- Ninguna"

    omisiones = "\n".join(
        f"- {item}"
        for item in validacion.omisiones_importantes
    ) or "- Ninguna"

    response = client.responses.create(
        model="gpt-5.6",
        input=[
            {
                "role": "system",
                "content": (
                    "Eres el corrector editorial de CursoMaker. "
                    "Debes corregir una lección educativa existente "
                    "utilizando exclusivamente el texto fuente proporcionado. "
                    "Conserva todo el contenido que ya sea correcto. "
                    "Corrige o elimina afirmaciones no respaldadas. "
                    "Incorpora las omisiones importantes señaladas por el auditor "
                    "cuando estén respaldadas por la fuente. "
                    "No agregues conocimiento externo. "
                    "Mantén una estructura pedagógica clara y devuelve únicamente "
                    "el HTML final de la lección, sin Markdown ni explicaciones."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"TÍTULO:\n{titulo}\n\n"
                    f"CONTENIDO ACTUAL:\n{contenido}\n\n"
                    f"AFIRMACIONES NO RESPALDADAS:\n{afirmaciones}\n\n"
                    f"OMISIONES IMPORTANTES:\n{omisiones}\n\n"
                    f"TEXTO FUENTE:\n{texto_fuente}"
                ),
            },
        ],
    )

    return response.output_text.strip()