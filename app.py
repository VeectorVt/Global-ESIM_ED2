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
tamanho = 53
tabela_paises = TabelaHash(tamanho)

dados_iniciais = carregar_dados()
for pais in dados_iniciais:
    tabela_paises.inserir(pais)

arvore_clientes = ArvoreB(grau_minimo=3)
clientes_iniciais = carregar_clientes()
if not clientes_iniciais:
    clientes_iniciais = gerar_clientes(1000)
    salvar_clientes(clientes_iniciais)
for cliente in clientes_iniciais:
    try:
        arvore_clientes.inserir(cliente)
    except (KeyError, TypeError, ValueError):
        continue

@app.route("/")
def inicio():
    return render_template("index.html", total_clientes=arvore_clientes.quantidade)


@app.route("/clientes")
def listar_clientes():
    return render_template(
        "clientes.html",
        clientes=arvore_clientes.listar_em_ordem(),
        pacotes=PACOTES,
        total=arvore_clientes.quantidade,
    )


@app.route("/clientes/cadastrar", methods=["POST"])
def cadastrar_cliente():
    try:
        identificador = int(request.form.get("id", ""))
        pacote = int(request.form.get("pacote", ""))
    except ValueError:
        flash("ID e pacote devem ser valores numéricos.", "erro")
        return redirect(url_for("listar_clientes"))

    nome = request.form.get("nome", "").strip()
    email = request.form.get("email", "").strip().lower()
    if identificador < 1 or not nome or "@" not in email or pacote not in PACOTES:
        flash("Informe ID positivo, nome, e-mail válido e um dos pacotes disponíveis.", "erro")
        return redirect(url_for("listar_clientes"))

    cliente = {
        "id": identificador,
        "nome": nome,
        "email": email,
        "esim": request.form.get("esim", "").strip() or f"GSIM-{identificador:08d}",
        "pacote": pacote,
        "status": "ativo",
        "ultimo_pais": "BR",
        "ultimo_acesso": (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat(),
    }
    if not arvore_clientes.inserir(cliente):
        flash("Já existe um cliente com esse ID.", "erro")
    else:
        salvar_clientes(arvore_clientes.listar_em_ordem())
        flash("Cliente cadastrado.", "sucesso")
    return redirect(url_for("listar_clientes"))


@app.route("/clientes/alterar", methods=["POST"])
def alterar_cliente():
    try:
        identificador = int(request.form.get("id", ""))
        pacote = int(request.form.get("pacote", ""))
    except ValueError:
        flash("ID ou pacote inválido.", "erro")
        return redirect(url_for("listar_clientes"))
    atual = arvore_clientes.buscar(identificador)
    if atual is None or pacote not in PACOTES:
        flash("Cliente não encontrado ou pacote inválido.", "erro")
        return redirect(url_for("listar_clientes"))
    atualizado = atual.copy()
    atualizado.update({
        "nome": request.form.get("nome", "").strip(),
        "email": request.form.get("email", "").strip().lower(),
        "esim": request.form.get("esim", "").strip(),
        "pacote": pacote,
    })
    if not atualizado["nome"] or "@" not in atualizado["email"] or not atualizado["esim"]:
        flash("Preencha nome, e-mail válido e identificador do eSIM.", "erro")
    else:
        arvore_clientes.alterar(identificador, atualizado)
        salvar_clientes(arvore_clientes.listar_em_ordem())
        flash("Dados do cliente atualizados.", "sucesso")
    return redirect(url_for("listar_clientes"))


@app.route("/clientes/remover", methods=["POST"])
def remover_cliente():
    try:
        identificador = int(request.form.get("id", ""))
    except ValueError:
        identificador = -1
    if arvore_clientes.remover(identificador):
        salvar_clientes(arvore_clientes.listar_em_ordem())
        flash("Cliente removido.", "sucesso")
    else:
        flash("Cliente não encontrado.", "erro")
    return redirect(url_for("listar_clientes"))


@app.route("/consulta-integrada", methods=["GET", "POST"])
def consulta_integrada():
    resultado = None
    if request.method == "POST":
        try:
            identificador = int(request.form.get("id", ""))
        except ValueError:
            identificador = -1
        destino = request.form.get("destino", "").strip().upper()
        cliente = arvore_clientes.buscar(identificador)
        pais = tabela_paises.buscar(destino)
        if cliente is None:
            flash("Cliente não encontrado na Árvore B.", "erro")
        elif pais is None:
            flash("Destino sem cadastro de cobertura na Tabela Hash.", "erro")
        elif cliente["status"] == "bloqueado_suspeita":
            resultado = {"cliente": cliente, "pais": pais, "bloqueado": True}
            flash("eSIM bloqueado por suspeita. Revise o cadastro antes de liberar.", "erro")
        else:
            pais_anterior = tabela_paises.buscar(cliente.get("ultimo_pais", ""))
            try:
                ultimo_acesso = datetime.fromisoformat(cliente["ultimo_acesso"])
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
                cliente["status"] = "bloqueado_suspeita"
                cliente["ultima_tentativa"] = {
                    "destino": destino,
                    "horario": datetime.now(timezone.utc).isoformat(),
                }
                salvar_clientes(arvore_clientes.listar_em_ordem())
                resultado = {"cliente": cliente, "pais": pais, "bloqueado": True}
                flash("ALERTA ANTIFRAUDE: salto entre regiões em menos de 2 horas. eSIM bloqueado.", "erro")
            else:
                cliente["ultimo_pais"] = destino
                cliente["ultimo_acesso"] = datetime.now(timezone.utc).isoformat()
                salvar_clientes(arvore_clientes.listar_em_ordem())
                resultado = {"cliente": cliente, "pais": pais, "bloqueado": False}
                flash("Consulta aprovada: cobertura encontrada.", "sucesso")
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