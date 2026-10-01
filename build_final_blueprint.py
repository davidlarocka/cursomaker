import copy
import json


RUTA_BLUEPRINT = "blueprint.json"
RUTA_QA = "blueprint_qa.json"
RUTA_FINAL = "blueprint_final.json"


# 1. Cargamos blueprint original.
with open(
    RUTA_BLUEPRINT,
    encoding="utf-8",
) as archivo:
    blueprint = json.load(archivo)


# 2. Cargamos resultados del QA.
with open(
    RUTA_QA,
    encoding="utf-8",
) as archivo:
    estado_qa = json.load(archivo)


# 3. Trabajamos sobre una copia.
blueprint_final = copy.deepcopy(blueprint)

total = 0
aprobados = 0


# 4. Sustituimos cada contenido por su versión aprobada.
for numero_seccion, seccion in enumerate(
    blueprint_final["secciones"],
    start=1,
):
    for numero_contenido, contenido in enumerate(
        seccion["contenidos"],
        start=1,
    ):
        total += 1

        clave = (
            f"seccion_{numero_seccion}_"
            f"contenido_{numero_contenido}"
        )

        resultado_qa = estado_qa["contenidos"].get(clave)

        if resultado_qa is None:
            raise RuntimeError(
                f"No existe resultado QA para {clave}."
            )

        if resultado_qa.get("estado") != "aprobado":
            raise RuntimeError(
                f"{clave} no está aprobado. "
                f"Estado: {resultado_qa.get('estado')}"
            )

        contenido["contenido"] = resultado_qa["contenido_final"]

        aprobados += 1


# 5. Verificación defensiva.
if aprobados != total:
    raise RuntimeError(
        f"Solo {aprobados} de {total} contenidos están aprobados."
    )


# 6. Guardamos el artefacto final.
with open(
    RUTA_FINAL,
    "w",
    encoding="utf-8",
) as archivo:
    json.dump(
        blueprint_final,
        archivo,
        ensure_ascii=False,
        indent=2,
    )


print()
print("✅ BLUEPRINT FINAL GENERADO")
print(f"📄 Contenidos: {total}")
print(f"✅ Aprobados: {aprobados}")
print(f"📁 Archivo: {RUTA_FINAL}")