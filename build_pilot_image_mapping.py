import json

from models.render_blueprint import CursoRender
from services.content_structure import (
    detectar_estructura_lista,
)
from services.image_section_mapper import (
    asignar_imagen_subseccion,
)


RUTA_RENDER = "blueprint_render.json"
RUTA_SALIDA = "pilot_image_mapping.json"

TITULO_PILOTO = (
    "Funciones y responsabilidades "
    "del personal en emergencias"
)


# --------------------------------------------------
# Cargar Render Blueprint
# --------------------------------------------------

with open(
    RUTA_RENDER,
    "r",
    encoding="utf-8",
) as archivo:
    render = CursoRender.model_validate(
        json.load(archivo)
    )


# --------------------------------------------------
# Localizar contenido piloto
# --------------------------------------------------

piloto = None

for seccion in render.secciones:
    for contenido in seccion.contenidos:

        if contenido.titulo == TITULO_PILOTO:
            piloto = contenido
            break

    if piloto:
        break


if piloto is None:
    raise RuntimeError(
        "No se encontró el contenido piloto."
    )


# --------------------------------------------------
# Detectar estructura interna
# --------------------------------------------------

bloque_html = next(
    bloque
    for bloque in piloto.bloques
    if bloque.tipo == "html"
)


estructura = detectar_estructura_lista(
    bloque_html.html
)


imagenes = [
    bloque.imagen
    for bloque in piloto.bloques
    if bloque.tipo == "imagen"
]


print()
print("=" * 70)
print("🧠 MAPEO INTERNO DEL PILOTO")
print("=" * 70)

print(
    f"🧩 Subsecciones: "
    f"{len(estructura.subsecciones)}"
)

print(
    f"🖼️ Imágenes: "
    f"{len(imagenes)}"
)


resultado_final = {
    "contenido": piloto.titulo,
    "imagenes": {},
}


# --------------------------------------------------
# Resolver cada imagen
# --------------------------------------------------

for numero, imagen in enumerate(
    imagenes,
    start=1,
):

    print()
    print(
        f"🖼️ [{numero}/{len(imagenes)}] "
        f"{imagen.archivo}"
    )

    resultado = asignar_imagen_subseccion(
        imagen=imagen,
        subsecciones=estructura.subsecciones,
    )

    indice = resultado.indice_subseccion

    subseccion = estructura.subsecciones[
        indice
    ]

    resultado_final["imagenes"][
        imagen.archivo
    ] = {
        "indice_subseccion": indice,
        "subseccion": subseccion.titulo,
        "descripcion": imagen.descripcion,
        "justificacion": resultado.justificacion,
    }

    print(
        f"   🎯 {subseccion.titulo}"
    )


# --------------------------------------------------
# Guardar
# --------------------------------------------------

with open(
    RUTA_SALIDA,
    "w",
    encoding="utf-8",
) as archivo:
    json.dump(
        resultado_final,
        archivo,
        ensure_ascii=False,
        indent=2,
    )


# --------------------------------------------------
# Resumen por subsección
# --------------------------------------------------

print()
print("=" * 70)
print("📊 DISTRIBUCIÓN VISUAL")
print("=" * 70)


for indice, subseccion in enumerate(
    estructura.subsecciones
):

    asignadas = [
        nombre
        for nombre, datos
        in resultado_final["imagenes"].items()
        if datos["indice_subseccion"] == indice
    ]

    print()
    print(
        f"{indice + 1}. "
        f"{subseccion.titulo}"
    )

    if asignadas:

        for nombre in asignadas:
            print(
                f"   🖼️ {nombre}"
            )

    else:
        print(
            "   — sin imagen —"
        )


print()
print("=" * 70)
print("🏁 MAPEO INTERNO FINALIZADO")
print("=" * 70)

print(
    f"🖼️ Imágenes procesadas: "
    f"{len(resultado_final['imagenes'])}"
)

print(
    f"💾 Resultado: "
    f"{RUTA_SALIDA}"
)