from tools.courses import _moodle_request


resultado = _moodle_request(
    "local_cursomaker_create_question",
    {
        "categoryid": 16,
        "name": "Pregunta piloto SOLAS 2",
        "questiontext": "¿Qué aspecto regula principalmente el convenio SOLAS?",
        "answers": [
            {
                "text": "La seguridad de la vida humana en el mar",
                "fraction": 1,
            },
            {
                "text": "Las tarifas portuarias",
                "fraction": 0,
            },
            {
                "text": "Los salarios de las tripulaciones",
                "fraction": 0,
            },
            {
                "text": "Los impuestos marítimos",
                "fraction": 0,
            },
        ],
    },
)


print("=== RESULTADO PREGUNTA 2 ===")
print(f"Creada: {resultado['created']}")
print(f"Question ID: {resultado['questionid']}")
print(f"Category ID: {resultado['categoryid']}")