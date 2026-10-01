import json
import os

from dotenv import load_dotenv
from openai import OpenAI

from tools.courses import (
    actualizar_pagina,
    crear_curso,
    crear_seccion,
    crear_pagina,
    listar_cursos,
    obtener_curso,
    obtener_pagina,
    obtener_secciones,
)


# =========================
# CONFIGURACIÓN
# =========================

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise ValueError("No se encontró OPENAI_API_KEY en el archivo .env")

client = OpenAI(api_key=api_key)


# =========================
# HERRAMIENTAS
# =========================

tools = [
            {
            "type": "function",
            "name": "obtener_pagina",
            "description": (
                "Obtiene una página Moodle existente incluyendo su contenido HTML completo. "
                "Úsala antes de modificar una página cuando necesites conservar, revisar "
                "o ampliar su contenido actual. Necesita el ID del curso y el course module ID."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "curso_id": {
                        "type": "integer",
                        "description": "ID numérico del curso Moodle."
                    },
                    "coursemodule_id": {
                        "type": "integer",
                        "description": (
                            "Course module ID de la página. "
                            "Puede obtenerse mediante obtener_secciones."
                        )
                    }
                },
                "required": [
                    "curso_id",
                    "coursemodule_id"
                ],
                "additionalProperties": False
            },
            "strict": True
        },
        {
        "type": "function",
        "name": "actualizar_pagina",
        "description": (
            "Actualiza el nombre y el contenido HTML de una página Moodle existente. "
            "Necesita el course module ID de la página. "
            "Si no conoces ese ID, primero consulta la estructura del curso con "
            "obtener_secciones. No confundas el course module ID con el instance ID."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "coursemodule_id": {
                    "type": "integer",
                    "description": (
                        "Course module ID de la página Moodle. "
                        "Es el ID que devuelve obtener_secciones para la actividad."
                    )
                },
                "nombre": {
                    "type": "string",
                    "description": "Nombre que tendrá la página."
                },
                "contenido": {
                    "type": "string",
                    "description": "Nuevo contenido completo de la página en HTML."
                }
            },
            "required": [
                "coursemodule_id",
                "nombre",
                "contenido"
            ],
            "additionalProperties": False
        },
        "strict": True
    },
    {
        "type": "function",
        "name": "crear_pagina",
        "description": (
            "Crea una página de contenido HTML dentro de una sección de un curso Moodle. "
            "Debes conocer el ID numérico del curso y el NÚMERO de la sección. "
            "Si solo conoces el nombre de la sección, primero usa obtener_secciones "
            "para encontrar su número. No uses el ID interno de la sección."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "curso_id": {
                    "type": "integer",
                    "description": "ID numérico del curso Moodle."
                },
                "seccion_numero": {
                    "type": "integer",
                    "description": (
                        "Número de la sección dentro del curso, por ejemplo 2. "
                        "NO es el ID interno de la sección."
                    )
                },
                "nombre": {
                    "type": "string",
                    "description": "Nombre visible de la página."
                },
                "contenido": {
                    "type": "string",
                    "description": "Contenido educativo de la página en HTML."
                }
            },
            "required": [
                "curso_id",
                "seccion_numero",
                "nombre",
                "contenido"
            ],
            "additionalProperties": False
        },
        "strict": True
    },
    {
        "type": "function",
        "name": "obtener_secciones",
        "description": (
            "Obtiene las secciones reales de un curso Moodle y las actividades "
            "que contiene cada sección. Úsala cuando necesites conocer la "
            "estructura de un curso o localizar una sección específica."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "curso_id": {
                    "type": "integer",
                    "description": "ID numérico del curso Moodle."
                }
            },
            "required": [
                "curso_id"
            ],
            "additionalProperties": False
        },
        "strict": True
    },
    {
        "type": "function",
        "name": "crear_seccion",
        "description": (
            "Crea una nueva sección dentro de un curso Moodle existente. "
            "Necesita el ID numérico del curso y el nombre de la sección."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "curso_id": {
                    "type": "integer",
                    "description": "ID numérico del curso Moodle."
                },
                "nombre": {
                    "type": "string",
                    "description": "Nombre de la nueva sección."
                }
            },
            "required": [
                "curso_id",
                "nombre"
            ],
            "additionalProperties": False
        },
        "strict": True
    }
    ,{
        "type": "function",
        "name": "crear_curso",
        "description": (
            "Crea un nuevo curso en Moodle. "
            "Los cursos se crean ocultos por seguridad."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "nombre": {
                    "type": "string",
                    "description": "Nombre completo del nuevo curso."
                },
                "shortname": {
                    "type": "string",
                    "description": (
                        "Nombre corto único para Moodle, por ejemplo curso-ia-001."
                    )
                },
                "categoria_id": {
                    "type": "integer",
                    "description": "ID de la categoría Moodle donde crear el curso."
                }
            },
            "required": [
                "nombre",
                "shortname",
                "categoria_id"
            ],
            "additionalProperties": False
        },
        "strict": True
    }
    ,{
        "type": "function",
        "name": "listar_cursos",
        "description": (
            "Obtiene la lista completa de cursos disponibles en Moodle. "
            "Úsala cuando el usuario pregunte cuántos cursos existen, "
            "qué cursos hay o quiera comparar varios cursos."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False
        },
        "strict": True
    },
    {

        "type": "function",
        "name": "obtener_curso",
        "description": "Obtiene información de un curso existente en Moodle.",
        "parameters": {
            "type": "object",
            "properties": {
                "nombre": {
                    "type": "string",
                    "description": "Nombre del curso que se desea consultar."
                }
            },
            "required": ["nombre"],
            "additionalProperties": False
        },
        "strict": True
    }
]


