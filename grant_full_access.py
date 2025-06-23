import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración de base de datos (igual que app.py)
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_NAME', 'armind_db'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', ''),
    'port': int(os.getenv('DB_PORT', 5432))
}

def grant_full_access_to_users():
    try:
        # Usar la misma configuración que app.py
        os.environ['PGCLIENTENCODING'] = 'UTF8'
        
        connection = psycopg2.connect(
            host=DB_CONFIG['host'],
            database=DB_CONFIG['database'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            port=DB_CONFIG['port'],
            cursor_factory=RealDictCursor,
            client_encoding='UTF8',
            options="-c client_encoding=UTF8"
        )
        
        cursor = connection.cursor()
        
        # Obtener todas las cuentas de usuario existentes (sin filtrar por role)
        cursor.execute('SELECT id, username, email FROM users')
        users = cursor.fetchall()
        
        print(f'Encontradas {len(users)} cuentas:')
        for user in users:
            print(f'- ID: {user["id"]}, Usuario: {user["username"]}, Email: {user["email"]}')
        
        if not users:
            print('No se encontraron cuentas para actualizar.')
            return
        
        # Crear suscripciones profesionales para cada usuario
        for user in users:
            user_id = user['id']
            username = user['username']
            email = user['email']
            
            # Verificar si ya tiene suscripción activa
            cursor.execute('SELECT id FROM subscriptions WHERE user_id = %s AND status = %s', (user_id, 'active'))
            existing_sub = cursor.fetchone()
            
            if existing_sub:
                print(f'Usuario {username} ya tiene suscripcion activa')
                continue
                
            # Calcular fechas (1 año de duración)
            start_date = datetime.now()
            end_date = start_date + timedelta(days=365)
            
            # Crear suscripción profesional
            try:
                cursor.execute("""
                    INSERT INTO subscriptions (user_id, plan_type, start_date, end_date, payment_method, transaction_id, amount, currency, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (user_id, 'pro', start_date, end_date, 'admin_grant', f'admin_grant_{user_id}', 0, 'CLP', 'active'))
                
                result = cursor.fetchone()
                if result:
                    subscription_id = result['id']
                    print(f'Suscripcion profesional creada para {username} (ID: {subscription_id})')
                else:
                    print(f'Error: No se pudo crear suscripcion para {username}')
            except Exception as sub_error:
                print(f'Error creando suscripcion para {username}: {sub_error}')
                continue
        
        connection.commit()
        print('\nTodas las cuentas han sido actualizadas con acceso completo')
        
    except Exception as e:
        print(f'Error: {e}')
        if 'connection' in locals():
            connection.rollback()
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals():
            connection.close()

if __name__ == '__main__':
    grant_full_access_to_users()