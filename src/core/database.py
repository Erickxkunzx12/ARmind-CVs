# Servicios de base de datos
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Optional, Dict, Any, List
from .models import UserProfile, CVDocument, CVAnalysisResult
import logging

logger = logging.getLogger(__name__)

class DatabaseService:
    """Servicio centralizado para operaciones de base de datos"""
    
    def __init__(self):
        self.connection = None
    
    def get_connection(self):
        """Obtener conexión a la base de datos"""
        if self.connection and not self.connection.closed:
            return self.connection
        
        try:
            # Configuración de PostgreSQL
            db_config = {
                'host': os.getenv('DB_HOST', 'localhost'),
                'port': os.getenv('DB_PORT', '5432'),
                'database': os.getenv('DB_NAME', 'armind_db'),
                'user': os.getenv('DB_USER', 'postgres'),
                'password': os.getenv('DB_PASSWORD', '')
            }
            
            self.connection = psycopg2.connect(**db_config)
            logger.info("Conexión a PostgreSQL establecida")
            return self.connection
            
        except Exception as e:
            logger.error(f"Error conectando a PostgreSQL: {e}")
            return None
    
    def test_connection(self) -> bool:
        """Probar conexión a la base de datos"""
        try:
            connection = self.get_connection()
            if connection and not connection.closed:
                # Ejecutar una consulta simple para verificar la conexión
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    cursor.fetchone()
                logger.info("Conexión a base de datos verificada")
                return True
            return False
        except Exception as e:
            logger.error(f"Error probando conexión a base de datos: {e}")
            return False
    
    def close_connection(self):
        """Cerrar conexión a la base de datos"""
        if self.connection and not self.connection.closed:
            self.connection.close()
            logger.info("Conexión a base de datos cerrada")
    
    def execute_query(self, query: str, params: tuple = None, fetch: bool = False):
        """Ejecutar consulta SQL"""
        connection = self.get_connection()
        if not connection:
            return None
        
        try:
            with connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, params)
                
                if fetch:
                    if 'SELECT' in query.upper():
                        return cursor.fetchall()
                    else:
                        return cursor.fetchone()
                else:
                    connection.commit()
                    return cursor.rowcount
                    
        except Exception as e:
            logger.error(f"Error ejecutando consulta: {e}")
            connection.rollback()
            return None
    
    def get_user_by_id(self, user_id: int) -> Optional[UserProfile]:
        """Obtener usuario por ID"""
        query = "SELECT * FROM users WHERE id = %s"
        result = self.execute_query(query, (user_id,), fetch=True)
        
        if result:
            user_data = result[0] if isinstance(result, list) else result
            return UserProfile(
                id=user_data['id'],
                email=user_data['email'],
                name=user_data.get('name', ''),
                is_admin=user_data.get('is_admin', False),
                is_verified=user_data.get('is_verified', False),
                is_active=user_data.get('is_active', True),
                created_at=user_data.get('created_at'),
                last_login=user_data.get('last_login')
            )
        return None
    
    def get_user_by_email(self, email: str) -> Optional[UserProfile]:
        """Obtener usuario por email"""
        query = "SELECT * FROM users WHERE email = %s"
        result = self.execute_query(query, (email,), fetch=True)
        
        if result:
            user_data = result[0] if isinstance(result, list) else result
            return UserProfile(
                id=user_data['id'],
                email=user_data['email'],
                name=user_data.get('name', ''),
                is_admin=user_data.get('is_admin', False),
                is_verified=user_data.get('is_verified', False),
                is_active=user_data.get('is_active', True),
                created_at=user_data.get('created_at'),
                last_login=user_data.get('last_login')
            )
        return None
    
    def create_user(self, email: str, password_hash: str, name: str = '') -> Optional[int]:
        """Crear nuevo usuario"""
        query = """
            INSERT INTO users (email, password, name, is_verified, created_at)
            VALUES (%s, %s, %s, %s, NOW())
            RETURNING id
        """
        result = self.execute_query(query, (email, password_hash, name, False), fetch=True)
        
        if result:
            return result[0]['id'] if isinstance(result, list) else result['id']
        return None
    
    def save_cv_document(self, cv_doc: CVDocument) -> Optional[int]:
        """Guardar documento de CV"""
        query = """
            INSERT INTO resumes (user_id, filename, content, created_at)
            VALUES (%s, %s, %s, NOW())
            RETURNING id
        """
        result = self.execute_query(
            query, 
            (cv_doc.user_id, cv_doc.filename, cv_doc.content),
            fetch=True
        )
        
        if result:
            return result[0]['id'] if isinstance(result, list) else result['id']
        return None
    
    def get_user_cvs(self, user_id: int) -> List[CVDocument]:
        """Obtener CVs de un usuario"""
        query = "SELECT * FROM resumes WHERE user_id = %s ORDER BY created_at DESC"
        results = self.execute_query(query, (user_id,), fetch=True)
        
        cvs = []
        if results:
            for row in results:
                cvs.append(CVDocument(
                    id=row['id'],
                    user_id=row['user_id'],
                    filename=row['filename'],
                    content=row['content'],
                    file_type=row.get('file_type', 'text'),
                    upload_date=row['created_at'],
                    file_size=row.get('file_size', 0)
                ))
        return cvs
    
    def save_analysis_result(self, user_id: int, cv_id: int, analysis: CVAnalysisResult) -> Optional[int]:
        """Guardar resultado de análisis"""
        query = """
            INSERT INTO feedback (resume_id, ai_provider, analysis_type, score, 
                                strengths, weaknesses, recommendations, keywords, 
                                created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
            RETURNING id
        """
        
        # Convertir listas a strings JSON
        import json
        strengths_json = json.dumps(analysis.strengths)
        weaknesses_json = json.dumps(analysis.weaknesses)
        recommendations_json = json.dumps(analysis.recommendations)
        keywords_json = json.dumps(analysis.keywords)
        
        result = self.execute_query(
            query,
            (cv_id, analysis.ai_provider, analysis.analysis_type, analysis.score,
             strengths_json, weaknesses_json, recommendations_json, keywords_json),
            fetch=True
        )
        
        if result:
            return result[0]['id'] if isinstance(result, list) else result['id']
        return None
    
    def get_user_analyses(self, user_id: int) -> List[Dict[str, Any]]:
        """Obtener análisis de un usuario"""
        query = """
            SELECT f.*, r.filename 
            FROM feedback f
            JOIN resumes r ON f.resume_id = r.id
            WHERE r.user_id = %s
            ORDER BY f.created_at DESC
        """
        results = self.execute_query(query, (user_id,), fetch=True)
        
        analyses = []
        if results:
            import json
            for row in results:
                try:
                    analysis_data = {
                        'id': row['id'],
                        'filename': row['filename'],
                        'ai_provider': row['ai_provider'],
                        'analysis_type': row['analysis_type'],
                        'score': row['score'],
                        'strengths': json.loads(row['strengths']) if row['strengths'] else [],
                        'weaknesses': json.loads(row['weaknesses']) if row['weaknesses'] else [],
                        'recommendations': json.loads(row['recommendations']) if row['recommendations'] else [],
                        'keywords': json.loads(row['keywords']) if row['keywords'] else [],
                        'detailed_feedback': '',  # Campo no existe en la tabla actual
                        'created_at': row['created_at']
                    }
                    analyses.append(analysis_data)
                except json.JSONDecodeError as e:
                    logger.error(f"Error decodificando JSON en análisis {row['id']}: {e}")
                    continue
        
        return analyses
    
    def delete_analysis(self, analysis_id: int, user_id: int) -> bool:
        """Eliminar análisis (solo si pertenece al usuario)"""
        query = """
            DELETE FROM feedback 
            WHERE id = %s AND resume_id IN (
                SELECT id FROM resumes WHERE user_id = %s
            )
        """
        result = self.execute_query(query, (analysis_id, user_id))
        return result and result > 0
    
    def get_user_analysis_results(self, user_id: int) -> List[Dict[str, Any]]:
        """Obtener resultados de análisis de un usuario (alias para get_user_analyses)"""
        return self.get_user_analyses(user_id)
    
    def update_user_last_login(self, user_id: int):
        """Actualizar último login del usuario"""
        query = "UPDATE users SET last_login = NOW() WHERE id = %s"
        self.execute_query(query, (user_id,))
    
    def verify_user_email(self, user_id: int):
        """Verificar email del usuario"""
        query = "UPDATE users SET is_verified = TRUE WHERE id = %s"
        self.execute_query(query, (user_id,))

# Instancia global del servicio de base de datos
db_service = DatabaseService()

def get_db_service() -> DatabaseService:
    """Obtener instancia del servicio de base de datos"""
    return db_service