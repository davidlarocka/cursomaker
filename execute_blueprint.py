import json

from models.blueprint import CursoBlueprint
from tools.courses import (
    obtener_curso,
    crear_curso,
    crear_seccion,
    obtener_secciones,
    crear_pagina,
    obtener_pagina,
)

def obtener_o_crear_seccion(
    curso_id,
    titulo,
):
    """
    Obtiene una sección existente por nombre.
    Si no existe, la crea y verifica su creación.
    """

    print()
    print(f"📁 Preparando sección: {titulo}")

    secciones = obtener_secciones(curso_id)

    seccion = next(
        (
            item
            for item in secciones
            if item["nombre"] == titulo
        ),
        None,
    )

    if seccion is not None:
        print("♻️ La sección ya existe. Se reutilizará.")
        return seccion

    print("➕ La sección no existe. Creándola...")

    crear_seccion(
        curso_id=curso_id,
        nombre=titulo,
    )

    secciones = obtener_secciones(curso_id)

    seccion = next(
        (
            item
            for item in secciones
            if item["nombre"] == titulo
        ),
        None,
    )

    if seccion is None:
        raise RuntimeError(
            f"No pudo verificarse la sección '{titulo}'."
        )

    print("✅ Sección creada y verificada.")

    return seccion


def obtener_o_crear_pagina(
    curso_id,
    seccion,
    titulo,
    contenido,
):
    """
    Obtiene una página existente dentro de una sección.
    Si no existe, la crea.

    En ambos casos, vuelve a leerla desde Moodle y verifica
    que nombre y contenido coincidan exactamente.
    """

    print()
    print(f"📄 Preparando página: {titulo}")

    secciones = obtener_secciones(curso_id)

    seccion_actual = next(
        (
            item
            for item in secciones
            if item["id"] == seccion["id"]
        ),
        None,
    )

    if seccion_actual is None:
        raise RuntimeError(
            f"No pudo recuperarse la sección '{seccion['nombre']}'."
        )

    pagina_existente = next(
        (
            actividad
            for actividad in seccion_actual["actividades"]
            if actividad["tipo"] == "page"
            and actividad["nombre"] == titulo
        ),
        None,
    )

    if pagina_existente is not None:
        print("♻️ La página ya existe. Se reutilizará.")
        coursemodule_id = pagina_existente["id"]

    else:
        print("➕ La página no existe. Creándola...")

        resultado = crear_pagina(
            curso_id=curso_id,
            seccion_numero=seccion["numero"],
            nombre=titulo,
            contenido=contenido,
        )

        coursemodule_id = resultado["coursemodule_id"]

    print("🔎 Verificando página en Moodle...")

    pagina = obtener_pagina(
        curso_id=curso_id,
        coursemodule_id=coursemodule_id,
    )

    if not pagina.get("encontrada"):
        raise RuntimeError(
            f"No pudo recuperarse la página '{titulo}' "
            f"después de prepararla."
        )

    if pagina["nombre"] != titulo:
        raise RuntimeError(
            f"El título almacenado en Moodle no coincide "
            f"para la página '{titulo}'."
        )

    if pagina["contenido"] != contenido:
        raise RuntimeError(
            f"El HTML almacenado en Moodle no coincide "
            f"con el blueprint para '{titulo}'."
        )

    print("✅ Página lista y verificada.")

    return pagina

RUTA_BLUEPRINT = "blueprint_final.json"

# Por ahora SIEMPRE True.
DRY_RUN = False


print("📦 Cargando blueprint final...")

with open(
    RUTA_BLUEPRINT,
    encoding="utf-8",
) as archivo:
    datos = json.load(archivo)


blueprint = CursoBlueprint.model_validate(datos)

print("🔎 Comprobando si el curso ya existe en Moodle...")

curso_existente = obtener_curso(
    blueprint.shortname
)

