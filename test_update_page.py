from tools.courses import obtener_pagina, actualizar_pagina

# Primero leemos el contenido REAL que existe actualmente en Moodle.
pagina_actual = obtener_pagina(
    curso_id=6,
    coursemodule_id=52
)

if not pagina_actual["encontrada"]:
    raise RuntimeError("No se encontró la página Bienvenida.")

print()
print("Contenido actual recuperado correctamente.")

# Enviamos exactamente el mismo contenido.
resultado = actualizar_pagina(
    coursemodule_id=52,
    nombre=pagina_actual["nombre"],
    contenido=pagina_actual["contenido"]
)

print()
print("Resultado:")
print(resultado)