from flask import Flask, request, render_template, redirect
import csv
import pandas as pd
from datetime import datetime

app = Flask(__name__, template_folder="../templates")

CONVIDADOS_FILE = "data/Lista_Convidados_Casamento.xlsx"
RESPOSTAS_FILE = "data/respostas.csv"


def load_convidados():
    df = pd.read_excel(CONVIDADOS_FILE,sheet_name="Noiva",converters={"id": str, "conexoes": str, "telefone": str, "Nome": str})
    df = df.set_index("id")
    res = df.to_dict(orient="index")
    return res


def get_convidado_by_phone(telefone):
    convidados = pd.DataFrame.from_dict([v for v in load_convidados().values()])
    q = convidados[convidados['telefone'] == telefone]
    q['id'] = q.index.values[0]
    res = q.iloc[0].to_dict() if not q.empty else None
    return res


def get_conexoes(convidado):
    convidados = load_convidados()
    ids = convidado['conexoes'].split(",") if convidado['conexoes'] else []
    # print(ids)
    # print(convidados)
    # res = [convidados[int(id)] for id in ids if int(id) in convidados and str(id) != str(convidado["id"])]
    res = [convidados[str(id)] for id in ids]
    return res


@app.route("/")
def home():
    return "API rodando 🚀"


@app.route("/form")
def form():
    telefone = request.args.get("telefone")

    if not telefone:
        return "Telefone não informado"

    convidado = get_convidado_by_phone(telefone)
    if not convidado:
        return "Convidado não encontrado"

    conexoes = get_conexoes(convidado)
    # print(conexoes)

    return render_template(
        "form.html",
        nome=convidado["Nome"],
        telefone=telefone,
        id=convidado["id"],
        conexoes=conexoes
    )

def load_respostas():
    try:
        df = pd.read_csv(RESPOSTAS_FILE)
    except FileNotFoundError:
        df = pd.DataFrame(columns=[
            "data", "id_principal", "nome", "telefone", "id_confirmado", "status"
        ])
    return df

def upsert_resposta(df, registro):
    id_confirmado = registro["id_confirmado"]

    idx = df[df["id_confirmado"] == id_confirmado].index

    if not idx.empty:
        df.loc[idx[0]] = registro
    else:
        df.loc[len(df)] = registro

    return df

def get_status(df, id_confirmado):
    row = df[df["id_confirmado"] == id_confirmado]
    if row.empty:
        return None
    return row.iloc[0]["status"]

def deve_marcar_nao(pessoa, df_respostas):
    tel = pessoa.get("telefone", "")
    conexoes = pessoa.get("conexoes", "")

    if tel != "-":
        return False

    if not conexoes or conexoes.strip() == "":
        return True

    ids = conexoes.split(",")

    # verifica se todas conexões já estão como NAO
    for cid in ids:
        status = get_status(df_respostas, cid)
        if status != "NAO":
            return False

    return True

@app.route("/submit", methods=["POST"])
def submit():
    nome = request.form["nome"]
    telefone = request.form["telefone"]
    id_principal = request.form["id"]
    status = request.form["status"]

    convidados = load_convidados()
    df_respostas = load_respostas()

    agora = datetime.now()

    def make_registro(id_confirmado, status):
        return {
            "data": agora,
            "id_principal": id_principal,
            "nome": nome,
            "telefone": telefone,
            "id_confirmado": id_confirmado,
            "status": status
        }

    # =========================
    # CASO SIM
    # =========================
    if status == "sim":
        confirmados = request.form.getlist("confirmados")

        for cid in confirmados:
            df_respostas = upsert_resposta(
                df_respostas,
                make_registro(cid, "SIM")
            )

    # =========================
    # CASO NAO
    # =========================
    else:
        # principal
        df_respostas = upsert_resposta(
            df_respostas,
            make_registro(id_principal, "NAO")
        )

        convidado = get_convidado_by_phone(telefone)
        conexoes = get_conexoes(convidado)

        for pessoa in conexoes:
            if deve_marcar_nao(pessoa, df_respostas):
                df_respostas = upsert_resposta(
                    df_respostas,
                    make_registro(pessoa["id"], "NAO")
                )

    # =========================
    # SALVA CSV (overwrite)
    # =========================
    df_respostas.to_csv(RESPOSTAS_FILE, index=False)

    return "Resposta registrada com sucesso ✅"


if __name__ == "__main__":
    app.run()