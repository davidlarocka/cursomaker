"""Ejecutor de actividades que reutiliza las herramientas Moodle existentes."""
import hashlib
import json
from html import escape
from pathlib import Path
from typing import Any, Dict, Optional

from models.assessment_blueprint import AssessmentBlueprint
from services.assessment_renderer import renderizar_actividad_desarrollo, renderizar_actividad_discusion
from services.h5p_pipeline import crear_actividad_h5p
from services.h5p_generator import generar_drag_question, generar_single_choice_set, generar_fill_in_the_blanks
from services.blueprint_store import guardar_json
from tools import courses
from tools.questions import crear_categoria, crear_pregunta
from tools.quizzes import agregar_pregunta


TIPOS_MOODLE = {"desarrollo": "assign", "discusion": "forum", "quiz": "quiz", "h5p": "h5pactivity"}


def firma_actividad(actividad, section):
    return hashlib.sha256((actividad.model_dump_json() + str(section)).encode()).hexdigest()


def validar_actividades(blueprint):
    numeros = [m.numero for m in blueprint.modulos]
    if len(numeros) != len(set(numeros)):
        raise ValueError("Módulos Assessment con números duplicados.")
    ids = set()
    nombres = set()
    for modulo in blueprint.modulos:
        if not modulo.actividades:
            raise ValueError(f"El módulo {modulo.numero} no contiene actividades.")
        for actividad in modulo.actividades:
            if actividad.id_logico in ids or actividad.modulo != modulo.numero:
                raise ValueError(f"ID duplicado o módulo inconsistente: {actividad.id_logico}")
            ids.add(actividad.id_logico)
            clave = (modulo.numero, actividad.titulo, actividad.tipo)
            if clave in nombres:
                raise ValueError(f"Actividad duplicada: {actividad.titulo}")
            nombres.add(clave)
            if actividad.tipo == "desarrollo":
                renderizar_actividad_desarrollo(actividad)
            elif actividad.tipo == "discusion":
                renderizar_actividad_discusion(actividad)
            elif actividad.tipo == "quiz":
                if not actividad.preguntas:
                    raise ValueError(f"Quiz sin preguntas: {actividad.titulo}")
                numeros = [p.numero for p in actividad.preguntas]
                if len(numeros) != len(set(numeros)):
                    raise ValueError(f"Quiz con números de pregunta duplicados: {actividad.titulo}")
            elif actividad.tipo == "h5p" and not any(r.requerido and not r.disponible for r in actividad.recursos):
                tipo = actividad.h5p_tipo_ejecucion or actividad.h5p_tipo
                generadores = {
                    "drag_and_drop": generar_drag_question,
                    "course_presentation": generar_single_choice_set,
                    "single_choice_set": generar_single_choice_set,
                    "fill_in_the_blanks": generar_fill_in_the_blanks,
                }
                if tipo in generadores:
                    generadores[tipo](actividad)


def cargar_estado_assessment(ruta, courseid):
    estado = json.loads(Path(ruta).read_text(encoding="utf-8")) if ruta and Path(ruta).exists() else {}
    destino = (courses.MOODLE_URL or "").rstrip("/")
    if estado and (estado.get("courseid") != courseid or estado.get("moodle_url") != destino):
        raise RuntimeError("El checkpoint Assessment pertenece a otro curso o servidor Moodle.")
    return estado or {"courseid": courseid, "moodle_url": destino, "actividades": {}}


def completar_quiz(actividad, courseid, registro, guardar):
    quizid = registro["resultado"]["instanceid"]
    if not registro.get("categoryid"):
        categoria = crear_categoria(
            f"CursoMaker {courseid} - Módulo {actividad.modulo}", courseid=courseid,
            idnumber=f"cursomaker-course-{courseid}-module-{actividad.modulo}",
        )
        registro["categoryid"] = categoria["categoryid"]
        guardar()
    preguntas = registro.setdefault("preguntas", {})
    for pregunta in actividad.preguntas:
        clave = str(pregunta.numero)
        item = preguntas.setdefault(clave, {})
        if not item.get("questionid"):
            firma = hashlib.sha256((actividad.id_logico + pregunta.model_dump_json()).encode()).hexdigest()[:16]
            resultado = crear_pregunta(
                registro["categoryid"], f"CM-{courseid}-{firma}",
                f"<p>{escape(pregunta.enunciado)}</p>",
                [{"text": escape(a.texto), "fraction": 1 if a.correcta else 0} for a in pregunta.alternativas],
            )
            item["questionid"] = resultado["questionid"]
            guardar()
        if not item.get("slotid"):
            resultado = agregar_pregunta(quizid, item["questionid"], page=pregunta.numero)
            if not resultado.get("slotid"):
                raise RuntimeError("Moodle no confirmó la asignación de la pregunta al quiz.")
            item["slotid"] = resultado["slotid"]
            guardar()


