from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.section import WD_SECTION

BASE = Path(__file__).resolve().parents[3]
PROJECT = BASE / 'proyecto'
OUT = PROJECT / 'docs' / 'evidencias'
CAP = OUT / 'capturas'
CAP.mkdir(parents=True, exist_ok=True)

items = [
('Evidencia 1 · Pipeline CI/CD', 'Jenkins · Build #3 · SUCCESS', ['Build → Test → SAST → SCA → Staging → OWASP ZAP → Producción', 'Build #3 | commit 9bbee95 | versión 1.0.3+9bbee95', 'Resultado real: SUCCESS | 14 pruebas aprobadas'], 'build-3/jenkins-build-summary.json · jenkins-console.txt'),
('Evidencia 2 · Revisiones continuas', 'JUnit · Bandit · pip-audit · Build #3', ['JUnit: 14 aprobadas · 0 fallidas · 0 omitidas', 'Bandit: 0 hallazgos High / Medium / Low', 'pip-audit: 0 vulnerabilidades conocidas en 13 dependencias'], 'build-3/junit.xml · bandit.json · pip-audit.json'),
('Evidencia 3 · Mitigaciones de código', 'proyecto/app.py', ['Consultas SQL parametrizadas', 'Escape de salida HTML con plantillas', 'CSRF · rate limit · secretos por entorno · cabeceras seguras'], '../../app.py'),
('Evidencia 4 · Registro de vulnerabilidades', 'docs/REGISTRO_SEGURIDAD.md', ['Registro documenta 7 hallazgos del código inicial y sus CWE', 'Incluye riesgo, corrección aplicada y verificación', 'Se conservan hallazgos y acciones en el repositorio privado'], '../REGISTRO_SEGURIDAD.md'),
('Evidencia 5 · OWASP ZAP integrado', 'Jenkinsfile · DAST en staging', ['Deploy Staging → DAST - OWASP ZAP → Deploy Producción', 'El gate bloquea producción ante alertas High o Medium', 'Reportes HTML, JSON y resumen quedan archivados'], '../../Jenkinsfile · build-3/zap-report.html'),
('Evidencia 6 · Resultado DAST', 'OWASP ZAP · Build #3', ['Objetivo: staging local', 'High 0 · Medium 0 · Low 0 · Informational 2', 'Alertas informativas: Session Management Response Identified; User Agent Fuzzer'], 'build-3/zap-resumen.txt · zap-alertas.json · zap-report.html'),
('Evidencia 7 · Grafana y Prometheus', 'Monitoreo provisionado', ['Grafana 11.4.0 · datasource Prometheus', 'Dashboard: Sistema Alumnos · Producción', 'Alerta: más de 5 logins fallidos/min durante 30 s'], 'build-3/grafana-dashboard-status.json · ../../../laboratorio/grafana'),
('Evidencia 8 · Métricas en tiempo real', 'Prometheus · tras simulación en producción local', ['up{job=produccion} = 1 · up{job=staging} = 1', 'login_fallidos_total{job=produccion} = 10', 'HTTP 429 = 21 · solicitudes sospechosas SQLi = 1 · XSS = 1'], 'build-3/prometheus-metrics.json'),
('Evidencia 9 · Incidente simulado', 'Prueba controlada · Grafana', ['31 intentos de login; 21 respondieron HTTP 429', 'Payload SQLi: sin exposición de datos internos', 'Payload XSS: salida escapada · alerta Grafana en estado active'], 'build-3/simulacion-produccion.txt · grafana-alert-active-snapshot.json'),
('Evidencia 10 · Dependabot', 'GitHub · repositorio privado', ['Unluccky/Parcial-3-Sistema-Alumnos', 'Dependabot alerts: habilitadas', 'Actualizaciones automáticas de seguridad: habilitadas'], 'build-3/github-dependabot-status.json'),
('Evidencia 11 · Dependencias actualizadas', 'SCA · pip-audit · Build #3', ['13 dependencias analizadas', '0 vulnerabilidades conocidas · 0 correcciones pendientes', 'Versiones fijadas en requirements.txt y requirements-dev.txt'], 'build-3/pip-audit.json · pip-audit.txt · ../../requirements.txt'),
('Evidencia 12 · Proceso de dependencias', 'Política de actualización', ['Revisar diff y changelog', 'Ejecutar pruebas, Bandit, pip-audit y ZAP', 'Desplegar solo después de un pipeline exitoso'], '../REGISTRO_SEGURIDAD.md · sección 5'),
('Evidencia 13 · Trazabilidad SDLC', 'Build #3 · versión desplegada', ['Commit 9bbee95', 'Versión 1.0.3+9bbee95', 'Trazabilidad relaciona pruebas, SAST, SCA, DAST y despliegue'], 'build-3/TRAZABILIDAD.md · trazabilidad-build.md'),
('Evidencia 14 · Seguridad durante el SDLC', 'Jenkins · ciclo completo', ['Cambios versionados en GitHub', 'Pruebas y análisis automáticos antes de producción', 'Monitoreo continuo con métricas y alerta de seguridad'], '../../Jenkinsfile · ../../README.md'),
]

