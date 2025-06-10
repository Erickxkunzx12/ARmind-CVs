"""API para LinkedIn Jobs"""

import requests
from typing import List, Dict, Optional
from urllib.parse import quote_plus, urljoin
from bs4 import BeautifulSoup
from .base_api import BaseJobAPI

class LinkedInAPI(BaseJobAPI):
    """API para buscar empleos en LinkedIn"""
    
    def __init__(self):
        super().__init__("LinkedIn", "https://www.linkedin.com")
        # LinkedIn requiere headers específicos
        self.session.headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
            'Cache-Control': 'max-age=0',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1'
        })
    
    def build_search_url(self, query: str, location: str = "") -> str:
        """Construir URL de búsqueda para LinkedIn"""
        normalized_query = quote_plus(query)
        normalized_location = quote_plus(location) if location else quote_plus("Colombia")
        
        return f"{self.base_url}/jobs/search/?keywords={normalized_query}&location={normalized_location}"
    
    def get_alternative_urls(self, query: str, location: str = "") -> List[str]:
        """Obtener URLs alternativas para LinkedIn"""
        normalized_query = quote_plus(query)
        normalized_location = quote_plus(location) if location else quote_plus("Colombia")
        
        return [
            f"{self.base_url}/jobs/search/?keywords={normalized_query}&location={normalized_location}",
            f"{self.base_url}/jobs/search/?keywords={normalized_query}&location={normalized_location}&sortBy=DD",
            f"{self.base_url}/jobs/search/?keywords={normalized_query}",
            f"{self.base_url}/jobs/search/?f_TPR=r86400&keywords={normalized_query}",  # Últimas 24 horas
            f"{self.base_url}/jobs/search/?f_JT=F&keywords={normalized_query}&location={normalized_location}"  # Tiempo completo
        ]
    
    def parse_job_listing(self, job_element) -> Optional[Dict]:
        """Parsear un elemento de trabajo de LinkedIn"""
        try:
            # Título del trabajo
            title_elem = (
                job_element.find('h3', class_='base-search-card__title') or
                job_element.find('h3', class_='job-search-card__title') or
                job_element.find('a', class_='base-card__full-link')
            )
            title = title_elem.get_text(strip=True) if title_elem else "Sin título"
            
            # Empresa
            company_elem = (
                job_element.find('h4', class_='base-search-card__subtitle') or
                job_element.find('h4', class_='job-search-card__subtitle') or
                job_element.find('a', class_='hidden-nested-link')
            )
            company = company_elem.get_text(strip=True) if company_elem else "Empresa no especificada"
            
            # Ubicación
            location_elem = (
                job_element.find('span', class_='job-search-card__location') or
                job_element.find('span', class_='base-search-card__location')
            )
            location = location_elem.get_text(strip=True) if location_elem else "Ubicación no especificada"
            
            # Salario (opcional)
            salary_elem = (
                job_element.find('span', class_='job-search-card__salary-info') or
                job_element.find('span', class_='base-search-card__salary')
            )
            salary = salary_elem.get_text(strip=True) if salary_elem else ""
            
            # URL del trabajo
            link_elem = (
                job_element.find('a', class_='base-card__full-link') or
                job_element.find('a', href=True)
            )
            
            if link_elem and link_elem.get('href'):
                job_url = urljoin(self.base_url, link_elem['href'])
            else:
                job_url = self.base_url
            
            # Descripción
            description_elem = (
                job_element.find('p', class_='job-search-card__snippet') or
                job_element.find('p', class_='base-search-card__snippet')
            )
            description = description_elem.get_text(strip=True) if description_elem else f"Oferta de trabajo para {title} en {company}"
            
            # Agregar salario a la descripción si existe
            if salary:
                description += f" | Salario: {salary}"
            
            # Fecha de publicación (opcional)
            date_elem = (
                job_element.find('time', class_='job-search-card__listdate') or
                job_element.find('time', class_='base-search-card__listdate')
            )
            posted_date = date_elem.get_text(strip=True) if date_elem else ""
            
            job_data = self.create_job_dict(
                title=title,
                company=company,
                location=location,
                description=description,
                url=job_url,
                salary=salary,
                posted_date=posted_date
            )
            
            return job_data if self.validate_job(job_data) else None
            
        except Exception as e:
            print(f"Error procesando oferta individual de LinkedIn: {e}")
            return None
    
    def search_jobs(self, query: str, location: str = "", limit: int = 10) -> List[Dict]:
        """Buscar empleos en LinkedIn"""
        jobs = []
        
        try:
            search_urls = self.get_alternative_urls(query, location)
            
            for search_url in search_urls:
                try:
                    # Delay más largo para LinkedIn
                    self.add_delay(2, 5)
                    
                    response = self.make_request(search_url, timeout=15)
                    if not response:
                        continue
                    
                    soup = self.parse_html(response)
                    if not soup:
                        continue
                    
                    # Buscar ofertas de trabajo con múltiples selectores
                    job_listings = (
                        soup.find_all('div', class_='base-card') or
                        soup.find_all('div', class_='job-search-card') or
                        soup.find_all('div', class_='jobs-search-results-list') or
                        soup.find_all('li', class_='result-card')
                    )
                    
                    if not job_listings:
                        print(f"No se encontraron ofertas en {search_url}")
                        continue
                    
                    print(f"Encontradas {len(job_listings)} ofertas en LinkedIn")
                    
                    for listing in job_listings[:limit]:
                        job = self.parse_job_listing(listing)
                        if job:
                            jobs.append(job)
                    
                    if jobs:  # Si encontramos trabajos, salir del bucle
                        break
                        
                except Exception as e:
                    print(f"Error en URL de LinkedIn {search_url}: {e}")
                    continue
            
            # Si no encontramos trabajos reales, agregar un trabajo de ejemplo
            if not jobs:
                jobs.append(self.create_job_dict(
                    title=f"Desarrollador {query}",
                    company="LinkedIn Jobs",
                    location=location or "Colombia",
                    description=f"Para acceder a ofertas reales de LinkedIn, es necesario configurar autenticación. Búsqueda: {query}",
                    url=self.build_search_url(query, location)
                ))
                
        except Exception as e:
            print(f"Error general en LinkedIn API: {e}")
        
        return jobs[:limit]
    
    def get_job_details(self, job_url: str) -> Dict:
        """Obtener detalles adicionales de un trabajo en LinkedIn"""
        details = {}
        
        try:
            response = self.make_request(job_url)
            if not response:
                return details
            
            soup = self.parse_html(response)
            if not soup:
                return details
            
            # Descripción completa
            description_elem = soup.find('div', class_='show-more-less-html__markup')
            if description_elem:
                details['full_description'] = self.normalize_text(description_elem.get_text())
            
            # Requisitos
            requirements_elem = soup.find('div', class_='job-criteria__text')
            if requirements_elem:
                details['requirements'] = self.normalize_text(requirements_elem.get_text())
            
            # Nivel de experiencia
            experience_elem = soup.find('span', class_='job-criteria__text--criteria')
            if experience_elem:
                details['experience_level'] = self.normalize_text(experience_elem.get_text())
                
        except Exception as e:
            print(f"Error obteniendo detalles del trabajo: {e}")
        
        return details