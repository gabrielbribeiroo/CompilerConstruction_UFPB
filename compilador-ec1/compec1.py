#!/usr/bin/env python3
"""compec1 - Compilador completo para a linguagem EC1.

Uso:
    python compec1.py <arquivo.ec1>

Le um programa EC1, faz analise lexica e sintatica, constroi a arvore de
sintaxe abstrata e gera um arquivo `.s` em assembly x86-64 (sintaxe GNU
Assembler) pronto para ser montado e linkado.

A saida e gravada em um arquivo de mesmo nome base, trocando `.ec1` por `.s`.

Em caso de erro lexico, sintatico ou de E/S, imprime mensagem em stderr e
encerra com codigo de saida 1. Nesses casos nenhum arquivo de saida e
criado.
"""

from __future__ import annotations

import os
import sys

from codegen import gerar_programa
from lexer import ErroLexico
from parser import ErroSintatico, analisar


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(f"uso: python {argv[0] or 'compec1.py'} <arquivo.ec1>", file=sys.stderr)
        return 2

    caminho_entrada = argv[1]
    try:
        with open(caminho_entrada, "r", encoding="utf-8") as f:
            fonte = f.read()
    except FileNotFoundError:
        print(f"erro: arquivo nao encontrado: {caminho_entrada}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"erro ao ler {caminho_entrada}: {exc}", file=sys.stderr)
        return 1

    try:
        arvore = analisar(fonte)
    except (ErroLexico, ErroSintatico) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    assembly = gerar_programa(arvore)

    raiz, _ = os.path.splitext(caminho_entrada)
    caminho_saida = raiz + ".s"
    try:
        with open(caminho_saida, "w", encoding="utf-8") as f:
            f.write(assembly)
    except OSError as exc:
        print(f"erro ao escrever {caminho_saida}: {exc}", file=sys.stderr)
        return 1

    print(f"compilado: {caminho_saida}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
