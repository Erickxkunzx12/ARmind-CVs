#!/usr/bin/env python3
"""Script de Inicialización del Proyecto ARMind"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
import secrets
import string
from typing import Dict, List

def generate_secret_key(length: int = 32) -> str:
    """Generar clave secreta aleatoria"""
    alphabet = string.ascii_letters + string.digits + '!@#$%^&*'
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def create_env_file():
    """Crear archivo .env con configuraciones por defecto"""
    env_content = f"""# Configuración de ARMind

# Entorno
FLASK_ENV=development
FLASK_DEBUG=True

# Seguridad
SECRET_KEY={generate_secret_key()}
JWT_SECRET_KEY={generate_secret_key()}

# Base de datos
DB_HOST=localhost
DB_PORT=5432
DB_NAME=armind_db
DB_USER=postgres
DB_PASSWORD=armind_password

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
REDIS_URL=redis://localhost:6379/0

# APIs de IA
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here

# Email
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password_here
SMTP_USE_TLS=true

# AWS S3 (opcional)
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_S3_BUCKET=your_bucket_name
AWS_REGION=us-east-1

# Configuración de archivos
UPLOAD_FOLDER=uploads
TEMP_FOLDER=temp
MAX_FILE_SIZE=16777216

# Configuración de logging
LOG_LEVEL=INFO
LOG_FORMAT=structured
LOG_DIR=logs

# Configuración de monitoreo
MONITORING_ENABLED=true
METRICS_INTERVAL=30

# Configuración de cache
CACHE_ENABLED=true
CACHE_DEFAULT_TTL=3600
CACHE_CV_ANALYSIS_TTL=3600
CACHE_JOB_SEARCH_TTL=1800

# Configuración de rendimiento
ENABLE_GZIP=true
ENABLE_ETAG=true
API_RATE_LIMIT=100/hour
MAX_WORKERS=4

# Configuración de seguridad
MAX_LOGIN_ATTEMPTS=5
LOCKOUT_DURATION=900
JWT_ACCESS_TOKEN_EXPIRES=3600
JWT_REFRESH_TOKEN_EXPIRES=2592000
"""
    
    with open('.env', 'w', encoding='utf-8') as f:
        f.write(env_content)
    
    print("✅ Archivo .env creado")

def create_directories():
    """Crear directorios necesarios"""
    directories = [
        'uploads',
        'temp',
        'logs',
        'static/css',
        'static/js',
        'static/images',
        'templates',
        'tests',
        'migrations',
        'ssl'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"📁 Directorio creado: {directory}")

def create_gitignore():
    """Crear archivo .gitignore"""
    gitignore_content = """# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# C extensions
*.so

# Distribution / packaging
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
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# PyInstaller
*.manifest
*.spec

# Installer logs
pip-log.txt
pip-delete-this-directory.txt

# Unit test / coverage reports
htmlcov/
.tox/
.nox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.py,cover
.hypothesis/
.pytest_cache/
cover/

# Translations
*.mo
*.pot

# Django stuff:
*.log
local_settings.py
db.sqlite3
db.sqlite3-journal

# Flask stuff:
instance/
.webassets-cache

# Scrapy stuff:
.scrapy

# Sphinx documentation
docs/_build/

# PyBuilder
.pybuilder/
target/

# Jupyter Notebook
.ipynb_checkpoints

# IPython
profile_default/
ipython_config.py

# pyenv
.python-version

# pipenv
Pipfile.lock

# poetry
poetry.lock

# pdm
.pdm.toml

# PEP 582
__pypackages__/

# Celery stuff
celerybeat-schedule
celerybeat.pid

# SageMath parsed files
*.sage.py

# Environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# Spyder project settings
.spyderproject
.spyproject

# Rope project settings
.ropeproject

# mkdocs documentation
/site

# mypy
.mypy_cache/
.dmypy.json
dmypy.json

# Pyre type checker
.pyre/

# pytype static type analyzer
.pytype/

# Cython debug symbols
cython_debug/

# PyCharm
.idea/

# VS Code
.vscode/

# Archivos específicos del proyecto
uploads/
temp/
logs/
ssl/
*.db
*.sqlite
*.sqlite3

# Archivos de configuración sensibles
.env.local
.env.production
.env.staging

# Archivos de Docker
.dockerignore

# Archivos de sistema
.DS_Store
Thumbs.db

# Archivos de backup
*.bak
*.backup
*.old

# Archivos temporales
*.tmp
*.temp

# Archivos de certificados
*.pem
*.key
*.crt
*.p12

# Archivos de datos
*.csv
*.xlsx
*.json
*.xml

# Archivos de media
*.pdf
*.doc
*.docx
*.jpg
*.jpeg
*.png
*.gif
*.mp4
*.avi
*.mov

# Archivos de configuración de IDE
*.swp
*.swo
*~

# Archivos de npm (si se usa)
node_modules/
package-lock.json
yarn.lock

# Archivos de Webpack
dist/
bundle.js

# Archivos de testing
.coverage
.pytest_cache/
.tox/

# Archivos de profiling
*.prof

