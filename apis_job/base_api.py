"""Clase base para todas las APIs de portales de empleo"""

import requests
import time
import random
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from urllib.parse import urljoin, quote_plus

class BaseJobAPI(ABC):
    """Clase base abstracta para todas las APIs de portales de empleo"""
    
    def __init__(self, name: str, base_url: str):
        self.name = name
        self.base_url = base_url
        self.session = requests.Session()
        self.setup_session()
    
    def setup_session(self):
        """Configurar la sesión HTTP con headers comunes"""
        self.session.headers.update({
            'User-Agent': self.get_random_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
    
    def get_random_user_agent(self) -> str:
        """Obtener un User-Agent aleatorio para evitar bloqueos"""
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15'
        ]
        return random.choice(user_agents)
    
    def add_delay(self, min_seconds: float = 1.0, max_seconds: float = 3.0):
        """Agregar delay aleatorio para evitar bloqueos"""
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)
    
    def make_request(self, url: str, timeout: int = 10) -> Optional[requests.Response]:
        """Realizar petición HTTP con manejo de errores"""
        try:
            self.add_delay()
            response = self.session.get(url, timeout=timeout)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            print(f"Error en petición a {url}: {e}")
            return None
    
    def parse_html(self, response: requests.Response) -> Optional[BeautifulSoup]:
        """Parsear HTML de la respuesta"""
        try:
            return BeautifulSoup(response.content, 'html.parser')
        except Exception as e:
            print(f"Error parseando HTML: {e}")
            return None
    
    def normalize_text(self, text: str) -> str:
        """Normalizar texto eliminando espacios extra y caracteres especiales"""
        if not text:
            return ""
        return ' '.join(text.strip().split())
    
    def create_job_dict(self, title: str, company: str, location: str, 
                       description: str, url: str, **kwargs) -> Dict:
        """Crear diccionario estándar para un trabajo"""
        return {
            'title': self.normalize_text(title),
            'company': self.normalize_text(company),
            'location': self.normalize_text(location),
            'description': self.normalize_text(description),
            'url': url,
            'source': self.name,
            **kwargs
        }
    
    @abstractmethod
    def search_jobs(self, query: str, location: str = "", limit: int = 10) -> List[Dict]:
        """Buscar empleos en el portal específico"""
        pass
    
    @abstractmethod
    def build_search_url(self, query: str, location: str = "") -> str:
        """Construir URL de búsqueda específica del portal"""
        pass
    
    @abstractmethod
    def parse_job_listing(self, job_element) -> Optional[Dict]:
        """Parsear un elemento de trabajo específico del portal"""
        pass
    
    def get_job_details(self, job_url: str) -> Dict:
        """Obtener detalles adicionales de un trabajo (opcional)"""
        return {}
    
    def validate_job(self, job: Dict) -> bool:
        """Validar que un trabajo tenga los campos mínimos requeridos"""
        required_fields = ['title', 'company', 'location', 'description', 'url', 'source']
        return all(job.get(field) for field in required_fields)