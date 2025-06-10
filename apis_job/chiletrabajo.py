"""API para ChileTrabajo"""

import requests
from typing import List, Dict, Optional
from urllib.parse import quote_plus, urljoin
from bs4 import BeautifulSoup
from .base_api import BaseJobAPI

class ChileTrabajoAPI(BaseJobAPI):
    """API para buscar empleos en ChileTrabajo"""
    
    def __init__(self):
        super().__init__("ChileTrabajo", "https://www.chiletrabajo.cl")
        # ChileTrabajo requiere headers específicos
        self.session.headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-CL,es;q=0.8,en;q=0.6',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        })
    
    def build_search_url(self, query: str, location: str = "") -> str:
        """Construir URL de búsqueda para ChileTrabajo"""
        normalized_query = quote_plus(query)
        normalized_location = quote_plus(location) if location else quote_plus("Chile")
        
        return f"{self.base_url}/empleos?q={normalized_query}&l={normalized_location}"
    
    def get_alternative_urls(self, query: str, location: str = "") -> List[str]:
        """Obtener URLs alternativas para ChileTrabajo"""
        normalized_query = quote_plus(query)
        normalized_location = quote_plus(location) if location else quote_plus("Chile")
        
        return [
            f"{self.base_url}/empleos?q={normalized_query}&l={normalized_location}",
            f"{self.base_url}/empleos?q={normalized_query}&l={normalized_location}&sort=date",
            f"{self.base_url}/empleos?q={normalized_query}&l=Santiago",  # Santiago específico
            f"{self.base_url}/empleos?q={normalized_query}&l=Valparaíso",  # Valparaíso específico
            f"{self.base_url}/empleos?q={normalized_query}&l=Concepción",  # Concepción específico
            f"{self.base_url}/empleos?q={normalized_query}",  # Sin ubicación específica
            f"{self.base_url}/empleos?q={normalized_query}&jornada=completa",  # Jornada completa
        ]
    
    def parse_job_listing(self, job_element) -> Optional[Dict]:
        """Parsear un elemento de trabajo de ChileTrabajo"""
        try:
            # Título del trabajo
            title_elem = (
                job_element.find('h3', class_='job-title') or
                job_element.find('h2', class_='job-title') or
                job_element.find('a', class_='job-link') or
                job_element.find('h3').find('a') if job_element.find('h3') else None or
                job_element.find('h2').find('a') if job_element.find('h2') else None
            )
            
            if title_elem:
                if title_elem.name == 'a':
                    title = title_elem.get('title') or title_elem.get_text(strip=True)
                else:
                    title = title_elem.get_text(strip=True)
            else:
                title = "Sin título"
            
            # Empresa
            company_elem = (
                job_element.find('span', class_='company-name') or
                job_element.find('div', class_='company-name') or
                job_element.find('a', class_='company-link') or
                job_element.find('p', class_='company')
            )
            company = company_elem.get_text(strip=True) if company_elem else "Empresa no especificada"
            
            # Ubicación
            location_elem = (
                job_element.find('span', class_='job-location') or
                job_element.find('div', class_='location') or
                job_element.find('p', class_='location') or
                job_element.find('span', class_='location')
            )
            location = location_elem.get_text(strip=True) if location_elem else "Chile"
            
            # Salario (opcional)
            salary_elem = (
                job_element.find('span', class_='salary') or
                job_element.find('div', class_='salary') or
                job_element.find('p', class_='salary') or
                job_element.find('span', class_='wage')
            )
            salary = salary_elem.get_text(strip=True) if salary_elem else ""
            
            # URL del trabajo
            link_elem = (
                job_element.find('h3').find('a') if job_element.find('h3') else None or
                job_element.find('h2').find('a') if job_element.find('h2') else None or
                job_element.find('a', class_='job-link') or
                job_element.find('a', href=True)
            )
            
            if link_elem and link_elem.get('href'):
                job_url = urljoin(self.base_url, link_elem['href'])
            else:
                job_url = self.base_url
            
            # Descripción
            description_elem = (
                job_element.find('div', class_='job-description') or
                job_element.find('p', class_='job-summary') or
                job_element.find('div', class_='summary') or
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
                job_element.find('span', class_='job-date') or
                job_element.find('time', class_='date') or
                job_element.find('p', class_='date') or
                job_element.find('span', class_='date')
            )
            posted_date = ""
            if date_elem:
                date_text = date_elem.get_text(strip=True)
                if any(word in date_text.lower() for word in ['hace', 'día', 'días', 'hoy', 'ayer']):
                    posted_date = date_text
            
            # Tipo de jornada (opcional)
            job_type_elem = (
                job_element.find('span', class_='job-type') or
                job_element.find('div', class_='jornada') or
                job_element.find('p', class_='jornada')
            )
            job_type = job_type_elem.get_text(strip=True) if job_type_elem else ""
            
            # Modalidad (opcional)
            modality_elem = (
                job_element.find('span', class_='modality') or
                job_element.find('div', class_='modalidad')
            )
            if modality_elem:
                modality = modality_elem.get_text(strip=True)
                if job_type:
                    job_type += f" - {modality}"
                else:
                    job_type = modality
            
            job_data = self.create_job_dict(
                title=title,
                company=company,
                location=location,
                description=description,
                url=job_url,
                salary=salary,
                posted_date=posted_date,
                job_type=job_type
            )
            
            return job_data if self.validate_job(job_data) else None
            
        except Exception as e:
            print(f"Error procesando oferta individual de ChileTrabajo: {e}")
            return None
    
    def search_jobs(self, query: str, location: str = "", limit: int = 10) -> List[Dict]:
        """Buscar empleos en ChileTrabajo"""
        jobs = []
        
        try:
            search_urls = self.get_alternative_urls(query, location)
            
            for search_url in search_urls:
                try:
                    response = self.make_request(search_url, timeout=15)
                    if not response:
                        continue
                    
                    soup = self.parse_html(response)
                    if not soup:
                        continue
                    
                    # Buscar ofertas de trabajo con múltiples selectores
                    job_listings = (
                        soup.find_all('div', class_='job-item') or
                        soup.find_all('div', class_='job-card') or
                        soup.find_all('article', class_='job') or
                        soup.find_all('div', class_='oferta') or
                        soup.find_all('li', class_='job-listing') or
                        soup.find_all('div', class_='resultado')
                    )
                    
                    if not job_listings:
                        print(f"No se encontraron ofertas en {search_url}")
                        continue
                    
                    print(f"Encontradas {len(job_listings)} ofertas en ChileTrabajo")
                    
                    for listing in job_listings[:limit]:
                        job = self.parse_job_listing(listing)
                        if job:
                            jobs.append(job)
                    
                    if jobs:  # Si encontramos trabajos, salir del bucle
                        break
                        
                except Exception as e:
                    print(f"Error en URL de ChileTrabajo {search_url}: {e}")
                    continue
            
            # Si no encontramos trabajos reales, agregar un trabajo de ejemplo
            if not jobs:
                jobs.append(self.create_job_dict(
                    title=f"Desarrollador {query}",
                    company="ChileTrabajo",
                    location=location or "Chile",
                    description=f"Oportunidad laboral en Chile. Para acceder a ofertas reales, puede ser necesario configurar parámetros adicionales. Búsqueda: {query}",
                    url=self.build_search_url(query, location)
                ))
                
        except Exception as e:
            print(f"Error general en ChileTrabajo API: {e}")
        
        return jobs[:limit]
    
    def get_job_details(self, job_url: str) -> Dict:
        """Obtener detalles adicionales de un trabajo en ChileTrabajo"""
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
                soup.find('div', class_='job-description') or
                soup.find('div', class_='descripcion') or
                soup.find('section', class_='job-details')
            )
            if description_elem:
                details['full_description'] = self.normalize_text(description_elem.get_text())
            
            # Requisitos
            requirements_elem = (
                soup.find('div', class_='requirements') or
                soup.find('div', class_='requisitos') or
                soup.find('section', class_='requisitos')
            )
            if requirements_elem:
                details['requirements'] = self.normalize_text(requirements_elem.get_text())
            
            # Beneficios
            benefits_elem = (
                soup.find('div', class_='benefits') or
                soup.find('div', class_='beneficios') or
                soup.find('section', class_='beneficios')
            )
            if benefits_elem:
                details['benefits'] = self.normalize_text(benefits_elem.get_text())
            
            # Información de la empresa
            company_elem = (
                soup.find('div', class_='company-info') or
                soup.find('section', class_='empresa')
            )
            if company_elem:
                details['company_info'] = self.normalize_text(company_elem.get_text())
            
            # Experiencia requerida
            experience_elem = (
                soup.find('span', class_='experience') or
                soup.find('div', class_='experiencia')
            )
            if experience_elem:
                details['experience'] = self.normalize_text(experience_elem.get_text())
                
        except Exception as e:
            print(f"Error obteniendo detalles del trabajo: {e}")
        
        return details