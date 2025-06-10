"""Módulo de APIs para portales de empleo"""

# Importar la clase base
from .base_api import BaseJobAPI

# Importar todas las clases de APIs
from .linkedin import LinkedInAPI
from .computrabajo import ComputrabajoAPI, ComputrabajoConfig
from .indeed import IndeedAPI
from .chiletrabajo import ChileTrabajoAPI
from .bolsa_nacional import BolsaNacionalAPI
from .empleos_publicos import EmpleosPublicosAPI
from .laborum import LaborumAPI
from .trabajando import TrabajandoAPI

# Exportar todas las clases
__all__ = [
    'BaseJobAPI',
    'LinkedInAPI',
    'ComputrabajoAPI',
    'ComputrabajoConfig',
    'IndeedAPI',
    'ChileTrabajoAPI',
    'BolsaNacionalAPI',
    'EmpleosPublicosAPI',
    'LaborumAPI',
    'TrabajandoAPI'
]

# Diccionario para facilitar el acceso a las APIs
API_CLASSES = {
    'linkedin': LinkedInAPI,
    'computrabajo': ComputrabajoAPI,
    'indeed': IndeedAPI,
    'chiletrabajo': ChileTrabajoAPI,
    'bolsa_nacional': BolsaNacionalAPI,
    'empleos_publicos': EmpleosPublicosAPI,
    'laborum': LaborumAPI,
    'trabajando': TrabajandoAPI
}

def get_api_instance(api_name: str):
    """Obtener una instancia de la API especificada"""
    api_class = API_CLASSES.get(api_name.lower())
    if api_class:
        return api_class()
    else:
        raise ValueError(f"API '{api_name}' no encontrada. APIs disponibles: {list(API_CLASSES.keys())}")

def get_all_apis():
    """Obtener instancias de todas las APIs disponibles"""
    return {name: api_class() for name, api_class in API_CLASSES.items()}