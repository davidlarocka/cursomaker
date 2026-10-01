import json
import zipfile
from pathlib import Path
from typing import Any, Dict


class H5PValidationError(ValueError):
    """Error de validación determinística de un paquete H5P."""


def validar_paquete_h5p(ruta_h5p: Path) -> Dict[str, Any]:
    """
    Valida la estructura mínima de un paquete .h5p.

    Retorna el manifest y el contenido ya parseados
    si todas las validaciones pasan.
    """

    ruta_h5p = Path(ruta_h5p)

    if not ruta_h5p.exists():
        raise H5PValidationError(
            f"No existe el archivo H5P: {ruta_h5p}"
        )

    if not ruta_h5p.is_file():
        raise H5PValidationError(
            f"La ruta no corresponde a un archivo: {ruta_h5p}"
        )

    if ruta_h5p.suffix.lower() != ".h5p":
        raise H5PValidationError(
            "El archivo debe tener extensión .h5p"
        )

    try:
        with zipfile.ZipFile(ruta_h5p) as paquete:
            archivos = paquete.namelist()

            if "h5p.json" not in archivos:
                raise H5PValidationError(
                    "El paquete no contiene h5p.json"
                )

            if "content/content.json" not in archivos:
                raise H5PValidationError(
                    "El paquete no contiene content/content.json"
                )

            try:
                manifest = json.loads(paquete.read("h5p.json"))
            except json.JSONDecodeError as exc:
                raise H5PValidationError(
                    "h5p.json no contiene JSON válido"
                ) from exc

            try:
                contenido = json.loads(
                    paquete.read("content/content.json")
                )
            except json.JSONDecodeError as exc:
                raise H5PValidationError(
                    "content/content.json no contiene JSON válido"
                ) from exc

    except zipfile.BadZipFile as exc:
        raise H5PValidationError(
            "El archivo no es un ZIP/H5P válido"
        ) from exc

    if not manifest.get("title"):
        raise H5PValidationError(
            "h5p.json no contiene title"
        )

    if not manifest.get("mainLibrary"):
        raise H5PValidationError(
            "h5p.json no contiene mainLibrary"
        )

    if not manifest.get("preloadedDependencies"):
        raise H5PValidationError(
            "h5p.json no contiene preloadedDependencies"
        )
    if manifest["mainLibrary"] == "H5P.SingleChoiceSet":
        validar_single_choice_set(contenido)
    if manifest["mainLibrary"] == "H5P.DragQuestion":
        validar_drag_question(contenido)    
    if manifest["mainLibrary"] == "H5P.Blanks":
        validar_fill_in_the_blanks(contenido)

    return {
        "valido": True,
        "ruta": str(ruta_h5p),
        "main_library": manifest["mainLibrary"],
        "manifest": manifest,
        "contenido": contenido,
    }
    
def validar_single_choice_set(contenido: Dict[str, Any]) -> None:
    """
    Valida content.json para H5P.SingleChoiceSet 1.11.

    Contrato relevante:
    - Debe existir choices.
    - Debe haber al menos una pregunta.
    - Cada pregunta debe tener texto.
    - Cada pregunta debe tener entre 2 y 4 alternativas.
    - La primera alternativa representa la respuesta correcta.
    """

    choices = contenido.get("choices")

    if not isinstance(choices, list) or not choices:
        raise H5PValidationError(
            "SingleChoiceSet debe contener al menos una pregunta."
        )

    for indice, choice in enumerate(choices, start=1):
        pregunta = choice.get("question")

        if not isinstance(pregunta, str) or not pregunta.strip():
            raise H5PValidationError(
                f"La pregunta {indice} no contiene un enunciado válido."
            )

        respuestas = choice.get("answers")

        if not isinstance(respuestas, list):
            raise H5PValidationError(
                f"La pregunta {indice} no contiene una lista de alternativas."
            )

        if not 2 <= len(respuestas) <= 4:
            raise H5PValidationError(
                f"La pregunta {indice} debe tener entre 2 y 4 alternativas."
            )

        for numero, respuesta in enumerate(respuestas, start=1):
            if not isinstance(respuesta, str) or not respuesta.strip():
                raise H5PValidationError(
                    f"La alternativa {numero} de la pregunta "
                    f"{indice} está vacía."
                )

        normalizadas = [
            respuesta.strip().casefold()
            for respuesta in respuestas
        ]

        if len(normalizadas) != len(set(normalizadas)):
            raise H5PValidationError(
                f"La pregunta {indice} contiene alternativas duplicadas."
            )
