# Sistema Alumnos · SecureDev

API y portal web Flask de la **Evaluación Parcial 3 de OCY1102 – Ciberseguridad en desarrollo**.
El código inicial es intencionalmente vulnerable. Las mitigaciones están aplicadas y Jenkins verifica
pruebas funcionales, SAST, SCA, DAST en staging y despliega a producción solo después de pasar los gates.

> La evidencia y el estado de cada hallazgo se documentan en `docs/REGISTRO_SEGURIDAD.md` y en **Desarrollo EV3.docx**. Registra únicamente resultados obtenidos en el laboratorio.

## Rutas

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/` | Portada con enlaces y formularios |
| GET | `/hello?name=Ana` | Saludo |
| GET | `/alumnos` · `/alumnos/<id>` | Listado y detalle de alumnos |
| GET | `/alumnos/buscar?nombre=Ana` | Búsqueda por nombre |
| POST | `/login` | Acceso del administrador (formulario) |
| GET | `/health` · `/version` | Estado y versión desplegada |
| GET | `/metrics` | Métricas para Prometheus (no cambies sus nombres) |

## Contenido

| Archivo | Para qué sirve |
|---|---|
| `app.py` | Aplicación corregida: escape HTML, SQL parametrizado, gestión externa de secreto, CSRF, limitación de login y encabezados seguros |
| `tests/` | Pruebas funcionales (pytest). Deben seguir pasando después de corregir |
| `requirements.txt` | Dependencias de ejecución con versiones revisadas y fijadas |
| `requirements-dev.txt` | Dependencias solo de pruebas |
| `Jenkinsfile` | Pipeline: Build → Test → Bandit → pip-audit → staging → OWASP ZAP → producción con gate |
| `scripts/deploy.sh` | Despliega en `staging` (5001) o `produccion` (5000) y hace prueba de humo |
| `scripts/zap_scan.py` | Escaneo DAST con OWASP ZAP (spider, pasivo y activo) |
| `scripts/trazabilidad.py` | Registro build ↔ versión ↔ commit ↔ hallazgos ↔ despliegue |
| `scripts/revisar_local.sh` | Pruebas + Bandit + pip-audit en el contenedor taller, antes del push |
| `scripts/simular_ataque.py` | Ataque de prueba para ver incidentes en Grafana (solo en este laboratorio) |
| `docs/REGISTRO_SEGURIDAD.md` | Registro de revisiones, vulnerabilidades, incidentes, dependencias y trazabilidad |
| `.github/dependabot.yml` | Actualizaciones semanales de pip y GitHub Actions; habilita alertas en los ajustes de GitHub |

## Convención de commits (trazabilidad)

Cada corrección va en su propio commit y empieza con el identificador del hallazgo:
`VULN-02: consulta parametrizada en /alumnos/buscar`. Así cada build del registro de
trazabilidad se puede seguir hasta el hallazgo que corrigió.

## Preparar las evidencias

1. Inicia Docker Desktop y ejecuta `laboratorio/INICIAR-AQUI.cmd`.
2. Crea un repositorio en GitHub, conecta esta carpeta `proyecto/` y configura un job Pipeline from SCM que lea `Jenkinsfile`.
3. Habilita Dependabot alerts y security updates en GitHub. Fusiona actualizaciones solo después de revisar el diff y los builds.
4. Verifica que termine un build en verde. Inspecciona `reports/` en Jenkins y completa los números reales en `docs/REGISTRO_SEGURIDAD.md`.
5. Ejecuta la simulación de ataques indicada abajo y revisa Grafana. Pega capturas en **Desarrollo EV3.docx**, en la evidencia numerada correspondiente.
6. Completa el nombre y la URL del repositorio en **Desarrollo EV3.docx**.

No publiques claves de Jenkins, Grafana ni ZAP. Las claves locales de `laboratorio/secrets/` se excluyen de Git.

**Implementación de pipeline e identificación y corrección de vulnerabilidades**

1. Pipeline de CI/CD en Jenkins con etapas de construcción, pruebas y despliegue: configuración del job y build en verde.
2. Revisiones de seguridad continuas en el pipeline (análisis del código y de dependencias) y sus reportes.
3. Corrección de cada vulnerabilidad: commits `VULN-xx` (diff) y build que verifica la corrección.
4. Documentación de las revisiones, las vulnerabilidades identificadas y cómo se mitigó cada una (`docs/REGISTRO_SEGURIDAD.md`, secciones 1 y 2).

**Pruebas automatizadas de seguridad**

5. OWASP ZAP integrado en el pipeline de Jenkins: etapa en el `Jenkinsfile` y en la vista de etapas.
6. Resultados de ZAP sobre el código vulnerable: alertas encontradas y cómo se mitiga cada una (sección 3).

**Monitorización del entorno de producción**

7. Grafana configurado: fuente de datos Prometheus, dashboard de producción y regla de alerta.
8. Monitoreo en tiempo real: dashboard y alerta mostrando un incidente de seguridad.
9. Documentación del monitoreo y del incidente: detección, análisis, clasificación, respuesta y verificación (sección 4).

**Gestión de dependencias**

10. Dependabot implementado: `.github/dependabot.yml` y alertas activas en GitHub.
11. Dependencias actualizadas (PR de Dependabot) y build que verifica que no hay nuevas vulnerabilidades.
12. Documentación del proceso de gestión de dependencias (sección 5).

**Documentación y trazabilidad en el SDLC**

13. Trazabilidad de las actividades del pipeline (revisiones de seguridad, pruebas automatizadas y gestión de dependencias): `TRAZABILIDAD.md` del último build y sección 6.
14. Documentación que refleje las prácticas de seguridad en todo el ciclo de vida: registro completo en GitHub y pipeline final en verde.

## Referencia del laboratorio

| Servicio | Dirección |
|---|---|
| Jenkins | `http://localhost:8080` |
| Producción (puerto 5000) / Staging (puerto 5001) | `http://localhost:5000` · `http://localhost:5001` (dentro de Docker: `http://jenkins:5000` · `http://jenkins:5001`) |
| Prometheus | `http://localhost:9090` (dentro de Docker: `http://prometheus:9090`) |
| Grafana | `http://localhost:3000` (usuario `admin`) |
| OWASP ZAP | solo red interna: `http://zap:8080`; la clave de su API está en `/run/secrets/zap_api_key` del contenedor de Jenkins |

