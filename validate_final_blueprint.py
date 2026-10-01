import json
from collections import Counter

from models.blueprint import CursoBlueprint
from services.documents import extraer_texto_pdf


RUTA_PDF = "documents/MANUAL OMI 1.41.pdf"
RUTA_FINAL = "blueprint_final.json"


print("🔎 Validando blueprint final...")


# 1. Cargamos el PDF para conocer sus páginas reales.
documento = extraer_texto_pdf(RUTA_PDF)

total_paginas_pdf = documento["total_paginas"]


# 2. Cargamos el JSON.
with open(
    RUTA_FINAL,
    encoding="utf-8",
) as archivo:
    datos = json.load(archivo)


# 3. Validación estructural con Pydantic.
blueprint = CursoBlueprint.model_validate(datos)


errores = []
advertencias = []


# 4. Validaciones generales.
if not blueprint.nombre.strip():
    errores.append("El curso no tiene nombre.")

if not blueprint.shortname.strip():
    errores.append("El curso no tiene shortname.")

if not blueprint.secciones:
    errores.append("El curso no contiene secciones.")


# 5. Detectamos títulos de secciones duplicados.
titulos_secciones = [
    seccion.titulo.strip().lower()
    for seccion in blueprint.secciones
]

duplicados_secciones = [
    titulo
    for titulo, cantidad
    in Counter(titulos_secciones).items()
    if cantidad > 1
]

for titulo in duplicados_secciones:
    advertencias.append(
        f"Título de sección duplicado: {titulo}"
    )


# 6. Validamos cada contenido.
total_contenidos = 0

for numero_seccion, seccion in enumerate(
    blueprint.secciones,
    start=1,
):
    if not seccion.titulo.strip():
        errores.append(
            f"La sección {numero_seccion} no tiene título."
        )

    titulos_contenidos = [
        contenido.titulo.strip().lower()
        for contenido in seccion.contenidos
    ]

    duplicados = [
        titulo
        for titulo, cantidad
        in Counter(titulos_contenidos).items()
        if cantidad > 1
    ]

    for titulo in duplicados:
        advertencias.append(
            f"Contenido duplicado en sección "
            f"{numero_seccion}: {titulo}"
        )

    for numero_contenido, contenido in enumerate(
        seccion.contenidos,
        start=1,
    ):
        total_contenidos += 1

        referencia = (
            f"Sección {numero_seccion}, "
            f"contenido {numero_contenido}"
        )

        if contenido.tipo != "pagina":
            errores.append(
                f"{referencia}: tipo no permitido "
                f"'{contenido.tipo}'."
            )

        if not contenido.titulo.strip():
            errores.append(
                f"{referencia}: título vacío."
            )

        if not contenido.contenido.strip():
            errores.append(
                f"{referencia}: contenido vacío."
            )

        if not contenido.paginas_fuente:
            errores.append(
                f"{referencia}: no tiene páginas fuente."
            )

        for pagina in contenido.paginas_fuente:
            if pagina < 1 or pagina > total_paginas_pdf:
                errores.append(
                    f"{referencia}: página fuente "
                    f"{pagina} fuera del rango del PDF "
                    f"(1-{total_paginas_pdf})."
                )


# 7. Resultado.
print()
print("=" * 60)
print("📋 VALIDACIÓN FINAL")
print("=" * 60)

print(f"📚 Secciones: {len(blueprint.secciones)}")
print(f"📄 Contenidos: {total_contenidos}")
print(f"📖 Páginas PDF: {total_paginas_pdf}")
print(f"❌ Errores: {len(errores)}")
print(f"⚠️ Advertencias: {len(advertencias)}")


if errores:
    print()
    print("❌ ERRORES")

    for error in errores:
        print(f"   - {error}")


if advertencias:
    print()
    print("⚠️ ADVERTENCIAS")

    for advertencia in advertencias:
        print(f"   - {advertencia}")


if errores:
    raise SystemExit(
        "\n⛔ Blueprint rechazado."
    )


print()
print("✅ Blueprint válido para ejecución.")