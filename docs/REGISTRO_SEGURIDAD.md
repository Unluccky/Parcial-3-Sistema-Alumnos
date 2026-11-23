# Registro de seguridad del Sistema Alumnos

**Estudiante:** ____________________  
**Repositorio GitHub:** ____________________  
**Fecha de ejecución:** ____________________

Este registro describe los cambios realizados sobre el código inicial vulnerable y la evidencia que debe generar cada ejecución. Los valores identificados como **pendientes** se completan con los reportes reales de Jenkins, ZAP, Grafana y GitHub; no se deben reemplazar por resultados estimados.

## 1. Revisiones de seguridad

| Revisión | Etapa | Herramienta o técnica | Qué verifica | Resultado disponible |
|---|---|---|---|---|
| R1 | Código (SAST) | Bandit, `bandit -ll` | Hallazgos Medium/High en `app.py` | Configurada en Jenkins; resultado del primer build: pendiente |
| R2 | Dependencias (SCA) | pip-audit | CVE/avisos de `requirements.txt` y `requirements-dev.txt` | Configurada en Jenkins; resultado posterior a actualización: pendiente |
| R3 | Pruebas dinámicas (DAST) | OWASP ZAP sobre staging | Spider, análisis pasivo y activo antes de habilitar producción | Etapa configurada; alertas del build: pendiente |
| R4 | Revisión manual | Lectura de `app.py` | XSS, SQLi, secretos, hash de contraseña, CSRF, intentos de login y modo debug | Hallazgos y mitigaciones registrados en la sección 2 |
| R5 | Producción | Prometheus y Grafana | Disponibilidad, tasa de solicitudes, autenticaciones fallidas, solicitudes sospechosas y latencia p95 | Provisionamiento como código incluido; validación visual: pendiente |

## 2. Vulnerabilidades del código inicial y mitigaciones

| ID | Vulnerabilidad | CWE | Ubicación inicial | Riesgo | Mitigación aplicada | Commit / build |
|---|---|---|---|---|---|---|
| VULN-01 | XSS reflejado en el saludo | CWE-79 | `app.py`, ruta `/hello` | Un parámetro HTML podía ejecutarse como script en el navegador | Renderizado con Jinja y escape automático; CSP y encabezados defensivos | Commit y build: pendientes |
| VULN-02 | Inyección SQL en la búsqueda | CWE-89 | `app.py`, ruta `/alumnos/buscar` | Un parámetro podía alterar la consulta y exponer datos | Consulta parametrizada (`LIKE ?`), límite de longitud y eliminación de SQL y errores internos de la respuesta | Commit y build: pendientes |
| VULN-03 | Secreto fijo en el código y contraseña MD5 | CWE-798, CWE-321, CWE-916 | Constantes `SECRET_KEY` y `ADMIN_CLAVE_MD5` | Exposición de credenciales y recuperación trivial de la contraseña | Eliminadas las constantes; secreto de producción externo al repositorio y contraseña validada con `check_password_hash`; el acceso queda inhabilitado si no se configura un hash | Commit y build: pendientes |
| VULN-04 | Falta de protección CSRF en el login | CWE-352 | Ruta `/login` y formulario de portada | Un sitio externo podía inducir una solicitud autenticada | Token aleatorio vinculado a la sesión y comparación segura; cookie HttpOnly y SameSite=Lax | Commit y build: pendientes |
| VULN-05 | Intentos ilimitados de autenticación | CWE-307 | Ruta `/login` | Facilita fuerza bruta contra credenciales | Límite por IP: 10 intentos en 5 minutos, respuesta HTTP 429 y métrica de intentos fallidos | Commit y build: pendientes |
| VULN-06 | Modo debug habilitado | CWE-489 | Bloque `app.run` inicial | Riesgo de exponer información y herramientas de depuración | `debug=False`; el despliegue usa Gunicorn | Commit y build: pendientes |
| VULN-07 | Ausencia de encabezados defensivos | CWE-693 | Respuestas HTTP | Aumenta exposición a framing y ejecución de contenido no esperado | CSP, `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy` y `Cache-Control` | Commit y build: pendientes |

## 3. Resultados OWASP ZAP

La versión inicial incluye XSS reflejado y SQLi en las rutas `/hello` y `/alumnos/buscar`. La mitigación se verifica con el escaneo de staging de ZAP después del cambio. ZAP puede informar alertas informativas o de configuración que requieren evaluación; no se registran como vulnerabilidades corregidas sin revisar el reporte.

