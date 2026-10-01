import json

from models.render_blueprint import CursoRender

from pathlib import Path

from datetime import datetime
from pathlib import Path
import argparse

from tools.courses import (
    obtener_secciones,
    subir_imagen_pagina,
    actualizar_pagina,
)

from services.html_renderer import renderizar_contenido


CURSO_ID = 7

CHECKPOINT_PATH = Path(
    "execution_render_checkpoint.json"
)


def guardar_checkpoint(datos):
    datos["actualizado_en"] = (
        datetime.now().isoformat(
            timespec="seconds"
        )
    )

    CHECKPOINT_PATH.write_text(
        json.dumps(
            datos,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def cargar_checkpoint():
    if not CHECKPOINT_PATH.exists():
        return {
            "curso_id": CURSO_ID,
            "paginas": {},
        }

    datos = json.loads(
        CHECKPOINT_PATH.read_text(
            encoding="utf-8"
        )
    )

    if datos.get("curso_id") != CURSO_ID:
        raise RuntimeError(
            "El checkpoint pertenece a "
            "otro curso Moodle."
        )

    return datos


def cargar_blueprint():
    with open(
        "blueprint_render.json",
        encoding="utf-8",
    ) as f:
        return CursoRender.model_validate(
            json.load(f)
        )


def construir_mapa_moodle(curso_id):
    secciones = obtener_secciones(curso_id)

    mapa = {}

    for seccion in secciones:
        for actividad in seccion["actividades"]:

            if actividad["tipo"] != "page":
                continue

            nombre = actividad["nombre"]

            if nombre in mapa:
                raise RuntimeError(
                    "Página Moodle duplicada: "
                    f"{nombre}"
                )

            mapa[nombre] = {
                "coursemodule_id": actividad["id"],
                "seccion_numero": seccion["numero"],
                "seccion_nombre": seccion["nombre"],
            }

    return mapa


def construir_plan(curso, mapa_moodle):
    plan = []
    titulos_blueprint = set()

    for seccion in curso.secciones:
        for contenido in seccion.contenidos:

            titulo = contenido.titulo

            if titulo in titulos_blueprint:
                raise RuntimeError(
                    "Título duplicado en blueprint: "
                    f"{titulo}"
                )

            titulos_blueprint.add(titulo)

            actividad = mapa_moodle.get(titulo)

            if actividad is None:
                raise RuntimeError(
                    "No existe página Moodle para: "
                    f"{titulo}"
                )

            imagenes = [
                bloque.imagen
                for bloque in contenido.bloques
                if bloque.tipo == "imagen"
                and bloque.imagen is not None
            ]

            plan.append({
                "titulo": titulo,
                "coursemodule_id": (
                    actividad["coursemodule_id"]
                ),
                "seccion_numero": (
                    actividad["seccion_numero"]
                ),
                "imagenes": imagenes,
            })

    # También detectamos páginas Moodle que no estén
    # representadas por el blueprint.
    extras = (
        set(mapa_moodle.keys())
        - titulos_blueprint
    )

    if extras:
        raise RuntimeError(
            "Hay páginas Moodle fuera del blueprint: "
            + ", ".join(sorted(extras))
        )

    return plan


def ejecutar_pagina(
    item,
    contenido,
    mapping,
    checkpoint,
):
    cmid = item["coursemodule_id"]
    titulo = item["titulo"]

    print()
    print("=" * 80)
    print(f"🚀 EJECUTANDO CM {cmid}")
    print(titulo)
    print("=" * 80)

    # -------------------------------------------------
    # 1. Subir imágenes
    # -------------------------------------------------

    imagenes_subidas = []

    for imagen in item["imagenes"]:
        print(
            f"📤 Subiendo {imagen.archivo}..."
        )

        resultado = subir_imagen_pagina(
            cmid,
            imagen.ruta,
        )

        imagenes_subidas.append(
            resultado["filename"]
        )

    # -------------------------------------------------
    # 2. Renderizar HTML para Moodle
    # -------------------------------------------------

    html = renderizar_contenido(
        contenido,
        mapping,
        modo="moodle",
    )

    if "documents/assets/" in html:
        raise RuntimeError(
            f"CM {cmid}: el HTML contiene "
            "una ruta local."
        )

    # -------------------------------------------------
    # 3. Actualizar + read-back
    # -------------------------------------------------

    resultado = actualizar_pagina(
        cmid,
        titulo,
        html,
    )

    if not resultado["verificada"]:
        raise RuntimeError(
            f"CM {cmid}: Moodle no pudo "
            "verificar la actualización."
        )

    # -------------------------------------------------
    # 4. Checkpoint SOLO después de verificar
    # -------------------------------------------------

    checkpoint["paginas"][str(cmid)] = {
        "titulo": titulo,
        "estado": "verificada",
        "imagenes": imagenes_subidas,
        "html_caracteres": len(html),
    }

    guardar_checkpoint(
        checkpoint
    )

    print(
        f"✅ CM {cmid} verificado "
        "y registrado en checkpoint."
    )

    return resultado

def pagina_esta_verificada(
    checkpoint,
    coursemodule_id,
):
    pagina = checkpoint.get(
        "paginas",
        {}
    ).get(
        str(coursemodule_id)
    )

    return (
        pagina is not None
        and pagina.get("estado") == "verificada"
    )
    
def ejecutar_plan(
    plan,
    curso,
    mapping,
):
    checkpoint = cargar_checkpoint()

    contenidos = {
        contenido.titulo: contenido
        for seccion in curso.secciones
        for contenido in seccion.contenidos
    }

    ejecutadas = 0
    omitidas = 0

    for item in plan:
        cmid = item["coursemodule_id"]
        titulo = item["titulo"]

        if pagina_esta_verificada(
            checkpoint,
            cmid,
        ):
            print(
                f"⏭️  CM {cmid} ya verificado: "
                f"{titulo}"
            )
            omitidas += 1
            continue

        ejecutar_pagina(
            item,
            contenidos[titulo],
            mapping,
            checkpoint,
        )

        ejecutadas += 1

    print()
    print("=" * 80)
    print("🏁 EJECUCIÓN FINALIZADA")
    print("=" * 80)
    print("Ejecutadas:", ejecutadas)
    print("Omitidas por checkpoint:", omitidas)
    print(
        "Total verificadas:",
        len(checkpoint["paginas"]),
    )

    if len(checkpoint["paginas"]) != len(plan):
        raise RuntimeError(
            "La ejecución terminó, pero no "
            "todas las páginas quedaron verificadas."
        )

    print()
    print("✅ Todas las páginas quedaron verificadas.")    

def main():
    parser = argparse.ArgumentParser(
        description="Renderiza CursoMaker en Moodle"
    )

    parser.add_argument(
        "--execute",
        action="store_true",
        help=(
            "Ejecuta las modificaciones en Moodle. "
            "Sin esta opción solo se realiza dry-run."
        ),
    )

    args = parser.parse_args()
    print()
    print("🧪 CURSOMAKER — DRY RUN")
    print("=" * 80)

    curso = cargar_blueprint()

    mapa_moodle = construir_mapa_moodle(
        CURSO_ID
    )

    plan = construir_plan(
        curso,
        mapa_moodle,
    )

    total_imagenes = 0

    for item in plan:
        cantidad = len(item["imagenes"])
        total_imagenes += cantidad

        print()
        print(
            f"CM {item['coursemodule_id']:>3} | "
            f"{item['titulo']}"
        )

        if not item["imagenes"]:
            print("      └─ sin imágenes")
            continue

        for imagen in item["imagenes"]:
            print(
                "      └─ "
                f"{imagen.archivo}"
            )

    
    
    
    with open(
        "subsection_image_mapping.json",
        encoding="utf-8",
    ) as f:
        mapping = json.load(f)["asignaciones"]

    contenidos_por_titulo = {
        contenido.titulo: contenido
        for seccion in curso.secciones
        for contenido in seccion.contenidos
    }

    errores = []
    total_html = 0
    total_pluginfile = 0

    for item in plan:
        titulo = item["titulo"]
        contenido = contenidos_por_titulo[titulo]

        # 1. Validar archivos físicos.
        for imagen in item["imagenes"]:
            ruta = Path(imagen.ruta)

            if not ruta.is_file():
                errores.append(
                    f"{titulo}: no existe {ruta}"
                )

        # 2. Renderizar exactamente como se enviaría a Moodle.
        try:
            html = renderizar_contenido(
                contenido,
                mapping,
                modo="moodle",
            )
        except Exception as exc:
            errores.append(
                f"{titulo}: error de render: {exc}"
            )
            continue

        total_html += 1

        # 3. Nunca deben sobrevivir rutas locales.
        if "documents/assets/" in html:
            errores.append(
                f"{titulo}: contiene ruta local"
            )

        # 4. Cada imagen del contenido debe aparecer
        #    exactamente una vez mediante PLUGINFILE.
        for imagen in item["imagenes"]:
            referencia = (
                "@@PLUGINFILE@@/"
                + imagen.archivo
            )

            cantidad = html.count(referencia)

            if cantidad != 1:
                errores.append(
                    f"{titulo}: {imagen.archivo} "
                    f"aparece {cantidad} veces"
                )
            else:
                total_pluginfile += 1

    print()
    print("🔍 VALIDACIÓN DE ARTEFACTOS")
    print("=" * 80)
    print(
        "HTML renderizados:",
        total_html,
    )
    print(
        "Referencias PLUGINFILE:",
        total_pluginfile,
    )
    print(
        "Errores:",
        len(errores),
    )

    if errores:
        print()

        for error in errores:
            print("❌", error)

        raise RuntimeError(
            "El dry-run encontró errores. "
            "No se permite ejecutar."
        )
    
    
    
    
    
    print()
    print("=" * 80)
    print(
        "Páginas planificadas:",
        len(plan),
    )
    print(
        "Imágenes planificadas:",
        total_imagenes,
    )

    if len(plan) != 28:
        raise RuntimeError(
            "Se esperaban exactamente 28 páginas."
        )

    if total_imagenes != 47:
        raise RuntimeError(
            "Se esperaban exactamente 47 imágenes."
        )

    print()
    print("✅ DRY RUN VÁLIDO")
    print("No se modificó Moodle.")
    
    if not args.execute:
        return

    print()
    print("⚠️ MODO EJECUCIÓN ACTIVADO")
    print(
        "Las páginas pendientes serán "
        "actualizadas en Moodle."
    )

    ejecutar_plan(
        plan,
        curso,
        mapping,
    )


if __name__ == "__main__":
    main()