def font(size, bold=False):
    options = [r'C:\Windows\Fonts\segoeuib.ttf' if bold else r'C:\Windows\Fonts\segoeui.ttf', r'C:\Windows\Fonts\arial.ttf']
    for p in options:
        try: return ImageFont.truetype(p, size)
        except OSError: pass
    return ImageFont.load_default()

for i, (title, source, lines, ref) in enumerate(items, 1):
    im = Image.new('RGB', (1500, 860), '#f3f6fb')
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((28, 24, 1472, 836), radius=28, fill='white', outline='#d5dfeb', width=3)
    d.rounded_rectangle((28, 24, 1472, 160), radius=28, fill='#132238')
    d.text((76, 56), title, fill='white', font=font(42, True))
    d.text((78, 186), 'FUENTE VERIFICABLE', fill='#2463a6', font=font(24, True))
    d.text((78, 228), source, fill='#1e293b', font=font(34, True))
    y = 330
    for line in lines:
        d.rounded_rectangle((80, y+5, 110, y+35), radius=10, fill='#16845b')
        d.text((136, y), line, fill='#263449', font=font(30))
        y += 84
    d.line((80, 700, 1420, 700), fill='#d5dfeb', width=2)
    d.text((80, 728), 'Archivo de respaldo: ' + ref, fill='#64748b', font=font(21))
    d.text((80, 782), 'Evidencia exportada del laboratorio local · 23-11-2026', fill='#64748b', font=font(20))
    im.save(CAP / f'evidencia-{i:02}.png')

doc = Document()
sec = doc.sections[0]
sec.top_margin = Inches(.6); sec.bottom_margin = Inches(.55); sec.left_margin = Inches(.7); sec.right_margin = Inches(.7)
styles = doc.styles
styles['Normal'].font.name = 'Aptos'; styles['Normal'].font.size = Pt(10)
styles['Title'].font.name = 'Aptos Display'; styles['Title'].font.size = Pt(25); styles['Title'].font.color.rgb = RGBColor(19,34,56)
p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.add_run('EVIDENCIAS DE DESARROLLO EV3').bold = True
p.runs[0].font.size = Pt(24); p.runs[0].font.color.rgb = RGBColor(19,34,56)
p = doc.add_paragraph('Sistema de Alumnos · Evaluación Parcial N°3'); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
doc.add_paragraph('Estudiante: Jose Muñoz')
doc.add_paragraph('Este documento reúne 14 capturas-resumen asociadas a la pauta y a sus respaldos técnicos. Los resultados del pipeline, ZAP, SCA, GitHub y monitoreo corresponden a registros reales conservados en docs/evidencias/build-3. Las imágenes son láminas exportadas de esos resultados; los archivos originales indicados en cada lámina permiten comprobar el detalle. No son capturas de pantalla de las interfaces web.')
doc.add_paragraph('Repositorio: https://github.com/Unluccky/Parcial-3-Sistema-Alumnos')
doc.add_paragraph('Build exitoso comprobado: #3 · commit 9bbee95 · versión 1.0.3+9bbee95 · 14 pruebas aprobadas.')
for i, (title, source, lines, ref) in enumerate(items, 1):
    doc.add_page_break()
    h = doc.add_heading(title, 1); h.runs[0].font.color.rgb = RGBColor(19,34,56)
    doc.add_paragraph('Correspondencia: Evidencia ' + str(i) + ' de la pauta · Fuente: ' + source)
    doc.add_picture(str(CAP / f'evidencia-{i:02}.png'), width=Inches(6.55))
    p = doc.add_paragraph('Respaldo original: ' + ref)
    p.runs[0].font.size = Pt(9); p.runs[0].font.color.rgb = RGBColor(80,95,115)
doc.save(BASE / 'Evidencias_Desarrollo_EV3.docx')
print(f'generadas {len(items)} capturas y {BASE / "Evidencias_Desarrollo_EV3.docx"}')
