"""Sistema Alumnos: demo Flask instrumentada para el laboratorio EV3."""
import os
import re
import secrets
import sqlite3
import threading
import time
from collections import defaultdict, deque
from pathlib import Path

from flask import Flask, Response, abort, g, jsonify, render_template_string, request, session
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest
from werkzeug.security import check_password_hash

app = Flask(__name__)
APP_SECRET_KEY = os.environ.get("APP_SECRET_KEY")
if os.environ.get("APP_ENV") == "production" and not APP_SECRET_KEY:
    raise RuntimeError("APP_SECRET_KEY es obligatorio en producción")
app.config.update(
    SECRET_KEY=APP_SECRET_KEY or secrets.token_hex(32),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("COOKIE_SECURE", "0") == "1",
    MAX_CONTENT_LENGTH=16 * 1024,
)

VERSION = os.environ.get("APP_VERSION", "dev")
DB_PATH = os.environ.get("DB_PATH", "alumnos.db")
ADMIN_USUARIO = os.environ.get("ADMIN_USUARIO", "admin")
ADMIN_PASSWORD_HASH = os.environ.get("ADMIN_PASSWORD_HASH", "")
LOGIN_MAX_INTENTOS = int(os.environ.get("LOGIN_MAX_INTENTOS", "10"))
LOGIN_VENTANA_SEGUNDOS = int(os.environ.get("LOGIN_VENTANA_SEGUNDOS", "300"))

ALUMNOS_INICIALES = [
    (1, "Ana Pérez", "Ingeniería en Informática", 6.1),
    (2, "Benjamín Rojas", "Ingeniería en Ciberseguridad", 5.4),
    (3, "Camila Soto", "Analista Programador", 6.8),
    (4, "Diego Muñoz", "Ingeniería en Informática", 4.9),
]

# Métricas públicas consumidas por Prometheus; conservar nombres para el laboratorio.
HTTP_PETICIONES = Counter("http_requests_total", "Peticiones HTTP atendidas", ["method", "endpoint", "status"])
HTTP_LATENCIA = Histogram("http_request_duration_seconds", "Duración de las peticiones HTTP", ["endpoint"])
LOGIN_FALLIDOS = Counter("login_fallidos_total", "Intentos de inicio de sesión fallidos")
LOGIN_EXITOSOS = Counter("login_exitosos_total", "Inicios de sesión correctos")
SOSPECHOSAS = Counter("peticiones_sospechosas_total", "Peticiones con patrones de ataque", ["tipo"])
APP_INFO = Gauge("app_info", "Versión desplegada de la aplicación", ["version"])
APP_INFO.labels(version=VERSION).set(1)

PATRONES_ATAQUE = {
    "xss": re.compile(r"<\s*script|javascript:|onerror\s*=|onload\s*=|<\s*img", re.I),
    "sqli": re.compile(r"('|%27)\s*(or|and|union)\b|union\s+select|--|;\s*drop\b|sleep\(", re.I),
    "path_traversal": re.compile(r"\.\./|\.\.\\|%2e%2e", re.I),
}
_login_lock = threading.Lock()
_login_intentos = defaultdict(deque)

PORTADA = """<!doctype html>
<html lang="es"><head><meta charset="utf-8"><title>Sistema Alumnos</title></head>
<body><h1>Sistema Alumnos · SecureDev</h1><p>Versión {{ version }}</p>
<ul><li><a href="/alumnos">Listado de alumnos (JSON)</a></li>
<li><a href="/alumnos/1">Alumno 1</a></li><li><a href="/hello?name=Ana">Saludo</a></li></ul>
<h2>Buscar alumno</h2><form action="/alumnos/buscar" method="get">
<input name="nombre" value="Ana"> <button>Buscar</button></form>
<h2>Acceso administrador</h2><form action="/login" method="post">
<input type="hidden" name="csrf_token" value="{{ csrf_token }}">
<input name="usuario" value="admin"><input name="clave" type="password">
<button>Entrar</button></form></body></html>"""


def conectar():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def cerrar_db(_error):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def iniciar_db():
    db = sqlite3.connect(DB_PATH)
    db.execute("CREATE TABLE IF NOT EXISTS alumnos (id INTEGER PRIMARY KEY, nombre TEXT, carrera TEXT, promedio REAL)")
    if db.execute("SELECT COUNT(*) FROM alumnos").fetchone()[0] == 0:
        db.executemany("INSERT INTO alumnos VALUES (?, ?, ?, ?)", ALUMNOS_INICIALES)
    db.commit()
    db.close()


