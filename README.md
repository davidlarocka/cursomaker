<p align="center">
  <img src="branding/cursomaker-logo-primary.png" alt="CursoMaker" width="760">
</p>

# CursoMaker

CursoMaker transforma los documentos de un curso en artefactos revisables y,
cuando se solicita, los ejecuta en Moodle. `execute_cursomaker.py` es el único
punto de entrada oficial: interpreta los argumentos y presenta el resultado.
La lógica del pipeline vive en `services/`, los contratos de datos en `models/`
y las llamadas a Moodle en `tools/`.

Este README describe el proceso de entrada de un curso nuevo, qué hace cada
etapa, qué información necesita y qué revisar antes de permitir escrituras en
Moodle.

## 1. Entradas de un curso

Cada curso se prepara en su propia carpeta bajo `documents/`. El flujo principal
requiere dos PDF: el manual que sirve de fuente para los contenidos del curso y
el documento que describe actividades y evaluaciones.

```text
documents/
    omi101/                    # carpeta de entrada; usar un identificador corto
        config.json            # identidad y configuración del curso
        manual.pdf             # contenido y material fuente
        actividades.pdf        # actividades, tests y evaluaciones
        examen_final.pdf       # opcional; para cargar preguntas al banco
    omi402/
        config.json
        manual.pdf
        actividades.pdf
```

`omi101` y `omi402` son ejemplos de identificadores internos para OMI 1.01 y
OMI 4.02. La carpeta debe ser única por curso y conviene usar letras minúsculas,
números y guiones bajos, sin espacios ni puntos. El nombre visible completo se
define por separado en `config.json`.

### Manual (`manual.pdf`)

- Incluye el contenido que debe convertirse en secciones y páginas Moodle.
- Puede incluir figuras e imágenes pedagógicas que el pipeline visual analizará.
- El PDF debe contener texto seleccionable y extraíble. CursoMaker no ejecuta
  OCR; si el documento es un escaneo, pásalo primero por OCR y revisa que el
  texto resultante sea correcto.
- Verifica que las páginas tengan orientación correcta, que el texto no esté
  cortado y que títulos, tablas y numeración sean legibles.

### Actividades y evaluaciones (`actividades.pdf`)

- Describe actividades de desarrollo, discusión, H5P, tests, respuestas y
  retroalimentaciones que deban crearse en Moodle.
- Mantén clara la separación por módulo. El módulo identificado en este PDF se
  debe poder asociar con una sección generada desde el manual.
- Las preguntas de un test deben incluir sus alternativas y la respuesta
  correcta cuando el documento la especifique. CursoMaker no debe completar
  respuestas que falten por inferencia.
- También debe tener texto extraíble; no se realiza OCR automático.

Los archivos pueden conservar su nombre original si se declaran en la
configuración, pero se recomienda copiarlos con los nombres `manual.pdf` y
`actividades.pdf` para que el ingreso de cada curso sea consistente.

## 2. Configuración de entrada (`config.json`)

Crear un `config.json` en la carpeta del curso. Ejemplo para un curso nuevo:

```json
{
  "nombre": "OMI 1.01 — Nombre completo del curso",
  "shortname": "omi101",
  "descripcion": "Descripción opcional del curso",
  "categoria_id": 1,
  "manual": "manual.pdf",
  "actividades": "actividades.pdf",
  "modulo_secciones": {}
}
```

Campos admitidos:

| Campo | Obligatorio | Uso |
|---|---|---|
| `nombre` | Sí | Nombre completo del curso. Debe coincidir con el nombre existente en Moodle si se reutiliza un curso. |
| `shortname` | Sí | Identificador único del curso en Moodle, por ejemplo `omi101`. |
| `descripcion` | No | Descripción que se incorpora al Content Blueprint. Por defecto queda vacía. |
| `categoria_id` | No | ID de categoría Moodle donde crear el curso. Por defecto es `1`. |
| `manual` | No | PDF del manual, relativo a esta carpeta. Por defecto `manual.pdf`. |
| `actividades` | No | PDF de actividades, relativo a esta carpeta. Por defecto `actividades.pdf`. |
| `modulo_secciones` | No | Correspondencia explícita entre número de módulo y título exacto de sección Moodle. |

