from db.database import DBManager
from path_util import resource_path

def init_db():
    DBManager.initialize()
    connection = DBManager.get_conn()
    cursor = connection.cursor()
    
    #recupero e lettura delle script sql
    schema = sql_read(resource_path("db/schema.sql"))
    
    # esecuzione script sql per la creazione dello schema
    cursor.execute(schema)
    
    connection.commit()
    cursor.close()
    DBManager.put_conn(connection)


def sql_read(sql_file_path):
    with open(sql_file_path, 'r') as file:
            sql_script = file.read()
    return sql_script
