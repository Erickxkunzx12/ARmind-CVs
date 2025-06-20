from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, send_file, make_response
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import sqlite3
# SQLite no necesita RealDictCursor
import os
import openai
from config_manager import ConfigManager

# Initialize configuration manager
config_manager = ConfigManager()
import PyPDF2
# from docx import Document  # Temporarily disabled
from datetime import datetime
import json
import uuid
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Cargar variables de entorno desde .env
from dotenv import load_dotenv
load_dotenv()  # Carga las variables de entorno desde .env

# Configuración de email usando variables de entorno
import os

EMAIL_CONFIG = {
    'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
    'smtp_port': int(os.getenv('SMTP_PORT', '587')),
    'email': os.getenv('EMAIL_USER'),
    'password': os.getenv('EMAIL_PASSWORD'),
    'use_tls': os.getenv('EMAIL_USE_TLS', 'True').lower() == 'true'
}

# Verificar si la configuración de email está completa
if not EMAIL_CONFIG['email'] or not EMAIL_CONFIG['password']:
    print("ADVERTENCIA: Configuración de email incompleta en variables de entorno")
# Intentar usar pdfkit como alternativa a WeasyPrint
try:
    import pdfkit
    PDFKIT_AVAILABLE = True
except ImportError:
    PDFKIT_AVAILABLE = False

# weasyprint deshabilitado en Windows por problemas de dependencias
WEASYPRINT_AVAILABLE = False

# Intentar usar reportlab como alternativa
try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import inch
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

from bs4 import BeautifulSoup  # Uncommented for HTML processing
import re
import tempfile  # Added for temporary file handling
import sqlite3  # Added for SQLite fallback

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'fallback_secret_key')
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Configuracion de OpenAI
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY
else:
    print("Advertencia: OpenAI API Key no configurada en variables de entorno")

# La configuracion de PostgreSQL se importa desde database_config.py

# Crear directorio de uploads si no existe
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

def generate_pdf_with_reportlab(html_content, title):
    """Generar PDF usando ReportLab desde contenido HTML"""
    if not REPORTLAB_AVAILABLE:
        return None
    
    try:
        from io import BytesIO
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib.colors import black, blue
        
        # Crear buffer para el PDF
        buffer = BytesIO()
        
        # Crear documento
        doc = SimpleDocTemplate(buffer, pagesize=A4, 
                              rightMargin=72, leftMargin=72,
                              topMargin=72, bottomMargin=18)
        
        # Obtener estilos
        styles = getSampleStyleSheet()
        
        # Crear estilos personalizados
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=1,  # Centrado
            textColor=black
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            textColor=blue
        )
        
        # Extraer texto del HTML usando BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Construir contenido del PDF
        story = []
        
        # Título principal
        title_text = soup.find('h1')
        if title_text:
            story.append(Paragraph(title_text.get_text().strip(), title_style))
        else:
            story.append(Paragraph(title, title_style))
        
        story.append(Spacer(1, 12))
        
        # Procesar el contenido
        for element in soup.find_all(['h2', 'h3', 'p', 'div']):
            text = element.get_text().strip()
            if text:
                if element.name in ['h2', 'h3']:
                    story.append(Paragraph(text, heading_style))
                else:
                    story.append(Paragraph(text, styles['Normal']))
                story.append(Spacer(1, 6))
        
        # Construir PDF
        doc.build(story)
        
        # Obtener contenido del buffer
        pdf_content = buffer.getvalue()
        buffer.close()
        
        return pdf_content
        
    except Exception as e:
        print(f"Error en generate_pdf_with_reportlab: {str(e)}")
        return None

def get_db_connection():
    """Obtener conexión a la base de datos SQLite con manejo de errores mejorado"""
    try:
        # Usar SQLite en lugar de PostgreSQL
        connection = sqlite3.connect('cv_analyzer.db')
        # Configurar SQLite para devolver diccionarios en lugar de tuplas
        connection.row_factory = sqlite3.Row
        return connection
    except Exception as err:
        logger.error(f"Error inesperado de base de datos: {err}")
        return None

    
    return text.strip()

def analyze_cv_with_ai(cv_text):
    """Analizar CV usando OpenAI"""
    prompt = f"""
    Actúa como un sistema ATS (Applicant Tracking System) profesional y analiza el siguiente currículum vitae.
    
    Evalúa la compatibilidad del CV con los sistemas ATS modernos y proporciona:
    1. Un puntaje general del 0 al 100 que indique la compatibilidad con sistemas ATS
    2. Análisis de fortalezas (máximo 5 puntos)
    3. Análisis de debilidades (máximo 5 puntos)
    4. Recomendaciones específicas de mejora (máximo 5 puntos)
    5. Sugerencias para palabras clave que podrían mejorar la visibilidad del CV
    
    Responde en formato JSON con la siguiente estructura:
    {{
        "score": número,
        "strengths": ["fortaleza1", "fortaleza2", ...],
        "weaknesses": ["debilidad1", "debilidad2", ...],
        "recommendations": ["recomendación1", "recomendación2", ...],
        "keywords": ["palabra_clave1", "palabra_clave2", ...]
    }}
    
    Currículum a analizar:
    {cv_text}
    """
    
    try:
        # Usar la sintaxis de OpenAI v0.28.1
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Eres un experto en recursos humanos, reclutamiento y sistemas ATS (Applicant Tracking System). Tu objetivo es ayudar a los candidatos a optimizar sus currículums para maximizar sus posibilidades de pasar los filtros ATS y llegar a la entrevista."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1500,
            temperature=0.7
        )
        
        analysis_text = response.choices[0].message.content
        analysis = json.loads(analysis_text)
        
        # Asegurarse de que todos los campos requeridos estén presentes
        if "keywords" not in analysis:
            analysis["keywords"] = []
            
        return analysis
    
    except json.JSONDecodeError as e:
        print(f"Error al decodificar JSON de la respuesta de IA: {e}")
        print(f"Respuesta recibida: {analysis_text}")
        return {
            "score": 0,
            "strengths": ["Error al procesar el análisis - Respuesta de IA no válida"],
            "weaknesses": ["No se pudo completar el análisis"],
            "recommendations": ["Intente nuevamente más tarde"],
            "keywords": []
        }
    except Exception as e:
        print(f"Error al analizar con IA: {e}")
        print(f"Tipo de error: {type(e).__name__}")
        return {
            "score": 0,
            "strengths": ["Error al procesar el análisis"],
            "weaknesses": ["No se pudo completar el análisis"],
            "recommendations": ["Intente nuevamente más tarde"],
            "keywords": []
        }

