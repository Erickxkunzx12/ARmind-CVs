# API de Computrabajo - Documentación

Esta implementación de la API de Computrabajo soporta tanto la **API oficial** como **web scraping** como método de respaldo.

## Configuración

### Opción 1: API Oficial (Recomendada)

Para usar la API oficial de Computrabajo, necesitas credenciales proporcionadas por Computrabajo. Basado en la documentación oficial: https://github.com/rcereceda/computrabajo

```python
from apis_job.computrabajo import ComputrabajoConfig, ComputrabajoAPI

# Crear configuración
config = ComputrabajoConfig()

# Configurar credenciales
config.setup(
    username="tu_usuario_computrabajo",          # username proporcionado por Computrabajo
    password="tu_password_computrabajo",         # password proporcionado por Computrabajo
    contact_name="Tu Nombre",                    # tu nombre de contacto
    contact_email="tu_email@empresa.com",        # tu email de contacto
    contact_telephone="+57 300 123 4567",        # tu número de teléfono
    contact_url="https://tu-empresa.com",        # URL de tu empresa
    job_reference="REF-2024-001",                # tu referencia interna de oferta
    environment="production"                      # production o development
)

# Crear instancia de la API
api = ComputrabajoAPI(config)
```

### Opción 2: Solo Web Scraping

Si no tienes credenciales de la API oficial, puedes usar solo web scraping:

```python
from apis_job.computrabajo import ComputrabajoAPI

# Crear instancia sin configuración (usará web scraping)
api = ComputrabajoAPI()
```

## Uso

### Buscar Empleos

```python
# Buscar empleos
empleos = api.search_jobs("desarrollador python", "Bogotá", limit=10)

for empleo in empleos:
    print(f"Título: {empleo['title']}")
    print(f"Empresa: {empleo['company']}")
    print(f"Ubicación: {empleo['location']}")
    print(f"URL: {empleo['url']}")
    print("-" * 50)
```

### Crear Oferta de Trabajo (Solo API Oficial)

```python
# Solo disponible con API oficial configurada
if api.use_official_api:
    nueva_oferta = {
        "title": "Desarrollador Python Senior",
        "description": "Buscamos desarrollador Python con experiencia en Django y FastAPI",
        "company": "Mi Empresa Tech",
        "location": "Bogotá, Colombia",
        "salary": "$3,000,000 - $5,000,000 COP",
        "contract_type": "Tiempo completo"
    }
    
    resultado = api.create_job_offer(nueva_oferta)
    if resultado:
        print(f"Oferta creada con ID: {resultado.get('id')}")
        print(f"Estado: {resultado.get('status')}")
```

### Obtener Detalles de Oferta (Solo API Oficial)

```python
# Obtener datos de una oferta específica
if api.use_official_api:
    oferta = api.get_job_offer("12345")
    if oferta:
        print(f"Detalles de la oferta: {oferta}")
```

### Eliminar Oferta (Solo API Oficial)

```python
# Eliminar una oferta
if api.use_official_api:
    eliminada = api.delete_job_offer("12345")
    if eliminada:
        print("Oferta eliminada exitosamente")
```

## Estados de Ofertas

Según la documentación oficial, las ofertas pueden tener los siguientes estados:

- **1**: Pendiente
- **2**: Activa
- **3**: Caducada
- **4**: Eliminada
- **5**: Rechazada
- **6**: Archivada

## Funcionamiento Automático

La implementación funciona de la siguiente manera:

1. **Si tienes credenciales configuradas**: Intenta usar la API oficial primero
2. **Si la API oficial falla**: Automáticamente usa web scraping como respaldo
3. **Si no tienes credenciales**: Usa directamente web scraping

## Ejemplo Completo

```python
from apis_job.computrabajo import ComputrabajoConfig, ComputrabajoAPI

def ejemplo_completo():
    # Configurar API oficial
    config = ComputrabajoConfig()
    config.setup(
        username="mi_usuario",
        password="mi_password",
        contact_name="Juan Pérez",
        contact_email="juan@miempresa.com",
        contact_telephone="+57 300 123 4567",
        contact_url="https://miempresa.com",
        job_reference="REF-2024-001",
        environment="production"
    )
    
    # Crear API
    api = ComputrabajoAPI(config)
    
    # Buscar empleos
    print("Buscando empleos...")
    empleos = api.search_jobs("desarrollador", "Colombia", limit=5)
    
    print(f"Encontrados {len(empleos)} empleos:")
    for i, empleo in enumerate(empleos, 1):
        print(f"{i}. {empleo['title']} - {empleo['company']}")
    
    # Si está usando API oficial, crear una oferta
    if api.use_official_api:
        print("\nCreando nueva oferta...")
        nueva_oferta = {
            "title": "Desarrollador Full Stack",
            "description": "Buscamos desarrollador con experiencia en React y Node.js",
            "company": "Tech Solutions",
            "location": "Medellín, Colombia",
            "salary": "$4,000,000 COP",
            "contract_type": "Tiempo completo"
        }
        
        resultado = api.create_job_offer(nueva_oferta)
        if resultado:
            print(f"✅ Oferta creada exitosamente")
            print(f"ID: {resultado.get('id')}")
            print(f"Estado: {resultado.get('status')}")
        else:
            print("❌ Error creando la oferta")
    else:
        print("\n⚠️ API oficial no configurada - Solo búsqueda disponible")

if __name__ == "__main__":
    ejemplo_completo()
```

## Notas Importantes

1. **Credenciales**: Las credenciales deben ser proporcionadas por Computrabajo
2. **Fallback Automático**: Si la API oficial falla, automáticamente usa web scraping
3. **Funcionalidades Limitadas**: Crear, obtener y eliminar ofertas solo está disponible con la API oficial
4. **Entornos**: Puedes usar `production` o `development` según tus necesidades
5. **Rate Limiting**: La implementación incluye delays automáticos para evitar bloqueos

## Solución de Problemas

### Error de Autenticación
- Verifica que las credenciales sean correctas
- Asegúrate de que el entorno (`production`/`development`) sea el correcto
- Contacta a Computrabajo si persisten los problemas

### No se Encuentran Empleos
- La API automáticamente usará web scraping como respaldo
- Verifica la conectividad a internet
- Prueba con diferentes términos de búsqueda

### Error al Crear Ofertas
- Solo disponible con API oficial configurada
- Verifica que todos los campos requeridos estén completos
- Revisa que el token de autenticación sea válido