def validar_drag_question(contenido: Dict[str, Any]) -> None:
    """
    Valida content.json para H5P.DragQuestion 1.15.

    Comprueba:
    - existencia de task
    - elements y dropZones no vacíos
    - referencias válidas en ambos sentidos
    - ningún elemento o zona queda huérfano
    - cada draggable contiene H5P.AdvancedText
    """

    try:
        task = contenido["params"]["question"]["task"]
    except (KeyError, TypeError) as exc:
        raise H5PValidationError(
            "DragQuestion no contiene params.question.task."
        ) from exc

    elements = task.get("elements")
    drop_zones = task.get("dropZones")

    if not isinstance(elements, list) or not elements:
        raise H5PValidationError(
            "DragQuestion debe contener al menos un elemento."
        )

    if not isinstance(drop_zones, list) or not drop_zones:
        raise H5PValidationError(
            "DragQuestion debe contener al menos una zona."
        )

    referencias_elementos = {
        str(i) for i in range(len(elements))
    }

    referencias_zonas = {
        str(i) for i in range(len(drop_zones))
    }

    # Validamos los elementos arrastrables.
    for indice, element in enumerate(elements):
        tipo = element.get("type")

        if not isinstance(tipo, dict):
            raise H5PValidationError(
                f"El elemento {indice} no contiene type válido."
            )

        if tipo.get("library") != "H5P.AdvancedText 1.1":
            raise H5PValidationError(
                f"El elemento {indice} no utiliza "
                "H5P.AdvancedText 1.1."
            )

        texto = tipo.get("params", {}).get("text")

        if not isinstance(texto, str) or not texto.strip():
            raise H5PValidationError(
                f"El elemento {indice} no contiene texto."
            )

        zonas = element.get("dropZones")

        if not isinstance(zonas, list) or not zonas:
            raise H5PValidationError(
                f"El elemento {indice} no está asociado "
                "a ninguna zona."
            )

        for zona in zonas:
            if str(zona) not in referencias_zonas:
                raise H5PValidationError(
                    f"El elemento {indice} referencia "
                    f"una zona inexistente: {zona}."
                )

    # Validamos las zonas destino.
    for indice, zone in enumerate(drop_zones):
        label = zone.get("label")

        if not isinstance(label, str) or not label.strip():
            raise H5PValidationError(
                f"La zona {indice} no contiene label."
            )

        correctos = zone.get("correctElements")

        if not isinstance(correctos, list) or not correctos:
            raise H5PValidationError(
                f"La zona {indice} no tiene elementos correctos."
            )

        for elemento in correctos:
            if str(elemento) not in referencias_elementos:
                raise H5PValidationError(
                    f"La zona {indice} referencia "
                    f"un elemento inexistente: {elemento}."
                )

        # Cada zona debe declarar elementos correctos válidos y
        # cada elemento debe poder soltarse en su zona correcta.
        for indice_zona, zone in enumerate(drop_zones):
            for element_ref in zone["correctElements"]:
                indice_elemento = int(element_ref)
                element = elements[indice_elemento]

                zonas_permitidas = {
                    str(x)
                    for x in element["dropZones"]
                }

                if str(indice_zona) not in zonas_permitidas:
                    raise H5PValidationError(
                        f"La zona {indice_zona} declara como correcto "
                        f"al elemento {element_ref}, pero ese elemento "
                        "no puede soltarse en esa zona."
                    )

        # En nuestro modelo de emparejamiento todos los elementos
        # deben poder probarse en todas las zonas.
        zonas_esperadas = {
            str(i)
            for i in range(len(drop_zones))
        }

        for indice, element in enumerate(elements):
            zonas_permitidas = {
                str(x)
                for x in element["dropZones"]
            }

            if zonas_permitidas != zonas_esperadas:
                raise H5PValidationError(
                    f"El elemento {indice} no puede soltarse en "
                    "todas las zonas."
                )
                
def validar_fill_in_the_blanks(contenido: Dict[str, Any]) -> None:
    """
    Valida contenido para H5P.Blanks 1.14.
    """

    descripcion = contenido.get("text")

    if not isinstance(descripcion, str) or not descripcion.strip():
        raise H5PValidationError(
            "Fill in the Blanks no contiene instrucciones."
        )

    questions = contenido.get("questions")

    if not isinstance(questions, list) or not questions:
        raise H5PValidationError(
            "Fill in the Blanks debe contener al menos "
            "un bloque de texto."
        )

    total_blancos = 0

    for indice, question in enumerate(questions, start=1):
        if not isinstance(question, str) or not question.strip():
            raise H5PValidationError(
                f"El bloque {indice} está vacío."
            )

        partes = question.split("*")

        # Cada blanco genera dos separadores *.
        if len(partes) % 2 == 0:
            raise H5PValidationError(
                f"El bloque {indice} contiene marcadores * "
                "sin cerrar."
            )

        blancos = partes[1::2]

        if not blancos:
            raise H5PValidationError(
                f"El bloque {indice} no contiene espacios "
                "en blanco."
            )

        for numero, blanco in enumerate(blancos, start=1):
            respuestas = [
                respuesta.strip()
                for respuesta in blanco.split("/")
            ]

            if not all(respuestas):
                raise H5PValidationError(
                    f"El blanco {numero} del bloque {indice} "
                    "contiene una respuesta vacía."
                )

            normalizadas = [
                respuesta.casefold()
                for respuesta in respuestas
            ]

            if len(normalizadas) != len(set(normalizadas)):
                raise H5PValidationError(
                    f"El blanco {numero} del bloque {indice} "
                    "contiene respuestas duplicadas."
                )

        total_blancos += len(blancos)

    if total_blancos < 1:
        raise H5PValidationError(
            "Fill in the Blanks no contiene espacios."
        )