def save_cv_analysis(user_id, filename, content, analysis):
    """Guardar análisis de CV en la base de datos"""
    connection = get_db_connection()
    if connection:
        cursor = connection.cursor()
        
        # Insertar currículum
        cursor.execute(
            "INSERT INTO resumes (user_id, filename, content) VALUES (%s, %s, %s) RETURNING id",
            (user_id, filename, content)
        )
        resume_id = cursor.fetchone()[0]
        
        # Insertar feedback
        cursor.execute(
            "INSERT INTO feedback (resume_id, score, strengths, weaknesses, recommendations, keywords) VALUES (%s, %s, %s, %s, %s, %s)",
            (resume_id, analysis['score'], 
             json.dumps(analysis['strengths']), 
             json.dumps(analysis['weaknesses']), 
             json.dumps(analysis['recommendations']),
             json.dumps(analysis['keywords']))
        )
        
        connection.commit()
        cursor.close()
        connection.close()

@app.route('/cv_builder')
def cv_builder():
    """Alias para create_cv - Constructor de CV"""
    return create_cv()

@app.route('/create_cv')
def create_cv():
    """Constructor de CV estilo Harvard"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('create_cv.html')

@app.route('/get_user_cv_data', methods=['GET'])
def get_user_cv_data():
    """Obtener datos guardados del CV del usuario"""
    if not session.get('user_id'):
        return jsonify({'error': 'No autorizado'}), 401
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(
            "SELECT personal_info, professional_summary, education, experience, skills, languages, format_options FROM user_cv_data WHERE user_id = %s",
            (session['user_id'],)
        )
        result = cursor.fetchone()
        cursor.close()
        connection.close()
        
        if result:
            return jsonify({
                'success': True,
                'data': {
                    'personal_info': result[0] if result[0] else {},
                    'professional_summary': result[1] if result[1] else '',
                    'education': result[2] if result[2] else [],
                    'experience': result[3] if result[3] else [],
                    'skills': result[4] if result[4] else [],
                    'languages': result[5] if result[5] else [],
                    'format_options': result[6] if result[6] else {}
                }
            })
        else:
            return jsonify({'success': True, 'data': None})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def improve_cv_with_ai(cv_data):
    """Mejorar el CV usando OpenAI basándose en las metodologías seleccionadas"""
    if not OPENAI_API_KEY:
        return cv_data
    
    try:
        format_options = cv_data.get('format_options', {})
        tech_xyz = format_options.get('tech_xyz', False)
        tech_start = format_options.get('tech_start', False)
        selected_skills = cv_data.get('skills', [])
        
        # Crear prompt para mejorar resumen profesional
        professional_summary = cv_data.get('professional_summary', '')
        experience = cv_data.get('experience', [])
        
        # Mejorar resumen profesional usando metodología XYZ
        if professional_summary:
            if tech_xyz:
                summary_methodology = "XYZ (eXperience, Years, Zeal): destaca tu experiencia específica, años de trayectoria y pasión por el área"
            else:
                summary_methodology = "metodología estándar profesional"
                
            summary_prompt = f"""
            Mejora este resumen profesional usando la metodología {summary_methodology} e incorporando estas tecnologías: {', '.join(selected_skills)}.
            
            Resumen actual: {professional_summary}
            
            Instrucciones:
            - Mantén un tono profesional y conciso
            - Incorpora las tecnologías mencionadas de manera natural
            - Si usas XYZ: estructura destacando experiencia específica, años de trayectoria y entusiasmo
            - Máximo 150 palabras
            - Responde solo con el resumen mejorado, sin explicaciones adicionales
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Eres un experto en recursos humanos especializado en optimización de CVs."},
                    {"role": "user", "content": summary_prompt}
                ],
                max_tokens=300,
                temperature=0.7
            )
            
            improved_summary = response.choices[0].message.content.strip()
            cv_data['professional_summary'] = improved_summary
        
        # Mejorar experiencia laboral usando metodología STAR
        if experience:
            improved_experience = []
            for exp in experience:
                if exp.get('description'):
                    if tech_start:
                        exp_methodology = "STAR (Situation, Task, Action, Result): describe la situación, tarea asignada, acciones tomadas y resultados obtenidos"
                    else:
                        exp_methodology = "metodología estándar profesional orientada a logros"
                        
                    exp_prompt = f"""
                    Mejora esta descripción de experiencia laboral usando la metodología {exp_methodology} e incorporando estas tecnologías cuando sea relevante: {', '.join(selected_skills)}.
                    
                    Puesto: {exp.get('position', '')}
                    Empresa: {exp.get('company', '')}
                    Descripción actual: {exp.get('description', '')}
                    
                    Instrucciones:
                    - Si usas STAR: estructura cada logro con Situación, Tarea, Acción y Resultado
                    - Incorpora métricas y resultados cuantificables cuando sea posible
                    - Menciona tecnologías relevantes de manera natural
                    - Máximo 200 palabras
                    - Responde solo con la descripción mejorada, sin explicaciones adicionales
                    """
                    
                    response = openai.ChatCompletion.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": "Eres un experto en recursos humanos especializado en optimización de CVs."},
                            {"role": "user", "content": exp_prompt}
                        ],
                        max_tokens=400,
                        temperature=0.7
                    )
                    
                    improved_description = response.choices[0].message.content.strip()
                    exp['description'] = improved_description
                
                improved_experience.append(exp)
            
            cv_data['experience'] = improved_experience
        
        return cv_data
        
    except Exception as e:
        print(f"Error mejorando CV con IA: {str(e)}")
        return cv_data

