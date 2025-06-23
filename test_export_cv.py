import psycopg2
import os
import json
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración de base de datos
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_NAME', 'armind_db'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', ''),
    'port': int(os.getenv('DB_PORT', 5432))
}

def test_export_cv_data(cv_id, user_id):
    try:
        # Conectar a la base de datos
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        print(f"=== PROBANDO EXPORT CV ID: {cv_id}, USER: {user_id} ===")
        
        # Paso 1: Verificar que el CV existe en resumes
        cur.execute(
            "SELECT filename FROM resumes WHERE id = %s AND user_id = %s",
            (cv_id, user_id)
        )
        resume_result = cur.fetchone()
        
        if not resume_result:
            print("❌ ERROR: CV no encontrado en tabla resumes")
            return False
        
        print(f"✅ CV encontrado: {resume_result[0]}")
        
        # Paso 2: Verificar datos en user_cv_data
        cur.execute(
            "SELECT personal_info, professional_summary, education, experience, skills, languages, format_options FROM user_cv_data WHERE user_id = %s",
            (user_id,)
        )
        result = cur.fetchone()
        
        if not result:
            print("❌ ERROR: Datos del CV no encontrados en user_cv_data")
            print("Esto significa que el usuario no ha creado un CV usando el constructor de CVs")
            
            # Verificar si hay algún registro para este usuario
            cur.execute("SELECT COUNT(*) FROM user_cv_data WHERE user_id = %s", (user_id,))
            count = cur.fetchone()[0]
            print(f"Registros en user_cv_data para usuario {user_id}: {count}")
            
            return False
        
        print("✅ Datos del CV encontrados en user_cv_data")
        
        # Mostrar los datos encontrados
        personal_info, professional_summary, education, experience, skills, languages, format_options = result
        
        print("\n=== DATOS ENCONTRADOS ===")
        print(f"Personal Info: {personal_info is not None}")
        print(f"Professional Summary: {professional_summary is not None}")
        print(f"Education: {education is not None}")
        print(f"Experience: {experience is not None}")
        print(f"Skills: {skills is not None}")
        print(f"Languages: {languages is not None}")
        print(f"Format Options: {format_options is not None}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ ERROR en test_export_cv_data: {e}")
        return False

def list_available_cvs():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        print("\n=== CVS DISPONIBLES ===")
        
        # Listar todos los CVs
        cur.execute("SELECT id, user_id, filename FROM resumes ORDER BY id DESC LIMIT 10")
        resumes = cur.fetchall()
        
        for resume in resumes:
            cv_id, user_id, filename = resume
            print(f"CV ID: {cv_id}, User: {user_id}, File: {filename}")
            
            # Verificar si tiene datos en user_cv_data
            cur.execute("SELECT COUNT(*) FROM user_cv_data WHERE user_id = %s", (user_id,))
            has_cv_data = cur.fetchone()[0] > 0
            print(f"  - Tiene datos en user_cv_data: {'✅' if has_cv_data else '❌'}")
        
        conn.close()
        
    except Exception as e:
        print(f"Error al listar CVs: {e}")

if __name__ == "__main__":
    # Listar CVs disponibles
    list_available_cvs()
    
    # Probar con algunos CVs específicos
    print("\n" + "="*50)
    test_export_cv_data(84, 14)  # CV más reciente
    
    print("\n" + "="*50)
    test_export_cv_data(80, 14)  # Otro CV del mismo usuario