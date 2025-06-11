#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de limpieza y organización del proyecto ARMind CVs
Este script ayuda a organizar el proyecto y eliminar archivos duplicados
"""

import os
import shutil
from datetime import datetime

def create_backup_folder():
    """Crear carpeta de respaldo para archivos antiguos"""
    backup_folder = "backup_old_files"
    if not os.path.exists(backup_folder):
        os.makedirs(backup_folder)
        print(f"✅ Carpeta de respaldo creada: {backup_folder}")
    return backup_folder

def move_old_files():
    """Mover archivos antiguos y duplicados a la carpeta de respaldo"""
    backup_folder = create_backup_folder()
    
    # Lista de archivos a mover (versiones antiguas y duplicados)
    files_to_move = [
        "app_backup.py",
        "app_fixed.py",
        "app_new.py",
        "app_problem_20250602_134213.py",
        "app_problem_20250602_135142.py",
        "database_config_new.py",
        "minimal_app.py",
        "backup_app.py",
        "restore_app.py",
        "check_routes.py",
        "connection_with_encoding.py",
        "direct_connection.py",
        "test_connection.py",
        "test_connection_encoding.py",
        "test_connection_new.py",
        "test_db.py",
        "test_db_connection.py",
        "test_delete.py",
        "test_email_verification.py",
        "cv_analyzer.db"  # Base de datos SQLite antigua
    ]
    
    moved_files = []
    for file in files_to_move:
        if os.path.exists(file):
            try:
                shutil.move(file, os.path.join(backup_folder, file))
                moved_files.append(file)
                print(f"📦 Movido: {file}")
            except Exception as e:
                print(f"❌ Error moviendo {file}: {e}")
    
    return moved_files

def create_gitignore():
    """Crear archivo .gitignore para el proyecto"""
    gitignore_content = """# Archivos de Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
PIPFILE.lock

# Entornos virtuales
venv/
venv_fix/
ENV/
env/
.venv

# Variables de entorno
.env
.env.local
.env.production

# Archivos de configuración sensibles
email_config.py
config_local.py

# Archivos de base de datos
*.db
*.sqlite
*.sqlite3

# Archivos subidos por usuarios
uploads/
static/temp_jobs/

# Logs
*.log
logs/

# Archivos temporales
*.tmp
*.temp
.DS_Store
Thumbs.db

# IDEs
.vscode/
.idea/
*.swp
*.swo

# Archivos de respaldo
backup_old_files/
*.backup
*.bak

# Certificados y claves
*.pem
*.key
*.crt

# Archivos de fuentes (si son muy grandes)
# fonts/*.ttf
"""
    
    with open('.gitignore', 'w', encoding='utf-8') as f:
        f.write(gitignore_content)
    print("✅ Archivo .gitignore creado")

def create_readme():
    """Crear README actualizado para el proyecto"""
    readme_content = """# ARMind CVs

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
venv\Scripts\activate
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
"""
    
    with open('README.md', 'w', encoding='utf-8') as f:
        f.write(readme_content)
    print("✅ README.md actualizado")

def create_requirements_updated():
    """Crear requirements.txt actualizado y limpio"""
    requirements_content = """# Framework web
Flask==2.3.3
Werkzeug==2.3.7

# Base de datos
psycopg2-binary==2.9.10

# IA y procesamiento
openai==0.28.1

# Procesamiento de documentos
PyPDF2==3.0.1
python-docx==0.8.11

# Generación de PDF
reportlab==4.0.4
WeasyPrint==60.1

# Web scraping
requests==2.31.0
beautifulsoup4==4.12.2
selenium==4.15.2
lxml==4.9.3

# Visualización
plotly==5.17.0
Pillow==10.0.1

# Utilidades
python-dotenv==1.0.0
"""
    
    with open('requirements_updated.txt', 'w', encoding='utf-8') as f:
        f.write(requirements_content)
    print("✅ requirements_updated.txt creado")

def main():
    """Función principal del script de limpieza"""
    print("🧹 Iniciando limpieza del proyecto ARMind CVs...\n")
    
    # Crear respaldo de archivos antiguos
    moved_files = move_old_files()
    
    # Crear archivos de configuración
    create_gitignore()
    create_readme()
    create_requirements_updated()
    
    print(f"\n✅ Limpieza completada!")
    print(f"📦 {len(moved_files)} archivos movidos a backup_old_files/")
    print("\n📋 Próximos pasos:")
    print("1. Ejecutar: python secure_config.py (para crear .env.example)")
    print("2. Copiar .env.example como .env y configurar tus valores")
    print("3. Usar: python app_fixed_secure.py (versión segura)")
    print("4. Instalar dependencias actualizadas: pip install -r requirements_updated.txt")
    
if __name__ == '__main__':
    main()