@app.before_request
def antes_de_la_peticion():
    g.inicio = time.perf_counter()
    for tipo, patron in PATRONES_ATAQUE.items():
        if any(patron.search(v) for v in (*request.args.values(), *request.form.values())):
            SOSPECHOSAS.labels(tipo=tipo).inc()
            app.logger.warning("Petición sospechosa (%s) desde %s a %s", tipo, request.remote_addr, request.path)


@app.after_request
def despues_de_la_peticion(respuesta):
    respuesta.headers.setdefault("X-Content-Type-Options", "nosniff")
    respuesta.headers.setdefault("X-Frame-Options", "DENY")
    respuesta.headers.setdefault("Referrer-Policy", "no-referrer")
    respuesta.headers.setdefault("Content-Security-Policy", "default-src 'self'; form-action 'self'; frame-ancestors 'none'; base-uri 'self'")
    respuesta.headers.setdefault("Cache-Control", "no-store")
    endpoint = request.url_rule.rule if request.url_rule else "desconocido"
    if endpoint != "/metrics":
        HTTP_PETICIONES.labels(request.method, endpoint, str(respuesta.status_code)).inc()
        HTTP_LATENCIA.labels(endpoint).observe(time.perf_counter() - g.get("inicio", time.perf_counter()))
    return respuesta


@app.route("/")
def portada():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_urlsafe(32)
    return render_template_string(PORTADA, version=VERSION, csrf_token=session["csrf_token"])


@app.route("/hello")
def hello():
    # Jinja escapa el parámetro antes de incorporarlo al HTML.
    return render_template_string("<h1>Hola, {{ name }}!</h1>", name=request.args.get("name", "visitante"))


@app.route("/health")
def health():
    return jsonify({"estado": "ok"})


@app.route("/version")
def version():
    return jsonify({"aplicacion": "Sistema Alumnos", "version": VERSION})


@app.route("/alumnos")
def listar_alumnos():
    return jsonify([dict(f) for f in conectar().execute("SELECT * FROM alumnos ORDER BY id").fetchall()])


@app.route("/alumnos/<int:alumno_id>")
def obtener_alumno(alumno_id):
    fila = conectar().execute("SELECT * FROM alumnos WHERE id = ?", (alumno_id,)).fetchone()
    if fila is None:
        return jsonify({"error": "Alumno no encontrado"}), 404
    return jsonify(dict(fila))


@app.route("/alumnos/buscar")
def buscar_alumnos():
    nombre = request.args.get("nombre", "")[:100]
    filas = conectar().execute("SELECT * FROM alumnos WHERE nombre LIKE ?", (f"%{nombre}%",)).fetchall()
    return jsonify([dict(f) for f in filas])


def _intentos_restantes(ip, ahora):
    intentos = _login_intentos[ip]
    while intentos and ahora - intentos[0] > LOGIN_VENTANA_SEGUNDOS:
        intentos.popleft()
    return max(0, LOGIN_MAX_INTENTOS - len(intentos))


@app.route("/login", methods=["POST"])
def login():
    ip = request.remote_addr or "desconocido"
    ahora = time.monotonic()
    with _login_lock:
        restantes = _intentos_restantes(ip, ahora)
        if restantes == 0:
            return jsonify({"error": "Demasiados intentos. Intente más tarde."}), 429

    esperado = session.get("csrf_token", "")
    recibido = request.form.get("csrf_token", "")
    if not esperado or not secrets.compare_digest(esperado, recibido):
        abort(400, description="Solicitud no válida")

    usuario = request.form.get("usuario", "")[:80]
    clave = request.form.get("clave", "")
    valido = bool(ADMIN_PASSWORD_HASH) and usuario == ADMIN_USUARIO and check_password_hash(ADMIN_PASSWORD_HASH, clave)
    if valido:
        with _login_lock:
            _login_intentos.pop(ip, None)
        session.clear()
        LOGIN_EXITOSOS.inc()
        return jsonify({"mensaje": "Bienvenido, administrador"})

    with _login_lock:
        _login_intentos[ip].append(ahora)
    LOGIN_FALLIDOS.inc()
    app.logger.warning("Login fallido desde %s", ip)
    return jsonify({"error": "Credenciales inválidas"}), 401


@app.route("/metrics")
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


iniciar_db()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
