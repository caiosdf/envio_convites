from flask import Flask, request, render_template
import sqlite3
from datetime import datetime

app = Flask(__name__, template_folder="../templates")

DB_NAME = "convidados.db"


# 🔌 conexão helper
def get_conn():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def get_ultima_confirmacao(convidado_id):
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT r.*, c.nome as nome_confirmador
        FROM respostas r
        JOIN convidados c ON c.id = r.convidado_a
        WHERE r.convidado_b = ?
        ORDER BY r.timestamp DESC
        LIMIT 1
    """, (convidado_id,))

    row = cursor.fetchone()
    conn.close()

    return dict(row) if row else None

# 🔎 buscar convidado por telefone
def get_convidado_by_phone(telefone):
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM convidados
        WHERE telefone = ?
    """, (telefone,))

    row = cursor.fetchone()
    conn.close()

    return dict(row) if row else None


# 🔗 buscar conexões
def get_conexoes(convidado_id):
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT c.*
        FROM conexoes cx
        JOIN convidados c
          ON c.id = CASE
                WHEN cx.convidado_id_a = ?
                THEN cx.convidado_id_b
                ELSE cx.convidado_id_a
          END
        WHERE ? IN (cx.convidado_id_a, cx.convidado_id_b)
    """, (convidado_id, convidado_id))

    rows = cursor.fetchall()
    conn.close()

    return [dict(r) for r in rows]


@app.route("/")
def home():
    return render_template("home.html")


# 📄 formulário
@app.route("/form")
def form():
    telefone = request.args.get("telefone")

    if not telefone:
        return "Telefone não informado"

    convidado = get_convidado_by_phone(telefone)
    if not convidado:
        return "Convidado não encontrado"

    # 🔍 verifica confirmação existente
    confirmacao = get_ultima_confirmacao(convidado["id"])

    override = request.args.get("override")

    if confirmacao and not override:
        return render_template(
            "confirmado.html",
            nome=convidado["nome"],
            confirmador=confirmacao["nome_confirmador"],
            status="SIM" if confirmacao["confirmado"] == 1 else "NÃO",
            telefone=telefone
        )

    conexoes = get_conexoes(convidado["id"])

    return render_template(
        "form.html",
        nome=convidado["nome"],
        telefone=telefone,
        id=convidado["id"],
        conexoes=conexoes
    )

# 🧠 regra: verificar se todas conexões são NÃO
def todas_conexoes_nao(convidado_id, conn):
    cursor = conn.cursor()

    cursor.execute("""
        SELECT c.id
        FROM conexoes cx
        JOIN convidados c
          ON c.id = CASE
                WHEN cx.convidado_id_a = ?
                THEN cx.convidado_id_b
                ELSE cx.convidado_id_a
          END
        WHERE ? IN (cx.convidado_id_a, cx.convidado_id_b)
    """, (convidado_id, convidado_id))

    conexoes = cursor.fetchall()

    for c in conexoes:
        cursor.execute("""
            SELECT confirmado
            FROM respostas
            WHERE convidado_b = ?
            ORDER BY timestamp DESC
            LIMIT 1
        """, (c["id"],))

        r = cursor.fetchone()

        if not r or r["confirmado"] != 0:
            return False

    return True


# 📩 submit
@app.route("/submit", methods=["POST"])
def submit():
    conn = get_conn()
    cursor = conn.cursor()

    nome = request.form["nome"]
    telefone = request.form["telefone"]
    id_principal = int(request.form["id"])
    status = request.form["status"]

    agora = datetime.now()

    def salvar(convidado_b, confirmado):
        cursor.execute("""
            INSERT INTO respostas (timestamp, convidado_a, convidado_b, confirmado)
            VALUES (?, ?, ?, ?)
        """, (agora, id_principal, convidado_b, confirmado))

    # =========================
    # CASO SIM
    # =========================
    if status == "sim":
        confirmados = set(map(int, request.form.getlist("confirmados")))

        # 👤 principal + conexões
        conexoes = get_conexoes(id_principal)
        todos_ids = {id_principal} | {p["id"] for p in conexoes}

        for cid in todos_ids:
            if cid in confirmados:
                salvar(cid, 1)
            else:
                salvar(cid, 0)

    # =========================
    # CASO NAO
    # =========================
    else:
        # principal
        salvar(id_principal, 0)

        conexoes = get_conexoes(id_principal)

        for pessoa in conexoes:
            if todas_conexoes_nao(pessoa["id"], conn):
                salvar(pessoa["id"], 0)

    conn.commit()
    conn.close()

    return render_template(
        "success.html",
        nome=nome,
        telefone=telefone,
        status="SIM" if status == "sim" else "NÃO"
    )


if __name__ == "__main__":
    app.run(debug=True)