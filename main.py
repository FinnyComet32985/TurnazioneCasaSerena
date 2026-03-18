from db.init_db import init_db
from sistemaSalvataggio import load_db
import sqlite3
import os


def main():
    db_exist = os.path.isfile('./db/turnazione.db')

    if db_exist:
        load_db()
    else:
        init_db()



if __name__ == '__main__':
    main()