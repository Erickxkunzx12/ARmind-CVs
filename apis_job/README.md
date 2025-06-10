# APIs de Portales de Empleo

Este módulo contiene implementaciones separadas para extraer ofertas de empleo de diferentes portales laborales. Cada API está en su propio archivo para evitar conflictos y facilitar el desarrollo modular.

## 🌟 Portales Soportados

| Portal | Archivo | Clase | País Principal |
|--------|---------|-------|----------------|
| LinkedIn | `linkedin.py` | `LinkedInAPI` | Global |
| ComputTrabajo | `computrabajo.py` | `ComputrabajoAPI` | Latinoamérica |
| Indeed ⭐ **API Oficial Soportada** | `indeed.py` | `IndeedAPI` | Global |
| ChileTrabajo | `chiletrabajo.py` | `ChileTrabajoAPI` | Chile |
| Bolsa Nacional de Empleo | `bolsa_nacional.py` | `BolsaNacionalAPI` | Colombia |
| Empleos Públicos | `empleos_publicos.py` | `EmpleosPublicosAPI` | Colombia |
| Laborum | `laborum.py` | `LaborumAPI` | Chile |
| Trabajando.com | `trabajando.py` | `TrabajandoAPI` | Argentina |

## 📁 Estructura del Módulo

```
apis_job/
├── __init__.py              # Importaciones y funciones de utilidad
├── base_api.py              # Clase base abstracta
├── linkedin.py              # API de LinkedIn
├── computrabajo.py          # API de ComputTrabajo
├── indeed.py                # API de Indeed
├── chiletrabajo.py          # API de ChileTrabajo
├── bolsa_nacional.py        # API de Bolsa Nacional de Empleo
├── empleos_publicos.py      # API de Empleos Públicos
├── laborum.py               # API de Laborum
├── trabajando.py            # API de Trabajando.com
├── example_usage.py         # Ejemplos de uso
└── README.md                # Esta documentación
```

## 🚀 Uso Básico

### Importar APIs

```python
# Importar APIs individuales
from apis_job import LinkedInAPI, ComputrabajoAPI, IndeedAPI

# Importar funciones de utilidad
from apis_job import get_api_instance, get_all_apis
```

### Indeed con API Oficial (Recomendado)

```python
from apis_job import IndeedAPI

# Opción 1: Con credenciales OAuth (API oficial)
indeed_api = IndeedAPI(
    client_id="tu_client_id",
    client_secret="tu_client_secret"
)
jobs = indeed_api.search_jobs("python developer", "Colombia", limit=10)

# Opción 2: Sin credenciales (web scraping fallback)
indeed_api = IndeedAPI()
jobs = indeed_api.search_jobs("python developer", "Colombia", limit=10)
```

### Otras APIs

```python
# Crear instancia
linkedin_api = LinkedInAPI()

# Buscar empleos
jobs = linkedin_api.search_jobs(
    query="desarrollador python",
    location="Colombia",
    limit=10
)

# Mostrar resultados
for job in jobs:
    print(f"{job['title']} - {job['company']} ({job['location']})")
    print(f"URL: {job['url']}")
    print(f"Descripción: {job['description'][:100]}...")
    print()
```

### Usar múltiples APIs

```python
# Obtener todas las APIs
all_apis = get_all_apis()

# Buscar en todas
all_jobs = []
for api_name, api_instance in all_apis.items():
    try:
        jobs = api_instance.search_jobs("desarrollador", "Colombia", limit=5)
        for job in jobs:
            job['source'] = api_instance.name
            all_jobs.append(job)
    except Exception as e:
        print(f"Error en {api_name}: {e}")

print(f"Total empleos encontrados: {len(all_jobs)}")
```

### Usar función de utilidad

```python
# Obtener API por nombre
api = get_api_instance('linkedin')
jobs = api.search_jobs("analista", "Chile")
```

## 📋 Estructura de Datos

Cada trabajo devuelto tiene la siguiente estructura:

```python
{
    'title': str,           # Título del trabajo
    'company': str,         # Nombre de la empresa
    'location': str,        # Ubicación
    'description': str,     # Descripción del trabajo
    'url': str,            # URL de la oferta
    'salary': str,         # Salario (opcional)
    'posted_date': str,    # Fecha de publicación (opcional)
    'job_type': str,       # Tipo de trabajo (opcional)
    'source': str          # Portal de origen
}
```

## 🔧 Métodos Disponibles

Todas las APIs heredan de `BaseJobAPI` y tienen estos métodos:

### `search_jobs(query, location="", limit=10)`
Busca empleos en el portal.

**Parámetros:**
- `query` (str): Término de búsqueda
- `location` (str): Ubicación (opcional)
- `limit` (int): Número máximo de resultados

**Retorna:** Lista de diccionarios con información de empleos

### `get_job_details(job_url)`
Obtiene detalles adicionales de un trabajo específico.

**Parámetros:**
- `job_url` (str): URL del trabajo

**Retorna:** Diccionario con detalles adicionales

### `build_search_url(query, location="")`
Construye la URL de búsqueda para el portal.

### `get_alternative_urls(query, location="")`
Obtiene URLs alternativas para mejorar las búsquedas.

## 🛠️ Características Técnicas

### Clase Base (`BaseJobAPI`)
- Manejo de sesiones HTTP con user agents aleatorios
- Delays automáticos entre requests
- Parsing robusto de HTML
- Normalización de texto
- Validación de datos
- Manejo de errores

