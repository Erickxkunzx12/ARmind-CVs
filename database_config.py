# Configuracion de la base de datos PostgreSQL
# Usando variables de entorno para mayor seguridad

import os
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_NAME', 'cv_analyzer'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD'),  # Debe estar configurado en .env
    'port': os.getenv('DB_PORT', '5432')
}

# Si no se encuentra alguna variable de entorno crítica, mostrar advertencia
if not DB_CONFIG['password']:
    print("ADVERTENCIA: DB_PASSWORD no está configurada en las variables de entorno")