| Alerta exacta de ZAP | Riesgo | URL afectada | VULN | Mitigación | Build / estado |
|---|---|---|---|---|---|
| Completar desde `reports/zap-resumen.txt` y `reports/zap-report.html` | Pendiente | Pendiente | VULN correspondiente | Revisar cada alerta, validar la corrección y repetir escaneo | No ejecutar aún |

El pipeline detiene el despliegue a producción si el script de ZAP informa alertas High o Medium. Los reportes JSON, HTML y de resumen se archivan en Jenkins.

## 4. Monitoreo e incidentes

El laboratorio configura Prometheus con scrape cada 5 segundos para producción y staging. Grafana se provisiona con la fuente de datos Prometheus, un dashboard de producción y una regla que alerta cuando se observan más de cinco intentos de login fallidos por minuto durante 30 segundos.

| Hora y fecha | Métrica | Observación | Entorno | Clasificación | Respuesta | Verificación |
|---|---|---|---|---|---|---|
| Completar con la hora de la simulación | `login_fallidos_total`, `peticiones_sospechosas_total{tipo}` | Registrar valores y estado de la regla en Grafana | Producción local del laboratorio | Intento de fuerza bruta / solicitudes de prueba | Bloqueo temporal HTTP 429; revisar IP y logs; conservar evidencia | Confirmar que el dashboard refleja los contadores y que la regla vuelve a Normal tras la ventana |

La evidencia de incidente debe provenir de una ejecución de `scripts/simular_ataque.py` contra `http://jenkins:5000` dentro de la red del laboratorio. El script envía cargas controladas únicamente a esta aplicación local.

## 5. Gestión de dependencias

Dependabot quedó configurado semanalmente para los ecosistemas `pip` y `github-actions`. El archivo de configuración crea propuestas de actualización; las alertas del repositorio y los PR solo aparecen después de publicar el proyecto en GitHub y activar Dependabot en **Settings → Code security and analysis**.

| Paquete | Versión inicial | Versión fijada en el proyecto | Origen | Estado de seguridad |
|---|---:|---:|---|---|
| Flask | 2.2.2 | 3.1.3 | Actualización manual inicial; después Dependabot | Pendiente de `pip-audit` y del build |
| Werkzeug | 2.2.2 | 3.1.9 | Actualización manual inicial; después Dependabot | Pendiente de `pip-audit` y del build |
| Jinja2 | 3.1.2 | 3.1.6 | Actualización manual inicial; después Dependabot | Pendiente de `pip-audit` y del build |
| gunicorn | 21.2.0 | 27.0.1 | Actualización manual inicial; después Dependabot | Pendiente de `pip-audit` y del build |
| prometheus-client | 0.17.1 | 0.26.0 | Actualización manual inicial; después Dependabot | Pendiente de `pip-audit` y del build |
| pytest | 8.3.4 | 9.2.0 | Actualización manual inicial; después Dependabot | Pendiente de `pip-audit` y del build |

No se asignan identificadores CVE por inferencia. Se copiarán los identificadores y versiones afectadas desde `reports/pip-audit.txt` o los reportes del PR de Dependabot. El pipeline analiza dependencias de ejecución y de pruebas y bloquea el despliegue ante vulnerabilidades conocidas.

## 6. Trazabilidad

El Jenkinsfile genera una versión `1.0.<build>+<commit>`, archiva los reportes y ejecuta `scripts/trazabilidad.py` al terminar cada build. El reporte del build actual se guarda como `reports/trazabilidad-build.md`; el historial persistente se escribe como `reports/TRAZABILIDAD.md`.

| Actividad | Hallazgo | Build de detección | Commit o PR correctivo | Build de verificación | Versión desplegada |
|---|---|---|---|---|---|
| Bandit (SAST) | Completar desde el reporte | Pendiente | Commit `VULN-xx` pendiente | Pendiente | Pendiente |
| OWASP ZAP (DAST) | Completar desde ZAP | Pendiente | Commit `VULN-xx` pendiente | Pendiente | Pendiente |
| Dependencias (SCA/Dependabot) | Completar con IDs del reporte o alerta | Pendiente | PR de Dependabot pendiente | Pendiente | Pendiente |

Para finalizar esta sección, copiar el `TRAZABILIDAD.md` del último build de Jenkins y registrar los SHA y números reales. No completar los campos de build, PR, alerta o versión con valores ficticios.
