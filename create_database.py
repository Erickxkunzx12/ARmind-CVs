import psycopg2
from psycopg2 import sql
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_database():
    # Configuración de conexión (sin especificar base de datos)
    conn_params = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': os.getenv('DB_PORT', '5432'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD'),
    }
    
    # Primero conectamos a la base de datos predeterminada 'postgres'
    try:
        print("Conectando a PostgreSQL...")
        conn = psycopg2.connect(
            database='postgres',  # Base de datos predeterminada
            **conn_params
        )
        conn.autocommit = True  # Necesario para crear bases de datos
        cursor = conn.cursor()
        
        # Verificar si la base de datos cv_analyzer ya existe
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = 'cv_analyzer'")
        exists = cursor.fetchone()
        
        if not exists:
            print("Creando base de datos 'cv_analyzer'...")
            cursor.execute("CREATE DATABASE cv_analyzer")
            print("Base de datos 'cv_analyzer' creada exitosamente.")
        else:
            print("La base de datos 'cv_analyzer' ya existe.")
            
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    create_database()