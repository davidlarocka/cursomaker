import json

from services.documents import (
    extraer_texto_pdf,
    obtener_texto_paginas,
)
from services.content_qa import procesar_qa_contenido
from services.qa_store import cargar_qa, guardar_qa


RUTA_PDF = "documents/MANUAL OMI 1.41.pdf"
RUTA_BLUEPRINT = "blueprint.json"
RUTA_QA = "blueprint_qa.json"
MAX_CONTENIDOS = None

# 1. Cargamos PDF y blueprint.
print("📄 Cargando documento...")

documento = extraer_texto_pdf(RUTA_PDF)

with open(
    RUTA_BLUEPRINT,
    encoding="utf-8",
) as archivo:
    blueprint = json.load(archivo)


# 2. Recuperamos el progreso anterior.
estado_qa = cargar_qa(RUTA_QA)

total = sum(
    len(seccion["contenidos"])
    for seccion in blueprint["secciones"]
)

procesados = 0


# 3. Recorremos todo el blueprint.
detener = False

for numero_seccion, seccion in enumerate(
    blueprint["secciones"],
    start=1,
):
    for numero_contenido, contenido in enumerate(
        seccion["contenidos"],
        start=1,
    ):
        procesados += 1

        if MAX_CONTENIDOS is not None and procesados > MAX_CONTENIDOS:
            detener = True
            break

        clave = (
            f"seccion_{numero_seccion}_"
            f"contenido_{numero_contenido}"
        )

        print()
        print("=" * 70)
        print(
            f"📚 [{procesados}/{total}] "
            f"{seccion['titulo']} → "
            f"{contenido['titulo']}"
        )

        # 4. Si ya fue aprobado anteriormente,
        #    no gastamos otra llamada a la API.
        existente = estado_qa["contenidos"].get(clave)

        if existente:
            estado_existente = existente.get("estado")

            if estado_existente == "aprobado":
                print("⏭️ Ya aprobado. Saltando...")
                continue

            if estado_existente == "requiere_revision":
                print("👤 Requiere revisión humana. Saltando...")
                continue

        # 5. Recuperamos solamente sus páginas fuente.
        texto_fuente = obtener_texto_paginas(
            documento,
            contenido["paginas_fuente"],
        )

        # 6. Ejecutamos auditoría + posibles correcciones.
        try:
            resultado = procesar_qa_contenido(
                titulo=contenido["titulo"],
                contenido=contenido["contenido"],
                texto_fuente=texto_fuente,
                max_intentos=2,
            )

            validacion = resultado["validacion"]

            estado_qa["contenidos"][clave] = {
                "seccion": seccion["titulo"],
                "titulo": contenido["titulo"],
                "paginas_fuente": contenido["paginas_fuente"],
                "estado": (
                    "aprobado"
                    if resultado["aprobado"]
                    else "requiere_revision"
                ),
                "correcciones": resultado["correcciones"],
                "fidelidad": validacion.fidelidad_fuente,
                "cobertura": validacion.cobertura_contenido,
                "afirmaciones_no_respaldadas": (
                    validacion.afirmaciones_no_respaldadas
                ),
                "omisiones_importantes": (
                    validacion.omisiones_importantes
                ),
                "contenido_original": contenido["contenido"],
                "contenido_final": resultado["contenido"],
            }

        except Exception as error:
            print(f"💥 Error procesando contenido: {error}")

            estado_qa["contenidos"][clave] = {
                "seccion": seccion["titulo"],
                "titulo": contenido["titulo"],
                "estado": "error",
                "error": str(error),
            }

        # 7. CHECKPOINT inmediatamente.
        guardar_qa(
            RUTA_QA,
            estado_qa,
        )

        print("💾 Progreso guardado.")

    # OJO: este if está FUERA del for de contenidos.
    if detener:
        break

print()
print("=" * 70)
print("🏁 QA FINALIZADO")
print("=" * 70)

aprobados = sum(
    1
    for item in estado_qa["contenidos"].values()
    if item.get("estado") == "aprobado"
)

revision = sum(
    1
    for item in estado_qa["contenidos"].values()
    if item.get("estado") == "requiere_revision"
)

errores = sum(
    1
    for item in estado_qa["contenidos"].values()
    if item.get("estado") == "error"
)

print(f"✅ Aprobados: {aprobados}")
print(f"⚠️ Revisión humana: {revision}")
print(f"💥 Errores: {errores}")
print(f"📄 Total: {total}")