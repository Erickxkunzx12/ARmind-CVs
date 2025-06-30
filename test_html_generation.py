#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Test script para verificar la generación de HTML

def test_html_generation():
    # Simular datos como en download_cover_letter
    job_title = "Armador de pedidos"
    company_name = "Transecom Global"
    content = "Estimado/a responsable de contratación,\n\nMe dirijo a usted con gran interés para postular al puesto de Armador de pedidos en Transecom Global. Con experiencia en logística y almacenamiento, estoy convencido/a de que puedo contribuir significativamente al éxito de su equipo.\n\nMi experiencia incluye:\n- Gestión eficiente de inventarios\n- Preparación y verificación de pedidos\n- Manejo de sistemas de gestión de almacenes\n- Trabajo en equipo y bajo presión\n\nEstoy entusiasmado/a por la oportunidad de formar parte de Transecom Global y contribuir con mis habilidades al crecimiento de la empresa.\n\nQuedo a su disposición para una entrevista personal.\n\nAtentamente"
    language = "es"
    
    # Configuración de idioma
    lang_config = {
        'title': 'Carta de Presentación',
        'closing': 'Atentamente'
    }
    
    # Formatear contenido
    paragraphs = content.split('\n\n')
    formatted_content = '\n'.join([f'<p>{p.strip()}</p>' for p in paragraphs if p.strip()])
    
    print(f"DEBUG: job_title = {job_title}")
    print(f"DEBUG: company_name = {company_name}")
    print(f"DEBUG: formatted_content = {formatted_content[:200]}...")
    
    # Simular session
    class MockSession:
        def get(self, key, default):
            return "Usuario Test"
    
    session = MockSession()
    
    # Generar HTML como en la función original
    html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; margin: 40px; color: #333; }}
                .header {{ text-align: center; margin-bottom: 30px; border-bottom: 2px solid #333; padding-bottom: 20px; }}
                .content {{ text-align: justify; margin-bottom: 30px; }}
                .content p {{ margin-bottom: 15px; }}
                .signature {{ margin-top: 30px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{lang_config['title']}</h1>
                <p><strong>{job_title}</strong> - {company_name}</p>
            </div>
            <div class="content">
                {formatted_content}
            </div>
            <div class="signature">
                <p>{lang_config['closing']},<br>
                {session.get('username', 'Candidato')}</p>
            </div>
        </body>
        </html>
        """
    
    print("\n=== HTML GENERADO ===")
    print(html_content)
    print("\n=== FIN HTML ===")
    
    # Verificar si las variables se están interpolando correctamente
    if '{job_title}' in html_content:
        print("ERROR: Las variables no se están interpolando!")
    else:
        print("OK: Las variables se están interpolando correctamente")

if __name__ == "__main__":
    test_html_generation()