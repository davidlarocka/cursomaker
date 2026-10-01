from tools.courses import _moodle_request


resultado = _moodle_request(
    "local_cursomaker_create_h5p_activity",
    {
        "courseid": 7,
        "section": 2,
        "contentid": 13,
        "name": "OMI141 M01 - Drag Question",
    }
)

print("=== RESULTADO H5P ACTIVITY ===")
print(resultado)