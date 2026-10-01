from models.blueprint import (
    ContenidoBlueprint,
    SeccionBlueprint,
    CursoBlueprint,
)


contenido = ContenidoBlueprint(
    tipo="pagina",
    titulo="Marco Jurídico Internacional",
    contenido="<h2>Marco Jurídico Internacional</h2><p>Contenido de prueba.</p>",
    paginas_fuente=[5, 6, 7],
)

seccion = SeccionBlueprint(
    titulo="Módulo I. Marco normativo y responsabilidades",
    contenidos=[contenido],
)

curso = CursoBlueprint(
    nombre="Formación en Control de Multitudes",
    shortname="omi-1-41",
    descripcion="Curso de prueba generado a partir del manual OMI 1.41.",
    objetivos=[
        "Comprender el marco normativo aplicable.",
        "Identificar responsabilidades del personal.",
    ],
    secciones=[seccion],
)

print(curso.model_dump_json(indent=2))


print("\n=== PRUEBA DE BLUEPRINT INVÁLIDO ===")

try:
    contenido_invalido = ContenidoBlueprint(
        tipo="pagina",
        titulo="Contenido defectuoso",
        contenido="<p>Prueba</p>",
        paginas_fuente="cinco",
    )

    print(contenido_invalido)

except Exception as error:
    print("✅ Blueprint rechazado correctamente.")
    print(error)