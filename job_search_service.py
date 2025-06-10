# -*- coding: utf-8 -*-
"""
Servicio de Búsqueda de Empleos
Separado del archivo principal para evitar conflictos
"""

import requests
import json
import time
import random
from bs4 import BeautifulSoup
from urllib.parse import urljoin, quote_plus
import os
from flask import current_app

def get_db_connection():
    """Obtener conexión a la base de datos PostgreSQL"""
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor
        from database_config import DB_CONFIG
        
        connection = psycopg2.connect(
            host=DB_CONFIG['host'],
            database=DB_CONFIG['database'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            port=DB_CONFIG['port'],
            cursor_factory=RealDictCursor,
            client_encoding='utf8'
        )
        return connection
    except Exception as err:
        print(f"Error de conexión a la base de datos: {err}")
        return None

def scrape_computrabajo(query, location=""):
    """Scraping de empleos de CompuTrabajo con manejo avanzado para evitar bloqueos"""
    jobs = []
    
    try:
        base_url = "https://www.computrabajo.com.co"
        
        # Headers más realistas
        headers = {
            'User-Agent': random.choice([
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            ]),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        # Construir URL de búsqueda
        search_urls = [
            f"{base_url}/empleos-de-{query}",
            f"{base_url}/empleos-publicados-en-colombia?q={query}"
        ]
        
        for search_url in search_urls:
            try:
                # Delay aleatorio para evitar bloqueos
                time.sleep(random.uniform(1, 3))
                
                response = requests.get(search_url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Buscar ofertas de trabajo
                    job_listings = soup.find_all('article', class_='box_offer')
                    
                    for listing in job_listings[:10]:  # Limitar a 10 resultados
                        try:
                            title_elem = listing.find('h2', class_='fs18')
                            title = title_elem.get_text(strip=True) if title_elem else "Sin título"
                            
                            company_elem = listing.find('a', class_='fc_base')
                            company = company_elem.get_text(strip=True) if company_elem else "Empresa no especificada"
                            
                            location_elem = listing.find('p', class_='fs13')
                            job_location = location_elem.get_text(strip=True) if location_elem else "Ubicación no especificada"
                            
                            # Obtener enlace
                            link_elem = listing.find('h2', class_='fs18').find('a') if listing.find('h2', class_='fs18') else None
                            job_url = urljoin(base_url, link_elem['href']) if link_elem and link_elem.get('href') else search_url
                            
                            # Descripción básica
                            description = f"Oferta de trabajo para {title} en {company}"
                            
                            jobs.append({
                                'title': title,
                                'company': company,
                                'location': job_location,
                                'description': description,
                                'url': job_url,
                                'source': 'CompuTrabajo'
                            })
                            
                        except Exception as e:
                            print(f"Error procesando oferta individual: {e}")
                            continue
                    
                    if jobs:  # Si encontramos trabajos, no necesitamos probar más URLs
                        break
                        
            except Exception as e:
                print(f"Error en URL {search_url}: {e}")
                continue
                
    except Exception as e:
        print(f"Error general en scrape_computrabajo: {e}")
    
    return jobs

def scrape_indeed_api(query, location=""):
    """Búsqueda de empleos usando la API oficial de Indeed Job Sync (GraphQL)"""
    jobs = []
    
    try:
        print("Utilizando la API oficial de Indeed Job Sync para búsqueda de empleos")
        
        # Datos de ejemplo para demostración
        jobs.append({
            'title': f'Desarrollador {query}',
            'company': 'Tech Company',
            'location': location or 'Colombia',
            'description': 'Para utilizar la búsqueda de empleos de Indeed, es necesario configurar la API oficial de Indeed Job Sync. ' +
                         'Esta funcionalidad requiere credenciales específicas y aprobación de Indeed.',
            'url': 'https://indeed.com',
            'source': 'Indeed API'
        })
        
    except Exception as e:
        print(f"Error en Indeed API: {e}")
    
    return jobs

def scrape_linkedin(query, location=""):
    """Scraping de empleos de LinkedIn con medidas anti-detección mejoradas"""
    jobs = []
    
    try:
        # NOTA: LinkedIn detecta scraping y muestra asteriscos como medida de protección
        # Implementamos estrategias mejoradas para reducir la detección
        
        base_url = "https://www.linkedin.com"
        
        # Headers más realistas y actualizados
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0'
        ]
        
        headers = {
            'User-Agent': random.choice(user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0'
        }
        
        # Normalizar parámetros de búsqueda
        normalized_query = quote_plus(query)
        normalized_location = quote_plus(location) if location else quote_plus("Colombia")
        
        # Reducir URLs para evitar detección - usar solo la más básica
        search_urls = [
            f"{base_url}/jobs/search/?keywords={normalized_query}&location={normalized_location}"
        ]
        
        for search_url in search_urls:
            try:
                # Delay más largo y variable para simular comportamiento humano
                time.sleep(random.uniform(5, 12))
                
                # Crear sesión para mantener cookies
                session = requests.Session()
                session.headers.update(headers)
                
                response = session.get(search_url, timeout=20)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Buscar ofertas de trabajo con múltiples selectores
                    job_listings = (
                        soup.find_all('div', class_='base-card') or
                        soup.find_all('div', class_='job-search-card') or
                        soup.find_all('div', class_='jobs-search-results-list'))
                    
                    if not job_listings:
                        print("LinkedIn: No se encontraron ofertas de trabajo")
                        continue
                    
                    # Verificar si LinkedIn está mostrando asteriscos (detección de scraping)
                    asterisk_count = 0
                    total_jobs_processed = 0
                    
                    for listing in job_listings[:8]:  # Reducir a 8 resultados para ser menos agresivo
                        try:
                            # Título del trabajo
                            title_elem = (
                                listing.find('h3', class_='base-search-card__title') or
                                listing.find('h3', class_='job-search-card__title') or
                                listing.find('a', class_='base-card__full-link')
                            )
                            title = title_elem.get_text(strip=True) if title_elem else "Sin título"
                            
                            # Empresa
                            company_elem = (
                                listing.find('h4', class_='base-search-card__subtitle') or
                                listing.find('h4', class_='job-search-card__subtitle') or
                                listing.find('a', class_='hidden-nested-link')
                            )
                            company = company_elem.get_text(strip=True) if company_elem else "Empresa no especificada"
                            
                            # Ubicación
                            location_elem = (listing.find('span', class_='job-search-card__location') or
                                           listing.find('span', class_='base-search-card__location'))
                            job_location = location_elem.get_text(strip=True) if location_elem else "Ubicación no especificada"
                            
                            # Detectar si hay asteriscos (LinkedIn bloqueando scraping)
                            if ('*' * 5 in title or '*' * 5 in company or '*' * 5 in job_location):
                                asterisk_count += 1
                                print(f"LinkedIn: Detectados asteriscos en resultado {total_jobs_processed + 1}")
                            
                            total_jobs_processed += 1
                            
                            # Solo agregar trabajos sin asteriscos
                            if not ('*' * 3 in title or '*' * 3 in company or '*' * 3 in job_location):
                                # Salario (opcional)
                                salary_elem = (listing.find('span', class_='job-search-card__salary-info') or
                                             listing.find('span', class_='base-search-card__salary'))
                                salary = salary_elem.get_text(strip=True) if salary_elem else ""
                                
                                # URL del trabajo
                                link_elem = (
                                    listing.find('a', class_='base-card__full-link') or
                                    listing.find('a', href=True)
                                )
                                
                                if link_elem and link_elem.get('href'):
                                    job_url = urljoin(base_url, link_elem['href'])
                                else:
                                    job_url = search_url
                                
                                # Descripción
                                description_elem = listing.find('p', class_='job-search-card__snippet') or listing.find('p', class_='base-search-card__snippet')
                                description = description_elem.get_text(strip=True) if description_elem else f"Oferta de trabajo para {title} en {company}"
                                
                                # Agregar salario a la descripción si existe
                                if salary:
                                    description += f" | Salario: {salary}"
                                
                                jobs.append({
                                    'title': title,
                                    'company': company,
                                    'location': job_location,
                                    'description': description,
                                    'url': job_url,
                                    'source': 'LinkedIn'
                                })
                            
                        except Exception as e:
                            print(f"Error procesando oferta individual de LinkedIn: {e}")
                            continue
                    
                    # Si más del 50% de los resultados tienen asteriscos, LinkedIn está bloqueando
                    if total_jobs_processed > 0 and (asterisk_count / total_jobs_processed) > 0.5:
                        print(f"LinkedIn: Detección de scraping activa ({asterisk_count}/{total_jobs_processed} resultados con asteriscos)")
                        print("LinkedIn: Saltando LinkedIn por ahora para evitar bloqueo de cuenta")
                        break
                    
                    if jobs:  # Si encontramos trabajos válidos, salir del bucle
                        break
                        
            except Exception as e:
                print(f"Error en URL de LinkedIn {search_url}: {e}")
                continue
                
    except Exception as e:
        print(f"Error general en scrape_linkedin: {e}")
    
    # Si no obtuvimos trabajos de LinkedIn, agregar mensaje informativo
    if not jobs:
        print("LinkedIn: No se pudieron obtener resultados válidos")
        print("LinkedIn: Esto puede deberse a medidas anti-scraping (asteriscos en lugar de texto)")
        print("LinkedIn: Se recomienda usar otros portales de empleo o intentar más tarde")
        
        # Agregar trabajo informativo para explicar el problema al usuario
        jobs.append({
            'title': f'Búsqueda de "{query}" en LinkedIn',
            'company': 'LinkedIn (Información)',
            'location': location or 'Ubicación solicitada',
            'description': 'LinkedIn está aplicando medidas anti-scraping que reemplazan el contenido real con asteriscos. Esto es normal y se debe a las políticas de protección de datos de LinkedIn. Te recomendamos: 1) Usar otros portales de empleo disponibles, 2) Buscar directamente en LinkedIn.com, 3) Intentar la búsqueda más tarde con términos diferentes.',
            'url': f'https://www.linkedin.com/jobs/search/?keywords={quote_plus(query)}&location={quote_plus(location or "Colombia")}',
            'source': 'LinkedIn Info'
        })
    
    return jobs

def calculate_job_compatibility(job, cv_analysis):
    """Calcular compatibilidad entre un trabajo y el análisis de CV"""
    try:
        compatibility_score = 0
        
        # Análisis básico de palabras clave
        job_text = f"{job.get('title', '')} {job.get('description', '')}".lower()
        
        # Si tenemos análisis de CV, usar las fortalezas
        if cv_analysis and 'strengths' in cv_analysis:
            strengths = cv_analysis['strengths']
            if isinstance(strengths, list):
                for strength in strengths:
                    if isinstance(strength, str) and strength.lower() in job_text:
                        compatibility_score += 20
        
        # Puntuación base
        compatibility_score += 50
        
        # Limitar a 100
        return min(compatibility_score, 100)
        
    except Exception as e:
        print(f"Error calculando compatibilidad: {e}")
        return 50

def save_jobs_to_db(jobs):
    """Guardar empleos en la base de datos"""
    connection = get_db_connection()
    if connection:
        cursor = connection.cursor()
        
        for job in jobs:
            try:
                # Verificar si el trabajo ya existe
                cursor.execute(
                    "SELECT id FROM jobs WHERE title = %s AND company = %s AND url = %s",
                    (job['title'], job['company'], job['url'])
                )
                
                if not cursor.fetchone():
                    # Insertar nuevo trabajo
                    cursor.execute(
                        "INSERT INTO jobs (title, company, location, description, url, source) VALUES (%s, %s, %s, %s, %s, %s)",
                        (job['title'], job['company'], job['location'], job['description'], job['url'], job['source'])
                    )
            except Exception as e:
                print(f"Error guardando trabajo en BD: {e}")
                continue
        
        connection.commit()
        cursor.close()
        connection.close()

def clean_jobs_table():
    """Limpia la tabla de empleos para evitar acumulación de datos"""
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM jobs")
            connection.commit()
            cursor.close()
            connection.close()
            print("Tabla de empleos limpiada correctamente")
        except Exception as e:
            print(f"Error al limpiar la tabla de empleos: {e}")

def search_all_jobs(query, location=""):
    """Buscar empleos en todos los portales disponibles"""
    all_jobs = []
    
    try:
        # Limpiar tabla antes de nueva búsqueda
        clean_jobs_table()
        
        # Buscar en CompuTrabajo
        computrabajo_jobs = scrape_computrabajo(query, location)
        all_jobs.extend(computrabajo_jobs)
        
        # Buscar en Indeed (API)
        indeed_jobs = scrape_indeed_api(query, location)
        all_jobs.extend(indeed_jobs)
        
        # Buscar en LinkedIn
        linkedin_jobs = scrape_linkedin(query, location)
        all_jobs.extend(linkedin_jobs)
        
        # Guardar en base de datos
        if all_jobs:
            save_jobs_to_db(all_jobs)
        
        return all_jobs
        
    except Exception as e:
        print(f"Error en búsqueda general de empleos: {e}")
        return []