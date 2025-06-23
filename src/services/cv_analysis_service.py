# Servicio de análisis de CV
from typing import Dict, Any, Optional
from core.ai_services import (
    analyze_cv_with_openai,
    analyze_cv_with_anthropic, 
    analyze_cv_with_gemini
)
from core.models import CVAnalysisResult, AnalysisTypes, AIProviders
from core.database import get_db_service
from utils.validation import validate_analysis_result, validate_cv_content
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class CVAnalysisService:
    """Servicio centralizado para análisis de CV"""
    
    def __init__(self):
        self.db_service = get_db_service()
        self.ai_providers = {
            AIProviders.OPENAI: analyze_cv_with_openai,
            AIProviders.ANTHROPIC: analyze_cv_with_anthropic,
            AIProviders.GEMINI: analyze_cv_with_gemini
        }
    
    def analyze_cv(self, cv_text: str, analysis_type: str, ai_provider: str) -> CVAnalysisResult:
        """Realizar análisis de CV"""
        # Validar entrada
        cv_validation = validate_cv_content(cv_text)
        if not cv_validation['is_valid']:
            return CVAnalysisResult(
                score=0,
                strengths=[],
                weaknesses=cv_validation['errors'],
                recommendations=["Corrija los errores en el CV antes de continuar"],
                keywords=[],
                analysis_type=analysis_type,
                ai_provider=ai_provider,
                detailed_feedback=f"Errores de validación: {', '.join(cv_validation['errors'])}",
                error=True,
                timestamp=datetime.now()
            )
        
        # Verificar proveedor de IA
        if ai_provider not in self.ai_providers:
            return self._create_error_result(
                analysis_type, ai_provider, 
                f"Proveedor de IA no válido: {ai_provider}"
            )
        
        # Verificar tipo de análisis
        if analysis_type not in AnalysisTypes.get_all_types():
            return self._create_error_result(
                analysis_type, ai_provider,
                f"Tipo de análisis no válido: {analysis_type}"
            )
        
        try:
            # Realizar análisis
            logger.info(f"Iniciando análisis {analysis_type} con {ai_provider}")
            analysis_function = self.ai_providers[ai_provider]
            raw_result = analysis_function(cv_text, analysis_type)
            
            # Validar resultado
            validation = validate_analysis_result(raw_result)
            if not validation['is_valid']:
                logger.error(f"Resultado de análisis inválido: {validation['errors']}")
                return self._create_error_result(
                    analysis_type, ai_provider,
                    f"Resultado inválido: {', '.join(validation['errors'])}"
                )
            
            # Crear objeto de resultado
            result = CVAnalysisResult(
                score=raw_result.get('score', 0),
                strengths=raw_result.get('strengths', []),
                weaknesses=raw_result.get('weaknesses', []),
                recommendations=raw_result.get('recommendations', []),
                keywords=raw_result.get('keywords', []),
                analysis_type=analysis_type,
                ai_provider=ai_provider,
                detailed_feedback=raw_result.get('detailed_feedback', ''),
                error=raw_result.get('error', False),
                timestamp=datetime.now()
            )
            
            logger.info(f"Análisis completado exitosamente. Score: {result.score}")
            return result
            
        except Exception as e:
            logger.error(f"Error durante análisis: {e}")
            return self._create_error_result(
                analysis_type, ai_provider, str(e)
            )
    
    def save_analysis(self, user_id: int, cv_id: int, analysis_result: CVAnalysisResult) -> Optional[int]:
        """Guardar resultado de análisis"""
        try:
            analysis_id = self.db_service.save_analysis_result(user_id, cv_id, analysis_result)
            if analysis_id:
                logger.info(f"Análisis guardado con ID: {analysis_id}")
            return analysis_id
        except Exception as e:
            logger.error(f"Error guardando análisis: {e}")
            return None
    
    def get_user_analyses(self, user_id: int) -> list:
        """Obtener análisis de un usuario"""
        try:
            return self.db_service.get_user_analyses(user_id)
        except Exception as e:
            logger.error(f"Error obteniendo análisis del usuario {user_id}: {e}")
            return []
    
    def get_user_analysis_history(self, user_id: int, limit: int = 10) -> list:
        """Obtener historial de análisis de un usuario con límite"""
        try:
            analyses = self.db_service.get_user_analyses(user_id)
            # Ordenar por fecha más reciente y limitar
            sorted_analyses = sorted(analyses, key=lambda x: x.get('created_at', ''), reverse=True)
            return sorted_analyses[:limit]
        except Exception as e:
            logger.error(f"Error obteniendo historial de análisis del usuario {user_id}: {e}")
            return []
    
    def delete_analysis(self, analysis_id: int, user_id: int) -> bool:
        """Eliminar análisis"""
        try:
            return self.db_service.delete_analysis(analysis_id, user_id)
        except Exception as e:
            logger.error(f"Error eliminando análisis {analysis_id}: {e}")
            return False
    
    def get_analysis_summary(self, user_id: int) -> Dict[str, Any]:
        """Obtener resumen de análisis del usuario"""
        try:
            analyses = self.get_user_analyses(user_id)
            
            summary = {
                'total_analyses': len(analyses),
                'by_provider': {},
                'by_type': {},
                'average_score': 0,
                'latest_analysis': None
            }
            
            if not analyses:
                return summary
            
            # Contar por proveedor y tipo
            total_score = 0
            for analysis in analyses:
                provider = analysis.get('ai_provider', 'unknown')
                analysis_type = analysis.get('analysis_type', 'unknown')
                score = analysis.get('score', 0)
                
                summary['by_provider'][provider] = summary['by_provider'].get(provider, 0) + 1
                summary['by_type'][analysis_type] = summary['by_type'].get(analysis_type, 0) + 1
                total_score += score
            
            # Calcular promedio
            summary['average_score'] = round(total_score / len(analyses), 1)
            
            # Último análisis
            summary['latest_analysis'] = analyses[0] if analyses else None
            
            return summary
            
        except Exception as e:
            logger.error(f"Error obteniendo resumen de análisis: {e}")
            return {
                'total_analyses': 0,
                'by_provider': {},
                'by_type': {},
                'average_score': 0,
                'latest_analysis': None
            }
    
    def _create_error_result(self, analysis_type: str, ai_provider: str, error_message: str) -> CVAnalysisResult:
        """Crear resultado de error"""
        return CVAnalysisResult(
            score=0,
            strengths=[],
            weaknesses=["Error en el análisis"],
            recommendations=["Intente nuevamente o use otro proveedor de IA"],
            keywords=[],
            analysis_type=analysis_type,
            ai_provider=ai_provider,
            detailed_feedback=f"Error: {error_message}",
            error=True,
            timestamp=datetime.now()
        )
    
    def get_available_providers(self) -> Dict[str, str]:
        """Obtener proveedores disponibles"""
        return AIProviders.get_display_names()
    
    def get_available_analysis_types(self) -> Dict[str, str]:
        """Obtener tipos de análisis disponibles"""
        return AnalysisTypes.get_display_names()

# Instancia global del servicio
cv_analysis_service = CVAnalysisService()

def get_cv_analysis_service() -> CVAnalysisService:
    """Obtener instancia del servicio de análisis"""
    return cv_analysis_service