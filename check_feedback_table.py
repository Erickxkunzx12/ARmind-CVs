import psycopg2
import os

try:
    # Conectar a la base de datos
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=os.getenv('DB_PORT', '5432'),
        database=os.getenv('DB_NAME', 'armind_db'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', '')
    )
    
    cur = conn.cursor()
    
    # Verificar estructura de la tabla feedback
    cur.execute("""
        SELECT column_name, data_type, is_nullable 
        FROM information_schema.columns 
        WHERE table_name = 'feedback' 
        ORDER BY ordinal_position;
    """)
    
    print('Columnas de la tabla feedback:')
    columns = cur.fetchall()
    for row in columns:
        print(f'{row[0]}: {row[1]} (nullable: {row[2]})')
    
    # Verificar si hay datos en la tabla
    cur.execute("SELECT COUNT(*) FROM feedback;")
    count = cur.fetchone()[0]
    print(f'\nTotal de registros en feedback: {count}')
    
    if count > 0:
        # Mostrar una muestra de datos
        cur.execute("SELECT * FROM feedback LIMIT 1;")
        sample = cur.fetchone()
        if sample:
            print('\nMuestra de datos:')
            for i, col in enumerate(columns):
                print(f'{col[0]}: {sample[i]}')
    
    conn.close()
    print('\nVerificación completada.')
    
except Exception as e:
    print(f'Error: {e}')