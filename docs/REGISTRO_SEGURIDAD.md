# Registro de seguridad del Sistema Alumnos

**Estudiante:** Jose Muñoz
**Repositorio GitHub:** https://github.com/Unluccky/Parcial-3-Sistema-Alumnos
**Fecha de ejecución:** 23-11-2026 (hora local UTC-03:00)

Este registro describe los cambios realizados sobre el código inicial vulnerable y la evidencia que debe generar cada ejecución. Los valores identificados como **pendientes** se completan con los reportes reales de Jenkins, ZAP, Grafana y GitHub; no se deben reemplazar por resultados estimados. Los resultados finales corresponden al build #3 (commit `9bbee95`, versión `1.0.3+9bbee95`); los reportes originales se conservan en `docs/evidencias/build-3/`.

## 1. Revisiones de seguridad

| Revisión | Etapa | Herramienta o técnica | Qué verifica | Resultado disponible |
|---|---|---|---|---|
| R1 | Código (SAST) | Bandit, `bandit -ll` | Hallazgos Medium/High en `app.py` | Build #3: 0 hallazgos High/Medium/Low (Bandit); JUnit 14/14 |
| R2 | Dependencias (SCA) | pip-audit | CVE/avisos de `requirements.txt` y `requirements-dev.txt` | Build #3: 13 dependencias analizadas; 0 vulnerabilidades conocidas (pip-audit) |
| R3 | Pruebas dinámicas (DAST) | OWASP ZAP sobre staging | Spider, análisis pasivo y activo antes de habilitar producción | Build #3: 0 High, 0 Medium, 0 Low y 2 tipos Informational |
| R4 | Revisión manual | Lectura de `app.py` | XSS, SQLi, secretos, hash de contraseña, CSRF, intentos de login y modo debug | Hallazgos y mitigaciones registrados en la sección 2 |
| R5 | Producción | Prometheus y Grafana | Disponibilidad, tasa de solicitudes, autenticaciones fallidas, solicitudes sospechosas y latencia p95 | Validado: dashboard provisionado, producción y staging disponibles (up=1) y alerta activa durante la simulación |

## 2. Vulnerabilidades del código inicial y mitigaciones

| ID | Vulnerabilidad | CWE | Ubicación inicial | Riesgo | Mitigación aplicada | Commit / build |
|---|---|---|---|---|---|---|
| VULN-01 | XSS reflejado en el saludo | CWE-79 | `app.py`, ruta `/hello` | Un parámetro HTML podía ejecutarse como script en el navegador | Renderizado con Jinja y escape automático; CSP y encabezados defensivos | Commit `a0bd58f`; verificado en builds #2 y #3 |
| VULN-02 | Inyección SQL en la búsqueda | CWE-89 | `app.py`, ruta `/alumnos/buscar` | Un parámetro podía alterar la consulta y exponer datos | Consulta parametrizada (`LIKE ?`), límite de longitud y eliminación de SQL y errores internos de la respuesta | Commit `a0bd58f`; verificado en builds #2 y #3 |
| VULN-03 | Secreto fijo en el código y contraseña MD5 | CWE-798, CWE-321, CWE-916 | Constantes `SECRET_KEY` y `ADMIN_CLAVE_MD5` | Exposición de credenciales y recuperación trivial de la contraseña | Eliminadas las constantes; secreto de producción externo al repositorio y contraseña validada con `check_password_hash`; el acceso queda inhabilitado si no se configura un hash | Commit `a0bd58f`; verificado en builds #2 y #3 |
| VULN-04 | Falta de protección CSRF en el login | CWE-352 | Ruta `/login` y formulario de portada | Un sitio externo podía inducir una solicitud autenticada | Token aleatorio vinculado a la sesión y comparación segura; cookie HttpOnly y SameSite=Lax | Commit `a0bd58f`; verificado en builds #2 y #3 |
| VULN-05 | Intentos ilimitados de autenticación | CWE-307 | Ruta `/login` | Facilita fuerza bruta contra credenciales | Límite por IP: 10 intentos en 5 minutos, respuesta HTTP 429 y métrica de intentos fallidos | Commit `a0bd58f`; verificado en builds #2 y #3 |
| VULN-06 | Modo debug habilitado | CWE-489 | Bloque `app.run` inicial | Riesgo de exponer información y herramientas de depuración | `debug=False`; el despliegue usa Gunicorn | Commit `a0bd58f`; verificado en builds #2 y #3 |
| VULN-07 | Ausencia de encabezados defensivos | CWE-693 | Respuestas HTTP | Aumenta exposición a framing y ejecución de contenido no esperado | CSP, `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy` y `Cache-Control` | Commit `a0bd58f`; verificado en builds #2 y #3 |

## 3. Resultados OWASP ZAP

La versión inicial incluye XSS reflejado y SQLi en las rutas `/hello` y `/alumnos/buscar`. La mitigación se verifica con el escaneo de staging de ZAP después del cambio. ZAP puede informar alertas informativas o de configuración que requieren evaluación; no se registran como vulnerabilidades corregidas sin revisar el reporte.

