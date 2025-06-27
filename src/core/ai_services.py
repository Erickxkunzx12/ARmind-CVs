# Servicios de IA para análisis de CV
import os
import json
from openai import OpenAI

# Configurar cliente OpenAI
OPENAI_CLIENT = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def get_analysis_prompt(analysis_type, cv_text):
    """Obtener prompt específico según el tipo de análisis"""
    analysis_prompts = {
        'general_health_check': f"""
        Analiza este currículum y proporciona una evaluación general de su calidad y efectividad.
        
        Evalúa:
        1. **Estructura y formato**: Organización, claridad, legibilidad
        2. **Contenido**: Relevancia, completitud, impacto de logros
        3. **Compatibilidad ATS**: Palabras clave, formato, secciones estándar
        4. **Presentación profesional**: Consistencia, errores, primera impresión
        5. **Optimización para reclutadores**: Escaneabilidad, información clave visible
        
        IMPORTANTE: Responde ÚNICAMENTE en formato JSON válido con esta estructura exacta:
        {{
            "score": número_entre_0_y_100,
            "strengths": ["fortaleza1", "fortaleza2", "fortaleza3"],
            "weaknesses": ["debilidad1", "debilidad2", "debilidad3"],
            "recommendations": ["recomendación1", "recomendación2", "recomendación3"],
            "keywords": ["palabra_clave1", "palabra_clave2", "palabra_clave3"],
            "analysis_type": "general_health_check",
            "detailed_feedback": "retroalimentación detallada aquí"
        }}
        
        CV: {cv_text}
        """,
        
        'ats_optimization': f"""
        Analiza este currículum específicamente para optimización ATS (Applicant Tracking System).
        
        Evalúa:
        1. **Palabras clave**: Presencia de términos relevantes del sector
        2. **Formato ATS-friendly**: Estructura, fuentes, elementos gráficos
        3. **Secciones estándar**: Títulos reconocibles por ATS
        4. **Parsing compatibility**: Facilidad de extracción de datos
        5. **Ranking factors**: Elementos que mejoran el ranking ATS
        
        IMPORTANTE: Responde ÚNICAMENTE en formato JSON válido con esta estructura exacta:
        {{
            "score": número_entre_0_y_100,
            "strengths": ["fortaleza1 ATS específica", "fortaleza2", "fortaleza3"],
            "weaknesses": ["debilidad1 ATS específica", "debilidad2", "debilidad3"],
            "recommendations": ["recomendación1 para ATS", "recomendación2", "recomendación3"],
            "keywords": ["keyword1_faltante", "keyword2_importante", "keyword3"],
            "analysis_type": "ats_optimization",
            "detailed_feedback": "análisis detallado de compatibilidad ATS"
        }}
        
        CV: {cv_text}
        """,
        
        'content_enhancement': f"""
        Analiza el contenido de este currículum para mejoras de impacto y relevancia.
        
        Evalúa:
        1. **Logros cuantificables**: Métricas, números, resultados específicos
        2. **Verbos de acción**: Uso de verbos impactantes y específicos
        3. **Relevancia sectorial**: Alineación con expectativas del sector
        4. **Progresión profesional**: Coherencia y crecimiento en la carrera
        5. **Diferenciación**: Elementos únicos que destacan al candidato
        
        IMPORTANTE: Responde ÚNICAMENTE en formato JSON válido con esta estructura exacta:
        {{
            "score": número_entre_0_y_100,
            "strengths": ["fortaleza1 de contenido", "fortaleza2", "fortaleza3"],
            "weaknesses": ["debilidad1 de contenido", "debilidad2", "debilidad3"],
            "recommendations": ["recomendación1 de mejora", "recomendación2", "recomendación3"],
            "keywords": ["skill1_destacar", "achievement2_añadir", "keyword3"],
            "analysis_type": "content_enhancement",
            "detailed_feedback": "análisis detallado de contenido y sugerencias de mejora"
        }}
        
        CV: {cv_text}
        """
    }
    
    return analysis_prompts.get(analysis_type, analysis_prompts['general_health_check'])

def analyze_cv_with_openai(cv_text, analysis_type):
    """Analizar CV usando OpenAI"""
    prompt = get_analysis_prompt(analysis_type, cv_text)
    
    system_prompt = """Eres un experto en recursos humanos, reclutamiento y sistemas ATS (Applicant Tracking System). 
    Tu objetivo es ayudar a los candidatos a optimizar sus currículums para maximizar sus posibilidades de pasar los filtros ATS y llegar a la entrevista.
    
    Responde SIEMPRE en formato JSON con la siguiente estructura:
    {
        "score": número (0-100),
        "strengths": ["fortaleza1", "fortaleza2", ...],
        "weaknesses": ["debilidad1", "debilidad2", ...],
        "recommendations": ["recomendación1", "recomendación2", ...],
        "keywords": ["palabra_clave1", "palabra_clave2", ...],
        "analysis_type": "tipo_de_análisis",
        "detailed_feedback": "retroalimentación detallada específica del tipo de análisis"
    }"""
    
    try:
        # Usar el nuevo cliente OpenAI
        if not OPENAI_CLIENT:
            raise ValueError("OpenAI client not configured")
        
        response = OPENAI_CLIENT.chat.completions.create(
            model="gpt-3.5-turbo",  # Usar gpt-3.5-turbo que es más estable
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2000,
            temperature=0.7
        )
        
        analysis_text = response.choices[0].message.content
        analysis = json.loads(analysis_text)
        
        # Asegurar campos requeridos
        analysis.setdefault("keywords", [])
        analysis.setdefault("analysis_type", analysis_type)
        analysis.setdefault("ai_provider", "openai")
            
        return analysis
    
    except Exception as e:
        print(f"Error al analizar con OpenAI: {e}")
        return get_error_analysis(analysis_type, "openai", str(e))

