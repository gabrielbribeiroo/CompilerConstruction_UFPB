"""Gera o arquivo RELATORIO.docx a partir do conteudo do RELATORIO.md.

Uso:
    python gerar_relatorio.py

Requer: python-docx (pip install python-docx).
"""

from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement


FONT = "Calibri"
BODY_SIZE = Pt(11)
CODE_FONT = "Consolas"
HEADING_COLOR = RGBColor(0x1F, 0x3A, 0x5F)
TABLE_HEADER_BG = "1F3A5F"
CODE_BG = "F4F4F4"


# -------- helpers --------

def set_cell_shading(cell, hex_color):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color)
    tc_pr.append(shd)


def set_paragraph_shading(paragraph, hex_color):
    p_pr = paragraph._p.get_or_add_pPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color)
    p_pr.append(shd)


def add_heading(doc, text, level):
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.font.name = FONT
    run.bold = True
    if level == 0:
        run.font.size = Pt(20)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    elif level == 1:
        run.font.size = Pt(14)
        run.font.color.rgb = HEADING_COLOR
    elif level == 2:
        run.font.size = Pt(12)
        run.font.color.rgb = HEADING_COLOR
    else:
        run.font.size = Pt(11)
    p.paragraph_format.space_before = Pt(14 if level > 0 else 0)
    p.paragraph_format.space_after = Pt(6)
    return p


def add_runs_with_inline_code(p, text):
    parts = text.split("`")
    for i, part in enumerate(parts):
        run = p.add_run(part)
        run.font.name = FONT
        run.font.size = BODY_SIZE
        if i % 2 == 1:
            run.font.name = CODE_FONT
            run.font.size = Pt(10)


def add_body(doc, text, alignment=WD_ALIGN_PARAGRAPH.JUSTIFY):
    p = doc.add_paragraph()
    p.alignment = alignment
    p.paragraph_format.space_after = Pt(6)
    add_runs_with_inline_code(p, text)
    return p


def add_bullet(doc, text):
    p = doc.add_paragraph(style="List Bullet")
    p.paragraph_format.space_after = Pt(3)
    add_runs_with_inline_code(p, text)
    return p


def add_code_block(doc, code):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(8)
    p.paragraph_format.left_indent = Cm(0.5)
    set_paragraph_shading(p, CODE_BG)
    linhas = code.rstrip("\n").split("\n")
    for i, linha in enumerate(linhas):
        if i > 0:
            run = p.add_run()
            run.add_break()
        run = p.add_run(linha)
        run.font.name = CODE_FONT
        run.font.size = Pt(9.5)
    return p


def add_centered_info_line(doc, label, value, bold_label=True):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(2)
    if label:
        r = p.add_run(label + " ")
        r.bold = bold_label
        r.font.name = FONT
        r.font.size = BODY_SIZE
    r2 = p.add_run(value)
    r2.font.name = FONT
    r2.font.size = BODY_SIZE


