"""Archivo de configuración de ejemplo para la API oficial de Computrabajo"""

from .computrabajo import ComputrabajoConfig, ComputrabajoAPI

# Ejemplo de configuración para la API oficial de Computrabajo
# Basado en la documentación: https://github.com/rcereceda/computrabajo

def setup_computrabajo_api():
    """Configurar la API de Computrabajo con credenciales oficiales"""
    
    # Crear configuración
    config = ComputrabajoConfig()
    
    # Configurar credenciales (reemplazar con valores reales)
    config.setup(
        username="gustavo cabrebra rosales",          # username proporcionado por Computrabajo
        password="Solido1976",         # password proporcionado por Computrabajo
        contact_name="gustavo",                    # tu nombre de contacto
        contact_email="gustavo.cabrera.rosales@gmail.com",        # tu email de contacto (si no está vacío, se mostrará en el detalle de la oferta para candidatos registrados)
        contact_telephone="+56971350556",        # tu número de teléfono
        contact_url="https://tu-empresa.com",        # URL de tu empresa
        job_reference="REF-2024-001",                # tu referencia interna de oferta
        environment="production"                      # Puedes elegir entre production o development
    )
    
    # Crear instancia de la API con configuración
    api = ComputrabajoAPI(config)
    
    return api

def setup_computrabajo_scraping():
    """Configurar la API de Computrabajo solo con web scraping (sin credenciales)"""
    
    # Crear instancia sin configuración (usará web scraping)
    api = ComputrabajoAPI()
    
    return api

# Ejemplo de uso
if __name__ == "__main__":
    # Opción 1: Con API oficial (requiere credenciales)
    print("=== Configuración con API oficial ===")
    api_oficial = setup_computrabajo_api()
    
    # Buscar empleos
    empleos = api_oficial.search_jobs("desarrollador python", "Bogotá", limit=5)
    print(f"Encontrados {len(empleos)} empleos")
    
    # Ejemplo de creación de oferta (solo con API oficial)
    if api_oficial.use_official_api:
        nueva_oferta = {
            "title": "Desarrollador Python Senior",
            "description": "Buscamos desarrollador Python con experiencia en Django y FastAPI",
            "company": "Mi Empresa Tech",
            "location": "Bogotá, Colombia",
            "salary": "$3,000,000 - $5,000,000 COP",
            "contract_type": "Tiempo completo"
        }
        
        resultado = api_oficial.create_job_offer(nueva_oferta)
        if resultado:
            print(f"Oferta creada con ID: {resultado.get('id')}")
    
    print("\n=== Configuración solo con web scraping ===")
    # Opción 2: Solo web scraping (sin credenciales)
    api_scraping = setup_computrabajo_scraping()
    
    # Buscar empleos
    empleos_scraping = api_scraping.search_jobs("desarrollador", "Colombia", limit=3)
    print(f"Encontrados {len(empleos_scraping)} empleos con web scraping")
    
    # Estados de ofertas según la documentación:
    # Pendiente = 1
    # Activa = 2
    # Caducada = 3
    # Eliminada = 4
    # Rechazada = 5
    # Archivada = 6