def ejecutar_assessment(
    blueprint: AssessmentBlueprint, courseid: int,
    modulo_secciones: Optional[Dict[int, int]] = None,
    output_dir: str = "output/h5p", checkpoint_path=None,
) -> Dict[str, Any]:
    validar_actividades(blueprint)
    secciones = courses.obtener_secciones(courseid)
    if modulo_secciones is None:
        modulo_secciones = {}
        for modulo in blueprint.modulos:
            coincidencias = [s for s in secciones if s["nombre"].strip().casefold() == modulo.titulo.strip().casefold()]
            if len(coincidencias) != 1:
                raise ValueError(f"Indicar sección explícita para módulo {modulo.numero}: {modulo.titulo}")
            modulo_secciones[modulo.numero] = coincidencias[0]["numero"]
    estado = cargar_estado_assessment(checkpoint_path, courseid)

    def guardar():
        if checkpoint_path:
            guardar_json(Path(checkpoint_path), estado)

    for modulo in blueprint.modulos:
        numero = modulo_secciones[modulo.numero]
        if not any(s["numero"] == numero for s in secciones):
            raise RuntimeError(f"No existe la sección Moodle {numero} para módulo {modulo.numero}.")
        for actividad in modulo.actividades:
            anterior = estado["actividades"].get(actividad.id_logico)
            if anterior and anterior["firma"] != firma_actividad(actividad, numero):
                raise RuntimeError(f"La actividad {actividad.id_logico} cambió después de ejecutarse; requiere revisión.")

    resultados = []
    for modulo in blueprint.modulos:
        section = modulo_secciones[modulo.numero]
        for actividad in modulo.actividades:
            firma = firma_actividad(actividad, section)
            registro = estado["actividades"].get(actividad.id_logico)
            tipo = TIPOS_MOODLE[actividad.tipo]
            existentes = [a for s in courses.obtener_secciones(courseid) if s["numero"] == section
                          for a in s["actividades"] if a["nombre"] == actividad.titulo and a["tipo"] == tipo]
            if len(existentes) > 1:
                raise RuntimeError(f"Actividad Moodle duplicada: {actividad.titulo}")
            if registro and registro.get("coursemodule"):
                if not existentes or existentes[0]["id"] != registro["coursemodule"]:
                    raise RuntimeError(f"La actividad registrada no coincide con Moodle: {actividad.titulo}")
                if registro.get("estado") == "verificada":
                    resultados.append(registro)
                    continue
            elif existentes:
                raise RuntimeError(f"Existe {actividad.titulo} sin checkpoint; revisar antes de reutilizarla.")
            if actividad.tipo == "h5p":
                faltantes = [r for r in actividad.recursos if r.requerido and not r.disponible]
                h5p_tipo = actividad.h5p_tipo_ejecucion or actividad.h5p_tipo
                if faltantes or h5p_tipo == "image_hotspots":
                    resultados.append({"id_logico": actividad.id_logico, "estado": "pendiente",
                                       "razon": "recurso_faltante" if faltantes else "empaquetador_no_disponible"})
                    continue
            if registro is None or not registro.get("coursemodule"):
                if actividad.tipo == "desarrollo":
                    resultado = courses.crear_assignment(courseid, section, actividad.titulo, renderizar_actividad_desarrollo(actividad))
                elif actividad.tipo == "discusion":
                    resultado = courses.crear_foro(courseid, section, actividad.titulo, renderizar_actividad_discusion(actividad))
                elif actividad.tipo == "quiz":
                    resultado = courses.crear_quiz(courseid, section, actividad.titulo, escape(actividad.instrucciones or ""))
                else:
                    carpeta = Path(output_dir) / hashlib.sha256(actividad.id_logico.encode()).hexdigest()[:16]
                    resultado = crear_actividad_h5p(actividad, courseid, section, output_dir=str(carpeta))
                    if not resultado.get("success"):
                        raise RuntimeError(f"No se creó H5P: {actividad.titulo}")
                cmid = resultado.get("coursemoduleid") or resultado.get("coursemodule")
                if not cmid:
                    raise RuntimeError(f"Moodle no devolvió el ID de actividad: {actividad.titulo}")
                registro = {"id_logico": actividad.id_logico, "firma": firma, "estado": "creada",
                            "tipo": actividad.tipo, "section": section, "coursemodule": cmid, "resultado": resultado}
                estado["actividades"][actividad.id_logico] = registro
                guardar()
            if actividad.tipo == "quiz":
                completar_quiz(actividad, courseid, registro, guardar)
            presentes = [a for s in courses.obtener_secciones(courseid) if s["numero"] == section
                         for a in s["actividades"] if a["id"] == registro["coursemodule"]
                         and a["nombre"] == actividad.titulo and a["tipo"] == tipo]
            if len(presentes) != 1:
                raise RuntimeError(f"No pudo verificarse la actividad en Moodle: {actividad.titulo}")
            registro["estado"] = "verificada"
            guardar()
            resultados.append(registro)
    pendientes = sum(r["estado"] == "pendiente" for r in resultados)
    return {"success": pendientes == 0, "courseid": courseid, "actividades_procesadas": len(resultados),
            "creadas": len(resultados) - pendientes, "pendientes": pendientes,
            "no_implementadas": 0, "resultados": resultados}
