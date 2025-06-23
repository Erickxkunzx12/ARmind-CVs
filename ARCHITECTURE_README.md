# CV Analyzer - Nueva Arquitectura Modular

## 🏗️ Descripción de la Arquitectura

Esta es una refactorización completa del CV Analyzer que implementa una arquitectura modular, escalable y mantenible. La nueva estructura separa las responsabilidades en módulos específicos y sigue las mejores prácticas de desarrollo.

## 📁 Estructura del Proyecto

```
WEB ARMIND/
├── src/                          # Código fuente principal
│   ├── __init__.py              # Inicialización del paquete
│   ├── config.py                # Configuración centralizada
│   ├── core/                    # Lógica de negocio principal
│   │   ├── __init__.py
│   │   ├── models.py            # Modelos de datos
│   │   ├── database.py          # Gestión de base de datos
│   │   └── ai_services.py       # Servicios de IA
│   ├── utils/                   # Utilidades
│   │   ├── __init__.py
│   │   ├── file_utils.py        # Manejo de archivos
│   │   └── validation.py        # Validaciones
│   └── services/                # Servicios de aplicación
│       ├── __init__.py
│       ├── auth_service.py      # Autenticación
│       ├── file_service.py      # Gestión de archivos
│       ├── cv_analysis_service.py # Análisis de CVs
│       └── web_routes.py        # Rutas web
├── static/                      # Archivos estáticos
├── templates/                   # Plantillas HTML
├── uploads/                     # Archivos subidos
├── app.py                       # Aplicación principal (legacy)
├── app_new.py                   # Nueva aplicación modular
├── migrate_to_new_architecture.py # Script de migración
├── finalize_migration.py        # Script de migración final
├── requirements.txt             # Dependencias
├── .env                         # Variables de entorno
└── README.md                    # Documentación
```

## 🔧 Componentes Principales

### 1. Configuración (`src/config.py`)
- **Propósito**: Centralizar toda la configuración de la aplicación
- **Características**:
  - Configuración por entornos (desarrollo, producción, testing)
  - Carga desde variables de entorno
  - Validación de configuración
  - Configuraciones específicas para DB, IA, archivos y seguridad

### 2. Modelos de Datos (`src/core/models.py`)
- **Propósito**: Definir estructuras de datos consistentes
- **Incluye**:
  - `CVAnalysisResult`: Resultados de análisis
  - `UserProfile`: Perfiles de usuario
  - `CVDocument`: Documentos de CV
  - `JobSearchResult`: Resultados de búsqueda
  - Enums para tipos de análisis y proveedores de IA

### 3. Base de Datos (`src/core/database.py`)
- **Propósito**: Centralizar operaciones de base de datos
- **Características**:
  - Gestión de conexiones
  - Operaciones CRUD para usuarios y CVs
  - Manejo de transacciones
  - Pool de conexiones

### 4. Servicios de IA (`src/core/ai_services.py`)
- **Propósito**: Integración con APIs de IA
- **Proveedores soportados**:
  - OpenAI (GPT)
  - Anthropic (Claude)
  - Google (Gemini)
- **Características**:
  - Manejo de errores robusto
  - Parsing de respuestas JSON
  - Configuración flexible de modelos

### 5. Servicios de Aplicación

#### Autenticación (`src/services/auth_service.py`)
- Registro y login de usuarios
- Validación de credenciales
- Gestión de perfiles
- Cambio de contraseñas
- Estadísticas de usuario

#### Gestión de Archivos (`src/services/file_service.py`)
- Procesamiento de archivos subidos
- Extracción de texto (PDF, DOCX, TXT)
- Validación de archivos
- Gestión de almacenamiento
- Estadísticas de archivos

#### Análisis de CVs (`src/services/cv_analysis_service.py`)
- Coordinación de análisis con diferentes IAs
- Validación de resultados
- Almacenamiento de análisis
- Historial de análisis
- Resúmenes y estadísticas

#### Rutas Web (`src/services/web_routes.py`)
- Todas las rutas Flask organizadas
- Decoradores de autenticación
- Manejo de formularios
- APIs REST
- Manejo de errores

### 6. Utilidades

#### Manejo de Archivos (`src/utils/file_utils.py`)
- Extracción de texto de diferentes formatos
- Validación de tipos y tamaños
- Sanitización de nombres
- Gestión de archivos temporales

#### Validaciones (`src/utils/validation.py`)
- Validación de emails
- Validación de contraseñas
- Validación de contenido de CVs
- Sanitización de inputs
- Validación de archivos

## 🚀 Instalación y Configuración

### 1. Preparar el Entorno

```bash
# Instalar dependencias
pip install -r requirements.txt

# Copiar configuración de ejemplo
cp .env.example .env
```

### 2. Configurar Variables de Entorno

Editar el archivo `.env`:

```env
# Base de datos
DB_HOST=localhost
DB_PORT=3306
DB_NAME=cv_analyzer
DB_USER=root
DB_PASSWORD=tu_password

# APIs de IA
OPENAI_API_KEY=tu_clave_openai
ANTHROPIC_API_KEY=tu_clave_anthropic
GEMINI_API_KEY=tu_clave_gemini

# Aplicación
SECRET_KEY=clave_secreta_segura
DEBUG=false
ENVIRONMENT=production

# Archivos
MAX_FILE_SIZE_MB=10
UPLOAD_FOLDER=uploads
```

