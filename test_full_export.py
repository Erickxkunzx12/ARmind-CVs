import psycopg2
from config_manager import ConfigManager

# Initialize configuration manager
config_manager = ConfigManager()
import json
import traceback

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

def test_full_export_cv(cv_id, user_id):
    """Reproducir exactamente la función export_cv"""
    try:
        print(f"=== PROBANDO EXPORT CV COMPLETO: ID {cv_id}, USER {user_id} ===")
        
        # Conectar a la base de datos
        db_config = config_manager.get_database_config()
        connection = psycopg2.connect(**db_config)
        cursor = connection.cursor()
        
        # Verificar que el CV existe y pertenece al usuario
        cursor.execute(
            "SELECT filename FROM resumes WHERE id = %s AND user_id = %s",
            (cv_id, user_id)
        )
        cv_result = cursor.fetchone()
        
        if not cv_result:
            print("❌ CV no encontrado")
            return False
        
        cv_title = cv_result[0]
        print(f"✅ CV encontrado: {cv_title}")
        
        # Obtener los datos del CV
        cursor.execute(
            "SELECT personal_info, professional_summary, education, experience, skills, languages, format_options FROM user_cv_data WHERE user_id = %s",
            (user_id,)
        )
        result = cursor.fetchone()
        
        if not result:
            print("❌ Datos del CV no encontrados")
            return False
        
        print("✅ Datos del CV encontrados")
        
        personal_info, professional_summary, education, experience, skills, languages, format_options = result
        cursor.close()
        connection.close()
        
        print("\n=== RECONSTRUYENDO DATOS DEL CV ===")
        
        # Reconstruir los datos del CV exactamente como en el código original
        cv_data = {
            'personal_info': personal_info if personal_info else {},
            'professional_summary': professional_summary if professional_summary else '',
            'education': education if education else [],
            'experience': experience if experience else [],
            'skills': skills if skills else [],
            'languages': languages if languages else [],
            'format_options': format_options if format_options else {'format': 'hardware', 'tech_xyz': False, 'tech_start': False}
        }
        
        print("✅ Datos reconstruidos exitosamente")
        
        print("\n=== INICIANDO GENERACIÓN DE HTML ===")
        
        # Simular generate_cv_html paso a paso
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
        
        print("✅ Variables extraídas")
        
        # Determinar el formato seleccionado
        selected_format = format_options.get('format', 'hardware')
        print(f"Formato seleccionado: {selected_format}")
        
        # Definir estilos CSS base
        if selected_format == 'ats':
            base_css = """
            body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: white; color: black; }
            .cv-container { max-width: 800px; margin: 0 auto; }
            h1 { font-size: 24px; margin-bottom: 5px; }
            h2 { font-size: 18px; margin-top: 20px; margin-bottom: 10px; }
            h3 { font-size: 16px; margin-top: 15px; margin-bottom: 8px; }
            """
        else:  # hardware
            base_css = """
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background-color: #f8f9fa; color: #333; }
            .cv-container { max-width: 800px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { font-size: 28px; margin-bottom: 5px; color: #2c3e50; }
            h2 { font-size: 20px; margin-top: 25px; margin-bottom: 15px; color: #34495e; border-bottom: 2px solid #3498db; padding-bottom: 5px; }
            h3 { font-size: 18px; margin-top: 20px; margin-bottom: 10px; color: #2c3e50; }
            """
        
        print("✅ CSS base definido")
        
        # Construir información de contacto
        try:
            name = personal.get('name', '')
            email = personal.get('email', '')
            phone = personal.get('phone', '')
            address = personal.get('address', '')
            
            contact_info = [email, phone, address]
            contact_info = [info for info in contact_info if info]  # Filtrar campos vacíos
            contact_line = ' | '.join(contact_info)
            
            print(f"✅ Información de contacto: {contact_line}")
            
        except Exception as e:
            print(f"❌ Error en información de contacto: {e}")
            traceback.print_exc()
            return False
        
        # Construir enlaces sociales
        try:
            social_links = []
            linkedin = personal.get('linkedin', '')
            github = personal.get('github', '')
            portfolio = personal.get('portfolio', '')
            
            if linkedin:
                social_links.append(f'<a href="{linkedin}" target="_blank">LinkedIn</a>')
            if github:
                social_links.append(f'<a href="{github}" target="_blank">GitHub</a>')
            if portfolio:
                social_links.append(f'<a href="{portfolio}" target="_blank">Portfolio</a>')
            
            social_links_html = ' | '.join(social_links) if social_links else ''
            
            print(f"✅ Enlaces sociales: {len(social_links)} enlaces")
            
        except Exception as e:
            print(f"❌ Error en enlaces sociales: {e}")
            traceback.print_exc()
            return False
        
        # Generar sección de resumen profesional
        try:
            summary_tech_xyz = format_options.get('summary_tech_xyz', False)
            summary_tech_start = format_options.get('summary_tech_start', False)
            
            professional_summary_html = generate_professional_summary_section(
                professional_summary, 
                summary_tech_xyz, 
                summary_tech_start
            )
            
            print("✅ Resumen profesional generado")
            
        except Exception as e:
            print(f"❌ Error en resumen profesional: {e}")
            traceback.print_exc()
            return False
        
        # Procesar educación
        try:
            education_html = ""
            if education:
                education_html = '<div class="section"><h3>Educación</h3>'
                for edu in education:
                    degree = edu.get('degree', '')
                    institution = edu.get('institution', '')
                    year = edu.get('year', '')
                    education_html += f'<div class="education-item"><strong>{degree}</strong><br>{institution}<br>{year}</div>'
                education_html += '</div>'
            
            print(f"✅ Educación procesada: {len(education)} elementos")
            
        except Exception as e:
            print(f"❌ Error en educación: {e}")
            traceback.print_exc()
            return False
        
        # Procesar experiencia
        try:
            experience_html = ""
            if experience:
                experience_html = '<div class="section"><h3>Experiencia Profesional</h3>'
                
                experience_tech_xyz = format_options.get('experience_tech_xyz', False)
                experience_tech_start = format_options.get('experience_tech_start', False)
                
                for exp in experience:
                    position = exp.get('position', '')
                    company = exp.get('company', '')
                    duration = exp.get('duration', '')
                    description = exp.get('description', '')
                    
                    # Mejorar descripción si está habilitado
                    enhanced_description = enhance_experience_description(
                        description, 
                        experience_tech_xyz, 
                        experience_tech_start
                    )
                    
                    experience_html += f'''
                    <div class="experience-item">
                        <strong>{position}</strong><br>
                        <em>{company}</em><br>
                        <span class="duration">{duration}</span><br>
                        <p>{enhanced_description}</p>
                    </div>
                    '''
                
                experience_html += '</div>'
            
            print(f"✅ Experiencia procesada: {len(experience)} elementos")
            
        except Exception as e:
            print(f"❌ Error en experiencia: {e}")
            traceback.print_exc()
            return False
        
        # Procesar habilidades
        try:
            skills_html = ""
            if skills:
                skills_html = '<div class="section"><h3>Habilidades</h3><ul>'
                for skill in skills:
                    skill_name = skill.get('name', '') if isinstance(skill, dict) else str(skill)
                    skills_html += f'<li>{skill_name}</li>'
                skills_html += '</ul></div>'
            
            print(f"✅ Habilidades procesadas: {len(skills)} elementos")
            
        except Exception as e:
            print(f"❌ Error en habilidades: {e}")
            traceback.print_exc()
            return False
        
        # Procesar idiomas
        try:
            languages_html = ""
            if languages:
                languages_html = '<div class="section"><h3>Idiomas</h3><ul>'
                for lang in languages:
                    if isinstance(lang, dict):
                        lang_name = lang.get('name', '')
                        lang_level = lang.get('level', '')
                        languages_html += f'<li>{lang_name} - {lang_level}</li>'
                    else:
                        languages_html += f'<li>{str(lang)}</li>'
                languages_html += '</ul></div>'
            
            print(f"✅ Idiomas procesados: {len(languages)} elementos")
            
        except Exception as e:
            print(f"❌ Error en idiomas: {e}")
            traceback.print_exc()
            return False
        
        print("\n✅ GENERACIÓN DE HTML COMPLETADA EXITOSAMENTE")
        print("El problema NO está en la generación de HTML")
        
        return True
        
    except Exception as e:
        print(f"❌ Error general: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Probar con CV ID 80, USER 14
    test_full_export_cv(80, 14)