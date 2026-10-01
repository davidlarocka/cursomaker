import json

from tools.courses import crear_quiz


COURSE_ID = 7
SECTION_NUMBER = 2


nombre = "Evaluación Módulo I - Sensibilización"
descripcion = """
<div class="cm-assessment cm-assessment-quiz">
<h4>Evaluación del módulo</h4>
<p>
Cuestionario de evaluación correspondiente al Módulo I.
</p>
</div>
"""


print("=== EJECUCIÓN PILOTO QUIZ ===")
print(f"Curso Moodle: {COURSE_ID}")
print(f"Sección Moodle: {SECTION_NUMBER}")
print(f"Nombre: {nombre}")
print()


resultado = crear_quiz(
    curso_id=COURSE_ID,
    seccion_numero=SECTION_NUMBER,
    nombre=nombre,
    descripcion=descripcion,
)


print("=== RESULTADO MOODLE ===")
print(f"Creado: {resultado['created']}")
print(f"Course module ID: {resultado['coursemoduleid']}")
print(f"Quiz instance ID: {resultado['instanceid']}")
print(f"Curso: {resultado['courseid']}")
print(f"Sección: {resultado['sectionnum']}")
print(f"Nombre: {resultado['name']}")