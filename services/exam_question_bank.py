"""Extrae exámenes de selección única y carga su banco sin crear actividades."""
import hashlib
import json
import re
from pathlib import Path

from models.assessment_blueprint import AlternativaPregunta, PreguntaSeleccionMultiple
from models.banco_examen import BancoExamen
from services.blueprint_store import guardar_blueprint, guardar_json
from services.documents import extraer_texto_pdf
from tools import courses, questions


def extraer_banco_examen(ruta):
    """Formato admitido: P1., a)..d), Correcta: A y Banco de reserva opcional."""
    documento = extraer_texto_pdf(ruta)
    lineas = []
    paginas = []
    for pagina in documento["paginas"]:
        for linea in pagina["texto"].splitlines():
            linea = linea.replace("\u200b", "").replace("✅", "").strip()
            if linea:
                lineas.append(linea)
                paginas.append(pagina["numero"])
    inicios = [(i, re.match(r"^P(\d+)\.\s*(.*)$", linea))
               for i, linea in enumerate(lineas) if re.match(r"^P\d+\.", linea)]
    if not inicios:
        raise ValueError("No se encontraron preguntas P1., P2., etc. El PDF debe contener texto extraíble.")
    reservas = [i for i, linea in enumerate(lineas) if re.search(r"banco de reserva", linea, re.I)]
    if len(reservas) > 1:
        raise ValueError("El documento contiene más de un encabezado de banco de reserva.")
    limite_reserva = reservas[0] if reservas else len(lineas)
    grupos = {"principales": [], "reserva": []}
    for posicion, (inicio, match) in enumerate(inicios):
        fin = inicios[posicion + 1][0] if posicion + 1 < len(inicios) else len(lineas)
        bloque = lineas[inicio:fin]
        claves = [(j, re.fullmatch(r"Correcta:\s*([A-D])\s*", linea, re.I))
                  for j, linea in enumerate(bloque) if re.match(r"^Correcta:", linea, re.I)]
        numero = int(match[1])
        if len(claves) != 1 or claves[0][1] is None:
            raise ValueError(f"P{numero}: se requiere una clave explícita Correcta: A/B/C/D.")
        indice_clave, clave = claves[0]
        opciones = [(j, re.match(r"^([a-d])\)\s*(.*)$", linea, re.I))
                    for j, linea in enumerate(bloque[:indice_clave])
                    if re.match(r"^[a-d]\)", linea, re.I)]
        if [m[1].lower() for _, m in opciones] != list("abcd"):
            raise ValueError(f"P{numero}: se esperaban cuatro alternativas a), b), c), d).")
        enunciado = " ".join([match[2]] + bloque[1:opciones[0][0]]).strip()
        alternativas = []
        for k, (indice, opcion) in enumerate(opciones):
            siguiente = opciones[k + 1][0] if k + 1 < len(opciones) else indice_clave
            texto = " ".join([opcion[2]] + bloque[indice + 1:siguiente]).strip()
            if not texto:
                raise ValueError(f"P{numero}: alternativa vacía.")
            alternativas.append(AlternativaPregunta(
                texto=texto, correcta=opcion[1].upper() == clave[1].upper(),
            ))
        if not enunciado:
            raise ValueError(f"P{numero}: enunciado vacío.")
        pregunta = PreguntaSeleccionMultiple(
            numero=numero, enunciado=enunciado, alternativas=alternativas,
            paginas_fuente=sorted(set(paginas[inicio:inicio + indice_clave + 1])),
        )
        grupos["reserva" if inicio > limite_reserva else "principales"].append(pregunta)
    return BancoExamen(documento_fuente=documento["archivo"], **grupos)


