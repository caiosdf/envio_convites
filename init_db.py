import os
import psycopg2

DATABASE_URL = 'postgresql://neondb_owner:npg_CZA5aI0sDGkV@ep-wispy-butterfly-acchfxdv-pooler.sa-east-1.aws.neon.tech/neondb?channel_binding=require&sslmode=require'
def create_db():
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    # # 🧱 Tabela convidados
    # cursor.execute("""
    # CREATE TABLE IF NOT EXISTS convidados (
    #     id INTEGER PRIMARY KEY,
    #     nome TEXT NOT NULL,
    #     telefone TEXT,
    #     faixa_etaria TEXT NOT NULL
    #         CHECK (faixa_etaria IN ('adulto', 'crianca')),
    #     relacao TEXT NOT NULL
    #         CHECK (relacao IN ('noiva', 'noivo'))
    # );
    # """)

    # # 🔗 Tabela conexoes
    # cursor.execute("""
    # CREATE TABLE IF NOT EXISTS conexoes (
    #     id SERIAL PRIMARY KEY,
    #     convidado_id_a INTEGER NOT NULL,
    #     convidado_id_b INTEGER NOT NULL,

    #     FOREIGN KEY (convidado_id_a) REFERENCES convidados(id),
    #     FOREIGN KEY (convidado_id_b) REFERENCES convidados(id),

    #     CHECK (convidado_id_a <> convidado_id_b),
    #     CHECK (convidado_id_a < convidado_id_b),

    #     UNIQUE (convidado_id_a, convidado_id_b)
    # );
    # """)

    # # 📊 Tabela respostas
    # cursor.execute("""
    # CREATE TABLE IF NOT EXISTS respostas (
    #     id SERIAL PRIMARY KEY,
    #     timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,

    #     convidado_a INTEGER NOT NULL,
    #     convidado_b INTEGER NOT NULL,

    #     confirmado BOOLEAN NOT NULL,

    #     FOREIGN KEY (convidado_a) REFERENCES convidados(id),
    #     FOREIGN KEY (convidado_b) REFERENCES convidados(id)
    # );
    # """)

    # 📨 Tabela transfer_interesse
    # cursor.execute("""
    # CREATE TABLE IF NOT EXISTS transfer_interesse (
    #     id SERIAL PRIMARY KEY,
    #     timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    #     convidado_id INTEGER NOT NULL,
    #     responsavel_id INTEGER NOT NULL,
    #     interessado BOOLEAN NOT NULL,

    #     FOREIGN KEY (convidado_id) REFERENCES convidados(id),
    #     FOREIGN KEY (responsavel_id) REFERENCES convidados(id),

    #     UNIQUE (convidado_id)
    # );
    # """)

    cursor.execute("""
        ALTER TABLE transfer_interesse
        ALTER COLUMN interessado TYPE INTEGER
        USING (CASE WHEN interessado THEN 1 ELSE 0 END);
    """)

    # Opcional: restringir a 0/1
    cursor.execute("""
        ALTER TABLE transfer_interesse
        ADD CONSTRAINT transfer_interesse_interessado_check
        CHECK (interessado IN (0, 1));
    """)

    conn.commit()
    cursor.close()
    conn.close()

    print("Banco de dados criado com sucesso!")


if __name__ == "__main__":
    create_db()