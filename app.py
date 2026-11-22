from datetime import datetime, timedelta, timezone

from flask import Flask, flash, redirect, render_template, request, url_for
from estrutura.arvore_b import ArvoreB
from estrutura.gerador_clientes import PACOTES, gerar_clientes
from estrutura.tabela_hash import TabelaHash

from persistencia import (
    carregar_clientes,
    carregar_dados,
    salvar_clientes,
    salvar_dados,
)

app = Flask(__name__)
app.secret_key = "globalsim-ed2-chave-secreta"
tamanho = 53
tabela_paises = TabelaHash(tamanho)

dados_iniciais = carregar_dados()
for pais in dados_iniciais:
    tabela_paises.inserir(pais)

arvore_clientes = ArvoreB(grau_minimo=3)
df_clientes = carregar_clientes()
if df_clientes.empty or "cpf" not in df_clientes.columns:
    df_clientes = gerar_clientes(1000)
    salvar_clientes(df_clientes)

for linha in df_clientes.itertuples():
    try:
        arvore_clientes.inserir(linha.cpf, int(linha.posicao))
    except (KeyError, TypeError, ValueError):
        continue

@app.route("/")
def inicio():
    return render_template("index.html", total_clientes=arvore_clientes.quantidade)


@app.route("/clientes")
def listar_clientes():
    busca_cpf = "".join(filter(str.isdigit, request.args.get("cpf", "").strip()))
    cliente_encontrado = None
    posicao_encontrada = None

    if busca_cpf:
        # Busca indexada na Árvore B (O(log n)): recupera a posição no arquivo físico
        posicao = arvore_clientes.buscar(busca_cpf)
        if posicao is not None and 0 <= posicao < len(df_clientes):
            posicao_encontrada = posicao
            cliente_encontrado = df_clientes.iloc[posicao].to_dict()
        else:
            flash(f"CPF {busca_cpf} não encontrado na Árvore B.", "erro")

    # Lista os registros ordenados pelas chaves da Árvore B acessando o DataFrame físico
    pares = arvore_clientes.listar_em_ordem()
    lista_clientes = [
        df_clientes.iloc[pos].to_dict()
        for _, pos in pares
        if 0 <= pos < len(df_clientes)
    ]

    return render_template(
        "clientes.html",
        clientes=lista_clientes,
        cliente_buscado=cliente_encontrado,
        posicao_buscada=posicao_encontrada,
        pacotes=PACOTES,
        total=arvore_clientes.quantidade,
    )


