"""Servicio de Cache con Redis para ARMind"""

import redis
import json
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging
from functools import wraps

logger = logging.getLogger(__name__)

class CacheService:
    """Servicio de cache distribuido con Redis"""
    
    def __init__(self, redis_url: str = 'redis://localhost:6379/0'):
        try:
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            # Test connection
            self.redis_client.ping()
            self.available = True
            logger.info("✅ Redis cache conectado exitosamente")
        except Exception as e:
            logger.warning(f"⚠️ Redis no disponible: {e}. Cache deshabilitado.")
            self.redis_client = None
            self.available = False
    
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Generar clave única para cache"""
        key_data = f"{prefix}:{':'.join(map(str, args))}:{json.dumps(kwargs, sort_keys=True)}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """Obtener valor del cache"""
        if not self.available:
            return None
        
        try:
            cached_data = self.redis_client.get(key)
            if cached_data:
                return json.loads(cached_data)
        except Exception as e:
            logger.error(f"Error al obtener del cache: {e}")
        return None
    
    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Guardar valor en cache"""
        if not self.available:
            return False
        
        try:
            serialized_value = json.dumps(value, default=str)
            return self.redis_client.setex(key, ttl, serialized_value)
        except Exception as e:
            logger.error(f"Error al guardar en cache: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Eliminar valor del cache"""
        if not self.available:
            return False
        
        try:
            return bool(self.redis_client.delete(key))
        except Exception as e:
            logger.error(f"Error al eliminar del cache: {e}")
            return False
    
    def cache_cv_analysis(self, cv_content: str, analysis_result: Dict, ttl: int = 3600) -> str:
        """Cache específico para análisis de CV"""
        cv_hash = hashlib.md5(cv_content.encode()).hexdigest()
        key = f"cv_analysis:{cv_hash}"
        
        cache_data = {
            'result': analysis_result,
            'timestamp': datetime.now().isoformat(),
            'ttl': ttl
        }
        
        self.set(key, cache_data, ttl)
        return cv_hash
    
    def get_cached_cv_analysis(self, cv_content: str) -> Optional[Dict]:
        """Obtener análisis de CV desde cache"""
        cv_hash = hashlib.md5(cv_content.encode()).hexdigest()
        key = f"cv_analysis:{cv_hash}"
        return self.get(key)
    
    def cache_job_search(self, query: str, location: str, results: list, ttl: int = 1800) -> None:
        """Cache específico para búsqueda de empleos"""
        key = self._generate_key('job_search', query, location)
        
        cache_data = {
            'results': results,
            'query': query,
            'location': location,
            'timestamp': datetime.now().isoformat(),
            'count': len(results)
        }
        
        self.set(key, cache_data, ttl)
    
    def get_cached_job_search(self, query: str, location: str) -> Optional[Dict]:
        """Obtener búsqueda de empleos desde cache"""
        key = self._generate_key('job_search', query, location)
        return self.get(key)
    
    def cache_user_session(self, user_id: int, session_data: Dict, ttl: int = 86400) -> None:
        """Cache para datos de sesión de usuario"""
        key = f"user_session:{user_id}"
        self.set(key, session_data, ttl)
    
    def get_user_session(self, user_id: int) -> Optional[Dict]:
        """Obtener datos de sesión de usuario"""
        key = f"user_session:{user_id}"
        return self.get(key)
    
    def invalidate_user_cache(self, user_id: int) -> None:
        """Invalidar todo el cache de un usuario"""
        if not self.available:
            return
        
        try:
            # Buscar todas las claves relacionadas con el usuario
            pattern = f"*user:{user_id}*"
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)
            
            # También invalidar sesión
            session_key = f"user_session:{user_id}"
            self.delete(session_key)
            
        except Exception as e:
            logger.error(f"Error al invalidar cache de usuario {user_id}: {e}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del cache"""
        if not self.available:
            return {'available': False}
        
        try:
            info = self.redis_client.info()
            return {
                'available': True,
                'connected_clients': info.get('connected_clients', 0),
                'used_memory_human': info.get('used_memory_human', '0B'),
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0),
                'hit_rate': self._calculate_hit_rate(info)
            }
        except Exception as e:
            logger.error(f"Error al obtener estadísticas: {e}")
            return {'available': False, 'error': str(e)}
    
    def _calculate_hit_rate(self, info: Dict) -> float:
        """Calcular tasa de aciertos del cache"""
        hits = info.get('keyspace_hits', 0)
        misses = info.get('keyspace_misses', 0)
        total = hits + misses
        return (hits / total * 100) if total > 0 else 0.0


def cache_result(prefix: str, ttl: int = 3600, key_func=None):
    """Decorador para cachear resultados de funciones"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Obtener instancia de cache desde la aplicación
            from flask import current_app
            cache_service = getattr(current_app, 'cache_service', None)
            
            if not cache_service or not cache_service.available:
                return func(*args, **kwargs)
            
            # Generar clave de cache
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = cache_service._generate_key(prefix, *args, **kwargs)
            
            # Intentar obtener del cache
            cached_result = cache_service.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit para {func.__name__}")
                return cached_result
            
            # Ejecutar función y cachear resultado
            result = func(*args, **kwargs)
            cache_service.set(cache_key, result, ttl)
            logger.debug(f"Cache miss para {func.__name__}, resultado cacheado")
            
            return result
        return wrapper
    return decorator


# Instancia global del servicio de cache
cache_service = None

def init_cache(app):
    """Inicializar servicio de cache con la aplicación Flask"""
    global cache_service
    
    redis_url = app.config.get('REDIS_URL', 'redis://localhost:6379/0')
    cache_service = CacheService(redis_url)
    app.cache_service = cache_service
    
    return cache_service