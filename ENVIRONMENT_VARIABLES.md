# Variables de Entorno - ARMind CV Analyzer

Este documento describe todas las variables de entorno requeridas y opcionales para el correcto funcionamiento del sistema ARMind.

## 📋 Variables Requeridas

Estas variables **DEBEN** estar configuradas para que la aplicación funcione:

### Base de Datos PostgreSQL
```bash
DB_HOST=localhost                    # Host de la base de datos
DB_NAME=cv_analyzer                  # Nombre de la base de datos
DB_USER=postgres                     # Usuario de la base de datos
DB_PASSWORD=tu_password_seguro       # Contraseña de la base de datos
DB_PORT=5432                         # Puerto de la base de datos (opcional, default: 5432)
```

### Seguridad
```bash
SECRET_KEY=tu_clave_secreta_muy_larga_y_segura_123456789
# IMPORTANTE: Debe ser una cadena aleatoria de al menos 32 caracteres
# Puedes generar una con: python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Entorno de Ejecución
```bash
FLASK_ENV=development               # development, production, o testing
DEBUG=True                          # True para desarrollo, False para producción
```

## 🔧 Variables Opcionales

### APIs de Inteligencia Artificial

#### OpenAI (Recomendado)
```bash
OPENAI_API_KEY=sk-proj-tu_api_key_aqui
# Obtener en: https://platform.openai.com/api-keys
```

#### Anthropic Claude
```bash
ANTHROPIC_API_KEY=sk-ant-api03-tu_api_key_aqui
# Obtener en: https://console.anthropic.com/
```

#### Google Gemini
```bash
GEMINI_API_KEY=tu_gemini_api_key_aqui
# Obtener en: https://makersuite.google.com/app/apikey
```

### Configuración de Email

#### Gmail (Recomendado)
```bash
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_USER=tu_email@gmail.com
EMAIL_PASSWORD=tu_app_password_aqui    # Contraseña de aplicación, NO tu contraseña normal
EMAIL_USE_TLS=True
```

#### Outlook/Hotmail
```bash
SMTP_SERVER=smtp-mail.outlook.com
SMTP_PORT=587
EMAIL_USER=tu_email@outlook.com
EMAIL_PASSWORD=tu_contraseña_aqui
EMAIL_USE_TLS=True
```

#### Yahoo
```bash
SMTP_SERVER=smtp.mail.yahoo.com
SMTP_PORT=587
EMAIL_USER=tu_email@yahoo.com
EMAIL_PASSWORD=tu_app_password_aqui
EMAIL_USE_TLS=True
```

### AWS S3 (Para almacenamiento de archivos)

#### Opción 1: Credenciales IAM (Recomendado para producción)
```bash
# No configurar estas variables para usar IAM roles automáticamente
# AWS_ACCESS_KEY_ID=
# AWS_SECRET_ACCESS_KEY=
AWS_REGION=us-east-1
S3_BUCKET_NAME=tu_bucket_name_aqui
S3_FOLDER_PREFIX=cv-analysis/
```

#### Opción 2: Credenciales explícitas (Solo para desarrollo)
```bash
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=us-east-1
S3_BUCKET_NAME=tu_bucket_name_aqui
S3_FOLDER_PREFIX=cv-analysis/
```

## 🧪 Variables para Testing

Para ejecutar tests, puedes usar una base de datos separada:

```bash
TEST_DB_HOST=localhost
TEST_DB_NAME=cv_analyzer_test
TEST_DB_USER=postgres
TEST_DB_PASSWORD=tu_password_test
TEST_DB_PORT=5432
```

## 📁 Configuración por Archivos

### Archivo .env
Crea un archivo `.env` en la raíz del proyecto con todas las variables:

```bash
# Copia .env.example y renómbralo a .env
cp .env.example .env

# Edita el archivo .env con tus valores reales
nano .env
```

### Archivo email_config.py (Alternativo)
Si prefieres no usar variables de entorno para email:

```python
# email_config.py
EMAIL_CONFIG = {
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587,
    'email': 'tu_email@gmail.com',
    'password': 'tu_app_password',
    'use_tls': True
}
```

## 🔒 Mejores Prácticas de Seguridad

### 1. Nunca hardcodear credenciales
❌ **MAL:**
```python
password = 'mi_password_123'
```

✅ **BIEN:**
```python
password = os.getenv('DB_PASSWORD')
```

### 2. Usar contraseñas de aplicación para email
- **Gmail:** Habilitar 2FA y generar contraseña de aplicación
- **Outlook:** Usar contraseña normal o contraseña de aplicación
- **Yahoo:** Generar contraseña de aplicación

### 3. Rotar credenciales regularmente
- Cambiar SECRET_KEY en cada despliegue
- Rotar API keys cada 90 días
- Usar AWS IAM roles en lugar de credenciales cuando sea posible

### 4. Separar entornos
- Usar diferentes bases de datos para dev/prod/test
- Usar diferentes buckets S3 para cada entorno
- Nunca usar credenciales de producción en desarrollo

## 🚀 Configuración por Entornos

### Desarrollo
```bash
FLASK_ENV=development
DEBUG=True
DB_NAME=cv_analyzer_dev
# APIs opcionales para desarrollo
```

### Producción
```bash
FLASK_ENV=production
DEBUG=False
DB_NAME=cv_analyzer_prod
# Todas las APIs requeridas
# SECRET_KEY debe ser muy segura
```

### Testing
```bash
FLASK_ENV=testing
DEBUG=True
DB_NAME=cv_analyzer_test
# Usar datos de prueba
```

## 🔍 Validación de Configuración

Puedes validar tu configuración ejecutando:

```bash
# Validar configuración completa
python -c "from config_manager import get_config, validate_full_config; config = get_config(); print(validate_full_config(config))"

# Ejecutar tests de configuración
python test_config_validation.py

# Verificar conexión a base de datos
python check_users_db.py

# Probar configuración de email
python test_smtp.py
```

## ❗ Solución de Problemas

### Error: "Variables de entorno faltantes"
- Verificar que el archivo `.env` existe
- Verificar que todas las variables requeridas están configuradas
- Verificar que no hay espacios extra en los nombres de variables

### Error: "SECRET_KEY insegura para producción"
- Generar una nueva clave: `python -c "import secrets; print(secrets.token_urlsafe(32))"`
- Asegurar que tiene al menos 32 caracteres
- No usar claves que empiecen con 'dev-'

### Error de conexión a base de datos
- Verificar que PostgreSQL está ejecutándose
- Verificar credenciales de base de datos
- Verificar que la base de datos existe

### Error de APIs de IA
- Verificar que las API keys son válidas
- Verificar que no han expirado
- Verificar límites de uso

## 📞 Soporte

Si tienes problemas con la configuración:

1. Revisar logs de la aplicación
2. Ejecutar tests de validación
3. Verificar documentación de cada servicio
4. Consultar archivos de ejemplo en el proyecto