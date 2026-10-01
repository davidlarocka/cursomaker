from typing import Any, Dict
import json
import zipfile
from pathlib import Path
import re
from models.assessment_blueprint import (
    H5PCoursePresentation,
    H5PFillInTheBlanks,
    H5PImageHotspots,
)

def generar_single_choice_set(
    actividad: H5PCoursePresentation,
) -> Dict[str, Any]:
    """
    Convierte una actividad Course Presentation en H5P.SingleChoiceSet.

    Las respuestas correctas de todas las situaciones forman el conjunto
    cerrado de alternativas. No se generan distractores nuevos.
    """

    alternativas = []

    for situacion in actividad.situaciones:
        respuesta = situacion.respuesta_correcta.strip()

        if not respuesta:
            raise ValueError(
                f"La situación {situacion.numero} no tiene respuesta correcta."
            )

        if respuesta not in alternativas:
            alternativas.append(respuesta)

    if len(alternativas) < 2:
        raise ValueError(
            "SingleChoiceSet necesita al menos dos alternativas distintas."
        )

    choices = []

    for situacion in actividad.situaciones:
        correcta = situacion.respuesta_correcta.strip()

        # SingleChoiceSet exige que la primera alternativa sea la correcta.
        respuestas = [
            correcta,
            *[alt for alt in alternativas if alt != correcta],
        ]

        choices.append(
            {
                "question": situacion.situacion,
                "answers": respuestas,
            }
        )

    return {
        "choices": choices,
    }
    
def generar_drag_question(actividad) -> Dict[str, Any]:
    """
    Convierte H5PDragAndDrop del blueprint en H5P.DragQuestion 1.15.

    Diseño:
    - Conceptos a la izquierda.
    - Definiciones arrastrables a la derecha.
    - Cada pareja i utiliza la relación i <-> i.
    """
    if len(actividad.parejas) < 2:
        raise ValueError(
            "DragQuestion necesita al menos dos parejas."
        )

    elements = []
    drop_zones = []

    total = len(actividad.parejas)

    # Repartimos verticalmente las parejas dentro del tablero.
    alto_fila = 100 / total

    for indice, pareja in enumerate(actividad.parejas):
        referencia = str(indice)

        y = indice * alto_fila + 1
        height = max(alto_fila - 2, 5)

        # Zona destino: concepto.
        drop_zones.append(
            {
                "x": 2,
                "y": y,
                "width": 32,
                "height": height,
                "correctElements": [referencia],
                "showLabel": True,
                "backgroundOpacity": 100,
                "tipsAndFeedback": {
                    "tip": "",
                },
                "single": True,
                "autoAlign": True,
                "label": f"<div>{pareja.concepto}</div>",
                "type": {
                    "library": "H5P.DragQuestionDropzone 0.1",
                },
            }
        )

        # Elemento arrastrable: definición.
        elements.append(
            {
                "x": 48,
                "y": y,
                "width": 48,
                "height": height,
                "dropZones": [
                    str(i) for i in range(total)
                ],
                "type": {
                    "library": "H5P.AdvancedText 1.1",
                    "params": {
                        "text": f"<p>{pareja.definicion}</p>",
                    },
                    "metadata": {
                        "contentType": "Text",
                        "license": "U",
                        "title": pareja.concepto,
                    },
                },
                "backgroundOpacity": 100,
                "multiple": False,
            }
        )

    return {
        "params": {
            "question": {
                "settings": {
                    "size": {
                        "width": 900,
                        "height": max(500, total * 90),
                    }
                },
                "task": {
                    "elements": elements,
                    "dropZones": drop_zones,
                },
            },
            "behaviour": {
                "enableRetry": True,
                "enableCheckButton": True,
                "singlePoint": False,
                "applyPenalties": True,
                "enableScoreExplanation": True,
                "dropZoneHighlighting": "dragging",
                "autoAlignSpacing": 2,
                "enableFullScreen": False,
                "showScorePoints": True,
                "showTitle": True,
                "dragHandleVisibility": True,
            },
            "scoreShow": "Comprobar",
            "submit": "Enviar",
            "tryAgain": "Intentar de nuevo",
            "scoreExplanation": (
                "Las respuestas correctas dan +1 punto. "
                "Las incorrectas dan -1 punto. "
                "La puntuación más baja posible es 0."
            ),
            "overallFeedback": [
                {
                    "from": 0,
                    "to": 100,
                }
            ],
            "grabbablePrefix": (
                "Elemento a colocar {num} de {total}."
            ),
            "grabbableSuffix": (
                "Colocado en zona de colocación {num}."
            ),
            "dropzonePrefix": (
                "Zona de colocación {num} de {total}."
            ),
            "noDropzone": "No es zona de colocación.",
            "tipLabel": "Mostrar pista.",
            "tipAvailable": "Pista disponible",
            "correctAnswer": "Respuesta correcta",
            "wrongAnswer": "Respuesta incorrecta",
            "feedbackHeader": "Retroalimentación",
            "scoreBarLabel": (
                "Has obtenido :num de un total de :total puntos"
            ),
            "scoreExplanationButtonLabel": (
                "Mostrar explicación de la puntuación"
            ),
            "localize": {
                "fullscreen": "Pantalla completa",
                "exitFullscreen": "Salir de pantalla completa",
            },
        },
        "metadata": {
            "title": actividad.titulo,
            "license": "U",
            "defaultLanguage": "es",
        },
        "title": actividad.titulo,
    }
    
