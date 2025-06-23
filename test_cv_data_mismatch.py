import psycopg2
import os
from dotenv import load_dotenv
import requests

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

def get_db_connection():
    """Obtener conexión a la base de datos"""
    return psycopg2.connect(**DB_CONFIG)

def test_cv_data_mismatch():
    """Test para verificar el problema de mismatch entre CV ID y user_cv_data"""
    
    print("=== ANALIZANDO PROBLEMA DE CV DATA MISMATCH ===")
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # 1. Verificar cuántos CVs tiene cada usuario
        print("\n1. Verificando CVs por usuario:")
        cursor.execute("""
            SELECT user_id, COUNT(*) as cv_count 
            FROM resumes 
            GROUP BY user_id 
            HAVING COUNT(*) > 1
            ORDER BY cv_count DESC
            LIMIT 5
        """)
        
        users_with_multiple_cvs = cursor.fetchall()
        
        if users_with_multiple_cvs:
            print(f"   Usuarios con múltiples CVs: {len(users_with_multiple_cvs)}")
            for user_id, cv_count in users_with_multiple_cvs:
                print(f"   - Usuario {user_id}: {cv_count} CVs")
        else:
            print("   No hay usuarios con múltiples CVs")
        
        # 2. Verificar la estructura de user_cv_data
        print("\n2. Verificando estructura de user_cv_data:")
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'user_cv_data'
            ORDER BY ordinal_position
        """)
        
        columns = cursor.fetchall()
        print("   Columnas en user_cv_data:")
        for col_name, data_type in columns:
            print(f"   - {col_name}: {data_type}")
        
        # 3. Verificar si hay un campo cv_id en user_cv_data
        has_cv_id = any(col[0] == 'cv_id' for col in columns)
        print(f"   ¿Tiene campo cv_id? {has_cv_id}")
        
        # 4. Verificar datos en user_cv_data
        print("\n3. Verificando datos en user_cv_data:")
        cursor.execute("SELECT COUNT(*) FROM user_cv_data")
        total_cv_data = cursor.fetchone()[0]
        print(f"   Total registros en user_cv_data: {total_cv_data}")
        
        # 5. Verificar datos en resumes
        print("\n4. Verificando datos en resumes:")
        cursor.execute("SELECT COUNT(*) FROM resumes")
        total_resumes = cursor.fetchone()[0]
        print(f"   Total registros en resumes: {total_resumes}")
        
        # 6. Buscar discrepancias
        print("\n5. Buscando discrepancias:")
        cursor.execute("""
            SELECT r.user_id, COUNT(r.id) as resume_count, 
                   CASE WHEN ucd.user_id IS NOT NULL THEN 1 ELSE 0 END as has_cv_data
            FROM resumes r
            LEFT JOIN user_cv_data ucd ON r.user_id = ucd.user_id
            GROUP BY r.user_id, ucd.user_id
            ORDER BY resume_count DESC
            LIMIT 10
        """)
        
        discrepancies = cursor.fetchall()
        print("   Usuarios y sus datos:")
        for user_id, resume_count, has_cv_data in discrepancies:
            status = "✅" if has_cv_data else "❌"
            print(f"   {status} Usuario {user_id}: {resume_count} CVs, datos: {'Sí' if has_cv_data else 'No'}")
        
        # 7. Simular el problema del export_cv
        print("\n6. Simulando problema de export_cv:")
        
        # Buscar un usuario con múltiples CVs
        if users_with_multiple_cvs:
            test_user_id = users_with_multiple_cvs[0][0]
            
            # Obtener todos los CVs de este usuario
            cursor.execute(
                "SELECT id, filename FROM resumes WHERE user_id = %s ORDER BY id",
                (test_user_id,)
            )
            user_cvs = cursor.fetchall()
            
            print(f"   Usuario de prueba {test_user_id} tiene {len(user_cvs)} CVs:")
            for cv_id, filename in user_cvs:
                print(f"   - CV {cv_id}: {filename}")
            
            # Verificar qué datos devuelve user_cv_data para este usuario
            cursor.execute(
                "SELECT personal_info, professional_summary FROM user_cv_data WHERE user_id = %s",
                (test_user_id,)
            )
            cv_data_result = cursor.fetchone()
            
            if cv_data_result:
                print(f"   ✅ user_cv_data encontrado para usuario {test_user_id}")
                print(f"   Pero... ¿corresponde a cuál CV? No hay forma de saberlo!")
                print(f"   🚨 PROBLEMA IDENTIFICADO: user_cv_data no tiene cv_id")
            else:
                print(f"   ❌ No hay datos en user_cv_data para usuario {test_user_id}")
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        print(f"❌ Error en análisis: {e}")
        import traceback
        traceback.print_exc()

def test_specific_cv_export():
    """Test específico para reproducir el error de export"""
    
    print("\n=== PROBANDO EXPORT DE CV ESPECÍFICO ===")
    
    try:
        # Probar con diferentes IDs de CV
        test_cv_ids = [80, 81, 82, 999]
        
        for cv_id in test_cv_ids:
            print(f"\nProbando CV ID {cv_id}:")
            
            try:
                response = requests.get(f"http://127.0.0.1:5000/export_cv/{cv_id}", 
                                      allow_redirects=True, timeout=10)
                
                print(f"   Status: {response.status_code}")
                
                if response.status_code == 500:
                    try:
                        error_data = response.json()
                        error_msg = error_data.get('error', 'Sin mensaje de error')
                        print(f"   Error: {error_msg}")
                        
                        if "Error al obtener CV: 0" in error_msg:
                            print(f"   🎯 ENCONTRADO: CV {cv_id} produce el error '0'")
                        
                    except:
                        print(f"   Error no es JSON: {response.text[:100]}")
                        
                elif response.status_code == 200:
                    content_type = response.headers.get('Content-Type', '')
                    if 'text/html' in content_type:
                        print(f"   ✅ Export exitoso, HTML generado ({len(response.text)} chars)")
                    else:
                        print(f"   ❓ Content-Type inesperado: {content_type}")
                        
                elif response.status_code == 404:
                    print(f"   ❌ CV no encontrado")
                    
                else:
                    print(f"   ❓ Status inesperado: {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                print(f"   ❌ Error de conexión: {e}")
            except Exception as e:
                print(f"   ❌ Error inesperado: {e}")
                
    except Exception as e:
        print(f"❌ Error en test: {e}")

if __name__ == "__main__":
    test_cv_data_mismatch()
    test_specific_cv_export()