# Archivos de cache
.cache/
*.cache

# Archivos de configuración local
config.local.py
settings.local.py

# Archivos de migración específicos
migrations/versions/

# Archivos de Celery
celerybeat-schedule.db

# Archivos de Redis
dump.rdb
appendonly.aof

# Archivos de PostgreSQL
*.sql

# Archivos de logs específicos
*.log.*
*.out
*.err

# Archivos de monitoreo
prometheus_data/
grafana_data/

# Archivos de Docker Compose
docker-compose.override.yml
"""
    
    with open('.gitignore', 'w', encoding='utf-8') as f:
        f.write(gitignore_content)
    
    print("✅ Archivo .gitignore creado")

def create_readme():
    """Crear README actualizado"""
    readme_content = """# ARMind CV Analyzer - Versión Mejorada

## 🚀 Características Principales

- **Análisis de CV con IA**: Análisis inteligente usando OpenAI, Anthropic y Gemini
- **Búsqueda de Empleos**: Scraping automatizado de múltiples portales
- **Sistema de Cache**: Redis para optimización de rendimiento
- **Monitoreo Avanzado**: Métricas con Prometheus y Grafana
- **Logging Estructurado**: Sistema de logs JSON para mejor observabilidad
- **Arquitectura Escalable**: Containerización con Docker y orquestación
- **Seguridad Mejorada**: Autenticación JWT, rate limiting y validación

## 🏗️ Arquitectura

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│     Nginx       │    │   Flask App     │    │   PostgreSQL    │
│  Load Balancer  │────│   (Gunicorn)    │────│    Database     │
│   & Reverse     │    │                 │    │                 │
│     Proxy       │    └─────────────────┘    └─────────────────┘
└─────────────────┘              │
                                 │
                    ┌─────────────────┐    ┌─────────────────┐
                    │     Redis       │    │   Prometheus    │
                    │     Cache       │    │   Monitoring    │
                    │                 │    │                 │
                    └─────────────────┘    └─────────────────┘
```

## 🛠️ Instalación y Configuración

### Opción 1: Instalación con Docker (Recomendada)

1. **Clonar el repositorio**:
   ```bash
   git clone <repository-url>
   cd WEB\ ARMIND
   ```

2. **Ejecutar script de inicialización**:
   ```bash
   python init_project.py
   ```

3. **Configurar variables de entorno**:
   Editar el archivo `.env` generado con tus credenciales:
   ```bash
   # APIs de IA
   OPENAI_API_KEY=tu_clave_openai
   ANTHROPIC_API_KEY=tu_clave_anthropic
   GEMINI_API_KEY=tu_clave_gemini
   
   # Email
   SMTP_USERNAME=tu_email@gmail.com
   SMTP_PASSWORD=tu_contraseña_app
   ```

4. **Levantar servicios con Docker**:
   ```bash
   # Servicios básicos
   docker-compose up -d
   
   # Con monitoreo (Prometheus + Grafana)
   docker-compose --profile monitoring up -d
   ```

5. **Verificar instalación**:
   - Aplicación: http://localhost
   - API Status: http://localhost/api/status
   - Métricas: http://localhost/metrics
   - Prometheus: http://localhost:9090 (si está habilitado)
   - Grafana: http://localhost:3000 (si está habilitado)

### Opción 2: Instalación Manual

1. **Crear entorno virtual**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```

2. **Instalar dependencias**:
   ```bash
   pip install -r requirements_enhanced.txt
   ```

3. **Configurar base de datos PostgreSQL**:
   ```bash
   # Crear base de datos
   createdb armind_db
   
   # Ejecutar migraciones
   flask db upgrade
   ```

4. **Configurar Redis**:
   ```bash
   # Instalar Redis
   # Ubuntu/Debian: sudo apt install redis-server
   # macOS: brew install redis
   # Windows: usar Docker o WSL
   
   # Iniciar Redis
   redis-server
   ```

5. **Ejecutar aplicación**:
   ```bash
   python app_factory.py
   ```

## 📊 Monitoreo y Métricas

### Endpoints de Salud
- `/health` - Estado básico
- `/health/detailed` - Verificación detallada
- `/health/ready` - Readiness para Kubernetes

### Métricas
- `/metrics` - Formato Prometheus
- `/metrics/json` - Formato JSON

### Logs
- `logs/armind.log` - Logs generales
- `logs/security.log` - Eventos de seguridad
- `logs/access.log` - Logs de acceso HTTP
- `logs/armind_errors.log` - Solo errores

## 🔧 Configuración Avanzada

### Variables de Entorno Principales

| Variable | Descripción | Valor por Defecto |
|----------|-------------|-------------------|
| `FLASK_ENV` | Entorno de ejecución | `development` |
| `LOG_LEVEL` | Nivel de logging | `INFO` |
| `CACHE_ENABLED` | Habilitar cache Redis | `true` |
| `MONITORING_ENABLED` | Habilitar monitoreo | `true` |
| `MAX_WORKERS` | Workers de Gunicorn | `4` |
| `API_RATE_LIMIT` | Límite de requests | `100/hour` |

