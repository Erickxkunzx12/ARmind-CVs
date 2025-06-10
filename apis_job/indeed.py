"""API para buscar empleos en Indeed usando Job Sync API oficial"""

import requests
import json
import base64
from typing import List, Dict, Optional
from urllib.parse import quote_plus, urljoin
from bs4 import BeautifulSoup
from .base_api import BaseJobAPI

class IndeedAPI(BaseJobAPI):
    """API para buscar empleos en Indeed usando Job Sync API oficial y web scraping como fallback"""
    
    def __init__(self, client_id: str = None, client_secret: str = None, access_token: str = None):
        super().__init__("Indeed", "https://co.indeed.com")
        
        # Configuración para Indeed Job Sync API oficial
        self.api_base_url = "https://apis.indeed.com"
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = access_token
        self.use_official_api = bool(access_token)
        
        # Headers para web scraping (fallback)
        self.session.headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-CO,es;q=0.8,en;q=0.6',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        })
        
        # Headers para API oficial
        if self.access_token:
            self.api_headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
    
    def get_oauth_token(self) -> Optional[str]:
        """Obtener token OAuth para Indeed Job Sync API"""
        if not self.client_id or not self.client_secret:
            print("Client ID y Client Secret son requeridos para OAuth")
            return None
            
        try:
            # Endpoint para obtener token (2-legged OAuth)
            token_url = "https://apis.indeed.com/oauth/v2/tokens"
            
            # Credenciales en base64
            credentials = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()
            
            headers = {
                'Authorization': f'Basic {credentials}',
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            data = {
                'grant_type': 'client_credentials',
                'scope': 'employer_access employer_hosted_job'
            }
            
            response = requests.post(token_url, headers=headers, data=data)
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data.get('access_token')
                self.api_headers = {
                    'Authorization': f'Bearer {self.access_token}',
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                }
                return self.access_token
            else:
                print(f"Error obteniendo token OAuth: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Error en autenticación OAuth: {e}")
            return None
    
    def search_jobs_official_api(self, query: str, location: str = "", limit: int = 10) -> List[Dict]:
        """Buscar empleos usando Indeed Job Sync API oficial"""
        if not self.access_token:
            print("Token de acceso requerido para usar la API oficial")
            return []
            
        try:
            # GraphQL query para buscar trabajos
            graphql_query = """
            query findEmployerJobsPartner($first: Int, $after: String) {
                findEmployerJobsPartner(first: $first, after: $after) {
                    pageInfo {
                        hasNextPage
                        endCursor
                    }
                    edges {
                        node {
                            id
                            jobData {
                                id
                                title
                                datePostedOnIndeed
                                dateCreated
                                description
                                company
                                jobLocation {
                                    countryCode
                                    admin1Code
                                    city
                                    postalCode
                                    fullAddress
                                }
                                externalJobPageUrl
                                externalPostingMetadata {
                                    jobPostingId
                                    jobRequisitionId
                                }
                            }
                            managementUrls {
                                viewJob
                            }
                            seatsConnection {
                                seats {
                                    jobPost {
                                        id
                                        status {
                                            surfaceStatuses {
                                                isRejected
                                                isSponsorshipRequired
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
            """
            
            variables = {
                "first": limit
            }
            
            payload = {
                "query": graphql_query,
                "variables": variables
            }
            
            response = requests.post(
                f"{self.api_base_url}/graphql",
                headers=self.api_headers,
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                jobs = []
                
                if 'data' in data and 'findEmployerJobsPartner' in data['data']:
                    edges = data['data']['findEmployerJobsPartner'].get('edges', [])
                    
                    for edge in edges:
                        job_node = edge.get('node', {})
                        job_data = job_node.get('jobData', {})
                        
                        # Filtrar por query si se proporciona
                        title = job_data.get('title', '')
                        description = job_data.get('description', '')
                        
                        if query.lower() in title.lower() or query.lower() in description.lower():
                            job_location = job_data.get('jobLocation', {})
                            
                            job = self.create_job_dict(
                                title=title,
                                company=job_data.get('company', 'Indeed'),
                                location=job_location.get('fullAddress', job_location.get('city', 'No especificada')),
                                description=description,
                                url=job_data.get('externalJobPageUrl', job_node.get('managementUrls', {}).get('viewJob', '')),
                                posted_date=job_data.get('datePostedOnIndeed', ''),
                                job_id=job_data.get('id', '')
                            )
                            
                            jobs.append(job)
                
                return jobs[:limit]
            else:
                print(f"Error en API oficial de Indeed: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            print(f"Error usando API oficial de Indeed: {e}")
            return []
    
    def build_search_url(self, query: str, location: str = "") -> str:
        """Construir URL de búsqueda para Indeed (web scraping fallback)"""
        normalized_query = quote_plus(query)
        normalized_location = quote_plus(location) if location else quote_plus("Colombia")
        
        return f"{self.base_url}/jobs?q={normalized_query}&l={normalized_location}"
    
    def get_alternative_urls(self, query: str, location: str = "") -> List[str]:
        """Obtener URLs alternativas para Indeed"""
        normalized_query = quote_plus(query)
        normalized_location = quote_plus(location) if location else quote_plus("Colombia")
        
        return [
            f"{self.base_url}/jobs?q={normalized_query}&l={normalized_location}",
            f"{self.base_url}/jobs?q={normalized_query}&l={normalized_location}&sort=date",
            f"{self.base_url}/jobs?q={normalized_query}&l={normalized_location}&fromage=1",  # Último día
            f"{self.base_url}/jobs?q={normalized_query}&l={normalized_location}&fromage=3",  # Últimos 3 días
            f"{self.base_url}/jobs?q={normalized_query}&l={normalized_location}&jt=fulltime",  # Tiempo completo
            f"{self.base_url}/jobs?q={normalized_query}",  # Sin ubicación específica
        ]
    
    def parse_job_listing(self, job_element) -> Optional[Dict]:
        """Parsear un elemento de trabajo de Indeed"""
        try:
            # Título del trabajo
            title_elem = (
                job_element.find('h2', class_='jobTitle') or
                job_element.find('a', {'data-jk': True}) or
                job_element.find('span', {'title': True}) or
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
                job_element.find('span', class_='companyName') or
                job_element.find('a', class_='companyName') or
                job_element.find('div', class_='companyName') or
                job_element.find('span', {'data-testid': 'company-name'})
            )
            company = company_elem.get_text(strip=True) if company_elem else "Empresa no especificada"
            
            # Ubicación
            location_elem = (
                job_element.find('div', class_='companyLocation') or
                job_element.find('span', class_='companyLocation') or
                job_element.find('div', {'data-testid': 'job-location'})
            )
            location = location_elem.get_text(strip=True) if location_elem else "Ubicación no especificada"
            
            # Salario (opcional)
            salary_elem = (
                job_element.find('span', class_='salary-snippet') or
                job_element.find('div', class_='salary-snippet') or
                job_element.find('span', class_='estimated-salary')
            )
            salary = salary_elem.get_text(strip=True) if salary_elem else ""
            
            # URL del trabajo
            link_elem = (
                job_element.find('h2', class_='jobTitle').find('a') if job_element.find('h2', class_='jobTitle') else None or
                job_element.find('a', {'data-jk': True}) or
                job_element.find('a', href=True)
            )
            
            if link_elem and link_elem.get('href'):
                job_url = urljoin(self.base_url, link_elem['href'])
            else:
                job_url = self.base_url
            
            # Descripción
            description_elem = (
                job_element.find('div', class_='job-snippet') or
                job_element.find('span', class_='job-snippet') or
                job_element.find('div', class_='summary')
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
                job_element.find('span', class_='date') or
                job_element.find('span', class_='visually-hidden') or
                job_element.find('time')
            )
            posted_date = ""
            if date_elem:
                date_text = date_elem.get_text(strip=True)
                if any(word in date_text.lower() for word in ['hace', 'day', 'hour', 'today', 'yesterday']):
                    posted_date = date_text
            
            # Tipo de trabajo (opcional)
            job_type_elem = (
                job_element.find('span', class_='jobType') or
                job_element.find('div', class_='jobType')
            )
            job_type = job_type_elem.get_text(strip=True) if job_type_elem else ""
            
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
            print(f"Error procesando oferta individual de Indeed: {e}")
            return None
    
    def search_jobs(self, query: str, location: str = "", limit: int = 10) -> List[Dict]:
        """Buscar empleos en Indeed usando API oficial o web scraping como fallback"""
        jobs = []
        
        # Intentar usar API oficial primero
        if self.use_official_api or (self.client_id and self.client_secret):
            print("Intentando usar Indeed Job Sync API oficial...")
            
            # Obtener token si no lo tenemos
            if not self.access_token and self.client_id and self.client_secret:
                self.get_oauth_token()
            
            # Usar API oficial si tenemos token
            if self.access_token:
                jobs = self.search_jobs_official_api(query, location, limit)
                if jobs:
                    print(f"Encontrados {len(jobs)} empleos usando API oficial de Indeed")
                    return jobs
                else:
                    print("No se encontraron empleos con la API oficial, usando web scraping...")
        
        # Fallback a web scraping
        print("Usando web scraping como método alternativo...")
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
                        soup.find_all('div', class_='job_seen_beacon') or
                        soup.find_all('div', class_='jobsearch-SerpJobCard') or
                        soup.find_all('div', class_='result') or
                        soup.find_all('a', {'data-jk': True}) or
                        soup.find_all('div', {'data-jk': True})
                    )
                    
                    if not job_listings:
                        print(f"No se encontraron ofertas en {search_url}")
                        continue
                    
                    print(f"Encontradas {len(job_listings)} ofertas en Indeed (web scraping)")
                    
                    for listing in job_listings[:limit]:
                        job = self.parse_job_listing(listing)
                        if job:
                            jobs.append(job)
                    
                    if jobs:  # Si encontramos trabajos, salir del bucle
                        break
                        
                except Exception as e:
                    print(f"Error en URL de Indeed {search_url}: {e}")
                    continue
            
            # Si no encontramos trabajos reales, agregar un trabajo informativo
            if not jobs:
                api_status = "API oficial disponible" if self.access_token else "Configurar credenciales OAuth para API oficial"
                jobs.append(self.create_job_dict(
                    title=f"Desarrollador {query}",
                    company="Indeed",
                    location=location or "Colombia",
                    description=f"Indeed Job Search - {api_status}. Búsqueda: {query}. Visite Indeed.com para ver ofertas actualizadas.",
                    url=self.build_search_url(query, location)
                ))
                
        except Exception as e:
            print(f"Error general en Indeed API: {e}")
        
        return jobs[:limit]
    
    def get_job_details(self, job_url: str) -> Dict:
        """Obtener detalles adicionales de un trabajo en Indeed"""
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
                soup.find('div', class_='jobsearch-jobDescriptionText') or
                soup.find('div', id='jobDescriptionText') or
                soup.find('div', class_='job-description')
            )
            if description_elem:
                details['full_description'] = self.normalize_text(description_elem.get_text())
            
            # Información de la empresa
            company_elem = soup.find('div', class_='jobsearch-CompanyInfoContainer')
            if company_elem:
                details['company_info'] = self.normalize_text(company_elem.get_text())
            
            # Beneficios
            benefits_elem = soup.find('div', class_='jobsearch-Benefits')
            if benefits_elem:
                details['benefits'] = self.normalize_text(benefits_elem.get_text())
                
        except Exception as e:
            print(f"Error obteniendo detalles del trabajo: {e}")
        
        return details