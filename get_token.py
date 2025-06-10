import sys
sys.path.append('.')
from app import get_db_connection

conn = get_db_connection()
if conn:
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT username, verification_token FROM users WHERE email_verified = FALSE AND verification_token IS NOT NULL LIMIT 1")
        result = cursor.fetchone()
        if result:
            username, token = result
            print(f"Usuario: {username}")
            print(f"Token completo: {token}")
            print(f"URL de verificación (localhost): http://127.0.0.1:5000/verify_email/{token}")
            print(f"URL de verificación (red local): http://192.168.1.90:5000/verify_email/{token}")
        else:
            print("No se encontró ningún usuario con token de verificación pendiente")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        cursor.close()
        conn.close()
else:
    print("No se pudo conectar a la base de datos")