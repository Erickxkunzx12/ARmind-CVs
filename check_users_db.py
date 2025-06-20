import psycopg2
from psycopg2.extras import RealDictCursor
from config_manager import get_config

def check_users():
    """Verificar usuarios en la base de datos"""
    try:
        # Usar configuración centralizada
        config = get_config()
        db_config = config.DATABASE_CONFIG
        
        conn = psycopg2.connect(
            host=db_config['host'],
            database=db_config['database'],
            user=db_config['user'],
            password=db_config['password'],
            port=db_config['port'],
            cursor_factory=RealDictCursor
        )
        
        cursor = conn.cursor()
        cursor.execute('SELECT id, username, email FROM users LIMIT 10')
        users = cursor.fetchall()
        
        print('Usuarios en la base de datos:')
        if users:
            for user in users:
                print(f'ID: {user["id"]}, Username: {user["username"]}, Email: {user["email"]}')
        else:
            print('No hay usuarios en la base de datos')
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f'Error: {e}')

if __name__ == "__main__":
    check_users()