"""Testes para o compilador Cmd: lexer, parser, semantica, interpretacao
e equivalencia semantica do codegen (incluindo if/while com rotulos).

Organizado em classes por etapa do compilador, seguindo o padrao das
atividades anteriores:
    - TestLexico: tokens novos ({, }, <, >, ==, palavras-chave).
    - TestParser: estrutura da AST (Programa/If/While/Atrib).
    - TestErrosSintaticos: entradas mal formadas.
    - TestSemantica: atribuicao a variavel nao declarada (lado esquerdo
      e lado direito, inclusive dentro de if/while), casos validos.
    - TestInterpretacao: Programa.avaliar() para os 4 exemplos do
      enunciado (discriminante, soma, resto, mdc).
    - TestEquivalenciaSemantica: simulador de maquina de pilha com
      memoria, comparacoes e rotulos/desvios, comparado com avaliar().
    - TestCLI: compcmd.py via subprocess.
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

from ast_cmd import Atrib, Const, If, Op, OpBin, Var, While  # noqa: E402
from codegen import gerar_programa  # noqa: E402
from lexer import AnalisadorLexico, ErroLexico, TipoToken  # noqa: E402
from parser import ErroSintatico, analisar  # noqa: E402
from semantica import ErroSemantico, verifica_programa  # noqa: E402


class TestLexico(unittest.TestCase):
    def test_chaves(self) -> None:
        toks = AnalisadorLexico("{ }").tokenizar()
        self.assertEqual([t.tipo for t in toks], [TipoToken.CHAVE_ESQ, TipoToken.CHAVE_DIR])

    def test_menor_maior(self) -> None:
        toks = AnalisadorLexico("a < b > c").tokenizar()
        tipos = [t.tipo for t in toks]
        self.assertEqual(
            tipos,
            [
                TipoToken.IDENT, TipoToken.MENOR, TipoToken.IDENT,
                TipoToken.MAIOR, TipoToken.IDENT,
            ],
        )

    def test_igual_igual_vs_igual(self) -> None:
        toks = AnalisadorLexico("a == b\nc = d").tokenizar()
        tipos = [t.tipo for t in toks]
        self.assertEqual(
            tipos,
            [
                TipoToken.IDENT, TipoToken.IGUAL_IGUAL, TipoToken.IDENT,
                TipoToken.IDENT, TipoToken.IGUAL, TipoToken.IDENT,
            ],
        )

    def test_palavras_chave_reconhecidas(self) -> None:
        toks = AnalisadorLexico("if else while return").tokenizar()
        self.assertEqual(
            [t.tipo for t in toks],
            [
                TipoToken.PALAVRA_IF, TipoToken.PALAVRA_ELSE,
                TipoToken.PALAVRA_WHILE, TipoToken.PALAVRA_RETURN,
            ],
        )

    def test_identificador_com_prefixo_de_palavra_chave(self) -> None:
        # "ifx" nao e a palavra-chave "if" -- deve ser um IDENT comum
        toks = AnalisadorLexico("ifx").tokenizar()
        self.assertEqual(len(toks), 1)
        self.assertEqual(toks[0].tipo, TipoToken.IDENT)
        self.assertEqual(toks[0].lexema, "ifx")

    def test_erro_lexico_digito_seguido_de_letra(self) -> None:
        with self.assertRaises(ErroLexico):
            AnalisadorLexico("237axy").tokenizar()


class TestParser(unittest.TestCase):
    def test_programa_minimo(self) -> None:
        prog = analisar("{ return 7 * 6; }")
        self.assertEqual(prog.declaracoes, ())
        self.assertEqual(prog.comandos, ())
        self.assertEqual(prog.exp_final, OpBin(Op.MULT, Const(7), Const(6)))

    def test_atribuicao_simples(self) -> None:
        prog = analisar("x = 1;\n{ x = x + 1;\n return x; }")
        self.assertEqual(len(prog.comandos), 1)
        cmd = prog.comandos[0]
        self.assertIsInstance(cmd, Atrib)
        self.assertEqual(cmd.nome, "x")
        self.assertEqual(cmd.exp, OpBin(Op.SOMA, Var("x"), Const(1)))

    def test_if_com_else(self) -> None:
        fonte = "x = 1;\n{ if x < 10 { x = 1; } else { x = 2; }\n return x; }"
        prog = analisar(fonte)
        self.assertEqual(len(prog.comandos), 1)
        cmd = prog.comandos[0]
        self.assertIsInstance(cmd, If)
        self.assertEqual(cmd.cond, OpBin(Op.MENOR, Var("x"), Const(10)))
        self.assertEqual(len(cmd.cmds_then), 1)
        self.assertEqual(len(cmd.cmds_else), 1)

    def test_if_com_bloco_else_vazio(self) -> None:
        prog = analisar("x = 1;\n{ if x < 10 { x = 1; } else { }\n return x; }")
        cmd = prog.comandos[0]
        self.assertEqual(cmd.cmds_else, ())

    def test_while(self) -> None:
        prog = analisar("n = 0;\n{ while n < 10 { n = n + 1; }\n return n; }")
        cmd = prog.comandos[0]
        self.assertIsInstance(cmd, While)
        self.assertEqual(cmd.cond, OpBin(Op.MENOR, Var("n"), Const(10)))
        self.assertEqual(len(cmd.cmds), 1)

    def test_comparacao_tem_precedencia_mais_baixa(self) -> None:
        # 1 + 2 < 3 * 4  ==  (1+2) < (3*4)
        prog = analisar("{ return 1 + 2 < 3 * 4; }")
        esperado = OpBin(
            Op.MENOR,
            OpBin(Op.SOMA, Const(1), Const(2)),
            OpBin(Op.MULT, Const(3), Const(4)),
        )
        self.assertEqual(prog.exp_final, esperado)


class TestErrosSintaticos(unittest.TestCase):
    def test_entrada_vazia(self) -> None:
        with self.assertRaises(ErroSintatico):
            analisar("")

    def test_if_sem_else(self) -> None:
        with self.assertRaises(ErroSintatico):
            analisar("x = 1;\n{ if x < 10 { x = 1; }\n return x; }")

    def test_bloco_sem_chaves(self) -> None:
        with self.assertRaises(ErroSintatico):
            analisar("return 1;")

    def test_atribuicao_sem_ponto_virgula(self) -> None:
        with self.assertRaises(ErroSintatico):
            analisar("x = 1;\n{ x = 2\n return x; }")

    def test_programa_sem_return(self) -> None:
        with self.assertRaises(ErroSintatico):
            analisar("x = 1;\n{ x = 2; }")


class TestSemantica(unittest.TestCase):
    def test_programa_valido_sem_erro(self) -> None:
        fonte = (
            "a = 1;\nb = 2;\nc = 3;\ndelta = b * b - 4 * a * c;\n"
            "{ if delta < 0 { delta = 0 - delta; } else { delta = delta; }\n"
            "return delta; }"
        )
        verifica_programa(analisar(fonte))  # nao deve levantar

    def test_atribuicao_lado_esquerdo_nao_declarado(self) -> None:
        prog = analisar("x = 10;\n{ y = 5;\n return x + y; }")
        with self.assertRaises(ErroSemantico) as ctx:
            verifica_programa(prog)
        self.assertEqual(ctx.exception.nome, "y")

    def test_atribuicao_lado_direito_nao_declarado(self) -> None:
        fonte = "x = 10;\n{ if x < 100 { x = x + w; } else { x = x; }\n return x; }"
        prog = analisar(fonte)
        with self.assertRaises(ErroSemantico) as ctx:
            verifica_programa(prog)
        self.assertEqual(ctx.exception.nome, "w")

    def test_variavel_nao_declarada_dentro_de_while(self) -> None:
        prog = analisar("x = 0;\n{ while x < 10 { x = x + k; }\n return x; }")
        with self.assertRaises(ErroSemantico) as ctx:
            verifica_programa(prog)
        self.assertEqual(ctx.exception.nome, "k")

    def test_atribuicao_nao_insere_na_tabela(self) -> None:
        # atribuir a uma variavel ja declarada nao insere nada de novo
        # -- mas usar uma nao declarada continua sendo erro mesmo
        # depois de "atribuida" incorretamente uma vez
        prog = analisar("x = 1;\n{ x = 2;\n return x; }")
        tabela = verifica_programa(prog)
        self.assertTrue(tabela.esta_declarada("x"))


class TestInterpretacao(unittest.TestCase):
    def test_discriminante_do_enunciado(self) -> None:
        # delta = b*b - 4*a*c = 4 - 12 = -8; abs = 8
        fonte = (
            "a = 1;\nb = 2;\nc = 3;\ndelta = b * b - 4 * a * c;\n"
            "{ if delta < 0 { delta = 0 - delta; } else { delta = delta; }\n"
            "return delta; }"
        )
        self.assertEqual(analisar(fonte).avaliar(), 8)

    def test_soma_do_enunciado(self) -> None:
        # soma de 1 a 9 = 45
        fonte = (
            "n = 1;\nm = 10;\nsoma = 0;\n"
            "{ while n < m { soma = soma + n;\n n = n + 1; }\n return soma; }"
        )
        self.assertEqual(analisar(fonte).avaliar(), 45)

    def test_resto_da_divisao(self) -> None:
        fonte = "m = 10;\nn = 4;\n{ while m + 1 > n { m = m - n; }\n return m; }"
        self.assertEqual(analisar(fonte).avaliar(), 2)

    def test_mdc(self) -> None:
        fonte = (
            "a = 18;\nb = 12;\nr = 0;\n"
            "{ r = a;\n"
            "  while r+1 > b { r = r - b; }\n"
            "  while r > 0 {\n"
            "    a = b;\n b = r;\n r = a;\n"
            "    while r+1 > b { r = r - b; }\n"
            "  }\n"
            "  return b; }"
        )
        self.assertEqual(analisar(fonte).avaliar(), 6)

    def test_discriminante_positivo_nao_inverte_sinal(self) -> None:
        # b*b - 4*a*c com a=1,b=5,c=1 -> 25-4=21 (positivo, delta = delta)
        fonte = (
            "a = 1;\nb = 5;\nc = 1;\ndelta = b * b - 4 * a * c;\n"
            "{ if delta < 0 { delta = 0 - delta; } else { delta = delta; }\n"
            "return delta; }"
        )
        self.assertEqual(analisar(fonte).avaliar(), 21)


# --------------------------------------------------------------------- #
# Simulador da maquina de pilha, estendido com memoria, comparacoes e
# rotulos/desvios (jmp, jz) -- entende exatamente o que codegen.py emite.
# --------------------------------------------------------------------- #

_RE_MOV_IMM = re.compile(r"^mov \$(-?\d+), %rax$")
_RE_MOV_STORE = re.compile(r"^mov %rax, (\w+)$")
_RE_MOV_LOAD = re.compile(r"^mov (\w+), %rax$")
_RE_CMP_IMM = re.compile(r"^cmp \$(-?\d+), %rax$")
_RE_LABEL_DEF = re.compile(r"^(\w+):$")
_RE_JMP = re.compile(r"^jmp (\w+)$")
_RE_JZ = re.compile(r"^jz (\w+)$")

MAX_PASSOS = 200_000


def simular(codigo: str) -> int:
    """Executa `codigo` (o corpo do .s, sem cabecalho/rodape) e devolve o
    valor final de %rax. Suporta rotulos e desvios (jmp/jz), alem de
    mov/push/pop/aritmetica/comparacao/memoria."""
    # monta a lista de instrucoes executaveis (descarta linhas vazias e
    # comentarios) e o mapa rotulo -> indice nessa lista
    instrucoes: list[str] = []
    rotulos: dict[str, int] = {}
    for linha in codigo.split("\n"):
        instr = linha.strip()
        if not instr or instr.startswith("#"):
            continue
        m_label = _RE_LABEL_DEF.match(instr)
        if m_label:
            rotulos[m_label.group(1)] = len(instrucoes)
            continue
        instrucoes.append(instr)

    rax = rbx = rcx = 0
    ultimo_cmp = 0  # diferenca (dst - src) do cmp mais recente
    pilha: list[int] = []
    mem: dict[str, int] = {}

    pc = 0
    passos = 0
    while pc < len(instrucoes):
        passos += 1
        if passos > MAX_PASSOS:
            raise AssertionError("simulacao excedeu o limite de passos (loop infinito?)")
        instr = instrucoes[pc]

        m = _RE_MOV_IMM.match(instr)
        if m:
            rax = int(m.group(1))
            pc += 1
            continue
        m = _RE_MOV_STORE.match(instr)
        if m:
            mem[m.group(1)] = rax
            pc += 1
            continue
        m = _RE_MOV_LOAD.match(instr)
        if m:
            rax = mem[m.group(1)]
            pc += 1
            continue
        if instr == "mov %rcx, %rax":
            rax = rcx
            pc += 1
            continue
        if instr == "push %rax":
            pilha.append(rax)
            pc += 1
            continue
        if instr == "pop %rbx":
            rbx = pilha.pop()
            pc += 1
            continue
        if instr == "add %rbx, %rax":
            rax = rax + rbx
            pc += 1
            continue
        if instr == "sub %rbx, %rax":
            rax = rax - rbx
            pc += 1
            continue
        if instr == "imul %rbx, %rax":
            rax = rax * rbx
            pc += 1
            continue
        if instr == "cqo":
            pc += 1
            continue
        if instr == "idiv %rbx":
            rax = int(rax / rbx)
            pc += 1
            continue
        if instr == "xor %rcx, %rcx":
            rcx = 0
            pc += 1
            continue
        if instr == "cmp %rbx, %rax":
            ultimo_cmp = rax - rbx
            pc += 1
            continue
        m = _RE_CMP_IMM.match(instr)
        if m:
            ultimo_cmp = rax - int(m.group(1))
            pc += 1
            continue
        if instr == "setz %cl":
            rcx = 1 if ultimo_cmp == 0 else 0
            pc += 1
            continue
        if instr == "setl %cl":
            rcx = 1 if ultimo_cmp < 0 else 0
            pc += 1
            continue
        if instr == "setg %cl":
            rcx = 1 if ultimo_cmp > 0 else 0
            pc += 1
            continue
        m = _RE_JMP.match(instr)
        if m:
            pc = rotulos[m.group(1)]
            continue
        m = _RE_JZ.match(instr)
        if m:
            if ultimo_cmp == 0:
                pc = rotulos[m.group(1)]
            else:
                pc += 1
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
    """O codigo gerado deve produzir o mesmo valor que Programa.avaliar(),
    inclusive para programas com if/while (controle de fluxo real)."""

    PROGRAMAS = [
        "{ return 7 * 6; }",
        (
            "a = 1;\nb = 2;\nc = 3;\ndelta = b * b - 4 * a * c;\n"
            "{ if delta < 0 { delta = 0 - delta; } else { delta = delta; }\n"
            "return delta; }"
        ),
        (
            "a = 1;\nb = 5;\nc = 1;\ndelta = b * b - 4 * a * c;\n"
            "{ if delta < 0 { delta = 0 - delta; } else { delta = delta; }\n"
            "return delta; }"
        ),
        (
            "n = 1;\nm = 10;\nsoma = 0;\n"
            "{ while n < m { soma = soma + n;\n n = n + 1; }\n return soma; }"
        ),
        "m = 10;\nn = 4;\n{ while m + 1 > n { m = m - n; }\n return m; }",
        (
            "a = 18;\nb = 12;\nr = 0;\n"
            "{ r = a;\n"
            "  while r+1 > b { r = r - b; }\n"
            "  while r > 0 {\n"
            "    a = b;\n b = r;\n r = a;\n"
            "    while r+1 > b { r = r - b; }\n"
            "  }\n"
            "  return b; }"
        ),
        "{ return 5 == 5; }",
        "{ return 5 == 6; }",
        "{ return 3 < 3; }",
        "{ return 3 > 3; }",
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
    def test_rotulos_unicos_para_ifs_diferentes(self) -> None:
        fonte = (
            "x = 1;\n{ if x < 10 { x = 1; } else { x = 2; }\n"
            "if x < 10 { x = 3; } else { x = 4; }\n"
            "return x; }"
        )
        assembly = gerar_programa(analisar(fonte))
        self.assertIn("Lfalso0:", assembly)
        self.assertIn("Lfim0:", assembly)
        self.assertIn("Lfalso1:", assembly)
        self.assertIn("Lfim1:", assembly)

    def test_while_gera_rotulos_de_inicio_e_fim(self) -> None:
        fonte = "n = 0;\n{ while n < 10 { n = n + 1; }\n return n; }"
        assembly = gerar_programa(analisar(fonte))
        self.assertIn("Linicio0:", assembly)
        self.assertIn("Lfim0:", assembly)

    def test_modelo_completo(self) -> None:
        prog = analisar("x = 1;\n{ return x; }")
        assembly = gerar_programa(prog)
        self.assertIn(".section .bss", assembly)
        self.assertIn(".section .text", assembly)
        self.assertIn(".globl _start", assembly)
        self.assertIn("_start:", assembly)
        self.assertIn("call imprime_num", assembly)
        self.assertIn("call sair", assembly)
        self.assertIn('.include "runtime.s"', assembly)


class TestCLI(unittest.TestCase):
    """Invoca compcmd.py como subprocesso."""

    @classmethod
    def _exec_compilador(cls, arquivo_entrada: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, "compcmd.py", arquivo_entrada],
            cwd=RAIZ,
            capture_output=True,
            text=True,
        )

    def test_compila_programa_com_if_e_while(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            entrada = os.path.join(tmp, "p.cmd")
            with open(entrada, "w", encoding="utf-8") as f:
                f.write(
                    "n = 1;\nm = 10;\nsoma = 0;\n"
                    "{ while n < m { soma = soma + n;\n n = n + 1; }\n"
                    "return soma; }\n"
                )
            res = self._exec_compilador(entrada)
            self.assertEqual(res.returncode, 0, msg=res.stderr)
            saida = os.path.join(tmp, "p.s")
            self.assertTrue(os.path.isfile(saida))
            with open(saida, "r", encoding="utf-8") as f:
                conteudo = f.read()
            self.assertIn("Linicio0:", conteudo)
            self.assertIn(".lcomm soma, 8", conteudo)

    def test_erro_semantico_falha_e_nao_gera_s(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            entrada = os.path.join(tmp, "ruim.cmd")
            with open(entrada, "w", encoding="utf-8") as f:
                f.write("x = 10;\n{ y = 5;\n return x + y; }\n")
            res = self._exec_compilador(entrada)
            self.assertEqual(res.returncode, 1)
            self.assertIn("Erro semantico", res.stderr)
            self.assertIn("y", res.stderr)
            self.assertFalse(os.path.isfile(os.path.join(tmp, "ruim.s")))

    def test_erro_sintatico_falha_e_nao_gera_s(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            entrada = os.path.join(tmp, "ruim.cmd")
            with open(entrada, "w", encoding="utf-8") as f:
                f.write("x = 1;\n{ if x < 10 { x = 1; }\n return x; }\n")
            res = self._exec_compilador(entrada)
            self.assertEqual(res.returncode, 1)
            self.assertIn("Erro sintatico", res.stderr)
            self.assertFalse(os.path.isfile(os.path.join(tmp, "ruim.s")))

    def test_erro_lexico_falha_e_nao_gera_s(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            entrada = os.path.join(tmp, "ruim.cmd")
            with open(entrada, "w", encoding="utf-8") as f:
                f.write("{ return 237axy; }\n")
            res = self._exec_compilador(entrada)
            self.assertEqual(res.returncode, 1)
            self.assertIn("Erro lexico", res.stderr)
            self.assertFalse(os.path.isfile(os.path.join(tmp, "ruim.s")))


if __name__ == "__main__":
    unittest.main(verbosity=2)
