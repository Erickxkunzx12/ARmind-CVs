import requests
import psycopg2
from psycopg2.extras import RealDictCursor

def get_db_connection():
    """Obtener conexión a la base de datos PostgreSQL"""
    try:
        connection = psycopg2.connect(
            host='localhost',
            database='cv_analyzer',
            user='postgres',
            password='Solido123',
            port='5432',
            cursor_factory=RealDictCursor,
            client_encoding='UTF8'
        )
        return connection
    except Exception as e:
        print(f"Error de conexión: {e}")
        return None

def test_image_serving():
    """Probar si las imágenes se sirven correctamente"""
    connection = get_db_connection()
    if not connection:
        return
    
    try:
        cursor = connection.cursor()
        
        # Obtener IDs de imágenes
        cursor.execute("SELECT id, filename FROM uploaded_images LIMIT 3")
        images = cursor.fetchall()
        
        cursor.close()
        connection.close()
        
        if not images:
            print("❌ No hay imágenes para probar")
            return
        
        print("🔍 Probando acceso a imágenes:")
        
        for img in images:
            image_id = img['id']
            filename = img['filename']
            url = f"http://127.0.0.1:5000/image/{image_id}"
            
            try:
                response = requests.get(url, timeout=5)
                
                if response.status_code == 200:
                    content_type = response.headers.get('content-type', 'unknown')
                    content_length = len(response.content)
                    print(f"  ✅ ID {image_id} ({filename}): {response.status_code} - {content_type} - {content_length} bytes")
                else:
                    print(f"  ❌ ID {image_id} ({filename}): {response.status_code} - {response.text[:100]}")
                    
            except requests.exceptions.RequestException as e:
                print(f"  ❌ ID {image_id} ({filename}): Error de conexión - {e}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

def create_test_post_with_uploaded_image():
    """Crear un post de prueba con una imagen subida"""
    connection = get_db_connection()
    if not connection:
        return
    
    try:
        cursor = connection.cursor()
        
        # Obtener la primera imagen disponible
        cursor.execute("SELECT id FROM uploaded_images LIMIT 1")
        result = cursor.fetchone()
        
        if not result:
            print("❌ No hay imágenes subidas para usar")
            return
        
        image_id = result['id']
        image_url = f"/image/{image_id}"
        
        # Crear post de prueba
        cursor.execute("""
            INSERT INTO blog_posts (title, content, image_url, author_id, is_published)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """, (
            "Post de Prueba con Imagen Subida",
            "Este es un post de prueba para verificar que las imágenes subidas se muestran correctamente.",
            image_url,
            1,  # Asumiendo que existe un usuario con ID 1
            True
        ))
        
        post_result = cursor.fetchone()
        if post_result:
            post_id = post_result['id']
            print(f"✅ Post de prueba creado con ID: {post_id}")
            print(f"   URL de imagen: {image_url}")
            print(f"   Ver en: http://127.0.0.1:5000/blog/tips")
        
        connection.commit()
        cursor.close()
        connection.close()
        
    except Exception as e:
        print(f"❌ Error creando post de prueba: {e}")
        if connection:
            connection.rollback()

if __name__ == "__main__":
    print("🧪 Probando sistema de imágenes...\n")
    
    print("1. Probando acceso directo a imágenes:")
    test_image_serving()
    
    print("\n2. Creando post de prueba con imagen subida:")
    create_test_post_with_uploaded_image()
    
    print("\n✅ Pruebas completadas")