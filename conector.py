import pymysql

def get_connection():
    return pymysql.connect(
        host='localhost',
        port=3306,
        user='root',
        password='1234',
        database='userauthdb',
        cursorclass=pymysql.cursors.DictCursor
    )

def executar_query(query, params=None):
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            resultado = cursor.fetchall()
            return resultado
    except pymysql.Error as e:
        print(f"Erro ao conectar ao MySQL ou ao executar a query: {e}")
        return None
    finally:
        if conn:
            conn.close()

def inserir_dados(query, params=None):
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            conn.commit()
            return True
    except pymysql.Error as e:
        print(f"Erro ao conectar ao MySQL ou ao executar a query de inserção: {e}")
        return False
    finally:
        if conn:
            conn.close()

def atualizar_dados(query, params=None):
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            conn.commit()
            return True
    except pymysql.Error as e:
        print(f"Erro ao conectar ao MySQL ou ao executar a query de atualização: {e}")
        return False
    finally:
        if conn:
            conn.close()
