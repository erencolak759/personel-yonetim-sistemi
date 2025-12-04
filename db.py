import pymysql

def get_connection():
    connection = pymysql.connect(
        host="shuttle.proxy.rlwy.net",
        user="root",
        password="WEwqlRAGrnTNiVoIiNZPzbhZeAGBSxIm",
        database="railway",
        port=30001,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor
    )
    return connection
