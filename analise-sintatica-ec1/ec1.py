#!/usr/bin/env python3
"""ec1 - Interpretador para a linguagem EC1 (Expressoes Constantes 1).

Uso:
    python ec1.py <arquivo.ec1>

Le um programa EC1 de um arquivo, faz analise lexica e sintatica,
constroi a arvore de sintaxe abstrata e imprime o valor do programa
obtido por interpretacao por varredura da arvore.

Em caso de erro lexico, sintatico ou de E/S, imprime mensagem no stderr
e termina com codigo de saida 1.
"""

from __future__ import annotations

import sys

from lexer import ErroLexico
from parser import ErroSintatico, analisar


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(f"uso: python {argv[0] or 'ec1.py'} <arquivo.ec1>", file=sys.stderr)
        return 2

    caminho = argv[1]
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            fonte = f.read()
    except FileNotFoundError:
        print(f"erro: arquivo nao encontrado: {caminho}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"erro ao ler {caminho}: {exc}", file=sys.stderr)
        return 1

    try:
        arvore = analisar(fonte)
    except (ErroLexico, ErroSintatico) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    try:
        valor = arvore.avaliar()
    except ZeroDivisionError as exc:
        print(f"erro em tempo de execucao: {exc}", file=sys.stderr)
        return 1

    print(valor)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
