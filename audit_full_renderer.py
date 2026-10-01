import json

from models.render_blueprint import CursoRender
from services.html_renderer import (
    renderizar_contenido,
)


RUTA_RENDER = "blueprint_render.json"
RUTA_MAPPING = "subsection_image_mapping.json"


with open(
    RUTA_RENDER,
    "r",
    encoding="utf-8",
) as archivo:
    curso = CursoRender.model_validate(
        json.load(archivo)
    )


with open(
    RUTA_MAPPING,
    "r",
    encoding="utf-8",
) as archivo:
    datos_mapping = json.load(archivo)


mapping = datos_mapping["asignaciones"]


total_contenidos = 0
total_toggles = 0
total_imagenes = 0
total_tablas = 0
errores = []


for seccion in curso.secciones:

    print()
    print(f"📁 {seccion.titulo}")

    for contenido in seccion.contenidos:

        total_contenidos += 1

        try:
            html = renderizar_contenido(
                contenido,
                mapping,
            )

            if not html.strip():
                raise RuntimeError(
                    "HTML vacío."
                )

            toggles = html.count(
                'class="cm-toggle"'
            )

            imagenes = html.count(
                'class="cm-figure"'
            )

            tablas = html.count(
                'class="cm-table"'
            )

            total_toggles += toggles
            total_imagenes += imagenes
            total_tablas += tablas

            print(
                f"  ✅ {contenido.titulo}"
                f" | toggles={toggles}"
                f" | imágenes={imagenes}"
                f" | tablas={tablas}"
            )

        except Exception as error:

            errores.append(
                {
                    "contenido": contenido.titulo,
                    "error": str(error),
                }
            )

            print(
                f"  ❌ {contenido.titulo}"
                f" | {error}"
            )


print()
print("=" * 70)
print("🔎 AUDITORÍA COMPLETA DEL RENDERER")
print("=" * 70)

print(
    f"📄 Contenidos procesados: {total_contenidos}"
)

print(
    f"🧩 Toggles generados:    {total_toggles}"
)

print(
    f"🖼️ Imágenes insertadas:  {total_imagenes}"
)

print(
    f"📊 Tablas renderizadas:   {total_tablas}"
)

print(
    f"❌ Errores:               {len(errores)}"
)


if errores:
    print()
    print("Errores encontrados:")

    for error in errores:
        print(
            f"- {error['contenido']}: "
            f"{error['error']}"
        )

else:
    print()
    print(
        "✅ Las 28 páginas pueden "
        "renderizarse correctamente."
    )