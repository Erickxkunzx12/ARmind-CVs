import psycopg2
from database_config import DB_CONFIG
import json

def test_json_deserialization(user_id):
    try:
        # Conectar a la base de datos
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        print(f"=== PROBANDO DESERIALIZACIÓN JSON PARA USER: {user_id} ===")
        
        # Obtener datos raw de la base de datos
        cur.execute(
            "SELECT personal_info, professional_summary, education, experience, skills, languages, format_options FROM user_cv_data WHERE user_id = %s",
            (user_id,)
        )
        result = cur.fetchone()
        
        if not result:
            print("❌ No se encontraron datos")
            return False
        
        personal_info, professional_summary, education, experience, skills, languages, format_options = result
        
        print("\n=== DATOS RAW ===")
        print(f"Personal Info Type: {type(personal_info)}, Value: {personal_info}")
        print(f"Professional Summary Type: {type(professional_summary)}, Value: {professional_summary}")
        print(f"Education Type: {type(education)}, Value: {education}")
        print(f"Experience Type: {type(experience)}, Value: {experience}")
        print(f"Skills Type: {type(skills)}, Value: {skills}")
        print(f"Languages Type: {type(languages)}, Value: {languages}")
        print(f"Format Options Type: {type(format_options)}, Value: {format_options}")
        
        print("\n=== PROBANDO DESERIALIZACIÓN ===")
        
        # Probar deserialización como se hace en el código original
        try:
            cv_data = {
                'personal_info': personal_info if personal_info else {},
                'professional_summary': professional_summary if professional_summary else '',
                'education': education if education else [],
                'experience': experience if experience else [],
                'skills': skills if skills else [],
                'languages': languages if languages else [],
                'format_options': format_options if format_options else {'format': 'hardware', 'tech_xyz': False, 'tech_start': False}
            }
            
            print("✅ Deserialización exitosa")
            print(f"CV Data: {cv_data}")
            
            # Probar acceso a campos específicos
            print("\n=== PROBANDO ACCESO A CAMPOS ===")
            print(f"Nombre: {cv_data['personal_info'].get('name', 'No encontrado')}")
            print(f"Email: {cv_data['personal_info'].get('email', 'No encontrado')}")
            print(f"Número de educaciones: {len(cv_data['education'])}")
            print(f"Número de experiencias: {len(cv_data['experience'])}")
            print(f"Número de habilidades: {len(cv_data['skills'])}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error en deserialización: {e}")
            return False
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error general: {e}")
        return False

def test_generate_cv_html_simulation(user_id):
    """Simular la función generate_cv_html para encontrar el error"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        cur.execute(
            "SELECT personal_info, professional_summary, education, experience, skills, languages, format_options FROM user_cv_data WHERE user_id = %s",
            (user_id,)
        )
        result = cur.fetchone()
        
        if not result:
            print("❌ No se encontraron datos")
            return False
        
        personal_info, professional_summary, education, experience, skills, languages, format_options = result
        
        # Reconstruir los datos del CV como en el código original
        cv_data = {
            'personal_info': personal_info if personal_info else {},
            'professional_summary': professional_summary if professional_summary else '',
            'education': education if education else [],
            'experience': experience if experience else [],
            'skills': skills if skills else [],
            'languages': languages if languages else [],
            'format_options': format_options if format_options else {'format': 'hardware', 'tech_xyz': False, 'tech_start': False}
        }
        
        print("\n=== SIMULANDO GENERATE_CV_HTML ===")
        
        # Simular las primeras líneas de generate_cv_html
        personal = cv_data.get('personal_info', {})
        professional_summary = cv_data.get('professional_summary', '')
        education = cv_data.get('education', [])
        experience = cv_data.get('experience', [])
        skills = cv_data.get('skills', [])
        languages = cv_data.get('languages', [])
        format_options = cv_data.get('format_options', {'format': 'hardware', 'summary_tech_xyz': False, 'summary_tech_start': False, 'experience_tech_xyz': False, 'experience_tech_start': False})
        
        print(f"Personal: {personal}")
        print(f"Professional Summary: {professional_summary}")
        print(f"Education: {education}")
        print(f"Experience: {experience}")
        print(f"Skills: {skills}")
        print(f"Languages: {languages}")
        print(f"Format Options: {format_options}")
        
        # Probar acceso a campos específicos que podrían causar error
        try:
            name = personal.get('name', '')
            email = personal.get('email', '')
            phone = personal.get('phone', '')
            address = personal.get('address', '')
            
            print(f"\nDatos personales extraídos:")
            print(f"  Nombre: {name}")
            print(f"  Email: {email}")
            print(f"  Teléfono: {phone}")
            print(f"  Dirección: {address}")
            
            # Probar construcción de contact_info como en el código original
            contact_info = [email, phone, address]
            contact_info = [info for info in contact_info if info]  # Filtrar campos vacíos
            contact_line = ' | '.join(contact_info)
            
            print(f"  Contact line: {contact_line}")
            
            print("✅ Simulación exitosa")
            return True
            
        except Exception as e:
            print(f"❌ Error en simulación: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error general en simulación: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Probar con usuario 14
    test_json_deserialization(14)
    test_generate_cv_html_simulation(14)