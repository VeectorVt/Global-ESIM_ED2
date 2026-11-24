import unittest

from estrutura.arvore_b import ArvoreB


class TestArvoreB(unittest.TestCase):
    def validar_invariantes(self, arvore: ArvoreB) -> None:
        def visitar(no, profundidade, folhas):
            self.assertLessEqual(len(no.chaves), 2 * arvore.grau_minimo - 1)
            if no is not arvore.raiz:
                self.assertGreaterEqual(len(no.chaves), arvore.grau_minimo - 1)
            self.assertEqual(no.chaves, sorted(no.chaves))
            if no.folha:
                folhas.add(profundidade)
                self.assertEqual(no.filhos, [])
            else:
                self.assertEqual(len(no.filhos), len(no.chaves) + 1)
                for filho in no.filhos:
                    visitar(filho, profundidade + 1, folhas)

        folhas = set()
        visitar(arvore.raiz, 0, folhas)
        self.assertLessEqual(len(folhas), 1)
        self.assertEqual(len(arvore.listar_em_ordem()), arvore.quantidade)

    def test_insercao_busca_duplicidade_e_ordem(self):
        arvore = ArvoreB(grau_minimo=3)
        for numero in range(1000, 0, -1):
            cpf = f"{numero:011d}"
            self.assertTrue(arvore.inserir(cpf, numero - 1))
        self.assertFalse(arvore.inserir("00000000500", 9999))
        self.assertEqual(arvore.buscar("00000000500"), 499)
        self.assertIsNone(arvore.buscar("00000001001"))
        pares = arvore.listar_em_ordem()
        self.assertEqual([cpf for cpf, _ in pares], sorted(cpf for cpf, _ in pares))
        self.assertEqual(len(pares), 1000)
        self.validar_invariantes(arvore)

    def test_alteracao_e_remocao_com_rebalanceamento(self):
        arvore = ArvoreB(grau_minimo=2)
        cpfs = [f"{chave:011d}" for chave in range(1, 151)]
        for posicao, cpf in enumerate(cpfs):
            arvore.inserir(cpf, posicao)
        self.assertTrue(arvore.alterar("00000000075", 999))
        self.assertEqual(arvore.buscar("00000000075"), 999)
        for cpf in cpfs[::2] + cpfs[1::2]:
            self.assertTrue(arvore.remover(cpf))
            self.validar_invariantes(arvore)
        self.assertEqual(arvore.listar_em_ordem(), [])
        self.assertFalse(arvore.remover("00000000075"))


if __name__ == "__main__":
    unittest.main()
