from tools.courses import _moodle_request

import pprint

pprint.pp({
    "answers": [
        {
            "text": "Regular salarios",
            "fraction": 0,
        },
        {
            "text": "Proteger la vida humana",
            "fraction": 1,
        },
    ]
})

resultado = _moodle_request(
    "local_cursomaker_create_question",
    {
        "categoryid": 16,
        "name": "Pregunta piloto SOLAS",
        "questiontext": "¿Cuál es el objetivo principal del convenio SOLAS?",
        "answers": [
            {
                "text": "Regular salarios",
                "fraction": 0,
            },
            {
                "text": "Proteger la vida humana en el mar",
                "fraction": 1,
            },
            {
                "text": "Controlar rutas comerciales",
                "fraction": 0,
            },
            {
                "text": "Definir tarifas portuarias",
                "fraction": 0,
            },
        ],
    },
)


print("=== RESULTADO PREGUNTA ===")
print(f"Creada: {resultado['created']}")
print(f"Question ID: {resultado['questionid']}")
print(f"Category ID: {resultado['categoryid']}")