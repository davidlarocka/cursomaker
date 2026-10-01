import os

import requests
from dotenv import load_dotenv


load_dotenv()

MOODLE_URL = os.getenv("MOODLE_URL")
MOODLE_TOKEN = os.getenv("MOODLE_TOKEN")

if not MOODLE_URL:
    raise ValueError("No se encontró MOODLE_URL en .env")

if not MOODLE_TOKEN:
    raise ValueError("No se encontró MOODLE_TOKEN en .env")


endpoint = f"{MOODLE_URL}/webservice/rest/server.php"

params = {
    "wstoken": MOODLE_TOKEN,
    "wsfunction": "core_course_get_courses",
    "moodlewsrestformat": "json",
}


print("🔌 Conectando con Moodle...")
print(f"🌐 Moodle: {MOODLE_URL}")

response = requests.get(
    endpoint,
    params=params,
    timeout=10
)

response.raise_for_status()

data = response.json()


# Moodle también puede devolver errores con HTTP 200
if isinstance(data, dict) and "exception" in data:
    print("\n❌ Moodle devolvió un error:")
    print(data)
    raise SystemExit(1)


print("\n✅ Conexión correcta.")
print(f"📚 Cursos encontrados: {len(data)}")
print()


for curso in data:
    print(
        f"ID: {curso.get('id')} | "
        f"Nombre: {curso.get('fullname')} | "
        f"Shortname: {curso.get('shortname')}"
    )