La configuración valida que `nombre` y `shortname` no estén vacíos, que
`categoria_id` sea positivo, que ambos documentos tengan extensión `.pdf` y
que los archivos existan. No coloques credenciales en `config.json`.

### Correspondencia entre módulos y secciones

CursoMaker intenta relacionar cada módulo del PDF de actividades con una
sección del Content Blueprint por título. Tolera mayúsculas, espacios y
prefijos como `Módulo I:` o `Módulo 1:` si coinciden el número y el título.
Cuando los nombres difieran, completa `modulo_secciones` con títulos exactos
de las secciones que se generaron en `blueprint.json`:

```json
"modulo_secciones": {
  "1": "Módulo I: Introducción al tema",
  "2": "Módulo II: Procedimientos"
}
```

Las claves son números de módulo expresados como texto en JSON. No asignes un
módulo a un número de sección Moodle: el valor debe ser el título de sección.
Primero genera y revisa los dos blueprints; agrega el mapeo solo para los
módulos que no puedan asociarse automáticamente.

## 3. Preparar una nueva carpeta de entrada

Desde la raíz del repositorio, crear las carpetas de los cursos y copiar los
PDF recibidos. Por ejemplo:

```bash
mkdir -p documents/omi101 documents/omi402

# Copiar los PDF recibidos a las carpetas correspondientes y dejarlos como:
# documents/omi101/manual.pdf
# documents/omi101/actividades.pdf
# documents/omi402/manual.pdf
# documents/omi402/actividades.pdf
```

Después, crear `documents/omi101/config.json` y
`documents/omi402/config.json` con sus respectivos nombres, shortnames y
categorías. No reutilices accidentalmente el shortname de otro curso.

Antes de ejecutar, revisar:

1. Cada curso tiene su propio `config.json`, `manual.pdf` y `actividades.pdf`.
2. El nombre y shortname corresponden al curso correcto.
3. La categoría Moodle existe y el ID es el esperado.
4. Ambos PDF abren, contienen texto seleccionable y corresponden a la versión
   aprobada por el cliente.
5. Los módulos están identificados con claridad en el PDF de actividades.
6. Si se conoce el ID de curso Moodle, verificar que corresponde al servidor
   definido por `MOODLE_URL` antes de cargar preguntas al banco.

Las reglas actuales de `.gitignore` excluyen nuevos archivos bajo `documents/`,
`assets/` y `output/`. Sin embargo, `.gitignore` no deja de versionar archivos
que ya estaban registrados en Git. Antes de publicar cambios, comprobar con
`git ls-files documents assets output` qué archivos continúan dentro del
repositorio. Los PDF del cliente, imágenes extraídas, credenciales y resultados
generados deben mantenerse fuera del repositorio público.

## 4. Entorno y credenciales

Usar el entorno virtual del proyecto:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install openai 'pydantic>=2' python-dotenv pymupdf beautifulsoup4 requests weasyprint
```

Las dependencias usadas por el código son Pydantic 2, OpenAI, python-dotenv,
PyMuPDF, BeautifulSoup4 y requests. Para ejecutar pruebas unitarias también se
requiere pytest (`python -m pip install pytest`). En macOS, dentro del entorno
virtual, el comando habitual es `python`; si no está disponible, activar
`.venv` o usar `python3`.

Crear `.env` en la raíz del repositorio. Nunca subirlo a Git:

```dotenv
OPENAI_API_KEY=clave_de_api
MOODLE_URL=https://tu-moodle/aulavirtual
MOODLE_TOKEN=token_del_servicio_web
```

`OPENAI_API_KEY` se necesita para generar blueprints y analizar/mapear imágenes.
`MOODLE_URL` y `MOODLE_TOKEN` se necesitan únicamente al consultar o modificar
Moodle y para cargar preguntas al banco. No incluir una barra final en
`MOODLE_URL`.

El usuario/token Moodle debe poder ejecutar las funciones web empleadas por el
proyecto. Entre ellas están las funciones core para consultar/crear cursos y
leer sus secciones, además de las funciones `local_cursomaker_*` para crear
secciones, páginas, imágenes, asignaciones, foros, cuestionarios, preguntas y
actividades H5P. El plugin local CursoMaker debe estar instalado y habilitado
en el Moodle destino. Los nombres exactos de las funciones invocadas se
encuentran en `tools/` y `services/`.

## 5. Ejecutar por etapas y revisar las entradas

Desde la raíz del repositorio y con `.venv` activado:

```bash
# Curso OMI 1.01: generar cada artefacto por separado
python execute_cursomaker.py documents/omi101 --etapa contenido
python execute_cursomaker.py documents/omi101 --etapa assessment
python execute_cursomaker.py documents/omi101 --etapa imagenes