def add_table(doc, headers, rows, col_widths=None):
    table = doc.add_table(rows=1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = "Light Grid Accent 1"
    hdr_cells = table.rows[0].cells
    for idx, h in enumerate(headers):
        hdr_cells[idx].text = ""
        r = hdr_cells[idx].paragraphs[0].add_run(h)
        r.bold = True
        r.font.name = FONT
        r.font.size = BODY_SIZE
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        set_cell_shading(hdr_cells[idx], TABLE_HEADER_BG)
        hdr_cells[idx].vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        if col_widths:
            hdr_cells[idx].width = col_widths[idx]
    for row in rows:
        cells = table.add_row().cells
        for idx, valor in enumerate(row):
            cells[idx].text = ""
            add_runs_with_inline_code(cells[idx].paragraphs[0], str(valor))
            cells[idx].vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            if col_widths:
                cells[idx].width = col_widths[idx]
    return table


# -------- documento --------

def build_document(path):
    doc = Document()
    style = doc.styles["Normal"]
    style.font.name = FONT
    style.font.size = BODY_SIZE
    for section in doc.sections:
        section.top_margin = Cm(2.5)
        section.bottom_margin = Cm(2.5)
        section.left_margin = Cm(3)
        section.right_margin = Cm(3)

    # Cabecalho institucional
    add_centered_info_line(doc, "", "Universidade Federal da Paraíba (UFPB)")
    add_centered_info_line(doc, "", "Centro de Informática – Curso de Ciência da Computação")
    add_centered_info_line(doc, "Disciplina:", "Construção de Compiladores 1")
    add_centered_info_line(doc, "Professor:", "Andrei de Araújo Formiga")
    doc.add_paragraph()

    # Titulo
    add_heading(doc, "Relatório – Projeto Final", 0)
    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_sub = p_sub.add_run("Compilador Fun estendido")
    r_sub.italic = True
    r_sub.font.size = Pt(13)
    r_sub.font.name = FONT
    p_sub.paragraph_format.space_after = Pt(18)

    # Integrantes
    add_heading(doc, "Integrantes do grupo", 1)
    add_table(
        doc,
        headers=["Nome", "Matrícula"],
        rows=[
            ["Davi Alves Rodrigues", "20230102377"],
            ["Gabriel Barbosa Ribeiro de Oliveira", "20230012814"],
            ["João Vitor Sampaio Costa", "20230089776"],
            ["Nathan Meira Nóbrega", "20240008904"],
        ],
    )
    doc.add_paragraph()

    # =============== O QUE FOI IMPLEMENTADO ===============
    add_heading(doc, "O que foi implementado", 1)

    # 1. Escolha de extensoes
    add_heading(doc, "1. Escolha de extensões", 2)
    add_body(
        doc,
        "O enunciado do Projeto Final (seção 1) permite escolher uma "
        "extensão de complexidade média ou alta, ou pelo menos três "
        "extensões simples, para acrescentar à linguagem Fun da "
        "Atividade 10. Optamos por três extensões simples da "
        "seção 1.1:",
    )
    add_bullet(doc, "Novos operadores de comparação: `<=`, `>=`, `!=`.")
    add_bullet(doc, "Operadores compostos de atribuição: `+=`, `-=`, `*=`, `/=`.")
    add_bullet(
        doc,
        "`return` como comando (retorno antecipado de dentro de "
        "if/while).",
    )
    add_body(
        doc,
        "O critério foi manter o escopo contido e verificável dentro "
        "do prazo: as três extensões são úteis de verdade (não apenas "
        "variações sintáticas cosméticas), mas nenhuma delas exige um "
        "tipo novo ou muda a representação de valores (tudo continua "
        "inteiro de 64 bits), o que manteve o trabalho concentrado no "
        "lexer/parser/codegen sem tocar a análise de tipos ou o "
        "modelo de memória.",
    )

    # 2. Comparacoes
    add_heading(doc, "2. Novos operadores de comparação (lexer.py, codegen.py)", 2)
    add_body(
        doc,
        "`<=`, `>=` e `!=` são reconhecidos com o mesmo lookahead de "
        "1 caractere já usado para `==` desde a Atividade 09: ao ler "
        "`<`, `>` ou `!`, o lexer olha o caractere seguinte (sem "
        "avançar o cursor até decidir) — se for `=`, consome os dois "
        "caracteres e produz o token composto; senão, produz o token "
        "simples (`<`/`>`) ou levanta erro léxico (`!` sozinho não "
        "existe em Fun, já que não há operador de negação). A "
        "generalização ficou natural: em vez de tratar `<`, `>`, `+`, "
        "`-`, `*`, `/` como casos avulsos, criamos um único dicionário "
        "`_OPERADOR_COMPOSTO` mapeando cada caractere ao par (token "
        "simples, token composto), com um único método "
        "`_ler_operador_composto()` cobrindo os 6 operadores que "
        "agora têm variante composta.",
    )
    add_body(
        doc,
        "No codegen, `Op.MENOR_IGUAL`/`MAIOR_IGUAL`/`DIFERENTE` só "
        "precisaram de três entradas novas em `_OP_COMPARACAO` "
        "(`setle`/`setge`/`setne`) — o esquema `xor %rcx,%rcx; cmp "
        "%rbx,%rax; set<cc> %cl; mov %rcx,%rax` já existente desde a "
        "Atividade 09 não mudou em nada.",
    )

    # 3. Atribuicao composta
    add_heading(doc, "3. Operadores compostos de atribuição (parser.py)", 2)
    add_body(
        doc,
        "`x OP= exp` é implementado como açúcar sintático puro: o "
        "parser desmonta a forma composta em `Atrib(x, OpBin(op, "
        "Var(x), exp))` no próprio `_analisa_atrib()`, antes de a AST "
        "chegar à análise semântica ou ao gerador de código. Não "
        "existe nenhum nó de AST novo para isso — `x += 5;` produz "
        "exatamente a mesma árvore (e, por consequência, o mesmo "
        "assembly) que `x = x + 5;` escrito por extenso. Essa decisão "
        "eliminou qualquer necessidade de tocar `semantica.py` ou "
        "`codegen.py` para esta extensão especificamente: toda a "
        "verificação de escopo e toda a geração de código de `Atrib` "
        "já existiam e continuam servindo sem alteração.",
    )
    add_body(
        doc,
        "Um detalhe de posição: o `Var(x)` sintetizado dentro do "
        "`OpBin` usa a mesma posição do identificador à esquerda, "
        "para que um erro semântico de \"variável usada antes de ser "
        "declarada\" (se `x` não existir) aponte para o lugar certo "
        "no código-fonte, e não para uma posição fictícia.",
    )

    # 4. Return como comando
    add_heading(
        doc,
        "4. return como comando (ast_fun.py, parser.py, semantica.py, codegen.py)",
        2,
    )
    add_body(
        doc,
        "Esta foi a extensão mais delicada, porque a gramática "
        "original de Fun sempre termina o corpo de uma função/main "
        "com um `return` obrigatório, fora da lista de comandos "
        "(`<cmd>* 'return' <exp> ';' '}'`). Permitir `return` também "
        "como comando comum, utilizável dentro de if/while, sem "
        "tornar a gramática ambígua, exigiu uma regra de "
        "desambiguação (detalhada em \"Decisões de projeto\").",
    )
    add_body(
        doc,
        "AST (ast_fun.py): um nó novo, `Return(exp)`, e uma exceção "
        "interna, `RetornoAntecipado(valor)`, usada por `_executar()` "
        "para implementar a saída antecipada no interpretador de "
        "referência — levantada ao encontrar um `Return`, ela se "
        "propaga naturalmente através de qualquer aninhamento de "
        "if/while (a recursão Python já faz esse trabalho) até ser "
        "capturada em `Chamada.avaliar()` ou `Programa.avaliar()`, "
        "que a usam para decidir o valor de retorno em vez de avaliar "
        "`exp_final`.",
    )
    add_body(
        doc,
        "Parser (parser.py): `_analisa_corpo()` (novo método, "
        "reaproveitado por `analisa_programa()` e "
        "`_analisa_fundecl()`, eliminando a duplicação que existia "
        "entre as duas) reconhece `<cmd>* 'return' <exp> ';'` e "
        "resolve a ambiguidade olhando o token logo após o `;` de "
        "cada `return`: se for `}`, é o obrigatório (vira "
        "`exp_final`, e o laço para); caso contrário, é um retorno "
        "antecipado (vira um comando `Return`, e o laço continua). "
        "Dentro de blocos aninhados (if/while), não há essa "
        "ambiguidade: todo `return` ali é sempre um `Return` comum, "
        "já que um bloco aninhado nunca tem \"expressão final\" "
        "própria.",
    )
    add_body(
        doc,
        "Semântica (semantica.py): um caso novo em `_verifica_cmd()` "
        "para `Return` — verifica a expressão com a mesma regra de "
        "escopo (local antes de global) de qualquer outra expressão. "
        "Não insere nem exige nada além disso.",
    )
    add_body(
        doc,
        "Codegen (codegen.py): cada função (e o bloco main) ganha um "
        "rótulo de saída fixo, emitido incondicionalmente logo após "
        "o código da expressão final e antes do epílogo:",
    )
    add_code_block(
        doc,
        "<nome>:\n"
        "    push %rbp\n"
        "    ...\n"
        "    <codigo dos comandos, pode conter Return>\n"
        "    <codigo da expressao final>\n"
        "Lfim_<nome>:\n"
        "    add $8*L, %rsp      # epilogo, igual a Atividade 10\n"
        "    pop %rbp\n"
        "    ret",
    )
    add_body(
        doc,
        "Um `Return(exp)` gera o código de `exp` (deixando o valor em "
        "`%rax`, a mesma convenção de sempre desde a Atividade 06) "
        "seguido de um `jmp Lfim_<nome>` — pulando direto para o "
        "epílogo, sem executar o restante dos comandos nem o código "
        "da expressão final. O bloco main segue a mesma ideia com um "
        "rótulo fixo `Lfim_main`, emitido logo antes de `call "
        "imprime_num`.",
    )

    # 5. Variacao sintatica
    add_heading(doc, "5. Variação sintática", 2)
    add_body(
        doc,
        "Fora as três extensões escolhidas, seguimos exatamente a "
        "gramática da Atividade 10 — nenhuma outra extensão simples "
        "da seção 1.1 (operadores lógicos, strings, booleanos, "
        "funções primitivas) nem qualquer extensão de complexidade "
        "média/alta foi implementada.",
    )

    # 6. Testes
    add_heading(doc, "6. Suíte de testes (tests/test_fun.py)", 2)
    add_body(
        doc,
        "66 testes, 0 falhas, em 8 classes — os 40 testes da "
        "Atividade 10 continuam passando sem nenhuma alteração "
        "(nenhuma regressão), mais 26 novos cobrindo as três "
        "extensões:",
    )
    add_table(
        doc,
        headers=["Classe", "Testes novos desta entrega"],
        rows=[
            [
                "TestLexico",
                "6 (comparações novas, atribuições compostas, operadores simples "
                "não afetados, != bem-formado, ! isolado é erro)",
            ],
            [
                "TestParser",
                "6 (comparações novas geram o Op certo, atribuição composta "
                "desmontada em OpBin, cada operador composto mapeado ao Op certo, "
                "return antecipado vira comando, return único não vira comando)",
            ],
            [
                "TestErrosSintaticos",
                "2 (corpo sem return final mesmo com antecipado presente, "
                "atribuição com operador inválido)",
            ],
            [
                "TestSemantica",
                "2 (variável não declarada dentro de Return, atribuição "
                "composta a variável não declarada)",
            ],
            [
                "TestInterpretacao",
                "5 (comparações novas, atribuição composta encadeada, return de "
                "dentro de if, de while, de recursão)",
            ],
            ["TestEquivalenciaSemantica", "+13 programas na lista (antes 8, agora 21)"],
            [
                "TestCodegen",
                "5 (SETcc novos, atribuição composta idêntica à equivalente, "
                "rótulo de saída emitido, jmp aponta certo)",
            ],
            ["TestCLI", "1 (compilação de programa combinando as três extensões)"],
        ],
    )
    doc.add_paragraph()
    add_body(doc, "Destaques:")
    add_bullet(
        doc,
        "`test_atribuicao_composta_gera_mesmo_codigo_que_equivalente` "
        "prova, byte a byte, que o açúcar sintático da extensão 2 "
        "realmente não introduz nenhuma diferença no assembly gerado "
        "— o teste mais forte possível para essa decisão de design.",
    )
    add_bullet(
        doc,
        "`TestEquivalenciaSemantica` — já o teste mais importante da "
        "Atividade 10 — precisou apenas de 3 linhas novas no "
        "simulador (`setle`/`setge`/`setne`); o rótulo `Lfim_<nome>` "
        "é reconhecido pelo mesmo mecanismo genérico de rótulos que "
        "já existia, sem exigir nenhuma mudança estrutural. Isso "
        "validou de ponta a ponta que um `return` antecipado dentro "
        "de if, de while, e mesmo dentro de uma chamada recursiva "
        "(`fibComReturn`), produz exatamente o mesmo resultado que o "
        "interpretador de referência.",
    )
    add_bullet(
        doc,
        "`test_corpo_sem_return_final_e_erro_mesmo_com_return_antecipado` "
        "confirma que a extensão 3 não afrouxou a exigência original "
        "de que todo corpo termine em `return` — ela só amplia onde "
        "mais `return` pode aparecer.",
    )

    # =============== EXEMPLO DE SAIDA ===============
    add_heading(
        doc, "Exemplo de saída — classifica (as três extensões combinadas)", 1
    )
    add_body(doc, "Fonte (exemplos/valido8_extensoes_combinadas.fun):")
    add_code_block(
        doc,
        "var contador = 0;\n"
        "\n"
        "fun classifica(n) {\n"
        "  if n <= 0 { return 0; } else {}\n"
        "  if n >= 100 { return 2; } else {}\n"
        "  return 1;\n"
        "}\n"
        "\n"
        "main {\n"
        "  contador += classifica(0 - 5);\n"
        "  contador += classifica(50);\n"
        "  contador += classifica(150);\n"
        "  return contador;\n"
        "}",
    )
    add_body(doc, "Trecho do assembly gerado para classifica:")
    add_code_block(
        doc,
        "classifica:\n"
        "    push %rbp\n"
        "    mov %rsp, %rbp\n"
        "    # if (n <= 0) {\n"
        "    mov $0, %rax\n"
        "    push %rax\n"
        "    mov 16(%rbp), %rax\n"
        "    pop %rbx\n"
        "    xor %rcx, %rcx\n"
        "    cmp %rbx, %rax\n"
        "    setle %cl\n"
        "    mov %rcx, %rax\n"
        "    cmp $0, %rax\n"
        "    jz Lfalso0\n"
        "    # return 0; (retorno antecipado)\n"
        "    mov $0, %rax\n"
        "    jmp Lfim_classifica\n"
        "    jmp Lfim0\n"
        "Lfalso0:\n"
        "    ...\n"
        "Lfim0:\n"
        "    # if (n >= 100) {\n"
        "    ...\n"
        "    setge %cl\n"
        "    ...\n"
        "    # return 2; (retorno antecipado)\n"
        "    mov $2, %rax\n"
        "    jmp Lfim_classifica\n"
        "    ...\n"
        "    # return 1;\n"
        "    mov $1, %rax\n"
        "Lfim_classifica:\n"
        "    pop %rbp\n"
        "    ret",
    )
    add_body(
        doc,
        "Executado, imprime `3` (classifica(-5) = 0, classifica(50) = "
        "1, classifica(150) = 2, somados via +=).",
    )

    # =============== ESTRUTURA DE ARQUIVOS ===============
    add_heading(doc, "Estrutura de arquivos entregue", 1)
    add_code_block(
        doc,
        "projeto-final/\n"
        "├── lexer.py\n"
        "├── ast_fun.py\n"
        "├── parser.py\n"
        "├── semantica.py\n"
        "├── codegen.py\n"
        "├── compfun.py\n"
        "├── runtime.s\n"
        "├── exemplos/\n"
        "│   ├── valido1.fun .. valido4.fun\n"
        "│   ├── valido5_comparacoes.fun\n"
        "│   ├── valido6_atribuicao_composta.fun\n"
        "│   ├── valido7_return_antecipado.fun\n"
        "│   ├── valido8_extensoes_combinadas.fun\n"
        "│   ├── invalido_funcao_nao_declarada.fun\n"
        "│   ├── invalido_numero_de_parametros.fun\n"
        "│   └── invalido_variavel_fora_de_escopo.fun\n"
        "├── tests/\n"
        "│   └── test_fun.py\n"
        "├── README.md\n"
        "├── PLANO.md\n"
        "└── RELATORIO.md",
    )

    # =============== DECISOES DE PROJETO ===============
    add_heading(doc, "Decisões de projeto", 1)

    add_heading(
        doc,
        "Por que resolver a ambiguidade do return final olhando o "
        "token após o ';', em vez de restringir return-como-comando "
        "só a blocos aninhados?",
        2,
    )
    add_body(
        doc,
        "A alternativa mais simples de implementar seria permitir "
        "`return` apenas dentro de if/while, nunca diretamente no "
        "corpo de uma função (evitando qualquer ambiguidade com o "
        "return final ali). Rejeitamos essa alternativa porque ela "
        "criaria uma regra artificial e surpreendente: por que "
        "`return` funcionaria dentro de um if mas não diretamente no "
        "corpo? A regra de \"olhar o que vem depois do ';': se é '}', "
        "era o último; senão, é antecipado\" é decidível com o "
        "lookahead de 1 token que o parser já usa em todo o resto da "
        "gramática, e generaliza `return` da forma mais direta "
        "possível: ele é sempre um comando válido em qualquer lugar "
        "onde um comando pode aparecer, e a única regra especial é "
        "reconhecer quando ele coincide com o fim do corpo.",
    )

    add_heading(
        doc,
        "Por que a atribuição composta é açúcar sintático no parser, "
        "em vez de um nó de Cmd próprio (AtribComposta)?",
        2,
    )
    add_body(
        doc,
        "Um `Atrib` já representa perfeitamente uma atribuição — a "
        "única diferença de `x += e` para `x = e2` é como o valor a "
        "ser atribuído é calculado, não que tipo de comando é. "
        "Desmontar no parser significa que a análise semântica (que "
        "verifica se `x` está declarado) e a geração de código (que "
        "emite o mov para .bss ou deslocamento(%rbp)) não precisam "
        "saber que atribuição composta existe — elas processam o "
        "`Atrib` resultante exatamente como sempre processaram. Menos "
        "código, e a prova de corretude fica trivial: "
        "`test_atribuicao_composta_gera_mesmo_codigo_que_equivalente` "
        "verifica que o assembly é idêntico ao da forma equivalente "
        "escrita por extenso.",
    )

    add_heading(
        doc,
        "Por que o rótulo de saída (Lfim_<nome>) é sempre emitido, "
        "mesmo em funções que não usam return antecipado?",
        2,
    )
    add_body(
        doc,
        "Emitir condicionalmente exigiria uma passada prévia pela AST "
        "da função só para descobrir se ela contém algum Return em "
        "algum nível de aninhamento — código extra para economizar "
        "uma única linha de rótulo no .s gerado, que o GNU Assembler "
        "aceita sem nenhum aviso mesmo quando não é alvo de nenhum "
        "jmp. Não vale a complexidade.",
    )

    add_heading(
        doc,
        "Por que a extensão de comparações não precisou tocar "
        "semantica.py?",
        2,
    )
    add_body(
        doc,
        "Porque `_verifica_exp()` trata OpBin genericamente — ela "
        "verifica os dois operandos e devolve, sem nunca inspecionar "
        "qual operador binário está sendo usado. Os três operadores "
        "novos são só mais valores possíveis do Enum Op; nenhuma "
        "regra de escopo ou tipo depende de qual comparação "
        "específica é usada.",
    )

    # =============== DIFICULDADES ===============
    add_heading(doc, "Dificuldades", 1)
    add_body(
        doc,
        "A única dificuldade real desta entrega foi projetar a regra "
        "de desambiguação do return como comando (descrita acima) sem "
        "reestruturar a AST existente (Programa/FunDecl continuam com "
        "um campo exp_final separado, exatamente como na Atividade "
        "10) — a alternativa de dobrar toda a gramática para \"todo "
        "corpo é uma lista de comandos, e o último precisa ser um "
        "Return\" foi considerada, mas descartada por exigir "
        "reescrever semantica.py e codegen.py para validar essa nova "
        "invariante estruturalmente, em vez de reaproveitar o "
        "mecanismo de exp_final já testado e funcionando. A solução "
        "adotada (_analisa_corpo com peek de 1 token) resolve o mesmo "
        "problema com uma mudança bem mais localizada, e o conjunto "
        "de testes (em especial "
        "test_corpo_sem_return_final_e_erro_mesmo_com_return_antecipado "
        "e test_return_final_unico_nao_vira_comando) dá confiança de "
        "que os dois casos-limite (nenhum return antecipado; um "
        "return antecipado seguido do final) continuam corretos.",
    )

    doc.save(path)


if __name__ == "__main__":
    import os
    out = os.path.join(os.path.dirname(__file__), "RELATORIO.docx")
    build_document(out)
    print(f"gerado: {out}")
