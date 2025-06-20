import psycopg2
from config_manager import ConfigManager

# Initialize configuration manager
config_manager = ConfigManager()
import json

def check_database():
    try:
        # Conectar a la base de datos
        db_config = config_manager.get_database_config()
        conn = psycopg2.connect(**db_config)
        cur = conn.cursor()
        
        print("=== DIAGNÓSTICO DE BASE DE DATOS ===")
        
        # Verificar tablas relacionadas con CV
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name LIKE '%cv%'
        """)
        cv_tables = cur.fetchall()
        print(f"Tablas CV encontradas: {cv_tables}")
        
        # Verificar tabla user_cv_data
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'user_cv_data'
            )
        """)
        user_cv_data_exists = cur.fetchone()[0]
        print(f"Tabla user_cv_data existe: {user_cv_data_exists}")
        
        if user_cv_data_exists:
            # Contar registros en user_cv_data
            cur.execute("SELECT COUNT(*) FROM user_cv_data")
            count = cur.fetchone()[0]
            print(f"Registros en user_cv_data: {count}")
            
            # Mostrar estructura de la tabla
            cur.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'user_cv_data'
                ORDER BY ordinal_position
            """)
            columns = cur.fetchall()
            print("Estructura de user_cv_data:")
            for col in columns:
                print(f"  - {col[0]}: {col[1]}")
        
        # Verificar tabla resumes
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'resumes'
            )
        """)
        resumes_exists = cur.fetchone()[0]
        print(f"Tabla resumes existe: {resumes_exists}")
        
        if resumes_exists:
            cur.execute("SELECT COUNT(*) FROM resumes")
            count = cur.fetchone()[0]
            print(f"Registros en resumes: {count}")
            
            # Mostrar algunos registros de resumes
            cur.execute("SELECT id, user_id, filename FROM resumes LIMIT 5")
            resumes = cur.fetchall()
            print("Primeros 5 registros de resumes:")
            for resume in resumes:
                print(f"  ID: {resume[0]}, User: {resume[1]}, File: {resume[2]}")
        
        # Verificar usuarios
        cur.execute("SELECT COUNT(*) FROM users")
        user_count = cur.fetchone()[0]
        print(f"Total de usuarios: {user_count}")
        
        conn.close()
        
    except Exception as e:
        print(f"Error al conectar a la base de datos: {e}")

if __name__ == "__main__":
    check_database()