# migrate_sqlite_to_postgres.py

import sqlite3
import psycopg2
from psycopg2.extras import execute_values

DATABASE_URL = 'postgresql://neondb_owner:npg_CZA5aI0sDGkV@ep-wispy-butterfly-acchfxdv-pooler.sa-east-1.aws.neon.tech/neondb?channel_binding=require&sslmode=require'
# Ajuste para o caminho real do seu SQLite
SQLITE_DB_PATH = "./convidados.db"


def fetch_all(sqlite_conn, table, columns):
    cursor = sqlite_conn.cursor()
    cursor.execute(f"SELECT {', '.join(columns)} FROM {table}")
    rows = cursor.fetchall()
    cursor.close()
    return rows


def main():
    # Conexão com SQLite
    sqlite_conn = sqlite3.connect(SQLITE_DB_PATH)

    # Conexão com Postgres
    pg_conn = psycopg2.connect(DATABASE_URL)
    pg_cur = pg_conn.cursor()

    # Opcional: limpar as tabelas de destino antes de migrar (ordem reversa por causa das FKs)
    # Se NÃO quiser apagar, comente esse bloco.
    pg_cur.execute("TRUNCATE TABLE transfer_interesse RESTART IDENTITY CASCADE;")
    pg_cur.execute("TRUNCATE TABLE respostas RESTART IDENTITY CASCADE;")
    pg_cur.execute("TRUNCATE TABLE conexoes RESTART IDENTITY CASCADE;")
    pg_cur.execute("TRUNCATE TABLE convidados RESTART IDENTITY CASCADE;")
    pg_conn.commit()

    # 1) convidados
    convidados_cols = ["id", "nome", "telefone", "faixa_etaria", "relacao"]
    convidados_rows = fetch_all(sqlite_conn, "convidados", convidados_cols)

    if convidados_rows:
        execute_values(
            pg_cur,
            """
            INSERT INTO convidados (id, nome, telefone, faixa_etaria, relacao)
            VALUES %s
            ON CONFLICT (id) DO NOTHING
            """,
            convidados_rows,
        )
        print(f"Migrados {len(convidados_rows)} registros de 'convidados'.")

    # 2) conexoes
    conexoes_cols = ["id", "convidado_id_a", "convidado_id_b"]
    conexoes_rows = fetch_all(sqlite_conn, "conexoes", conexoes_cols)

    if conexoes_rows:
        execute_values(
            pg_cur,
            """
            INSERT INTO conexoes (id, convidado_id_a, convidado_id_b)
            VALUES %s
            ON CONFLICT (id) DO NOTHING
            """,
            conexoes_rows,
        )
        print(f"Migrados {len(conexoes_rows)} registros de 'conexoes'.")

    # 3) respostas
    respostas_cols = ["id", "timestamp", "convidado_a", "convidado_b", "confirmado"]
    respostas_rows = fetch_all(sqlite_conn, "respostas", respostas_cols)

    if respostas_rows:
        # SQLite pode ter 0/1; Postgres aceita bool ou 0/1, mas vamos garantir bool
        respostas_rows_bool = []
        for row in respostas_rows:
            # row é uma tupla (id, timestamp, convidado_a, convidado_b, confirmado)
            id_, ts, a, b, conf = row
            # conf pode ser 0/1 ou True/False
            conf_bool = bool(conf)
            respostas_rows_bool.append((id_, ts, a, b, conf_bool))

        execute_values(
            pg_cur,
            """
            INSERT INTO respostas (id, timestamp, convidado_a, convidado_b, confirmado)
            VALUES %s
            ON CONFLICT (id) DO NOTHING
            """,
            respostas_rows_bool,
        )
        print(f"Migrados {len(respostas_rows)} registros de 'respostas'.")

    # 4) transfer_interesse
    transfer_cols = ["id", "timestamp", "convidado_id", "responsavel_id", "interessado"]
    transfer_rows = fetch_all(sqlite_conn, "transfer_interesse", transfer_cols)

    if transfer_rows:
        transfer_rows_bool = []
        for row in transfer_rows:
            id_, ts, convidado_id, responsavel_id, interessado = row
            inter_bool = bool(interessado)
            transfer_rows_bool.append((id_, ts, convidado_id, responsavel_id, inter_bool))

        execute_values(
            pg_cur,
            """
            INSERT INTO transfer_interesse (id, timestamp, convidado_id, responsavel_id, interessado)
            VALUES %s
            ON CONFLICT (id) DO NOTHING
            """,
            transfer_rows_bool,
        )
        print(f"Migrados {len(transfer_rows)} registros de 'transfer_interesse'.")

    # Ajustar sequences (SERIAL) para não quebrar futuros INSERTs sem id
    # conexoes.id
    pg_cur.execute("""
        SELECT setval(
            pg_get_serial_sequence('conexoes', 'id'),
            COALESCE(MAX(id), 1),
            true
        ) FROM conexoes;
    """)

    # respostas.id
    pg_cur.execute("""
        SELECT setval(
            pg_get_serial_sequence('respostas', 'id'),
            COALESCE(MAX(id), 1),
            true
        ) FROM respostas;
    """)

    # transfer_interesse.id
    pg_cur.execute("""
        SELECT setval(
            pg_get_serial_sequence('transfer_interesse', 'id'),
            COALESCE(MAX(id), 1),
            true
        ) FROM transfer_interesse;
    """)

    pg_conn.commit()

    pg_cur.close()
    pg_conn.close()
    sqlite_conn.close()

    print("Migração concluída com sucesso.")


if __name__ == "__main__":
    main()