# =========================
# EJECUTAR HERRAMIENTAS
# =========================

def ejecutar_herramienta(nombre, argumentos):

    if nombre == "listar_cursos":
        return listar_cursos()

    if nombre == "obtener_curso":
        return obtener_curso(**argumentos)
    if nombre == "crear_curso":
        return crear_curso(**argumentos)
    if nombre == "crear_seccion":
        return crear_seccion(**argumentos)
    if nombre == "obtener_secciones":
        return obtener_secciones(**argumentos)
    if nombre == "crear_pagina":
        return crear_pagina(**argumentos)
    if nombre == "actualizar_pagina":
        return actualizar_pagina(**argumentos)
    if nombre == "obtener_pagina":
        return obtener_pagina(**argumentos)

    raise ValueError(f"Herramienta desconocida: {nombre}")


# =========================
# AGENTE
# =========================
def preguntar_a_cursomaker(pregunta):
    response = client.responses.create(
        model="gpt-5.6",
        instructions=(
            "Eres CursoMaker, un agente especializado en administrar "
            "cursos Moodle. Utiliza las herramientas disponibles cuando "
            "necesites consultar o modificar Moodle. "
            "Nunca inventes IDs, cursos ni resultados. "
            "Si para realizar una acción necesitas primero obtener "
            "información, utiliza las herramientas necesarias."
        ),
        input=pregunta,
        tools=tools
    )

    while True:

        llamadas = [
            item
            for item in response.output
            if item.type == "function_call"
        ]

        # Si no hay herramientas pendientes,
        # el agente ya terminó.
        if not llamadas:
            return response.output_text

        resultados = []

        for item in llamadas:

            print(f"\n🔧 Tool: {item.name}")

            argumentos = json.loads(item.arguments)

            print(f"📦 Argumentos: {argumentos}")

            resultado = ejecutar_herramienta(
                item.name,
                argumentos
            )

            print(f"📤 Resultado: {resultado}")

            resultados.append({
                "type": "function_call_output",
                "call_id": item.call_id,
                "output": json.dumps(resultado)
            })

        # Devolvemos los resultados al modelo.
        # El modelo decide si ya puede responder
        # o si necesita ejecutar otra herramienta.
        response = client.responses.create(
            model="gpt-5.6",
            instructions=(
                "Eres CursoMaker, un agente especializado en administrar "
                "cursos Moodle. Utiliza las herramientas disponibles cuando "
                "necesites consultar o modificar Moodle. "
                "Nunca inventes IDs, cursos ni resultados. "
                "Si para realizar una acción necesitas primero obtener "
                "información, utiliza las herramientas necesarias."
            ),
            previous_response_id=response.id,
            input=resultados,
            tools=tools
        )


# =========================
# CHAT
# =========================

print()
print("🤖 CursoMaker v0.1")
print("-------------------")
print("Escribe 'salir' para terminar.")
print()


while True:

    pregunta = input("👤 Tú > ").strip()

    if not pregunta:
        continue

    if pregunta.lower() in ["salir", "exit", "quit"]:
        print("\n🤖 CursoMaker > ¡Hasta luego!")
        break

    try:

        respuesta = preguntar_a_cursomaker(pregunta)

        print()
        print(f"🤖 CursoMaker > {respuesta}")
        print()

    except Exception as error:

        print()
        print(f"❌ Error: {error}")
        print()