from tools.h5p import crear_h5p


resultado = crear_h5p(
    courseid=7,
    ruta_h5p="output/omi141-m01-drag-question.h5p",
)

print("=== RESULTADO H5P ===")
print(f"Creado: {resultado['created']}")
print(f"Content ID: {resultado['contentid']}")
print(f"Course ID: {resultado['courseid']}")
print(f"Context ID: {resultado['contextid']}")
print(f"Filename: {resultado['filename']}")