# Validar los artefactos y el mapeo antes de conectar con Moodle
python execute_cursomaker.py documents/omi101 --etapa moodle --dry-run
```

Repetir para `documents/omi402`. No ejecutes `moodle` real ni el pipeline
completo hasta revisar los resultados generados.

| Etapa | Lee | Genera o hace |
|---|---|---|
| `contenido` | `manual.pdf`, `config.json` | Llama a OpenAI y guarda `blueprint.json`, con secciones, páginas y páginas fuente. |
| `assessment` | `actividades.pdf`, `config.json` | Llama a OpenAI y guarda `assessment_blueprint.json`, con actividades y evaluaciones agrupadas por módulo. |
| `imagenes` | `manual.pdf`, `blueprint.json` | Extrae imágenes incrustadas, analiza candidatas, las relaciona con contenidos y subsecciones, y guarda los mapas y el `blueprint_render.json`. Llama a OpenAI para análisis y asignaciones que lo requieran. |
| `moodle --dry-run` | Artefactos de las tres etapas anteriores y los documentos originales | Valida consistencia, imágenes y correspondencia de módulos. No hace llamadas ni escrituras en Moodle. |
| `moodle` | Los mismos artefactos, `.env` y Moodle accesible | Ejecuta el contenido y las actividades en Moodle y guarda checkpoints y resumen. Puede crear el curso si no existe. |
| `todo` | Toda la entrada del curso | Ejecuta contenido, assessment, imágenes y luego Moodle real. **No es una previsualización.** |

Los nombres `contenido`, `assessment` e `imagenes` producen artefactos locales,
pero no crean actividades Moodle. La etapa `moodle` necesita esos artefactos
previamente generados, incluso si se usa con `--dry-run`.

### Revisar antes de ejecutar en Moodle

Abrir y revisar:

- `output/<carpeta>/blueprint.json`: identidad, secciones, títulos, texto y
  páginas fuente deben reflejar el manual.
- `output/<carpeta>/assessment_blueprint.json`: módulos, actividades, tests,
  instrucciones, respuestas y páginas fuente deben reflejar el PDF de
  actividades.
- `output/<carpeta>/image_analysis.json` y `image_mapping.json`: comprobar que
  las imágenes incluidas sean pedagógicas y estén asignadas al contenido
  correcto.
- `output/<carpeta>/blueprint_render.json` y
  `subsection_image_mapping.json`: revisar la distribución visual final.
- `config.json`: completar `modulo_secciones` si la validación indica que un
  módulo no coincide con una sección.

Los PDFs son la fuente, pero el resultado generado requiere revisión humana.
En particular, validar instrucciones, respuestas correctas, nombres y
ubicación de cada actividad antes de usar la ejecución real.

## 6. Ejecución real en Moodle

Cuando las revisiones y el `dry-run` estén correctos:

```bash
python execute_cursomaker.py documents/omi101 --etapa moodle
```

La ejecución busca el curso por `shortname`. Si no existe, lo crea oculto en
`categoria_id`. Si ya existe, su nombre debe coincidir con `nombre` y debe
permanecer oculto para que el pipeline lo reutilice. El comando real crea y
verifica páginas y actividades según sus checkpoints; puede actualizar una
página existente para igualarla al blueprint. No actualiza una actividad
Assessment modificada en el lugar: si cambia después de ejecutarse, la ejecución
se detiene y requiere revisión. No lo uses contra producción hasta confirmar
URL, token, categoría y destino.

El pipeline verifica las páginas y las actividades creadas, y registra el
progreso para reanudación. Si una actividad o su destino cambia después de
ejecutarse, requiere revisión. Si Moodle ya contiene una actividad con el
mismo título y tipo pero no existe checkpoint, la ejecución se detiene en vez
de reutilizarla a ciegas.

Algunas H5P pueden quedar pendientes por recursos faltantes. Image Hotspots
también queda pendiente mientras no esté disponible el empaquetador de ese
tipo. El resumen final indica cuántas actividades quedaron pendientes.

Para ejecutar todo en una sola operación —incluida la escritura real en
Moodle— se puede usar:

```bash
python execute_cursomaker.py documents/omi101
```

Por defecto `--etapa` es `todo`, que ejecuta Moodle realmente. Para una
ejecución final más controlable, se recomienda generar y revisar por etapas,
y ejecutar `moodle` explícitamente.

## 7. Archivos generados y reanudación

Las carpetas `assets/` y `output/` se crean automáticamente en la raíz del
proyecto. **El nombre de la carpeta de entrada**, no el shortname, determina
el subdirectorio de resultados:

```text
documents/omi101/       -> assets/omi101/ y output/omi101/
documents/omi402/       -> assets/omi402/ y output/omi402/
```

Los resultados típicos dentro de `output/<carpeta>/` son:

```text
blueprint.json
assessment_blueprint.json
image_analysis.json
image_mapping.json
blueprint_render.json
subsection_image_mapping.json
execution_render_checkpoint.json
execution_assessment_checkpoint.json
execution_summary.json
```

Los paquetes H5P se guardan dentro de subcarpetas de `output/<carpeta>/h5p/`.
Las imágenes extraídas quedan en `assets/<carpeta>/`. La etapa del banco de
preguntas guarda sus archivos en `output/<carpeta>/question_bank/`, separados
por servidor y curso.

Conservar checkpoints y carpetas de `output/` entre reintentos: permiten
reanudar sin duplicar lo ya confirmado. No borrar checkpoints para forzar una
repetición. Si cambias el manual o el PDF de actividades, regenera la etapa
afectada y vuelve a revisar los artefactos dependientes antes de ejecutar
Moodle. Los cambios posteriores a una ejecución remota pueden requerir
reconciliación manual.

## 8. Carga opcional del examen final al banco de preguntas

Esta etapa carga preguntas a un curso Moodle existente y no crea un
cuestionario ni las agrega a una sección. Coloca el PDF como
`documents/<carpeta>/examen_final.pdf` o pasa otra ruta con `--examen`.

Formato que reconoce el parser:

```text
P1. Enunciado de la pregunta
a) Primera alternativa
b) Segunda alternativa
c) Tercera alternativa
d) Cuarta alternativa
Correcta: B

