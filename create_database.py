import psycopg2

def create_database():
    # Primero conectamos a la base de datos predeterminada 'postgres'
    try:
        print("Conectando a PostgreSQL...")
        conn = psycopg2.connect(
            host='localhost',
            database='postgres',  # Base de datos predeterminada
            user='postgres',
            password='Solido123',
            port='5432'
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