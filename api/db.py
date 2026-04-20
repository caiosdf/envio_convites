import os
import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = 'postgresql://neondb_owner:npg_CZA5aI0sDGkV@ep-wispy-butterfly-acchfxdv-pooler.sa-east-1.aws.neon.tech/neondb?channel_binding=require&sslmode=require'

def get_conn():
    # Conexão simples; depois você pode evoluir para pool se quiser
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    return conn