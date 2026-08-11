#!/bin/bash
set -e
NOME=$1
if [[ -z "$NOME" ]]; then
  echo "Uso: $0 <nome_exemplo>"
  echo "Exemplo: $0 valido1"
  echo "Exemplo inválido: $0 invalido_funcao_nao_declarada"
  exit 1
fi
if [[ "$NOME" == invalido_* ]]; then
  echo "Testando exemplo inválido: $NOME"
  python3 compfun.py exemplos/$NOME.fun
  echo "[ERRO] o compilador aceitou um exemplo inválido?"
  exit 1
else
  echo "Compilando: $NOME"
  python3 compfun.py exemplos/$NOME.fun
  as --64 -o exemplos/$NOME.o exemplos/$NOME.s
  ld -o exemplos/$NOME exemplos/$NOME.o
  ./exemplos/$NOME
fi
