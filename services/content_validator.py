import os

from dotenv import load_dotenv
from openai import OpenAI

from models.blueprint import ValidacionContenido


load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)


def validar_contenido(titulo, contenido, texto_fuente):
    """
    Compara un contenido generado contra sus páginas fuente
    y devuelve una evaluación estructurada.
    """

    print(f"🔎 Validando contenido: {titulo}...")

    response = client.responses.parse(
        model="gpt-5.6",
        input=[
            {
                "role": "system",
                "content": (
                    "Eres el revisor de calidad de CursoMaker. "
                    "Debes verificar un contenido educativo generado "
                    "comparándolo exclusivamente con el texto fuente proporcionado. "
                    "No utilices conocimiento externo para justificar afirmaciones. "
                    "Identifica afirmaciones concretas que no estén respaldadas "
                    "por la fuente y omisiones importantes que puedan alterar "
                    "el sentido pedagógico del material. "
                    "No marques como problema simples cambios de redacción, "
                    "resúmenes o reorganizaciones que conserven fielmente "
                    "el significado de la fuente. "
                    "Aprueba únicamente cuando el contenido sea sustancialmente "
                    "fiel a la fuente y no contenga afirmaciones importantes "
                    "sin respaldo."
                    "Considera aprobado el contenido únicamente cuando "
                    "la fidelidad a la fuente sea al menos 95, "
                    "la cobertura del contenido sea al menos 90, "
                    "no existan afirmaciones importantes sin respaldo "
                    "y no existan omisiones importantes."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"TÍTULO DEL CONTENIDO:\n{titulo}\n\n"
                    f"CONTENIDO GENERADO:\n{contenido}\n\n"
                    f"TEXTO FUENTE:\n{texto_fuente}"
                ),
            },
        ],
        text_format=ValidacionContenido,
    )

    if response.output_parsed is None:
        raise RuntimeError(
            "No fue posible obtener una validación estructurada."
        )

    return response.output_parsed