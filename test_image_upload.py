import psycopg2
from psycopg2.extras import RealDictCursor
import os

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

def check_table_structure():
    """Verificar estructura de la tabla uploaded_images"""
    connection = get_db_connection()
    if not connection:
        print("❌ No se pudo conectar a la base de datos")
        return
    
    try:
        cursor = connection.cursor()
        
        # Verificar columnas de la tabla
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'uploaded_images' 
            ORDER BY ordinal_position
        """)
        
        columns = cursor.fetchall()
        
        if not columns:
            print("❌ La tabla 'uploaded_images' no existe")
        else:
            print("✅ Estructura de la tabla 'uploaded_images':")
            for col in columns:
                print(f"  - {col['column_name']}: {col['data_type']}")
        
        # Verificar contenido de la tabla
        cursor.execute("SELECT COUNT(*) as total FROM uploaded_images")
        count = cursor.fetchone()['total']
        print(f"\n📊 Total de imágenes en la tabla: {count}")
        
        if count > 0:
            cursor.execute("SELECT id, filename, content_type FROM uploaded_images LIMIT 5")
            images = cursor.fetchall()
            print("\n📸 Últimas imágenes:")
            for img in images:
                print(f"  - ID: {img['id']}, Archivo: {img['filename']}, Tipo: {img['content_type']}")
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

def check_blog_posts():
    """Verificar posts del blog con imágenes"""
    connection = get_db_connection()
    if not connection:
        return
    
    try:
        cursor = connection.cursor()
        
        cursor.execute("""
            SELECT id, title, image_url, is_published
            FROM blog_posts
            WHERE image_url IS NOT NULL AND image_url != ''
            ORDER BY id DESC
            LIMIT 5
        """)
        
        posts = cursor.fetchall()
        
        print(f"\n📝 Posts con imágenes ({len(posts)}):")
        for post in posts:
            print(f"  - ID: {post['id']}, Título: {post['title']}")
            print(f"    URL: {post['image_url']}")
            if post['image_url'].startswith('/image/'):
                print(f"    ✅ Imagen subida al servidor")
            else:
                print(f"    🌐 Imagen externa")
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        print(f"❌ Error verificando posts: {e}")

if __name__ == "__main__":
    print("🔍 Verificando sistema de imágenes...\n")
    
    print("1. Verificando estructura de tabla:")
    check_table_structure()
    
    print("\n2. Verificando posts del blog:")
    check_blog_posts()
    
    print("\n✅ Verificación completada")