### 3. Inicializar Base de Datos

```bash
# Usando Flask CLI
flask init-db

# O directamente con Python
python -c "from src.core.database import init_database; from src.config import get_config; init_database(get_config().database)"
```

### 4. Ejecutar la Aplicación

```bash
# Modo desarrollo
python app_new.py

# Modo producción
ENVIRONMENT=production python app_new.py
```

## 🔄 Migración desde la Versión Anterior

### Opción 1: Migración Automática

```bash
# Ejecutar script de migración
python migrate_to_new_architecture.py

# Finalizar migración
python finalize_migration.py
```

### Opción 2: Migración Manual

1. **Crear backup**:
   ```bash
   cp app.py app_legacy.py
   cp -r static static_backup
   cp -r templates templates_backup
   ```

2. **Activar nueva aplicación**:
   ```bash
   mv app_new.py app.py
   ```

3. **Configurar entorno**:
   - Crear archivo `.env` con las configuraciones necesarias
   - Instalar nuevas dependencias si es necesario

4. **Probar funcionamiento**:
   ```bash
   python app.py
   ```

## 🧪 Comandos de Desarrollo

### Comandos Flask CLI

```bash
# Inicializar base de datos
flask init-db

# Probar APIs de IA
flask test-apis

# Crear usuario administrador
flask create-admin
```

### Comandos de Testing

```bash
# Probar configuración
python -c "from src.config import get_config; print(get_config().validate())"

# Probar servicios
python -c "from src.services.auth_service import get_auth_service; print('Auth service OK')"

# Probar base de datos
python -c "from src.core.database import get_db_service; print(get_db_service().test_connection())"
```

## 📊 Beneficios de la Nueva Arquitectura

### 1. **Modularidad**
- Código organizado en módulos específicos
- Fácil mantenimiento y extensión
- Reutilización de componentes

### 2. **Escalabilidad**
- Servicios independientes
- Fácil adición de nuevos proveedores de IA
- Configuración flexible por entorno

### 3. **Mantenibilidad**
- Separación clara de responsabilidades
- Código más legible y documentado
- Fácil testing de componentes individuales

### 4. **Robustez**
- Manejo de errores mejorado
- Validaciones centralizadas
- Logging estructurado

### 5. **Seguridad**
- Validaciones de entrada robustas
- Configuración de seguridad centralizada
- Manejo seguro de credenciales

## 🔧 Personalización y Extensión

### Agregar Nuevo Proveedor de IA

1. **Actualizar modelos** (`src/core/models.py`):
   ```python
   class AIProviders:
       NUEVO_PROVEEDOR = "nuevo_proveedor"
   ```

2. **Implementar servicio** (`src/core/ai_services.py`):
   ```python
   def analyze_cv_with_nuevo_proveedor(cv_text, analysis_type):
       # Implementación
       pass
   ```

3. **Actualizar configuración** (`src/config.py`):
   ```python
   @dataclass
   class AIConfig:
       nuevo_proveedor_api_key: str = ''
   ```

### Agregar Nuevo Tipo de Análisis

1. **Actualizar modelos**:
   ```python
   class AnalysisTypes:
       NUEVO_TIPO = "nuevo_tipo"
   ```

2. **Actualizar prompts** (`src/core/ai_services.py`):
   ```python
   def get_analysis_prompt(analysis_type):
       prompts = {
           "nuevo_tipo": "Prompt para nuevo análisis..."
       }
   ```

### Agregar Nueva Funcionalidad

1. **Crear servicio** en `src/services/`
2. **Agregar rutas** en `src/services/web_routes.py`
3. **Actualizar templates** si es necesario
4. **Agregar validaciones** en `src/utils/validation.py`

## 🐛 Troubleshooting

### Problemas Comunes

1. **Error de importación**:
   - Verificar que `src/` esté en el PYTHONPATH
   - Verificar que todos los `__init__.py` existan

2. **Error de base de datos**:
   - Verificar configuración en `.env`
   - Verificar que la base de datos exista
   - Ejecutar `flask init-db`

3. **Error de APIs de IA**:
   - Verificar claves de API en `.env`
   - Verificar conectividad a internet
   - Verificar límites de API

4. **Error de archivos**:
   - Verificar permisos del directorio `uploads/`
   - Verificar tamaño máximo de archivo
   - Verificar extensiones permitidas

### Logs y Debugging

- Los logs se guardan en `app.log`
- Usar `DEBUG=true` para más información
- Verificar logs de migración en `migration.log`

## 📚 Documentación Adicional

- [Configuración de APIs de IA](docs/ai_setup.md)
- [Guía de Desarrollo](docs/development.md)
- [Deployment en Producción](docs/deployment.md)
- [API Reference](docs/api_reference.md)

## 🤝 Contribución

Para contribuir al proyecto:

1. Fork el repositorio
2. Crear rama de feature: `git checkout -b feature/nueva-funcionalidad`
3. Commit cambios: `git commit -am 'Agregar nueva funcionalidad'`
4. Push a la rama: `git push origin feature/nueva-funcionalidad`
5. Crear Pull Request

## 📄 Licencia

Este proyecto está bajo la licencia MIT. Ver `LICENSE` para más detalles.

---

**Nota**: Esta nueva arquitectura es completamente compatible con la funcionalidad existente. La migración preserva todos los datos y funcionalidades mientras mejora significativamente la estructura del código.