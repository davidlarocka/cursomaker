from tools.courses import _moodle_request


resultado = _moodle_request(
    "local_cursomaker_add_quiz_question",
    {
        "quizid": 7,
        "questionid": 64,
        "page": 1,
        "maxmark": 1,
    },
)


print("=== RESULTADO ASIGNACIÓN 2 ===")
print(f"Creada: {resultado['created']}")
print(f"Quiz ID: {resultado['quizid']}")
print(f"Question ID: {resultado['questionid']}")
print(f"Slot ID: {resultado['slotid']}")