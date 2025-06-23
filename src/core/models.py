# Modelos de datos para la aplicación ARMind
from dataclasses import dataclass
from typing import List, Dict, Optional, Any
from datetime import datetime

@dataclass
class CVAnalysisResult:
    """Resultado del análisis de CV"""
    score: int
    strengths: List[str]
    weaknesses: List[str]
    recommendations: List[str]
    keywords: List[str]
    analysis_type: str
    ai_provider: str
    detailed_feedback: str
    error: bool = False
    timestamp: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario"""
        return {
            'score': self.score,
            'strengths': self.strengths,
            'weaknesses': self.weaknesses,
            'recommendations': self.recommendations,
            'keywords': self.keywords,
            'analysis_type': self.analysis_type,
            'ai_provider': self.ai_provider,
            'detailed_feedback': self.detailed_feedback,
            'error': self.error,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CVAnalysisResult':
        """Crear desde diccionario"""
        timestamp = None
        if data.get('timestamp'):
            timestamp = datetime.fromisoformat(data['timestamp'])
        
        return cls(
            score=data.get('score', 0),
            strengths=data.get('strengths', []),
            weaknesses=data.get('weaknesses', []),
            recommendations=data.get('recommendations', []),
            keywords=data.get('keywords', []),
            analysis_type=data.get('analysis_type', 'general_health_check'),
            ai_provider=data.get('ai_provider', 'unknown'),
            detailed_feedback=data.get('detailed_feedback', ''),
            error=data.get('error', False),
            timestamp=timestamp
        )

@dataclass
class UserProfile:
    """Perfil de usuario"""
    id: int
    email: str
    name: str
    is_admin: bool = False
    is_verified: bool = False
    is_active: bool = True
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario"""
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'is_admin': self.is_admin,
            'is_verified': self.is_verified,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }

@dataclass
class CVDocument:
    """Documento de CV"""
    id: Optional[int]
    user_id: int
    filename: str
    content: str
    file_type: str
    upload_date: Optional[datetime] = None
    file_size: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'filename': self.filename,
            'content': self.content,
            'file_type': self.file_type,
            'upload_date': self.upload_date.isoformat() if self.upload_date else None,
            'file_size': self.file_size
        }

@dataclass
class JobSearchResult:
    """Resultado de búsqueda de empleo"""
    title: str
    company: str
    location: str
    description: str
    url: str
    source: str
    posted_date: Optional[str] = None
    salary: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario"""
        return {
            'title': self.title,
            'company': self.company,
            'location': self.location,
            'description': self.description,
            'url': self.url,
            'source': self.source,
            'posted_date': self.posted_date,
            'salary': self.salary
        }

class AnalysisTypes:
    """Tipos de análisis disponibles"""
    GENERAL_HEALTH_CHECK = 'general_health_check'
    ATS_OPTIMIZATION = 'ats_optimization'
    CONTENT_ENHANCEMENT = 'content_enhancement'
    VISUAL_DESIGN = 'visual_design_assessment'
    COMPREHENSIVE_SCORE = 'comprehensive_score'
    
    @classmethod
    def get_all_types(cls) -> List[str]:
        """Obtener todos los tipos de análisis"""
        return [
            cls.GENERAL_HEALTH_CHECK,
            cls.ATS_OPTIMIZATION,
            cls.CONTENT_ENHANCEMENT,
            cls.VISUAL_DESIGN,
            cls.COMPREHENSIVE_SCORE
        ]
    
    @classmethod
    def get_display_names(cls) -> Dict[str, str]:
        """Obtener nombres para mostrar"""
        return {
            cls.GENERAL_HEALTH_CHECK: 'Evaluación General',
            cls.ATS_OPTIMIZATION: 'Optimización ATS',
            cls.CONTENT_ENHANCEMENT: 'Mejora de Contenido',
            cls.VISUAL_DESIGN: 'Diseño Visual',
            cls.COMPREHENSIVE_SCORE: 'Puntuación Completa'
        }
    
    @classmethod
    def get_all(cls) -> List[Dict[str, str]]:
        """Obtener todos los tipos de análisis con sus nombres para mostrar"""
        display_names = cls.get_display_names()
        return [
            {'value': analysis_type, 'name': display_names[analysis_type]}
            for analysis_type in cls.get_all_types()
        ]

class AIProviders:
    """Proveedores de IA disponibles"""
    OPENAI = 'openai'
    ANTHROPIC = 'anthropic'
    GEMINI = 'gemini'
    
    @classmethod
    def get_all_providers(cls) -> List[str]:
        """Obtener todos los proveedores"""
        return [cls.OPENAI, cls.ANTHROPIC, cls.GEMINI]
    
    @classmethod
    def get_display_names(cls) -> Dict[str, str]:
        """Obtener nombres para mostrar"""
        return {
            cls.OPENAI: 'OpenAI GPT',
            cls.ANTHROPIC: 'Anthropic Claude',
            cls.GEMINI: 'Google Gemini'
        }
    
    @classmethod
    def get_all(cls) -> List[Dict[str, str]]:
        """Obtener todos los proveedores de IA con sus nombres para mostrar"""
        display_names = cls.get_display_names()
        return [
            {'value': provider, 'name': display_names[provider]}
            for provider in cls.get_all_providers()
        ]