@app.route("/clientes/cadastrar", methods=["POST"])
def cadastrar_cliente():
    global df_clientes
    cpf_bruto = request.form.get("cpf", "").strip()
    cpf_limpo = "".join(filter(str.isdigit, cpf_bruto))
    
    try:
        pacote = int(request.form.get("pacote", ""))
    except ValueError:
        flash("Selecione um pacote válido.", "erro")
        return redirect(url_for("listar_clientes"))

    nome = request.form.get("nome", "").strip()
    email = request.form.get("email", "").strip().lower()

    if len(cpf_limpo) != 11:
        flash("O CPF deve conter exatamente 11 dígitos numéricos.", "erro")
        return redirect(url_for("listar_clientes"))

    if not nome or "@" not in email or pacote not in PACOTES:
        flash("Preencha nome completo, e-mail válido e pacote.", "erro")
        return redirect(url_for("listar_clientes"))

    if arvore_clientes.buscar(cpf_limpo) is not None:
        flash("Já existe um cliente cadastrado com este CPF na Árvore B.", "erro")
        return redirect(url_for("listar_clientes"))

    nova_posicao = len(df_clientes)
    cliente = {
        "cpf": cpf_limpo,
        "posicao": nova_posicao,
        "nome": nome,
        "email": email,
        "esim": request.form.get("esim", "").strip() or f"GSIM-{nova_posicao + 1:08d}",
        "pacote": pacote,
        "status": "ativo",
        "ultimo_pais": "BR",
        "ultimo_acesso": (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat(),
    }

    if not arvore_clientes.inserir(cpf_limpo, nova_posicao):
        flash("Erro ao indexar CPF na Árvore B.", "erro")
    else:
        df_clientes.loc[nova_posicao] = cliente
        salvar_clientes(df_clientes)
        flash(f"Cliente cadastrado e indexado na Árvore B! Posição física no DataFrame: linha #{nova_posicao}.", "sucesso")

    return redirect(url_for("listar_clientes"))


@app.route("/clientes/alterar", methods=["POST"])
def alterar_cliente():
    global df_clientes
    cpf = "".join(filter(str.isdigit, request.form.get("cpf", "").strip()))
    try:
        pacote = int(request.form.get("pacote", ""))
    except ValueError:
        flash("Pacote inválido.", "erro")
        return redirect(url_for("listar_clientes"))

    # Busca a posição física na Árvore B
    posicao = arvore_clientes.buscar(cpf)
    if posicao is None or posicao < 0 or posicao >= len(df_clientes) or pacote not in PACOTES:
        flash("Cliente não encontrado na Árvore B ou pacote inválido.", "erro")
        return redirect(url_for("listar_clientes"))

    nome = request.form.get("nome", "").strip()
    email = request.form.get("email", "").strip().lower()
    esim = request.form.get("esim", "").strip()

    if not nome or "@" not in email or not esim:
        flash("Preencha nome, e-mail válido e identificador do eSIM.", "erro")
    else:
        df_clientes.at[posicao, "nome"] = nome
        df_clientes.at[posicao, "email"] = email
        df_clientes.at[posicao, "esim"] = esim
        df_clientes.at[posicao, "pacote"] = pacote
        salvar_clientes(df_clientes)
        flash(f"Dados do cliente (CPF {cpf}) atualizados na posição física #{posicao}.", "sucesso")

    return redirect(url_for("listar_clientes"))


@app.route("/clientes/remover", methods=["POST"])
def remover_cliente():
    global df_clientes
    cpf = "".join(filter(str.isdigit, request.form.get("cpf", "").strip()))
    posicao = arvore_clientes.buscar(cpf)
    if posicao is not None and arvore_clientes.remover(cpf):
        df_clientes.at[posicao, "status"] = "inativo"
        salvar_clientes(df_clientes)
        flash(f"Cliente (CPF {cpf}) removido do índice da Árvore B e marcado como inativo na linha #{posicao}.", "sucesso")
    else:
        flash("Cliente não encontrado na Árvore B.", "erro")
    return redirect(url_for("listar_clientes"))


@app.route("/consulta-integrada", methods=["GET", "POST"])
def consulta_integrada():
    global df_clientes
    resultado = None
    if request.method == "POST":
        cpf = "".join(filter(str.isdigit, request.form.get("cpf", "").strip()))
        destino = request.form.get("destino", "").strip().upper()

        # 1. Busca indexada na Árvore B: retorna a posição da linha física
        posicao = arvore_clientes.buscar(cpf)
        cliente = df_clientes.iloc[posicao].to_dict() if (posicao is not None and 0 <= posicao < len(df_clientes)) else None

        # 2. Busca na Tabela Hash: valida cobertura do destino
        pais = tabela_paises.buscar(destino)

        if cliente is None:
            flash(f"Cliente com CPF '{cpf}' não encontrado na Árvore B.", "erro")
        elif pais is None:
            flash(f"Destino '{destino}' sem cadastro de cobertura na Tabela Hash.", "erro")
        elif cliente.get("status") == "bloqueado_suspeita":
            resultado = {"cliente": cliente, "posicao_fisica": posicao, "pais": pais, "bloqueado": True}
            flash("eSIM bloqueado por suspeita. Revise o cadastro antes de liberar.", "erro")
        else:
            pais_anterior = tabela_paises.buscar(str(cliente.get("ultimo_pais", "")))
            try:
                ultimo_acesso = datetime.fromisoformat(str(cliente["ultimo_acesso"]))
                if ultimo_acesso.tzinfo is None:
                    ultimo_acesso = ultimo_acesso.replace(tzinfo=timezone.utc)
            except (KeyError, TypeError, ValueError):
                ultimo_acesso = datetime.now(timezone.utc) - timedelta(days=1)

            intervalo = datetime.now(timezone.utc) - ultimo_acesso
            salto_suspeito = (
                pais_anterior is not None
                and pais_anterior["regiao"] != pais["regiao"]
                and timedelta(0) <= intervalo < timedelta(hours=2)
            )

            if salto_suspeito:
                df_clientes.at[posicao, "status"] = "bloqueado_suspeita"
                salvar_clientes(df_clientes)
                cliente["status"] = "bloqueado_suspeita"
                resultado = {"cliente": cliente, "posicao_fisica": posicao, "pais": pais, "bloqueado": True}
                flash("ALERTA ANTIFRAUDE: salto entre regiões em menos de 2 horas. eSIM bloqueado no arquivo físico.", "erro")
            else:
                agora_iso = datetime.now(timezone.utc).isoformat()
                df_clientes.at[posicao, "ultimo_pais"] = destino
                df_clientes.at[posicao, "ultimo_acesso"] = agora_iso
                salvar_clientes(df_clientes)
                cliente["ultimo_pais"] = destino
                cliente["ultimo_acesso"] = agora_iso
                resultado = {"cliente": cliente, "posicao_fisica": posicao, "pais": pais, "bloqueado": False}
                flash(f"Consulta aprovada! Cliente localizado na posição física #{posicao} via Árvore B.", "sucesso")

    return render_template("consulta.html", resultado=resultado)

@app.route("/inserir_pais", methods=["POST"])
def inserir():
    codigo_limpo = request.form.get("codigo", "").strip().upper()
    
    novo_pais = {
        "codigo": codigo_limpo,
        "ddi": request.form.get("ddi"),
        "pais": request.form.get("pais"),
        "regiao": request.form.get("regiao"),
        "operadora": request.form.get("operadora"),
        "tecnologia": request.form.get("tecnologia")
    }

    inserido = tabela_paises.inserir(novo_pais)

    if inserido:
        salvar_dados(tabela_paises.listar_paises())
    
    return redirect("/listagem_paises")

@app.route("/buscar_pais", methods=["GET"])
def buscar_pais():
    codigo_limpo = request.args.get("codigo", "").strip().upper()
    pais = tabela_paises.buscar(codigo_limpo)
    return render_template("paises.html", pais=pais)

@app.route("/listagem_paises")
def listar_paises():
    lista_paises = tabela_paises.listar_paises()
    return render_template("paises.html", paises=lista_paises)

@app.route("/alterar_pais", methods=["POST"])
def alterar_pais():
    codigo_limpo = request.form.get("codigo", "").strip().upper()
    ddi = request.form.get("ddi")
    pais = request.form.get("pais")
    regiao = request.form.get("regiao")
    operadora = request.form.get("operadora")
    tecnologia = request.form.get("tecnologia")

    alterado = tabela_paises.alterar(codigo_limpo, ddi, pais, regiao, operadora, tecnologia)
    
    if alterado:
        salvar_dados(tabela_paises.listar_paises())
        
    return redirect("/listagem_paises")

@app.route("/remover_pais", methods=["POST"])
def remover_pais():
    codigo_limpo = request.form.get("codigo", "").strip().upper()
    removido = tabela_paises.remover(codigo_limpo)

    if removido:
        salvar_dados(tabela_paises.listar_paises())
        
    return redirect("/listagem_paises")

if __name__ == "__main__":
    app.run(debug=True)