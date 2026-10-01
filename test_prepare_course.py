from tools.courses import _moodle_request


resultado = _moodle_request(
    "local_cursomaker_prepare_course",
    {
        "courseid": 7,
    },
)

print("=== RESULTADO PREPARE COURSE ===")
print(f"Preparado: {resultado['prepared']}")
print(f"Curso ID: {resultado['courseid']}")
print(f"Usuario ID: {resultado['userid']}")
print(f"Rol ID: {resultado['roleid']}")
print(f"Enrol ID: {resultado['enrolid']}")
print(f"Matriculado: {resultado['enrolled']}")
print(f"Manage activities: {resultado['manageactivities']}")
print(f"Quiz manage: {resultado['quizmanage']}")