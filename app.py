from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, send_file, make_response
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import openai
from database_config import DB_CONFIG
import PyPDF2
from docx import Document
from datetime import datetime
import json
import uuid
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Cargar variables de entorno desde .env
from dotenv import load_dotenv
load_dotenv()  # Carga las variables de entorno desde .env

# Importar funciones de scraping
from job_search_service import scrape_linkedin, scrape_computrabajo as scrape_computrabajo_service, scrape_indeed_api

# Configuración de email usando variables de entorno
import os
from dotenv import load_dotenv

# Cargar variables de entorno desde archivo .env
load_dotenv()

# Intentar importar configuración de email desde archivo local
try:
    from email_config import EMAIL_CONFIG as CONFIG_FROM_FILE
    # Verificar si la configuración del archivo tiene valores de ejemplo
    example_values = ['tu_email@gmail.com', 'tu_email@outlook.com', 'tu_email@yahoo.com', 'tu_app_password', 'tu_contraseña']
    
    if (CONFIG_FROM_FILE['email'] in example_values or CONFIG_FROM_FILE['password'] in example_values):
        print("⚠️ email_config.py contiene valores de ejemplo, usando variables de entorno")
        # Usar variables de entorno si el archivo tiene valores de ejemplo
        EMAIL_CONFIG = {
            'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
            'smtp_port': int(os.getenv('SMTP_PORT', '587')),
            'email': os.getenv('EMAIL_USER'),
            'password': os.getenv('EMAIL_PASSWORD'),
            'use_tls': os.getenv('EMAIL_USE_TLS', 'True').lower() == 'true'
        }
        print("✅ Configuración de email cargada desde archivo .env")
    else:
        EMAIL_CONFIG = CONFIG_FROM_FILE
        print("✅ Configuración de email cargada desde email_config.py")
except ImportError:
    # Usar variables de entorno como respaldo
    EMAIL_CONFIG = {
        'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
        'smtp_port': int(os.getenv('SMTP_PORT', '587')),
        'email': os.getenv('EMAIL_USER'),
        'password': os.getenv('EMAIL_PASSWORD'),
        'use_tls': os.getenv('EMAIL_USE_TLS', 'True').lower() == 'true'
    }
    print("✅ Configuración de email cargada desde archivo .env (email_config.py no encontrado)")

# Verificar si la configuración de email está completa
# Lista de valores de ejemplo que indican configuración incompleta
example_values = ['tu_email@gmail.com', 'tu_email@outlook.com', 'tu_email@yahoo.com', 'tu_app_password', 'tu_contraseña']

if (not EMAIL_CONFIG['email'] or not EMAIL_CONFIG['password'] or 
    EMAIL_CONFIG['email'] in example_values or EMAIL_CONFIG['password'] in example_values):
    print("❌ ADVERTENCIA: Configuración de email incompleta o usando valores de ejemplo")
    print("   Para habilitar el envío de emails:")
    print("   1. Edita 'email_config.py'")
    print("   2. Reemplaza 'tu_email@gmail.com' con tu email real")
    print("   3. Reemplaza 'tu_app_password' con tu contraseña de aplicación real")
    print("   4. Reinicia el servidor")
    EMAIL_CONFIG_COMPLETE = False
else:
    EMAIL_CONFIG_COMPLETE = True
    print(f"✅ Email configurado: {EMAIL_CONFIG['email']}")
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

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'fallback_secret_key')
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Hacer datetime disponible en todas las plantillas
app.jinja_env.globals['datetime'] = datetime

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
    """Obtener conexión a la base de datos PostgreSQL con manejo de errores mejorado"""
    try:
        # Configuración manual para evitar problemas de codificación
        db_config = {
            'host': 'localhost',
            'database': 'cv_analyzer',
            'user': 'postgres',
            'password': 'Solido123',
            'port': '5432',
            'cursor_factory': RealDictCursor
        }
        
        # Usar opciones adicionales para manejar problemas de codificación
        os.environ['PGCLIENTENCODING'] = 'UTF8'
        
        connection = psycopg2.connect(
            host=db_config['host'],
            database=db_config['database'],
            user=db_config['user'],
            password=db_config['password'],
            port=db_config['port'],
            cursor_factory=db_config['cursor_factory'],
            client_encoding='UTF8',
            options="-c client_encoding=UTF8"
        )
        return connection
    except psycopg2.Error as err:
        logger.error(f"Error de conexión a la base de datos: {err}")
        return None
    except Exception as err:
        logger.error(f"Error inesperado de base de datos: {err}")
        return None

def get_db():
    """Obtener conexión a la base de datos con cursor de diccionario"""
    return get_db_connection()

def generate_verification_token():
    """Generar token único para verificación de email"""
    return str(uuid.uuid4())

