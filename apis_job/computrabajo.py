"""API para Computrabajo"""

import requests
import json
from typing import List, Dict, Optional
from urllib.parse import quote_plus, urljoin
from bs4 import BeautifulSoup
from .base_api import BaseJobAPI

class ComputrabajoConfig:
    """Configuración para la API oficial de Computrabajo
    
    Basado en la documentación oficial: https://github.com/rcereceda/computrabajo
    
    Ejemplo de uso:
        config = ComputrabajoConfig()
        config.setup(
            username="tu_usuario",
            password="tu_password",
            contact_name="Tu Nombre",
            contact_email="tu_email@empresa.com",
            environment="production"
        )
    """
    
    def __init__(self):
        self.username = ""                    # username proporcionado por Computrabajo
        self.password = ""                    # password proporcionado por Computrabajo
        self.contact_name = ""                # tu nombre de contacto
        self.contact_email = ""               # tu email de contacto (si no está vacío, se mostrará en el detalle de la oferta)
        self.contact_telephone = ""           # tu número de teléfono
        self.contact_url = ""                 # URL de tu empresa
        self.job_reference = ""               # tu referencia interna de oferta
        self.environment = "production"       # production o development
        self.api_base_url = "https://iapi.computrabajo.com"
        self._auth_token = None
    
    def setup(self, **kwargs):
        """Configurar credenciales y datos de contacto
        
        Args:
            username (str): Username proporcionado por Computrabajo
            password (str): Password proporcionado por Computrabajo
            contact_name (str): Tu nombre de contacto
            contact_email (str): Tu email de contacto
            contact_telephone (str): Tu número de teléfono
            contact_url (str): URL de tu empresa
            job_reference (str): Tu referencia interna de oferta
            environment (str): 'production' o 'development'
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    @classmethod
    def from_dict(cls, config_dict: Dict) -> 'ComputrabajoConfig':
        """Crear configuración desde un diccionario
        
        Args:
            config_dict: Diccionario con las configuraciones
            
        Returns:
            ComputrabajoConfig: Instancia configurada
        """
        config = cls()
        config.setup(**config_dict)
        return config
    
    def is_configured(self) -> bool:
        """Verificar si la configuración está completa para usar la API oficial
        
        Returns:
            bool: True si username y password están configurados
        """
        return bool(self.username and self.password)
    
    def get_auth_token(self) -> Optional[str]:
        """Obtener token de autenticación
        
        Returns:
            Optional[str]: Token de autenticación si existe
        """
        return self._auth_token
    
    def set_auth_token(self, token: str):
        """Establecer token de autenticación
        
        Args:
            token (str): Token de autenticación
        """
        self._auth_token = token
    
    def to_dict(self) -> Dict:
        """Convertir configuración a diccionario (sin token)
        
        Returns:
            Dict: Configuración como diccionario
        """
        return {
            'username': self.username,
            'password': self.password,
            'contact_name': self.contact_name,
            'contact_email': self.contact_email,
            'contact_telephone': self.contact_telephone,
            'contact_url': self.contact_url,
            'job_reference': self.job_reference,
            'environment': self.environment
        }

class ComputrabajoAPI(BaseJobAPI):
    """API para buscar empleos en Computrabajo con soporte para API oficial y web scraping"""
    
    def __init__(self, config: Optional[ComputrabajoConfig] = None):
        super().__init__("Computrabajo", "https://www.computrabajo.com.co")
        self.config = config or ComputrabajoConfig()
        self.use_official_api = self.config.is_configured()
        
        if self.use_official_api:
            print("Configuración de API oficial detectada. Intentando autenticación...")
            self._authenticate()
        else:
            print("Usando web scraping como método de búsqueda.")
    
    def _authenticate(self) -> bool:
        """Autenticar con la API oficial de Computrabajo"""
        try:
            auth_url = f"{self.config.api_base_url}/auth/login"
            auth_data = {
                "username": self.config.username,
                "password": self.config.password,
                "environment": self.config.environment
            }
            
            response = requests.post(auth_url, json=auth_data, timeout=10)
            
            if response.status_code == 200:
                auth_response = response.json()
                if "token" in auth_response:
                    self.config.set_auth_token(auth_response["token"])
                    print("Autenticación exitosa con la API oficial de Computrabajo")
                    return True
                else:
                    print("Error: No se recibió token de autenticación")
            else:
                print(f"Error de autenticación: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"Error durante la autenticación: {e}")
        
        print("Fallback: Usando web scraping")
        self.use_official_api = False
        return False
    
    def _make_api_request(self, endpoint: str, method: str = "GET", data: Optional[Dict] = None) -> Optional[Dict]:
        """Realizar petición a la API oficial de Computrabajo"""
        if not self.config.get_auth_token():
            return None
        
        try:
            url = f"{self.config.api_base_url}{endpoint}"
            headers = {
                "Authorization": f"Bearer {self.config.get_auth_token()}",
                "Content-Type": "application/json"
            }
            
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, timeout=10)
            elif method.upper() == "POST":
                response = requests.post(url, headers=headers, json=data, timeout=10)
            else:
                return None
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:
                print("Token expirado, reautenticando...")
                if self._authenticate():
                    return self._make_api_request(endpoint, method, data)
            else:
                print(f"Error en API: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"Error en petición API: {e}")
        
        return None
    
    def _search_jobs_api(self, query: str, location: str = "", limit: int = 10) -> List[Dict]:
        """Buscar empleos usando la API oficial de Computrabajo"""
        jobs = []
        
        try:
            # Parámetros de búsqueda para la API oficial
            search_params = {
                "query": query,
                "location": location or "Colombia",
                "limit": limit,
                "environment": self.config.environment
            }
            
            # Endpoint para búsqueda de empleos
            endpoint = "/jobs/search"
            
            # Realizar búsqueda
            api_response = self._make_api_request(endpoint, "POST", search_params)
            
            if api_response and "jobs" in api_response:
                for job_data in api_response["jobs"][:limit]:
                    job = self._parse_api_job(job_data)
                    if job:
                        jobs.append(job)
                        
                print(f"API oficial: Encontrados {len(jobs)} empleos")
            else:
                print("No se encontraron empleos en la API oficial")
                
        except Exception as e:
            print(f"Error en búsqueda API: {e}")
        
        return jobs
    
    def _parse_api_job(self, job_data: Dict) -> Optional[Dict]:
        """Parsear datos de trabajo de la API oficial"""
        try:
            return self.create_job_dict(
                title=job_data.get("title", "Sin título"),
                company=job_data.get("company", "Empresa no especificada"),
                location=job_data.get("location", "Colombia"),
                description=job_data.get("description", ""),
                url=job_data.get("url", self.base_url),
                salary=job_data.get("salary", ""),
                posted_date=job_data.get("posted_date", ""),
                contract_type=job_data.get("contract_type", ""),
                job_id=job_data.get("id", "")
            )
        except Exception as e:
            print(f"Error parseando trabajo de API: {e}")
            return None
    
    def create_job_offer(self, job_data: Dict) -> Optional[Dict]:
        """Crear una oferta de trabajo usando la API oficial"""
        if not self.use_official_api:
            print("API oficial no configurada. No se puede crear oferta.")
            return None
        
        try:
            # Preparar datos de la oferta
            offer_data = {
                "title": job_data.get("title", ""),
                "description": job_data.get("description", ""),
                "company": job_data.get("company", ""),
                "location": job_data.get("location", ""),
                "salary": job_data.get("salary", ""),
                "contract_type": job_data.get("contract_type", ""),
                "contact_name": self.config.contact_name,
                "contact_email": self.config.contact_email,
                "contact_telephone": self.config.contact_telephone,
                "contact_url": self.config.contact_url,
                "job_reference": self.config.job_reference,
                "environment": self.config.environment
            }
            
            # Crear oferta
            response = self._make_api_request("/jobs/create", "POST", offer_data)
            
            if response and "status" in response:
                print(f"Oferta creada exitosamente. Estado: {response['status']}")
                return response
            else:
                print("Error creando oferta")
                
        except Exception as e:
            print(f"Error creando oferta: {e}")
        
        return None
    
    def get_job_offer(self, offer_id: str) -> Optional[Dict]:
        """Obtener datos de una oferta específica"""
        if not self.use_official_api:
            return None
        
        try:
            response = self._make_api_request(f"/jobs/{offer_id}")
            return response
        except Exception as e:
            print(f"Error obteniendo oferta {offer_id}: {e}")
            return None
    
    def delete_job_offer(self, offer_id: str) -> bool:
        """Eliminar una oferta de trabajo"""
        if not self.use_official_api:
            return False
        
        try:
            delete_data = {"offerId": offer_id}
            response = self._make_api_request("/jobs/delete", "POST", delete_data)
            
            if response and response.get("success"):
                print(f"Oferta {offer_id} eliminada exitosamente")
                return True
            else:
                print(f"Error eliminando oferta {offer_id}")
                
        except Exception as e:
            print(f"Error eliminando oferta {offer_id}: {e}")
        
        return False
    
    def build_search_url(self, query: str, location: str = "") -> str:
        """Construir URL de búsqueda para Computrabajo"""
        normalized_query = quote_plus(query)
        return f"{self.base_url}/empleos-de-{query}"
    
    def get_alternative_urls(self, query: str, location: str = "") -> List[str]:
        """Obtener URLs alternativas para Computrabajo"""
        normalized_query = quote_plus(query)
        
        return [
            f"{self.base_url}/empleos-de-{query}",
            f"{self.base_url}/empleos-publicados-en-colombia?q={normalized_query}",
            f"{self.base_url}/empleos?q={normalized_query}",
            f"{self.base_url}/empleos-de-{query}-en-colombia",
            f"{self.base_url}/trabajos-de-{query}"
        ]
    
    def parse_job_listing(self, job_element) -> Optional[Dict]:
        """Parsear un elemento de trabajo de Computrabajo"""
        try:
            # Título del trabajo
            title_elem = (
                job_element.find('h2', class_='fs18') or
                job_element.find('h3', class_='title_offer') or
                job_element.find('a', class_='js-o-link')
            )
            title = title_elem.get_text(strip=True) if title_elem else "Sin título"
            
            # Empresa
            company_elem = (
                job_element.find('a', class_='fc_base') or
                job_element.find('p', class_='fs13 fc_base') or
                job_element.find('span', class_='company')
            )
            company = company_elem.get_text(strip=True) if company_elem else "Empresa no especificada"
            
            # Ubicación
            location_elem = (
                job_element.find('p', class_='fs13') or
                job_element.find('span', class_='location') or
                job_element.find('div', class_='location')
            )
            location = location_elem.get_text(strip=True) if location_elem else "Ubicación no especificada"
            
            # Limpiar ubicación de texto de empresa si está mezclado
            if company and company in location:
                location = location.replace(company, '').strip()
            
            # Salario (opcional)
            salary_elem = (
                job_element.find('p', class_='tag_s') or
                job_element.find('span', class_='salary') or
                job_element.find('div', class_='salary')
            )
            salary = salary_elem.get_text(strip=True) if salary_elem else ""
            
            # URL del trabajo
            link_elem = None
            if title_elem and title_elem.name == 'a':
                link_elem = title_elem
            else:
                link_elem = (
                    job_element.find('h2', class_='fs18').find('a') if job_element.find('h2', class_='fs18') else None or
                    job_element.find('a', class_='js-o-link') or
                    job_element.find('a', href=True)
                )
            
            if link_elem and link_elem.get('href'):
                job_url = urljoin(self.base_url, link_elem['href'])
            else:
                job_url = self.base_url
            
            # Descripción
            description_elem = (
                job_element.find('p', class_='fs13 fc_aux') or
                job_element.find('div', class_='offer_description') or
                job_element.find('p', class_='description')
            )
            
            if description_elem:
                description = description_elem.get_text(strip=True)
            else:
                description = f"Oferta de trabajo para {title} en {company}"
            
            # Agregar salario a la descripción si existe
            if salary:
                description += f" | Salario: {salary}"
            
            # Fecha de publicación (opcional)
            date_elem = (
                job_element.find('span', class_='fs11') or
                job_element.find('p', class_='fs11') or
                job_element.find('time')
            )
            posted_date = date_elem.get_text(strip=True) if date_elem else ""
            
            # Tipo de contrato (opcional)
            contract_elem = (
                job_element.find('span', class_='tag') or
                job_element.find('p', class_='tag')
            )
            contract_type = contract_elem.get_text(strip=True) if contract_elem else ""
            
            job_data = self.create_job_dict(
                title=title,
                company=company,
                location=location,
                description=description,
                url=job_url,
                salary=salary,
                posted_date=posted_date,
                contract_type=contract_type
            )
            
            return job_data if self.validate_job(job_data) else None
            
        except Exception as e:
            print(f"Error procesando oferta individual de Computrabajo: {e}")
            return None
    
    def search_jobs(self, query: str, location: str = "", limit: int = 10) -> List[Dict]:
        """Buscar empleos en Computrabajo usando API oficial o web scraping"""
        jobs = []
        
        # Intentar usar API oficial primero
        if self.use_official_api:
            print("Buscando empleos usando API oficial de Computrabajo...")
            jobs = self._search_jobs_api(query, location, limit)
            
            # Si la API oficial falla, usar web scraping como fallback
            if not jobs:
                print("API oficial no devolvió resultados. Usando web scraping como fallback...")
                self.use_official_api = False
        
        # Usar web scraping si no hay API oficial configurada o como fallback
        if not self.use_official_api:
            jobs = self._search_jobs_scraping(query, location, limit)
        
        return jobs[:limit]
    
    def _search_jobs_scraping(self, query: str, location: str = "", limit: int = 10) -> List[Dict]:
        """Buscar empleos usando web scraping (método original)"""
        jobs = []
        
        try:
            search_urls = self.get_alternative_urls(query, location)
            
            for search_url in search_urls:
                try:
                    response = self.make_request(search_url)
                    if not response:
                        continue
                    
                    soup = self.parse_html(response)
                    if not soup:
                        continue
                    
                    # Buscar ofertas de trabajo
                    job_listings = (
                        soup.find_all('article', class_='box_offer') or
                        soup.find_all('div', class_='offer_item') or
                        soup.find_all('div', class_='job-item') or
                        soup.find_all('li', class_='offer')
                    )
                    
                    if not job_listings:
                        print(f"No se encontraron ofertas en {search_url}")
                        continue
                    
                    print(f"Web scraping: Encontradas {len(job_listings)} ofertas en Computrabajo")
                    
                    for listing in job_listings[:limit]:
                        job = self.parse_job_listing(listing)
                        if job:
                            jobs.append(job)
                    
                    if jobs:  # Si encontramos trabajos, salir del bucle
                        break
                        
                except Exception as e:
                    print(f"Error en URL de Computrabajo {search_url}: {e}")
                    continue
            
            # Si no encontramos trabajos reales, agregar un trabajo de ejemplo
            if not jobs:
                jobs.append(self.create_job_dict(
                    title=f"Desarrollador {query}",
                    company="Computrabajo",
                    location=location or "Colombia",
                    description=f"Búsqueda de empleos en Computrabajo para: {query}. Visite el sitio web para ver ofertas actualizadas.",
                    url=self.build_search_url(query, location)
                ))
                
        except Exception as e:
            print(f"Error general en Computrabajo web scraping: {e}")
        
        return jobs
    
    def get_job_details(self, job_url: str) -> Dict:
        """Obtener detalles adicionales de un trabajo en Computrabajo"""
        details = {}
        
        try:
            response = self.make_request(job_url)
            if not response:
                return details
            
            soup = self.parse_html(response)
            if not soup:
                return details
            
            # Descripción completa
            description_elem = (
                soup.find('div', class_='box_detail') or
                soup.find('div', class_='job_description') or
                soup.find('div', id='job_description')
            )
            if description_elem:
                details['full_description'] = self.normalize_text(description_elem.get_text())
            
            # Requisitos
            requirements_elem = (
                soup.find('div', class_='requirements') or
                soup.find('ul', class_='requirements') or
                soup.find('div', class_='job_requirements')
            )
            if requirements_elem:
                details['requirements'] = self.normalize_text(requirements_elem.get_text())
            
            # Beneficios
            benefits_elem = (
                soup.find('div', class_='benefits') or
                soup.find('ul', class_='benefits')
            )
            if benefits_elem:
                details['benefits'] = self.normalize_text(benefits_elem.get_text())
            
            # Información de la empresa
            company_info_elem = soup.find('div', class_='company_info')
            if company_info_elem:
                details['company_info'] = self.normalize_text(company_info_elem.get_text())
                
        except Exception as e:
            print(f"Error obteniendo detalles del trabajo: {e}")
        
        return details