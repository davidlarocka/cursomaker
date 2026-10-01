import json


with open("blueprint.json", encoding="utf-8") as archivo:
    blueprint = json.load(archivo)


muestras = [
    (1, 0),  # Módulo I - primer contenido
    (2, 5),  # Módulo II - Cuadro de Obligaciones
    (4, 6),  # Módulo IV - asistencia a personas
]


for seccion_index, contenido_index in muestras:
    seccion = blueprint["secciones"][seccion_index]
    contenido = seccion["contenidos"][contenido_index]

    print()
    print("=" * 80)
    print(f"📚 SECCIÓN: {seccion['titulo']}")
    print(f"📄 CONTENIDO: {contenido['titulo']}")
    print(f"🔎 FUENTES: {contenido['paginas_fuente']}")
    print("=" * 80)
    print()
    print(contenido["contenido"])
    print()