from tools.courses import _moodle_request


resultado = _moodle_request(
    "local_cursomaker_create_question_category",
    {
        "courseid": 7,
        "name": "CursoMaker - Módulo I",
        "idnumber": "cursomaker-course-7-module-1",
    },
)

print("=== RESULTADO CATEGORÍA ===")
print(f"Creada: {resultado['created']}")
print(f"Category ID: {resultado['categoryid']}")
print(f"Context ID: {resultado['contextid']}")