Métricas de la app: `http_requests_total`, `login_fallidos_total`, `peticiones_sospechosas_total{tipo}`, `app_info{version}`.

Para generar tráfico de demostración contra producción desde el contenedor `taller`:

```powershell
docker compose exec taller python3 scripts/simular_ataque.py http://jenkins:5000
```

Los intentos fallidos incrementan contadores y alcanzan HTTP 429 al superar el límite configurado. ZAP debe escanear staging desde Jenkins; no se debe escanear una app publicada en Internet.

## Evidencias de la evaluación

- `docs/Desarrollo EV3.docx`: pauta completada con los resultados verificados.
- `docs/Evidencias_Desarrollo_EV3.docx`: 14 láminas-resumen vinculadas a la pauta. Son resúmenes exportados; los registros originales se conservan bajo `docs/evidencias/build-3/`.
- `docs/evidencias/build-3/`: salidas de Jenkins #3, JUnit, Bandit, pip-audit, OWASP ZAP, trazabilidad, métricas Prometheus, simulación local y estado de Grafana/Dependabot.

Resultado final documentado: Jenkins build #3 SUCCESS, commit `9bbee95`, versión `1.0.3+9bbee95`, 14/14 pruebas, 0 vulnerabilidades conocidas por pip-audit y 0 alertas High/Medium/Low en ZAP.