@app.route('/save_cv', methods=['POST'])
def save_cv():
    if not session.get('user_id'):
        return redirect(url_for('login'))
    
    data = request.get_json()
    
    # Validar datos requeridos
    if not data or not all(key in data for key in ['personal_info', 'education', 'experience']):
        return jsonify({'error': 'Faltan datos requeridos'}), 400
    
    # Validar que las opciones de formato estén presentes
    if 'format_options' not in data:
        data['format_options'] = {'format': 'hardware', 'tech_xyz': False, 'tech_start': False}
    
    # Mejorar CV con IA antes de generar HTML
    improved_data = improve_cv_with_ai(data)
    
    # Generar HTML del CV con los datos mejorados
    cv_html = generate_cv_html(improved_data)
    
    # Guardar en la base de datos
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Guardar el CV generado
        cursor.execute(
            "INSERT INTO resumes (user_id, filename, content) VALUES (%s, %s, %s) RETURNING id",
            (session['user_id'], data['personal_info'].get('name', 'Mi CV'), cv_html)
        )
        cv_id = cursor.fetchone()[0]
        
        # Guardar/actualizar la información del usuario mejorada por IA para uso futuro
        cursor.execute(
            """
            INSERT INTO user_cv_data (user_id, personal_info, professional_summary, education, experience, skills, languages, format_options, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (user_id) 
            DO UPDATE SET 
                personal_info = EXCLUDED.personal_info,
                professional_summary = EXCLUDED.professional_summary,
                education = EXCLUDED.education,
                experience = EXCLUDED.experience,
                skills = EXCLUDED.skills,
                languages = EXCLUDED.languages,
                format_options = EXCLUDED.format_options,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                session['user_id'],
                json.dumps(improved_data.get('personal_info', {})),
                improved_data.get('professional_summary', ''),
                json.dumps(improved_data.get('education', [])),
                json.dumps(improved_data.get('experience', [])),
                json.dumps(improved_data.get('skills', [])),
                json.dumps(improved_data.get('languages', [])),
                json.dumps(improved_data.get('format_options', {}))
            )
        )
        
        connection.commit()
        cursor.close()
        connection.close()
        
        return jsonify({
            'success': True, 
            'cv_id': cv_id, 
            'message': 'CV guardado y mejorado con IA. Datos del usuario actualizados.',
            'improved_data': improved_data,
            'cv_html': cv_html
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/export_cv/<int:cv_id>')
def export_cv(cv_id):
    if not session.get('user_id'):
        return redirect(url_for('login'))
    
    # Obtener los datos del CV de la base de datos
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Primero verificar que el CV existe en la tabla resumes
        cursor.execute(
            "SELECT filename FROM resumes WHERE id = %s AND user_id = %s",
            (cv_id, session['user_id'])
        )
        resume_result = cursor.fetchone()
        
        if not resume_result:
            cursor.close()
            connection.close()
            return jsonify({'error': 'CV no encontrado'}), 404
        
        cv_title = resume_result[0]
        
        # Obtener los datos estructurados del CV desde user_cv_data
        cursor.execute(
            "SELECT personal_info, professional_summary, education, experience, skills, languages, format_options FROM user_cv_data WHERE user_id = %s",
            (session['user_id'],)
        )
        result = cursor.fetchone()
        
        if not result:
            cursor.close()
            connection.close()
            return jsonify({'error': 'Datos del CV no encontrados'}), 404
        
        personal_info, professional_summary, education, experience, skills, languages, format_options = result
        cursor.close()
        connection.close()
        
        # Reconstruir los datos del CV
        cv_data = {
            'personal_info': personal_info if personal_info else {},
            'professional_summary': professional_summary if professional_summary else '',
            'education': education if education else [],
            'experience': experience if experience else [],
            'skills': skills if skills else [],
            'languages': languages if languages else [],
            'format_options': format_options if format_options else {'format': 'hardware', 'tech_xyz': False, 'tech_start': False}
        }
        
        # Generar el HTML exactamente igual que en la vista previa
        cv_html = generate_cv_html(cv_data)
        
        # Crear HTML optimizado para PDF con estilos mejorados para impresión
        pdf_optimized_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>CV</title>
            <style>
                @page {{
                    margin: 0;
                    size: A4;
                    /* Eliminar headers y footers del navegador */
                    @top-left {{ content: ""; }}
                    @top-center {{ content: ""; }}
                    @top-right {{ content: ""; }}
                    @bottom-left {{ content: ""; }}
                    @bottom-center {{ content: ""; }}
                    @bottom-right {{ content: ""; }}
                }}
                
                @media print {{
                    html, body {{
                        margin: 0 !important;
                        padding: 0 !important;
                        width: 210mm !important;
                        height: 297mm !important;
                        font-size: 11pt !important;
                        line-height: 1.3 !important;
                        -webkit-print-color-adjust: exact !important;
                        color-adjust: exact !important;
                    }}
                    
                    body {{
                        padding: 20mm 15mm 15mm 15mm !important;
                    }}
                    
                    .no-print {{ display: none !important; }}
                    .page-break {{ page-break-before: always; }}
                    .section-title {{
                        border-bottom: 1px solid #000 !important;
                        page-break-after: avoid;
                    }}
                    .item {{
                        page-break-inside: avoid;
                    }}
                    
                    /* Eliminar cualquier contenido generado automáticamente */
                    *::before, *::after {{
                        content: none !important;
                    }}
                }}
                
                @media screen {{
                    body {{
                        max-width: 210mm;
                        margin: 20px auto;
                        padding: 20mm;
                        box-shadow: 0 0 10px rgba(0,0,0,0.1);
                        background: white;
                    }}
                    .print-instructions {{
                        position: fixed;
                        top: 10px;
                        right: 10px;
                        background: #007bff;
                        color: white;
                        padding: 10px 15px;
                        border-radius: 5px;
                        font-family: Arial, sans-serif;
                        font-size: 14px;
                        z-index: 1000;
                        box-shadow: 0 2px 10px rgba(0,0,0,0.2);
                    }}
                    .print-instructions button {{
                        background: white;
                        color: #007bff;
                        border: none;
                        padding: 5px 10px;
                        border-radius: 3px;
                        cursor: pointer;
                        margin-left: 10px;
                        font-weight: bold;
                    }}
                }}
                
                /* Estilos base del CV */
                body {{
                    font-family: 'Times New Roman', serif;
                    margin: 0;
                    padding: 20px;
                    line-height: 1.4;
                    color: #000;
                }}
                
                .header {{
                    text-align: center;
                    border-bottom: 2px solid #000;
                    padding-bottom: 10px;
                    margin-bottom: 20px;
                }}
                
                .name {{
                    font-size: 24px;
                    font-weight: bold;
                    margin-bottom: 5px;
                }}
                
                .contact {{
                    font-size: 12px;
                }}
                
                .section {{
                    margin-bottom: 20px;
                }}
                
                .section-title {{
                    font-size: 14px;
                    font-weight: bold;
                    border-bottom: 1px solid #000;
                    margin-bottom: 10px;
                    padding-bottom: 2px;
                }}
                
                .item {{
                    margin-bottom: 10px;
                }}
                
                .item-title {{
                    font-weight: bold;
                }}
                
                .item-subtitle {{
                    font-style: italic;
                }}
                
                .item-date {{
                    float: right;
                }}
                
                .skills-list {{
                    display: flex;
                    flex-wrap: wrap;
                    gap: 10px;
                }}
                
                .skill {{
                    background: #f0f0f0;
                    padding: 2px 8px;
                    border-radius: 3px;
                    font-size: 12px;
                }}
                
                .skill-xyz {{
                    background: #d1ecf1;
                    color: #0c5460;
                    font-weight: bold;
                }}
                
                .skill-start {{
                    background: #d4edda;
                    color: #155724;
                    font-weight: bold;
                }}
            </style>
            <script>
                function printPDF() {{
                    window.print();
                }}
                
                // Auto-abrir diálogo de impresión después de 1 segundo
                setTimeout(function() {{
                    if (confirm('¿Deseas abrir el diálogo de impresión para guardar como PDF?')) {{
                        window.print();
                    }}
                }}, 1000);
            </script>
        </head>
        <body>
            <div class="print-instructions no-print">
                📄 Presiona Ctrl+P para guardar como PDF
                <button onclick="printPDF()">Imprimir/PDF</button>
            </div>
            
            {cv_html[cv_html.find('<body>') + 6:cv_html.find('</body>')].strip() if '<body>' in cv_html else cv_html}
        </body>
        </html>
        """
        
        # Devolver el HTML optimizado para PDF
        response = make_response(pdf_optimized_html)
        response.headers['Content-Type'] = 'text/html; charset=utf-8'
        
        return response
        
    except Exception as e:
        return jsonify({'error': f'Error al obtener CV: {str(e)}'}), 500

@app.route('/job_search')
def job_search():
    """Motor de búsqueda de empleos"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('job_search.html')

@app.route('/search_jobs', methods=['POST'])
def search_jobs():
    """Buscar empleos en diferentes portales"""
    if 'user_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    
    query = request.json.get('query', '')
    location = request.json.get('location', '')
    source = request.json.get('source', 'all')
    
    jobs = []
    
    if source == 'all' or source == 'computrabajo':
        jobs.extend(scrape_computrabajo(query, location))
    
    if source == 'all' or source == 'indeed':
        jobs.extend(scrape_indeed(query, location))
    
    # Guardar empleos en la base de datos
    save_jobs_to_db(jobs)
    
    return jsonify({'jobs': jobs})

@app.route('/my_analyses')
def my_analyses():
    """Ver análisis previos del usuario"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    connection = get_db_connection()
    analyses = []
    
    if connection:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT f.id, r.filename, r.created_at, f.score, f.strengths, f.weaknesses, f.recommendations, f.keywords
            FROM resumes r
            INNER JOIN feedback f ON r.id = f.resume_id
            WHERE r.user_id = %s
            ORDER BY r.created_at DESC
        """, (session['user_id'],))
        
        results = cursor.fetchall()
        for result in results:
            analysis = {
                'id': result[0],  # Ahora es f.id (feedback ID)
                'filename': result[1],
                'created_at': result[2],
                'score': result[3] if result[3] else 0,
                'strengths': json.loads(result[4]) if result[4] else [],
                'weaknesses': json.loads(result[5]) if result[5] else [],
                'recommendations': json.loads(result[6]) if result[6] else [],
                'keywords': json.loads(result[7]) if result[7] else []
            }
            analyses.append(analysis)
        
        cursor.close()
        connection.close()
    
    return render_template('my_analyses.html', analyses=analyses)

def generate_professional_summary_section(professional_summary, use_xyz, use_start):
    """Generar sección de resumen profesional con metodologías aplicadas"""
    enhanced_summary = professional_summary
    
    if use_xyz or use_start:
        # Palabras clave y frases para metodología XYZ (enfoque en tecnologías emergentes e innovación)
        xyz_enhancements = [
            "con enfoque en tecnologías emergentes",
            "especializado en soluciones innovadoras",
            "con experiencia en transformación digital",
            "orientado a la implementación de nuevas tecnologías",
            "con visión estratégica en innovación tecnológica"
        ]
        
        # Palabras clave y frases para metodología Start (enfoque en fundamentos sólidos y crecimiento)
        start_enhancements = [
            "con sólidos fundamentos técnicos",
            "enfocado en el crecimiento profesional continuo",
            "con base sólida en principios fundamentales",
            "orientado al desarrollo progresivo de competencias",
            "con enfoque metodológico y estructurado"
        ]
        
        # Aplicar mejoras según las metodologías seleccionadas
        if use_xyz and use_start:
            # Combinar ambas metodologías
            enhanced_summary += f" {xyz_enhancements[0]} y {start_enhancements[0]}."
        elif use_xyz:
            # Solo metodología XYZ
            enhanced_summary += f" {xyz_enhancements[0]}."
        elif use_start:
            # Solo metodología Start
            enhanced_summary += f" {start_enhancements[0]}."
    
    return f'<div class="section"><div class="section-title">RESUMEN PROFESIONAL</div><div style="text-align: justify; line-height: 1.4;">{enhanced_summary}</div></div>'

def enhance_experience_description(description, use_xyz, use_start):
    """Mejorar descripción de experiencia con metodologías aplicadas"""
    if not description or not description.strip():
        return description
    
    enhanced_description = description
    
    if use_xyz or use_start:
        # Frases para metodología XYZ (enfoque en innovación y tecnologías emergentes)
        xyz_phrases = [
            "implementando soluciones innovadoras",
            "utilizando tecnologías de vanguardia",
            "desarrollando estrategias disruptivas",
            "aplicando metodologías ágiles y modernas",
            "liderando iniciativas de transformación digital"
        ]
        
        # Frases para metodología Start (enfoque en fundamentos y crecimiento estructurado)
        start_phrases = [
            "aplicando metodologías estructuradas",
            "siguiendo mejores prácticas establecidas",
            "implementando procesos sistemáticos",
            "desarrollando competencias fundamentales",
            "estableciendo bases sólidas para el crecimiento"
        ]
        
        # Aplicar mejoras según las metodologías seleccionadas
        if use_xyz and use_start:
            # Combinar ambas metodologías
            enhanced_description += f" Destacando por {xyz_phrases[0]} y {start_phrases[0]}."
        elif use_xyz:
            # Solo metodología XYZ
            enhanced_description += f" Destacando por {xyz_phrases[0]}."
        elif use_start:
            # Solo metodología Start
            enhanced_description += f" Destacando por {start_phrases[0]}."
    
    return enhanced_description

def generate_cv_html(cv_data):
    """Generar HTML del CV según el formato seleccionado"""
    personal = cv_data.get('personal_info', {})
    professional_summary = cv_data.get('professional_summary', '')
    education = cv_data.get('education', [])
    experience = cv_data.get('experience', [])
    skills = cv_data.get('skills', [])
    languages = cv_data.get('languages', [])
    format_options = cv_data.get('format_options', {'format': 'hardware', 'summary_tech_xyz': False, 'summary_tech_start': False, 'experience_tech_xyz': False, 'experience_tech_start': False})
    
    # Determinar el formato seleccionado
    is_ats_format = format_options.get('format') == 'ats'
    
    # Metodologías específicas por sección
    summary_tech_xyz = format_options.get('summary_tech_xyz', False)
    summary_tech_start = format_options.get('summary_tech_start', False)
    experience_tech_xyz = format_options.get('experience_tech_xyz', False)
    experience_tech_start = format_options.get('experience_tech_start', False)
    
    # Estilos base según el formato
    if is_ats_format:
        # Estilo ATS: Simple, sin diseño complejo, optimizado para sistemas de seguimiento
        styles = """
            body { font-family: Arial, sans-serif; margin: 0; padding: 20px; line-height: 1.4; }
            .header { text-align: left; border-bottom: 1px solid #000; padding-bottom: 10px; margin-bottom: 20px; }
            .name { font-size: 18px; font-weight: bold; margin-bottom: 5px; }
            .contact { font-size: 12px; }
            .section { margin-bottom: 20px; }
            .section-title { font-size: 14px; font-weight: bold; text-transform: uppercase; margin-bottom: 10px; }
            .item { margin-bottom: 10px; }
            .item-title { font-weight: bold; }
            .item-subtitle { font-style: italic; }
            .item-date { float: right; }
            .skills-list { margin-bottom: 10px; }
            .skill { margin-right: 5px; }
        """
    else:
        # Estilo Hardware: Formato profesional basado en la imagen de referencia
        styles = """
            body { 
                font-family: 'Times New Roman', serif; 
                margin: 0; 
                padding: 20px; 
                line-height: 1.4; 
                font-size: 11pt;
                color: #000;
            }
            .header { 
                text-align: left; 
                border-bottom: 2px solid #000; 
                padding-bottom: 15px; 
                margin-bottom: 25px; 
            }
            .name { 
                font-size: 18pt; 
                font-weight: bold; 
                margin-bottom: 8px; 
                text-align: center;
            }
            .contact { 
                font-size: 10pt; 
                text-align: center;
                margin-bottom: 5px;
            }
            .section { 
                margin-bottom: 20px; 
            }
            .section-title { 
                font-size: 12pt; 
                font-weight: bold; 
                text-transform: uppercase;
                border-bottom: 1px solid #000; 
                margin-bottom: 12px;
                padding-bottom: 3px;
            }
            .item { 
                margin-bottom: 15px; 
                position: relative;
            }
            .item-title { 
                font-weight: bold; 
                font-size: 11pt;
            }
            .item-subtitle { 
                font-style: italic; 
                font-size: 10pt;
                margin-bottom: 3px;
            }
            .item-date { 
                float: right; 
                font-size: 10pt;
                font-weight: normal;
            }
            .item-description {
                text-align: justify;
                margin-top: 5px;
                font-size: 10pt;
                line-height: 1.3;
            }
            .skills-list { 
                text-align: justify;
                font-size: 10pt;
            }
            .skill { 
                display: inline;
                margin-right: 8px;
            }
            .languages-section {
                font-size: 10pt;
            }
            .language-item {
                margin-bottom: 5px;
            }
        """
    
    # Construir información de contacto
    contact_info = [personal.get('email', ''), personal.get('phone', ''), personal.get('address', '')]
    contact_info = [info for info in contact_info if info]  # Filtrar campos vacíos
    contact_line = ' | '.join(contact_info)
    
    # Construir redes sociales
    social_links = []
    if personal.get('linkedin'):
        social_links.append(f"LinkedIn: {personal.get('linkedin')}")
    if personal.get('github'):
        social_links.append(f"GitHub: {personal.get('github')}")
    if personal.get('website'):
        social_links.append(f"Web: {personal.get('website')}")
    
    social_line = ' | '.join(social_links) if social_links else ''
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>CV - {personal.get('name', '')}</title>
        <style>
            {styles}
        </style>
    </head>
    <body>
        <div class="header">
            <div class="name">{personal.get('name', '')}</div>
            <div class="contact">
                {contact_line}
            </div>
            {f'<div class="contact" style="font-size: 11px; margin-top: 5px;">{social_line}</div>' if social_line else ''}
        </div>
        
        {generate_professional_summary_section(professional_summary, summary_tech_xyz, summary_tech_start) if professional_summary and professional_summary.strip() else ''}
        
        <div class="section">
            <div class="section-title">EDUCACIÓN</div>
    """
    
    for edu in education:
        html += f"""
            <div class="item">
                <div class="item-date">{edu.get('end_date', '')}</div>
                <div class="item-title">{edu.get('degree', '')}</div>
                <div class="item-subtitle">{edu.get('institution', '')}</div>
                {f'<div class="item-description">{edu.get("description", "")}</div>' if edu.get('description', '').strip() else ''}
            </div>
        """
    
    html += """
        </div>
        
        <div class="section">
            <div class="section-title">EXPERIENCIA PROFESIONAL</div>
    """
    
    for exp in experience:
        enhanced_description = enhance_experience_description(exp.get('description', ''), experience_tech_xyz, experience_tech_start)
        html += f"""
            <div class="item">
                <div class="item-date">{exp.get('start_date', '')} - {exp.get('end_date', '')}</div>
                <div class="item-title">{exp.get('position', '')}</div>
                <div class="item-subtitle">{exp.get('company', '')}</div>
                {f'<div class="item-description">{enhanced_description}</div>' if enhanced_description.strip() else ''}
            </div>
        """
    
    if skills:
        html += """
        </div>
        
        <div class="section">
            <div class="section-title">HABILIDADES</div>
        """
        
        # Palabras clave para tecnologías XYZ (emergentes)
        xyz_keywords = ['AI', 'Machine Learning', 'Blockchain', 'IoT', 'Cloud', 'DevOps', 'React', 'Vue', 'Angular', 'Node.js']
        
        # Palabras clave para tecnologías Start (fundamentales)
        start_keywords = ['Java', 'Python', 'C++', 'SQL', 'HTML', 'CSS', 'JavaScript', 'Git', 'Linux', 'Windows']
        
        if is_ats_format:
            # Formato ATS: lista simple de habilidades
            html += f'<div class="skills-list">{"، ".join(skills)}</div>'
        else:
            # Formato Hardware: lista simple de habilidades
            html += f'<div class="skills-list">{"، ".join(skills)}</div>'
    
    if languages:
        html += """
        </div>
        
        <div class="section">
            <div class="section-title">IDIOMAS</div>
        """
        
        for lang in languages:
            html += f'<div class="language-item">{lang.get("language", "")} - {lang.get("level", "")}</div>'
    
    html += """
        </div>
    </body>
    </html>
    """
    
    return html

def scrape_computrabajo(query, location):
    """Scraping de empleos de CompuTrabajo"""
    jobs = []
    
    try:
        # Construir URL de búsqueda
        base_url = "https://www.computrabajo.com"
        search_url = f"{base_url}/empleos-publicados-en-{location.lower().replace(' ', '-')}?q={query.replace(' ', '+')}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(search_url, headers=headers, timeout=10)
        # soup = BeautifulSoup(response.content, 'html.parser')  # Temporarily disabled
        
        # Buscar ofertas de empleo
        # job_listings = soup.find_all('div', class_='box_offer')  # Temporarily disabled
        job_listings = []  # Empty list when scraping is disabled
        
        for listing in job_listings[:10]:  # Limitar a 10 resultados
            try:
                title_elem = listing.find('h2', class_='fs18')
                company_elem = listing.find('p', class_='fs16')
                location_elem = listing.find('p', class_='fs13')
                
                if title_elem and company_elem:
                    title = title_elem.get_text(strip=True)
                    company = company_elem.get_text(strip=True)
                    job_location = location_elem.get_text(strip=True) if location_elem else location
                    
                    # Obtener enlace
                    link_elem = title_elem.find('a')
                    job_url = base_url + link_elem['href'] if link_elem else ''
                    
                    jobs.append({
                        'title': title,
                        'company': company,
                        'location': job_location,
                        'url': job_url,
                        'source': 'CompuTrabajo',
                        'description': ''
                    })
            except Exception as e:
                continue
                
    except Exception as e:
        print(f"Error scraping CompuTrabajo: {e}")
    
    return jobs

def scrape_indeed(query, location):
    """Scraping de empleos de Indeed"""
    jobs = []
    
    try:
        # Construir URL de búsqueda
        base_url = "https://www.indeed.com"
        search_url = f"{base_url}/jobs?q={query.replace(' ', '+')}&l={location.replace(' ', '+')}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(search_url, headers=headers, timeout=10)
        # soup = BeautifulSoup(response.content, 'html.parser')  # Temporarily disabled
        
        # Buscar ofertas de empleo
        # job_listings = soup.find_all('div', class_='job_seen_beacon')  # Temporarily disabled
        job_listings = []  # Empty list when scraping is disabled
        
        for listing in job_listings[:10]:  # Limitar a 10 resultados
            try:
                title_elem = listing.find('h2', class_='jobTitle')
                company_elem = listing.find('span', class_='companyName')
                location_elem = listing.find('div', class_='companyLocation')
                
                if title_elem and company_elem:
                    title_link = title_elem.find('a')
                    title = title_link.get_text(strip=True) if title_link else title_elem.get_text(strip=True)
                    company = company_elem.get_text(strip=True)
                    job_location = location_elem.get_text(strip=True) if location_elem else location
                    
                    # Obtener enlace
                    job_url = base_url + title_link['href'] if title_link and title_link.get('href') else ''
                    
                    jobs.append({
                        'title': title,
                        'company': company,
                        'location': job_location,
                        'url': job_url,
                        'source': 'Indeed',
                        'description': ''
                    })
            except Exception as e:
                continue
                
    except Exception as e:
        print(f"Error scraping Indeed: {e}")
    
    return jobs

def save_jobs_to_db(jobs):
    """Guardar empleos en la base de datos"""
    connection = get_db_connection()
    if connection:
        cursor = connection.cursor()
        
        for job in jobs:
            try:
                # Verificar si el empleo ya existe
                cursor.execute(
                    "SELECT id FROM jobs WHERE title = %s AND company = %s AND url = %s",
                    (job['title'], job['company'], job['url'])
                )
                
                if not cursor.fetchone():
                    cursor.execute(
                        "INSERT INTO jobs (title, company, location, description, url, source) VALUES (%s, %s, %s, %s, %s, %s)",
                        (job['title'], job['company'], job['location'], job['description'], job['url'], job['source'])
                    )
            except Exception as e:
                print(f"Error guardando empleo: {e}")
                continue
        
        connection.commit()
        cursor.close()
        connection.close()

@app.route('/profile')
def profile():
    """Perfil del usuario"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    connection = get_db_connection()
    user = None
    analyses_count = 0
    last_analysis = None
    
    if connection:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT id, username, email, created_at FROM users WHERE id = %s",
            (session['user_id'],)
        )
        user = cursor.fetchone()
        
        # Obtener estadísticas de análisis
        cursor.execute(
            "SELECT COUNT(*) FROM resumes WHERE user_id = %s",
            (session['user_id'],)
        )
        analyses_count = cursor.fetchone()[0]
        
        cursor.execute(
            "SELECT created_at FROM resumes WHERE user_id = %s ORDER BY created_at DESC LIMIT 1",
            (session['user_id'],)
        )
        result = cursor.fetchone()
        last_analysis = result[0] if result else None
        
        cursor.close()
        connection.close()
    
    return render_template('profile.html', user=user, analyses_count=analyses_count, last_analysis=last_analysis)

def generate_professional_summary_section(professional_summary, use_xyz, use_start):
    """Generar sección de resumen profesional con metodologías aplicadas"""
    enhanced_summary = professional_summary
    
    if use_xyz or use_start:
        # Palabras clave y frases para metodología XYZ (enfoque en tecnologías emergentes e innovación)
        xyz_enhancements = [
            "con enfoque en tecnologías emergentes",
            "especializado en soluciones innovadoras",
            "con experiencia en transformación digital",
            "orientado a la implementación de nuevas tecnologías",
            "con visión estratégica en innovación tecnológica"
        ]
        
        # Palabras clave y frases para metodología Start (enfoque en fundamentos sólidos y crecimiento)
        start_enhancements = [
            "con sólidos fundamentos técnicos",
            "enfocado en el crecimiento profesional continuo",
            "con base sólida en principios fundamentales",
            "orientado al desarrollo progresivo de competencias",
            "con enfoque metodológico y estructurado"
        ]
        
        # Aplicar mejoras según las metodologías seleccionadas
        if use_xyz and use_start:
            # Combinar ambas metodologías
            enhanced_summary += f" {xyz_enhancements[0]} y {start_enhancements[0]}."
        elif use_xyz:
            # Solo metodología XYZ
            enhanced_summary += f" {xyz_enhancements[0]}."
        elif use_start:
            # Solo metodología Start
            enhanced_summary += f" {start_enhancements[0]}."
    
    return f'<div class="section"><div class="section-title">RESUMEN PROFESIONAL</div><div style="text-align: justify; line-height: 1.4;">{enhanced_summary}</div></div>'

def enhance_experience_description(description, use_xyz, use_start):
    """Mejorar descripción de experiencia con metodologías aplicadas"""
    if not description or not description.strip():
        return description
    
    enhanced_description = description
    
    if use_xyz or use_start:
        # Frases para metodología XYZ (enfoque en innovación y tecnologías emergentes)
        xyz_phrases = [
            "implementando soluciones innovadoras",
            "utilizando tecnologías de vanguardia",
            "desarrollando estrategias disruptivas",
            "aplicando metodologías ágiles y modernas",
            "liderando iniciativas de transformación digital"
        ]
        
        # Frases para metodología Start (enfoque en fundamentos y crecimiento estructurado)
        start_phrases = [
            "aplicando metodologías estructuradas",
            "siguiendo mejores prácticas establecidas",
            "implementando procesos sistemáticos",
            "desarrollando competencias fundamentales",
            "estableciendo bases sólidas para el crecimiento"
        ]
        
        # Aplicar mejoras según las metodologías seleccionadas
        if use_xyz and use_start:
            # Combinar ambas metodologías
            enhanced_description += f" Destacando por {xyz_phrases[0]} y {start_phrases[0]}."
        elif use_xyz:
            # Solo metodología XYZ
            enhanced_description += f" Destacando por {xyz_phrases[0]}."
        elif use_start:
            # Solo metodología Start
            enhanced_description += f" Destacando por {start_phrases[0]}."
    
    return enhanced_description

def generate_cv_html(cv_data):
    """Generar HTML del CV según el formato seleccionado"""
    personal = cv_data.get('personal_info', {})
    professional_summary = cv_data.get('professional_summary', '')
    education = cv_data.get('education', [])
    experience = cv_data.get('experience', [])
    skills = cv_data.get('skills', [])
    languages = cv_data.get('languages', [])
    format_options = cv_data.get('format_options', {'format': 'hardware', 'summary_tech_xyz': False, 'summary_tech_start': False, 'experience_tech_xyz': False, 'experience_tech_start': False})
    
    # Determinar el formato seleccionado
    is_ats_format = format_options.get('format') == 'ats'
    
    # Metodologías específicas por sección
    summary_tech_xyz = format_options.get('summary_tech_xyz', False)
    summary_tech_start = format_options.get('summary_tech_start', False)
    experience_tech_xyz = format_options.get('experience_tech_xyz', False)
    experience_tech_start = format_options.get('experience_tech_start', False)
    
    # Estilos base según el formato
    if is_ats_format:
        # Estilo ATS: Simple, sin diseño complejo, optimizado para sistemas de seguimiento
        styles = """
            body { font-family: Arial, sans-serif; margin: 0; padding: 20px; line-height: 1.4; }
            .header { text-align: left; border-bottom: 1px solid #000; padding-bottom: 10px; margin-bottom: 20px; }
            .name { font-size: 18px; font-weight: bold; margin-bottom: 5px; }
            .contact { font-size: 12px; }
            .section { margin-bottom: 20px; }
            .section-title { font-size: 14px; font-weight: bold; text-transform: uppercase; margin-bottom: 10px; }
            .item { margin-bottom: 10px; }
            .item-title { font-weight: bold; }
            .item-subtitle { font-style: italic; }
            .item-date { float: right; }
            .skills-list { margin-bottom: 10px; }
            .skill { margin-right: 5px; }
        """
    else:
        # Estilo Hardware: Formato profesional basado en la imagen de referencia
        styles = """
            body { 
                font-family: 'Times New Roman', serif; 
                margin: 0; 
                padding: 20px; 
                line-height: 1.4; 
                font-size: 11pt;
                color: #000;
            }
            .header { 
                text-align: left; 
                border-bottom: 2px solid #000; 
                padding-bottom: 15px; 
                margin-bottom: 25px; 
            }
            .name { 
                font-size: 18pt; 
                font-weight: bold; 
                margin-bottom: 8px; 
                text-align: center;
            }
            .contact { 
                font-size: 10pt; 
                text-align: center;
                margin-bottom: 5px;
            }
            .section { 
                margin-bottom: 20px; 
            }
            .section-title { 
                font-size: 12pt; 
                font-weight: bold; 
                text-transform: uppercase;
                border-bottom: 1px solid #000; 
                margin-bottom: 12px;
                padding-bottom: 3px;
            }
            .item { 
                margin-bottom: 15px; 
                position: relative;
            }
            .item-title { 
                font-weight: bold; 
                font-size: 11pt;
            }
            .item-subtitle { 
                font-style: italic; 
                font-size: 10pt;
                margin-bottom: 3px;
            }
            .item-date { 
                float: right; 
                font-size: 10pt;
                font-weight: normal;
            }
            .item-description {
                text-align: justify;
                margin-top: 5px;
                font-size: 10pt;
                line-height: 1.3;
            }
            .skills-list { 
                text-align: justify;
                font-size: 10pt;
            }
            .skill { 
                display: inline;
                margin-right: 8px;
            }
            .languages-section {
                font-size: 10pt;
            }
            .language-item {
                margin-bottom: 5px;
            }
        """
    
    # Construir información de contacto
    contact_info = [personal.get('email', ''), personal.get('phone', ''), personal.get('address', '')]
    contact_info = [info for info in contact_info if info]  # Filtrar campos vacíos
    contact_line = ' | '.join(contact_info)
    
    # Construir redes sociales
    social_links = []
    if personal.get('linkedin'):
        social_links.append(f"LinkedIn: {personal.get('linkedin')}")
    if personal.get('github'):
        social_links.append(f"GitHub: {personal.get('github')}")
    if personal.get('website'):
        social_links.append(f"Web: {personal.get('website')}")
    
    social_line = ' | '.join(social_links) if social_links else ''
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>CV - {personal.get('name', '')}</title>
        <style>
            {styles}
        </style>
    </head>
    <body>
        <div class="header">
            <div class="name">{personal.get('name', '')}</div>
            <div class="contact">
                {contact_line}
            </div>
            {f'<div class="contact" style="font-size: 11px; margin-top: 5px;">{social_line}</div>' if social_line else ''}
        </div>
        
        {generate_professional_summary_section(professional_summary, summary_tech_xyz, summary_tech_start) if professional_summary and professional_summary.strip() else ''}
        
        <div class="section">
            <div class="section-title">EDUCACIÓN</div>
    """
    
    for edu in education:
        html += f"""
            <div class="item">
                <div class="item-date">{edu.get('end_date', '')}</div>
                <div class="item-title">{edu.get('degree', '')}</div>
                <div class="item-subtitle">{edu.get('institution', '')}</div>
                {f'<div class="item-description">{edu.get("description", "")}</div>' if edu.get('description', '').strip() else ''}
            </div>
        """
    
    html += """
        </div>
        
        <div class="section">
            <div class="section-title">EXPERIENCIA PROFESIONAL</div>
    """
    
    for exp in experience:
        enhanced_description = enhance_experience_description(exp.get('description', ''), experience_tech_xyz, experience_tech_start)
        html += f"""
            <div class="item">
                <div class="item-date">{exp.get('start_date', '')} - {exp.get('end_date', '')}</div>
                <div class="item-title">{exp.get('position', '')}</div>
                <div class="item-subtitle">{exp.get('company', '')}</div>
                {f'<div class="item-description">{enhanced_description}</div>' if enhanced_description.strip() else ''}
            </div>
        """
    
    if skills:
        html += """
        </div>
        
        <div class="section">
            <div class="section-title">HABILIDADES</div>
        """
        
        # Palabras clave para tecnologías XYZ (emergentes)
        xyz_keywords = ['AI', 'Machine Learning', 'Blockchain', 'IoT', 'Cloud', 'DevOps', 'React', 'Vue', 'Angular', 'Node.js']
        
        # Palabras clave para tecnologías Start (fundamentales)
        start_keywords = ['Java', 'Python', 'C++', 'SQL', 'HTML', 'CSS', 'JavaScript', 'Git', 'Linux', 'Windows']
        
        if is_ats_format:
            # Formato ATS: lista simple de habilidades
            html += f'<div class="skills-list">{"، ".join(skills)}</div>'
        else:
            # Formato Hardware: lista simple de habilidades
            html += f'<div class="skills-list">{"، ".join(skills)}</div>'
    
    if languages:
        html += """
        </div>
        
        <div class="section">
            <div class="section-title">IDIOMAS</div>
        """
        
        for lang in languages:
            html += f'<div class="language-item">{lang.get("language", "")} - {lang.get("level", "")}</div>'
    
    html += """
        </div>
    </body>
    </html>
    """
    
    return html

def scrape_computrabajo(query, location):
    """Scraping de empleos de CompuTrabajo"""
    jobs = []
    
    try:
        # Construir URL de búsqueda
        base_url = "https://www.computrabajo.com"
        search_url = f"{base_url}/empleos-publicados-en-{location.lower().replace(' ', '-')}?q={query.replace(' ', '+')}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(search_url, headers=headers, timeout=10)
        # soup = BeautifulSoup(response.content, 'html.parser')  # Temporarily disabled
        
        # Buscar ofertas de empleo
        # job_listings = soup.find_all('div', class_='box_offer')  # Temporarily disabled
        job_listings = []  # Empty list when scraping is disabled
        
        for listing in job_listings[:10]:  # Limitar a 10 resultados
            try:
                title_elem = listing.find('h2', class_='fs18')
                company_elem = listing.find('p', class_='fs16')
                location_elem = listing.find('p', class_='fs13')
                
                if title_elem and company_elem:
                    title = title_elem.get_text(strip=True)
                    company = company_elem.get_text(strip=True)
                    job_location = location_elem.get_text(strip=True) if location_elem else location
                    
                    # Obtener enlace
                    link_elem = title_elem.find('a')
                    job_url = base_url + link_elem['href'] if link_elem else ''
                    
                    jobs.append({
                        'title': title,
                        'company': company,
                        'location': job_location,
                        'url': job_url,
                        'source': 'CompuTrabajo',
                        'description': ''
                    })
            except Exception as e:
                continue
                
    except Exception as e:
        print(f"Error scraping CompuTrabajo: {e}")
    
    return jobs

def scrape_indeed(query, location):
    """Scraping de empleos de Indeed"""
    jobs = []
    
    try:
        # Construir URL de búsqueda
        base_url = "https://www.indeed.com"
        search_url = f"{base_url}/jobs?q={query.replace(' ', '+')}&l={location.replace(' ', '+')}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(search_url, headers=headers, timeout=10)
        # soup = BeautifulSoup(response.content, 'html.parser')  # Temporarily disabled
        
        # Buscar ofertas de empleo
        # job_listings = soup.find_all('div', class_='job_seen_beacon')  # Temporarily disabled
        job_listings = []  # Empty list when scraping is disabled
        
        for listing in job_listings[:10]:  # Limitar a 10 resultados
            try:
                title_elem = listing.find('h2', class_='jobTitle')
                company_elem = listing.find('span', class_='companyName')
                location_elem = listing.find('div', class_='companyLocation')
                
                if title_elem and company_elem:
                    title_link = title_elem.find('a')
                    title = title_link.get_text(strip=True) if title_link else title_elem.get_text(strip=True)
                    company = company_elem.get_text(strip=True)
                    job_location = location_elem.get_text(strip=True) if location_elem else location
                    
                    # Obtener enlace
                    job_url = base_url + title_link['href'] if title_link and title_link.get('href') else ''
                    
                    jobs.append({
                        'title': title,
                        'company': company,
                        'location': job_location,
                        'url': job_url,
                        'source': 'Indeed',
                        'description': ''
                    })
            except Exception as e:
                continue
                
    except Exception as e:
        print(f"Error scraping Indeed: {e}")
    
    return jobs

def save_jobs_to_db(jobs):
    """Guardar empleos en la base de datos"""
    connection = get_db_connection()
    if connection:
        cursor = connection.cursor()
        
        for job in jobs:
            try:
                # Verificar si el empleo ya existe
                cursor.execute(
                    "SELECT id FROM jobs WHERE title = %s AND company = %s AND url = %s",
                    (job['title'], job['company'], job['url'])
                )
                
                if not cursor.fetchone():
                    cursor.execute(
                        "INSERT INTO jobs (title, company, location, description, url, source) VALUES (%s, %s, %s, %s, %s, %s)",
                        (job['title'], job['company'], job['location'], job['description'], job['url'], job['source'])
                    )
            except Exception as e:
                print(f"Error guardando empleo: {e}")
                continue
        
        connection.commit()
        cursor.close()
        connection.close()

@app.route('/delete_analysis/<int:analysis_id>', methods=['DELETE'])
def delete_analysis(analysis_id):
    """Eliminar un análisis específico"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    
    connection = get_db_connection()
    if not connection:
        return jsonify({'success': False, 'message': 'Error de conexión a la base de datos'}), 500
    
    try:
        cursor = connection.cursor()
        
        # Verificar que el análisis pertenece al usuario a través de la tabla resumes
        cursor.execute(
            "SELECT f.id FROM feedback f JOIN resumes r ON f.resume_id = r.id WHERE f.id = %s AND r.user_id = %s",
            (analysis_id, session['user_id'])
        )
        
        if not cursor.fetchone():
            return jsonify({'success': False, 'message': 'Análisis no encontrado'}), 404
        
        # Eliminar el análisis de la tabla feedback
        cursor.execute(
            "DELETE FROM feedback WHERE id = %s AND resume_id IN (SELECT id FROM resumes WHERE user_id = %s)",
            (analysis_id, session['user_id'])
        )
        
        connection.commit()
        cursor.close()
        connection.close()
        
        return jsonify({'success': True, 'message': 'Análisis eliminado correctamente'})
        
    except Exception as e:
        print(f"Error eliminando análisis: {e}")
        return jsonify({'success': False, 'message': 'Error interno del servidor'}), 500

@app.route('/delete_account', methods=['DELETE'])
def delete_account():
    """Eliminar cuenta de usuario"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    
    connection = get_db_connection()
    if not connection:
        return jsonify({'success': False, 'message': 'Error de conexión a la base de datos'}), 500
    
    try:
        cursor = connection.cursor()
        user_id = session['user_id']
        
        # Eliminar todos los análisis del usuario
        cursor.execute("DELETE FROM feedback WHERE resume_id IN (SELECT id FROM resumes WHERE user_id = %s)", (user_id,))
        
        # Eliminar la cuenta del usuario
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        
        connection.commit()
        cursor.close()
        connection.close()
        
        # Limpiar la sesión
        session.clear()
        
        return jsonify({'success': True, 'message': 'Cuenta eliminada correctamente'})
        
    except Exception as e:
        print(f"Error eliminando cuenta: {e}")
        return jsonify({'success': False, 'message': 'Error interno del servidor'}), 500

@app.route('/change_password', methods=['POST'])
def change_password():
    """Cambiar contraseña del usuario"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    
    data = request.get_json()
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    
    if not current_password or not new_password:
        return jsonify({'success': False, 'message': 'Faltan datos requeridos'}), 400
    
    if len(new_password) < 6:
        return jsonify({'success': False, 'message': 'La nueva contraseña debe tener al menos 6 caracteres'}), 400
    
    connection = get_db_connection()
    if not connection:
        return jsonify({'success': False, 'message': 'Error de conexión a la base de datos'}), 500
    
    try:
        cursor = connection.cursor()
        
        # Verificar contraseña actual
        cursor.execute(
            "SELECT password FROM users WHERE id = %s",
            (session['user_id'],)
        )
        
        user_data = cursor.fetchone()
        if not user_data or not check_password_hash(user_data[0], current_password):
            return jsonify({'success': False, 'message': 'Contraseña actual incorrecta'}), 400
        
        # Actualizar contraseña
        hashed_password = generate_password_hash(new_password)
        cursor.execute(
            "UPDATE users SET password = %s WHERE id = %s",
            (hashed_password, session['user_id'])
        )
        
        connection.commit()
        cursor.close()
        connection.close()
        
        return jsonify({'success': True, 'message': 'Contraseña cambiada correctamente'})
        
    except Exception as e:
        print(f"Error cambiando contraseña: {e}")
        return jsonify({'success': False, 'message': 'Error interno del servidor'}), 500

if __name__ == '__main__':
    init_database()
    app.run(debug=True)