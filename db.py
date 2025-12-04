import pymysql

def get_connection():
    connection = pymysql.connect(
        host="localhost",
        user="root",
        password="",
        database="maas_takip", # Veritabanı adın neyse onu yaz
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor
    )
    return connection