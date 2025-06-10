# ARmind CVs 🚀

Aplicación web inteligente para análisis de currículums con IA y búsqueda automatizada de empleos.

## ✨ Características

- 🤖 **Análisis de CV con IA**: Utiliza OpenAI GPT para análisis detallado de currículums
- 🔍 **Búsqueda de empleos**: Integración con 8 portales laborales (LinkedIn, Indeed, ComputTrabajo, etc.)
- 👥 **Sistema de usuarios**: Registro, autenticación y verificación por email
- 📊 **Dashboard interactivo**: Estadísticas y gestión de análisis
- 📄 **Generación de reportes**: Exportación a PDF de análisis
- 🛡️ **Panel de administración**: Gestión completa del sistema

## 🛠️ Tecnologías

- **Backend**: Flask (Python)
- **Base de datos**: PostgreSQL
- **IA**: OpenAI GPT-3.5/4
- **Frontend**: Bootstrap 5, HTML/CSS/JavaScript
- **Web Scraping**: BeautifulSoup, Selenium
- **PDF**: ReportLab, PyPDF2

## 📋 Requisitos

- Python 3.8+
- PostgreSQL 12+
- Cuenta de OpenAI API
- Cuenta de email (Gmail recomendado)

## 🚀 Instalación

### 1. Clonar el repositorio
```bash
git clone https://github.com/tu-usuario/cv-analyzer-pro.git
cd cv-analyzer-pro
```

### 2. Crear entorno virtual
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar PostgreSQL
```sql
CREATE DATABASE cv_analyzer;
CREATE USER cv_app_user WITH PASSWORD 'tu_password_segura';
GRANT ALL PRIVILEGES ON DATABASE cv_analyzer TO cv_app_user;
```

### 5. Configurar variables de entorno
```bash
# Copiar archivo de ejemplo
cp .env.example .env

# Editar .env con tus credenciales
```

**Variables requeridas en .env:**
- `DB_PASSWORD`: Contraseña de PostgreSQL
- `OPENAI_API_KEY`: Tu API key de OpenAI
- `EMAIL_USER`: Tu email para verificaciones
- `EMAIL_PASSWORD`: App password de tu email
- `SECRET_KEY`: Clave secreta para Flask

### 6. Inicializar base de datos
```bash
python create_database.py
```

### 7. Ejecutar la aplicación
```bash
python app.py
```

La aplicación estará disponible en `http://localhost:5000`

## 📁 Estructura del Proyecto

```
cv-analyzer-pro/
├── app.py                    # Aplicación principal
├── database_config.py        # Configuración de BD
├── job_search_service.py     # Servicio de búsqueda
├── secure_config.py          # Configuración segura
├── apis_job/                 # APIs de portales laborales
│   ├── base_api.py          # Clase base
│   ├── linkedin.py          # API LinkedIn
│   ├── indeed.py            # API Indeed
│   └── ...
├── templates/               # Plantillas HTML
├── static/                  # Archivos estáticos
├── uploads/                 # CVs subidos (git ignored)
└── requirements.txt         # Dependencias
```

## 🔧 Configuración Adicional

### OpenAI API
1. Crear cuenta en [OpenAI](https://platform.openai.com/)
2. Generar API key
3. Agregar a `.env`: `OPENAI_API_KEY=sk-...`

### Email (Gmail)
1. Habilitar verificación en 2 pasos
2. Generar App Password
3. Configurar en `.env`

### Portales de Empleo
Algunos portales requieren configuración adicional:
- **Indeed**: API oficial disponible
- **LinkedIn**: Requiere configuración especial
- **Otros**: Web scraping automático

## 🚀 Despliegue

### Heroku
```bash
# Instalar Heroku CLI
heroku create tu-app-name
heroku addons:create heroku-postgresql:hobby-dev
heroku config:set OPENAI_API_KEY=tu_key
# ... otras variables
git push heroku main
```

### Docker
```bash
# Construir imagen
docker build -t cv-analyzer-pro .

# Ejecutar contenedor
docker run -p 5000:5000 --env-file .env cv-analyzer-pro
```

## 📖 Uso

1. **Registro**: Crear cuenta y verificar email
2. **Subir CV**: Cargar archivo PDF o DOCX
3. **Análisis**: La IA analizará el CV automáticamente
4. **Búsqueda**: Buscar empleos compatibles
5. **Reportes**: Descargar análisis en PDF

## 🤝 Contribuir

1. Fork el proyecto
2. Crear rama feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crear Pull Request

## 📝 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para detalles.

## 🆘 Soporte

- 📧 Email: tu-email@ejemplo.com
- 🐛 Issues: [GitHub Issues](https://github.com/tu-usuario/cv-analyzer-pro/issues)
- 📖 Documentación: Ver archivos MD en el repositorio

## 🙏 Agradecimientos

- OpenAI por la API de GPT
- Comunidad de Flask
- Contribuidores del proyecto

---

⭐ **¡Si te gusta el proyecto, dale una estrella!** ⭐