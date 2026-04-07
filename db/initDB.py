import sqlite3
import os
from path_util import resource_path

def init_db():
    # Creiamo la cartella 'db' nel percorso di esecuzione se non esiste, 
    # altrimenti sqlite3.connect fallirà non trovando la directory.
    if not os.path.exists('./db'):
        os.makedirs('./db')
    
    connection = sqlite3.connect('./db/turnazione.db')

    # Usiamo resource_path per trovare lo script SQL dentro il bundle dell'eseguibile
    schema = sql_read(resource_path("db/schema.sql"))
    
    # esecuzione script sql per la creazione dello schema
    connection.executescript(schema)
    
    connection.commit()
    connection.close()


def sql_read(sql_file_path):
    with open(sql_file_path, 'r', encoding='utf-8') as file:
            sql_script = file.read()
    return sql_script
