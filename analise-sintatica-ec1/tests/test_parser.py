"""Testes para o analisador sintatico e interpretador de EC1."""

from __future__ import annotations

import os
import sys
import unittest

# permite rodar `python tests/test_parser.py` a partir da pasta do projeto
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from ast_ec1 import Const, Op, OpBin  # noqa: E402
from lexer import ErroLexico  # noqa: E402
from parser import ErroSintatico, analisar  # noqa: E402


class TestArvoreSintatica(unittest.TestCase):
    """Verifica que o parser produz a AST correta."""

    def test_constante_simples(self) -> None:
        self.assertEqual(analisar("42"), Const(42))

    def test_constante_varios_digitos(self) -> None:
        self.assertEqual(analisar("333"), Const(333))

    def test_constante_zero(self) -> None:
        self.assertEqual(analisar("0"), Const(0))

    def test_operacao_simples_soma(self) -> None:
        self.assertEqual(analisar("(1 + 2)"), OpBin(Op.SOMA, Const(1), Const(2)))

    def test_operacao_simples_subtracao(self) -> None:
        self.assertEqual(analisar("(10 - 4)"), OpBin(Op.SUB, Const(10), Const(4)))

    def test_operacao_simples_multiplicacao(self) -> None:
        self.assertEqual(analisar("(6 * 7)"), OpBin(Op.MULT, Const(6), Const(7)))

    def test_operacao_simples_divisao(self) -> None:
        self.assertEqual(analisar("(20 / 4)"), OpBin(Op.DIV, Const(20), Const(4)))

    def test_exemplo_do_enunciado(self) -> None:
        # (33 + (912 * 11)) deve produzir a arvore mostrada no enunciado:
        #     +
        #    / \
        #   33  *
        #      / \
        #    912  11
        esperado = OpBin(
            Op.SOMA,
            Const(33),
            OpBin(Op.MULT, Const(912), Const(11)),
        )
        self.assertEqual(analisar("(33 + (912 * 11))"), esperado)

    def test_aninhamento_profundo(self) -> None:
        # (3 + (4 + (11 + 7)))
        esperado = OpBin(
            Op.SOMA,
            Const(3),
            OpBin(Op.SOMA, Const(4), OpBin(Op.SOMA, Const(11), Const(7))),
        )
        self.assertEqual(analisar("(3 + (4 + (11 + 7)))"), esperado)

    def test_expressao_complexa_do_enunciado(self) -> None:
        # ((427 / 7) + (11 * (231 + 5)))
        esperado = OpBin(
            Op.SOMA,
            OpBin(Op.DIV, Const(427), Const(7)),
            OpBin(Op.MULT, Const(11), OpBin(Op.SOMA, Const(231), Const(5))),
        )
        self.assertEqual(
            analisar("((427 / 7) + (11 * (231 + 5)))"), esperado
        )

    def test_espacos_e_quebras_de_linha_irrelevantes(self) -> None:
        compacta = analisar("(1+2)")
        espacada = analisar("  ( 1   +\n   2 )\n")
        self.assertEqual(compacta, espacada)


class TestInterpretador(unittest.TestCase):
    """Verifica que avaliar() produz o resultado correto."""

    def test_constante(self) -> None:
        self.assertEqual(analisar("42").avaliar(), 42)

    def test_soma(self) -> None:
        self.assertEqual(analisar("(1 + 2)").avaliar(), 3)

    def test_subtracao(self) -> None:
        self.assertEqual(analisar("(10 - 4)").avaliar(), 6)

    def test_multiplicacao(self) -> None:
        self.assertEqual(analisar("(6 * 7)").avaliar(), 42)

    def test_divisao_exata(self) -> None:
        self.assertEqual(analisar("(20 / 4)").avaliar(), 5)

    def test_exemplo_do_enunciado_avaliacao(self) -> None:
        # (33 + (912 * 11)) = 33 + 10032 = 10065
        self.assertEqual(analisar("(33 + (912 * 11))").avaliar(), 10065)

    def test_exemplo_complexo_avaliacao(self) -> None:
        # ((427 / 7) + (11 * (231 + 5))) = 61 + 11*236 = 61 + 2596 = 2657
        self.assertEqual(
            analisar("((427 / 7) + (11 * (231 + 5)))").avaliar(), 2657
        )

    def test_aninhamento_avaliacao(self) -> None:
        # (3 + (4 + (11 + 7))) = 3 + (4 + 18) = 3 + 22 = 25
        self.assertEqual(analisar("(3 + (4 + (11 + 7)))").avaliar(), 25)

    def test_divisao_por_zero_levanta(self) -> None:
        with self.assertRaises(ZeroDivisionError):
            analisar("(10 / 0)").avaliar()


class TestErrosSintaticos(unittest.TestCase):
    """Verifica deteccao de programas mal formados."""

    def test_entrada_vazia(self) -> None:
        with self.assertRaises(ErroSintatico):
            analisar("")

    def test_apenas_espacos(self) -> None:
        with self.assertRaises(ErroSintatico):
            analisar("   \n\t  ")

    def test_parentese_nao_fechado(self) -> None:
        with self.assertRaises(ErroSintatico):
            analisar("(33 + (912 * 11)")

    def test_parentese_fechando_inesperado(self) -> None:
        with self.assertRaises(ErroSintatico):
            analisar(")")

    def test_operador_sem_operandos(self) -> None:
        with self.assertRaises(ErroSintatico):
            analisar("(+ 1 2)")

    def test_operando_no_lugar_de_operador(self) -> None:
        # (3 3 4) — esperava operador, encontrou Numero
        with self.assertRaises(ErroSintatico):
            analisar("(3 3 4)")

    def test_lixo_apos_expressao_raiz(self) -> None:
        with self.assertRaises(ErroSintatico):
            analisar("(6 * 7) 42")

    def test_so_abre_parenteses(self) -> None:
        with self.assertRaises(ErroSintatico):
            analisar("(")

    def test_falta_operando_direito(self) -> None:
        with self.assertRaises(ErroSintatico):
            analisar("(1 +)")

    def test_erro_lexico_caractere_invalido(self) -> None:
        # 'x' nao pertence ao alfabeto da linguagem
        with self.assertRaises(ErroLexico):
            analisar("(12 x 5)")


class TestImpressaoCanonica(unittest.TestCase):
    """Verifica que __str__ na AST reconstroi a expressao original."""

    def test_constante(self) -> None:
        self.assertEqual(str(analisar("42")), "42")

    def test_operacao_simples(self) -> None:
        self.assertEqual(str(analisar("(6 * 7)")), "(6 * 7)")

    def test_expressao_aninhada(self) -> None:
        self.assertEqual(
            str(analisar("(33 + (912 * 11))")), "(33 + (912 * 11))"
        )

    def test_normaliza_espacos(self) -> None:
        # com espacos irregulares na entrada, __str__ produz a forma canonica
        self.assertEqual(str(analisar("(  1+2 )")), "(1 + 2)")


if __name__ == "__main__":
    unittest.main(verbosity=2)
