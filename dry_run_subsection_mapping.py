import json

from models.render_blueprint import CursoRender
from services.content_structure import (
    detectar_estructura_contenido,
)
from services.subsection_mapping_store import (
    cargar_checkpoint,
)


RUTA_RENDER = "blueprint_render.json"
RUTA_CHECKPOINT = "subsection_image_mapping.json"


with open(
    RUTA_RENDER,
    "r",
    encoding="utf-8",
) as archivo:
    render = CursoRender.model_validate(
        json.load(archivo)
    )


checkpoint = cargar_checkpoint(
    RUTA_CHECKPOINT
)

guardadas = checkpoint.get(
    "asignaciones",
    {}
)


reutilizadas = 0
deterministicas = 0
requieren_gpt = 0
sin_estructura = 0
total = 0


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

        total += len(imagenes)

        if bloque_html is None:
            sin_estructura += len(imagenes)
            continue

        deteccion = detectar_estructura_contenido(
            bloque_html.html
        )

        estructura = deteccion["estructura"]

        if estructura is None:
            sin_estructura += len(imagenes)
            continue

        for imagen in imagenes:

            if imagen.archivo in guardadas:
                reutilizadas += 1

            elif len(
                estructura.subsecciones
            ) == 1:
                deterministicas += 1

            else:
                requieren_gpt += 1


print()
print("=" * 60)
print("🔎 DRY-RUN MAPPING DE IMÁGENES")
print("=" * 60)

print(
    f"🖼️ Total:              {total}"
)

print(
    f"♻️ Reutilizadas:       {reutilizadas}"
)

print(
    f"⚙️ Determinísticas:    {deterministicas}"
)

print(
    f"🧠 Requieren GPT:      {requieren_gpt}"
)

print(
    f"📃 Sin estructura:     {sin_estructura}"
)

print("-" * 60)

suma = (
    reutilizadas
    + deterministicas
    + requieren_gpt
    + sin_estructura
)

print(
    f"Σ Clasificadas:        {suma}"
)

print(
    "✅ Cuadra con total"
    if suma == total
    else "❌ NO CUADRA"
)