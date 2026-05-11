# Relatório - Atividade 02 - Compilador CI (Constantes Inteiras)

**Universidade Federal da Paraíba (UFPB)**
**Centro de Informática - Curso de Ciência da Computação**
**Disciplina:** Construção de Compiladores 1
**Professor:** Andrei de Araújo Formiga

## Integrantes do grupo

| Nome                                       | Matrícula     |
| ------------------------------------------ | ------------- |
| Davi Alves Rodrigues                       | 20230102377   |
| Gabriel Barbosa Ribeiro de Oliveira        | 20230012814   |
| João Vitor Sampaio Costa                   | 20230089776   |
| Nathan Meira Nóbrega                       | 20240008904   |

## Como a atividade foi feita

O compilador foi implementado como um único script seguindo a estrutura
clássica de análise -> síntese descrita no enunciado:

1. **Leitura da entrada.** O nome do arquivo `.ci` é recebido como argumento
   na linha de comando (`sys.argv[1]`) e o conteúdo é lido inteiro em memória.
2. **Análise.** O conteúdo é validado contra a gramática da linguagem CI: após
   remover espaços em branco em volta, o texto precisa casar com a expressão
   regular `\d+` (um ou mais dígitos). Qualquer outra coisa (letras, símbolos,
   string vazia) é tratada como erro de sintaxe — o compilador imprime uma
   mensagem no `stderr` e encerra com código de saída diferente de zero, sem
   gerar arquivo de saída.
3. **Síntese / geração de código.** A constante validada é interpolada em um
   template de assembly x86-64 (sintaxe GNU Assembler) que segue exatamente
   o modelo do enunciado: seção `.text`, rótulo `_start`, a instrução
   `mov $<n>, %rax` gerada pelo compilador, chamadas a `imprime_num` e `sair`,
   e a inclusão final de `runtime.s`.
4. **Escrita da saída.** O arquivo `.s` resultante é escrito no mesmo
   diretório da entrada, com o mesmo nome base e extensão trocada de `.ci`
   para `.s`.

## Linguagem utilizada

Python 3. A escolha foi por simplicidade: não há etapa de build, a leitura de
arquivos e o uso de expressões regulares são diretos na biblioteca padrão, e
o mesmo script roda em Windows e Linux sem alteração. Como a linguagem CI tem
apenas dígitos, qualquer linguagem serviria; Python deixou o código do
compilador curto e legível.

## Dificuldades

Não houve dificuldades significativas. A linguagem CI é minimalista, então a
análise se reduz a uma checagem de regex e a geração de código a uma
interpolação de string. Os únicos pontos que exigiram alguma decisão foram:

- Definir o que é "espaço em branco aceitável" na entrada — optamos por
  permitir espaços/quebras de linha no início e no fim do arquivo (uso de
  `strip()`), o que é comum em editores de texto, mas exigir que o conteúdo
  efetivo seja apenas dígitos.
- Convenção do nome do arquivo de saída — escolhemos preservar o caminho da
  entrada e apenas trocar a extensão, o que torna a localização do `.s`
  previsível para quem usa o compilador.

A verificação de overflow para 64 bits, mencionada como opcional no
enunciado, não foi implementada.

## Testes

- `testes/p1.ci` contém `42` — programa correto. O compilador gera
  `testes/p1.s` com `mov $42, %rax` no lugar indicado.
- `testes/erro.ci` contém `42abc` — programa com erro de sintaxe. O
  compilador encerra com código de saída 1 e imprime uma mensagem de erro no
  `stderr`, sem gerar arquivo de saída.