def analyze_cv_with_anthropic(cv_text, analysis_type):
    """Analizar CV usando Anthropic Claude"""
    try:
        import anthropic
        
        # Verificar API key
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key or api_key == 'your_anthropic_api_key_here':
            return get_error_analysis(analysis_type, "anthropic", "API Key de Anthropic no configurada")
        
        # Configurar cliente de Anthropic
        client = anthropic.Anthropic(api_key=api_key)
        
        prompt = get_analysis_prompt(analysis_type, cv_text)
        
        system_prompt = """Eres un experto en recursos humanos, reclutamiento y sistemas ATS. 
        Responde SIEMPRE en formato JSON válido con la estructura especificada."""
        
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2000,
            temperature=0.7,
            system=system_prompt,
            messages=[
                {"role": "user", "content": prompt + "\n\nResponde en formato JSON con: score, strengths, weaknesses, recommendations, keywords, analysis_type, detailed_feedback"}
            ]
        )
        
        analysis_text = response.content[0].text
        
        # Limpiar respuesta si contiene markdown
        if "```json" in analysis_text:
            analysis_text = analysis_text.split("```json")[1].split("```")[0]
        elif "```" in analysis_text:
            analysis_text = analysis_text.split("```")[1]
        
        analysis = json.loads(analysis_text.strip())
        
        # Asegurar campos requeridos
        analysis.setdefault("keywords", [])
        analysis.setdefault("analysis_type", analysis_type)
        analysis.setdefault("ai_provider", "anthropic")
        
        return analysis
        
    except ImportError:
        return get_error_analysis(analysis_type, "anthropic", "Librería de Anthropic no instalada")
    except json.JSONDecodeError as e:
        print(f"Error de JSON en Anthropic: {e}")
        print(f"Respuesta recibida: {analysis_text if 'analysis_text' in locals() else 'No disponible'}")
        return get_error_analysis(analysis_type, "anthropic", f"Error de formato JSON: {str(e)}")
    except Exception as e:
        print(f"Error al analizar con Anthropic: {e}")
        return get_error_analysis(analysis_type, "anthropic", str(e))

def analyze_cv_with_gemini(cv_text, analysis_type):
    """Analizar CV usando Google Gemini"""
    try:
        # Intentar importar con diferentes métodos
        try:
            import google.generativeai as genai
        except ImportError:
            try:
                from google import generativeai as genai
            except ImportError:
                return get_error_analysis(analysis_type, "gemini", "Librería de Google Generative AI no disponible")
        
        # Verificar API key
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key or api_key == 'your_gemini_api_key_here':
            return get_error_analysis(analysis_type, "gemini", "API Key de Gemini no configurada")
        
        # Configurar Gemini
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = get_analysis_prompt(analysis_type, cv_text)
        
        system_instruction = """Eres un experto en recursos humanos y sistemas ATS. 
        Responde SIEMPRE en formato JSON válido con la estructura especificada."""
        
        full_prompt = f"{system_instruction}\n\n{prompt}\n\nResponde en formato JSON con: score, strengths, weaknesses, recommendations, keywords, analysis_type, detailed_feedback"
        
        response = model.generate_content(full_prompt)
        analysis_text = response.text
        
        # Limpiar respuesta si contiene markdown
        if "```json" in analysis_text:
            analysis_text = analysis_text.split("```json")[1].split("```")[0]
        elif "```" in analysis_text:
            analysis_text = analysis_text.split("```")[1]
        
        analysis = json.loads(analysis_text.strip())
        
        # Asegurar campos requeridos
        analysis.setdefault("keywords", [])
        analysis.setdefault("analysis_type", analysis_type)
        analysis.setdefault("ai_provider", "gemini")
        
        return analysis
        
    except ImportError:
        return get_error_analysis(analysis_type, "gemini", "Librería de Google Generative AI no instalada")
    except json.JSONDecodeError as e:
        print(f"Error de JSON en Gemini: {e}")
        print(f"Respuesta recibida: {analysis_text if 'analysis_text' in locals() else 'No disponible'}")
        return get_error_analysis(analysis_type, "gemini", f"Error de formato JSON: {str(e)}")
    except Exception as e:
        print(f"Error al analizar con Gemini: {e}")
        return get_error_analysis(analysis_type, "gemini", str(e))

def get_error_analysis(analysis_type, ai_provider, error_message):
    """Retornar análisis de error estándar"""
    return {
        "score": 0,
        "strengths": [f"Error al procesar con {ai_provider}"],
        "weaknesses": ["No se pudo completar el análisis"],
        "recommendations": ["Intente nuevamente más tarde o use otro proveedor de IA"],
        "keywords": [],
        "analysis_type": analysis_type,
        "ai_provider": ai_provider,
        "detailed_feedback": f"Error: {error_message}",
        "error": True
    }

def analyze_cv_with_ai(cv_text):
    """Función legacy para compatibilidad - usar OpenAI por defecto"""
    return analyze_cv_with_openai(cv_text, 'general_health_check')