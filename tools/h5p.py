import base64
from pathlib import Path

from tools.courses import _moodle_request


def crear_h5p(
    courseid: int,
    ruta_h5p: str,
) -> dict:
    """
    Sube un paquete .h5p al Content Bank de Moodle.

    Moodle recibe el archivo codificado en Base64 y se encarga
    de validarlo e importarlo mediante su API de Content Bank.
    """

    ruta = Path(ruta_h5p)

    if not ruta.exists():
        raise FileNotFoundError(
            f"No existe el archivo H5P: {ruta}"
        )

    if not ruta.is_file():
        raise ValueError(
            f"La ruta no corresponde a un archivo: {ruta}"
        )

    if ruta.suffix.lower() != ".h5p":
        raise ValueError(
            f"El archivo debe tener extensión .h5p: {ruta.name}"
        )

    contenido_base64 = base64.b64encode(
        ruta.read_bytes()
    ).decode("ascii")

    resultado = _moodle_request(
        "local_cursomaker_create_h5p",
        {
            "courseid": courseid,
            "filename": ruta.name,
            "contentbase64": contenido_base64,
        },
    )

    if not resultado.get("created"):
        raise RuntimeError(
            "Moodle no confirmó la creación del contenido H5P."
        )

    if int(resultado["courseid"]) != int(courseid):
        raise RuntimeError(
            "Moodle creó el H5P en un curso diferente al esperado."
        )

    return resultado