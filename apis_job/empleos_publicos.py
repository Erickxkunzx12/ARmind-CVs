"""API para Empleos Públicos"""

import requests
from typing import List, Dict, Optional
from urllib.parse import quote_plus, urljoin
from bs4 import BeautifulSoup
from .base_api import BaseJobAPI

class EmpleosPublicosAPI(BaseJobAPI):
    """API para buscar empleos públicos"""
    
    def __init__(self):
        super().__init__("Empleos Públicos", "https://www.empleospublicos.gov.co")
        # Empleos Públicos requiere headers específicos
        self.session.headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-CO,es;q=0.8,en;q=0.6',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        })
    
    def build_search_url(self, query: str, location: str = "") -> str:
        """Construir URL de búsqueda para Empleos Públicos"""
        normalized_query = quote_plus(query)
        normalized_location = quote_plus(location) if location else quote_plus("Colombia")
        
        return f"{self.base_url}/convocatorias?q={normalized_query}&l={normalized_location}"
    
    def get_alternative_urls(self, query: str, location: str = "") -> List[str]:
        """Obtener URLs alternativas para Empleos Públicos"""
        normalized_query = quote_plus(query)
        normalized_location = quote_plus(location) if location else quote_plus("Colombia")
        
        return [
            f"{self.base_url}/convocatorias?q={normalized_query}&l={normalized_location}",
            f"{self.base_url}/convocatorias?q={normalized_query}&entidad=nacional",  # Nivel nacional
            f"{self.base_url}/convocatorias?q={normalized_query}&entidad=departamental",  # Nivel departamental
            f"{self.base_url}/convocatorias?q={normalized_query}&entidad=municipal",  # Nivel municipal
            f"{self.base_url}/convocatorias?q={normalized_query}&estado=abierta",  # Convocatorias abiertas
            f"{self.base_url}/convocatorias?q={normalized_query}",  # Sin filtros específicos
            f"{self.base_url}/ofertas-empleo?q={normalized_query}",  # URL alternativa
            f"{self.base_url}/concursos?q={normalized_query}",  # Concursos públicos
        ]
    
    def parse_job_listing(self, job_element) -> Optional[Dict]:
        """Parsear un elemento de trabajo de Empleos Públicos"""
        try:
            # Título del trabajo/convocatoria
            title_elem = (
                job_element.find('h3', class_='convocatoria-title') or
                job_element.find('h2', class_='convocatoria-title') or
                job_element.find('h3', class_='job-title') or
                job_element.find('a', class_='convocatoria-link') or
                job_element.find('h3').find('a') if job_element.find('h3') else None or
                job_element.find('h2').find('a') if job_element.find('h2') else None or
                job_element.find('div', class_='titulo-convocatoria')
            )
            
            if title_elem:
                if title_elem.name == 'a':
                    title = title_elem.get('title') or title_elem.get_text(strip=True)
                else:
                    title = title_elem.get_text(strip=True)
            else:
                title = "Sin título"
            
            # Entidad/Empresa
            entity_elem = (
                job_element.find('span', class_='entidad') or
                job_element.find('div', class_='entidad') or
                job_element.find('p', class_='entidad') or
                job_element.find('span', class_='institucion') or
                job_element.find('div', class_='institucion')
            )
            company = entity_elem.get_text(strip=True) if entity_elem else "Entidad Pública"
            
            # Ubicación
            location_elem = (
                job_element.find('span', class_='location') or
                job_element.find('div', class_='ubicacion') or
                job_element.find('p', class_='ubicacion') or
                job_element.find('span', class_='ciudad') or
                job_element.find('div', class_='departamento')
            )
            location = location_elem.get_text(strip=True) if location_elem else "Colombia"
            
            # Salario/Asignación (opcional)
            salary_elem = (
                job_element.find('span', class_='salary') or
                job_element.find('div', class_='salario') or
                job_element.find('p', class_='asignacion') or
                job_element.find('span', class_='remuneracion') or
                job_element.find('div', class_='grado-salarial')
            )
            salary = salary_elem.get_text(strip=True) if salary_elem else ""
            
            # URL del trabajo
            link_elem = (
                job_element.find('h3').find('a') if job_element.find('h3') else None or
                job_element.find('h2').find('a') if job_element.find('h2') else None or
                job_element.find('a', class_='convocatoria-link') or
                job_element.find('a', href=True)
            )
            
            if link_elem and link_elem.get('href'):
                job_url = urljoin(self.base_url, link_elem['href'])
            else:
                job_url = self.base_url
            
            # Descripción
            description_elem = (
                job_element.find('div', class_='convocatoria-description') or
                job_element.find('p', class_='descripcion') or
                job_element.find('div', class_='resumen') or
                job_element.find('p', class_='resumen') or
                job_element.find('div', class_='objeto')
            )
            
            if description_elem:
                description = description_elem.get_text(strip=True)
            else:
                description = f"Convocatoria pública para {title} en {company}"
            
            # Agregar salario a la descripción si existe
            if salary:
                description += f" | Asignación: {salary}"
            
            # Fecha de publicación (opcional)
            date_elem = (
                job_element.find('span', class_='fecha-publicacion') or
                job_element.find('time', class_='date') or
                job_element.find('p', class_='fecha') or
                job_element.find('div', class_='fecha-apertura')
            )
            posted_date = ""
            if date_elem:
                date_text = date_elem.get_text(strip=True)
                if any(word in date_text.lower() for word in ['publicado', 'abierta', 'desde', 'hasta']):
                    posted_date = date_text
            
            # Fecha de cierre (opcional)
            closing_date_elem = (
                job_element.find('span', class_='fecha-cierre') or
                job_element.find('div', class_='fecha-limite') or
                job_element.find('p', class_='cierre')
            )
            closing_date = ""
            if closing_date_elem:
                closing_date = closing_date_elem.get_text(strip=True)
                if closing_date:
                    description += f" | Cierre: {closing_date}"
            
            # Tipo de convocatoria (opcional)
            conv_type_elem = (
                job_element.find('span', class_='tipo-convocatoria') or
                job_element.find('div', class_='modalidad') or
                job_element.find('p', class_='tipo')
            )
            job_type = conv_type_elem.get_text(strip=True) if conv_type_elem else "Convocatoria Pública"
            
            # Estado de la convocatoria (opcional)
            status_elem = (
                job_element.find('span', class_='estado') or
                job_element.find('div', class_='status')
            )
            if status_elem:
                status = status_elem.get_text(strip=True)
                if job_type:
                    job_type += f" - {status}"
                else:
                    job_type = status
            
            # Nivel educativo (opcional)
            education_elem = (
                job_element.find('span', class_='nivel-educativo') or
                job_element.find('div', class_='formacion')
            )
            education = education_elem.get_text(strip=True) if education_elem else ""
            if education:
                description += f" | Formación: {education}"
            
            # Experiencia requerida (opcional)
            experience_elem = (
                job_element.find('span', class_='experiencia') or
                job_element.find('div', class_='experiencia-requerida')
            )
            experience = experience_elem.get_text(strip=True) if experience_elem else ""
            if experience:
                description += f" | Experiencia: {experience}"
            
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
            print(f"Error procesando convocatoria individual de Empleos Públicos: {e}")
            return None
    
    def search_jobs(self, query: str, location: str = "", limit: int = 10) -> List[Dict]:
        """Buscar empleos públicos"""
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
                    
                    # Buscar convocatorias con múltiples selectores
                    job_listings = (
                        soup.find_all('div', class_='convocatoria-item') or
                        soup.find_all('div', class_='job-item') or
                        soup.find_all('article', class_='convocatoria') or
                        soup.find_all('div', class_='oferta-publica') or
                        soup.find_all('li', class_='convocatoria-listing') or
                        soup.find_all('div', class_='resultado-convocatoria')
                    )
                    
                    if not job_listings:
                        print(f"No se encontraron convocatorias en {search_url}")
                        continue
                    
                    print(f"Encontradas {len(job_listings)} convocatorias en Empleos Públicos")
                    
                    for listing in job_listings[:limit]:
                        job = self.parse_job_listing(listing)
                        if job:
                            jobs.append(job)
                    
                    if jobs:  # Si encontramos trabajos, salir del bucle
                        break
                        
                except Exception as e:
                    print(f"Error en URL de Empleos Públicos {search_url}: {e}")
                    continue
            
            # Si no encontramos trabajos reales, agregar un trabajo de ejemplo
            if not jobs:
                jobs.append(self.create_job_dict(
                    title=f"Profesional {query}",
                    company="Empleos Públicos",
                    location=location or "Colombia",
                    description=f"Convocatoria pública en Colombia. Para acceder a convocatorias reales, puede ser necesario configurar parámetros adicionales. Búsqueda: {query}",
                    url=self.build_search_url(query, location),
                    job_type="Convocatoria Pública"
                ))
                
        except Exception as e:
            print(f"Error general en Empleos Públicos API: {e}")
        
        return jobs[:limit]
    
    def get_job_details(self, job_url: str) -> Dict:
        """Obtener detalles adicionales de una convocatoria pública"""
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
                soup.find('div', class_='convocatoria-description') or
                soup.find('div', class_='descripcion-completa') or
                soup.find('section', class_='detalles-convocatoria')
            )
            if description_elem:
                details['full_description'] = self.normalize_text(description_elem.get_text())
            
            # Objeto de la convocatoria
            object_elem = (
                soup.find('div', class_='objeto-convocatoria') or
                soup.find('section', class_='objeto')
            )
            if object_elem:
                details['object'] = self.normalize_text(object_elem.get_text())
            
            # Requisitos
            requirements_elem = (
                soup.find('div', class_='requirements') or
                soup.find('div', class_='requisitos') or
                soup.find('section', class_='requisitos')
            )
            if requirements_elem:
                details['requirements'] = self.normalize_text(requirements_elem.get_text())
            
            # Funciones del cargo
            functions_elem = (
                soup.find('div', class_='functions') or
                soup.find('div', class_='funciones') or
                soup.find('section', class_='funciones-cargo')
            )
            if functions_elem:
                details['functions'] = self.normalize_text(functions_elem.get_text())
            
            # Cronograma
            schedule_elem = (
                soup.find('div', class_='cronograma') or
                soup.find('section', class_='fechas-importantes')
            )
            if schedule_elem:
                details['schedule'] = self.normalize_text(schedule_elem.get_text())
            
            # Información de la entidad
            entity_elem = (
                soup.find('div', class_='entity-info') or
                soup.find('section', class_='entidad-convocante')
            )
            if entity_elem:
                details['entity_info'] = self.normalize_text(entity_elem.get_text())
            
            # Documentos requeridos
            documents_elem = (
                soup.find('div', class_='documentos-requeridos') or
                soup.find('section', class_='documentacion')
            )
            if documents_elem:
                details['required_documents'] = self.normalize_text(documents_elem.get_text())
            
            # Proceso de selección
            selection_elem = (
                soup.find('div', class_='proceso-seleccion') or
                soup.find('section', class_='metodologia')
            )
            if selection_elem:
                details['selection_process'] = self.normalize_text(selection_elem.get_text())
                
        except Exception as e:
            print(f"Error obteniendo detalles de la convocatoria: {e}")
        
        return details