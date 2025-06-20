import psycopg2
from config_manager import ConfigManager

# Initialize configuration manager
config_manager = ConfigManager()

def init_tables():
    try:
        print("Conectando a PostgreSQL...")
        db_config = config_manager.get_database_config()
        conn = psycopg2.connect(
            host=db_config['host'],
            database=db_config['database'],
            user=db_config['user'],
            password=db_config['password'],
            port=db_config['port']
        )
        conn.autocommit = False
        cursor = conn.cursor()
        
        # Crear tablas si no existen
        print("Creando tablas si no existen...")
        
        # Tabla de usuarios
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(100) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            email_verified BOOLEAN DEFAULT FALSE,
            verification_token VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Tabla de resumes (CVs)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS resumes (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            filename VARCHAR(255) NOT NULL,
            content TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Tabla de feedback (análisis de CV)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id SERIAL PRIMARY KEY,
            resume_id INTEGER REFERENCES resumes(id),
            score INTEGER,
            strengths TEXT,
            weaknesses TEXT,
            recommendations TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Tabla de trabajos
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id SERIAL PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            company VARCHAR(255),
            location VARCHAR(255),
            description TEXT,
            url VARCHAR(500),
            source VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        conn.commit()
        print("Tablas creadas exitosamente.")
        
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Error: {e}")
        if conn:
            conn.rollback()
        return False

if __name__ == "__main__":
    init_tables()