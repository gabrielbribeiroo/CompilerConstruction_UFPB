"""Testes para o parser EC2 (precedencia e associatividade) e a integracao
com o gerador de codigo da Atividade 06.

Cobre:
    1. Estrutura da AST produzida para casos de precedencia e
       associatividade (comparacao literal com a arvore esperada).
    2. Valor avaliado (arvore.avaliar()) para os mesmos casos.
    3. Compatibilidade retroativa: programas EC1 (com parenteses em toda
       operacao) continuam sendo aceitos e avaliando para o mesmo valor.
    4. Deteccao de erros sintaticos.
    5. Equivalencia semantica entre o codigo gerado (codegen.py, reusado
       sem alteracao da Atividade 06) e o interpretador, reaproveitando
       o mesmo simulador de maquina de pilha da atividade anterior.
    6. CLI (compec2.py) via subprocess.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from ast_ec1 import Const, Op, OpBin  # noqa: E402
from codegen import gerar_codigo  # noqa: E402
from lexer import ErroLexico  # noqa: E402
from parser import ErroSintatico, analisar  # noqa: E402


# --------------------------------------------------------------------- #
# Simulador da maquina de pilha (mesma tecnica da Atividade 06): entende
# exatamente as instrucoes que codegen.py pode emitir.
# --------------------------------------------------------------------- #

_RE_MOV_IMM = re.compile(r"^mov \$(-?\d+), %rax$")


def simular(codigo: str) -> int:
    rax = 0
    rbx = 0
    pilha: list[int] = []
    for linha in codigo.split("\n"):
        instr = linha.strip()
        if not instr or instr.startswith("#"):
            continue
        m = _RE_MOV_IMM.match(instr)
        if m:
            rax = int(m.group(1))
            continue
        if instr == "push %rax":
            pilha.append(rax)
            continue
        if instr == "pop %rbx":
            rbx = pilha.pop()
            continue
        if instr == "add %rbx, %rax":
            rax = rax + rbx
            continue
        if instr == "sub %rbx, %rax":
            rax = rax - rbx
            continue
        if instr == "imul %rbx, %rax":
            rax = rax * rbx
            continue
        if instr == "cqo":
            continue
        if instr == "idiv %rbx":
            rax = int(rax / rbx)
            continue
        raise AssertionError(f"instrucao inesperada no codigo gerado: {instr!r}")
    if pilha:
        raise AssertionError(f"pilha nao foi esvaziada: {pilha!r}")
    return rax


class TestPrecedencia(unittest.TestCase):
    """A multiplicacao/divisao deve ligar mais forte que soma/subtracao."""

    def test_soma_e_multiplicacao_estrutura(self) -> None:
        # 7 + 5 * 3  ==  7 + (5 * 3), NAO (7 + 5) * 3
        esperado = OpBin(Op.SOMA, Const(7), OpBin(Op.MULT, Const(5), Const(3)))
        self.assertEqual(analisar("7 + 5 * 3"), esperado)

    def test_soma_e_multiplicacao_valor(self) -> None:
        self.assertEqual(analisar("7 + 5 * 3").avaliar(), 22)
        self.assertNotEqual(analisar("7 + 5 * 3").avaliar(), 36)

    def test_multiplicacao_antes_de_subtracao(self) -> None:
        # 20 - 4 * 3 == 20 - 12 == 8, nao (20-4)*3 == 48
        self.assertEqual(analisar("20 - 4 * 3").avaliar(), 8)

    def test_divisao_antes_de_soma(self) -> None:
        # 2 + 10 / 5 == 2 + 2 == 4, nao (2+10)/5 == 2 (truncado)
        self.assertEqual(analisar("2 + 10 / 5").avaliar(), 4)

    def test_parenteses_sobrepoe_precedencia(self) -> None:
        # (7 + 5) * 3 == 36, forcando a soma primeiro
        self.assertEqual(analisar("(7 + 5) * 3").avaliar(), 36)

    def test_expressao_mista(self) -> None:
        # 2 + 3 * 4 - 10 / 5  ==  2 + 12 - 2  ==  12
        self.assertEqual(analisar("2 + 3 * 4 - 10 / 5").avaliar(), 12)


class TestAssociatividade(unittest.TestCase):
    """Operadores de mesma precedencia devem associar a esquerda."""

    def test_subtracao_associa_a_esquerda_estrutura(self) -> None:
        # 10 - 8 - 2  ==  (10 - 8) - 2, NAO 10 - (8 - 2)
        esperado = OpBin(Op.SUB, OpBin(Op.SUB, Const(10), Const(8)), Const(2))
        self.assertEqual(analisar("10 - 8 - 2"), esperado)

    def test_subtracao_associa_a_esquerda_valor(self) -> None:
        self.assertEqual(analisar("10 - 8 - 2").avaliar(), 0)
        self.assertNotEqual(analisar("10 - 8 - 2").avaliar(), 4)

    def test_divisao_associa_a_esquerda_estrutura(self) -> None:
        # 100 / 10 / 2  ==  (100 / 10) / 2, NAO 100 / (10 / 2)
        esperado = OpBin(Op.DIV, OpBin(Op.DIV, Const(100), Const(10)), Const(2))
        self.assertEqual(analisar("100 / 10 / 2"), esperado)

    def test_divisao_associa_a_esquerda_valor(self) -> None:
        self.assertEqual(analisar("100 / 10 / 2").avaliar(), 5)
        self.assertNotEqual(analisar("100 / 10 / 2").avaliar(), 20)

    def test_soma_longa_associa_a_esquerda(self) -> None:
        # 1 + 2 + 3 + 4 == ((1 + 2) + 3) + 4
        esperado = OpBin(
            Op.SOMA,
            OpBin(Op.SOMA, OpBin(Op.SOMA, Const(1), Const(2)), Const(3)),
            Const(4),
        )
        self.assertEqual(analisar("1 + 2 + 3 + 4"), esperado)
        self.assertEqual(analisar("1 + 2 + 3 + 4").avaliar(), 10)


class TestCompatibilidadeComEC1(unittest.TestCase):
    """Programas EC1 (parenteses obrigatorios) continuam funcionando em EC2."""

    def test_constante_simples(self) -> None:
        self.assertEqual(analisar("333").avaliar(), 333)

    def test_operacao_simples_parentizada(self) -> None:
        self.assertEqual(analisar("(6 * 7)").avaliar(), 42)

    def test_exemplo_do_enunciado_da_atividade_04(self) -> None:
        self.assertEqual(analisar("(33 + (912 * 11))").avaliar(), 10065)

    def test_expressao_complexa_do_enunciado(self) -> None:
        self.assertEqual(
            analisar("((427 / 7) + (11 * (231 + 5)))").avaliar(), 2657
        )

    def test_aninhamento_profundo_ec1(self) -> None:
        self.assertEqual(analisar("(3 + (4 + (11 + 7)))").avaliar(), 25)


class TestErrosSintaticos(unittest.TestCase):
    def test_entrada_vazia(self) -> None:
        with self.assertRaises(ErroSintatico):
            analisar("")

    def test_operador_sem_operando_direito(self) -> None:
        with self.assertRaises(ErroSintatico):
            analisar("7 + * 3")

    def test_operador_sem_operando_esquerdo(self) -> None:
        with self.assertRaises(ErroSintatico):
            analisar("+ 7")

    def test_parentese_nao_fechado(self) -> None:
        with self.assertRaises(ErroSintatico):
            analisar("(7 + 5")

    def test_parentese_fechando_inesperado(self) -> None:
        with self.assertRaises(ErroSintatico):
            analisar(")")

    def test_lixo_apos_expressao_raiz(self) -> None:
        with self.assertRaises(ErroSintatico):
            analisar("7 + 5 42")

    def test_erro_lexico_caractere_invalido(self) -> None:
        with self.assertRaises(ErroLexico):
            analisar("7 + x")


class TestEquivalenciaSemantica(unittest.TestCase):
    """O codigo gerado (codegen.py, reusado da Atividade 06 sem alteracao)
    precisa produzir o mesmo valor que o interpretador para qualquer
    programa EC2, incluindo os casos de precedencia/associatividade."""

    PROGRAMAS = [
        "7 + 5 * 3",
        "20 - 4 * 3",
        "2 + 10 / 5",
        "(7 + 5) * 3",
        "2 + 3 * 4 - 10 / 5",
        "10 - 8 - 2",
        "100 / 10 / 2",
        "1 + 2 + 3 + 4",
        "333",
        "(6 * 7)",
        "(33 + (912 * 11))",
        "((427 / 7) + (11 * (231 + 5)))",
        "2 * 3 + 4 * 5 - 6 / 2",
    ]

    def test_codigo_gerado_bate_com_interpretador(self) -> None:
        for fonte in self.PROGRAMAS:
            with self.subTest(programa=fonte):
                arvore = analisar(fonte)
                esperado = arvore.avaliar()
                obtido = simular(gerar_codigo(arvore))
                self.assertEqual(obtido, esperado)


class TestCLI(unittest.TestCase):
    """Invoca compec2.py como subprocesso."""

    @classmethod
    def _exec_compilador(cls, arquivo_entrada: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, "compec2.py", arquivo_entrada],
            cwd=RAIZ,
            capture_output=True,
            text=True,
        )

    def test_compila_expressao_sem_parenteses(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            entrada = os.path.join(tmp, "p.ec2")
            with open(entrada, "w", encoding="utf-8") as f:
                f.write("7 + 5 * 3\n")
            res = self._exec_compilador(entrada)
            self.assertEqual(res.returncode, 0, msg=res.stderr)
            saida = os.path.join(tmp, "p.s")
            self.assertTrue(os.path.isfile(saida))
            with open(saida, "r", encoding="utf-8") as f:
                conteudo = f.read()
            self.assertIn("_start:", conteudo)
            self.assertIn("imul %rbx, %rax", conteudo)
            self.assertIn("add %rbx, %rax", conteudo)

    def test_entrada_invalida_falha_e_nao_gera_s(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            entrada = os.path.join(tmp, "ruim.ec2")
            with open(entrada, "w", encoding="utf-8") as f:
                f.write("7 + * 3\n")
            res = self._exec_compilador(entrada)
            self.assertEqual(res.returncode, 1)
            self.assertIn("Erro sintatico", res.stderr)
            self.assertFalse(os.path.isfile(os.path.join(tmp, "ruim.s")))


if __name__ == "__main__":
    unittest.main(verbosity=2)
