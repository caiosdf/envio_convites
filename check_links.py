import sqlite3
import csv

DB_NAME = "convidados.db"
BASE_URL = "https://eieiei.vercel.app/form"


def get_convidados():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT nome, telefone
        FROM convidados
        WHERE telefone IS NOT NULL
        AND TRIM(telefone) <> ''
    """)

    rows = cursor.fetchall()
    conn.close()

    return rows


def gerar_link(telefone):
    return f"{BASE_URL}?telefone={telefone}"


def main():
    convidados = get_convidados()

    resultado = []

    print("\n📋 Lista de convites:\n")

    for nome, telefone in convidados:
        link = gerar_link(telefone)

        resultado.append((nome, telefone, link))

        print(f"{nome} → {link}")


if __name__ == "__main__":
    main()