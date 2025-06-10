"""Ejemplo de uso de las APIs de portales de empleo"""

import sys
import os

# Agregar el directorio padre al path para importar las APIs
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from apis_job import (
    LinkedInAPI, ComputrabajoAPI, IndeedAPI, ChileTrabajoAPI,
    BolsaNacionalAPI, EmpleosPublicosAPI, LaborumAPI, TrabajandoAPI,
    get_api_instance, get_all_apis
)

# Configuración opcional para Indeed Job Sync API oficial
# Descomenta y configura con tus credenciales reales:
# INDEED_CLIENT_ID = "tu_client_id_aqui"
# INDEED_CLIENT_SECRET = "tu_client_secret_aqui"

def test_single_api():
    """Ejemplo de uso de una API específica"""
    print("\n=== Probando API individual (Indeed con OAuth) ===")
    
    # Ejemplo con Indeed usando credenciales OAuth (si están disponibles)
    # Descomenta las siguientes líneas y configura tus credenciales:
    # indeed_api = IndeedAPI(
    #     client_id=INDEED_CLIENT_ID,
    #     client_secret=INDEED_CLIENT_SECRET
    # )
    
    # Ejemplo sin credenciales (solo web scraping)
    indeed_api = IndeedAPI()
    jobs = indeed_api.search_jobs("python developer", "Colombia", limit=3)
    
    print(f"Encontrados {len(jobs)} empleos en Indeed:")
    for job in jobs:
        print(f"- {job['title']} en {job['company']} ({job['location']})")
        print(f"  URL: {job['url']}")
        print(f"  Descripción: {job['description'][:100]}...")
        print()
    
    print("\n=== Probando API individual (LinkedIn) ===")
    
    linkedin_api = LinkedInAPI()
    jobs = linkedin_api.search_jobs("python developer", "Colombia", limit=3)
    
    print(f"Encontrados {len(jobs)} empleos en LinkedIn:")
    for job in jobs:
        print(f"- {job['title']} en {job['company']} ({job['location']})")
        print(f"  URL: {job['url']}")
        print(f"  Descripción: {job['description'][:100]}...")
        print()

def test_multiple_apis():
    """Ejemplo de uso de múltiples APIs"""
    print("=== Prueba de Múltiples APIs ===")
    
    # APIs a probar
    apis_to_test = [
        ('linkedin', 'LinkedIn'),
        ('computrabajo', 'ComputTrabajo'),
        ('indeed', 'Indeed'),
        ('chiletrabajo', 'ChileTrabajo'),
        ('bolsa_nacional', 'Bolsa Nacional'),
        ('empleos_publicos', 'Empleos Públicos'),
        ('laborum', 'Laborum'),
        ('trabajando', 'Trabajando.com')
    ]
    
    query = "desarrollador"
    location = "Colombia"
    
    all_jobs = []
    
    for api_name, display_name in apis_to_test:
        try:
            print(f"\nBuscando en {display_name}...")
            api = get_api_instance(api_name)
            jobs = api.search_jobs(query, location, limit=3)
            
            print(f"Encontrados {len(jobs)} empleos:")
            for job in jobs:
                job['source'] = display_name  # Agregar fuente
                all_jobs.append(job)
                print(f"  - {job['title']} en {job['company']}")
                
        except Exception as e:
            print(f"Error en {display_name}: {e}")
    
    print(f"\n=== RESUMEN TOTAL ===")
    print(f"Total de empleos encontrados: {len(all_jobs)}")
    
    # Agrupar por fuente
    by_source = {}
    for job in all_jobs:
        source = job['source']
        if source not in by_source:
            by_source[source] = []
        by_source[source].append(job)
    
    for source, jobs in by_source.items():
        print(f"{source}: {len(jobs)} empleos")

def test_all_apis_at_once():
    """Ejemplo usando la función get_all_apis"""
    print("\n=== Prueba de Todas las APIs a la Vez ===")
    
    # Obtener todas las APIs
    all_apis = get_all_apis()
    
    query = "programador"
    location = "Chile"
    
    total_jobs = 0
    
    for api_name, api_instance in all_apis.items():
        try:
            print(f"\nBuscando en {api_instance.name}...")
            jobs = api_instance.search_jobs(query, location, limit=2)
            total_jobs += len(jobs)
            
            for job in jobs:
                print(f"  - {job['title']} | {job['company']} | {job['location']}")
                
        except Exception as e:
            print(f"Error en {api_instance.name}: {e}")
    
    print(f"\nTotal de empleos encontrados en todas las APIs: {total_jobs}")

def test_job_details():
    """Ejemplo de obtención de detalles de un trabajo"""
    print("\n=== Prueba de Detalles de Trabajo ===")
    
    # Usar ComputTrabajo como ejemplo
    computrabajo_api = ComputrabajoAPI()
    jobs = computrabajo_api.search_jobs("analista", "Colombia", limit=1)
    
    if jobs:
        job = jobs[0]
        print(f"Obteniendo detalles para: {job['title']}")
        print(f"URL: {job['url']}")
        
        # Obtener detalles adicionales
        details = computrabajo_api.get_job_details(job['url'])
        
        if details:
            print("\nDetalles adicionales encontrados:")
            for key, value in details.items():
                print(f"{key}: {value[:200]}..." if len(value) > 200 else f"{key}: {value}")
        else:
            print("No se pudieron obtener detalles adicionales")
    else:
        print("No se encontraron trabajos para obtener detalles")

def main():
    """Función principal para ejecutar todos los ejemplos"""
    print("🚀 DEMO DE APIs DE PORTALES DE EMPLEO 🚀")
    print("=" * 50)
    
    try:
        # Ejecutar diferentes ejemplos
        test_single_api()
        test_multiple_apis()
        test_all_apis_at_once()
        test_job_details()
        
        print("\n✅ Demo completado exitosamente!")
        
    except Exception as e:
        print(f"\n❌ Error durante la demo: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()