import pandas as pd
import numpy as np
import sqlite3

DB_NAME = "convidados.db"
FILE_PATH = r"data/Lista_Convidados_Casamento.xlsx"  # ou .csv


def normalize_faixa(value):
    value = str(value).strip().lower()
    return "crianca" if "cri" in value else "adulto"


def normalize_relacao(value):
    value = str(value).strip().lower()
    return "noiva" if "noiva" in value else "noivo"


def main():
    df = pd.read_excel(FILE_PATH, sheet_name="Planilha1",converters={"telefone": str,"conexoes": str})
    # df.replace({'.': ','}, inplace=True)
    df.replace({'-': None}, inplace=True)
    # print(df.iloc[15:25])
    # exit()

    # 🔌 Conectar no banco
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")

    # 🧹 Limpar tabelas (opcional)
    cursor.execute("DELETE FROM conexoes;")
    cursor.execute("DELETE FROM convidados;")

    # 🧱 Inserir convidados
    convidados_map = {}

    for _, row in df.iterrows():
        id = row["id"]
        nome = row["Nome"]
        telefone = str(row["telefone"])
        faixa = normalize_faixa(row["faixa etaria"])
        relacao = normalize_relacao(row["relação"])

        cursor.execute("""
            INSERT INTO convidados (id, nome, telefone, faixa_etaria, relacao)
            VALUES (?, ?, ?, ?, ?)
        """, (id, nome, telefone, faixa, relacao))

        convidado_id = cursor.lastrowid
        convidados_map[row["id"]] = convidado_id

    # 🔗 Inserir conexões
    conexoes_set = set()

    for _, row in df.iterrows():
        origem = convidados_map[row["id"]]

        if pd.isna(row["conexoes"]):
            continue

        destinos = str(row["conexoes"]).split(",")
        print(f"Processando conexões para {row['Nome']} (origem ID {origem}): {destinos}")
        for d in destinos:
            d = d.strip()
            if not d:
                continue

            destino = convidados_map.get(int(d))
            if not destino:
                continue

            a, b = sorted([origem, destino])

            # evita duplicidade
            if (a, b) in conexoes_set:
                continue

            conexoes_set.add((a, b))

            cursor.execute("""
                INSERT OR IGNORE INTO conexoes (convidado_id_a, convidado_id_b)
                VALUES (?, ?)
            """, (a, b))

    conn.commit()
    conn.close()

    print("✅ Importação concluída com sucesso!")


if __name__ == "__main__":
    main()