### Funcionalidades Comunes
- **Anti-blocking**: User agents rotativos y delays
- **Robustez**: Múltiples selectores CSS para cada elemento
- **Flexibilidad**: URLs alternativas para mejorar resultados
- **Validación**: Verificación de datos antes de retornar
- **Logging**: Información de debug y errores

## 📝 Ejemplos Avanzados

### Búsqueda en paralelo

```python
import concurrent.futures
from apis_job import get_all_apis

def search_in_api(api_data):
    api_name, api_instance = api_data
    try:
        return api_instance.search_jobs("programador", "Colombia", limit=5)
    except Exception as e:
        print(f"Error en {api_name}: {e}")
        return []

# Búsqueda en paralelo
all_apis = get_all_apis()
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
    results = list(executor.map(search_in_api, all_apis.items()))

# Combinar resultados
all_jobs = []
for jobs in results:
    all_jobs.extend(jobs)

print(f"Total empleos encontrados: {len(all_jobs)}")
```

### Filtrado y análisis

```python
from collections import Counter
from apis_job import get_all_apis

# Buscar empleos
all_apis = get_all_apis()
all_jobs = []

for api_name, api_instance in all_apis.items():
    jobs = api_instance.search_jobs("desarrollador", limit=10)
    for job in jobs:
        job['source'] = api_instance.name
        all_jobs.append(job)

# Análisis por ubicación
locations = [job['location'] for job in all_jobs]
location_counts = Counter(locations)
print("Empleos por ubicación:")
for location, count in location_counts.most_common(5):
    print(f"  {location}: {count}")

# Análisis por fuente
sources = [job['source'] for job in all_jobs]
source_counts = Counter(sources)
print("\nEmpleos por portal:")
for source, count in source_counts.items():
    print(f"  {source}: {count}")

# Filtrar por salario
jobs_with_salary = [job for job in all_jobs if job.get('salary')]
print(f"\nEmpleos con información salarial: {len(jobs_with_salary)}")
```

## ⚠️ Consideraciones Importantes

1. **Rate Limiting**: Las APIs incluyen delays automáticos para evitar ser bloqueadas
2. **Robots.txt**: Respeta las políticas de cada portal
3. **Términos de Uso**: Asegúrate de cumplir con los términos de cada portal
4. **APIs Oficiales**: Algunos portales pueden requerir APIs oficiales para acceso completo
5. **Estructura HTML**: Los selectores pueden cambiar si los portales actualizan su estructura

## Configuración de Indeed Job Sync API Oficial

### ⭐ Ventajas de la API Oficial

- **Datos oficiales y actualizados** en tiempo real
- **Mayor estabilidad** sin riesgo de bloqueos
- **Acceso a metadatos** adicionales de empleos
- **Soporte oficial** de Indeed
- **Rate limits más altos**

### Pasos para Configurar

1. **Regístrate como Partner de Indeed**
   - Visita: https://partners.indeed.com/
   - Completa el proceso de registro

2. **Crea una Aplicación**
   - Accede al Partner Console
   - Crea una nueva aplicación
   - Configura los scopes requeridos:
     - `employer_access`
     - `employer_hosted_job`

3. **Obtén tus Credenciales OAuth**
   - Client ID
   - Client Secret

4. **Configura en tu Código**
   ```python
   from apis_job import IndeedAPI
   
   # Con credenciales OAuth
   indeed_api = IndeedAPI(
       client_id="tu_client_id_real",
       client_secret="tu_client_secret_real"
   )
   
   # La API automáticamente:
   # - Obtiene el access token
   # - Usa GraphQL para consultas
   # - Fallback a web scraping si falla
   ```

5. **Archivo de Configuración (Recomendado)**
   ```python
   # config.py
   INDEED_CONFIG = {
       'client_id': 'tu_client_id',
       'client_secret': 'tu_client_secret'
   }
   
   # uso.py
   from config import INDEED_CONFIG
   from apis_job import IndeedAPI
   
   indeed_api = IndeedAPI(**INDEED_CONFIG)
   ```

### Características Técnicas

- **OAuth 2.0**: Autenticación automática
- **GraphQL**: Consultas eficientes
- **Fallback automático**: Web scraping si la API falla
- **Rate limiting**: Manejo inteligente de límites
- **Error handling**: Recuperación automática de errores

## 🔄 Mantenimiento

Para mantener las APIs actualizadas:

1. **Monitorear cambios**: Los portales pueden cambiar su estructura HTML
2. **Actualizar selectores**: Modificar los selectores CSS según sea necesario
3. **Probar regularmente**: Ejecutar `example_usage.py` para verificar funcionamiento
4. **Logs de error**: Revisar logs para identificar problemas
5. **Indeed API**: Mantener credenciales OAuth actualizadas

## 🚀 Ejecución de Ejemplos

```bash
# Ejecutar ejemplos
python apis_job/example_usage.py
```

## 📞 Soporte

Para reportar problemas o sugerir mejoras:
1. Verificar que el portal objetivo no haya cambiado su estructura
2. Revisar los logs de error
3. Probar con diferentes términos de búsqueda
4. Documentar el comportamiento esperado vs actual

---

**Nota**: Este módulo está diseñado para uso educativo y de desarrollo. Asegúrate de cumplir con los términos de uso de cada portal y considera usar APIs oficiales cuando estén disponibles.