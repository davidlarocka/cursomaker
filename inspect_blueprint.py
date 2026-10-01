import json


with open("blueprint.json", encoding="utf-8") as archivo:
    blueprint = json.load(archivo)


print(f"🎓 {blueprint['nombre']}")
print(f"🔖 Shortname: {blueprint['shortname']}")

print()
print("🎯 OBJETIVOS")

for numero, objetivo in enumerate(
    blueprint["objetivos"],
    start=1,
):
    print(f"   {numero}. {objetivo}")


print()
print("📚 ESTRUCTURA")

total_contenidos = 0

for numero_seccion, seccion in enumerate(
    blueprint["secciones"],
    start=1,
):
    print()
    print(
        f"{numero_seccion}. {seccion['titulo']}"
    )

    for numero_contenido, contenido in enumerate(
        seccion["contenidos"],
        start=1,
    ):
        total_contenidos += 1

        paginas = ", ".join(
            str(pagina)
            for pagina in contenido["paginas_fuente"]
        )

        print(
            f"   {numero_contenido}. "
            f"{contenido['titulo']} "
            f"[páginas: {paginas}]"
        )


print()
print(f"📄 Total de contenidos: {total_contenidos}")