if curso_existente.get("encontrado"):
    curso = curso_existente["curso"]

    print()
    print("🔄 CURSO EXISTENTE ENCONTRADO")
    print(f"🆔 Moodle ID: {curso['id']}")
    print(f"🎓 Nombre: {curso['nombre']}")
    print(f"🔖 Shortname: {curso['shortname']}")

    if curso["nombre"] != blueprint.nombre:
        raise RuntimeError(
            "El shortname pertenece a un curso con "
            "un nombre diferente al blueprint."
        )

    if curso["visible"]:
        raise RuntimeError(
            "El curso existente está visible. "
            "Ejecución bloqueada por seguridad."
        )

    print("✅ El curso existente coincide con el blueprint.")
    print("🔒 El curso está oculto.")
    print("▶️ Es seguro continuar sobre este curso.")

else:
    print("ℹ️ El curso todavía no existe.")


print()
print("=" * 70)
print("🚀 PLAN DE EJECUCIÓN MOODLE")
print("=" * 70)

print(f"🎓 Curso: {blueprint.nombre}")
print(f"🔖 Shortname: {blueprint.shortname}")
print(f"📚 Secciones: {len(blueprint.secciones)}")


total_contenidos = sum(
    len(seccion.contenidos)
    for seccion in blueprint.secciones
)

print(f"📄 Contenidos: {total_contenidos}")

print()


for numero_seccion, seccion in enumerate(
    blueprint.secciones,
    start=1,
):
    print(
        f"📁 CREAR SECCIÓN {numero_seccion}: "
        f"{seccion.titulo}"
    )

    for contenido in seccion.contenidos:
        print(
            f"   └── 📄 CREAR PÁGINA: "
            f"{contenido.titulo}"
        )


print()
print("=" * 70)

if DRY_RUN:
    print("🛡️ DRY-RUN ACTIVADO")
    print("No se realizó ningún cambio en Moodle.")

else:
    print("⚠️ EJECUCIÓN REAL ACTIVADA")

    if curso_existente.get("encontrado"):
        print()
        print("🔄 MODO REANUDACIÓN")
        print(
            f"Continuando sobre el curso Moodle "
            f"ID {curso_existente['curso']['id']}."
        )
        
        curso_id = curso_existente["curso"]["id"]

        print()
        
        print()
        print("🧪 EJECUCIÓN CONTROLADA")
        print(
            f"Se procesarán las {len(blueprint.secciones)} "
            f"secciones del blueprint."
        )

        secciones_procesadas = 0
        paginas_procesadas = 0

        for seccion_blueprint in blueprint.secciones:

            seccion_moodle = obtener_o_crear_seccion(
                curso_id=curso_id,
                titulo=seccion_blueprint.titulo,
            )

            print()
            print("✅ SECCIÓN LISTA")
            print(f"🆔 Section ID: {seccion_moodle['id']}")
            print(f"🔢 Número: {seccion_moodle['numero']}")
            print(f"📁 Nombre: {seccion_moodle['nombre']}")

            secciones_procesadas += 1

            for contenido in seccion_blueprint.contenidos:

                if contenido.tipo != "pagina":
                    raise RuntimeError(
                        f"Tipo de contenido todavía no soportado: "
                        f"{contenido.tipo}"
                    )

                pagina_moodle = obtener_o_crear_pagina(
                    curso_id=curso_id,
                    seccion=seccion_moodle,
                    titulo=contenido.titulo,
                    contenido=contenido.contenido,
                )

                print(
                    f"   ✅ Página verificada: "
                    f"{pagina_moodle['nombre']}"
                )

                paginas_procesadas += 1

        print()
        print("=" * 70)
        print("🏁 EJECUCIÓN CONTROLADA FINALIZADA")
        print(f"📁 Secciones procesadas: {secciones_procesadas}")
        print(f"📄 Páginas procesadas: {paginas_procesadas}")
        print("🔒 El curso permanece oculto.")
        print("=" * 70)
      

    else:
        print()
        print("🛑 No se creará un nuevo curso en esta prueba.")