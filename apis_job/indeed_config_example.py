"""Ejemplo de configuración para Indeed Job Sync API oficial"""

# IMPORTANTE: Este es un archivo de ejemplo. 
# Crea tu propio archivo de configuración con tus credenciales reales.
# NO subas tus credenciales reales a repositorios públicos.

from .indeed import IndeedAPI

# Configuración para Indeed Job Sync API oficial
# Obtén estas credenciales desde Indeed Partner Console:
# https://partners.indeed.com/

INDEED_CONFIG = {
    'client_id': 'tu_client_id_aqui',
    'client_secret': 'tu_client_secret_aqui',
    # access_token se obtiene automáticamente usando OAuth
}

def create_indeed_api_with_credentials():
    """Crear instancia de IndeedAPI con credenciales OAuth"""
    return IndeedAPI(
        client_id=INDEED_CONFIG['client_id'],
        client_secret=INDEED_CONFIG['client_secret']
    )

def create_indeed_api_fallback():
    """Crear instancia de IndeedAPI solo con web scraping (sin credenciales)"""
    return IndeedAPI()

# Ejemplo de uso:
if __name__ == "__main__":
    # Opción 1: Con credenciales OAuth (recomendado)
    try:
        indeed_api = create_indeed_api_with_credentials()
        jobs = indeed_api.search_jobs("python developer", "Colombia", limit=5)
        print(f"Encontrados {len(jobs)} empleos usando API oficial")
        for job in jobs:
            print(f"- {job['title']} en {job['company']}")
    except Exception as e:
        print(f"Error con API oficial: {e}")
        
        # Fallback a web scraping
        print("Usando web scraping como alternativa...")
        indeed_api_fallback = create_indeed_api_fallback()
        jobs = indeed_api_fallback.search_jobs("python developer", "Colombia", limit=5)
        print(f"Encontrados {len(jobs)} empleos usando web scraping")
        for job in jobs:
            print(f"- {job['title']} en {job['company']}")

# Pasos para configurar Indeed Job Sync API:
# 
# 1. Regístrate como partner de Indeed:
#    https://partners.indeed.com/
# 
# 2. Crea una aplicación en Partner Console
# 
# 3. Obtén tus credenciales OAuth:
#    - Client ID
#    - Client Secret
# 
# 4. Configura los scopes requeridos:
#    - employer_access
#    - employer_hosted_job
# 
# 5. Reemplaza las credenciales en INDEED_CONFIG
# 
# 6. La API automáticamente:
#    - Obtendrá el access token usando OAuth 2.0
#    - Usará GraphQL para consultar empleos
#    - Fallback a web scraping si la API falla