Banco de reserva
P2. Otra pregunta...
```

Cada pregunta debe identificarse como `P<número>.` y tener cuatro alternativas
en orden `a)`–`d)` y una clave explícita `Correcta: A/B/C/D`. Se recomienda
numerar de forma consecutiva desde P1 para facilitar la revisión; el parser no
valida que no haya saltos en la numeración.
El encabezado opcional `Banco de reserva` separa preguntas de reserva. Se
requiere texto PDF extraíble. CursoMaker conserva la clave indicada; no valida
su exactitud temática.

Primero extraer y revisar sin Moodle:

```bash
python execute_cursomaker.py documents/omi101 \
  --etapa banco-examen \
  --examen examen_final.pdf \
  --course-id 8 \
  --dry-run
```

El `course-id` debe existir en el servidor de `MOODLE_URL` y su shortname debe
coincidir con `shortname` de la configuración. `--dry-run` crea
`examen_final_blueprint.json` para revisión y no hace peticiones Moodle.

Tras validar la extracción, repetir sin `--dry-run` para crear categorías y
preguntas:

```bash
python execute_cursomaker.py documents/omi101 \
  --etapa banco-examen \
  --examen examen_final.pdf \
  --course-id 8
```

El banco principal y el banco de reserva se crean como categorías separadas.
Los checkpoints evitan volver a cargar preguntas confirmadas. Si un envío queda
con estado `enviando`, comprobar Moodle y reconciliar el checkpoint antes de
reintentar; no borrarlo ni volver a enviar automáticamente.

## 9. Pruebas

Ejecutar las pruebas unitarias desde la raíz:

```bash
python -m pytest tests/unit -q
```

No requieren credenciales y simulan llamadas externas. Los `test_*.py` de la
raíz son pruebas históricas de integración; algunas pueden realizar
operaciones reales al importarse. Para validar cambios automáticos, ejecutar
específicamente `tests/unit`.
