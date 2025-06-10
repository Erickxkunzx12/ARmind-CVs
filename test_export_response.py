import psycopg2
from database_config import DB_CONFIG
import json
import traceback
from flask import Flask, session, jsonify, Response

# Crear una aplicación Flask temporal para probar
app = Flask(__name__)
app.secret_key = 'test_key'

def get_db_connection():
    """Función para obtener conexión a la base de datos"""
    return psycopg2.connect(**DB_CONFIG)

def generate_professional_summary_section(summary, tech_xyz=False, tech_start=False):
    """Función auxiliar para generar la sección de resumen profesional"""
    if not summary:
        return ""
    
    enhanced_summary = summary
    
    if tech_xyz:
        xyz_phrases = [
            "con enfoque en tecnologías emergentes",
            "aplicando metodologías XYZ innovadoras",
            "orientado a la transformación digital",
            "con visión de futuro tecnológico"
        ]
        enhanced_summary += f" {xyz_phrases[0]}"
    
    if tech_start:
        start_phrases = [
            "con sólidos fundamentos técnicos",
            "enfocado en el crecimiento profesional continuo",
            "con base sólida en principios fundamentales",
            "orientado al desarrollo de competencias clave"
        ]
        enhanced_summary += f" {start_phrases[0]}"
    
    return f'<div class="section"><h3>Resumen Profesional</h3><p>{enhanced_summary}</p></div>'

def enhance_experience_description(description, tech_xyz=False, tech_start=False):
    """Función auxiliar para mejorar la descripción de experiencia"""
    if not description:
        return description
    
    enhanced_desc = description
    
    if tech_xyz:
        xyz_enhancements = [
            "implementando soluciones innovadoras",
            "aplicando tecnologías de vanguardia",
            "desarrollando estrategias disruptivas",
            "liderando iniciativas de transformación"
        ]
        enhanced_desc += f" {xyz_enhancements[0]}"
    
    if tech_start:
        start_enhancements = [
            "consolidando bases técnicas sólidas",
            "fortaleciendo competencias fundamentales",
            "desarrollando habilidades core",
            "estableciendo fundamentos profesionales"
        ]
        enhanced_desc += f" {start_enhancements[0]}"
    
    return enhanced_desc