def generar_image_hotspots(
    actividad: H5PImageHotspots,
) -> Dict[str, Any]:
    """
    Convierte H5PImageHotspots del blueprint
    en contenido compatible con H5P.ImageHotspots.
    """

    if not actividad.hotspots:
        raise ValueError(
            "Image Hotspots necesita al menos un hotspot."
        )

    # Buscar la imagen base.
    imagenes = [
        recurso
        for recurso in actividad.recursos
        if recurso.tipo == "imagen"
        and recurso.requerido
        and recurso.disponible
        and recurso.archivo
    ]

    if not imagenes:
        raise ValueError(
            "Image Hotspots requiere una imagen base disponible."
        )

    imagen = imagenes[0]

    if not imagen.archivo:
        raise ValueError(
            "El recurso de imagen no tiene archivo asociado."
        )

    hotspots = []

    for hotspot in actividad.hotspots:
        if hotspot.x is None or hotspot.y is None:
            raise ValueError(
                f"El hotspot '{hotspot.nombre}' no tiene coordenadas x/y."
            )

        hotspots.append({
            "position": {
                "x": hotspot.x,
                "y": hotspot.y,
            },
            "label": hotspot.nombre,
            "content": [
                {
                    "library": "H5P.Text 1.1",
                    "params": {
                        "text": hotspot.descripcion or hotspot.nombre,
                    },
                    "subContentId": "",
                }
            ],
        })

    return {
        "image": {
            "path": imagen.archivo,
            "alt": actividad.titulo,
        },
        "hotspot": hotspots,
    }
        
def generar_h5p_manifest_single_choice_set(
    titulo: str,
) -> Dict[str, Any]:
    """
    Genera el h5p.json para H5P.SingleChoiceSet 1.11.
    """

    return {
        "title": titulo,
        "language": "es",
        "mainLibrary": "H5P.SingleChoiceSet",
        "embedTypes": ["iframe"],
        "license": "U",
        "preloadedDependencies": [
            {
                "machineName": "H5P.SingleChoiceSet",
                "majorVersion": 1,
                "minorVersion": 11,
            }
        ],
    }    
    
def empaquetar_h5p(
    actividad: H5PCoursePresentation,
    ruta_salida: Path,
) -> Path:
    """
    Genera un paquete .h5p para una actividad ejecutada
    mediante H5P.SingleChoiceSet.
    """

    contenido = generar_single_choice_set(actividad)
    manifest = generar_h5p_manifest_single_choice_set(actividad.titulo)

    ruta_salida = Path(ruta_salida)

    if ruta_salida.suffix.lower() != ".h5p":
        raise ValueError("La ruta de salida debe terminar en .h5p")

    ruta_salida.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(
        ruta_salida,
        mode="w",
        compression=zipfile.ZIP_DEFLATED,
    ) as paquete:
        paquete.writestr(
            "h5p.json",
            json.dumps(
                manifest,
                ensure_ascii=False,
                indent=2,
            ),
        )

        paquete.writestr(
            "content/content.json",
            json.dumps(
                contenido,
                ensure_ascii=False,
                indent=2,
            ),
        )

    return ruta_salida

def generar_h5p_manifest_drag_question(
    titulo: str,
) -> Dict[str, Any]:
    """
    Genera h5p.json para H5P.DragQuestion 1.15.
    """
    return {
        "title": titulo,
        "language": "es",
        "mainLibrary": "H5P.DragQuestion",
        "embedTypes": ["iframe"],
        "license": "U",
        "preloadedDependencies": [
            {
                "machineName": "H5P.DragQuestion",
                "majorVersion": 1,
                "minorVersion": 15,
            }
        ],
    }


def empaquetar_drag_question(
    actividad,
    ruta_salida: Path,
) -> Path:
    """
    Genera un paquete .h5p ejecutable para H5P.DragQuestion 1.15.
    """
    contenido = generar_drag_question(actividad)
    manifest = generar_h5p_manifest_drag_question(
        actividad.titulo
    )

    ruta_salida = Path(ruta_salida)

    if ruta_salida.suffix.lower() != ".h5p":
        raise ValueError(
            "La ruta de salida debe terminar en .h5p"
        )

    ruta_salida.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with zipfile.ZipFile(
        ruta_salida,
        mode="w",
        compression=zipfile.ZIP_DEFLATED,
    ) as paquete:
        paquete.writestr(
            "h5p.json",
            json.dumps(
                manifest,
                ensure_ascii=False,
                indent=2,
            ),
        )

        paquete.writestr(
            "content/content.json",
            json.dumps(
                contenido,
                ensure_ascii=False,
                indent=2,
            ),
        )

    return ruta_salida