def ejecutar_banco_examen(contexto, examen, courseid, dry_run=False):
    if isinstance(courseid, bool) or not isinstance(courseid, int) or courseid < 1:
        raise ValueError("Indicar --course-id con un ID de curso positivo.")
    ruta = Path(examen)
    if not ruta.is_absolute():
        ruta = contexto.directorio / ruta
    banco = extraer_banco_examen(ruta)
    blueprint_path = contexto.output_dir / "examen_final_blueprint.json"
    guardar_blueprint(blueprint_path, banco)
    contexto.banco_examen_blueprint_path = blueprint_path
    resultado = {"estado": "validado" if dry_run else "completado", "courseid": courseid,
                 "principales": len(banco.principales), "reserva": len(banco.reserva)}
    if dry_run:
        contexto.banco_examen_resultado = resultado
        return contexto
    if not courses.MOODLE_URL or not courses.MOODLE_TOKEN:
        raise ValueError("Faltan MOODLE_URL o MOODLE_TOKEN en el entorno o en .env.")
    destino = courses.MOODLE_URL.rstrip("/")
    cursos = [c for c in courses.listar_cursos() if c["id"] == courseid]
    if len(cursos) != 1 or cursos[0]["shortname"] != contexto.config.shortname:
        raise RuntimeError("El curso de destino no coincide con el ID y shortname configurados.")
    ambito = hashlib.sha256(destino.encode()).hexdigest()[:16]
    carpeta = contexto.output_dir / "question_bank" / f"{ambito}-course-{courseid}"
    carpeta.mkdir(parents=True, exist_ok=True)
    checkpoint = carpeta / "examen_final_checkpoint.json"
    # Bloqueamos cambios semánticos, pero no cambios de nombre o paginación del PDF.
    contenido = {grupo: [p.model_dump(exclude={"paginas_fuente"}) for p in getattr(banco, grupo)]
                 for grupo in ("principales", "reserva")}
    firma = hashlib.sha256(json.dumps(contenido, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    estado = json.loads(checkpoint.read_text(encoding="utf-8")) if checkpoint.exists() else {
        "courseid": courseid, "moodle_url": destino, "firma": firma,
        "categorias": {}, "preguntas": {},
    }
    if (estado.get("courseid"), estado.get("moodle_url"), estado.get("firma")) != (courseid, destino, firma):
        raise RuntimeError("El checkpoint del examen corresponde a otro contenido o destino; requiere revisión.")
    if any(item.get("estado") == "enviando" for item in estado["preguntas"].values()):
        raise RuntimeError("Hay una pregunta con resultado remoto incierto. Revisar Moodle y el checkpoint antes de reintentar.")
    guardar_json(checkpoint, estado)
    creadas = 0
    omitidas = 0
    for grupo, etiqueta in (("principales", "Examen final"), ("reserva", "Reserva examen final")):
        lista = getattr(banco, grupo)
        if not lista:
            continue
        if not estado["categorias"].get(grupo):
            categoria = questions.crear_categoria(
                f"CursoMaker {contexto.config.shortname} - {etiqueta}", courseid=courseid,
                idnumber=f"cursomaker-course-{courseid}-final-{grupo}",
            )
            if not isinstance(categoria, dict) or not categoria.get("categoryid"):
                raise RuntimeError("Moodle no confirmó la categoría del examen.")
            estado["categorias"][grupo] = categoria["categoryid"]
            guardar_json(checkpoint, estado)
        for pregunta in lista:
            clave = str(pregunta.numero)
            if estado["preguntas"].get(clave, {}).get("questionid"):
                omitidas += 1
                continue
            # Persistir antes del POST impide duplicar ante timeout o interrupción.
            estado["preguntas"][clave] = {"estado": "enviando", "grupo": grupo}
            guardar_json(checkpoint, estado)
            respuesta = questions.crear_pregunta_desde_modelo(
                estado["categorias"][grupo], courseid, f"examen-final-{grupo}", pregunta,
            )
            estado["preguntas"][clave] = {"estado": "creada", "grupo": grupo,
                                          "questionid": respuesta["questionid"]}
            guardar_json(checkpoint, estado)
            creadas += 1
            print(f"Pregunta P{pregunta.numero} confirmada en el banco.")
    resultado.update(creadas=creadas, omitidas=omitidas, categorias=estado["categorias"],
                     checkpoint=str(checkpoint))
    reporte = guardar_json(carpeta / "examen_final_summary.json", resultado)
    contexto.banco_examen_report_path = reporte
    contexto.banco_examen_resultado = resultado
    return contexto
