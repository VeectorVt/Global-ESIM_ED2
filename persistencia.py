import json
import pandas as pd
from pathlib import Path

PASTA_ARQUIVOS = Path(__file__).resolve().parent / "arquivos"
CAMINHO_JSON = PASTA_ARQUIVOS / "paises.json"
CAMINHO_CLIENTES_JSON = PASTA_ARQUIVOS / "clientes.json"

def carregar_dados():
    """Lê o arquivo paises.json e retorna a lista de dicionários."""
    if not CAMINHO_JSON.exists():
        return []
    
    try:
        with CAMINHO_JSON.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []

def salvar_dados(lista_paises):
    """Recebe a lista de países (obtida da Tabela Hash) e grava no JSON."""
    _salvar_json(CAMINHO_JSON, lista_paises)


def carregar_clientes() -> pd.DataFrame:
    """Lê clientes.json; devolve uma lista vazia se ainda não existir."""
    if not CAMINHO_CLIENTES_JSON.exists():
        return pd.DataFrame()
    try:
        df_clientes = pd.read_json(CAMINHO_CLIENTES_JSON)
        return df_clientes
    except (json.JSONDecodeError, OSError):
        return pd.DataFrame()


def salvar_clientes(clientes):
    """Persiste clientes em JSON usando substituição atômica do arquivo."""
    if isinstance(clientes, pd.DataFrame):
        clientes = clientes.to_dict(orient="records")
    _salvar_json(CAMINHO_CLIENTES_JSON, clientes)


def _salvar_json(caminho, dados):
    caminho.parent.mkdir(parents=True, exist_ok=True)
    temporario = caminho.with_suffix(caminho.suffix + ".tmp")
    with temporario.open("w", encoding="utf-8") as arquivo:
        json.dump(dados, arquivo, ensure_ascii=False, indent=2)
    temporario.replace(caminho)