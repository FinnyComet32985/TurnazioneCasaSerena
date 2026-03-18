import sqlite3

def init_db():
    
    connection = sqlite3.connect('./db/turnazione.db')

    #recupero e lettura delle script sql
    schema = sql_read("./db/schema.sql")
    
    # esecuzione script sql per la creazione dello schema
    connection.executescript(schema)
    
    connection.commit()
    connection.close()


def sql_read(sql_file_path):
    with open(sql_file_path, 'r') as file:
            sql_script = file.read()
    return sql_script
