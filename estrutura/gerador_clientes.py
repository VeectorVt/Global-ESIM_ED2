from datetime import datetime, timedelta, timezone
import random
import pandas as pd

PACOTES = {
    101: {"nome": "Américas Essencial", "franquia_gb": 5},
    102: {"nome": "Américas Plus", "franquia_gb": 15},
    201: {"nome": "Europa Essencial", "franquia_gb": 5},
    202: {"nome": "Europa Plus", "franquia_gb": 15},
    301: {"nome": "Global", "franquia_gb": 30},
}

NOMES = [
    "Ana Silva", "Bruno Santos", "Camila Oliveira", "Diego Costa", "Elisa Souza",
    "Felipe Pereira", "Gabriela Lima", "Hugo Almeida", "Isabela Rocha", "João Martins",
    "Karina Araujo", "Lucas Ribeiro", "Marina Carvalho", "Nicolas Gomes", "Olivia Barbosa",
    "Paulo Ferreira", "Rafaela Cardoso", "Samuel Nunes", "Tainá Moreira", "Vitor Correia",
]


def gerar_cpf_valido() -> str:
    """Gera um CPF aleatório com dígitos verificadores matematicamente válidos."""
    # 9 primeiros dígitos
    nove_digitos = [random.randint(0, 9) for _ in range(9)]

    # 1º dígito verificador
    soma_1 = sum(d * peso for d, peso in zip(nove_digitos, range(10, 1, -1)))
    resto_1 = (soma_1 * 10) % 11
    d1 = 0 if resto_1 == 10 else resto_1

    # 2º dígito verificador
    dez_digitos = nove_digitos + [d1]
    soma_2 = sum(d * peso for d, peso in zip(dez_digitos, range(11, 1, -1)))
    resto_2 = (soma_2 * 10) % 11
    d2 = 0 if resto_2 == 10 else resto_2

    todos = dez_digitos + [d2]
    return "".join(map(str, todos))


def gerar_clientes(quantidade: int = 1000) -> pd.DataFrame:
    """Cria registros demonstrativos com CPFs únicos para a carga inicial da Etapa 2."""
    agora = datetime.now(timezone.utc)
    codigos_pacote = tuple(PACOTES)

    
    cpfs_unicos = set()
    while len(cpfs_unicos) < quantidade:
        cpfs_unicos.add(gerar_cpf_valido())

    lista_cpfs = list(cpfs_unicos)
    registros = []

    for indice in range(1, quantidade + 1):
        primeiro, ultimo = NOMES[(indice - 1) % len(NOMES)].split(" ", 1)
        nome = f"{primeiro} {ultimo}{indice:04d}"
        
        registros.append({
            "cpf": lista_cpfs[indice - 1],
            "posicao": indice - 1,
            "nome": nome,
            "email": f"cliente{indice:04d}@globalsim.example",
            "esim": f"GSIM-{indice:08d}",
            "pacote": codigos_pacote[(indice - 1) % len(codigos_pacote)],
            "status": "ativo",
            "ultimo_pais": "BR",
            "ultimo_acesso": (agora - timedelta(hours=24)).isoformat(),
        })

    
    df_clientes = pd.DataFrame(registros)
    return df_clientes

