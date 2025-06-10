# CV Analyzer Pro

Aplicación web para análisis de currículums y búsqueda de empleos compatible.

## 🚀 Características

- ✅ Análisis de CV con IA (OpenAI GPT)
- ✅ Búsqueda de empleos compatible
- ✅ Sistema de usuarios con verificación por email
- ✅ Generación de reportes en PDF
- ✅ Interfaz web moderna y responsive

## 📋 Requisitos

- Python 3.8+
- PostgreSQL 12+
- Cuenta de OpenAI (para análisis de CV)
- Cuenta de email (Gmail recomendado)

## 🛠️ Instalación

### 1. Clonar el repositorio
```bash
git clone <url-del-repositorio>
cd WEB_ARMIND
```

### 2. Crear entorno virtual
```bash
python -m venv venv
# En Windows:
venv\Scriptsctivate
# En Linux/Mac:
source venv/bin/activate
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar base de datos PostgreSQL
```sql
CREATE DATABASE cv_analyzer;
CREATE USER cv_app_user WITH PASSWORD 'tu_password_segura';
GRANT ALL PRIVILEGES ON DATABASE cv_analyzer TO cv_app_user;
```

### 5. Configurar variables de entorno
```bash
# Crear archivo .env basado en .env.example
cp .env.example .env
# Editar .env con tus configuraciones
```

### 6. Ejecutar la aplicación
```bash
# Usando la versión segura (recomendado)
python app_fixed_secure.py

# O la versión original
python app.py
```

## 🔧 Configuración

### Variables de entorno requeridas (.env):

```env
# Base de datos
DB_HOST=localhost
DB_NAME=cv_analyzer
DB_USER=cv_app_user
DB_PASSWORD=tu_password_segura
DB_PORT=5432

# OpenAI
OPENAI_API_KEY=sk-...

# Email
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_USER=tu_email@gmail.com
EMAIL_PASSWORD=tu_app_password
EMAIL_USE_TLS=True

# Flask
SECRET_KEY=tu_clave_secreta_muy_segura
FLASK_DEBUG=False
```

## 📁 Estructura del proyecto

```
WEB_ARMIND/
├── app.py                    # Aplicación principal (original)
├── app_fixed_secure.py       # Versión segura (recomendada)
├── secure_config.py          # Configuración segura
├── database_config.py        # Configuración de BD
├── job_search_service.py     # Servicio de búsqueda de empleos
├── requirements.txt          # Dependencias
├── templates/               # Plantillas HTML
├── static/                  # Archivos estáticos
├── uploads/                 # Archivos subidos
├── fonts/                   # Fuentes para PDF
└── apis_job/               # APIs de búsqueda de empleo
```

## 🔒 Seguridad

### Problemas solucionados en `app_fixed_secure.py`:

- ✅ Eliminadas credenciales hardcodeadas
- ✅ Configuración mediante variables de entorno
- ✅ Validación mejorada de entrada
- ✅ Logging de seguridad
- ✅ Manejo de errores mejorado
- ✅ Modo debug deshabilitado por defecto

## 🚨 Problemas conocidos del archivo original (app.py)

- ❌ API keys expuestas en el código
- ❌ Contraseñas hardcodeadas
- ❌ Modo debug habilitado en producción
- ❌ Falta validación de entrada
- ❌ Manejo de errores insuficiente

## 📝 Uso

1. Registrarse en la aplicación
2. Verificar email
3. Subir CV en formato PDF/DOC
4. Obtener análisis con IA
5. Buscar empleos compatibles
6. Descargar reportes

## 🤝 Contribuir

1. Fork el proyecto
2. Crear rama para feature (`git checkout -b feature/AmazingFeature`)
3. Commit cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para detalles.

## 🆘 Soporte

Si encuentras algún problema:

1. Revisa la documentación
2. Busca en issues existentes
3. Crea un nuevo issue con detalles del problema

## 🔄 Migración desde versión anterior

```bash
# Ejecutar script de limpieza
python cleanup_project.py

# Configurar variables de entorno
python secure_config.py

# Usar la nueva versión segura
python app_fixed_secure.py
```
