from tools.courses import crear_pagina

resultado = crear_pagina(
    curso_id=6,
    seccion_numero=1,
    nombre="Prueba de contenido",
    contenido="""
        <h2>Prueba de contenido</h2>
        <p>Si puedes leer este texto en Moodle, CursoMaker ya puede crear páginas con contenido HTML correctamente.</p>
        <ul>
            <li>Primer elemento</li>
            <li>Segundo elemento</li>
        </ul>
    """
)

print()
print("Resultado:")
print(resultado)