### Configuración de Cache

```python
# TTL por tipo de operación
CACHE_CV_ANALYSIS_TTL=3600      # 1 hora
CACHE_JOB_SEARCH_TTL=1800       # 30 minutos
CACHE_USER_SESSION_TTL=86400    # 24 horas
```

### Configuración de Seguridad

```python
# Límites de seguridad
MAX_LOGIN_ATTEMPTS=5
LOCKOUT_DURATION=900           # 15 minutos
JWT_ACCESS_TOKEN_EXPIRES=3600  # 1 hora
PASSWORD_MIN_LENGTH=8
```

## 🧪 Testing

```bash
# Ejecutar tests
pytest

# Con cobertura
pytest --cov=.

# Tests específicos
pytest tests/test_cache.py
pytest tests/test_monitoring.py
```

## 📈 Escalabilidad

### Escalado Horizontal

1. **Múltiples instancias de la aplicación**:
   ```yaml
   # docker-compose.yml
   web:
     deploy:
       replicas: 3
   ```

2. **Load Balancer con Nginx**:
   ```nginx
   upstream armind_backend {
       server web1:5000;
       server web2:5000;
       server web3:5000;
   }
   ```

### Escalado con Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: armind-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: armind
  template:
    spec:
      containers:
      - name: armind
        image: armind:latest
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
```

## 🔒 Seguridad

### Mejores Prácticas Implementadas

- ✅ Autenticación JWT con refresh tokens
- ✅ Rate limiting por IP y endpoint
- ✅ Validación de entrada con Marshmallow
- ✅ Headers de seguridad (CORS, CSP, etc.)
- ✅ Logging de eventos de seguridad
- ✅ Encriptación de contraseñas con bcrypt
- ✅ Protección CSRF
- ✅ Validación de archivos subidos

### Configuración SSL/TLS

```bash
# Generar certificados para desarrollo
openssl req -x509 -newkey rsa:4096 -keyout ssl/key.pem -out ssl/cert.pem -days 365 -nodes
```

## 🚀 Despliegue en Producción

### Checklist de Producción

- [ ] Configurar variables de entorno de producción
- [ ] Usar certificados SSL válidos
- [ ] Configurar backup de base de datos
- [ ] Configurar monitoreo y alertas
- [ ] Configurar logs centralizados
- [ ] Implementar CI/CD pipeline
- [ ] Configurar auto-scaling
- [ ] Realizar pruebas de carga

### Variables de Entorno de Producción

```bash
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=<clave-super-secreta>
DB_PASSWORD=<contraseña-segura>
REDIS_PASSWORD=<contraseña-redis>
```

## 📚 Documentación Adicional

- [Guía de Desarrollo](docs/development.md)
- [API Documentation](docs/api.md)
- [Guía de Despliegue](docs/deployment.md)
- [Troubleshooting](docs/troubleshooting.md)

## 🤝 Contribución

1. Fork el proyecto
2. Crear rama de feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crear Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para detalles.

## 🆘 Soporte

Para soporte técnico:
- 📧 Email: soporte@armind.com
- 💬 Discord: [ARMind Community](https://discord.gg/armind)
- 📖 Wiki: [Documentación Completa](https://wiki.armind.com)

---

**ARMind CV Analyzer** - Potenciando tu búsqueda laboral con IA 🚀
"""
    
    with open('README_ENHANCED.md', 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print("✅ README mejorado creado")

def check_dependencies():
    """Verificar dependencias del sistema"""
    dependencies = {
        'docker': 'Docker para containerización',
        'docker-compose': 'Docker Compose para orquestación',
        'python': 'Python 3.8+',
        'pip': 'Gestor de paquetes Python'
    }
    
    missing = []
    
    for dep, description in dependencies.items():
        try:
            result = subprocess.run([dep, '--version'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ {dep}: {result.stdout.strip().split()[0]}")
            else:
                missing.append((dep, description))
        except FileNotFoundError:
            missing.append((dep, description))
    
    if missing:
        print("\n⚠️ Dependencias faltantes:")
        for dep, description in missing:
            print(f"  - {dep}: {description}")
        return False
    
    return True

def main():
    """Función principal de inicialización"""
    print("🚀 Inicializando proyecto ARMind...\n")
    
    # Verificar dependencias
    print("📋 Verificando dependencias del sistema...")
    if not check_dependencies():
        print("\n❌ Por favor instala las dependencias faltantes antes de continuar.")
        sys.exit(1)
    
    print("\n📁 Creando estructura de directorios...")
    create_directories()
    
    print("\n🔧 Creando archivos de configuración...")
    create_env_file()
    create_gitignore()
    create_readme()
    
    print("\n✅ Proyecto inicializado exitosamente!")
    print("\n📋 Próximos pasos:")
    print("1. Editar el archivo .env con tus credenciales")
    print("2. Ejecutar: docker-compose up -d")
    print("3. Visitar: http://localhost")
    print("\n🎉 ¡Disfruta desarrollando con ARMind!")

if __name__ == '__main__':
    main()