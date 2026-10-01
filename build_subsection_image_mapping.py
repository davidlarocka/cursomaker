import json

from models.render_blueprint import (
    CursoRender,
    ImagenSubseccionMapping,
)
from services.content_structure import (
    detectar_estructura_contenido,
)
from services.image_section_mapper import (
    asignar_imagen_subseccion,
)
from services.subsection_mapping_store import (
    cargar_checkpoint,
    guardar_checkpoint,
)

RUTA_RENDER = "blueprint_render.json"
RUTA_SALIDA = "subsection_image_mapping.json"

checkpoint = cargar_checkpoint(
    RUTA_SALIDA
)

asignaciones_guardadas = checkpoint.get(
    "asignaciones",
    {}
)

with open(
    RUTA_RENDER,
    "r",
    encoding="utf-8",
) as archivo:
    render = CursoRender.model_validate(
        json.load(archivo)
    )


resultados = asignaciones_guardadas
sin_estructura = []


for seccion in render.secciones:

    for contenido in seccion.contenidos:

        bloque_html = next(
            (
                bloque
                for bloque in contenido.bloques
                if bloque.tipo == "html"
            ),
            None,
        )

        imagenes = [
            bloque.imagen
            for bloque in contenido.bloques
            if (
                bloque.tipo == "imagen"
                and bloque.imagen is not None
            )
        ]

        if not imagenes:
            continue

        if bloque_html is None:
            continue

        deteccion = detectar_estructura_contenido(
            bloque_html.html
        )

        estructura = deteccion["estructura"]

        if estructura is None:

            for imagen in imagenes:
                sin_estructura.append({
                    "archivo": imagen.archivo,
                    "contenido": contenido.titulo,
                })

            continue

        for imagen in imagenes:
            

            if imagen.archivo in resultados:
                print(
                    f"♻️ Reutilizando: {imagen.archivo}"
                )
                continue
                if len(estructura.subsecciones) == 1:
                    subseccion = estructura.subsecciones[0]

                    resultados[imagen.archivo] = (
                        ImagenSubseccionMapping(
                            archivo=imagen.archivo,
                            contenido=contenido.titulo,
                            tipo_estructura=deteccion["tipo"],
                            indice_subseccion=0,
                            titulo_subseccion=subseccion.titulo,
                            justificacion=(
                                "Asignación determinística: "
                                "el contenido posee una única "
                                "subsección candidata."
                            ),
                        ).model_dump()
                    )

                    guardar_checkpoint(
                        RUTA_SALIDA,
                        {
                            "asignaciones": resultados,
                            "sin_estructura": sin_estructura,
                        },
                    )

                    print(
                        f"⚙️ Determinística: "
                        f"{imagen.archivo} → "
                        f"{subseccion.titulo}"
                    )

                    continue
            
            resolucion = asignar_imagen_subseccion(
                imagen,
                estructura.subsecciones,
            )

            subseccion = estructura.subsecciones[
                resolucion.indice_subseccion
            ]

            resultados[imagen.archivo] = (
                ImagenSubseccionMapping(
                    archivo=imagen.archivo,
                    contenido=contenido.titulo,
                    tipo_estructura=deteccion["tipo"],
                    indice_subseccion=(
                        resolucion.indice_subseccion
                    ),
                    titulo_subseccion=subseccion.titulo,
                    justificacion=(
                        resolucion.justificacion
                    ),
                ).model_dump()
            )

            guardar_checkpoint(
                RUTA_SALIDA,
                {
                    "asignaciones": resultados,
                    "sin_estructura": sin_estructura,
                },
            )

            print()
            print(
                f"🖼️ {imagen.archivo}"
            )

            print(
                f"   📄 {contenido.titulo}"
            )

            print(
                f"   → {subseccion.titulo}"
            )


guardar_checkpoint(
    RUTA_SALIDA,
    {
        "asignaciones": resultados,
        "sin_estructura": sin_estructura,
    },
)


print()
print("=" * 70)
print("🧠 MAPEO INTERNO FINALIZADO")
print("=" * 70)

print(
    f"🖼️ Imágenes asignadas: "
    f"{len(resultados)}"
)

print(
    f"📃 Imágenes sin estructura: "
    f"{len(sin_estructura)}"
)

print(
    f"💾 Guardado en: "
    f"{RUTA_SALIDA}"
)