def generar_fill_in_the_blanks(
    actividad: H5PFillInTheBlanks,
) -> Dict[str, Any]:
    """
    Convierte H5PFillInTheBlanks del blueprint
    en contenido para H5P.Blanks 1.14.

    Cada secuencia de guiones bajos representa un blanco:
        *respuesta*
        *respuesta1/respuesta2*
    """

    texto = actividad.texto

    if not actividad.espacios:
        raise ValueError(
            "Fill in the Blanks necesita al menos un espacio."
        )

    numeros = {
        espacio.numero
        for espacio in actividad.espacios
    }

    esperados = set(
        range(1, len(actividad.espacios) + 1)
    )

    if numeros != esperados:
        raise ValueError(
            "Los espacios deben estar numerados "
            "consecutivamente desde 1."
        )

    marcadores = re.findall(r"_+", texto)

    if len(marcadores) != len(actividad.espacios):
        raise ValueError(
            "La cantidad de espacios del texto "
            f"({len(marcadores)}) no coincide con "
            "la cantidad de respuestas definidas "
            f"({len(actividad.espacios)})."
        )

    for espacio in actividad.espacios:
        respuestas = [
            respuesta.strip()
            for respuesta in espacio.respuestas_aceptadas
            if respuesta.strip()
        ]

        if not respuestas:
            raise ValueError(
                f"El espacio {espacio.numero} "
                "no tiene respuestas válidas."
            )

        blanco_h5p = (
            "*"
            + "/".join(respuestas)
            + "*"
        )

        texto = re.sub(
            r"_+",
            lambda _: blanco_h5p,
            texto,
            count=1,
        )

    return {
        "text": actividad.instrucciones
        or "Complete los espacios en blanco.",
        "questions": [
            texto,
        ],
        "behaviour": {
            "enableRetry": True,
            "enableSolutionsButton": True,
            "enableCheckButton": True,
            "autoCheck": False,
            "caseSensitive": False,
            "showSolutionsRequiresInput": True,
            "separateLines": False,
            "confirmCheckDialog": False,
            "confirmRetryDialog": False,
            "acceptSpellingErrors": False,
        },
        "showSolutions": "Mostrar solución",
        "tryAgain": "Intentar de nuevo",
        "checkAnswer": "Comprobar",
        "submitAnswer": "Enviar",
        "notFilledOut": (
            "Complete todos los espacios antes "
            "de ver la solución."
        ),
        "answerIsCorrect": "':ans' es correcto",
        "answerIsWrong": "':ans' es incorrecto",
        "answeredCorrectly": "Respuesta correcta",
        "answeredIncorrectly": "Respuesta incorrecta",
        "solutionLabel": "Respuesta correcta:",
        "inputLabel": "Espacio @num de @total",
        "inputHasTipLabel": "Pista disponible",
        "tipLabel": "Pista",
        "scoreBarLabel": (
            "Has obtenido :num de :total puntos"
        ),
    }
    
def generar_h5p_manifest_blanks(
        titulo: str,
    ) -> Dict[str, Any]:
        """
        Genera h5p.json para H5P.Blanks 1.14.
        """
        return {
            "title": titulo,
            "language": "es",
            "mainLibrary": "H5P.Blanks",
            "embedTypes": ["iframe"],
            "license": "U",
            "preloadedDependencies": [
                {
                    "machineName": "H5P.Blanks",
                    "majorVersion": 1,
                    "minorVersion": 14,
                }
            ],
        }


def empaquetar_fill_in_the_blanks(
        actividad: H5PFillInTheBlanks,
        ruta_salida: Path,
    ) -> Path:
        """
        Genera un paquete .h5p para H5P.Blanks 1.14.
        """
        contenido = generar_fill_in_the_blanks(actividad)
        manifest = generar_h5p_manifest_blanks(
            actividad.titulo
        )

        ruta_salida = Path(ruta_salida)

        if ruta_salida.suffix.lower() != ".h5p":
            raise ValueError(
                "La ruta de salida debe terminar en .h5p"
            )

        ruta_salida.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with zipfile.ZipFile(
            ruta_salida,
            mode="w",
            compression=zipfile.ZIP_DEFLATED,
        ) as paquete:
            paquete.writestr(
                "h5p.json",
                json.dumps(
                    manifest,
                    ensure_ascii=False,
                    indent=2,
                ),
            )

            paquete.writestr(
                "content/content.json",
                json.dumps(
                    contenido,
                    ensure_ascii=False,
                    indent=2,
                ),
            )

        return ruta_salida