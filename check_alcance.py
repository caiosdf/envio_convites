import sqlite3

DB_NAME = "convidados.db"


def tem_telefone(valor):
    return valor is not None and str(valor).strip() != ""


def main():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("PRAGMA foreign_keys = ON;")

    # Buscar todos convidados
    convidados = cursor.execute("""
        SELECT id, nome, telefone
        FROM convidados
    """).fetchall()

    resultado = []

    for convidado in convidados:
        convidado_id, nome, telefone = convidado

        # Se já tem telefone, ignora
        if tem_telefone(telefone):
            continue

        # Buscar conexões
        conexoes = cursor.execute("""
            SELECT c.id, c.nome, c.telefone
            FROM conexoes cx
            JOIN convidados c
              ON c.id = CASE
                    WHEN cx.convidado_id_a = ?
                    THEN cx.convidado_id_b
                    ELSE cx.convidado_id_a
                END
            WHERE ? IN (cx.convidado_id_a, cx.convidado_id_b)
        """, (convidado_id, convidado_id)).fetchall()

        # Verificar se alguma conexão tem telefone
        tem_telefone_em_conexao = any(
            tem_telefone(c[2]) for c in conexoes
        )

        if not tem_telefone_em_conexao:
            resultado.append({
                "id": convidado_id,
                "nome": nome,
                "conexoes": [c[1] for c in conexoes]
            })

    conn.close()

    # 📊 Output
    print("\n🚨 Convidados sem telefone e sem conexões com telefone:\n")

    for r in resultado:
        print(f"- {r['nome']} (ID: {r['id']}) | Conexões: {r['conexoes']}")

    print(f"\nTotal: {len(resultado)}")


if __name__ == "__main__":
    main()