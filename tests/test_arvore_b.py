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
        for chave in range(1000, 0, -1):
            self.assertTrue(arvore.inserir({"id": chave, "nome": f"Cliente {chave}"}))
        self.assertFalse(arvore.inserir({"id": 500, "nome": "Duplicado"}))
        self.assertEqual(arvore.buscar(500)["nome"], "Cliente 500")
        self.assertIsNone(arvore.buscar(1001))
        self.assertEqual([item["id"] for item in arvore.listar_em_ordem()], list(range(1, 1001)))
        self.validar_invariantes(arvore)

    def test_alteracao_e_remocao_com_rebalanceamento(self):
        arvore = ArvoreB(grau_minimo=2)
        for chave in range(1, 151):
            arvore.inserir({"id": chave, "nome": str(chave)})
        self.assertTrue(arvore.alterar(75, {"id": 75, "nome": "Atualizado"}))
        self.assertEqual(arvore.buscar(75)["nome"], "Atualizado")
        for chave in list(range(1, 151))[::2] + list(range(2, 151))[::2]:
            self.assertTrue(arvore.remover(chave))
            self.validar_invariantes(arvore)
        self.assertEqual(arvore.listar_em_ordem(), [])
        self.assertFalse(arvore.remover(75))


if __name__ == "__main__":
    unittest.main()