def send_verification_email(email, username, token):
    """Enviar email de verificación"""
    try:
        # Crear mensaje
        msg = MIMEMultipart('alternative')
        msg['Subject'] = 'Verifica tu cuenta de ARMind CVs'
        msg['From'] = EMAIL_CONFIG['email']
        msg['To'] = email
        
        # Versión texto plano
        text = f"""Hola {username},
        
Gracias por registrarte en ARMind CVs. Para verificar tu cuenta, haz clic en el siguiente enlace:
        
http://localhost:5000/verify_email/{token}
        
Si no solicitaste esta verificación, puedes ignorar este mensaje.
        
Saludos,
El equipo de ARMind CVs
        """
        
        # Versión HTML
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #4A90E2; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f9f9f9; }}
                .button {{ display: inline-block; background-color: #4A90E2; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; }}
                .footer {{ text-align: center; margin-top: 20px; font-size: 12px; color: #777; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>ARMind CVs</h1>
                </div>
                <div class="content">
                    <h2>Hola {username},</h2>
                    <p>Gracias por registrarte en ARMind CVs. Para verificar tu cuenta, haz clic en el siguiente botón:</p>
                    <p style="text-align: center;">
                        <a href="http://localhost:5000/verify_email/{token}" class="button">Verificar mi cuenta</a>
                    </p>
                    <p>Si el botón no funciona, copia y pega el siguiente enlace en tu navegador:</p>
                    <p>http://localhost:5000/verify_email/{token}</p>
                    <p>Si no solicitaste esta verificación, puedes ignorar este mensaje.</p>
                </div>
                <div class="footer">
                    <p>© 2023 ARMind CVs. Todos los derechos reservados.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Adjuntar partes al mensaje
        part1 = MIMEText(text, 'plain')
        part2 = MIMEText(html, 'html')
        msg.attach(part1)
        msg.attach(part2)
        
        # Conectar al servidor SMTP
        server = smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port'])
        if EMAIL_CONFIG['use_tls']:
            server.starttls()
        
        # Iniciar sesión
        server.login(EMAIL_CONFIG['email'], EMAIL_CONFIG['password'])
        
        # Enviar email
        server.sendmail(EMAIL_CONFIG['email'], email, msg.as_string())
        server.quit()
        
        print(f"✅ Email de verificación enviado exitosamente a: {email}")
        print(f"   Usuario: {username}")
        print(f"   Token: {token}")
        return True
    except Exception as e:
        print(f"Error al enviar email de verificación: {e}")
        print(f"Email destino: {email}")
        print(f"Username: {username}")
        print(f"Token: {token}")
        print(f"Configuración SMTP: {EMAIL_CONFIG['smtp_server']}:{EMAIL_CONFIG['smtp_port']}")
        import traceback
        traceback.print_exc()
        return False

def generate_reset_token():
    """Generar token único para reset de contraseña"""
    return str(uuid.uuid4())

def send_password_reset_email(email, username, token):
    """Enviar email de recuperación de contraseña"""
    try:
        # Crear mensaje
        msg = MIMEMultipart('alternative')
        msg['Subject'] = 'Recuperar contraseña - ARMind CVs'
        msg['From'] = EMAIL_CONFIG['email']
        msg['To'] = email
        
        # Versión texto plano
        text = f"""Hola {username},
        
Hemos recibido una solicitud para restablecer tu contraseña en ARMind CVs.
        
Para restablecer tu contraseña, haz clic en el siguiente enlace:
        
http://localhost:5000/reset_password/{token}
        
Este enlace expirará en 1 hora por seguridad.
        
Si no solicitaste este restablecimiento, puedes ignorar este mensaje.
        
Saludos,
El equipo de ARMind CVs
        """
        
        # Versión HTML
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #dc3545; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f9f9f9; }}
                .button {{ display: inline-block; background-color: #dc3545; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; font-weight: bold; }}
                .footer {{ text-align: center; margin-top: 20px; font-size: 12px; color: #777; }}
                .warning {{ background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 10px; border-radius: 5px; margin: 15px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔐 Recuperar Contraseña</h1>
                </div>
                <div class="content">
                    <h2>Hola {username},</h2>
                    <p>Hemos recibido una solicitud para restablecer tu contraseña en ARMind CVs.</p>
                    <p style="text-align: center;">
                        <a href="http://localhost:5000/reset_password/{token}" class="button">Restablecer mi contraseña</a>
                    </p>
                    <div class="warning">
                        <strong>⚠️ Importante:</strong> Este enlace expirará en 1 hora por seguridad.
                    </div>
                    <p>Si el botón no funciona, copia y pega el siguiente enlace en tu navegador:</p>
                    <p style="word-break: break-all;">http://localhost:5000/reset_password/{token}</p>
                    <p>Si no solicitaste este restablecimiento, puedes ignorar este mensaje de forma segura.</p>
                </div>
                <div class="footer">
                    <p>© 2023 ARMind CVs. Todos los derechos reservados.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Adjuntar partes al mensaje
        part1 = MIMEText(text, 'plain')
        part2 = MIMEText(html, 'html')
        msg.attach(part1)
        msg.attach(part2)
        
        # Conectar al servidor SMTP
        server = smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port'])
        if EMAIL_CONFIG['use_tls']:
            server.starttls()
        
        # Iniciar sesión
        server.login(EMAIL_CONFIG['email'], EMAIL_CONFIG['password'])
        
        # Enviar email
        server.sendmail(EMAIL_CONFIG['email'], email, msg.as_string())
        server.quit()
        
        print(f"✅ Email de recuperación enviado exitosamente a: {email}")
        print(f"   Usuario: {username}")
        print(f"   Token: {token}")
        return True
    except Exception as e:
        print(f"Error al enviar email de recuperación: {e}")
        print(f"Email destino: {email}")
        print(f"Username: {username}")
        print(f"Token: {token}")
        import traceback
        traceback.print_exc()
        return False

def validate_password_strength(password):
    """Validar que la contraseña cumpla con los requisitos de seguridad"""
    errors = []
    
    if len(password) < 8:
        errors.append("La contraseña debe tener al menos 8 caracteres")
    
    if not re.search(r'[a-z]', password):
        errors.append("La contraseña debe contener al menos una letra minúscula")
    
    if not re.search(r'[A-Z]', password):
        errors.append("La contraseña debe contener al menos una letra mayúscula")
    
    if not re.search(r'\d', password):
        errors.append("La contraseña debe contener al menos un número")
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>\-_+=\[\]\\;/~`]', password):
        errors.append("La contraseña debe contener al menos un carácter especial")
    
    return errors

def init_database():
    """Inicializar la base de datos y crear las tablas necesarias"""
    connection = get_db_connection()
    if not connection:
        logger.error("No se pudo conectar a la base de datos para inicializar")
        return False
        
    try:
        cursor = connection.cursor()
        
        # Crear tabla de usuarios
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(255) UNIQUE NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                email_verified BOOLEAN DEFAULT FALSE,
                verification_token VARCHAR(255),
                reset_token VARCHAR(255),
                reset_token_expires TIMESTAMP,
                role VARCHAR(50) DEFAULT 'user',
                is_banned BOOLEAN DEFAULT FALSE,
                ban_until TIMESTAMP NULL,
                ban_reason TEXT,
                last_login TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Crear tabla de curriculums
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS resumes (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                filename VARCHAR(255) NOT NULL,
                file_path VARCHAR(500) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Crear tabla de empleos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id SERIAL PRIMARY KEY,
                title VARCHAR(500),
                company VARCHAR(255),
                location VARCHAR(255),
                description TEXT,
                url VARCHAR(1000),
                source VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Crear tabla de feedback de IA
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id SERIAL PRIMARY KEY,
                resume_id INTEGER REFERENCES resumes(id) ON DELETE CASCADE,
                score INTEGER,
                strengths TEXT,
                weaknesses TEXT,
                recommendations TEXT,
                keywords TEXT,
                s3_key VARCHAR(500),
                analysis_type VARCHAR(100),
                ai_provider VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Crear tabla para guardar información del CV del usuario
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_cv_data (
                id SERIAL PRIMARY KEY,
                user_id INTEGER UNIQUE REFERENCES users(id) ON DELETE CASCADE,
                personal_info TEXT,
                professional_summary TEXT,
                education TEXT,
                experience TEXT,
                skills TEXT,
                languages TEXT,
                format_options TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Verificar si la columna professional_summary existe (PostgreSQL)
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='user_cv_data' AND column_name='professional_summary'
        """)
        if not cursor.fetchone():
            cursor.execute("ALTER TABLE user_cv_data ADD COLUMN professional_summary TEXT")
        
        # Verificar y agregar nuevas columnas de administración y reset de contraseña
        admin_columns = [
            ('role', 'VARCHAR(50) DEFAULT \'user\''),
            ('is_banned', 'BOOLEAN DEFAULT FALSE'),
            ('ban_until', 'TIMESTAMP NULL'),
            ('ban_reason', 'TEXT'),
            ('last_login', 'TIMESTAMP'),
            ('reset_token', 'VARCHAR(255)'),
            ('reset_token_expires', 'TIMESTAMP')
        ]
        
        for column_name, column_def in admin_columns:
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='users' AND column_name=%s
            """, (column_name,))
            if not cursor.fetchone():
                cursor.execute(f"ALTER TABLE users ADD COLUMN {column_name} {column_def}")
        
        connection.commit()
        cursor.close()
        connection.close()
        print("Base de datos inicializada correctamente")
        return True
        
    except psycopg2.Error as e:
        logger.error(f"Error de PostgreSQL al inicializar la base de datos: {e}")
        if connection:
            connection.rollback()
            connection.close()
        return False
    except Exception as e:
        logger.error(f"Error inesperado al inicializar la base de datos: {e}")
        if connection:
            connection.rollback()
            connection.close()
        return False

@app.route('/')
def index():
    """Página principal"""
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Registro de usuarios"""
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        add_console_log('INFO', f'Intento de registro para usuario: {username} ({email})', 'AUTH')
        
        # Validaciones básicas
        if not username or not email or not password:
            add_console_log('WARNING', f'Registro fallido - campos incompletos para: {username}', 'AUTH')
            flash('Todos los campos son obligatorios', 'error')
            return render_template('register.html')
        
        # Validar fortaleza de la contraseña
        password_errors = validate_password_strength(password)
        if password_errors:
            add_console_log('WARNING', f'Registro fallido - contraseña débil para: {username}', 'AUTH')
            for error in password_errors:
                flash(error, 'error')
            return render_template('register.html')
        
        # Hash de la contraseña
        password_hash = generate_password_hash(password)
        
        # Generar token de verificación
        verification_token = generate_verification_token()
        
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            try:
                cursor.execute(
                    "INSERT INTO users (username, email, password_hash, email_verified, verification_token) VALUES (%s, %s, %s, %s, %s) RETURNING id",
                    (username, email, password_hash, False, verification_token)
                )
                user_id = cursor.fetchone()['id']
                connection.commit()
                
                add_console_log('INFO', f'Usuario registrado exitosamente: {username} (ID: {user_id})', 'AUTH')
                
                # Enviar correo de verificación
                print(f"🔄 Intentando enviar email de verificación...")
                email_sent = send_verification_email(email, username, verification_token)
                
                if email_sent:
                    add_console_log('INFO', f'Email de verificación enviado a: {email}', 'EMAIL')
                    print(f"✅ Email de verificación procesado correctamente")
                    flash('Usuario registrado exitosamente. Por favor, verifica tu correo electrónico para activar tu cuenta.', 'success')
                else:
                    add_console_log('ERROR', f'Error al enviar email de verificación a: {email}', 'EMAIL')
                    print(f"❌ Error al enviar email de verificación")
                    flash('Usuario registrado, pero hubo un problema al enviar el email de verificación. Contacta al administrador.', 'warning')
                return redirect(url_for('login'))
            except Exception as e:
                add_console_log('ERROR', f'Error al registrar usuario {username}: {str(e)}', 'AUTH')
                flash(f'Error al registrar usuario: {e}', 'error')
            finally:
                cursor.close()
                connection.close()
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Inicio de sesión"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        add_console_log('INFO', f'Intento de login para usuario: {username}', 'AUTH')
        
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            cursor.execute(
                "SELECT id, username, password_hash, email, email_verified, role, is_banned, ban_until, ban_reason FROM users WHERE username = %s",
                (username,)
            )
            user = cursor.fetchone()
            
            if user and check_password_hash(user['password_hash'], password):
                # Verificar si el correo está verificado
                if not user['email_verified']:
                    add_console_log('WARNING', f'Usuario no verificado intentó acceder: {username}', 'AUTH')
                    cursor.close()
                    connection.close()
                    flash('Por favor, verifica tu correo electrónico antes de iniciar sesión. Si no has recibido el correo de verificación, puedes solicitar uno nuevo.', 'warning')
                    return render_template('login.html', unverified_email=user['email'])
                
                # Verificar si el usuario está baneado
                if user['is_banned']:
                    ban_message = 'Tu cuenta ha sido suspendida.'
                    if user['ban_until']:
                        from datetime import datetime
                        if datetime.now() < user['ban_until']:
                            ban_message += f" Suspensión hasta: {user['ban_until'].strftime('%d/%m/%Y %H:%M')}"
                        else:
                            # El ban ha expirado, desbanearlo
                            cursor.execute(
                                "UPDATE users SET is_banned = FALSE, ban_until = NULL, ban_reason = NULL WHERE id = %s",
                                (user['id'],)
                            )
                            connection.commit()
                    else:
                        ban_message += ' Suspensión permanente.'
                    
                    if user['ban_reason']:
                        ban_message += f" Razón: {user['ban_reason']}"
                    
                    if user['is_banned'] and (not user['ban_until'] or datetime.now() < user['ban_until']):
                        add_console_log('WARNING', f'Usuario baneado intentó acceder: {username} - {ban_message}', 'AUTH')
                        cursor.close()
                        connection.close()
                        flash(ban_message, 'error')
                        return render_template('login.html')
                
                # Actualizar último login
                cursor.execute(
                    "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = %s",
                    (user['id'],)
                )
                connection.commit()
                
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['user_role'] = user.get('role', 'user')
                
                add_console_log('INFO', f'Login exitoso para {user.get("role", "user")}: {username}', 'AUTH')
                
                cursor.close()
                connection.close()
                
                flash('Inicio de sesión exitoso', 'success')
                
                # Redirigir según el rol
                if user.get('role') == 'admin':
                    return redirect(url_for('admin_dashboard'))
                else:
                    return redirect(url_for('dashboard'))
            else:
                add_console_log('WARNING', f'Login fallido para usuario: {username}', 'AUTH')
                cursor.close()
                connection.close()
                flash('Credenciales inválidas', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Cerrar sesión"""
    username = session.get('username', 'unknown')
    add_console_log('INFO', f'Usuario cerró sesión: {username}', 'AUTH')
    session.clear()
    flash('Sesión cerrada', 'info')
    return redirect(url_for('index'))

@app.route('/forgot_password', methods=['POST'])
def forgot_password():
    """Solicitar recuperación de contraseña"""
    email = request.form.get('resetEmail')
    
    if not email:
        return jsonify({'success': False, 'message': 'Email es requerido'}), 400
    
    # Verificar si la configuración de email está completa
    if not EMAIL_CONFIG_COMPLETE:
        add_console_log('ERROR', 'Intento de recuperación de contraseña sin configuración de email', 'AUTH')
        return jsonify({
            'success': False, 
            'message': 'El servicio de recuperación de contraseña no está disponible. Contacta al administrador.'
        }), 503
    
    add_console_log('INFO', f'Solicitud de recuperación de contraseña para: {email}', 'AUTH')
    
    connection = get_db_connection()
    if connection:
        cursor = connection.cursor()
        try:
            # Verificar si el email existe
            cursor.execute("SELECT id, username, email FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()
            
            if user:
                # Generar token de reset
                reset_token = generate_reset_token()
                
                # Establecer expiración del token (1 hora)
                from datetime import datetime, timedelta
                expires_at = datetime.now() + timedelta(hours=1)
                
                # Guardar token en la base de datos
                cursor.execute(
                    "UPDATE users SET reset_token = %s, reset_token_expires = %s WHERE id = %s",
                    (reset_token, expires_at, user['id'])
                )
                connection.commit()
                
                # Enviar email de recuperación
                email_sent = send_password_reset_email(user['email'], user['username'], reset_token)
                
                if email_sent:
                    add_console_log('INFO', f'Email de recuperación enviado a: {email}', 'EMAIL')
                    return jsonify({'success': True, 'message': 'Se ha enviado un enlace de recuperación a tu correo electrónico.'})
                else:
                    add_console_log('ERROR', f'Error al enviar email de recuperación a: {email}', 'EMAIL')
                    return jsonify({'success': False, 'message': 'Error al enviar el email. Inténtalo más tarde.'}), 500
            else:
                # Por seguridad, no revelamos si el email existe o no
                add_console_log('WARNING', f'Intento de recuperación con email inexistente: {email}', 'AUTH')
                return jsonify({'success': True, 'message': 'Si el email existe, se ha enviado un enlace de recuperación.'})
                
        except Exception as e:
            add_console_log('ERROR', f'Error en recuperación de contraseña para {email}: {str(e)}', 'AUTH')
            return jsonify({'success': False, 'message': 'Error interno del servidor'}), 500
        finally:
            cursor.close()
            connection.close()
    
    return jsonify({'success': False, 'message': 'Error de conexión a la base de datos'}), 500

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Restablecer contraseña con token"""
    if request.method == 'GET':
        # Verificar si el token es válido
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            try:
                from datetime import datetime
                cursor.execute(
                    "SELECT id, username, email FROM users WHERE reset_token = %s AND reset_token_expires > %s",
                    (token, datetime.now())
                )
                user = cursor.fetchone()
                
                if user:
                    return render_template('reset_password.html', token=token, username=user['username'])
                else:
                    add_console_log('WARNING', f'Token de reset inválido o expirado: {token}', 'AUTH')
                    flash('El enlace de recuperación es inválido o ha expirado. Solicita uno nuevo.', 'error')
                    return redirect(url_for('login'))
                    
            except Exception as e:
                add_console_log('ERROR', f'Error al verificar token de reset: {str(e)}', 'AUTH')
                flash('Error al procesar la solicitud', 'error')
                return redirect(url_for('login'))
            finally:
                cursor.close()
                connection.close()
    
    elif request.method == 'POST':
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # Validaciones
        if not new_password or not confirm_password:
            flash('Todos los campos son obligatorios', 'error')
            return render_template('reset_password.html', token=token)
        
        if new_password != confirm_password:
            flash('Las contraseñas no coinciden', 'error')
            return render_template('reset_password.html', token=token)
        
        # Validar fortaleza de la contraseña
        password_errors = validate_password_strength(new_password)
        if password_errors:
            for error in password_errors:
                flash(error, 'error')
            return render_template('reset_password.html', token=token)
        
        # Actualizar contraseña
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            try:
                from datetime import datetime
                # Verificar token nuevamente
                cursor.execute(
                    "SELECT id, username, email FROM users WHERE reset_token = %s AND reset_token_expires > %s",
                    (token, datetime.now())
                )
                user = cursor.fetchone()
                
                if user:
                    # Actualizar contraseña y limpiar token
                    password_hash = generate_password_hash(new_password)
                    cursor.execute(
                        "UPDATE users SET password_hash = %s, reset_token = NULL, reset_token_expires = NULL WHERE id = %s",
                        (password_hash, user['id'])
                    )
                    connection.commit()
                    
                    add_console_log('INFO', f'Contraseña restablecida exitosamente para: {user["username"]}', 'AUTH')
                    flash('Tu contraseña ha sido restablecida exitosamente. Ya puedes iniciar sesión.', 'success')
                    return redirect(url_for('login'))
                else:
                    add_console_log('WARNING', f'Token de reset inválido o expirado en POST: {token}', 'AUTH')
                    flash('El enlace de recuperación es inválido o ha expirado.', 'error')
                    return redirect(url_for('login'))
                    
            except Exception as e:
                add_console_log('ERROR', f'Error al restablecer contraseña: {str(e)}', 'AUTH')
                flash('Error al restablecer la contraseña', 'error')
                return render_template('reset_password.html', token=token)
            finally:
                cursor.close()
                connection.close()
    
    flash('Error de conexión a la base de datos', 'error')
    return redirect(url_for('login'))

@app.route('/resend_verification', methods=['POST'])
def resend_verification():
    """Reenviar correo de verificación"""
    if request.method == 'POST':
        email = request.form.get('email')
        
        if not email:
            flash('Por favor, introduce tu correo electrónico', 'danger')
            return redirect(url_for('login'))
        
        # Verificar si el usuario existe y no está verificado
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
                user = cursor.fetchone()
                
                if not user:
                    flash('No existe una cuenta con ese correo electrónico', 'danger')
                    return redirect(url_for('login'))
                
                if user['email_verified']:
                    flash('Esta cuenta ya está verificada. Puedes iniciar sesión', 'info')
                    return redirect(url_for('login'))
                
                # Generar nuevo token
                token = generate_verification_token()
                
                # Actualizar token en la base de datos
                cursor.execute(
                    "UPDATE users SET verification_token = %s WHERE id = %s",
                    (token, user['id'])
                )
                conn.commit()
                
                # Enviar correo de verificación
                if send_verification_email(user['email'], user['username'], token):
                    flash('Se ha enviado un nuevo correo de verificación. Por favor, revisa tu bandeja de entrada', 'success')
                else:
                    flash('Error al enviar el correo de verificación. Por favor, inténtalo de nuevo más tarde', 'danger')
                
                return redirect(url_for('login'))
            
            except Exception as e:
                conn.rollback()
                flash(f'Error: {str(e)}', 'danger')
                return redirect(url_for('login'))
            
            finally:
                cursor.close()
                conn.close()
        
        flash('Error de conexión a la base de datos', 'danger')
        return redirect(url_for('login'))

@app.route('/verify_email/<token>')
def verify_email(token):
    """Verificar correo electrónico con token"""
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE verification_token = %s", (token,))
            user = cursor.fetchone()
            
            if not user:
                flash('El enlace de verificación no es válido o ha expirado', 'danger')
                return redirect(url_for('login'))
            
            if user['email_verified']:
                flash('Esta cuenta ya está verificada. Puedes iniciar sesión', 'info')
                return redirect(url_for('login'))
            
            # Marcar la cuenta como verificada
            cursor.execute(
                "UPDATE users SET email_verified = TRUE, verification_token = NULL WHERE id = %s",
                (user['id'],)
            )
            conn.commit()
            
            flash('¡Tu cuenta ha sido verificada exitosamente! Ahora puedes iniciar sesión', 'success')
            return redirect(url_for('login'))
        
        except Exception as e:
            conn.rollback()
            flash(f'Error: {str(e)}', 'danger')
            return redirect(url_for('login'))
        
        finally:
            cursor.close()
            conn.close()
    
    flash('Error de conexión a la base de datos', 'danger')
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    """Panel principal del usuario"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Obtener estadísticas del usuario
    connection = get_db_connection()
    stats = {
        'cvs_analyzed': 0,
        'jobs_found': 0
    }
    
    if connection:
        cursor = connection.cursor()
        
        # Contar CVs analizados
        cursor.execute(
            "SELECT COUNT(*) FROM resumes WHERE user_id = %s",
            (session['user_id'],)
        )
        result = cursor.fetchone()
        stats['cvs_analyzed'] = result['count'] if result else 0
        
        # Contar empleos encontrados (esto es un placeholder, ajustar según la lógica de negocio)
        cursor.execute(
            "SELECT COUNT(*) FROM jobs"
        )
        result = cursor.fetchone()
        stats['jobs_found'] = result['count'] if result else 0
        
        cursor.close()
        connection.close()
    
    return render_template('dashboard.html', stats=stats)

@app.route('/analyze_cv', methods=['GET', 'POST'])
def analyze_cv():
    """Analizador de CV con IA - Paso 1: Subir archivo (usando archivos temporales)"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    username = session.get('username', 'unknown')
    
    if request.method == 'POST':
        add_console_log('INFO', f'Usuario inició análisis de CV: {username}', 'CV')
        
        if 'file' not in request.files:
            add_console_log('WARNING', f'Análisis CV fallido - sin archivo: {username}', 'CV')
            flash('No se seleccionó ningún archivo', 'error')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            add_console_log('WARNING', f'Análisis CV fallido - archivo vacío: {username}', 'CV')
            flash('No se seleccionó ningún archivo', 'error')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            
            # Usar archivo temporal en lugar de guardarlo permanentemente
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                filepath = temp_file.name
                file.save(filepath)
                
                add_console_log('INFO', f'Archivo CV procesado temporalmente: {filename} por {username}', 'CV')
                
                # Extraer texto del archivo (pasar la extensión del archivo original)
                original_extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else None
                text_content = extract_text_from_file(filepath, original_extension)
                print(f"Texto extraído (primeros 200 caracteres): {text_content[:200] if text_content else 'None'}")
                
                # Eliminar el archivo temporal después de extraer el texto
                try:
                    os.unlink(filepath)
                except PermissionError:
                    # En Windows, a veces el archivo sigue en uso
                    # Registrar el error pero continuar con el proceso
                    add_console_log('WARNING', f'No se pudo eliminar el archivo temporal: {filepath}', 'CV')
                    pass
                
                if text_content:
                    # Guardar el contenido del CV en la sesión para el siguiente paso
                    session['cv_content'] = text_content
                    session['cv_filename'] = filename
                    
                    # Redirigir a la selección de IA
                    return redirect(url_for('select_ai_provider'))
                else:
                    add_console_log('ERROR', f'Error extrayendo texto de: {filename} por {username}', 'CV')
                    print("Error: No se pudo extraer texto del archivo")
                    flash('No se pudo extraer texto del archivo', 'error')
        else:
            add_console_log('WARNING', f'Archivo no permitido subido: {file.filename} por {username}', 'CV')
            flash('Tipo de archivo no permitido. Solo se permiten archivos PDF, DOC y DOCX.', 'error')
    
    return render_template('analyze_cv.html')

@app.route('/select_ai_provider')
def select_ai_provider():
    """Paso 2: Seleccionar proveedor de IA"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if 'cv_content' not in session:
        flash('Primero debes subir un CV', 'error')
        return redirect(url_for('analyze_cv'))
    
    return render_template('select_ai_provider.html')

@app.route('/select_analysis_type/<ai_provider>')
def select_analysis_type(ai_provider):
    """Paso 3: Seleccionar tipo de análisis"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if 'cv_content' not in session:
        flash('Primero debes subir un CV', 'error')
        return redirect(url_for('analyze_cv'))
    
    # Validar proveedor de IA
    valid_providers = ['openai', 'anthropic', 'gemini']
    if ai_provider not in valid_providers:
        flash('Proveedor de IA no válido', 'error')
        return redirect(url_for('select_ai_provider'))
    
    session['selected_ai'] = ai_provider
    
    return render_template('select_analysis_type.html', ai_provider=ai_provider)

@app.route('/perform_analysis/<analysis_type>')
def perform_analysis(analysis_type):
    """Paso 4: Realizar análisis específico"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if 'cv_content' not in session or 'selected_ai' not in session:
        flash('Sesión expirada. Reinicia el proceso', 'error')
        return redirect(url_for('analyze_cv'))
    
    username = session.get('username', 'unknown')
    cv_content = session['cv_content']
    filename = session['cv_filename']
    ai_provider = session['selected_ai']
    
    # Validar tipo de análisis
    valid_analysis_types = [
        'general_health_check',
        'content_quality_analysis', 
        'job_tailoring_optimization',
        'ats_compatibility_verification',
        'tone_style_evaluation',
        'industry_role_feedback',
        'benchmarking_comparison',
        'ai_improvement_suggestions',
        'visual_design_assessment',
        'comprehensive_score'
    ]
    
    if analysis_type not in valid_analysis_types:
        flash('Tipo de análisis no válido', 'error')
        return redirect(url_for('select_analysis_type', ai_provider=ai_provider))
    
    try:
        add_console_log('INFO', f'Iniciando análisis {analysis_type} con {ai_provider} para: {filename}', 'CV')
        
        # Realizar análisis según el proveedor y tipo seleccionado
        analysis = perform_cv_analysis(cv_content, ai_provider, analysis_type)
        
        # Guardar en la base de datos
        save_cv_analysis(session['user_id'], filename, cv_content, analysis)
        add_console_log('INFO', f'Análisis CV completado exitosamente: {filename} por {username}', 'CV')
        
        # Limpiar sesión
        session.pop('cv_content', None)
        session.pop('cv_filename', None)
        session.pop('selected_ai', None)
        
        return render_template('cv_analysis_result.html', analysis=analysis, analysis_type=analysis_type, ai_provider=ai_provider)
        
    except Exception as e:
        add_console_log('ERROR', f'Error en análisis: {str(e)}', 'CV')
        flash(f'Error durante el análisis: {str(e)}', 'error')
        return redirect(url_for('select_analysis_type', ai_provider=ai_provider))

def allowed_file(filename):
    """Verificar si el archivo tiene una extensión permitida"""
    ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_file(filepath, file_extension=None):
    """Extraer texto de archivos PDF o Word"""
    text = ""
    
    # Si no se proporciona extensión, intentar obtenerla del filepath
    if file_extension is None:
        if '.' not in filepath:
            # Si no hay extensión, intentar detectar el tipo de archivo
            try:
                with open(filepath, 'rb') as f:
                    header = f.read(8)
                    if header.startswith(b'%PDF'):
                        file_extension = 'pdf'
                    elif header.startswith(b'PK\x03\x04'):
                        file_extension = 'docx'
                    else:
                        return ""
            except:
                return ""
        else:
            file_extension = filepath.rsplit('.', 1)[1].lower()
    
    try:
        if file_extension == 'pdf':
            with open(filepath, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text()
        
        elif file_extension in ['doc', 'docx']:
            doc = Document(filepath)
            for paragraph in doc.paragraphs:
                text += paragraph.text + '\n'
    
    except Exception as e:
        print(f"Error al extraer texto: {e}")
        return None
    
    return text.strip()

def perform_cv_analysis(cv_text, ai_provider, analysis_type):
    """Realizar análisis de CV según el proveedor de IA y tipo de análisis seleccionado"""
    if ai_provider == 'openai':
        return analyze_cv_with_openai(cv_text, analysis_type)
    elif ai_provider == 'anthropic':
        return analyze_cv_with_anthropic(cv_text, analysis_type)
    elif ai_provider == 'gemini':
        return analyze_cv_with_gemini(cv_text, analysis_type)
    else:
        raise ValueError(f"Proveedor de IA no soportado: {ai_provider}")

def get_analysis_prompt(analysis_type, cv_text):
    """Obtener el prompt específico según el tipo de análisis"""
    
    analysis_prompts = {
        'general_health_check': f"""
        Realiza una revisión general exhaustiva del estado del currículum como un experto en recursos humanos con 15 años de experiencia. Evalúa minuciosamente la ortografía, gramática, formato, integridad de secciones y longitud del currículum.
        
        Proporciona un análisis EXTREMADAMENTE DETALLADO que incluya:
        1. Puntaje general (0-100) con justificación específica
        2. Lista detallada de errores de ortografía y gramática encontrados con ejemplos exactos
        3. Problemas de formato específicos con ubicaciones precisas
        4. Recomendaciones de mejora con ejemplos concretos de cómo implementarlas
        5. Análisis de estructura y organización
        6. Evaluación de la longitud y densidad de información
        7. Ejemplos específicos de mejoras con texto "antes" y "después"
        8. Comparación con estándares de la industria
        
        IMPORTANTE: Responde ÚNICAMENTE en formato JSON válido con esta estructura exacta:
        {{
            "score": número_entre_0_y_100,
            "strengths": ["fortaleza1 con ejemplo específico", "fortaleza2 con detalle", "fortaleza3 con contexto", "fortaleza4 con justificación", "fortaleza5 con evidencia"],
            "weaknesses": ["debilidad1 con ejemplo específico del CV", "debilidad2 con ubicación exacta", "debilidad3 con impacto explicado", "debilidad4 con consecuencias", "debilidad5 con contexto"],
            "recommendations": ["recomendación1 con ejemplo práctico de implementación", "recomendación2 con texto sugerido", "recomendación3 con pasos específicos", "recomendación4 con plantilla", "recomendación5 con mejores prácticas"],
            "keywords": ["palabra1", "palabra2", "palabra3", "palabra4", "palabra5", "palabra6", "palabra7", "palabra8"],
            "analysis_type": "general_health_check",
            "detailed_feedback": "Análisis exhaustivo de 500+ palabras que incluya: evaluación detallada de cada sección del CV, ejemplos específicos de errores encontrados con citas textuales, sugerencias de mejora con ejemplos concretos de texto mejorado, comparación con mejores prácticas de la industria, análisis de impacto en sistemas ATS, recomendaciones de formato específicas con justificación, evaluación de la coherencia y flujo narrativo, análisis de la efectividad comunicativa, sugerencias de reorganización si es necesario, y proyección del impacto de las mejoras sugeridas en la empleabilidad del candidato.",
            "examples": {{
                "spelling_errors": ["Error encontrado: 'texto_original' → Corrección: 'texto_corregido'"],
                "format_improvements": ["Problema: descripción del problema → Solución: ejemplo específico de mejora"],
                "before_after": ["Antes: 'texto original problemático' → Después: 'texto mejorado y optimizado'"]
            }},
            "metrics": {{
                "readability_score": número_0_100,
                "ats_compatibility": número_0_100,
                "professional_impact": número_0_100,
                "structure_quality": número_0_100
            }}
        }}
        
        CV: {cv_text}
        """,
        
        'content_quality_analysis': f"""
        Evalúa exhaustivamente verbos de acción, logros cuantificables, claridad y lenguaje profesional del currículum como un experto en comunicación corporativa y desarrollo profesional.
        
        Analiza DETALLADAMENTE:
        1. Uso de verbos de acción efectivos con análisis de impacto y alternativas
        2. Logros cuantificados con números/porcentajes y contexto de relevancia
        3. Claridad en la comunicación con ejemplos específicos de mejora
        4. Profesionalismo del lenguaje con evaluación de tono y registro
        5. Estructura narrativa y storytelling profesional
        6. Densidad informativa y eficiencia comunicativa
        7. Diferenciación competitiva en la expresión
        8. Adaptabilidad del mensaje a diferentes audiencias
        9. Coherencia estilística y consistencia terminológica
        10. Impacto emocional y persuasivo del contenido
        
        IMPORTANTE: Responde ÚNICAMENTE en formato JSON válido con esta estructura exacta:
        {{
            "score": número_entre_0_y_100,
            "strengths": ["fortaleza1 con ejemplo específico del CV", "fortaleza2 con análisis de impacto", "fortaleza3 con contexto profesional", "fortaleza4 con diferenciación", "fortaleza5 con efectividad comunicativa", "fortaleza6 con valor agregado"],
            "weaknesses": ["debilidad1 con ejemplo textual específico", "debilidad2 con impacto en percepción", "debilidad3 con oportunidad perdida", "debilidad4 con comparación de mejores prácticas", "debilidad5 con consecuencias en empleabilidad", "debilidad6 con análisis de efectividad"],
            "recommendations": ["recomendación1 con ejemplo antes/después", "recomendación2 con verbos alternativos específicos", "recomendación3 con métricas sugeridas", "recomendación4 con reformulación completa", "recomendación5 con estrategia de storytelling", "recomendación6 con optimización de impacto"],
            "keywords": ["palabra1", "palabra2", "palabra3", "palabra4", "palabra5", "palabra6", "palabra7", "palabra8", "palabra9", "palabra10"],
            "analysis_type": "content_quality_analysis",
            "detailed_feedback": "Análisis exhaustivo de 600+ palabras que incluya: evaluación detallada de cada verbo de acción utilizado con sugerencias de alternativas más impactantes, análisis específico de logros cuantificados con contexto de relevancia sectorial, evaluación de claridad comunicativa con ejemplos de reformulación, análisis de profesionalismo del lenguaje con comparación de registros, evaluación de estructura narrativa y coherencia del storytelling, análisis de densidad informativa y eficiencia del mensaje, evaluación de diferenciación competitiva en la expresión, análisis de adaptabilidad del contenido a diferentes audiencias, evaluación de consistencia terminológica y estilística, y proyección del impacto persuasivo en reclutadores y sistemas ATS.",
            "communication_analysis": {{
                "action_verbs_effectiveness": número_0_100,
                "quantified_achievements": número_0_100,
                "clarity_score": número_0_100,
                "professionalism_level": número_0_100,
                "storytelling_quality": número_0_100,
                "persuasive_impact": número_0_100
            }},
            "detailed_examples": {{
                "weak_verbs": ["Verbo débil encontrado: 'responsable de' → Alternativa impactante: 'lideró/optimizó/transformó' con contexto específico"],
                "strong_achievements": ["Logro bien cuantificado identificado con análisis de por qué es efectivo"],
                "clarity_improvements": ["Frase confusa: 'texto original' → Versión clara: 'texto mejorado' con explicación"],
                "professionalism_upgrades": ["Expresión informal: 'texto original' → Versión profesional: 'texto mejorado'"]
            }},
            "optimization_suggestions": {{
                "high_impact_verbs": ["Lista de verbos de alto impacto específicos para el perfil"],
                "quantification_opportunities": ["Oportunidades específicas de cuantificación identificadas"],
                "storytelling_improvements": ["Sugerencias específicas de mejora narrativa"]
            }}
        }}
        
        CV: {cv_text}
        """,
        
        'job_tailoring_optimization': f"""
        Analiza exhaustivamente si el currículum coincide con descripciones de trabajo específicas para una mejor inserción laboral, actuando como un especialista en reclutamiento con experiencia en múltiples industrias.
        
        Evalúa COMPREHENSIVAMENTE:
        1. Alineación estratégica con roles objetivo y análisis de fit cultural
        2. Palabras clave relevantes para la industria con análisis de densidad y posicionamiento
        3. Habilidades transferibles con mapeo de competencias cross-funcionales
        4. Sugerencias de personalización específicas por sector y nivel jerárquico
        5. Análisis de competitividad frente a perfiles similares del mercado
        6. Evaluación de gaps críticos y cómo compensarlos estratégicamente
        7. Optimización de narrativa profesional para diferentes tipos de empleadores
        8. Análisis de tendencias del mercado laboral y adaptación del perfil
        9. Estrategias de diferenciación competitiva por industria
        10. Proyección de empleabilidad y potencial de contratación por sector
        
        IMPORTANTE: Responde ÚNICAMENTE en formato JSON válido con esta estructura exacta:
        {{
            "score": número_entre_0_y_100,
            "strengths": ["fortaleza1 con análisis de mercado específico", "fortaleza2 con ventaja competitiva identificada", "fortaleza3 con alineación sectorial", "fortaleza4 con transferibilidad de skills", "fortaleza5 con diferenciación estratégica", "fortaleza6 con potencial de crecimiento"],
            "weaknesses": ["debilidad1 con impacto en empleabilidad sectorial", "debilidad2 con gap crítico identificado", "debilidad3 con desalineación de mercado", "debilidad4 con competencia desfavorable", "debilidad5 con barrera de entrada", "debilidad6 con limitación de oportunidades"],
            "recommendations": ["recomendación1 con estrategia de personalización específica", "recomendación2 con keywords sectoriales exactas", "recomendación3 con reformulación para industria target", "recomendación4 con compensación de gaps", "recomendación5 con diferenciación competitiva", "recomendación6 con optimización de narrativa"],
            "keywords": ["keyword1_industria", "keyword2_técnica", "keyword3_soft_skill", "keyword4_herramienta", "keyword5_metodología", "keyword6_certificación", "keyword7_sector", "keyword8_nivel", "keyword9_función", "keyword10_tendencia"],
            "analysis_type": "job_tailoring_optimization",
            "detailed_feedback": "Análisis exhaustivo de 650+ palabras que incluya: evaluación detallada de alineación con roles target específicos, análisis de competitividad frente a perfiles similares del mercado, mapeo de habilidades transferibles con ejemplos de aplicación sectorial, identificación de gaps críticos con estrategias de compensación, análisis de keywords sectoriales con densidad óptima y posicionamiento estratégico, evaluación de narrativa profesional con adaptaciones por tipo de empleador, análisis de tendencias del mercado laboral relevantes, estrategias de diferenciación competitiva específicas por industria, proyección de empleabilidad por sector con probabilidades de éxito, y recomendaciones de personalización con ejemplos concretos de reformulación para diferentes oportunidades laborales.",
            "market_analysis": {{
                "industry_alignment": número_0_100,
                "keyword_optimization": número_0_100,
                "skills_transferability": número_0_100,
                "competitive_positioning": número_0_100,
                "market_readiness": número_0_100,
                "growth_potential": número_0_100
            }},
            "tailoring_examples": {{
                "industry_specific_keywords": ["Keyword crítico para sector X con justificación de importancia"],
                "role_adaptations": ["Adaptación específica: 'descripción original' → 'versión optimizada para rol Y'"],
                "skills_repositioning": ["Skill reposicionado: 'presentación actual' → 'enfoque estratégico para industria Z'"],
                "narrative_adjustments": ["Ajuste narrativo: 'versión genérica' → 'versión personalizada para empleador tipo A'"]
            }},
            "competitive_analysis": {{
                "market_advantages": ["Ventaja competitiva específica con contexto de mercado"],
                "improvement_priorities": ["Prioridad de mejora con impacto proyectado en empleabilidad"],
                "differentiation_strategies": ["Estrategia de diferenciación específica con implementación práctica"]
            }}
        }}
        
        CV: {cv_text}
        """,
        
        'ats_compatibility_verification': f"""
        Verifica exhaustivamente la compatibilidad con sistemas ATS (Applicant Tracking Systems) actuando como un especialista en tecnología de reclutamiento con conocimiento profundo de múltiples plataformas ATS.
        
        Asegúrate de que el currículum pase exitosamente a través de los sistemas de seguimiento de solicitantes más utilizados en el mercado.
        
        Evalúa METICULOSAMENTE:
        1. Formato compatible con ATS con análisis de parsing y legibilidad automática
        2. Uso de palabras clave estándar con análisis de densidad y posicionamiento óptimo
        3. Estructura de secciones con evaluación de headers y jerarquía informativa
        4. Elementos que podrían causar problemas con identificación específica de conflictos
        5. Análisis de fuentes, espaciado y elementos gráficos problemáticos
        6. Evaluación de compatibilidad con diferentes versiones de ATS populares
        7. Análisis de metadata y información estructurada
        8. Verificación de campos estándar y formatos de fecha/contacto
        9. Evaluación de longitud y densidad de contenido para parsing óptimo
        10. Análisis de probabilidad de ranking alto en búsquedas automatizadas
        
        IMPORTANTE: Responde ÚNICAMENTE en formato JSON válido con esta estructura exacta:
        {{
            "score": número_entre_0_y_100,
            "strengths": ["fortaleza1 con compatibilidad específica de ATS", "fortaleza2 con ventaja en parsing automático", "fortaleza3 con optimización de keywords", "fortaleza4 con estructura favorable", "fortaleza5 con metadata correcta", "fortaleza6 con ranking potencial alto"],
            "weaknesses": ["debilidad1 con riesgo específico de parsing", "debilidad2 con elemento problemático identificado", "debilidad3 con incompatibilidad de formato", "debilidad4 con pérdida de información", "debilidad5 con ranking desfavorable", "debilidad6 con barrera técnica"],
            "recommendations": ["recomendación1 con solución técnica específica", "recomendación2 con reformateo exacto", "recomendación3 con optimización de keywords", "recomendación4 con ajuste de estructura", "recomendación5 con corrección de metadata", "recomendación6 con mejora de compatibilidad"],
            "keywords": ["keyword1_ats_friendly", "keyword2_standard", "keyword3_industry", "keyword4_technical", "keyword5_role", "keyword6_skill", "keyword7_certification", "keyword8_tool", "keyword9_methodology", "keyword10_level"],
            "analysis_type": "ats_compatibility_verification",
            "detailed_feedback": "Análisis exhaustivo de 700+ palabras que incluya: evaluación detallada de compatibilidad con sistemas ATS principales (Workday, Taleo, iCIMS, Greenhouse, etc.), análisis específico de elementos que causan problemas de parsing con ejemplos concretos, evaluación de estructura de headers y secciones con recomendaciones de optimización, análisis de densidad y posicionamiento de keywords para ranking automático, verificación de formatos de fecha, contacto y campos estándar, evaluación de fuentes y elementos gráficos problemáticos, análisis de metadata y información estructurada, proyección de probabilidad de paso exitoso por filtros automáticos, recomendaciones específicas de reformateo con ejemplos antes/después, y estrategias de optimización para diferentes tipos de ATS con consideraciones técnicas específicas.",
            "ats_analysis": {{
                "parsing_compatibility": número_0_100,
                "keyword_optimization": número_0_100,
                "structure_quality": número_0_100,
                "format_compliance": número_0_100,
                "metadata_accuracy": número_0_100,
                "ranking_potential": número_0_100
            }},
            "technical_issues": {{
                "problematic_elements": ["Elemento problemático específico: 'descripción del problema' → Solución: 'corrección técnica'"],
                "parsing_risks": ["Riesgo de parsing identificado con probabilidad de fallo y solución"],
                "format_conflicts": ["Conflicto de formato: 'problema específico' → Alternativa compatible: 'solución'"],
                "optimization_opportunities": ["Oportunidad de optimización: 'situación actual' → 'mejora sugerida con impacto'"]
            }},
            "ats_compatibility_matrix": {{
                "workday_score": número_0_100,
                "taleo_score": número_0_100,
                "icims_score": número_0_100,
                "greenhouse_score": número_0_100,
                "general_ats_score": número_0_100
            }}
        }}
        
        CV: {cv_text}
        """,
        
        'tone_style_evaluation': f"""
        Evalúa el tono profesional, la idoneidad del idioma y la legibilidad del currículum con análisis exhaustivo.
        
        Analiza en detalle:
        1. **Consistencia del tono profesional**: Evalúa uniformidad, autoridad, confianza
        2. **Apropiación del lenguaje para la industria**: Terminología técnica, jerga profesional, nivel de formalidad
        3. **Legibilidad y fluidez**: Estructura de oraciones, transiciones, claridad
        4. **Impacto y persuasión**: Poder de convencimiento, llamadas a la acción, diferenciación
        5. **Comunicación efectiva**: Concisión, precisión, engagement
        6. **Adaptación al público objetivo**: Alineación con expectativas del reclutador
        
        Proporciona ejemplos específicos de:
        - Frases que demuestran tono profesional vs. informal
        - Terminología técnica bien/mal utilizada
        - Oraciones que necesitan mejora en fluidez
        - Expresiones con alto/bajo impacto persuasivo
        
        IMPORTANTE: Responde ÚNICAMENTE en formato JSON válido con esta estructura exacta:
        {{
            "score": número_entre_0_y_100,
            "strengths": ["fortaleza1 con ejemplo específico", "fortaleza2 con ejemplo específico", "fortaleza3"],
            "weaknesses": ["debilidad1 con ejemplo específico", "debilidad2 con ejemplo específico", "debilidad3"],
            "recommendations": ["recomendación1 con ejemplo antes/después", "recomendación2 con ejemplo", "recomendación3"],
            "keywords": ["palabra_clave_profesional1", "palabra_clave_industria2", "término_técnico3"],
            "analysis_type": "tone_style_evaluation",
            "detailed_feedback": "análisis detallado de tono y estilo con ejemplos específicos",
            "tone_metrics": {{
                "professionalism_score": número_0_100,
                "industry_language_score": número_0_100,
                "readability_score": número_0_100,
                "persuasion_impact_score": número_0_100,
                "consistency_score": número_0_100
            }},
            "language_analysis": {{
                "formal_expressions": ["expresión formal 1", "expresión formal 2"],
                "informal_expressions": ["expresión informal 1", "expresión informal 2"],
                "technical_terms_used": ["término técnico 1", "término técnico 2"],
                "missing_industry_terms": ["término faltante 1", "término faltante 2"]
            }},
            "improvement_examples": {{
                "weak_phrases": [
                    {{"original": "frase débil", "improved": "frase mejorada", "reason": "razón de mejora"}},
                    {{"original": "otra frase débil", "improved": "otra frase mejorada", "reason": "razón de mejora"}}
                ],
                "tone_adjustments": [
                    {{"section": "sección del CV", "current_tone": "tono actual", "recommended_tone": "tono recomendado", "example": "ejemplo de mejora"}}
                ]
            }}
        }}
        
        CV: {cv_text}
        """,
        
        'industry_role_feedback': f"""
        Proporciona asesoramiento personalizado exhaustivo basado en la industria y rol específico identificados en el CV.
        
        Analiza en profundidad:
        1. **Relevancia para la industria específica**: Alineación con estándares, certificaciones, experiencia sectorial
        2. **Competencias clave del rol**: Skills técnicos, soft skills, competencias emergentes
        3. **Tendencias del mercado laboral**: Demanda actual, skills en crecimiento, tecnologías emergentes
        4. **Recomendaciones específicas del sector**: Certificaciones valoradas, experiencias clave, networking
        5. **Posicionamiento competitivo**: Ventajas diferenciales, gaps vs. competencia
        6. **Proyección de carrera**: Próximos pasos, roles objetivo, desarrollo profesional
        
        Identifica y proporciona ejemplos específicos de:
        - Experiencias que demuestran expertise sectorial
        - Skills técnicos específicos de la industria presentes/ausentes
        - Logros cuantificados relevantes para el sector
        - Terminología y keywords específicas de la industria
        - Certificaciones y formación valoradas en el sector
        
        IMPORTANTE: Responde ÚNICAMENTE en formato JSON válido con esta estructura exacta:
        {{
            "score": número_entre_0_y_100,
            "strengths": ["fortaleza1 con ejemplo específico del sector", "fortaleza2 con contexto industrial", "fortaleza3"],
            "weaknesses": ["debilidad1 con impacto en la industria", "debilidad2 con comparación sectorial", "debilidad3"],
            "recommendations": ["recomendación1 específica del sector con ejemplo", "recomendación2 con certificación sugerida", "recomendación3"],
            "keywords": ["keyword_industria1", "skill_técnico2", "certificación3", "herramienta4"],
            "analysis_type": "industry_role_feedback",
            "detailed_feedback": "análisis detallado específico de la industria con ejemplos y contexto sectorial",
            "industry_analysis": {{
                "identified_industry": "industria identificada",
                "target_role": "rol objetivo identificado",
                "industry_alignment_score": número_0_100,
                "role_readiness_score": número_0_100,
                "market_competitiveness_score": número_0_100
            }},
            "sector_requirements": {{
                "essential_skills": ["skill esencial 1", "skill esencial 2", "skill esencial 3"],
                "preferred_skills": ["skill preferido 1", "skill preferido 2"],
                "missing_skills": ["skill faltante 1", "skill faltante 2"],
                "relevant_certifications": ["certificación 1", "certificación 2"]
            }},
            "market_insights": {{
                "current_trends": ["tendencia 1", "tendencia 2", "tendencia 3"],
                "emerging_technologies": ["tecnología 1", "tecnología 2"],
                "salary_range": "rango salarial estimado",
                "growth_outlook": "perspectiva de crecimiento del sector"
            }},
            "career_development": {{
                "next_steps": ["paso 1 específico", "paso 2 con timeline", "paso 3"],
                "target_companies": ["tipo de empresa 1", "tipo de empresa 2"],
                "networking_opportunities": ["evento/plataforma 1", "asociación profesional 2"],
                "skill_development_priority": ["skill prioritario 1", "skill prioritario 2"]
            }}
        }}
        
        CV: {cv_text}
        """,
        
        'benchmarking_comparison': f"""
        Compara exhaustivamente el currículum con ejemplos exitosos y estándares de la industria para roles similares.
        
        Realiza análisis comparativo detallado:
        1. **Comparación con estándares de la industria**: Benchmarks sectoriales, métricas de rendimiento, niveles esperados
        2. **Identificación de brechas críticas**: Gaps en experiencia, skills, logros, formación
        3. **Mejores prácticas aplicables**: Estructuras exitosas, formatos optimizados, contenido efectivo
        4. **Posicionamiento competitivo**: Ranking vs. competencia, ventajas diferenciales, áreas de mejora
        5. **Análisis de perfiles top-tier**: Comparación con candidatos exitosos del mismo nivel
        6. **Evaluación de mercado**: Posición relativa, competitividad, oportunidades
        
        Proporciona ejemplos específicos y comparaciones concretas:
        - Logros cuantificados vs. estándares del mercado
        - Estructura y formato vs. mejores prácticas
        - Skills y certificaciones vs. perfiles exitosos
        - Experiencia y progresión vs. trayectorias típicas
        - Lenguaje y terminología vs. estándares profesionales
        
        IMPORTANTE: Responde ÚNICAMENTE en formato JSON válido con esta estructura exacta:
        {{
            "score": número_entre_0_y_100,
            "strengths": ["fortaleza1 vs. benchmark específico", "fortaleza2 con comparación cuantificada", "fortaleza3"],
            "weaknesses": ["debilidad1 vs. estándar industrial", "debilidad2 con gap específico", "debilidad3"],
            "recommendations": ["recomendación1 basada en mejores prácticas", "recomendación2 con ejemplo de mejora", "recomendación3"],
            "keywords": ["keyword_benchmark1", "término_estándar2", "skill_competitivo3"],
            "analysis_type": "benchmarking_comparison",
            "detailed_feedback": "análisis detallado de comparación y benchmarking con ejemplos específicos",
            "benchmark_analysis": {{
                "industry_percentile": número_0_100,
                "experience_level_match": "junior/mid/senior/executive",
                "competitive_position": "below_average/average/above_average/top_tier",
                "market_readiness_score": número_0_100
            }},
            "comparison_metrics": {{
                "format_vs_standard": {{
                    "current_score": número_0_100,
                    "industry_average": número_0_100,
                    "top_performers": número_0_100,
                    "gap_analysis": "descripción del gap"
                }},
                "content_vs_benchmark": {{
                    "achievements_quality": número_0_100,
                    "skills_relevance": número_0_100,
                    "experience_depth": número_0_100,
                    "industry_alignment": número_0_100
                }}
            }},
            "best_practices_analysis": {{
                "successful_patterns": ["patrón exitoso 1", "patrón exitoso 2", "patrón exitoso 3"],
                "missing_elements": ["elemento faltante 1", "elemento faltante 2"],
                "optimization_opportunities": [
                    {{"area": "área de mejora", "current_state": "estado actual", "best_practice": "mejor práctica", "expected_impact": "impacto esperado"}}
                ]
            }},
            "competitive_analysis": {{
                "strengths_vs_market": ["ventaja competitiva 1", "ventaja competitiva 2"],
                "weaknesses_vs_market": ["desventaja 1", "desventaja 2"],
                "differentiation_opportunities": ["oportunidad 1", "oportunidad 2"],
                "market_positioning": "posicionamiento en el mercado"
            }}
        }}
        
        CV: {cv_text}
        """,
        
        'ai_improvement_suggestions': f"""
        Proporciona consejos de mejora avanzados basados en IA y machine learning para optimizar el currículum de manera integral.
        
        Analiza y proporciona sugerencias inteligentes sobre:
        1. **Optimizaciones basadas en IA**: Análisis de patrones exitosos, predicciones de rendimiento, scoring automático
        2. **Sugerencias específicas de mejora**: Recomendaciones personalizadas, ajustes de contenido, optimización de formato
        3. **Tendencias actuales del mercado**: Insights de datos de reclutamiento, skills emergentes, demandas del mercado
        4. **Estrategias de diferenciación**: Elementos únicos, propuesta de valor, posicionamiento competitivo
        5. **Optimización para ATS y IA**: Compatibilidad con sistemas automatizados, keywords estratégicas
        6. **Predicciones de éxito**: Probabilidad de éxito, áreas de alto impacto, ROI de mejoras
        
        Incluye ejemplos específicos y transformaciones concretas:
        - Antes/después de secciones optimizadas
        - Keywords con mayor impacto según IA
        - Estructuras de frases más efectivas
        - Métricas y logros optimizados
        - Formatos que maximizan el engagement
        
        IMPORTANTE: Responde ÚNICAMENTE en formato JSON válido con esta estructura exacta:
        {{
            "score": número_entre_0_y_100,
            "strengths": ["fortaleza1 identificada por IA", "fortaleza2 con potencial de optimización", "fortaleza3"],
            "weaknesses": ["debilidad1 detectada por análisis automático", "debilidad2 con impacto cuantificado", "debilidad3"],
            "recommendations": ["recomendación1 basada en ML con ejemplo", "recomendación2 con predicción de impacto", "recomendación3"],
            "keywords": ["keyword_ai_optimized1", "trending_skill2", "high_impact_term3"],
            "analysis_type": "ai_improvement_suggestions",
            "detailed_feedback": "sugerencias detalladas de mejora basadas en IA con ejemplos específicos",
            "ai_insights": {{
                "optimization_score": número_0_100,
                "market_alignment_score": número_0_100,
                "ats_compatibility_prediction": número_0_100,
                "success_probability": número_0_100
            }},
            "smart_optimizations": {{
                "high_impact_changes": [
                    {{"section": "sección", "current": "contenido actual", "optimized": "contenido optimizado", "impact_score": número_0_100, "reasoning": "razón basada en IA"}}
                ],
                "keyword_optimization": [
                    {{"current_keyword": "keyword actual", "optimized_keyword": "keyword optimizado", "frequency_recommendation": "frecuencia recomendada", "context": "contexto de uso"}}
                ],
                "structure_improvements": [
                    {{"area": "área de mejora", "current_structure": "estructura actual", "recommended_structure": "estructura recomendada", "ai_reasoning": "razón basada en datos"}}
                ]
            }},
            "market_intelligence": {{
                "trending_skills": ["skill emergente 1", "skill emergente 2", "skill emergente 3"],
                "declining_skills": ["skill en declive 1", "skill en declive 2"],
                "industry_predictions": ["predicción 1", "predicción 2"],
                "salary_impact_factors": ["factor 1", "factor 2"]
            }},
            "personalization": {{
                "career_stage_optimization": "optimización específica para nivel de carrera",
                "industry_customization": "personalización para industria específica",
                "role_targeting": "enfoque para rol objetivo",
                "geographic_considerations": "consideraciones geográficas del mercado"
            }},
            "predictive_analysis": {{
                "interview_probability": número_0_100,
                "salary_negotiation_strength": número_0_100,
                "career_advancement_potential": número_0_100,
                "market_competitiveness": número_0_100
            }}
        }}
        
        CV: {cv_text}
        """,
        
        'visual_design_assessment': f"""
        Evalúa exhaustivamente el atractivo visual, la legibilidad y la presentación profesional del currículum desde una perspectiva de diseño UX/UI.
        
        Analiza en detalle:
        1. **Diseño visual y layout**: Jerarquía visual, balance, alineación, consistencia tipográfica
        2. **Legibilidad y organización**: Flujo de lectura, espaciado, contraste, accesibilidad
        3. **Uso efectivo del espacio**: Distribución, márgenes, densidad de información, respiración visual
        4. **Impresión profesional general**: Primera impresión, credibilidad visual, modernidad
        5. **Experiencia de usuario**: Facilidad de navegación, escaneabilidad, jerarquía de información
        6. **Adaptabilidad**: Compatibilidad con diferentes formatos, impresión, visualización digital
        
        Proporciona análisis específico de elementos visuales:
        - Tipografía: fuentes, tamaños, jerarquías, legibilidad
        - Color y contraste: esquema cromático, accesibilidad, profesionalismo
        - Espaciado: márgenes, padding, line-height, secciones
        - Estructura: grid, alineación, balance visual
        - Elementos gráficos: iconos, líneas, separadores, bullets
        
        IMPORTANTE: Responde ÚNICAMENTE en formato JSON válido con esta estructura exacta:
        {{
            "score": número_entre_0_y_100,
            "strengths": ["fortaleza1 de diseño específica", "fortaleza2 visual con detalle", "fortaleza3"],
            "weaknesses": ["debilidad1 de layout específica", "debilidad2 de legibilidad", "debilidad3"],
            "recommendations": ["recomendación1 de diseño con ejemplo", "recomendación2 de mejora visual", "recomendación3"],
            "keywords": ["término_diseño1", "concepto_visual2", "elemento_ux3"],
            "analysis_type": "visual_design_assessment",
            "detailed_feedback": "análisis detallado de diseño visual con ejemplos específicos",
            "design_metrics": {{
                "visual_hierarchy_score": número_0_100,
                "readability_score": número_0_100,
                "professional_appearance_score": número_0_100,
                "space_utilization_score": número_0_100,
                "consistency_score": número_0_100,
                "modern_design_score": número_0_100
            }},
            "visual_elements_analysis": {{
                "typography": {{
                    "font_choices": "evaluación de fuentes",
                    "hierarchy_effectiveness": número_0_100,
                    "readability_assessment": "evaluación de legibilidad",
                    "size_consistency": número_0_100
                }},
                "layout_structure": {{
                    "grid_system": "evaluación del sistema de grid",
                    "alignment_quality": número_0_100,
                    "balance_assessment": "evaluación del balance visual",
                    "flow_effectiveness": número_0_100
                }},
                "spacing_whitespace": {{
                    "margin_usage": "evaluación de márgenes",
                    "section_separation": número_0_100,
                    "breathing_room": "evaluación del espacio en blanco",
                    "density_optimization": número_0_100
                }}
            }},
            "ux_assessment": {{
                "scannability": número_0_100,
                "information_hierarchy": número_0_100,
                "user_journey": "evaluación del flujo de lectura",
                "accessibility_score": número_0_100
            }},
            "design_improvements": {{
                "priority_fixes": [
                    {{"issue": "problema visual", "solution": "solución específica", "impact": "impacto esperado", "difficulty": "fácil/medio/difícil"}}
                ],
                "enhancement_suggestions": [
                    {{"area": "área de mejora", "current_state": "estado actual", "recommended_change": "cambio recomendado", "visual_impact": número_0_100}}
                ],
                "modern_trends": ["tendencia de diseño 1", "tendencia de diseño 2", "tendencia de diseño 3"]
            }},
            "format_compatibility": {{
                "print_readiness": número_0_100,
                "digital_optimization": número_0_100,
                "ats_visual_compatibility": número_0_100,
                "mobile_friendliness": número_0_100
            }}
        }}
        
        CV: {cv_text}
        """,
        
        'comprehensive_score': f"""
        Proporciona una puntuación completa del currículum con desglose detallado y retroalimentación procesable.
        
        Incluye:
        1. Puntuación general detallada (0-100)
        2. Desglose por categorías (formato, contenido, ATS, etc.)
        3. Fortalezas principales identificadas
        4. Áreas de mejora prioritarias
        5. Plan de acción específico y procesable
        
        IMPORTANTE: Responde ÚNICAMENTE en formato JSON válido con esta estructura exacta:
        {{
            "score": número_entre_0_y_100,
            "strengths": ["fortaleza1", "fortaleza2", "fortaleza3"],
            "weaknesses": ["debilidad1", "debilidad2", "debilidad3"],
            "recommendations": ["recomendación1", "recomendación2", "recomendación3"],
            "keywords": ["palabra_clave1", "palabra_clave2", "palabra_clave3"],
            "analysis_type": "comprehensive_score",
            "detailed_feedback": "Análisis completo: [Puntuación general: X/100] [Formato: Y/100] [Contenido: Z/100] [Compatibilidad ATS: W/100] - Detalles específicos y plan de acción aquí"
        }}
        
        CV: {cv_text}
        """
    }
    
    return analysis_prompts.get(analysis_type, analysis_prompts['general_health_check'])

def analyze_cv_with_openai(cv_text, analysis_type):
    """Analizar CV usando OpenAI"""
    prompt = get_analysis_prompt(analysis_type, cv_text)
    
    system_prompt = """Eres un experto en recursos humanos, reclutamiento y sistemas ATS (Applicant Tracking System). 
    Tu objetivo es ayudar a los candidatos a optimizar sus currículums para maximizar sus posibilidades de pasar los filtros ATS y llegar a la entrevista.
    
    Responde SIEMPRE en formato JSON con la siguiente estructura:
    {
        "score": número (0-100),
        "strengths": ["fortaleza1", "fortaleza2", ...],
        "weaknesses": ["debilidad1", "debilidad2", ...],
        "recommendations": ["recomendación1", "recomendación2", ...],
        "keywords": ["palabra_clave1", "palabra_clave2", ...],
        "analysis_type": "tipo_de_análisis",
        "detailed_feedback": "retroalimentación detallada específica del tipo de análisis"
    }"""
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2000,
            temperature=0.7
        )
        
        analysis_text = response.choices[0].message.content
        analysis = json.loads(analysis_text)
        
        # Asegurar campos requeridos
        analysis.setdefault("keywords", [])
        analysis.setdefault("analysis_type", analysis_type)
        analysis.setdefault("ai_provider", "openai")
            
        return analysis
    
    except Exception as e:
        print(f"Error al analizar con OpenAI: {e}")
        return get_error_analysis(analysis_type, "openai", str(e))

def analyze_cv_with_anthropic(cv_text, analysis_type):
    """Analizar CV usando Anthropic Claude"""
    try:
        import anthropic
        
        # Configurar cliente de Anthropic
        client = anthropic.Anthropic(
            api_key=os.getenv('ANTHROPIC_API_KEY')
        )
        
        prompt = get_analysis_prompt(analysis_type, cv_text)
        
        system_prompt = """Eres un experto en recursos humanos, reclutamiento y sistemas ATS. 
        Responde SIEMPRE en formato JSON válido con la estructura especificada."""
        
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2000,
            temperature=0.7,
            system=system_prompt,
            messages=[
                {"role": "user", "content": prompt + "\n\nResponde en formato JSON con: score, strengths, weaknesses, recommendations, keywords, analysis_type, detailed_feedback"}
            ]
        )
        
        analysis_text = message.content[0].text
        
        # Limpiar respuesta si contiene markdown
        if "```json" in analysis_text:
            analysis_text = analysis_text.split("```json")[1].split("```")[0]
        elif "```" in analysis_text:
            analysis_text = analysis_text.split("```")[1]
        
        analysis = json.loads(analysis_text.strip())
        
        # Asegurar campos requeridos
        analysis.setdefault("keywords", [])
        analysis.setdefault("analysis_type", analysis_type)
        analysis.setdefault("ai_provider", "anthropic")
        
        return analysis
        
    except ImportError:
        return get_error_analysis(analysis_type, "anthropic", "Librería de Anthropic no instalada")
    except json.JSONDecodeError as e:
        print(f"Error de JSON en Anthropic: {e}")
        print(f"Respuesta recibida: {analysis_text if 'analysis_text' in locals() else 'No disponible'}")
        return get_error_analysis(analysis_type, "anthropic", f"Error de formato JSON: {str(e)}")
    except Exception as e:
        print(f"Error al analizar con Anthropic: {e}")
        return get_error_analysis(analysis_type, "anthropic", str(e))

def analyze_cv_with_gemini(cv_text, analysis_type):
    """Analizar CV usando Google Gemini"""
    try:
        import google.generativeai as genai
        
        # Configurar Gemini
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        model = genai.GenerativeModel('gemini-1.5-pro')
        
        prompt = get_analysis_prompt(analysis_type, cv_text)
        
        system_instruction = """Eres un experto en recursos humanos y sistemas ATS. 
        Responde SIEMPRE en formato JSON válido con la estructura especificada."""
        
        full_prompt = f"{system_instruction}\n\n{prompt}\n\nResponde en formato JSON con: score, strengths, weaknesses, recommendations, keywords, analysis_type, detailed_feedback"
        
        response = model.generate_content(full_prompt)
        analysis_text = response.text
        
        # Limpiar respuesta si contiene markdown
        if "```json" in analysis_text:
            analysis_text = analysis_text.split("```json")[1].split("```")[0]
        elif "```" in analysis_text:
            analysis_text = analysis_text.split("```")[1]
        
        analysis = json.loads(analysis_text.strip())
        
        # Asegurar campos requeridos
        analysis.setdefault("keywords", [])
        analysis.setdefault("analysis_type", analysis_type)
        analysis.setdefault("ai_provider", "gemini")
        
        return analysis
        
    except ImportError:
        return get_error_analysis(analysis_type, "gemini", "Librería de Google Generative AI no instalada")
    except json.JSONDecodeError as e:
        print(f"Error de JSON en Gemini: {e}")
        print(f"Respuesta recibida: {analysis_text if 'analysis_text' in locals() else 'No disponible'}")
        return get_error_analysis(analysis_type, "gemini", f"Error de formato JSON: {str(e)}")
    except Exception as e:
        print(f"Error al analizar con Gemini: {e}")
        return get_error_analysis(analysis_type, "gemini", str(e))

def get_error_analysis(analysis_type, ai_provider, error_message):
    """Retornar análisis de error estándar"""
    return {
        "score": 0,
        "strengths": [f"Error al procesar con {ai_provider}"],
        "weaknesses": ["No se pudo completar el análisis"],
        "recommendations": ["Intente nuevamente más tarde o use otro proveedor de IA"],
        "keywords": [],
        "analysis_type": analysis_type,
        "ai_provider": ai_provider,
        "detailed_feedback": f"Error: {error_message}",
        "error": True
    }

def analyze_cv_with_ai(cv_text):
    """Función legacy para compatibilidad - usar OpenAI por defecto"""
    return analyze_cv_with_openai(cv_text, 'general_health_check')

def save_cv_analysis(user_id, filename, content, analysis):
    """Guardar análisis de CV en S3 y referencia en la base de datos"""
    from s3_utils import save_analysis_to_s3, delete_old_analysis_for_section
    
    # Obtener información del análisis
    analysis_type = analysis.get('analysis_type', 'general_health_check')
    ai_provider = analysis.get('ai_provider', 'openai')
    
    # Eliminar análisis anterior del mismo tipo y proveedor
    delete_old_analysis_for_section(user_id, analysis_type, ai_provider)
    
    # Guardar análisis completo en S3
    s3_key = save_analysis_to_s3(user_id, analysis, analysis_type, ai_provider)
    
    connection = get_db_connection()
    if connection:
        cursor = connection.cursor()
        
        # Eliminar análisis anterior del mismo tipo y proveedor de la base de datos
        cursor.execute("""
            DELETE FROM feedback 
            WHERE resume_id IN (
                SELECT id FROM resumes WHERE user_id = %s
            ) AND analysis_type = %s AND ai_provider = %s
        """, (user_id, analysis_type, ai_provider))
        
        # Insertar un registro mínimo en resumes (sin el contenido completo)
        cursor.execute(
            "INSERT INTO resumes (user_id, filename, content) VALUES (%s, %s, %s) RETURNING id",
            (user_id, filename, "Análisis almacenado en S3 - contenido no local")
        )
        resume_id = cursor.fetchone()['id']
        
        # Insertar feedback con referencia a S3
        cursor.execute("""
            INSERT INTO feedback (resume_id, score, strengths, weaknesses, recommendations, keywords, s3_key, analysis_type, ai_provider) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            resume_id, 
            analysis['score'], 
            json.dumps(analysis['strengths']), 
            json.dumps(analysis['weaknesses']), 
            json.dumps(analysis['recommendations']),
            json.dumps(analysis['keywords']),
            s3_key,
            analysis_type,
            ai_provider
        ))
        
        connection.commit()
        cursor.close()
        connection.close()
        
        print(f"Análisis guardado - S3: {s3_key}, DB: resume_id {resume_id}")

def get_latest_cv_analysis(user_id):
    """Obtener el análisis de CV más reciente del usuario desde S3"""
    from s3_utils import get_analysis_from_s3
    
    connection = get_db_connection()
    if connection:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT f.s3_key, f.analysis_type, f.ai_provider, f.created_at
            FROM feedback f
            INNER JOIN resumes r ON f.resume_id = r.id
            WHERE r.user_id = %s AND f.s3_key IS NOT NULL
            ORDER BY f.created_at DESC
            LIMIT 1
        """, (user_id,))
        
        result = cursor.fetchone()
        cursor.close()
        connection.close()
        
        if result and result['s3_key']:
            # Recuperar análisis completo desde S3
            analysis_data = get_analysis_from_s3(result['s3_key'])
            if analysis_data:
                return analysis_data
        
        # Fallback: buscar en base de datos local (para compatibilidad)
        cursor = connection.cursor()
        cursor.execute("""
            SELECT f.score, f.strengths, f.weaknesses, f.recommendations, f.keywords, r.content
            FROM feedback f
            INNER JOIN resumes r ON f.resume_id = r.id
            WHERE r.user_id = %s
            ORDER BY f.created_at DESC
            LIMIT 1
        """, (user_id,))
        
        result = cursor.fetchone()
        cursor.close()
        connection.close()
        
        if result:
            return {
                'score': result['score'],
                'strengths': json.loads(result['strengths']) if result['strengths'] else [],
                'weaknesses': json.loads(result['weaknesses']) if result['weaknesses'] else [],
                'recommendations': json.loads(result['recommendations']) if result['recommendations'] else [],
                'keywords': json.loads(result['keywords']) if result['keywords'] else [],
                'content': result['content']
            }
    return None

def get_user_cv_analyses(user_id):
    """Obtener todos los análisis de CV de un usuario organizados por tipo y proveedor"""
    from s3_utils import get_analysis_from_s3
    
    connection = get_db_connection()
    if not connection:
        return {}
    
    cursor = connection.cursor()
    cursor.execute("""
        SELECT f.s3_key, f.analysis_type, f.ai_provider, f.created_at, f.score
        FROM feedback f
        INNER JOIN resumes r ON f.resume_id = r.id
        WHERE r.user_id = %s AND f.s3_key IS NOT NULL
        ORDER BY f.analysis_type, f.ai_provider, f.created_at DESC
    """, (user_id,))
    
    results = cursor.fetchall()
    cursor.close()
    connection.close()
    
    analyses = {}
    
    for result in results:
        analysis_type = result['analysis_type']
        ai_provider = result['ai_provider']
        
        # Crear estructura anidada si no existe
        if analysis_type not in analyses:
            analyses[analysis_type] = {}
        
        # Solo mantener el más reciente por tipo y proveedor
        if ai_provider not in analyses[analysis_type]:
            # Recuperar análisis completo desde S3
            analysis_data = get_analysis_from_s3(result['s3_key'])
            if analysis_data:
                # Aplanar la estructura para que el template pueda acceder directamente
                flattened_analysis = {
                    'score': analysis_data.get('score', 0),
                    'strengths': analysis_data.get('strengths', []),
                    'weaknesses': analysis_data.get('weaknesses', []),
                    'recommendations': analysis_data.get('recommendations', []),
                    'keywords': analysis_data.get('keywords', []),
                    'created_at': result['created_at'],
                    's3_key': result['s3_key'],
                    'analysis': analysis_data  # Mantener el análisis completo también
                }
                analyses[analysis_type][ai_provider] = flattened_analysis
    
    return analyses

def generate_smart_search_terms(cv_analysis):
    """Generar términos de búsqueda inteligentes basados en el análisis de CV usando IA"""
    try:
        # Combinar información del CV para generar términos de búsqueda
        cv_info = {
            'strengths': cv_analysis.get('strengths', []),
            'keywords': cv_analysis.get('keywords', []),
            'content_preview': cv_analysis.get('content', '')[:1000]  # Primeros 1000 caracteres
        }
        
        prompt = f"""
        Basándote en el siguiente análisis de CV, genera términos de búsqueda específicos para encontrar empleos relevantes.
        
        Fortalezas del candidato: {cv_info['strengths']}
        Palabras clave del CV: {cv_info['keywords']}
        Contenido del CV (muestra): {cv_info['content_preview']}
        
        Genera 5 términos de búsqueda específicos y relevantes que ayuden a encontrar empleos compatibles.
        Los términos deben ser:
        1. Específicos para el perfil profesional
        2. Incluir tecnologías, habilidades o roles mencionados
        3. Ser términos que realmente se usen en ofertas de trabajo
        
        Responde SOLO con una lista de términos separados por comas, sin explicaciones adicionales.
        Ejemplo: "Desarrollador Python, Analista de datos, Machine Learning, Django, SQL"
        """
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Eres un experto en reclutamiento que ayuda a generar términos de búsqueda efectivos para encontrar empleos relevantes."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=200,
            temperature=0.7
        )
        
        terms_text = response.choices[0].message.content.strip()
        search_terms = [term.strip() for term in terms_text.split(',')]
        
        # Filtrar términos vacíos y limitar a 5
        search_terms = [term for term in search_terms if term][:5]
        
        return search_terms
        
    except Exception as e:
        print(f"Error generando términos de búsqueda: {e}")
        # Fallback: usar palabras clave del CV
        keywords = cv_analysis.get('keywords', [])
        return keywords[:5] if keywords else ['desarrollador', 'analista', 'programador']

def remove_duplicate_jobs(jobs):
    """Eliminar trabajos duplicados basándose en título y empresa"""
    seen = set()
    unique_jobs = []
    
    for job in jobs:
        # Crear una clave única basada en título y empresa
        key = f"{job.get('title', '').lower().strip()}_{job.get('company', '').lower().strip()}"
        
        if key not in seen:
            seen.add(key)
            unique_jobs.append(job)
    
    return unique_jobs

def calculate_ai_job_compatibility(job, cv_analysis):
    """Calcular compatibilidad entre un trabajo y el CV usando IA con ponderación por área de experiencia"""
    try:
        # Preparar información del trabajo
        job_info = {
            'title': job.get('title', ''),
            'description': job.get('description', ''),
            'company': job.get('company', ''),
            'location': job.get('location', '')
        }
        
        # Preparar información del CV
        cv_info = {
            'strengths': cv_analysis.get('strengths', []),
            'keywords': cv_analysis.get('keywords', []),
            'score': cv_analysis.get('score', 0),
            'experience_areas': cv_analysis.get('experience_areas', []),
            'skill_level': cv_analysis.get('skill_level', 'intermedio')
        }
        
        prompt = f"""
        Analiza la compatibilidad entre este trabajo y el perfil del candidato, aplicando ponderación según área de experiencia.
        
        TRABAJO:
        Título: {job_info['title']}
        Empresa: {job_info['company']}
        Descripción: {job_info['description'][:500]}...
        
        PERFIL DEL CANDIDATO:
        Fortalezas principales: {cv_info['strengths']}
        Palabras clave del CV: {cv_info['keywords']}
        Áreas de experiencia: {cv_info['experience_areas']}
        Nivel de habilidad: {cv_info['skill_level']}
        Puntuación ATS del CV: {cv_info['score']}/100
        
        INSTRUCCIONES DE PONDERACIÓN:
        - Si el trabajo está en un área donde el candidato NO tiene experiencia: reducir compatibilidad en 20-40%
        - Si el trabajo requiere habilidades que el candidato no domina: reducir compatibilidad en 15-30%
        - Si el nivel del puesto es muy superior a la experiencia del candidato: reducir compatibilidad en 10-25%
        - Si hay coincidencia perfecta de área y habilidades: mantener o aumentar compatibilidad
        
        Calcula un porcentaje de compatibilidad del 0 al 100 considerando:
        1. Coincidencia de área de experiencia (peso: 35%)
        2. Coincidencia de habilidades técnicas (peso: 30%)
        3. Nivel del puesto vs experiencia (peso: 20%)
        4. Palabras clave coincidentes (peso: 15%)
        
        IMPORTANTE: No todos los trabajos deben tener alta compatibilidad. Sé realista con las puntuaciones.
        Responde SOLO con el número del porcentaje (ejemplo: 65)
        """
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Eres un experto en recursos humanos que evalúa la compatibilidad entre candidatos y ofertas de trabajo. Eres crítico y realista con las puntuaciones, no das puntuaciones altas a menos que haya una excelente coincidencia."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=50,
            temperature=0.2
        )
        
        compatibility_text = response.choices[0].message.content.strip()
        
        # Extraer el número del texto
        import re
        numbers = re.findall(r'\d+', compatibility_text)
        if numbers:
            compatibility = min(int(numbers[0]), 100)  # Limitar a 100
            return max(compatibility, 0)  # Asegurar que no sea negativo
        
        return 50  # Valor por defecto si no se puede extraer
        
    except Exception as e:
        print(f"Error calculando compatibilidad IA: {e}")
        # Fallback: usar método básico mejorado
        return calculate_basic_compatibility(job, cv_analysis)

def calculate_basic_compatibility(job, cv_analysis):
    """Método básico de compatibilidad sin IA como fallback con ponderación mejorada"""
    try:
        compatibility_score = 0
        
        # Texto del trabajo en minúsculas
        job_text = f"{job.get('title', '')} {job.get('description', '')}".lower()
        
        # Verificar coincidencias con fortalezas (peso mayor)
        strengths = cv_analysis.get('strengths', [])
        strength_matches = 0
        for strength in strengths:
            if isinstance(strength, str) and strength.lower() in job_text:
                strength_matches += 1
                compatibility_score += 12
        
        # Verificar coincidencias con palabras clave
        keywords = cv_analysis.get('keywords', [])
        keyword_matches = 0
        for keyword in keywords:
            if isinstance(keyword, str) and keyword.lower() in job_text:
                keyword_matches += 1
                compatibility_score += 8
        
        # Verificar áreas de experiencia
        experience_areas = cv_analysis.get('experience_areas', [])
        area_match = False
        for area in experience_areas:
            if isinstance(area, str) and area.lower() in job_text:
                area_match = True
                compatibility_score += 20
                break
        
        # Puntuación base del CV (reducida)
        base_score = cv_analysis.get('score', 50)
        compatibility_score += base_score * 0.2
        
        # Penalización si no hay coincidencias importantes
        if strength_matches == 0:
            compatibility_score *= 0.7  # Reducir 30%
        
        if not area_match and len(experience_areas) > 0:
            compatibility_score *= 0.8  # Reducir 20% si no coincide área
        
        # Asegurar que no todos los trabajos tengan alta compatibilidad
        if compatibility_score > 85:
            compatibility_score = 85  # Máximo realista para método básico
        
        # Limitar entre 15 y 85 para ser más realista
        return max(15, min(int(compatibility_score), 85))
        
    except Exception as e:
        print(f"Error en compatibilidad básica: {e}")
        return 45  # Valor más realista por defecto

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
                    'personal_info': result['personal_info'] if result['personal_info'] else {},
                    'professional_summary': result['professional_summary'] if result['professional_summary'] else '',
                    'education': result['education'] if result['education'] else [],
                    'experience': result['experience'] if result['experience'] else [],
                    'skills': result['skills'] if result['skills'] else [],
                    'languages': result['languages'] if result['languages'] else [],
                    'format_options': result['format_options'] if result['format_options'] else {}
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

@app.route('/save_cv_draft', methods=['POST'])
def save_cv_draft():
    """Guardar borrador de CV sin validación estricta"""
    if not session.get('user_id'):
        return jsonify({'error': 'No autorizado'}), 401
    
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No se recibieron datos'}), 400
    
    # Validar que las opciones de formato estén presentes
    if 'format_options' not in data:
        data['format_options'] = {'format': 'hardware', 'tech_xyz': False, 'tech_start': False}
    
    # Guardar en la base de datos sin validación estricta
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Guardar/actualizar la información del usuario como borrador
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
                json.dumps(data.get('personal_info', {})),
                data.get('professional_summary', ''),
                json.dumps(data.get('education', [])),
                json.dumps(data.get('experience', [])),
                json.dumps(data.get('skills', [])),
                json.dumps(data.get('languages', [])),
                json.dumps(data.get('format_options', {}))
            )
        )
        
        connection.commit()
        cursor.close()
        connection.close()
        
        return jsonify({
            'success': True, 
            'message': 'Borrador guardado exitosamente'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
        
        # Guardar una referencia mínima del CV (sin el HTML completo para optimizar almacenamiento)
        cursor.execute(
            "INSERT INTO resumes (user_id, filename, content) VALUES (%s, %s, %s) RETURNING id",
            (session['user_id'], data['personal_info'].get('name', 'Mi CV'), "CV creado por el usuario - datos estructurados en user_cv_data")
        )
        cv_id = cursor.fetchone()['id']
        
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
        
        cv_title = resume_result['filename']
        
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
        
        cursor.close()
        connection.close()
        
        # Reconstruir los datos del CV
        cv_data = {
            'personal_info': result['personal_info'] if result['personal_info'] else {},
            'professional_summary': result['professional_summary'] if result['professional_summary'] else '',
            'education': result['education'] if result['education'] else [],
            'experience': result['experience'] if result['experience'] else [],
            'skills': result['skills'] if result['skills'] else [],
            'languages': result['languages'] if result['languages'] else [],
            'format_options': result['format_options'] if result['format_options'] else {'format': 'hardware', 'tech_xyz': False, 'tech_start': False}
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
                    html {{
                        margin: 0;
                        padding: 0;
                    }}
                    body {{
                        max-width: 210mm;
                        margin: 0 auto;
                        padding: 20px;
                        box-shadow: 0 0 10px rgba(0,0,0,0.1);
                        background: white;
                        min-height: 100vh;
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
        # Mejorar el manejo de errores para evitar mensajes confusos
        error_message = str(e) if str(e) and str(e) != '0' else 'Error desconocido en la exportación del CV'
        
        # Log del error para debugging
        import traceback
        print(f"Error en export_cv: {error_message}")
        print(f"Tipo de excepción: {type(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        
        return jsonify({'error': f'Error al obtener CV: {error_message}'}), 500

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
        jobs.extend(scrape_computrabajo_service(query, location))
    
    if source == 'all' or source == 'indeed':
        jobs.extend(scrape_indeed_api(query, location))
    
    if source == 'all' or source == 'linkedin':
        jobs.extend(scrape_linkedin(query, location))
    
    # Eliminar duplicados
    unique_jobs = remove_duplicate_jobs(jobs)
    
    # Obtener análisis de CV para calcular compatibilidad
    cv_analysis = get_latest_cv_analysis(session['user_id'])
    
    # Calcular compatibilidad con IA si hay análisis de CV
    if cv_analysis and unique_jobs:
        for job in unique_jobs:
            compatibility = calculate_ai_job_compatibility(job, cv_analysis)
            job['compatibility_score'] = compatibility
        
        # Ordenar por compatibilidad (mayor a menor)
        unique_jobs.sort(key=lambda x: x.get('compatibility_score', 0), reverse=True)
    
    # Guardar empleos en la base de datos
    save_jobs_to_db(unique_jobs)
    
    return jsonify({
        'jobs': unique_jobs,
        'total_found': len(unique_jobs),
        'has_ai_scoring': bool(cv_analysis)
    })

@app.route('/ai_job_search', methods=['POST'])
def ai_job_search():
    """Búsqueda inteligente de empleos con IA basada en el CV del usuario"""
    if 'user_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    
    try:
        # Obtener el análisis de CV más reciente del usuario
        cv_analysis = get_latest_cv_analysis(session['user_id'])
        
        if not cv_analysis:
            return jsonify({
                'error': 'No se encontró un análisis de CV. Por favor, sube y analiza tu CV primero.'
            }), 400
        
        # Generar términos de búsqueda inteligentes basados en el CV
        search_terms = generate_smart_search_terms(cv_analysis)
        
        # Buscar empleos en múltiples portales
        all_jobs = []
        
        for term in search_terms[:3]:  # Usar los 3 términos más relevantes
            # Buscar en LinkedIn
            linkedin_jobs = scrape_linkedin(term, "")
            all_jobs.extend(linkedin_jobs)
            
            # Buscar en CompuTrabajo
            computrabajo_jobs = scrape_computrabajo_service(term, "")
            all_jobs.extend(computrabajo_jobs)
            
            # Buscar en Indeed
            indeed_jobs = scrape_indeed_api(term, "")
            all_jobs.extend(indeed_jobs)
        
        # Eliminar duplicados
        unique_jobs = remove_duplicate_jobs(all_jobs)
        
        # Calcular compatibilidad con IA para cada trabajo
        jobs_with_compatibility = []
        for job in unique_jobs:
            compatibility = calculate_ai_job_compatibility(job, cv_analysis)
            job['compatibility_score'] = compatibility
            jobs_with_compatibility.append(job)
        
        # Ordenar por compatibilidad (mayor a menor)
        jobs_with_compatibility.sort(key=lambda x: x['compatibility_score'], reverse=True)
        
        # Tomar los mejores 100 empleos
        top_jobs = jobs_with_compatibility[:100]
        
        # Guardar en base de datos
        if top_jobs:
            save_jobs_to_db(top_jobs)
        
        return jsonify({
            'jobs': top_jobs,
            'total_found': len(unique_jobs),
            'search_terms_used': search_terms[:3]
        })
        
    except Exception as e:
        print(f"Error en búsqueda IA: {e}")
        return jsonify({'error': f'Error interno del servidor: {str(e)}'}), 500

@app.route('/my_analyses')
def my_analyses():
    """Ver análisis previos del usuario organizados por tipo y proveedor de IA"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Obtener análisis organizados desde S3
    user_analyses = get_user_cv_analyses(session['user_id'])
    
    # Fallback: obtener análisis legacy de la base de datos
    connection = get_db_connection()
    legacy_analyses = []
    
    if connection:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT f.id, r.filename, r.created_at, f.score, f.strengths, f.weaknesses, f.recommendations, f.keywords, f.analysis_type, f.ai_provider
            FROM resumes r
            INNER JOIN feedback f ON r.id = f.resume_id
            WHERE r.user_id = %s AND f.s3_key IS NULL
            ORDER BY r.created_at DESC
        """, (session['user_id'],))
        
        results = cursor.fetchall()
        for result in results:
            analysis = {
                'id': result['id'],
                'filename': result['filename'],
                'created_at': result['created_at'],
                'score': result['score'] if result['score'] else 0,
                'strengths': json.loads(result['strengths']) if result['strengths'] else [],
                'weaknesses': json.loads(result['weaknesses']) if result['weaknesses'] else [],
                'recommendations': json.loads(result['recommendations']) if result['recommendations'] else [],
                'keywords': json.loads(result['keywords']) if result['keywords'] else [],
                'analysis_type': result['analysis_type'] or 'general_health_check',
                'ai_provider': result['ai_provider'] or 'openai'
            }
            legacy_analyses.append(analysis)
        
        cursor.close()
        connection.close()
    
    # Definir nombres amigables para tipos de análisis
    analysis_type_names = {
        'general_health_check': 'Revisión General',
        'content_quality_analysis': 'Análisis de Calidad',
        'job_tailoring_optimization': 'Optimización para Empleos',
        'ats_compatibility_verification': 'Compatibilidad ATS',
        'tone_style_evaluation': 'Evaluación de Tono y Estilo',
        'industry_role_feedback': 'Feedback por Industria',
        'benchmarking_comparison': 'Comparación Benchmarking',
        'ai_improvement_suggestions': 'Sugerencias de IA',
        'visual_design_assessment': 'Evaluación de Diseño',
        'comprehensive_score': 'Puntuación Integral'
    }
    
    # Nombres amigables para proveedores de IA
    ai_provider_names = {
        'openai': 'OpenAI GPT',
        'anthropic': 'Anthropic Claude',
        'gemini': 'Google Gemini'
    }
    
    # Calcular el número total de análisis en S3
    s3_analyses_count = sum(len(providers) for providers in user_analyses.values())
    
    # Crear una lista plana de todos los análisis para JavaScript
    all_analyses = []
    
    # Agregar análisis de S3 (convertir estructura anidada a lista plana)
    for analysis_type, providers in user_analyses.items():
        for ai_provider, analysis_data in providers.items():
            all_analyses.append({
                'id': f"s3_{analysis_type}_{ai_provider}",
                'filename': f"Análisis {analysis_type_names.get(analysis_type, analysis_type)}",
                'created_at': analysis_data['created_at'],
                'score': analysis_data.get('score', 0),
                'strengths': analysis_data.get('strengths', []),
                'weaknesses': analysis_data.get('weaknesses', []),
                'recommendations': analysis_data.get('recommendations', []),
                'keywords': analysis_data.get('keywords', []),
                'analysis_type': analysis_type,
                'ai_provider': ai_provider,
                'source': 's3'
            })
    
    # Agregar análisis legacy
    all_analyses.extend(legacy_analyses)
    
    # Calcular puntuación promedio
    scores = []
    for analysis in all_analyses:
        score = analysis.get('score', 0)
        if score and score != 0:
            scores.append(score)
    
    avg_score = sum(scores) / len(scores) if scores else 0
    
    return render_template('my_analyses.html', 
                         s3_analyses=user_analyses,
                         legacy_analyses=legacy_analyses,
                         analyses=all_analyses,
                         type_names=analysis_type_names,
                         provider_names=ai_provider_names,
                         s3_analyses_count=s3_analyses_count,
                         avg_score=avg_score)

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
            if xyz_enhancements and start_enhancements:
                enhanced_summary += f" {xyz_enhancements[0]} y {start_enhancements[0]}."
        elif use_xyz:
            # Solo metodología XYZ
            if xyz_enhancements:
                enhanced_summary += f" {xyz_enhancements[0]}."
        elif use_start:
            # Solo metodología Start
            if start_enhancements:
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
            if xyz_phrases and start_phrases:
                enhanced_description += f" Destacando por {xyz_phrases[0]} y {start_phrases[0]}."
        elif use_xyz:
            # Solo metodología XYZ
            if xyz_phrases:
                enhanced_description += f" Destacando por {xyz_phrases[0]}."
        elif use_start:
            # Solo metodología Start
            if start_phrases:
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
            # Formato ATS: habilidades con estilos individuales
            html += '<div class="skills-list">'
            for skill in skills:
                skill_class = "skill"
                if any(keyword.lower() in skill.lower() for keyword in xyz_keywords):
                    skill_class = "skill skill-xyz"
                elif any(keyword.lower() in skill.lower() for keyword in start_keywords):
                    skill_class = "skill skill-start"
                html += f'<span class="{skill_class}">{skill}</span>'
            html += '</div>'
        else:
            # Formato Hardware: habilidades con estilos individuales
            html += '<div class="skills-list">'
            for skill in skills:
                skill_class = "skill"
                if any(keyword.lower() in skill.lower() for keyword in xyz_keywords):
                    skill_class = "skill skill-xyz"
                elif any(keyword.lower() in skill.lower() for keyword in start_keywords):
                    skill_class = "skill skill-start"
                html += f'<span class="{skill_class}">{skill}</span>'
            html += '</div>'
    
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
        analyses_count = cursor.fetchone()['count']
        
        cursor.execute(
            "SELECT created_at FROM resumes WHERE user_id = %s ORDER BY created_at DESC LIMIT 1",
            (session['user_id'],)
        )
        result = cursor.fetchone()
        last_analysis = result['created_at'] if result else None
        
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
            if xyz_enhancements and start_enhancements:
                enhanced_summary += f" {xyz_enhancements[0]} y {start_enhancements[0]}."
        elif use_xyz:
            # Solo metodología XYZ
            if xyz_enhancements:
                enhanced_summary += f" {xyz_enhancements[0]}."
        elif use_start:
            # Solo metodología Start
            if start_enhancements:
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
            if xyz_phrases and start_phrases:
                enhanced_description += f" Destacando por {xyz_phrases[0]} y {start_phrases[0]}."
        elif use_xyz:
            # Solo metodología XYZ
            if xyz_phrases:
                enhanced_description += f" Destacando por {xyz_phrases[0]}."
        elif use_start:
            # Solo metodología Start
            if start_phrases:
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
            # Formato ATS: habilidades con estilos individuales
            html += '<div class="skills-list">'
            for skill in skills:
                skill_class = "skill"
                if any(keyword.lower() in skill.lower() for keyword in xyz_keywords):
                    skill_class = "skill skill-xyz"
                elif any(keyword.lower() in skill.lower() for keyword in start_keywords):
                    skill_class = "skill skill-start"
                html += f'<span class="{skill_class}">{skill}</span>'
            html += '</div>'
        else:
            # Formato Hardware: habilidades con estilos individuales
            html += '<div class="skills-list">'
            for skill in skills:
                skill_class = "skill"
                if any(keyword.lower() in skill.lower() for keyword in xyz_keywords):
                    skill_class = "skill skill-xyz"
                elif any(keyword.lower() in skill.lower() for keyword in start_keywords):
                    skill_class = "skill skill-start"
                html += f'<span class="{skill_class}">{skill}</span>'
            html += '</div>'
    
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

# ==================== RUTAS DE ADMINISTRACIÓN ====================

def admin_required(f):
    """Decorador para verificar que el usuario sea administrador"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Debes iniciar sesión para acceder a esta página', 'error')
            return redirect(url_for('login'))
        if session.get('user_role') != 'admin':
            flash('No tienes permisos para acceder a esta página', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin')
@admin_required
def admin_dashboard():
    """Panel principal de administración"""
    username = session.get('username', 'unknown')
    add_console_log('INFO', f'Admin accedió al panel principal: {username}', 'ADMIN')
    return render_template('admin/dashboard.html')

@app.route('/admin/console')
@admin_required
def admin_console():
    """Consola en tiempo real del servidor"""
    username = session.get('username', 'unknown')
    add_console_log('INFO', f'Admin accedió a la consola del servidor: {username}', 'ADMIN')
    return render_template('admin/console.html')

@app.route('/admin/stats')
@admin_required
def admin_stats():
    """Estadísticas de usuarios"""
    username = session.get('username', 'unknown')
    add_console_log('INFO', f'Admin accedió a estadísticas: {username}', 'ADMIN')
    
    connection = get_db_connection()
    if not connection:
        flash('Error de conexión a la base de datos', 'error')
        return redirect(url_for('admin_dashboard'))
    
    try:
        cursor = connection.cursor()
        
        # Usuarios en tiempo real (últimos 5 minutos)
        cursor.execute("""
            SELECT COUNT(*) as active_users 
            FROM users 
            WHERE last_login >= NOW() - INTERVAL '5 minutes'
        """)
        active_users = cursor.fetchone()['active_users']
        
        # Usuarios conectados hoy
        cursor.execute("""
            SELECT COUNT(*) as daily_users 
            FROM users 
            WHERE DATE(last_login) = CURRENT_DATE
        """)
        daily_users = cursor.fetchone()['daily_users']
        
        # Usuarios conectados esta semana
        cursor.execute("""
            SELECT COUNT(*) as weekly_users 
            FROM users 
            WHERE last_login >= DATE_TRUNC('week', NOW())
        """)
        weekly_users = cursor.fetchone()['weekly_users']
        
        # Usuarios conectados este mes
        cursor.execute("""
            SELECT COUNT(*) as monthly_users 
            FROM users 
            WHERE last_login >= DATE_TRUNC('month', NOW())
        """)
        monthly_users = cursor.fetchone()['monthly_users']
        
        # Total de usuarios registrados
        cursor.execute("SELECT COUNT(*) as total_users FROM users")
        total_users = cursor.fetchone()['total_users']
        
        cursor.close()
        connection.close()
        
        stats = {
            'active_users': active_users,
            'daily_users': daily_users,
            'weekly_users': weekly_users,
            'monthly_users': monthly_users,
            'total_users': total_users
        }
        
        return render_template('admin/stats.html', stats=stats)
        
    except Exception as e:
        print(f"Error obteniendo estadísticas: {e}")
        flash('Error obteniendo estadísticas', 'error')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/database')
@admin_required
def admin_database():
    """Interfaz de consultas a la base de datos"""
    return render_template('admin/database.html')

@app.route('/admin/search_users', methods=['POST'])
@admin_required
def admin_search_users():
    """Buscar usuarios por título profesional"""
    search_term = request.form.get('search_query', '').strip()
    
    if not search_term:
        flash('Por favor, introduce un término de búsqueda', 'warning')
        return redirect(url_for('admin_database'))
    
    connection = get_db_connection()
    if not connection:
        flash('Error de conexión a la base de datos', 'error')
        return redirect(url_for('admin_database'))
    
    try:
        cursor = connection.cursor()
        
        # Buscar en los datos de CV de usuarios
        cursor.execute("""
            SELECT u.id, u.username, u.email, u.created_at, u.last_login,
                   cv.personal_info, cv.professional_summary, cv.education, 
                   cv.experience, cv.skills
            FROM users u
            LEFT JOIN user_cv_data cv ON u.id = cv.user_id
            WHERE cv.personal_info ILIKE %s 
               OR cv.professional_summary ILIKE %s
               OR cv.education ILIKE %s
               OR cv.experience ILIKE %s
               OR cv.skills ILIKE %s
        """, (f'%{search_term}%', f'%{search_term}%', f'%{search_term}%', f'%{search_term}%', f'%{search_term}%'))
        
        results = cursor.fetchall()
        cursor.close()
        connection.close()
        
        return render_template('admin/search_results.html', results=results, search_term=search_term)
        
    except Exception as e:
        print(f"Error en búsqueda de usuarios: {e}")
        flash('Error realizando la búsqueda', 'error')
        return redirect(url_for('admin_database'))

@app.route('/admin/export_users', methods=['POST'])
@admin_required
def admin_export_users():
    """Exportar usuarios a Excel"""
    search_term = request.form.get('search_query', '')
    
    connection = get_db_connection()
    if not connection:
        flash('Error de conexión a la base de datos', 'error')
        return redirect(url_for('admin_database'))
    
    try:
        import pandas as pd
        from io import BytesIO
        
        cursor = connection.cursor()
        
        if search_term:
            cursor.execute("""
                SELECT u.id, u.username, u.email, u.created_at, u.last_login,
                       cv.personal_info, cv.professional_summary, cv.education, 
                       cv.experience, cv.skills
                FROM users u
                LEFT JOIN user_cv_data cv ON u.id = cv.user_id
                WHERE cv.personal_info ILIKE %s 
                   OR cv.professional_summary ILIKE %s
                   OR cv.education ILIKE %s
                   OR cv.experience ILIKE %s
                   OR cv.skills ILIKE %s
            """, (f'%{search_term}%', f'%{search_term}%', f'%{search_term}%', f'%{search_term}%', f'%{search_term}%'))
        else:
            cursor.execute("""
                SELECT u.id, u.username, u.email, u.created_at, u.last_login,
                       cv.personal_info, cv.professional_summary, cv.education, 
                       cv.experience, cv.skills
                FROM users u
                LEFT JOIN user_cv_data cv ON u.id = cv.user_id
            """)
        
        results = cursor.fetchall()
        cursor.close()
        connection.close()
        
        # Crear DataFrame
        df = pd.DataFrame(results, columns=['ID', 'Usuario', 'Email', 'Fecha Registro', 'Último Login', 
                                          'Info Personal', 'Resumen Profesional', 'Educación', 'Experiencia', 'Habilidades'])
        
        # Crear archivo Excel en memoria
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Usuarios', index=False)
        
        output.seek(0)
        
        filename = f"usuarios_{search_term}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx" if search_term else f"todos_usuarios_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
        
    except ImportError:
        flash('pandas no está instalado. No se puede exportar a Excel.', 'error')
        return redirect(url_for('admin_database'))
    except Exception as e:
        print(f"Error exportando usuarios: {e}")
        flash('Error exportando usuarios', 'error')
        return redirect(url_for('admin_database'))

@app.route('/admin/users')
@admin_required
def admin_users():
    """Gestión de usuarios"""
    search = request.args.get('search', '')
    page = int(request.args.get('page', 1))
    per_page = 20
    
    connection = get_db_connection()
    if not connection:
        flash('Error de conexión a la base de datos', 'error')
        return redirect(url_for('admin_dashboard'))
    
    try:
        cursor = connection.cursor()
        
        # Construir consulta con búsqueda
        base_query = """
            SELECT id, username, email, role, is_banned, ban_until, ban_reason, 
                   last_login, created_at, email_verified
            FROM users
        """
        
        if search:
            base_query += " WHERE username ILIKE %s OR email ILIKE %s"
            search_param = f"%{search}%"
            cursor.execute(base_query + " ORDER BY created_at DESC LIMIT %s OFFSET %s", 
                         (search_param, search_param, per_page, (page-1)*per_page))
        else:
            cursor.execute(base_query + " ORDER BY created_at DESC LIMIT %s OFFSET %s", 
                         (per_page, (page-1)*per_page))
        
        users = cursor.fetchall()
        
        # Contar total para paginación
        if search:
            cursor.execute("SELECT COUNT(*) FROM users WHERE username ILIKE %s OR email ILIKE %s", 
                         (search_param, search_param))
        else:
            cursor.execute("SELECT COUNT(*) FROM users")
        
        total_users = cursor.fetchone()['count']
        total_pages = (total_users + per_page - 1) // per_page
        
        cursor.close()
        connection.close()
        
        return render_template('admin/users.html', 
                             users=users, 
                             search=search, 
                             page=page, 
                             total_pages=total_pages)
        
    except Exception as e:
        print(f"Error obteniendo usuarios: {e}")
        flash('Error obteniendo usuarios', 'error')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/ban_user', methods=['POST'])
@admin_required
def admin_ban_user():
    """Banear usuario"""
    data = request.get_json()
    user_id = data.get('user_id')
    ban_type = data.get('ban_type')  # 'permanent' o 'temporary'
    ban_duration = data.get('ban_duration')  # en días para bans temporales
    ban_reason = data.get('ban_reason', '')
    
    if not user_id:
        return jsonify({'success': False, 'message': 'ID de usuario requerido'})
    
    connection = get_db_connection()
    if not connection:
        return jsonify({'success': False, 'message': 'Error de conexión a la base de datos'})
    
    try:
        cursor = connection.cursor()
        
        if ban_type == 'permanent':
            cursor.execute("""
                UPDATE users 
                SET is_banned = TRUE, ban_until = NULL, ban_reason = %s
                WHERE id = %s
            """, (ban_reason, user_id))
        else:  # temporary
            from datetime import datetime, timedelta
            ban_until = datetime.now() + timedelta(days=int(ban_duration))
            cursor.execute("""
                UPDATE users 
                SET is_banned = TRUE, ban_until = %s, ban_reason = %s
                WHERE id = %s
            """, (ban_until, ban_reason, user_id))
        
        connection.commit()
        cursor.close()
        connection.close()
        
        return jsonify({'success': True, 'message': 'Usuario baneado correctamente'})
        
    except Exception as e:
        print(f"Error baneando usuario: {e}")
        return jsonify({'success': False, 'message': 'Error interno del servidor'})

@app.route('/admin/unban_user', methods=['POST'])
@admin_required
def admin_unban_user():
    """Desbanear usuario"""
    data = request.get_json()
    user_id = data.get('user_id')
    
    if not user_id:
        return jsonify({'success': False, 'message': 'ID de usuario requerido'})
    
    connection = get_db_connection()
    if not connection:
        return jsonify({'success': False, 'message': 'Error de conexión a la base de datos'})
    
    try:
        cursor = connection.cursor()
        
        cursor.execute("""
            UPDATE users 
            SET is_banned = FALSE, ban_until = NULL, ban_reason = NULL
            WHERE id = %s
        """, (user_id,))
        
        connection.commit()
        cursor.close()
        connection.close()
        
        return jsonify({'success': True, 'message': 'Usuario desbaneado correctamente'})
        
    except Exception as e:
        print(f"Error desbaneando usuario: {e}")
        return jsonify({'success': False, 'message': 'Error interno del servidor'})

@app.route('/admin/delete_user', methods=['POST'])
@admin_required
def admin_delete_user():
    """Eliminar usuario"""
    data = request.get_json()
    user_id = data.get('user_id')
    
    if not user_id:
        return jsonify({'success': False, 'message': 'ID de usuario requerido'})
    
    # Prevenir que el admin se elimine a sí mismo
    if int(user_id) == session['user_id']:
        return jsonify({'success': False, 'message': 'No puedes eliminar tu propia cuenta'})
    
    connection = get_db_connection()
    if not connection:
        return jsonify({'success': False, 'message': 'Error de conexión a la base de datos'})
    
    try:
        cursor = connection.cursor()
        
        # Eliminar usuario (las relaciones se eliminan en cascada)
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        
        connection.commit()
        cursor.close()
        connection.close()
        
        return jsonify({'success': True, 'message': 'Usuario eliminado correctamente'})
        
    except Exception as e:
        print(f"Error eliminando usuario: {e}")
        return jsonify({'success': False, 'message': 'Error interno del servidor'})

# Sistema de logs global para la consola de administrador
import logging
from collections import deque
from datetime import datetime
import threading

# Cola de logs para la consola (máximo 1000 entradas)
console_logs = deque(maxlen=1000)
logs_lock = threading.Lock()

def add_console_log(level, message, source='SYSTEM'):
    """Agregar un log a la consola de administrador"""
    with logs_lock:
        log_entry = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'level': level,
            'source': source,
            'message': str(message)
        }
        console_logs.append(log_entry)

# Configurar logging personalizado
class ConsoleLogHandler(logging.Handler):
    def emit(self, record):
        try:
            msg = self.format(record)
            level = record.levelname
            add_console_log(level, msg, 'APP')
        except Exception:
            pass

# Configurar el handler personalizado
console_handler = ConsoleLogHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(name)s - %(message)s')
console_handler.setFormatter(formatter)

# Agregar el handler al logger de Flask
app.logger.addHandler(console_handler)
app.logger.setLevel(logging.INFO)

# Manejador de errores global para capturar errores sin que sean fatales
@app.errorhandler(Exception)
def handle_exception(e):
    """Manejador global de excepciones para evitar errores fatales"""
    import traceback
    
    # Log del error en la consola de administrador
    error_msg = f"Error en {request.endpoint or 'unknown'}: {str(e)}"
    add_console_log('ERROR', error_msg, 'APP')
    
    # Log detallado para debugging
    app.logger.error(f"Excepción no manejada: {str(e)}")
    app.logger.error(f"Traceback: {traceback.format_exc()}")
    
    # Si es una petición AJAX, devolver JSON
    if request.is_json or 'application/json' in request.headers.get('Accept', ''):
        return jsonify({
            'success': False,
            'error': 'Error interno del servidor',
            'message': str(e) if app.debug else 'Ha ocurrido un error inesperado'
        }), 500
    
    # Para peticiones normales, mostrar página de error
    flash(f'Ha ocurrido un error: {str(e)}', 'error')
    return redirect(request.referrer or url_for('index'))

# Manejador específico para errores 404
@app.errorhandler(404)
def not_found_error(error):
    add_console_log('WARNING', f'Página no encontrada: {request.url}', 'APP')
    flash('Página no encontrada', 'error')
    return redirect(url_for('index'))

# Manejador específico para errores 500
@app.errorhandler(500)
def internal_error(error):
    add_console_log('ERROR', f'Error interno del servidor: {str(error)}', 'APP')
    flash('Error interno del servidor', 'error')
    return redirect(url_for('index'))

@app.route('/admin/console_logs')
@admin_required
def admin_console_logs():
    """API para obtener logs del servidor en tiempo real"""
    try:
        import psutil
        current_time = datetime.now()
        
        # Información del sistema en tiempo real
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Agregar logs de sistema si no hay logs recientes
            if not console_logs or (current_time - datetime.strptime(console_logs[-1]['timestamp'], '%Y-%m-%d %H:%M:%S')).seconds > 5:
                add_console_log('INFO', f'Sistema - CPU: {cpu_percent:.1f}%, RAM: {memory.percent:.1f}%, Disco: {disk.percent:.1f}%', 'SYSTEM')
        except Exception as e:
            add_console_log('WARNING', f'Error obteniendo métricas del sistema: {str(e)}', 'SYSTEM')
        
        # Logs de actividad de base de datos
        try:
            conn = get_db_connection()
            if conn:
                cursor = conn.cursor()
            
                # Contar usuarios activos (últimos 5 minutos)
                cursor.execute("""
                    SELECT COUNT(*) as active_count FROM users 
                    WHERE last_login >= NOW() - INTERVAL '5 minutes'
                """)
                result = cursor.fetchone()
                active_users = result['active_count'] if result else 0
                
                # Últimos logins
                cursor.execute("""
                    SELECT email, last_login 
                    FROM users 
                    WHERE last_login IS NOT NULL 
                    ORDER BY last_login DESC 
                    LIMIT 5
                """)
                recent_logins = cursor.fetchall()
                
                add_console_log('INFO', f'Base de datos conectada - {active_users} usuarios activos', 'DATABASE')
                
                for login in recent_logins:
                    if login['last_login']:
                        add_console_log('INFO', f'Login de usuario: {login["email"]}', 'AUTH')
                
                cursor.close()
                conn.close()
                
        except Exception as db_error:
            add_console_log('ERROR', f'Error de base de datos: {str(db_error)}', 'DATABASE')
        
        # Logs de advertencias del sistema
        try:
            if 'memory' in locals() and memory.percent > 80:
                add_console_log('WARNING', f'Uso alto de memoria detectado: {memory.percent:.1f}%', 'SYSTEM')
            
            if 'cpu_percent' in locals() and cpu_percent > 80:
                add_console_log('WARNING', f'Uso alto de CPU detectado: {cpu_percent:.1f}%', 'SYSTEM')
        except Exception:
            pass
        
        # Convertir deque a lista para JSON
        with logs_lock:
            logs_list = list(console_logs)
        
        return jsonify({
            'success': True,
            'logs': logs_list[-50:],  # Últimos 50 logs
            'timestamp': current_time.strftime('%Y-%m-%d %H:%M:%S')
        })
        
    except Exception as e:
        add_console_log('ERROR', f'Error en consola de administrador: {str(e)}', 'ADMIN')
        return jsonify({
             'success': False,
             'error': str(e),
             'logs': []
         })

@app.route('/admin/check_s3')
def check_s3_connection():
    """Check S3 connection and create bucket if needed"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Check if user is admin
    connection = get_db_connection()
    if connection:
        cursor = connection.cursor()
        cursor.execute("SELECT role FROM users WHERE id = %s", (session['user_id'],))
        user = cursor.fetchone()
        cursor.close()
        connection.close()
        
        if not user or user['role'] != 'admin':
            return jsonify({'success': False, 'error': 'Access denied'})
    else:
        return jsonify({'success': False, 'error': 'Database connection failed'})
    
    try:
        from s3_utils import check_s3_connection, create_bucket_if_not_exists
        
        # Check S3 connection
        connection_result = check_s3_connection()
        if not connection_result['success']:
            return jsonify({
                'success': False,
                'error': f"S3 connection failed: {connection_result['error']}"
            })
        
        # Create bucket if it doesn't exist
        bucket_result = create_bucket_if_not_exists()
        if not bucket_result['success']:
            return jsonify({
                'success': False,
                'error': f"Failed to create S3 bucket: {bucket_result['error']}"
            })
        
        return jsonify({
            'success': True,
            'message': 'S3 connection successful and bucket is ready',
            'bucket_name': bucket_result.get('bucket_name', 'Unknown')
        })
        
    except ImportError:
        return jsonify({
            'success': False,
            'error': 'S3 utilities not available. Please check s3_utils.py'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Unexpected error: {str(e)}'
        })

if __name__ == '__main__':
    init_database()
    app.run(debug=True)