def generate_cv_html(cv_data):
    """Función simplificada para generar HTML del CV"""
    try:
        personal = cv_data.get('personal_info', {})
        professional_summary = cv_data.get('professional_summary', '')
        education = cv_data.get('education', [])
        experience = cv_data.get('experience', [])
        skills = cv_data.get('skills', [])
        languages = cv_data.get('languages', [])
        format_options = cv_data.get('format_options', {
            'format': 'hardware', 
            'summary_tech_xyz': False, 
            'summary_tech_start': False, 
            'experience_tech_xyz': False, 
            'experience_tech_start': False
        })
        
        # Determinar el formato seleccionado
        selected_format = format_options.get('format', 'hardware')
        
        # CSS base simplificado
        css = """
        <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .cv-container { max-width: 800px; margin: 0 auto; }
        h1 { color: #2c3e50; }
        h3 { color: #34495e; }
        .section { margin: 20px 0; }
        </style>
        """
        
        # Información personal
        name = personal.get('name', '')
        email = personal.get('email', '')
        phone = personal.get('phone', '')
        address = personal.get('address', '')
        
        contact_info = [email, phone, address]
        contact_info = [info for info in contact_info if info]
        contact_line = ' | '.join(contact_info)
        
        # HTML básico
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>CV - {name}</title>
            {css}
        </head>
        <body>
            <div class="cv-container">
                <h1>{name}</h1>
                <p>{contact_line}</p>
                
                <div class="section">
                    <h3>Resumen Profesional</h3>
                    <p>{professional_summary}</p>
                </div>
                
                <div class="section">
                    <h3>Educación</h3>
        """
        
        # Agregar educación
        for edu in education:
            degree = edu.get('degree', '')
            institution = edu.get('institution', '')
            year = edu.get('year', '')
            html += f"<p><strong>{degree}</strong><br>{institution}<br>{year}</p>"
        
        html += "</div>"
        
        # Agregar experiencia
        html += '<div class="section"><h3>Experiencia Profesional</h3>'
        for exp in experience:
            position = exp.get('position', '')
            company = exp.get('company', '')
            duration = exp.get('duration', '')
            description = exp.get('description', '')
            
            html += f"""
            <div>
                <strong>{position}</strong><br>
                <em>{company}</em><br>
                <span>{duration}</span><br>
                <p>{description}</p>
            </div>
            """
        
        html += "</div>"
        
        # Agregar habilidades
        html += '<div class="section"><h3>Habilidades</h3><ul>'
        for skill in skills:
            skill_name = skill.get('name', '') if isinstance(skill, dict) else str(skill)
            html += f'<li>{skill_name}</li>'
        html += '</ul></div>'
        
        html += """
            </div>
        </body>
        </html>
        """
        
        return html
        
    except Exception as e:
        print(f"Error en generate_cv_html: {e}")
        traceback.print_exc()
        raise e

def test_export_cv_response(cv_id, user_id):
    """Probar la función export_cv completa incluyendo la respuesta HTTP"""
    try:
        print(f"=== PROBANDO EXPORT CV RESPONSE: ID {cv_id}, USER {user_id} ===")
        
        with app.app_context():
            # Simular sesión
            with app.test_request_context():
                session['user_id'] = user_id
                
                # Obtener los datos del CV de la base de datos
                try:
                    connection = get_db_connection()
                    cursor = connection.cursor()
                    
                    print("✅ Conexión a base de datos establecida")
                    
                    # Primero verificar que el CV existe en la tabla resumes
                    cursor.execute(
                        "SELECT filename FROM resumes WHERE id = %s AND user_id = %s",
                        (cv_id, session['user_id'])
                    )
                    resume_result = cursor.fetchone()
                    
                    if not resume_result:
                        cursor.close()
                        connection.close()
                        print("❌ CV no encontrado")
                        return jsonify({'error': 'CV no encontrado'}), 404
                    
                    cv_title = resume_result[0]
                    print(f"✅ CV encontrado: {cv_title}")
                    
                    # Obtener los datos estructurados del CV desde user_cv_data
                    cursor.execute(
                        "SELECT personal_info, professional_summary, education, experience, skills, languages, format_options FROM user_cv_data WHERE user_id = %s",
                        (session['user_id'],)
                    )
                    result = cursor.fetchone()
                    
                    if not result:
                        cursor.close()
                        connection.close()
                        print("❌ Datos del CV no encontrados")
                        return jsonify({'error': 'Datos del CV no encontrados'}), 404
                    
                    print("✅ Datos del CV encontrados")
                    
                    personal_info, professional_summary, education, experience, skills, languages, format_options = result
                    cursor.close()
                    connection.close()
                    
                    print("✅ Conexión cerrada")
                    
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
                    
                    print("✅ Datos del CV reconstruidos")
                    
                    # Generar el HTML exactamente igual que en la vista previa
                    cv_html = generate_cv_html(cv_data)
                    
                    print("✅ HTML generado exitosamente")
                    print(f"Longitud del HTML: {len(cv_html)} caracteres")
                    
                    # Preparar HTML optimizado para PDF
                    pdf_optimized_html = f"""
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <meta charset="UTF-8">
                        <title>CV - {cv_data['personal_info'].get('name', 'CV')}</title>
                        <style>
                            @media print {{
                                @page {{
                                    size: A4;
                                    margin: 1cm;
                                }}
                                body {{
                                    -webkit-print-color-adjust: exact;
                                    print-color-adjust: exact;
                                }}
                            }}
                            body {{
                                font-family: Arial, sans-serif;
                                line-height: 1.4;
                                margin: 0;
                                padding: 20px;
                            }}
                        </style>
                        <script>
                            window.onload = function() {{
                                setTimeout(function() {{
                                    window.print();
                                }}, 500);
                            }};
                        </script>
                    </head>
                    <body>
                        {cv_html}
                        <div class="print-instructions" style="display: block; margin-top: 20px; padding: 10px; background-color: #f0f0f0; border-radius: 5px;">
                            <p><strong>Instrucciones para guardar como PDF:</strong></p>
                            <ol>
                                <li>Se abrirá automáticamente el diálogo de impresión</li>
                                <li>Selecciona "Guardar como PDF" como destino</li>
                                <li>Ajusta las configuraciones si es necesario</li>
                                <li>Haz clic en "Guardar"</li>
                            </ol>
                        </div>
                    </body>
                    </html>
                    """
                    
                    print("✅ HTML optimizado para PDF generado")
                    print(f"Longitud del HTML optimizado: {len(pdf_optimized_html)} caracteres")
                    
                    # Crear la respuesta HTTP
                    try:
                        response = Response(
                            pdf_optimized_html,
                            mimetype='text/html',
                            headers={
                                'Content-Disposition': f'inline; filename="{cv_title.replace(".pdf", "")}_export.html"'
                            }
                        )
                        
                        print("✅ Respuesta HTTP creada exitosamente")
                        print(f"Content-Type: {response.content_type}")
                        print(f"Headers: {dict(response.headers)}")
                        
                        return response
                        
                    except Exception as e:
                        print(f"❌ Error al crear respuesta HTTP: {e}")
                        traceback.print_exc()
                        return jsonify({'error': f'Error al crear respuesta: {str(e)}'}), 500
                    
                except Exception as e:
                    print(f"❌ Error en base de datos: {e}")
                    traceback.print_exc()
                    return jsonify({'error': f'Error al obtener CV: {str(e)}'}), 500
                
    except Exception as e:
        print(f"❌ Error general: {e}")
        traceback.print_exc()
        return jsonify({'error': f'Error al obtener CV: {str(e)}'}), 500

if __name__ == "__main__":
    # Probar con CV ID 80, USER 14
    result = test_export_cv_response(80, 14)
    print(f"\nResultado final: {type(result)}")
    if hasattr(result, 'status_code'):
        print(f"Status code: {result.status_code}")
    if hasattr(result, 'data'):
        print(f"Data length: {len(result.data) if result.data else 0}")