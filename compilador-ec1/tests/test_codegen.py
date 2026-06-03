"""Testes para o gerador de codigo x86-64 da Atividade 06.

Os testes cobrem:
    1. Estrutura literal das instrucoes geradas para cada tipo de no.
    2. Programa completo (com o modelo de saida em volta).
    3. Equivalencia semantica: simulamos em Python a maquina de pilha que o
       codigo gerado executaria, e comparamos com o avaliar() do
       interpretador da Atividade 05. Se os dois batem para uma bateria
       grande de programas, o codigo gerado e semanticamente correto, mesmo
       sem montar e rodar o .s aqui.
    4. CLI: invocar compec1.py gera o .s correto ao lado da entrada.
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
from codegen import gerar_codigo, gerar_programa  # noqa: E402
from parser import analisar  # noqa: E402


# --------------------------------------------------------------------- #
# Simulador da maquina de pilha
# --------------------------------------------------------------------- #
# So precisa entender as instrucoes que o nosso codegen pode emitir.
# Esto é o que verifica semantica sem precisar montar e linkar.

_RE_MOV_IMM = re.compile(r"^mov \$(-?\d+), %rax$")


def simular(codigo: str) -> int:
    """Executa o `codigo` em uma maquina de pilha minimalista e devolve %rax."""
    rax = 0
    rbx = 0
    rdx = 0
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
            # sign-extend rax em rdx; simulamos so o necessario p/ idiv
            rdx = -1 if rax < 0 else 0
            continue
        if instr == "idiv %rbx":
            # rdx:rax / rbx, com truncamento para zero (semantica x86-64)
            # como rdx so e usado depois de cqo, basta usar rax
            _ = rdx  # silencia "nao usado"
            rax = int(rax / rbx)
            continue
        raise AssertionError(f"instrucao inesperada no codigo gerado: {instr!r}")
    if pilha:
        raise AssertionError(f"pilha nao foi esvaziada: {pilha!r}")
    return rax


# --------------------------------------------------------------------- #


class TestCodigoDeConstantes(unittest.TestCase):
    def test_constante_simples(self) -> None:
        self.assertEqual(gerar_codigo(Const(42)), "mov $42, %rax")

    def test_constante_zero(self) -> None:
        self.assertEqual(gerar_codigo(Const(0)), "mov $0, %rax")

    def test_constante_grande(self) -> None:
        self.assertEqual(gerar_codigo(Const(123456789)), "mov $123456789, %rax")


class TestCodigoDeOperacoes(unittest.TestCase):
    """Verifica a estrutura literal do codigo para cada operador."""

    def test_soma(self) -> None:
        codigo = gerar_codigo(OpBin(Op.SOMA, Const(7), Const(11)))
        esperado = (
            "mov $11, %rax\n"
            "push %rax\n"
            "mov $7, %rax\n"
            "pop %rbx\n"
            "add %rbx, %rax"
        )
        self.assertEqual(codigo, esperado)

    def test_subtracao(self) -> None:
        # (11 - 7): esq=11, dir=7
        # esquema invertido: dir primeiro, depois esq
        codigo = gerar_codigo(OpBin(Op.SUB, Const(11), Const(7)))
        esperado = (
            "mov $7, %rax\n"
            "push %rax\n"
            "mov $11, %rax\n"
            "pop %rbx\n"
            "sub %rbx, %rax"
        )
        self.assertEqual(codigo, esperado)

    def test_multiplicacao(self) -> None:
        codigo = gerar_codigo(OpBin(Op.MULT, Const(6), Const(7)))
        esperado = (
            "mov $7, %rax\n"
            "push %rax\n"
            "mov $6, %rax\n"
            "pop %rbx\n"
            "imul %rbx, %rax"
        )
        self.assertEqual(codigo, esperado)

    def test_divisao(self) -> None:
        codigo = gerar_codigo(OpBin(Op.DIV, Const(20), Const(4)))
        esperado = (
            "mov $4, %rax\n"
            "push %rax\n"
            "mov $20, %rax\n"
            "pop %rbx\n"
            "cqo\n"
            "idiv %rbx"
        )
        self.assertEqual(codigo, esperado)


class TestAninhamento(unittest.TestCase):
    def test_aninhamento_a_direita(self) -> None:
        # (7 + (3 + 8))
        arvore = analisar("(7 + (3 + 8))")
        codigo = gerar_codigo(arvore)
        # propriedade: pilha sempre fica balanceada
        self.assertEqual(codigo.count("push %rax"), codigo.count("pop %rbx"))
        # e o codigo simulado deve dar 18
        self.assertEqual(simular(codigo), 18)


class TestEquivalenciaSemantica(unittest.TestCase):
    """Para varios programas, o resultado do codigo gerado deve ser igual ao
    do interpretador da Atividade 05."""

    PROGRAMAS = [
        "0",
        "42",
        "333",
        "(6 * 7)",
        "(7 + 11)",
        "(11 - 7)",
        "(20 / 4)",
        "(7 + (3 + 8))",
        "(33 + (912 * 11))",
        "((427 / 7) + (11 * (231 + 5)))",
        "(3 + (4 + (11 + 7)))",
        # operadores nao-comutativos aninhados
        "((100 - 30) - 5)",
        "(100 - (30 - 5))",
        "((1000 / 10) / 2)",
        "(1000 / (10 / 2))",
        "((8 * 7) - (3 + 4))",
    ]

    def test_resultado_bate_com_interpretador(self) -> None:
        for fonte in self.PROGRAMAS:
            with self.subTest(programa=fonte):
                arvore = analisar(fonte)
                esperado = arvore.avaliar()
                obtido = simular(gerar_codigo(arvore))
                self.assertEqual(obtido, esperado)

    def test_pilha_balanceada(self) -> None:
        for fonte in self.PROGRAMAS:
            with self.subTest(programa=fonte):
                codigo = gerar_codigo(analisar(fonte))
                self.assertEqual(
                    codigo.count("push %rax"),
                    codigo.count("pop %rbx"),
                    f"pilha desbalanceada para {fonte!r}",
                )


class TestProgramaCompleto(unittest.TestCase):
    """Verifica que `gerar_programa` envolve o codigo no template correto."""

    def test_template_basico(self) -> None:
        prog = gerar_programa(Const(42))
        # cabecalho e .text
        self.assertIn(".section .text", prog)
        self.assertIn(".globl _start", prog)
        self.assertIn("_start:", prog)
        # corpo
        self.assertIn("mov $42, %rax", prog)
        # rodape: chamadas finais e include
        self.assertIn("call imprime_num", prog)
        self.assertIn("call sair", prog)
        self.assertIn('.include "runtime.s"', prog)

    def test_ordem_no_template(self) -> None:
        prog = gerar_programa(Const(42))
        idx_start = prog.index("_start:")
        idx_mov = prog.index("mov $42, %rax")
        idx_imprime = prog.index("call imprime_num")
        idx_sair = prog.index("call sair")
        idx_include = prog.index(".include")
        # ordem esperada
        self.assertLess(idx_start, idx_mov)
        self.assertLess(idx_mov, idx_imprime)
        self.assertLess(idx_imprime, idx_sair)
        self.assertLess(idx_sair, idx_include)


class TestCLI(unittest.TestCase):
    """Invoca o compec1.py como subprocesso e verifica o arquivo gerado."""

    @classmethod
    def _exec_compilador(cls, arquivo_entrada: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, "compec1.py", arquivo_entrada],
            cwd=RAIZ,
            capture_output=True,
            text=True,
        )

    def test_compila_entrada_valida_e_grava_s(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            entrada = os.path.join(tmp, "p.ec1")
            with open(entrada, "w", encoding="utf-8") as f:
                f.write("(6 * 7)\n")
            res = self._exec_compilador(entrada)
            self.assertEqual(res.returncode, 0, msg=res.stderr)
            saida = os.path.join(tmp, "p.s")
            self.assertTrue(os.path.isfile(saida))
            with open(saida, "r", encoding="utf-8") as f:
                conteudo = f.read()
            # ja temos testes de unidade verificando esse formato; aqui so
            # checamos que e o programa completo
            self.assertIn("_start:", conteudo)
            self.assertIn("mov $7, %rax", conteudo)
            self.assertIn("imul %rbx, %rax", conteudo)
            self.assertIn("call sair", conteudo)

    def test_entrada_invalida_falha_e_nao_gera_s(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            entrada = os.path.join(tmp, "ruim.ec1")
            with open(entrada, "w", encoding="utf-8") as f:
                f.write("(3 3 4)\n")
            res = self._exec_compilador(entrada)
            self.assertEqual(res.returncode, 1)
            self.assertIn("Erro sintatico", res.stderr)
            self.assertFalse(os.path.isfile(os.path.join(tmp, "ruim.s")))

    def test_arquivo_inexistente(self) -> None:
        res = self._exec_compilador("/caminho/que/nao/existe.ec1")
        self.assertEqual(res.returncode, 1)
        self.assertIn("nao encontrado", res.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
