class NoB:
    """Nó de uma Árvore B; listas armazenam chaves ordenadas e filhos do nó."""

    def __init__(self, grau_minimo: int, folha: bool = True):
        self.grau_minimo = grau_minimo
        self.folha = folha
        self.chaves: list[int] = []
        self.valores: list[dict] = []
        self.filhos: list[NoB] = []


class ArvoreB:
    """Árvore B indexada pelo ID inteiro do cliente (busca O(log n))."""

    def __init__(self, grau_minimo: int = 3):
        if grau_minimo < 2:
            raise ValueError("O grau mínimo da Árvore B deve ser pelo menos 2.")
        self.grau_minimo = grau_minimo
        self.raiz = NoB(grau_minimo)
        self.quantidade = 0

    def buscar(self, chave: int) -> dict | None:
        return self._buscar_no(self.raiz, chave)

    def _buscar_no(self, no: NoB, chave: int) -> dict | None:
        indice = 0
        while indice < len(no.chaves) and chave > no.chaves[indice]:
            indice += 1
        if indice < len(no.chaves) and chave == no.chaves[indice]:
            return no.valores[indice]
        if no.folha:
            return None
        return self._buscar_no(no.filhos[indice], chave)

    def inserir(self, valor: dict) -> bool:
        chave = int(valor["id"])
        if self.buscar(chave) is not None:
            return False
        raiz = self.raiz
        limite = 2 * self.grau_minimo - 1
        if len(raiz.chaves) == limite:
            nova_raiz = NoB(self.grau_minimo, folha=False)
            nova_raiz.filhos.append(raiz)
            self._dividir_filho(nova_raiz, 0)
            self.raiz = nova_raiz
        self._inserir_nao_cheio(self.raiz, chave, valor)
        self.quantidade += 1
        return True

    def _inserir_nao_cheio(self, no: NoB, chave: int, valor: dict) -> None:
        indice = len(no.chaves) - 1
        if no.folha:
            no.chaves.append(0)
            no.valores.append({})
            while indice >= 0 and chave < no.chaves[indice]:
                no.chaves[indice + 1] = no.chaves[indice]
                no.valores[indice + 1] = no.valores[indice]
                indice -= 1
            no.chaves[indice + 1] = chave
            no.valores[indice + 1] = valor
            return

        while indice >= 0 and chave < no.chaves[indice]:
            indice -= 1
        indice += 1
        if len(no.filhos[indice].chaves) == 2 * self.grau_minimo - 1:
            self._dividir_filho(no, indice)
            if chave > no.chaves[indice]:
                indice += 1
        self._inserir_nao_cheio(no.filhos[indice], chave, valor)

    def _dividir_filho(self, pai: NoB, indice: int) -> None:
        grau = self.grau_minimo
        cheio = pai.filhos[indice]
        novo = NoB(grau, cheio.folha)
        chave_mediana = cheio.chaves[grau - 1]
        valor_mediano = cheio.valores[grau - 1]
        novo.chaves = cheio.chaves[grau:]
        novo.valores = cheio.valores[grau:]
        cheio.chaves = cheio.chaves[:grau - 1]
        cheio.valores = cheio.valores[:grau - 1]
        if not cheio.folha:
            novo.filhos = cheio.filhos[grau:]
            cheio.filhos = cheio.filhos[:grau]
        pai.filhos.insert(indice + 1, novo)
        pai.chaves.insert(indice, chave_mediana)
        pai.valores.insert(indice, valor_mediano)

    def alterar(self, chave: int, valor: dict) -> bool:
        existente = self.buscar(chave)
        if existente is None:
            return False
        valor["id"] = int(chave)
        existente.clear()
        existente.update(valor)
        return True

    def remover(self, chave: int) -> bool:
        if self.buscar(chave) is None:
            return False
        self._remover(self.raiz, chave)
        if not self.raiz.folha and not self.raiz.chaves:
            self.raiz = self.raiz.filhos[0]
        self.quantidade -= 1
        return True

    def _remover(self, no: NoB, chave: int) -> None:
        indice = 0
        while indice < len(no.chaves) and no.chaves[indice] < chave:
            indice += 1
        if indice < len(no.chaves) and no.chaves[indice] == chave:
            if no.folha:
                no.chaves.pop(indice)
                no.valores.pop(indice)
            else:
                self._remover_interno(no, indice)
            return

        if no.folha:
            return
        esta_no_ultimo_filho = indice == len(no.chaves)
        if len(no.filhos[indice].chaves) < self.grau_minimo:
            self._preparar_filho(no, indice)
            if esta_no_ultimo_filho and indice > len(no.chaves):
                indice -= 1
        self._remover(no.filhos[indice], chave)

    def _remover_interno(self, no: NoB, indice: int) -> None:
        chave = no.chaves[indice]
        if len(no.filhos[indice].chaves) >= self.grau_minimo:
            predecessor, valor = self._maximo(no.filhos[indice])
            no.chaves[indice] = predecessor
            no.valores[indice] = valor
            self._remover(no.filhos[indice], predecessor)
        elif len(no.filhos[indice + 1].chaves) >= self.grau_minimo:
            sucessor, valor = self._minimo(no.filhos[indice + 1])
            no.chaves[indice] = sucessor
            no.valores[indice] = valor
            self._remover(no.filhos[indice + 1], sucessor)
        else:
            self._fundir(no, indice)
            self._remover(no.filhos[indice], chave)

    def _maximo(self, no: NoB) -> tuple[int, dict]:
        while not no.folha:
            no = no.filhos[-1]
        return no.chaves[-1], no.valores[-1]

    def _minimo(self, no: NoB) -> tuple[int, dict]:
        while not no.folha:
            no = no.filhos[0]
        return no.chaves[0], no.valores[0]

    def _preparar_filho(self, pai: NoB, indice: int) -> None:
        if indice > 0 and len(pai.filhos[indice - 1].chaves) >= self.grau_minimo:
            filho = pai.filhos[indice]
            irmao = pai.filhos[indice - 1]
            filho.chaves.insert(0, pai.chaves[indice - 1])
            filho.valores.insert(0, pai.valores[indice - 1])
            if not filho.folha:
                filho.filhos.insert(0, irmao.filhos.pop())
            pai.chaves[indice - 1] = irmao.chaves.pop()
            pai.valores[indice - 1] = irmao.valores.pop()
        elif indice < len(pai.chaves) and len(pai.filhos[indice + 1].chaves) >= self.grau_minimo:
            filho = pai.filhos[indice]
            irmao = pai.filhos[indice + 1]
            filho.chaves.append(pai.chaves[indice])
            filho.valores.append(pai.valores[indice])
            if not filho.folha:
                filho.filhos.append(irmao.filhos.pop(0))
            pai.chaves[indice] = irmao.chaves.pop(0)
            pai.valores[indice] = irmao.valores.pop(0)
        elif indice < len(pai.chaves):
            self._fundir(pai, indice)
        else:
            self._fundir(pai, indice - 1)

    def _fundir(self, pai: NoB, indice: int) -> None:
        filho = pai.filhos[indice]
        irmao = pai.filhos[indice + 1]
        filho.chaves.append(pai.chaves.pop(indice))
        filho.valores.append(pai.valores.pop(indice))
        filho.chaves.extend(irmao.chaves)
        filho.valores.extend(irmao.valores)
        if not filho.folha:
            filho.filhos.extend(irmao.filhos)
        pai.filhos.pop(indice + 1)

    def listar_em_ordem(self) -> list[dict]:
        registros: list[dict] = []
        self._percorrer(self.raiz, registros)
        return registros

    def _percorrer(self, no: NoB, registros: list[dict]) -> None:
        for indice, valor in enumerate(no.valores):
            if not no.folha:
                self._percorrer(no.filhos[indice], registros)
            registros.append(valor)
        if not no.folha:
            self._percorrer(no.filhos[-1], registros)
