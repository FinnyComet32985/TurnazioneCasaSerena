import sqlite3


def load_db():
    connection = sqlite3.connect('./db/turnazione.db')
    cursor = connection.cursor()

    query = "select * from dipendente"

    cursor.execute(query)
    dipendenti = cursor.fetchall()

    for dipendente in dipendenti:
        print(dipendente)

    connection.close()

