from tools.courses import obtener_secciones

secciones = obtener_secciones(6)

print()

for seccion in secciones:
    print(
        f"Sección {seccion['numero']} | "
        f"ID {seccion['id']} | "
        f"{seccion['nombre']} | "
        f"Visible: {seccion['visible']}"
    )

    for actividad in seccion["actividades"]:
        print(
            f"    └── {actividad['tipo']}: "
            f"{actividad['nombre']}"
        )