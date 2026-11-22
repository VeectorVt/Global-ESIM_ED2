class NoB:
    """Nó de uma Árvore B; armazena chaves (CPFs) ordenadas, posições no arquivo e filhos."""

    def __init__(self, grau_minimo: int, folha: bool = True):
        self.grau_minimo = grau_minimo
        self.folha = folha
        self.chaves: list[str] = []
        self.valores: list[int] = []  # Armazena apenas a posição (índice da linha) no arquivo físico/DataFrame
        self.filhos: list[NoB] = []


class ArvoreB:
    """Árvore B como índice primário: armazena (CPF -> posição no arquivo físico)."""

    def __init__(self, grau_minimo: int = 3):
        if grau_minimo < 2:
            raise ValueError("O grau mínimo da Árvore B deve ser pelo menos 2.")
        self.grau_minimo = grau_minimo
        self.raiz = NoB(grau_minimo)
        self.quantidade = 0

    def buscar(self, chave: str | int) -> int | None:
        """Busca o CPF na Árvore B e retorna a posição (linha no DataFrame), ou None."""
        chave_str = str(chave).strip()
        return self._buscar_no(self.raiz, chave_str)

    def _buscar_no(self, no: NoB, chave: str) -> int | None:
        indice = 0
        while indice < len(no.chaves) and chave > no.chaves[indice]:
            indice += 1
        if indice < len(no.chaves) and chave == no.chaves[indice]:
            return no.valores[indice]
        if no.folha:
            return None
        return self._buscar_no(no.filhos[indice], chave)

    def inserir(self, chave_ou_registro, posicao: int | None = None) -> bool:
        """
        Insere a chave (CPF) e sua posição no arquivo físico.
        Pode ser chamada de duas formas:
          - inserir(cpf, posicao)
          - inserir({"cpf": "...", "posicao": ...})
        """
        if isinstance(chave_ou_registro, dict) or hasattr(chave_ou_registro, "__getitem__") and not isinstance(chave_ou_registro, str):
            chave = str(chave_ou_registro["cpf"]).strip()
            posicao = int(chave_ou_registro["posicao"])
        else:
            chave = str(chave_ou_registro).strip()
            if posicao is None:
                raise ValueError("A posição no arquivo físico/DataFrame deve ser informada.")
            posicao = int(posicao)

        if self.buscar(chave) is not None:
            return False

        raiz = self.raiz
        limite = 2 * self.grau_minimo - 1
        if len(raiz.chaves) == limite:
            nova_raiz = NoB(self.grau_minimo, folha=False)
            nova_raiz.filhos.append(raiz)
            self._dividir_filho(nova_raiz, 0)
            self.raiz = nova_raiz
        self._inserir_nao_cheio(self.raiz, chave, posicao)
        self.quantidade += 1
        return True

    def _inserir_nao_cheio(self, no: NoB, chave: str, posicao: int) -> None:
        indice = len(no.chaves) - 1
        if no.folha:
            no.chaves.append("")
            no.valores.append(0)
            while indice >= 0 and chave < no.chaves[indice]:
                no.chaves[indice + 1] = no.chaves[indice]
                no.valores[indice + 1] = no.valores[indice]
                indice -= 1
            no.chaves[indice + 1] = chave
            no.valores[indice + 1] = posicao
            return

        while indice >= 0 and chave < no.chaves[indice]:
            indice -= 1
        indice += 1
        if len(no.filhos[indice].chaves) == 2 * self.grau_minimo - 1:
            self._dividir_filho(no, indice)
            if chave > no.chaves[indice]:
                indice += 1
        self._inserir_nao_cheio(no.filhos[indice], chave, posicao)

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

    def alterar(self, chave: str | int, nova_posicao: int) -> bool:
        """Atualiza a posição física associada ao CPF."""
        chave_str = str(chave).strip()
        return self._alterar_no(self.raiz, chave_str, int(nova_posicao))

    def _alterar_no(self, no: NoB, chave: str, nova_posicao: int) -> bool:
        indice = 0
        while indice < len(no.chaves) and chave > no.chaves[indice]:
            indice += 1
        if indice < len(no.chaves) and chave == no.chaves[indice]:
            no.valores[indice] = nova_posicao
            return True
        if no.folha:
            return False
        return self._alterar_no(no.filhos[indice], chave, nova_posicao)

    def remover(self, chave: str | int) -> bool:
        chave_str = str(chave).strip()
        if self.buscar(chave_str) is None:
            return False
        self._remover(self.raiz, chave_str)
        if not self.raiz.folha and not self.raiz.chaves:
            self.raiz = self.raiz.filhos[0]
        self.quantidade -= 1
        return True

    def _remover(self, no: NoB, chave: str) -> None:
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

    def _maximo(self, no: NoB) -> tuple[str, int]:
        while not no.folha:
            no = no.filhos[-1]
        return no.chaves[-1], no.valores[-1]

    def _minimo(self, no: NoB) -> tuple[str, int]:
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

    def listar_em_ordem(self) -> list[tuple[str, int]]:
        """Retorna os pares (cpf, posicao) ordenados pelo CPF."""
        indices: list[tuple[str, int]] = []
        self._percorrer(self.raiz, indices)
        return indices

    def _percorrer(self, no: NoB, indices: list[tuple[str, int]]) -> None:
        for indice, pos in enumerate(no.valores):
            if not no.folha:
                self._percorrer(no.filhos[indice], indices)
            indices.append((no.chaves[indice], pos))
        if not no.folha:
            self._percorrer(no.filhos[-1], indices)

