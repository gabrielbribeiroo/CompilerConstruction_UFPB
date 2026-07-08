"""Testes para o compilador EV: lexer, parser, analise semantica e codegen.

Organizado em classes por etapa do compilador, seguindo o mesmo padrao
das atividades anteriores:
    - TestLexico: tokens novos (IDENT, IGUAL, PONTO_VIRGULA) e o erro
      lexico de digito seguido de letra.
    - TestParser: estrutura da AST (Programa/Decl/Var) para programas
      com zero, uma e varias declaracoes.
    - TestErrosSintaticos: entradas mal formadas.
    - TestSemantica: os dois erros do exemplo do enunciado (uso antes da
      propria declaracao, uso de variavel nunca declarada), e programas
      validos passando sem erro.
    - TestInterpretacao: avaliar(env) via Programa.avaliar() para os
      exemplos do enunciado.
    - TestEquivalenciaSemantica: simulador da maquina de pilha (com
      memoria para variaveis) comparado a avaliar() do interpretador.
    - TestCLI: compev.py via subprocess.
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

from ast_ev import Const, Decl, Op, OpBin, Programa, Var  # noqa: E402
from codegen import gerar_programa  # noqa: E402
from lexer import AnalisadorLexico, ErroLexico, TipoToken  # noqa: E402
from parser import ErroSintatico, analisar  # noqa: E402
from semantica import ErroSemantico, verifica_programa  # noqa: E402


class TestLexico(unittest.TestCase):
    def test_identificador_simples(self) -> None:
        toks = AnalisadorLexico("x").tokenizar()
        self.assertEqual(len(toks), 1)
        self.assertEqual(toks[0].tipo, TipoToken.IDENT)
        self.assertEqual(toks[0].lexema, "x")

    def test_identificador_com_letras_e_digitos(self) -> None:
        toks = AnalisadorLexico("valor2x").tokenizar()
        self.assertEqual(len(toks), 1)
        self.assertEqual(toks[0].tipo, TipoToken.IDENT)
        self.assertEqual(toks[0].lexema, "valor2x")

    def test_igual_e_ponto_virgula(self) -> None:
        toks = AnalisadorLexico("x = 1;").tokenizar()
        tipos = [t.tipo for t in toks]
        self.assertEqual(
            tipos,
            [
                TipoToken.IDENT,
                TipoToken.IGUAL,
                TipoToken.NUMERO,
                TipoToken.PONTO_VIRGULA,
            ],
        )

    def test_erro_lexico_digito_seguido_de_letra(self) -> None:
        # "237axy" -- digitos seguidos de letra sem separador, exemplo
        # citado explicitamente no enunciado (secao 3) como erro lexico
        with self.assertRaises(ErroLexico):
            AnalisadorLexico("237axy").tokenizar()

    def test_numero_seguido_de_espaco_e_identificador_ok(self) -> None:
        # com espaco entre eles, sao dois tokens validos
        toks = AnalisadorLexico("237 axy").tokenizar()
        self.assertEqual([t.tipo for t in toks], [TipoToken.NUMERO, TipoToken.IDENT])


class TestParser(unittest.TestCase):
    def test_programa_sem_declaracoes(self) -> None:
        prog = analisar("= 6 * 7")
        self.assertEqual(prog.declaracoes, ())
        self.assertEqual(prog.exp_final, OpBin(Op.MULT, Const(6), Const(7)))

    def test_programa_uma_declaracao(self) -> None:
        prog = analisar("x = 10;\n= x")
        self.assertEqual(prog.declaracoes, (Decl("x", Const(10)),))
        self.assertEqual(prog.exp_final, Var("x"))

    def test_programa_varias_declaracoes(self) -> None:
        prog = analisar("l = 30;\nc = 40;\n= l + l + c + c")
        self.assertEqual(
            prog.declaracoes,
            (Decl("l", Const(30)), Decl("c", Const(40))),
        )
        esperado_exp = OpBin(
            Op.SOMA,
            OpBin(Op.SOMA, OpBin(Op.SOMA, Var("l"), Var("l")), Var("c")),
            Var("c"),
        )
        self.assertEqual(prog.exp_final, esperado_exp)

    def test_variavel_em_expressao_composta(self) -> None:
        prog = analisar("x = 5;\n= (x + 1) * 2")
        esperado = OpBin(Op.MULT, OpBin(Op.SOMA, Var("x"), Const(1)), Const(2))
        self.assertEqual(prog.exp_final, esperado)


class TestErrosSintaticos(unittest.TestCase):
    def test_entrada_vazia(self) -> None:
        with self.assertRaises(ErroSintatico):
            analisar("")

    def test_declaracao_sem_ponto_virgula(self) -> None:
        with self.assertRaises(ErroSintatico):
            analisar("x = 10\n= x")

    def test_programa_sem_expressao_final(self) -> None:
        with self.assertRaises(ErroSintatico):
            analisar("x = 10;")

    def test_declaracao_sem_sinal_de_igual(self) -> None:
        with self.assertRaises(ErroSintatico):
            analisar("x 10;\n= x")

    def test_lixo_apos_expressao_final(self) -> None:
        with self.assertRaises(ErroSintatico):
            analisar("= 1 + 2 3")


class TestSemantica(unittest.TestCase):
    def test_programa_valido_sem_erro(self) -> None:
        prog = analisar("x = 7 * 8;\ny = x * 11 - 17;\n= x * y + 33")
        verifica_programa(prog)  # nao deve levantar

    def test_uso_de_variavel_antes_da_propria_declaracao(self) -> None:
        # x = 7 + y;  -- y ainda nao foi declarada nesse ponto
        prog = analisar("x = 7 + y;\ny = x * 11;\n= x * y + z")
        with self.assertRaises(ErroSemantico) as ctx:
            verifica_programa(prog)
        self.assertEqual(ctx.exception.nome, "y")

    def test_variavel_nao_declarada_na_expressao_final(self) -> None:
        prog = analisar("x = 7 * 8;\n= x + w")
        with self.assertRaises(ErroSemantico) as ctx:
            verifica_programa(prog)
        self.assertEqual(ctx.exception.nome, "w")

    def test_variavel_pode_ser_usada_apos_declarada(self) -> None:
        prog = analisar("x = 1;\ny = x + 1;\n= y")
        tabela = verifica_programa(prog)
        self.assertTrue(tabela.esta_declarada("x"))
        self.assertTrue(tabela.esta_declarada("y"))

    def test_reatribuicao_nao_causa_erro(self) -> None:
        prog = analisar("x = 10;\nx = x + 5;\n= x")
        verifica_programa(prog)  # nao deve levantar


class TestInterpretacao(unittest.TestCase):
    def test_exemplo_perimetro_do_enunciado(self) -> None:
        prog = analisar("l = 30;\nc = 40;\n= l + l + c + c")
        self.assertEqual(prog.avaliar(), 140)

    def test_exemplo_completo_do_enunciado(self) -> None:
        # x = (7+4)*12 = 132; y = 132*3+11 = 407
        # resultado = 132*407 + 132*11 + 407*13 = 60467
        fonte = (
            "x = (7 + 4) * 12;\n"
            "y = x * 3 + 11;\n"
            "= (x * y) + (x * 11) + (y * 13)"
        )
        prog = analisar(fonte)
        self.assertEqual(prog.avaliar(), 60467)

    def test_sem_declaracoes(self) -> None:
        self.assertEqual(analisar("= 6 * 7").avaliar(), 42)

    def test_reatribuicao(self) -> None:
        self.assertEqual(analisar("x = 10;\nx = x + 5;\n= x").avaliar(), 15)


# --------------------------------------------------------------------- #
# Simulador da maquina de pilha, estendido com memoria para variaveis
# --------------------------------------------------------------------- #

_RE_MOV_IMM = re.compile(r"^mov \$(-?\d+), %rax$")
_RE_MOV_STORE = re.compile(r"^mov %rax, (\w+)$")
_RE_MOV_LOAD = re.compile(r"^mov (\w+), %rax$")


def simular(codigo: str) -> int:
    """Executa `codigo` (o corpo do .s, sem o template) e devolve o valor
    final de %rax. Entende exatamente as instrucoes que codegen.py pode
    emitir para EV: mov imediato, mov de/para variavel, push/pop,
    add/sub/imul, cqo/idiv."""
    rax = 0
    rbx = 0
    pilha: list[int] = []
    mem: dict[str, int] = {}
    for linha in codigo.split("\n"):
        instr = linha.strip()
        if not instr or instr.startswith("#"):
            continue
        m = _RE_MOV_IMM.match(instr)
        if m:
            rax = int(m.group(1))
            continue
        m = _RE_MOV_STORE.match(instr)
        if m:
            mem[m.group(1)] = rax
            continue
        m = _RE_MOV_LOAD.match(instr)
        if m:
            rax = mem[m.group(1)]
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


def _extrai_corpo(assembly: str) -> str:
    """Extrai apenas as linhas entre `_start:` e `call imprime_num`."""
    linhas = assembly.split("\n")
    inicio = linhas.index("_start:") + 1
    fim = next(i for i, l in enumerate(linhas) if l.strip() == "call imprime_num")
    return "\n".join(linhas[inicio:fim])


class TestEquivalenciaSemantica(unittest.TestCase):
    """O codigo gerado deve produzir o mesmo valor que Programa.avaliar()."""

    PROGRAMAS = [
        "= 6 * 7",
        "l = 30;\nc = 40;\n= l + l + c + c",
        "x = (7 + 4) * 12;\ny = x * 3 + 11;\n= (x * y) + (x * 11) + (y * 13)",
        "x = 7 * 8;\ny = x * 11 - 17;\n= x * y + 33",
        "x = 10;\nx = x + 5;\n= x",
        "a = 100;\nb = a / 10;\nc = b / 2;\n= c",
    ]

    def test_codigo_gerado_bate_com_interpretador(self) -> None:
        for fonte in self.PROGRAMAS:
            with self.subTest(programa=fonte):
                prog = analisar(fonte)
                verifica_programa(prog)
                esperado = prog.avaliar()
                assembly = gerar_programa(prog)
                obtido = simular(_extrai_corpo(assembly))
                self.assertEqual(obtido, esperado)


class TestCodegen(unittest.TestCase):
    def test_secao_bss_tem_uma_entrada_por_variavel(self) -> None:
        prog = analisar("x = 1;\ny = 2;\n= x + y")
        assembly = gerar_programa(prog)
        self.assertIn(".lcomm x, 8", assembly)
        self.assertIn(".lcomm y, 8", assembly)

    def test_variavel_reatribuida_nao_duplica_lcomm(self) -> None:
        prog = analisar("x = 10;\nx = x + 5;\n= x")
        assembly = gerar_programa(prog)
        self.assertEqual(assembly.count(".lcomm x, 8"), 1)

    def test_sem_variaveis_secao_bss_fica_vazia(self) -> None:
        prog = analisar("= 6 * 7")
        assembly = gerar_programa(prog)
        self.assertIn(".section .bss", assembly)
        self.assertNotIn(".lcomm", assembly)

    def test_modelo_completo(self) -> None:
        prog = analisar("x = 1;\n= x")
        assembly = gerar_programa(prog)
        self.assertIn(".section .bss", assembly)
        self.assertIn(".section .text", assembly)
        self.assertIn(".globl _start", assembly)
        self.assertIn("_start:", assembly)
        self.assertIn("call imprime_num", assembly)
        self.assertIn("call sair", assembly)
        self.assertIn('.include "runtime.s"', assembly)
        self.assertIn("mov %rax, x", assembly)
        self.assertIn("mov x, %rax", assembly)


class TestCLI(unittest.TestCase):
    """Invoca compev.py como subprocesso."""

    @classmethod
    def _exec_compilador(cls, arquivo_entrada: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, "compev.py", arquivo_entrada],
            cwd=RAIZ,
            capture_output=True,
            text=True,
        )

    def test_compila_programa_com_variaveis(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            entrada = os.path.join(tmp, "p.ev")
            with open(entrada, "w", encoding="utf-8") as f:
                f.write("l = 30;\nc = 40;\n= l + l + c + c\n")
            res = self._exec_compilador(entrada)
            self.assertEqual(res.returncode, 0, msg=res.stderr)
            saida = os.path.join(tmp, "p.s")
            self.assertTrue(os.path.isfile(saida))
            with open(saida, "r", encoding="utf-8") as f:
                conteudo = f.read()
            self.assertIn(".lcomm l, 8", conteudo)
            self.assertIn(".lcomm c, 8", conteudo)

    def test_erro_semantico_falha_e_nao_gera_s(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            entrada = os.path.join(tmp, "ruim.ev")
            with open(entrada, "w", encoding="utf-8") as f:
                f.write("x = 7 * 8;\n= x + w\n")
            res = self._exec_compilador(entrada)
            self.assertEqual(res.returncode, 1)
            self.assertIn("Erro semantico", res.stderr)
            self.assertIn("w", res.stderr)
            self.assertFalse(os.path.isfile(os.path.join(tmp, "ruim.s")))

    def test_erro_sintatico_falha_e_nao_gera_s(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            entrada = os.path.join(tmp, "ruim.ev")
            with open(entrada, "w", encoding="utf-8") as f:
                f.write("x = 10\n= x\n")
            res = self._exec_compilador(entrada)
            self.assertEqual(res.returncode, 1)
            self.assertIn("Erro sintatico", res.stderr)
            self.assertFalse(os.path.isfile(os.path.join(tmp, "ruim.s")))

    def test_erro_lexico_falha_e_nao_gera_s(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            entrada = os.path.join(tmp, "ruim.ev")
            with open(entrada, "w", encoding="utf-8") as f:
                f.write("= 237axy\n")
            res = self._exec_compilador(entrada)
            self.assertEqual(res.returncode, 1)
            self.assertIn("Erro lexico", res.stderr)
            self.assertFalse(os.path.isfile(os.path.join(tmp, "ruim.s")))


if __name__ == "__main__":
    unittest.main(verbosity=2)
