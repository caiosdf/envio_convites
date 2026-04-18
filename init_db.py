import sqlite3

DB_NAME = "convidados.db"

def create_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # 🔒 Ativar foreign keys
    cursor.execute("PRAGMA foreign_keys = ON;")

    # 🧱 Tabela convidados
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS convidados (
        id INTEGER PRIMARY KEY UNIQUE,
        nome TEXT NOT NULL,
        telefone TEXT,
        faixa_etaria TEXT NOT NULL
            CHECK (faixa_etaria IN ('adulto', 'crianca')),
        relacao TEXT NOT NULL
            CHECK (relacao IN ('noiva', 'noivo'))
    );
    """)

    # 🔗 Tabela conexoes
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS conexoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        convidado_id_a INTEGER NOT NULL,
        convidado_id_b INTEGER NOT NULL,

        FOREIGN KEY (convidado_id_a) REFERENCES convidados(id),
        FOREIGN KEY (convidado_id_b) REFERENCES convidados(id),

        CHECK (convidado_id_a <> convidado_id_b),
        CHECK (convidado_id_a < convidado_id_b),

        UNIQUE (convidado_id_a, convidado_id_b)
    );
    """)

    # 📊 Tabela respostas
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS respostas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,

        convidado_a INTEGER NOT NULL,
        convidado_b INTEGER NOT NULL,

        confirmado BOOLEAN NOT NULL,

        FOREIGN KEY (convidado_a) REFERENCES convidados(id),
        FOREIGN KEY (convidado_b) REFERENCES convidados(id)
    );
    """)

    conn.commit()
    conn.close()

    print("Banco de dados criado com sucesso!")

if __name__ == "__main__":
    create_db()