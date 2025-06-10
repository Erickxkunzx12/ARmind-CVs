import sys
sys.path.append('.')
from app import get_db_connection

conn = get_db_connection()
if conn:
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT id, username, email, password_hash FROM users ORDER BY id DESC LIMIT 3')
        results = cursor.fetchall()
        print('Usuarios encontrados:')
        for user in results:
            hash_preview = user['password_hash'][:20] + '...' if user['password_hash'] else 'None'
            print(f'  ID: {user["id"]}, Usuario: {user["username"]}, Email: {user["email"]}, Hash: {hash_preview}')
    except Exception as e:
        print(f'Error: {e}')
    finally:
        cursor.close()
        conn.close()
else:
    print('No se pudo conectar a la base de datos')