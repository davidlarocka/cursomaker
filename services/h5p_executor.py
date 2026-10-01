"""Compatibilidad con el nombre histórico del ejecutor H5P."""
from services.h5p_pipeline import crear_actividad_h5p


def ejecutar_h5p(actividad, courseid: int, section: int, output_dir: str = "output/h5p") -> dict:
    resultado = crear_actividad_h5p(actividad, courseid, section, output_dir=output_dir)
    if "h5p_path" in resultado:
        resultado["ruta_h5p"] = resultado["h5p_path"]
    return resultado
