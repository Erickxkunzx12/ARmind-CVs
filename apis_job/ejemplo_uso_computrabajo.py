"""Ejemplo práctico de uso de la API de Computrabajo con autenticación oficial"""

import os
import json
from typing import Dict, List
from .computrabajo import ComputrabajoConfig, ComputrabajoAPI

def cargar_configuracion_desde_archivo(archivo_config: str) -> ComputrabajoConfig:
    """Cargar configuración desde un archivo JSON
    
    Args:
        archivo_config (str): Ruta al archivo de configuración JSON
        
    Returns:
        ComputrabajoConfig: Configuración cargada
    """
    try:
        with open(archivo_config, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        return ComputrabajoConfig.from_dict(config_data)
    except FileNotFoundError:
        print(f"Archivo de configuración {archivo_config} no encontrado")
        return ComputrabajoConfig()
    except json.JSONDecodeError:
        print(f"Error al leer el archivo de configuración {archivo_config}")
        return ComputrabajoConfig()

def cargar_configuracion_desde_env() -> ComputrabajoConfig:
    """Cargar configuración desde variables de entorno
    
    Variables de entorno esperadas:
    - COMPUTRABAJO_USERNAME
    - COMPUTRABAJO_PASSWORD
    - COMPUTRABAJO_CONTACT_NAME
    - COMPUTRABAJO_CONTACT_EMAIL
    - COMPUTRABAJO_CONTACT_PHONE
    - COMPUTRABAJO_CONTACT_URL
    - COMPUTRABAJO_JOB_REFERENCE
    - COMPUTRABAJO_ENVIRONMENT
    
    Returns:
        ComputrabajoConfig: Configuración cargada
    """
    config = ComputrabajoConfig()
    
    config.setup(
        username=os.getenv('COMPUTRABAJO_USERNAME', ''),
        password=os.getenv('COMPUTRABAJO_PASSWORD', ''),
        contact_name=os.getenv('COMPUTRABAJO_CONTACT_NAME', ''),
        contact_email=os.getenv('COMPUTRABAJO_CONTACT_EMAIL', ''),
        contact_telephone=os.getenv('COMPUTRABAJO_CONTACT_PHONE', ''),
        contact_url=os.getenv('COMPUTRABAJO_CONTACT_URL', ''),
        job_reference=os.getenv('COMPUTRABAJO_JOB_REFERENCE', ''),
        environment=os.getenv('COMPUTRABAJO_ENVIRONMENT', 'production')
    )
    
    return config

def crear_archivo_configuracion_ejemplo(archivo_destino: str):
    """Crear un archivo de configuración de ejemplo
    
    Args:
        archivo_destino (str): Ruta donde crear el archivo
    """
    config_ejemplo = {
        "username": "tu_usuario_computrabajo",
        "password": "tu_password_computrabajo",
        "contact_name": "Tu Nombre Completo",
        "contact_email": "tu_email@empresa.com",
        "contact_telephone": "+57 300 123 4567",
        "contact_url": "https://tu-empresa.com",
        "job_reference": "REF-2024-001",
        "environment": "production"
    }
    
    try:
        with open(archivo_destino, 'w', encoding='utf-8') as f:
            json.dump(config_ejemplo, f, indent=4, ensure_ascii=False)
        print(f"Archivo de configuración de ejemplo creado en: {archivo_destino}")
    except Exception as e:
        print(f"Error creando archivo de configuración: {e}")

def buscar_empleos_con_fallback(termino_busqueda: str, ubicacion: str = "Colombia", limite: int = 10) -> List[Dict]:
    """Buscar empleos con fallback automático entre API oficial y web scraping
    
    Args:
        termino_busqueda (str): Término de búsqueda
        ubicacion (str): Ubicación de búsqueda
        limite (int): Número máximo de resultados
        
    Returns:
        List[Dict]: Lista de empleos encontrados
    """
    # Intentar cargar configuración desde variables de entorno
    config = cargar_configuracion_desde_env()
    
    # Si no hay configuración en variables de entorno, intentar desde archivo
    if not config.is_configured():
        config = cargar_configuracion_desde_archivo('computrabajo_config.json')
    
    # Crear API con configuración (o sin ella para usar web scraping)
    api = ComputrabajoAPI(config)
    
    # Buscar empleos
    empleos = api.search_jobs(termino_busqueda, ubicacion, limite)
    
    return empleos

def gestionar_ofertas_trabajo(config: ComputrabajoConfig):
    """Ejemplo de gestión completa de ofertas de trabajo
    
    Args:
        config (ComputrabajoConfig): Configuración de la API
    """
    api = ComputrabajoAPI(config)
    
    if not api.use_official_api:
        print("⚠️ API oficial no configurada. Solo búsqueda disponible.")
        return
    
    print("🚀 Gestión de ofertas con API oficial de Computrabajo")
    
    # 1. Crear una nueva oferta
    print("\n1. Creando nueva oferta...")
    nueva_oferta = {
        "title": "Desarrollador Python Senior",
        "description": "Buscamos desarrollador Python con experiencia en Django, FastAPI y bases de datos. Trabajo remoto disponible.",
        "company": "Tech Innovations SAS",
        "location": "Bogotá, Colombia",
        "salary": "$4,000,000 - $6,000,000 COP",
        "contract_type": "Tiempo completo"
    }
    
    resultado_creacion = api.create_job_offer(nueva_oferta)
    
    if resultado_creacion:
        offer_id = resultado_creacion.get('id')
        print(f"✅ Oferta creada exitosamente")
        print(f"   ID: {offer_id}")
        print(f"   Estado: {resultado_creacion.get('status')}")
        
        # 2. Obtener detalles de la oferta creada
        print(f"\n2. Obteniendo detalles de la oferta {offer_id}...")
        detalles = api.get_job_offer(offer_id)
        
        if detalles:
            print(f"✅ Detalles obtenidos:")
            print(f"   Título: {detalles.get('title', 'N/A')}")
            print(f"   Estado: {detalles.get('status', 'N/A')}")
        
        # 3. Buscar empleos similares
        print("\n3. Buscando empleos similares...")
        empleos_similares = api.search_jobs("python", "Bogotá", 3)
        
        print(f"✅ Encontrados {len(empleos_similares)} empleos similares:")
        for i, empleo in enumerate(empleos_similares, 1):
            print(f"   {i}. {empleo['title']} - {empleo['company']}")
        
        # 4. Opcional: Eliminar la oferta (descomenta si quieres probar)
        # print(f"\n4. Eliminando oferta {offer_id}...")
        # eliminada = api.delete_job_offer(offer_id)
        # if eliminada:
        #     print("✅ Oferta eliminada exitosamente")
        
    else:
        print("❌ Error creando la oferta")

def ejemplo_completo():
    """Ejemplo completo de uso de la API de Computrabajo"""
    print("=" * 60)
    print("🔍 EJEMPLO COMPLETO - API DE COMPUTRABAJO")
    print("=" * 60)
    
    # 1. Búsqueda básica con fallback automático
    print("\n📋 1. BÚSQUEDA BÁSICA (con fallback automático)")
    print("-" * 50)
    
    empleos = buscar_empleos_con_fallback("desarrollador", "Colombia", 5)
    
    print(f"\n✅ Encontrados {len(empleos)} empleos:")
    for i, empleo in enumerate(empleos, 1):
        print(f"{i:2d}. {empleo['title'][:50]:<50} | {empleo['company'][:30]:<30}")
        print(f"     📍 {empleo['location']:<20} | 🔗 {empleo['source']}")
        print()
    
    # 2. Configuración manual para API oficial
    print("\n⚙️  2. CONFIGURACIÓN MANUAL PARA API OFICIAL")
    print("-" * 50)
    
    # Crear configuración manual (reemplaza con tus credenciales reales)
    config_manual = ComputrabajoConfig()
    config_manual.setup(
        username="tu_usuario_aqui",  # Reemplazar con credenciales reales
        password="tu_password_aqui",  # Reemplazar con credenciales reales
        contact_name="Juan Pérez",
        contact_email="juan@miempresa.com",
        contact_telephone="+57 300 123 4567",
        contact_url="https://miempresa.com",
        job_reference="REF-2024-001",
        environment="production"
    )
    
    if config_manual.is_configured() and config_manual.username != "tu_usuario_aqui":
        print("🔑 Configuración detectada. Probando gestión de ofertas...")
        gestionar_ofertas_trabajo(config_manual)
    else:
        print("⚠️ Configuración no válida (usando valores de ejemplo)")
        print("   Para probar la API oficial, actualiza las credenciales en el código")
    
    # 3. Crear archivo de configuración de ejemplo
    print("\n📄 3. CREANDO ARCHIVO DE CONFIGURACIÓN DE EJEMPLO")
    print("-" * 50)
    
    crear_archivo_configuracion_ejemplo('computrabajo_config_ejemplo.json')
    
    print("\n✅ Ejemplo completado exitosamente!")
    print("\n📚 Para más información, consulta:")
    print("   - README_COMPUTRABAJO.md")
    print("   - computrabajo_config_example.py")
    print("   - https://github.com/rcereceda/computrabajo")

if __name__ == "__main__":
    ejemplo_completo()