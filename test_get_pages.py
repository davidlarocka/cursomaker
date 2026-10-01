from tools.courses import _moodle_request

resultado = _moodle_request(
    "mod_page_get_pages_by_courses",
    {
        "courseids[0]": 6
    }
)

print(resultado)