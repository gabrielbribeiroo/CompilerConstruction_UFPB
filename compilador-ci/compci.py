#!/usr/bin/env python3
"""compci - Compilador para a linguagem CI (Constantes Inteiras).

Uso:
    python compci.py <arquivo.ci>

Le um arquivo contendo uma constante inteira e gera um arquivo .s em
assembly x86-64 (sintaxe GNU Assembler) seguindo o modelo da atividade.
"""

import os
import re
import sys

TEMPLATE = """#
# Saida gerada pelo compilador CI
#
    .section .text
    .globl _start

_start:
    mov ${valor}, %rax

    call imprime_num
    call sair

    .include "runtime.s"
"""


def erro(mensagem, codigo=1):
    print(f"erro: {mensagem}", file=sys.stderr)
    sys.exit(codigo)


def analisar(conteudo):
    """Etapa de analise: verifica se a entrada e uma constante inteira valida.

    Retorna a string da constante (sem espacos em branco em volta) se for valida;
    chama erro() caso contrario.
    """
    texto = conteudo.strip()
    if not re.fullmatch(r"\d+", texto):
        erro(
            "sintaxe invalida: o programa deve conter apenas uma constante "
            f"inteira (um ou mais digitos). Recebido: {conteudo!r}"
        )
    return texto


def gerar(constante):
    """Etapa de sintese: monta o codigo assembly final a partir da constante."""
    return TEMPLATE.format(valor=constante)


def main(argv):
    if len(argv) != 2:
        erro("uso: compci <arquivo.ci>", codigo=2)

    caminho_entrada = argv[1]
    if not os.path.isfile(caminho_entrada):
        erro(f"arquivo nao encontrado: {caminho_entrada}")

    with open(caminho_entrada, "r", encoding="utf-8") as f:
        conteudo = f.read()

    constante = analisar(conteudo)
    saida = gerar(constante)

    raiz, _ = os.path.splitext(caminho_entrada)
    caminho_saida = raiz + ".s"
    with open(caminho_saida, "w", encoding="utf-8") as f:
        f.write(saida)

    print(f"compilado: {caminho_saida}")


if __name__ == "__main__":
    main(sys.argv)
