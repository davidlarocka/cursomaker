from pathlib import Path

import fitz
import hashlib


def extraer_texto_pdf(ruta_pdf):
    """
    Extrae el texto de un PDF página por página.
    """

    ruta = Path(ruta_pdf)

    if not ruta.exists():
        raise FileNotFoundError(
            f"No existe el archivo PDF: {ruta}"
        )

    if ruta.suffix.lower() != ".pdf":
        raise ValueError(
            "El archivo proporcionado no es un PDF."
        )

    documento = fitz.open(ruta)

    paginas = []

    try:
        for numero, pagina in enumerate(documento, start=1):
            texto = pagina.get_text("text")

            paginas.append({
                "numero": numero,
                "texto": texto.strip(),
            })

        return {
            "archivo": ruta.name,
            "total_paginas": len(documento),
            "paginas": paginas,
        }

    finally:
        documento.close()
        
def construir_texto_documento(documento):
    """
    Construye una representación textual del documento
    conservando los números de página.
    """

    bloques = []

    for pagina in documento["paginas"]:
        texto = pagina["texto"].strip()

        if not texto:
            continue

        bloques.append(
            f"--- PÁGINA {pagina['numero']} ---\n"
            f"{texto}"
        )

    return "\n\n".join(bloques)

def obtener_texto_paginas(documento, numeros_paginas):
    """
    Obtiene el texto original de páginas específicas
    conservando su número de página.
    """

    paginas_por_numero = {
        pagina["numero"]: pagina["texto"]
        for pagina in documento["paginas"]
    }

    bloques = []

    for numero in numeros_paginas:
        if numero not in paginas_por_numero:
            raise ValueError(
                f"La página {numero} no existe en el documento."
            )

        bloques.append(
            f"--- PÁGINA {numero} ---\n"
            f"{paginas_por_numero[numero]}"
        )

    return "\n\n".join(bloques)

def extraer_imagenes_pdf(ruta_pdf, directorio_salida):
    """
    Extrae las imágenes incrustadas de un PDF y conserva
    información sobre la página de origen.
    """

    ruta = Path(ruta_pdf)
    salida = Path(directorio_salida)

    if not ruta.exists():
        raise FileNotFoundError(
            f"No existe el archivo PDF: {ruta}"
        )

    salida.mkdir(parents=True, exist_ok=True)

    documento = fitz.open(ruta)

    imagenes = []

    try:
        for numero_pagina, pagina in enumerate(
            documento,
            start=1,
        ):
            imagenes_pagina = pagina.get_images(full=True)

            for indice, imagen_info in enumerate(
                imagenes_pagina,
                start=1,
            ):
                xref = imagen_info[0]

                datos_imagen = documento.extract_image(xref)

                extension = datos_imagen["ext"]
                contenido = datos_imagen["image"]

                nombre_archivo = (
                    f"pagina_{numero_pagina:03d}"
                    f"_img_{indice:02d}.{extension}"
                )

                ruta_imagen = salida / nombre_archivo

                ruta_imagen.write_bytes(contenido)

                imagenes.append({
                    "pagina": numero_pagina,
                    "indice": indice,
                    "xref": xref,
                    "archivo": nombre_archivo,
                    "ruta": str(ruta_imagen),
                    "extension": extension,
                    "ancho": datos_imagen.get("width"),
                    "alto": datos_imagen.get("height"),
                })

        return imagenes

    finally:
        documento.close()

def deduplicar_imagenes(imagenes):
    """
    Agrupa imágenes idénticas utilizando su hash SHA-256.

    No elimina archivos. Devuelve un inventario de imágenes
    únicas indicando todas las páginas donde aparecen.
    """

    unicas = {}

    for imagen in imagenes:
        ruta = Path(imagen["ruta"])

        contenido = ruta.read_bytes()

        hash_imagen = hashlib.sha256(
            contenido
        ).hexdigest()

        if hash_imagen not in unicas:
            unicas[hash_imagen] = {
                "hash": hash_imagen,
                "archivo": imagen["archivo"],
                "ruta": imagen["ruta"],
                "ancho": imagen["ancho"],
                "alto": imagen["alto"],
                "paginas": [],
                "ocurrencias": 0,
            }

        unicas[hash_imagen]["paginas"].append(
            imagen["pagina"]
        )

        unicas[hash_imagen]["ocurrencias"] += 1

    return list(unicas.values())

def clasificar_imagenes(imagenes_unicas):
    """
    Clasifica imágenes únicas mediante reglas técnicas conservadoras.

    Por ahora solo descartamos automáticamente elementos
    extremadamente repetitivos, típicos de logos o plantillas.
    """

    candidatos = []
    decorativas = []

    for imagen in imagenes_unicas:

        # Elementos presentes en gran parte del documento:
        # probablemente logos, encabezados o decoración.
        if imagen["ocurrencias"] >= 10:
            imagen_clasificada = {
                **imagen,
                "clasificacion": "decorativa",
                "motivo": "imagen repetida en muchas páginas",
            }

            decorativas.append(imagen_clasificada)
            continue

        imagen_clasificada = {
            **imagen,
            "clasificacion": "candidata",
            "motivo": "requiere análisis de contenido",
        }

        candidatos.append(imagen_clasificada)

    return {
        "candidatos": candidatos,
        "decorativas": decorativas,
    }
    
    