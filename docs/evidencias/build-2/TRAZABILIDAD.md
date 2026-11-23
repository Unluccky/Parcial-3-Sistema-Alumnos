# Registro de trazabilidad - Sistema Alumnos

Cada fila la agrega Jenkins al terminar un build (`scripts/trazabilidad.py`).

| Build | Fecha (UTC) | Versión | Commit | Mensaje del commit | Pruebas | Bandit H/M/L | pip-audit | ZAP H/M/L | Resultado | Producción |
|---|---|---|---|---|---|---|---|---|---|---|
| 2 | 2026-11-23 20:34 | 1.0.2+a0bd58f | `a0bd58f` | Implementa controles DevSecOps para EV3 | 14/14 OK | 0/0/0 | 0 vuln. | 0/0/0 | SUCCESS | 1.0.2+a0bd58f |
