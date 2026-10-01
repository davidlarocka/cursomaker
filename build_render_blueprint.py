import json

from models.blueprint import CursoBlueprint
from models.render_blueprint import (
    CursoRender,
    SeccionRender,
    ContenidoRender,
    BloqueRender,
    ImagenRender,
)


RUTA_BLUEPRINT = "blueprint_final.json"
RUTA_IMAGENES = "image_mapping.json"
RUTA_SALIDA = "blueprint_render.json"


print("📦 Cargando blueprint semántico...")


with open(
    RUTA_BLUEPRINT,
    "r",
    encoding="utf-8",
) as archivo:
    blueprint = CursoBlueprint.model_validate(
        json.load(archivo)
    )


print("🖼️ Cargando mapa de imágenes...")


with open(
    RUTA_IMAGENES,
    "r",
    encoding="utf-8",
) as archivo:
    mapa_imagenes = json.load(archivo)


secciones_render = []

imagenes_utilizadas = set()


for numero_seccion, seccion in enumerate(
    blueprint.secciones,
    start=1,
):

    contenidos_render = []

    for numero_contenido, contenido in enumerate(
        seccion.contenidos,
        start=1,
    ):

        bloques = []

        # Por ahora conservamos intacto el HTML
        # aprobado por nuestro pipeline de QA.
        bloques.append(
            BloqueRender(
                tipo="html",
                html=contenido.contenido,
            )
        )

        # Buscamos las imágenes que fueron asignadas
        # exactamente a este contenido.
        imagenes_contenido = []

        for nombre, imagen in mapa_imagenes[
            "imagenes"
        ].items():

            if (
                imagen["seccion_numero"]
                == numero_seccion
                and imagen["contenido_numero"]
                == numero_contenido
            ):
                imagenes_contenido.append(
                    (
                        nombre,
                        imagen,
                    )
                )

        # Orden estable según la página original.
        imagenes_contenido.sort(
            key=lambda item: (
                item[1]["pagina"],
                item[0],
            )
        )

        for nombre, imagen in imagenes_contenido:

            bloques.append(
                BloqueRender(
                    tipo="imagen",
                    imagen=ImagenRender(
                        archivo=nombre,
                        ruta=imagen["ruta"],
                        pagina_fuente=imagen["pagina"],
                        descripcion=imagen["descripcion"],
                        alt=imagen["descripcion"],
                    ),
                )
            )

            imagenes_utilizadas.add(nombre)

        contenidos_render.append(
            ContenidoRender(
                titulo=contenido.titulo,
                paginas_fuente=contenido.paginas_fuente,
                bloques=bloques,
            )
        )

    secciones_render.append(
        SeccionRender(
            titulo=seccion.titulo,
            contenidos=contenidos_render,
        )
    )


render = CursoRender(
    nombre=blueprint.nombre,
    shortname=blueprint.shortname,
    descripcion=blueprint.descripcion,
    secciones=secciones_render,
)


with open(
    RUTA_SALIDA,
    "w",
    encoding="utf-8",
) as archivo:
    json.dump(
        render.model_dump(),
        archivo,
        ensure_ascii=False,
        indent=2,
    )


total_contenidos = sum(
    len(seccion.contenidos)
    for seccion in render.secciones
)

total_imagenes = sum(
    1
    for seccion in render.secciones
    for contenido in seccion.contenidos
    for bloque in contenido.bloques
    if bloque.tipo == "imagen"
)

imagenes_mapeadas = len(
    mapa_imagenes["imagenes"]
)

imagenes_no_utilizadas = (
    set(mapa_imagenes["imagenes"].keys())
    - imagenes_utilizadas
)


print()
print("=" * 60)
print("🏗️ RENDER BLUEPRINT CONSTRUIDO")
print("=" * 60)

print(
    f"📁 Secciones: "
    f"{len(render.secciones)}"
)

print(
    f"📄 Contenidos: "
    f"{total_contenidos}"
)

print(
    f"🖼️ Imágenes mapeadas: "
    f"{imagenes_mapeadas}"
)

print(
    f"🖼️ Imágenes insertadas: "
    f"{total_imagenes}"
)

print(
    f"❓ Imágenes no utilizadas: "
    f"{len(imagenes_no_utilizadas)}"
)

if imagenes_no_utilizadas:
    print()
    print("⚠️ NO UTILIZADAS:")

    for nombre in sorted(
        imagenes_no_utilizadas
    ):
        print(
            f"   - {nombre}"
        )

print()
print(
    f"💾 Resultado: "
    f"{RUTA_SALIDA}"
)