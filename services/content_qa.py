from services.content_validator import validar_contenido
from services.content_corrector import corregir_contenido


def procesar_qa_contenido(
    titulo,
    contenido,
    texto_fuente,
    max_intentos=2,
):
    """
    Audita y, si es necesario, corrige un contenido.

    Nunca realiza más correcciones que max_intentos.
    """

    contenido_actual = contenido

    for intento in range(max_intentos + 1):
        print(
            f"\n🔎 Auditoría {intento + 1} "
            f"para: {titulo}"
        )

        validacion = validar_contenido(
            titulo=titulo,
            contenido=contenido_actual,
            texto_fuente=texto_fuente,
        )

        print(
            f"   Fidelidad: {validacion.fidelidad_fuente}%"
        )
        print(
            f"   Cobertura: {validacion.cobertura_contenido}%"
        )

        if validacion.aprobado:
            return {
                "aprobado": True,
                "contenido": contenido_actual,
                "validacion": validacion,
                "correcciones": intento,
            }

        if intento == max_intentos:
            break

        print("🛠️ El contenido requiere corrección...")

        contenido_actual = corregir_contenido(
            titulo=titulo,
            contenido=contenido_actual,
            texto_fuente=texto_fuente,
            validacion=validacion,
        )

    return {
        "aprobado": False,
        "contenido": contenido_actual,
        "validacion": validacion,
        "correcciones": max_intentos,
    }