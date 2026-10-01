# CursoMaker

Orquestador de generación de cursos desde documentos PDF y ejecución en Moodle.
`execute_cursomaker.py` maneja argumentos y presentación; `services/` contiene
la lógica y `models/` los contratos Pydantic.

## Documentos y configuración

```text
documents/omi110/
    config.json
    manual.pdf
    actividades.pdf
```

Configuración mínima:

```json
{
  "nombre": "OMI 1.10 — Cargas peligrosas",
  "shortname": "omi110",
  "categoria_id": 1
}
```

Opcionalmente pueden indicarse `descripcion`, `manual` y `actividades`.
Las rutas de los PDF se resuelven desde la carpeta del curso.
`assets/omi110/` y `output/omi110/` se crean desde la raíz del proyecto.

Assessment se asigna a las secciones del Content Blueprint por título,
ignorando diferencias de mayúsculas y espacios. También acepta el prefijo
`Módulo I:` o `Módulo 1:` si coinciden el número del módulo y el título completo.
Si los títulos difieren,
indicar explícitamente el destino por número de módulo:

```json
"modulo_secciones": {
  "1": "Título exacto de la sección en Content Blueprint",
  "2": "Título de otra sección"
}
```

No se asume que el módulo 1 pertenezca a una sección Moodle de número fijo.

## Entorno y ejecución

Activar el entorno virtual del proyecto. Las dependencias utilizadas son
Pydantic 2, OpenAI, python-dotenv, PyMuPDF, BeautifulSoup4 y requests.
El `.env` de la raíz o las variables del entorno deben proporcionar:

```dotenv
OPENAI_API_KEY=...
MOODLE_URL=https://tu-moodle/aulavirtual
MOODLE_TOKEN=...
```

El servidor necesita las funciones web de `local_cursomaker` ya utilizadas
por las herramientas del proyecto, además de las funciones core para cursos,
secciones y lectura de páginas. La validación local no necesita credenciales.

```bash
source .venv/bin/activate

# Generación individual
python execute_cursomaker.py documents/omi110 --etapa contenido
python execute_cursomaker.py documents/omi110 --etapa assessment
python execute_cursomaker.py documents/omi110 --etapa imagenes

# Ejecutar en Moodle con los artefactos ya generados
python execute_cursomaker.py documents/omi110 --etapa moodle

# Validar artefactos localmente sin consultar ni modificar Moodle
python execute_cursomaker.py documents/omi110 --etapa moodle --dry-run

# Pipeline completo: genera ambos blueprints, imágenes y escribe en Moodle
python execute_cursomaker.py documents/omi110
```

`--dry-run` omite las operaciones Moodle. En el pipeline completo, las etapas
anteriores siguen generando artefactos y utilizando OpenAI.
Los scripts históricos de generación y ejecución delegan en esta misma entrada.

## Ejecución Moodle

El curso se busca por shortname exacto. Si no existe se crea oculto; si existe,
debe coincidir en nombre y permanecer oculto. Se preparan las secciones, las
páginas y sus imágenes. El contenido de las páginas se compara mediante lectura
posterior, normalizando únicamente las URLs de archivos que transforma Moodle.

Assessment reutiliza los renderizadores de tareas y foros, las herramientas de
cuestionarios y preguntas y el pipeline H5P. Las actividades se comprueban por
ID, tipo, nombre y sección; las preguntas y slots conservan sus IDs en el
checkpoint. Esta comprobación de actividades no es una comparación de todo su
contenido interno.

Las actividades con recursos requeridos faltantes quedan pendientes. Image
Hotspots queda pendiente porque el pipeline existente tiene generador de
contenido pero todavía no tiene empaquetador. No se inventan recursos ni se
crean paquetes con ese tipo.

Los checkpoints se vinculan al curso y al servidor. Repetir `--etapa moodle`
conserva las actividades registradas y comprueba de nuevo las páginas.
Si una actividad Assessment registrada cambia, la ejecución pide revisión
para evitar reutilizar una versión anterior. Una actividad existente sin
checkpoint requiere revisión antes de reutilizarla.

## Resultados

Todos los JSON se guardan en `output/omi110/`:

- `blueprint.json` y `assessment_blueprint.json`.
- `image_analysis.json`, `image_mapping.json`, `blueprint_render.json` y
  `subsection_image_mapping.json`.
- `execution_render_checkpoint.json`, `execution_assessment_checkpoint.json`
  y `execution_summary.json`.

Los paquetes H5P se guardan en subcarpetas por actividad dentro de
`output/omi110/h5p/`. Las imágenes extraídas quedan en `assets/omi110/`.
El resumen distingue ejecución completada y ejecución con pendientes.

## Verificación

```bash
python -m pytest tests/unit -q
```

Las pruebas unitarias no necesitan credenciales y simulan las llamadas externas.
Los archivos `test_*.py` de la raíz son pruebas históricas de integración;
algunos ejecutan operaciones reales al importarse. Para la suite automática,
usar específicamente `tests/unit`.

## Banco de preguntas del examen final

Para cargar un PDF de examen al banco de preguntas de un curso existente:

```bash
python execute_cursomaker.py documents/omi110 --etapa banco-examen --examen examen_final.pdf --course-id 8
```

La ruta `--examen` es relativa al directorio del curso (o una ruta absoluta). Colocar
el documento en `documents/omi110/examen_final.pdf`. El `course-id` se interpreta
en el servidor definido por `MOODLE_URL`; su shortname debe coincidir con config.json.
Puede usarse en un curso visible, ya que no crea ni publica actividades.

Esta etapa usa la extracción PDF y las herramientas de categorías y preguntas
existentes. No usa OpenAI, no genera contenido ni assessment y no crea un quiz,
sección ni H5P. El formato admitido es texto extraíble con `P1.`, `P2.`, etc., cuatro
alternativas `a)` a `d)` y una clave explícita `Correcta: A/B/C/D` por pregunta.
La numeración debe ser consecutiva desde P1. El encabezado `Banco de reserva`
separa las preguntas opcionales. PDFs escaneados u otros formatos requieren revisión.
Se conserva literalmente la clave del documento; no se valida su exactitud temática.

Para revisar la extracción antes de enviar preguntas a Moodle:

```bash
python execute_cursomaker.py documents/omi110 --etapa banco-examen --examen examen_final.pdf --course-id 8 --dry-run
```

`--dry-run` no hace peticiones a Moodle: guarda `examen_final_blueprint.json` para
revisar textos, alternativas, respuestas y páginas fuente. El examen OMI 1.10
aportado contiene 50 preguntas principales y 10 de reserva. Se crean dos categorías
del curso: `CursoMaker omi110 - Examen final` y `CursoMaker omi110 - Reserva examen final`.
La nota máxima de 7 se configura cuando se cree el cuestionario que las utilice;
las preguntas conservan el punto individual que asigna el plugin actual.

Los checkpoints y resúmenes se guardan en `output/omi110/question_bank/`, separados
por servidor y curso. Conservar estos archivos: una repetición omite las preguntas
confirmadas en el checkpoint. Los cambios de contenido del examen se bloquean
para revisión. Un POST interrumpido o sin confirmación deja una pregunta `enviando`
y bloquea el reintento automático: comprobar en Moodle si se creó y reconciliar
su `questionid` en el checkpoint antes de continuar. No borrar checkpoints para
forzar una repetición. La confirmación procede de la respuesta del plugin; no
hay lectura remota posterior para detectar preguntas eliminadas manualmente.

Las funciones del servicio web necesarias son las mismas usadas por los tests:
`core_course_get_courses`, `local_cursomaker_create_question_category` y
`local_cursomaker_create_question`.
