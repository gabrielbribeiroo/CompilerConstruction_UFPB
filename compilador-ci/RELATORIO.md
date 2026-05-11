# Relatorio - Atividade 02 - Compilador CI (Constantes Inteiras)

**Universidade Federal da Paraiba (UFPB)**
**Centro de Informatica - Curso de Ciencia da Computacao**
**Disciplina:** Construcao de Compiladores 1
**Professor:** Andrei de Araujo Formiga

## Integrantes do grupo

| Nome                                       | Matricula     |
| ------------------------------------------ | ------------- |
| Davi Alves Rodrigues                       | 20230102377   |
| Gabriel Barbosa Ribeiro de Oliveira        | 20230012814   |
| Joao Vitor Sampaio Costa                   | 20230089776   |
| Nathan Meira Nobrega                       | 20240008904   |

## Como a atividade foi feita

O compilador foi implementado como um unico script seguindo a estrutura
classica de analise -> sintese descrita no enunciado:

1. **Leitura da entrada.** O nome do arquivo `.ci` e recebido como argumento
   na linha de comando (`sys.argv[1]`) e o conteudo e lido inteiro em memoria.
2. **Analise.** O conteudo e validado contra a gramatica da linguagem CI: apos
   remover espacos em branco em volta, o texto precisa casar com a expressao
   regular `\d+` (um ou mais digitos). Qualquer outra coisa (letras, simbolos,
   string vazia) e tratada como erro de sintaxe — o compilador imprime uma
   mensagem no `stderr` e encerra com codigo de saida diferente de zero, sem
   gerar arquivo de saida.
3. **Sintese / geracao de codigo.** A constante validada e interpolada em um
   template de assembly x86-64 (sintaxe GNU Assembler) que segue exatamente
   o modelo do enunciado: secao `.text`, rotulo `_start`, a instrucao
   `mov $<n>, %rax` gerada pelo compilador, chamadas a `imprime_num` e `sair`,
   e a inclusao final de `runtime.s`.
4. **Escrita da saida.** O arquivo `.s` resultante e escrito no mesmo diretorio
   da entrada, com o mesmo nome base e extensao trocada de `.ci` para `.s`.

## Linguagem utilizada

Python 3. A escolha foi por simplicidade: nao ha etapa de build, a leitura de
arquivos e o uso de expressoes regulares sao diretos na biblioteca padrao, e o
mesmo script roda em Windows e Linux sem alteracao. Como a linguagem CI tem
apenas digitos, qualquer linguagem serviria; Python deixou o codigo do
compilador curto e legivel.

## Dificuldades

Nao houve dificuldades significativas. A linguagem CI e minimalista, entao a
analise se reduz a uma checagem de regex e a geracao de codigo a uma
interpolacao de string. Os unicos pontos que exigiram alguma decisao foram:

- Definir o que e "espaco em branco aceitavel" na entrada — optamos por
  permitir espacos/quebras de linha no inicio e no fim do arquivo (uso de
  `strip()`), o que e comum em editores de texto, mas exigir que o conteudo
  efetivo seja apenas digitos.
- Convencao do nome do arquivo de saida — escolhemos preservar o caminho da
  entrada e apenas trocar a extensao, o que torna a localizacao do `.s`
  previsivel para quem usa o compilador.

A verificacao de overflow para 64 bits, mencionada como opcional no enunciado,
nao foi implementada.

## Testes

- `testes/p1.ci` contem `42` — programa correto. O compilador gera
  `testes/p1.s` com `mov $42, %rax` no lugar indicado.
- `testes/erro.ci` contem `42abc` — programa com erro de sintaxe. O compilador
  encerra com codigo de saida 1 e imprime uma mensagem de erro no `stderr`,
  sem gerar arquivo de saida.
