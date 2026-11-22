from datetime import datetime, timedelta, timezone

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


def gerar_clientes(quantidade: int = 1000) -> list[dict]:
    """Cria registros demonstrativos reproduzíveis para a carga inicial da Etapa 2."""
    agora = datetime.now(timezone.utc)
    clientes = []
    codigos_pacote = tuple(PACOTES)
    for indice in range(1, quantidade + 1):
        primeiro, ultimo = NOMES[(indice - 1) % len(NOMES)].split(" ", 1)
        nome = f"{primeiro} {ultimo}{indice:04d}"
        clientes.append({
            "id": indice,
            "nome": nome,
            "email": f"cliente{indice:04d}@globalsim.example",
            "esim": f"GSIM-{indice:08d}",
            "pacote": codigos_pacote[(indice - 1) % len(codigos_pacote)],
            "status": "ativo",
            "ultimo_pais": "BR",
            "ultimo_acesso": (agora - timedelta(hours=24)).isoformat(),
        })
    return clientes
