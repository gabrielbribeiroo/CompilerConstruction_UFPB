"""Testes para o compilador Fun: lexer, parser, semantica, interpretacao
e equivalencia semantica do codegen (incluindo chamadas de funcao,
recursao e acesso a variaveis locais via deslocamento de %rbp).

Organizado em classes por etapa do compilador, seguindo o padrao das
atividades anteriores:
    - TestLexico: virgula e as tres palavras-chave novas.
    - TestParser: estrutura da AST (FunDecl/VarDecl/Chamada), incluindo
      a diferenciacao Var vs. Chamada.
    - TestErrosSintaticos: entradas mal formadas.
    - TestSemantica: funcao nao declarada, numero de parametros errado,
      variavel fora de escopo, recursao direta permitida, variavel
      local escondendo global.
    - TestInterpretacao: Programa.avaliar() para os exemplos do
      enunciado (abs, fib) e os exemplos adicionais.
    - TestEquivalenciaSemantica: simulador de maquina de pilha com
      suporte a CALL/RET (pilha de retorno), memoria enderecavel por
      deslocamento de %rbp, e LEAVE -- comparado com avaliar().
    - TestCLI: compfun.py via subprocess.
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

from ast_fun import Chamada, Const, FunDecl, Op, OpBin, Var, VarDecl  # noqa: E402
from codegen import gerar_programa  # noqa: E402
from lexer import AnalisadorLexico, ErroLexico, TipoToken  # noqa: E402
from parser import ErroSintatico, analisar  # noqa: E402
from semantica import ErroSemantico, verifica_programa  # noqa: E402


class TestLexico(unittest.TestCase):
    def test_virgula(self) -> None:
        toks = AnalisadorLexico("a, b, c").tokenizar()
        self.assertEqual(
            [t.tipo for t in toks],
            [
                TipoToken.IDENT, TipoToken.VIRGULA, TipoToken.IDENT,
                TipoToken.VIRGULA, TipoToken.IDENT,
            ],
        )

    def test_palavras_chave_novas(self) -> None:
        toks = AnalisadorLexico("fun var main").tokenizar()
        self.assertEqual(
            [t.tipo for t in toks],
            [TipoToken.PALAVRA_FUN, TipoToken.PALAVRA_VAR, TipoToken.PALAVRA_MAIN],
        )

    def test_identificador_parecido_com_palavra_chave(self) -> None:
        toks = AnalisadorLexico("funcao variavel mainframe").tokenizar()
        self.assertEqual([t.tipo for t in toks], [TipoToken.IDENT] * 3)


class TestParser(unittest.TestCase):
    def test_programa_so_com_main(self) -> None:
        prog = analisar("main { return 7 * 6; }")
        self.assertEqual(prog.declaracoes, ())
        self.assertEqual(prog.exp_final, OpBin(Op.MULT, Const(7), Const(6)))

    def test_fundecl_sem_parametros(self) -> None:
        prog = analisar("fun f() { return 1; }\nmain { return f(); }")
        fundecl = prog.declaracoes[0]
        self.assertIsInstance(fundecl, FunDecl)
        self.assertEqual(fundecl.nome, "f")
        self.assertEqual(fundecl.params, ())

    def test_fundecl_com_parametros(self) -> None:
        prog = analisar("fun soma(a, b) { return a + b; }\nmain { return soma(1, 2); }")
        fundecl = prog.declaracoes[0]
        self.assertEqual(fundecl.params, ("a", "b"))

    def test_fundecl_com_vardecl_local(self) -> None:
        fonte = "fun f(x) { var y = x + 1;\n return y; }\nmain { return f(1); }"
        prog = analisar(fonte)
        fundecl = prog.declaracoes[0]
        self.assertEqual(fundecl.vardecls, (VarDecl("y", OpBin(Op.SOMA, Var("x"), Const(1))),))

    def test_vardecl_global(self) -> None:
        prog = analisar("var x = 10;\nmain { return x; }")
        self.assertEqual(prog.declaracoes, (VarDecl("x", Const(10)),))

    def test_referencia_a_variavel_vs_chamada_de_funcao(self) -> None:
        # "f" sozinho e Var; "f()" e Chamada -- mesmo identificador
        prog = analisar("var f = 1;\nmain { return f; }")
        self.assertEqual(prog.exp_final, Var("f"))

        prog2 = analisar("fun f() { return 1; }\nmain { return f(); }")
        self.assertEqual(prog2.exp_final, Chamada("f", ()))

    def test_chamada_com_multiplos_argumentos(self) -> None:
        prog = analisar(
            "fun soma3(a, b, c) { return a + b + c; }\n"
            "main { return soma3(1, 2, 3); }"
        )
        self.assertEqual(
            prog.exp_final, Chamada("soma3", (Const(1), Const(2), Const(3)))
        )

    def test_chamada_aninhada_em_expressao(self) -> None:
        prog = analisar(
            "fun dobro(x) { return x * 2; }\n"
            "main { return dobro(3) + 1; }"
        )
        esperado = OpBin(Op.SOMA, Chamada("dobro", (Const(3),)), Const(1))
        self.assertEqual(prog.exp_final, esperado)


class TestErrosSintaticos(unittest.TestCase):
    def test_entrada_vazia(self) -> None:
        with self.assertRaises(ErroSintatico):
            analisar("")

    def test_main_ausente(self) -> None:
        with self.assertRaises(ErroSintatico):
            analisar("var x = 1;\n{ return x; }")

    def test_fundecl_sem_fechar_parenteses(self) -> None:
        with self.assertRaises(ErroSintatico):
            analisar("fun f(a, b { return a; }\nmain { return f(1, 2); }")

    def test_chamada_sem_fechar_parenteses(self) -> None:
        with self.assertRaises(ErroSintatico):
            analisar("fun f() { return 1; }\nmain { return f(; }")

    def test_vardecl_sem_ponto_virgula(self) -> None:
        with self.assertRaises(ErroSintatico):
            analisar("var x = 1\nmain { return x; }")


class TestSemantica(unittest.TestCase):
    def test_programa_valido_sem_erro(self) -> None:
        fonte = (
            "fun abs(x) {\n"
            "  var y = 0;\n"
            "  if x < 0 { y = 0 - x; } else { y = x; }\n"
            "  return y;\n"
            "}\n"
            "main { return abs(0 - 42); }"
        )
        verifica_programa(analisar(fonte))  # nao deve levantar

    def test_funcao_nao_declarada(self) -> None:
        prog = analisar("main { return naoExiste(1, 2); }")
        with self.assertRaises(ErroSemantico):
            verifica_programa(prog)

    def test_numero_de_parametros_incorreto(self) -> None:
        fonte = "fun soma(a, b) { return a + b; }\nmain { return soma(1, 2, 3); }"
        prog = analisar(fonte)
        with self.assertRaises(ErroSemantico):
            verifica_programa(prog)

    def test_variavel_local_fora_de_escopo(self) -> None:
        fonte = "fun f(x) { return x + 1; }\nmain { return x; }"
        prog = analisar(fonte)
        with self.assertRaises(ErroSemantico):
            verifica_programa(prog)

    def test_recursao_direta_permitida(self) -> None:
        fonte = (
            "fun fib(n) {\n"
            "  var res = 0;\n"
            "  if n < 2 { res = 1; } else { res = fib(n - 1) + fib(n - 2); }\n"
            "  return res;\n"
            "}\n"
            "main { return fib(10); }"
        )
        verifica_programa(analisar(fonte))  # nao deve levantar

    def test_variavel_local_esconde_global(self) -> None:
        fonte = (
            "var x = 100;\n"
            "fun dobro(x) { return x * 2; }\n"
            "main { return dobro(5) + x; }"
        )
        verifica_programa(analisar(fonte))  # nao deve levantar

    def test_nome_usado_como_funcao_e_variavel(self) -> None:
        fonte = "fun f() { return 1; }\nmain { return f + 1; }"
        prog = analisar(fonte)
        with self.assertRaises(ErroSemantico):
            verifica_programa(prog)

    def test_funcao_mutuamente_recursiva_e_rejeitada(self) -> None:
        # par declarado antes de impar -- chama impar, que so e
        # declarada depois: deve ser rejeitado (nao suportamos
        # recursao mutua, conforme secao 5.1 do enunciado)
        fonte = (
            "fun par(n) {\n"
            "  var r = 0;\n"
            "  if n == 0 { r = 1; } else { r = impar(n - 1); }\n"
            "  return r;\n"
            "}\n"
            "fun impar(n) {\n"
            "  var r = 0;\n"
            "  if n == 0 { r = 0; } else { r = par(n - 1); }\n"
            "  return r;\n"
            "}\n"
            "main { return par(4); }"
        )
        prog = analisar(fonte)
        with self.assertRaises(ErroSemantico):
            verifica_programa(prog)


class TestInterpretacao(unittest.TestCase):
    def test_abs_do_enunciado(self) -> None:
        fonte = (
            "fun abs(x) {\n"
            "  var y = 0;\n"
            "  if x < 0 { y = 0 - x; } else { y = x; }\n"
            "  return y;\n"
            "}\n"
            "main { return abs(0 - 42); }"
        )
        self.assertEqual(analisar(fonte).avaliar(), 42)

    def test_abs_de_positivo(self) -> None:
        fonte = (
            "fun abs(x) {\n"
            "  var y = 0;\n"
            "  if x < 0 { y = 0 - x; } else { y = x; }\n"
            "  return y;\n"
            "}\n"
            "main { return abs(7); }"
        )
        self.assertEqual(analisar(fonte).avaliar(), 7)

    def test_fib_recursivo(self) -> None:
        fonte = (
            "fun fib(n) {\n"
            "  var res = 0;\n"
            "  if n < 2 { res = 1; } else { res = fib(n - 1) + fib(n - 2); }\n"
            "  return res;\n"
            "}\n"
            "main { return fib(10); }"
        )
        self.assertEqual(analisar(fonte).avaliar(), 89)

    def test_funcao_chamando_outra_funcao(self) -> None:
        fonte = (
            "fun quadrado(x) { return x * x; }\n"
            "fun somaDosQuadrados(a, b) { return quadrado(a) + quadrado(b); }\n"
            "main { return somaDosQuadrados(3, 4); }"
        )
        self.assertEqual(analisar(fonte).avaliar(), 25)

    def test_variavel_local_esconde_global_valor(self) -> None:
        fonte = (
            "var x = 100;\n"
            "fun dobro(x) { return x * 2; }\n"
            "main { return dobro(5) + x; }"
        )
        self.assertEqual(analisar(fonte).avaliar(), 110)


# --------------------------------------------------------------------- #
# Simulador da maquina de pilha, estendido com CALL/RET, memoria
# enderecavel por deslocamento de %rbp, e LEAVE -- entende exatamente o
# que codegen.py emite para Fun.
# --------------------------------------------------------------------- #

_RE_MOV_IMM = re.compile(r"^mov \$(-?\d+), %rax$")
_RE_MOV_STORE_GLOBAL = re.compile(r"^mov %rax, ([A-Za-z_]\w*)$")
_RE_MOV_LOAD_GLOBAL = re.compile(r"^mov ([A-Za-z_]\w*), %rax$")
_RE_MOV_STORE_LOCAL = re.compile(r"^mov %rax, (-?\d+)\(%rbp\)$")
_RE_MOV_LOAD_LOCAL = re.compile(r"^mov (-?\d+)\(%rbp\), %rax$")
_RE_CMP_IMM = re.compile(r"^cmp \$(-?\d+), %rax$")
_RE_LABEL_DEF = re.compile(r"^([A-Za-z_]\w*):$")
_RE_JMP = re.compile(r"^jmp (\w+)$")
_RE_JZ = re.compile(r"^jz (\w+)$")
_RE_CALL = re.compile(r"^call (\w+)$")
_RE_ADD_RSP = re.compile(r"^add \$(\d+), %rsp$")
_RE_SUB_RSP = re.compile(r"^sub \$(\d+), %rsp$")

MAX_PASSOS = 2_000_000


def _monta_instrucoes(codigo: str) -> tuple[list[str], dict[str, int]]:
    """Extrai as instrucoes executaveis (descartando comentarios/linhas
    vazias) e o mapa rotulo -> indice nessa lista."""
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
    return instrucoes, rotulos


def simular_programa(assembly: str) -> int:
    """Executa o arquivo .s completo (bloco principal + funcoes) e
    devolve o valor final de %rax ao chegar em `call imprime_num`.

    Modela a pilha do sistema como memoria enderecavel de verdade
    (dict endereco -> valor), com %rsp e %rbp como inteiros que
    decrescem/crescem exatamente como no x86-64 real -- isso evita
    ter que reimplementar a aritmetica de deslocamentos "por fora"
    (com indices de lista), reduzindo o simulador a uma traducao
    quase literal de cada instrucao.

    Suporta: mov imediato/global/local(%rbp), push/pop (%rax/%rbp),
    aritmetica, comparacao (cmp/setz/setl/setg), cqo/idiv, jmp/jz com
    rotulos, call/ret (com pilha de retorno propria), leave, sub/add
    em %rsp.
    """
    linhas = assembly.split("\n")
    idx_start = linhas.index("_start:")
    idx_imprime = next(
        i for i, l in enumerate(linhas) if l.strip() == "call imprime_num"
    )
    idx_sair = next(
        i for i, l in enumerate(linhas) if l.strip() == "call sair"
    )
    # inclui a propria linha "call imprime_num" no corpo principal: ela
    # funciona como sentinela de parada (ver tratamento de CALL abaixo),
    # em vez de compararmos indices de pc contra o fim do bloco -- essa
    # comparacao por indice e falha, porque o codigo da primeira funcao
    # comeca exatamente nesse mesmo indice, entao um CALL de main para
    # ela seria confundido com o fim natural do bloco principal.
    corpo_principal = "\n".join(linhas[idx_start + 1 : idx_imprime + 1])
    # o codigo das funcoes comeca depois de "call sair" (nao antes --
    # essa linha nao faz parte do namespace de rotulos das funcoes)
    corpo_resto = "\n".join(linhas[idx_sair + 1 :])

    # o corpo principal comeca em pc=0; as funcoes vem "penduradas" logo
    # em seguida, para que os rotulos das funcoes sejam alcancaveis por
    # CALL a partir de qualquer ponto (inclusive do proprio corpo
    # principal e de outras funcoes).
    instrucoes_principal, rotulos_principal = _monta_instrucoes(corpo_principal)
    fim_principal = len(instrucoes_principal)
    instrucoes_funcoes, rotulos_funcoes_raw = _monta_instrucoes(corpo_resto)
    rotulos_funcoes = {k: v + fim_principal for k, v in rotulos_funcoes_raw.items()}

    instrucoes = instrucoes_principal + instrucoes_funcoes
    rotulos = {**rotulos_principal, **rotulos_funcoes}

    rax = rbx = rcx = 0
    ultimo_cmp = 0
    mem: dict[str, int] = {}  # variaveis globais (por nome)
    pilha: dict[int, int] = {}  # memoria da pilha (por endereco)
    globais_nomes = set()

    RSP_INICIAL = 1_000_000
    rsp = RSP_INICIAL
    rbp = 0

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
        m = _RE_MOV_STORE_LOCAL.match(instr)
        if m:
            pilha[rbp + int(m.group(1))] = rax
            pc += 1
            continue
        m = _RE_MOV_LOAD_LOCAL.match(instr)
        if m:
            rax = pilha[rbp + int(m.group(1))]
            pc += 1
            continue
        m = _RE_MOV_STORE_GLOBAL.match(instr)
        if m:
            mem[m.group(1)] = rax
            globais_nomes.add(m.group(1))
            pc += 1
            continue
        m = _RE_MOV_LOAD_GLOBAL.match(instr)
        if m:
            rax = mem[m.group(1)]
            pc += 1
            continue
        if instr == "mov %rcx, %rax":
            rax = rcx
            pc += 1
            continue
        if instr == "mov %rsp, %rbp":
            rbp = rsp
            pc += 1
            continue
        if instr == "push %rax":
            rsp -= 8
            pilha[rsp] = rax
            pc += 1
            continue
        if instr == "push %rbp":
            rsp -= 8
            pilha[rsp] = rbp
            pc += 1
            continue
        if instr == "pop %rbx":
            rbx = pilha.pop(rsp)
            rsp += 8
            pc += 1
            continue
        if instr == "pop %rbp":
            rbp = pilha.pop(rsp)
            rsp += 8
            pc += 1
            continue
        m = _RE_SUB_RSP.match(instr)
        if m:
            rsp -= int(m.group(1))
            pc += 1
            continue
        m = _RE_ADD_RSP.match(instr)
        if m:
            rsp += int(m.group(1))
            pc += 1
            continue
        if instr == "leave":
            # equivale a: mov %rbp, %rsp ; pop %rbp
            rsp = rbp
            rbp = pilha.pop(rsp)
            rsp += 8
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
            pc = rotulos[m.group(1)] if ultimo_cmp == 0 else pc + 1
            continue
        m = _RE_CALL.match(instr)
        if m:
            if m.group(1) == "imprime_num":
                # sentinela: fim natural do bloco principal
                break
            rsp -= 8
            pilha[rsp] = pc + 1  # endereco de retorno = indice da proxima instrucao
            pc = rotulos[m.group(1)]
            continue
        if instr == "ret":
            pc = pilha.pop(rsp)
            rsp += 8
            continue
        raise AssertionError(f"instrucao inesperada no codigo gerado: {instr!r}")

    if rsp != RSP_INICIAL:
        raise AssertionError(
            f"pilha nao foi esvaziada: rsp final={rsp}, esperado={RSP_INICIAL}"
        )
    return rax


class TestEquivalenciaSemantica(unittest.TestCase):
    """O codigo gerado deve produzir o mesmo valor que Programa.avaliar(),
    inclusive para chamadas de funcao, recursao e variaveis locais."""

    PROGRAMAS = [
        "main { return 7 * 6; }",
        (
            "fun abs(x) {\n"
            "  var y = 0;\n"
            "  if x < 0 { y = 0 - x; } else { y = x; }\n"
            "  return y;\n"
            "}\n"
            "main { return abs(0 - 42); }"
        ),
        (
            "fun abs(x) {\n"
            "  var y = 0;\n"
            "  if x < 0 { y = 0 - x; } else { y = x; }\n"
            "  return y;\n"
            "}\n"
            "main { return abs(17); }"
        ),
        (
            "fun fib(n) {\n"
            "  var res = 0;\n"
            "  if n < 2 { res = 1; } else { res = fib(n - 1) + fib(n - 2); }\n"
            "  return res;\n"
            "}\n"
            "main { return fib(10); }"
        ),
        (
            "fun quadrado(x) { return x * x; }\n"
            "fun somaDosQuadrados(a, b) { return quadrado(a) + quadrado(b); }\n"
            "main { return somaDosQuadrados(3, 4); }"
        ),
        (
            "var x = 100;\n"
            "fun dobro(x) { return x * 2; }\n"
            "main { return dobro(5) + x; }"
        ),
        (
            "fun f(a, b, c) { return a + b * c; }\n"
            "main { return f(1, 2, 3); }"
        ),
        (
            "fun conta(n) {\n"
            "  var total = 0;\n"
            "  var i = 0;\n"
            "  while i < n {\n"
            "    total = total + i;\n"
            "    i = i + 1;\n"
            "  }\n"
            "  return total;\n"
            "}\n"
            "main { return conta(6); }"
        ),
    ]

    def test_codigo_gerado_bate_com_interpretador(self) -> None:
        for fonte in self.PROGRAMAS:
            with self.subTest(programa=fonte):
                prog = analisar(fonte)
                verifica_programa(prog)
                esperado = prog.avaliar()
                assembly = gerar_programa(prog)
                obtido = simular_programa(assembly)
                self.assertEqual(obtido, esperado)


class TestCodegen(unittest.TestCase):
    def test_funcao_gera_rotulo_com_seu_nome(self) -> None:
        fonte = "fun f(x) { return x; }\nmain { return f(1); }"
        assembly = gerar_programa(analisar(fonte))
        self.assertIn("f:", assembly)
        self.assertIn("call f", assembly)

    def test_prologo_e_epilogo_da_funcao(self) -> None:
        fonte = "fun f(x) { var y = 1;\n return x + y; }\nmain { return f(1); }"
        assembly = gerar_programa(analisar(fonte))
        self.assertIn("push %rbp", assembly)
        self.assertIn("sub $8, %rsp", assembly)  # 1 variavel local = 8 bytes
        self.assertIn("mov %rsp, %rbp", assembly)
        self.assertIn("add $8, %rsp", assembly)  # desfaz o sub do prologo
        self.assertIn("pop %rbp", assembly)
        self.assertIn("ret", assembly)

    def test_parametros_empilhados_em_ordem_inversa(self) -> None:
        fonte = "fun f(a, b) { return a - b; }\nmain { return f(11, 202); }"
        assembly = gerar_programa(analisar(fonte))
        idx_202 = assembly.index("mov $202, %rax")
        idx_11 = assembly.index("mov $11, %rax")
        self.assertLess(idx_202, idx_11)  # 202 (2o param) empilhado primeiro

    def test_limpeza_da_pilha_apos_chamada(self) -> None:
        fonte = "fun f(a, b) { return a + b; }\nmain { return f(1, 2); }"
        assembly = gerar_programa(analisar(fonte))
        self.assertIn("add $16, %rsp", assembly)  # 2 parametros * 8 bytes

    def test_sem_parametros_nao_gera_limpeza_de_pilha(self) -> None:
        fonte = "fun f() { return 1; }\nmain { return f(); }"
        assembly = gerar_programa(analisar(fonte))
        self.assertNotIn("call f\n    add", assembly)

    def test_modelo_completo(self) -> None:
        prog = analisar("var x = 1;\nmain { return x; }")
        assembly = gerar_programa(prog)
        self.assertIn(".section .bss", assembly)
        self.assertIn(".section .text", assembly)
        self.assertIn(".globl _start", assembly)
        self.assertIn("_start:", assembly)
        self.assertIn("call imprime_num", assembly)
        self.assertIn("call sair", assembly)
        self.assertIn('.include "runtime.s"', assembly)


class TestCLI(unittest.TestCase):
    """Invoca compfun.py como subprocesso."""

    @classmethod
    def _exec_compilador(cls, arquivo_entrada: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, "compfun.py", arquivo_entrada],
            cwd=RAIZ,
            capture_output=True,
            text=True,
        )

    def test_compila_programa_com_funcao_recursiva(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            entrada = os.path.join(tmp, "p.fun")
            with open(entrada, "w", encoding="utf-8") as f:
                f.write(
                    "fun fib(n) {\n"
                    "  var res = 0;\n"
                    "  if n < 2 { res = 1; } else { res = fib(n - 1) + fib(n - 2); }\n"
                    "  return res;\n"
                    "}\n"
                    "main { return fib(10); }\n"
                )
            res = self._exec_compilador(entrada)
            self.assertEqual(res.returncode, 0, msg=res.stderr)
            saida = os.path.join(tmp, "p.s")
            self.assertTrue(os.path.isfile(saida))
            with open(saida, "r", encoding="utf-8") as f:
                conteudo = f.read()
            self.assertIn("fib:", conteudo)
            self.assertIn("call fib", conteudo)

    def test_erro_semantico_falha_e_nao_gera_s(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            entrada = os.path.join(tmp, "ruim.fun")
            with open(entrada, "w", encoding="utf-8") as f:
                f.write("main { return naoExiste(1); }\n")
            res = self._exec_compilador(entrada)
            self.assertEqual(res.returncode, 1)
            self.assertIn("Erro semantico", res.stderr)
            self.assertFalse(os.path.isfile(os.path.join(tmp, "ruim.s")))

    def test_erro_sintatico_falha_e_nao_gera_s(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            entrada = os.path.join(tmp, "ruim.fun")
            with open(entrada, "w", encoding="utf-8") as f:
                f.write("fun f(a, b { return a; }\nmain { return f(1, 2); }\n")
            res = self._exec_compilador(entrada)
            self.assertEqual(res.returncode, 1)
            self.assertIn("Erro sintatico", res.stderr)
            self.assertFalse(os.path.isfile(os.path.join(tmp, "ruim.s")))

    def test_erro_lexico_falha_e_nao_gera_s(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            entrada = os.path.join(tmp, "ruim.fun")
            with open(entrada, "w", encoding="utf-8") as f:
                f.write("main { return 237axy; }\n")
            res = self._exec_compilador(entrada)
            self.assertEqual(res.returncode, 1)
            self.assertIn("Erro lexico", res.stderr)
            self.assertFalse(os.path.isfile(os.path.join(tmp, "ruim.s")))


if __name__ == "__main__":
    unittest.main(verbosity=2)
