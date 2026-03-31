import psycopg2
from psycopg2 import pool
import os
from dotenv import load_dotenv

# Carica le variabili dal file .env
load_dotenv()

DB_URL = os.getenv("DATABASE_URL")

class DBManager:
    _pool = None

    @classmethod
    def initialize(cls):
        if cls._pool is None and DB_URL:
            # Min 1 connessione, Max 10 connessioni contemporanee
            cls._pool = psycopg2.pool.SimpleConnectionPool(1, 10, DB_URL)

    @classmethod
    def get_conn(cls):
        if cls._pool is None:
            cls.initialize()
        return cls._pool.getconn()

    @classmethod
    def put_conn(cls, conn):
        cls._pool.putconn(conn)

    @classmethod
    def close_all(cls):
        if cls._pool:
            cls._pool.closeall()