| Alerta exacta de ZAP | Riesgo | URL afectada | VULN | Mitigación | Build / estado |
|---|---|---|---|---|---|
| Session Management Response Identified | Informational | Staging local | Configuración de sesión | Revisada; no se detectaron High/Medium/Low | Build #3, escaneo SUCCESS |
| User Agent Fuzzer | Informational | Staging local | No aplica como vulnerabilidad confirmada | Alerta informativa; sin High/Medium/Low | Build #3, escaneo SUCCESS |

El pipeline detiene el despliegue a producción si el script de ZAP informa alertas High o Medium. En el build #3, ZAP registró dos tipos informativos y cero alertas High/Medium/Low; producción se desplegó correctamente. Reportes JSON, HTML y de resumen: `docs/evidencias/build-3/`.

## 4. Monitoreo e incidentes

El laboratorio configura Prometheus con scrape cada 5 segundos para producción y staging. Grafana se provisiona con la fuente de datos Prometheus, un dashboard de producción y una regla que alerta cuando se observan más de cinco intentos de login fallidos por minuto durante 30 segundos.

| Hora y fecha | Métrica | Observación | Entorno | Clasificación | Respuesta | Verificación |
|---|---|---|---|---|---|---|
| 23-11-2026 17:57 -03 (alerta) | `login_fallidos_total=10`; `HTTP 429=21`; SQLi=1; XSS=1 | Simulación: 31 intentos; sin acceso válido; SQLi sin datos internos; XSS escapado. Regla Grafana observada `active` | Producción local del laboratorio | Fuerza bruta y solicitudes controladas | Límite de login respondió 429; revisión de salida y métricas | Prometheus `up=1` en producción y staging; snapshot de alerta en `docs/evidencias/build-3/grafana-alert-active-snapshot.json` |

La evidencia de incidente proviene de `scripts/simular_ataque.py` contra `http://jenkins:5000` dentro de la red del laboratorio. El resultado completo está en `docs/evidencias/build-3/simulacion-produccion.txt`; el snapshot de Grafana y las consultas Prometheus están junto a él.

## 5. Gestión de dependencias

Dependabot quedó configurado semanalmente para los ecosistemas `pip` y `github-actions`. El archivo de configuración crea propuestas de actualización; las alertas del repositorio y los PR solo aparecen después de publicar el proyecto en GitHub y activar Dependabot en **Settings → Code security and analysis**.

| Paquete | Versión inicial | Versión fijada en el proyecto | Origen | Estado de seguridad |
|---|---:|---:|---|---|
| Flask | 2.2.2 | 3.1.3 | Actualización manual inicial; después Dependabot | Build #3: 0 vulnerabilidades conocidas |
| Werkzeug | 2.2.2 | 3.1.9 | Actualización manual inicial; después Dependabot | Build #3: 0 vulnerabilidades conocidas |
| Jinja2 | 3.1.2 | 3.1.6 | Actualización manual inicial; después Dependabot | Build #3: 0 vulnerabilidades conocidas |
| gunicorn | 21.2.0 | 27.0.1 | Actualización manual inicial; después Dependabot | Build #3: 0 vulnerabilidades conocidas |
| prometheus-client | 0.17.1 | 0.26.0 | Actualización manual inicial; después Dependabot | Build #3: 0 vulnerabilidades conocidas |
| pytest | 8.3.4 | 9.2.0 | Actualización manual inicial; después Dependabot | Build #3: 0 vulnerabilidades conocidas |

No se asignan identificadores CVE por inferencia. Se copiarán los identificadores y versiones afectadas desde `reports/pip-audit.txt` o los reportes del PR de Dependabot. El Build #3 analizó 13 dependencias de ejecución y pruebas, sin vulnerabilidades conocidas. La salida legible `pip-audit.txt` y el JSON están en `docs/evidencias/build-3/`.

## 6. Trazabilidad

El Jenkinsfile genera una versión `1.0.<build>+<commit>`, archiva los reportes y ejecuta `scripts/trazabilidad.py` al terminar cada build. El reporte del build actual se guarda como `reports/trazabilidad-build.md`; el historial persistente se escribe como `reports/TRAZABILIDAD.md`.

| Actividad | Hallazgo | Build de detección | Commit o PR correctivo | Build de verificación | Versión desplegada |
|---|---|---|---|---|---|
| Bandit (SAST) | 0 hallazgos High/Medium/Low | Build #3 | Commit correctivo `a0bd58f` | Builds #2 y #3 SUCCESS | `1.0.3+9bbee95` |
| OWASP ZAP (DAST) | 0 High/Medium/Low; 2 tipos informativos | Build #3 | Commit correctivo `a0bd58f` | Build #3 SUCCESS | `1.0.3+9bbee95` |
| Dependencias (SCA/Dependabot) | 0 vulnerabilidades conocidas; Dependabot activo | Build #3 | No aplica; sin actualización vulnerable pendiente | Build #3 SUCCESS | `1.0.3+9bbee95` |

El historial real de Jenkins se incluye en `docs/evidencias/build-3/TRAZABILIDAD.md`: build #2 (`a0bd58f`, `1.0.2+a0bd58f`) y build #3 (`9bbee95`, `1.0.3+9bbee95`), ambos SUCCESS, 14/14 pruebas y 0 vulnerabilidades conocidas. No se generó PR de Dependabot porque el análisis no encontró actualizaciones vulnerables pendientes.
