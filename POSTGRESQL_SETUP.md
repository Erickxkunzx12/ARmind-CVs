# Migración a PostgreSQL

Este documento explica cómo migrar la aplicación de SQLite a PostgreSQL para mejorar el rendimiento y escalabilidad.

## ¿Por qué PostgreSQL?

PostgreSQL es una excelente opción para tu aplicación porque:

- **Escalabilidad**: Maneja mejor grandes volúmenes de datos y usuarios concurrentes
- **Rendimiento**: Mejor optimización para consultas complejas
- **Características avanzadas**: Soporte para JSON, búsqueda de texto completo, etc.
- **Producción**: Ampliamente usado en aplicaciones web de producción
- **Desarrollo local**: Funciona perfectamente tanto en desarrollo como en producción

## Instalación de PostgreSQL

### Windows
1. Descarga PostgreSQL desde: https://www.postgresql.org/download/windows/
2. Ejecuta el instalador y sigue las instrucciones
3. Anota la contraseña que configures para el usuario `postgres`
4. Por defecto se instala en el puerto 5432

### Verificar instalación
Abre Command Prompt o PowerShell y ejecuta:
```bash
psql --version
```

## Configuración de la base de datos

### 1. Crear la base de datos
Abre pgAdmin (incluido con PostgreSQL) o usa la línea de comandos:

```sql
-- Conectar como usuario postgres
psql -U postgres -h localhost

-- Crear la base de datos
CREATE DATABASE cv_analyzer;

-- Crear un usuario específico (opcional pero recomendado)
CREATE USER cv_app_user WITH PASSWORD 'tu_password_segura';
GRANT ALL PRIVILEGES ON DATABASE cv_analyzer TO cv_app_user;
```

### 2. Configurar credenciales
Edita el archivo `database_config.py` con tus credenciales:

```python
DB_CONFIG = {
    'host': 'localhost',
    'database': 'cv_analyzer',
    'user': 'postgres',  # o 'cv_app_user' si creaste un usuario específico
    'password': 'tu_password_real',  # Cambia por tu contraseña
    'port': '5432'
}
```

## Migración de datos

### Opción 1: Migración automática (recomendada)
Si ya tienes datos en SQLite:

```bash
# Ejecutar el script de migración
python migrate_to_postgresql.py
```

### Opción 2: Empezar desde cero
Si prefieres empezar con una base de datos limpia:

```bash
# Solo ejecutar la aplicación, las tablas se crearán automáticamente
python app.py
```

## Verificación

### 1. Probar conexión
Puedes probar la conexión ejecutando este código Python:

```python
import psycopg2
from database_config import DB_CONFIG

try:
    conn = psycopg2.connect(**DB_CONFIG)
    print("✅ Conexión exitosa a PostgreSQL")
    conn.close()
except Exception as e:
    print(f"❌ Error de conexión: {e}")
```

### 2. Ejecutar la aplicación
```bash
python app.py
```

La aplicación debería iniciarse y crear las tablas automáticamente si no existen.

## Configuración para producción

### Variables de entorno
Para producción, es recomendable usar variables de entorno. Modifica `database_config.py`:

```python
import os

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_NAME', 'cv_analyzer'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD'),
    'port': os.getenv('DB_PORT', '5432')
}
```

### Servicios en la nube
Puedes usar servicios como:
- **Heroku Postgres**: Fácil integración con Heroku
- **AWS RDS**: Amazon Relational Database Service
- **Google Cloud SQL**: Servicio de base de datos de Google
- **DigitalOcean Managed Databases**: Opción económica

## Solución de problemas

### Error de conexión
- Verifica que PostgreSQL esté ejecutándose
- Confirma las credenciales en `database_config.py`
- Asegúrate de que la base de datos `cv_analyzer` existe

### Error de permisos
- Verifica que el usuario tenga permisos en la base de datos
- Usa `GRANT ALL PRIVILEGES ON DATABASE cv_analyzer TO tu_usuario;`

### Puerto ocupado
- PostgreSQL usa el puerto 5432 por defecto
- Puedes cambiarlo en la configuración si hay conflictos

## Ventajas de la migración

✅ **Mejor rendimiento** con múltiples usuarios
✅ **Escalabilidad** para crecimiento futuro
✅ **Características avanzadas** de PostgreSQL
✅ **Preparado para producción**
✅ **Mejor manejo de concurrencia**
✅ **Soporte para índices avanzados**

¡Tu aplicación ahora está lista para manejar una gran cantidad de usuarios y archivos!