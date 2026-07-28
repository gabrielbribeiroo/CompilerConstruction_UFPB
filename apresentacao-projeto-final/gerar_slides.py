"""Gera apresentacao.pptx (16:9) a partir do conteudo do ROTEIRO.md.

Uso:
    python gerar_slides.py

Requer: python-pptx (pip install python-pptx).
"""

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn
from lxml import etree


# Identidade visual (mesma dos relatorios e do Marco 1)
FONT = "Calibri"
TITLE_FONT = "Calibri"
MONO_FONT = "Consolas"

COLOR_BG = RGBColor(0xFF, 0xFF, 0xFF)
COLOR_PRIMARY = RGBColor(0x1F, 0x3A, 0x5F)
COLOR_TEXT = RGBColor(0x22, 0x22, 0x22)
COLOR_MUTED = RGBColor(0x66, 0x66, 0x66)
COLOR_ACCENT = RGBColor(0x2E, 0x75, 0xB6)
COLOR_CODE_BG = RGBColor(0xF4, 0xF4, 0xF4)
COLOR_OK = RGBColor(0x2E, 0x8B, 0x57)

# 16:9 = 13.333 x 7.5 inches
SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)

MARGIN_X = Inches(0.6)
MARGIN_Y = Inches(0.5)
CONTENT_W = SLIDE_W - MARGIN_X * 2


# --------------------------------------------------------------------- #
# Helpers (identicos aos de apresentacao-marco1/gerar_slides.py)
# --------------------------------------------------------------------- #

def add_textbox(slide, left, top, width, height, text, *, font_size=18,
                bold=False, italic=False, color=None, font_name=None,
                align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP):
    tb = slide.shapes.add_textbox(left, top, width, height)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = Emu(0)
    tf.margin_right = Emu(0)
    tf.margin_top = Emu(0)
    tf.margin_bottom = Emu(0)
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.size = Pt(font_size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.name = font_name or FONT
    if color is not None:
        run.font.color.rgb = color
    return tb


def add_multiline(slide, left, top, width, height, lines, *, font_size=18,
                  bold=False, color=None, font_name=None,
                  bullet=False, line_spacing=1.15):
    """lines pode ser list[str] ou list[dict] com chaves: text, size, bold,
    italic, color, font, bullet, indent."""
    tb = slide.shapes.add_textbox(left, top, width, height)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = Emu(0)
    tf.margin_right = Emu(0)
    tf.margin_top = Emu(0)
    tf.margin_bottom = Emu(0)
    for i, line in enumerate(lines):
        if isinstance(line, str):
            line = {"text": line}
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = line.get("align", PP_ALIGN.LEFT)
        p.line_spacing = line_spacing
        p.space_after = Pt(line.get("space_after", 4))
        is_bullet = line.get("bullet", bullet)
        if is_bullet:
            _set_bullet(p, level=line.get("indent", 0))
        run = p.add_run()
        run.text = line["text"]
        run.font.size = Pt(line.get("size", font_size))
        run.font.bold = line.get("bold", bold)
        run.font.italic = line.get("italic", False)
        run.font.name = line.get("font", font_name or FONT)
        clr = line.get("color", color)
        if clr is not None:
            run.font.color.rgb = clr
    return tb


def _set_bullet(paragraph, level=0):
    """Adiciona marcador • ao paragrafo."""
    pPr = paragraph._pPr
    if pPr is None:
        pPr = paragraph._p.get_or_add_pPr()
    pPr.set("indent", str(-228600))  # -0.25in
    pPr.set("marL", str(228600 + level * 228600))
    pPr.set("lvl", str(level))
    # remove qualquer buChar/buNone existente
    for tag in ("a:buChar", "a:buNone", "a:buAutoNum"):
        for el in pPr.findall(qn(tag)):
            pPr.remove(el)
    buChar = etree.SubElement(pPr, qn("a:buChar"))
    buChar.set("char", "•")


def add_filled_rect(slide, left, top, width, height, fill_color, line_color=None):
    rect = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
    rect.fill.solid()
    rect.fill.fore_color.rgb = fill_color
    if line_color is None:
        rect.line.fill.background()
    else:
        rect.line.color.rgb = line_color
    rect.shadow.inherit = False
    # remove texto default
    rect.text_frame.text = ""
    return rect


def add_section_header(slide, eyebrow, title):
    """Cabecalho padrao: faixa colorida na esquerda + eyebrow + titulo grande."""
    # Faixa lateral
    add_filled_rect(slide, Inches(0), Inches(0), Inches(0.15), SLIDE_H, COLOR_PRIMARY)
    # Eyebrow (texto pequeno por cima)
    if eyebrow:
        add_textbox(
            slide, MARGIN_X, Inches(0.45), CONTENT_W, Inches(0.4),
            eyebrow, font_size=14, bold=True, color=COLOR_ACCENT,
        )
    add_textbox(
        slide, MARGIN_X, Inches(0.8), CONTENT_W, Inches(0.9),
        title, font_size=32, bold=True, color=COLOR_PRIMARY,
    )


def add_code_panel(slide, left, top, width, height, code, *, font_size=14):
    """Painel de codigo monoespacado com fundo cinza claro."""
    add_filled_rect(slide, left, top, width, height, COLOR_CODE_BG)
    pad = Inches(0.18)
    lines = code.split("\n")
    line_objs = []
    for ln in lines:
        line_objs.append({
            "text": ln if ln else " ",
            "font": MONO_FONT,
            "size": font_size,
            "color": COLOR_TEXT,
            "space_after": 0,
        })
    add_multiline(
        slide, left + pad, top + pad, width - 2 * pad, height - 2 * pad,
        line_objs, line_spacing=1.05,
    )


def add_footer(slide, page_num, total, speaker=None):
    """Rodape com numero do slide e quem fala."""
    pad = Inches(0.25)
    right = SLIDE_W - pad - Inches(0.6)
    add_textbox(
        slide, right, SLIDE_H - Inches(0.4), Inches(0.6), Inches(0.3),
        f"{page_num}/{total}", font_size=10, color=COLOR_MUTED,
        align=PP_ALIGN.RIGHT,
    )
    if speaker:
        add_textbox(
            slide, MARGIN_X, SLIDE_H - Inches(0.4), Inches(6.0), Inches(0.3),
            f"Apresenta: {speaker}", font_size=10, color=COLOR_MUTED,
        )


# --------------------------------------------------------------------- #
# Construcao da apresentacao
# --------------------------------------------------------------------- #

TOTAL_SLIDES = 13


def new_blank_slide(prs):
    blank = prs.slide_layouts[6]  # layout em branco
    return prs.slides.add_slide(blank)


def slide_capa(prs):
    s = new_blank_slide(prs)
    add_filled_rect(s, Inches(0), Inches(0), SLIDE_W, Inches(1.8), COLOR_PRIMARY)
    add_textbox(
        s, MARGIN_X, Inches(0.5), CONTENT_W, Inches(0.4),
        "Universidade Federal da Paraíba — Centro de Informática",
        font_size=14, color=RGBColor(0xFF, 0xFF, 0xFF),
    )
    add_textbox(
        s, MARGIN_X, Inches(0.9), CONTENT_W, Inches(0.5),
        "Construção de Compiladores 1 — Prof. Andrei de Araújo Formiga",
        font_size=14, color=RGBColor(0xFF, 0xFF, 0xFF), italic=True,
    )
    add_textbox(
        s, MARGIN_X, Inches(2.6), CONTENT_W, Inches(1.2),
        "Projeto Final — Compilador Fun estendido", font_size=40, bold=True,
        color=COLOR_PRIMARY, align=PP_ALIGN.CENTER,
    )
    add_textbox(
        s, MARGIN_X, Inches(3.8), CONTENT_W, Inches(0.7),
        "Comparações novas · Atribuição composta · return como comando",
        font_size=19, italic=True, color=COLOR_MUTED,
        align=PP_ALIGN.CENTER,
    )
    add_textbox(
        s, MARGIN_X, Inches(5.2), CONTENT_W, Inches(0.4),
        "Integrantes do grupo", font_size=14, bold=True,
        color=COLOR_ACCENT, align=PP_ALIGN.CENTER,
    )
    add_multiline(
        s, MARGIN_X, Inches(5.7), CONTENT_W, Inches(1.4),
        [
            {"text": "Davi Alves Rodrigues", "align": PP_ALIGN.CENTER, "size": 16},
            {"text": "Gabriel Barbosa Ribeiro de Oliveira",
             "align": PP_ALIGN.CENTER, "size": 16},
            {"text": "João Vitor Sampaio Costa",
             "align": PP_ALIGN.CENTER, "size": 16},
            {"text": "Nathan Meira Nóbrega",
             "align": PP_ALIGN.CENTER, "size": 16},
        ],
        line_spacing=1.2,
    )
    add_footer(s, 1, TOTAL_SLIDES, "Davi")


def slide_desde_marco1(prs):
    s = new_blank_slide(prs)
    add_section_header(s, "Contexto", "O que mudou desde o Marco 1")

    y = Inches(2.3)
    h = Inches(1.0)
    gap = Inches(0.2)
    n = 5
    box_w = (CONTENT_W - gap * (n - 1)) // n
    x = MARGIN_X
    items = [
        ("EC1\n(Marco 1)", COLOR_MUTED),
        ("EC2 (07)\nprecedência", COLOR_PRIMARY),
        ("EV (08)\nvariáveis", COLOR_PRIMARY),
        ("Cmd (09)\nTuring-completa", COLOR_PRIMARY),
        ("Fun (10)\nfunções", COLOR_PRIMARY),
    ]
    for i, (label, bg) in enumerate(items):
        rect = add_filled_rect(s, x, y, box_w, h, bg)
        tf = rect.text_frame
        tf.margin_left = Inches(0.05)
        tf.margin_right = Inches(0.05)
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        run = p.add_run()
        run.text = label
        run.font.size = Pt(13)
        run.font.bold = True
        run.font.name = FONT
        run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        if i < n - 1:
            arrow_x = x + box_w + Inches(0.01)
            arrow_w = gap - Inches(0.02)
            arrow = s.shapes.add_shape(
                MSO_SHAPE.RIGHT_ARROW, arrow_x, y + h // 2 - Inches(0.12),
                arrow_w, Inches(0.24),
            )
            arrow.fill.solid()
            arrow.fill.fore_color.rgb = COLOR_ACCENT
            arrow.line.fill.background()
        x += box_w + gap

    add_multiline(
        s, MARGIN_X, Inches(3.7), CONTENT_W, Inches(3.2),
        [
            {"text": "07 — Precedência: exp_a/exp_m tiram a obrigação de "
                     "parentizar tudo.", "bullet": True},
            {"text": "08 — Variáveis + primeira análise semântica de verdade "
                     "(tabela de símbolos).", "bullet": True},
            {"text": "09 — Condicionais, laços e comparações: Cmd é a primeira "
                     "linguagem Turing-completa da série.", "bullet": True},
            {"text": "10 — Funções: parâmetros, variáveis locais, recursão "
                     "direta, convenção de chamada em pilha com RBP.",
             "bullet": True},
            {"text": "Projeto Final — parte exatamente daqui.",
             "bullet": True, "bold": True, "color": COLOR_OK},
        ],
        font_size=16,
    )
    add_footer(s, 2, TOTAL_SLIDES, "Davi")


def slide_fun_rapido(prs):
    s = new_blank_slide(prs)
    add_section_header(s, "Ponto de partida", "A linguagem Fun, rapidamente")
    col_w = (CONTENT_W - Inches(0.6)) // 2
    add_textbox(
        s, MARGIN_X, Inches(2.0), col_w, Inches(0.4),
        "Exemplo (Atividade 10)", font_size=16, bold=True, color=COLOR_ACCENT,
    )
    add_code_panel(
        s, MARGIN_X, Inches(2.5), col_w, Inches(3.4),
        "fun abs(x) {\n"
        "  var y = 0;\n"
        "  if x < 0 { y = 0 - x; }\n"
        "  else { y = x; }\n"
        "  return y;\n"
        "}\n"
        "main {\n"
        "  return abs(0 - 42);\n"
        "}",
        font_size=15,
    )
    right_x = MARGIN_X + col_w + Inches(0.6)
    add_textbox(
        s, right_x, Inches(2.0), col_w, Inches(0.4),
        "As três extensões escolhidas", font_size=16, bold=True,
        color=COLOR_ACCENT,
    )
    add_multiline(
        s, right_x, Inches(2.5), col_w, Inches(3.4),
        [
            {"text": "1. Comparações novas: <=, >=, !=", "bullet": True, "size": 17},
            {"text": "2. Atribuição composta: +=, -=, *=, /=",
             "bullet": True, "size": 17},
            {"text": "3. return como comando (retorno antecipado)",
             "bullet": True, "size": 17},
            {"text": "", "size": 8},
            {"text": "Critério: nenhuma exige tipo novo — escopo contido, "
                     "toda a base de Fun continua funcionando sem regressão.",
             "italic": True, "color": COLOR_MUTED, "size": 14},
        ],
        line_spacing=1.3,
    )
    add_footer(s, 3, TOTAL_SLIDES, "Davi")


def slide_ext1_comparacoes(prs):
    s = new_blank_slide(prs)
    add_section_header(s, "Extensão 1", "Novos operadores de comparação")
    add_multiline(
        s, MARGIN_X, Inches(2.0), CONTENT_W, Inches(0.7),
        [{"text": "<=, >= e != — mesmo lookahead de 1 caractere já usado "
                  "para == desde a Atividade 09.", "size": 17}],
    )
    add_code_panel(
        s, MARGIN_X, Inches(2.8), Inches(7.0), Inches(2.6),
        "_OPERADOR_COMPOSTO = {\n"
        '    "<": (MENOR, MENOR_IGUAL),\n'
        '    ">": (MAIOR, MAIOR_IGUAL),\n'
        "    ...\n"
        "}\n"
        "# le o caractere seguinte sem\n"
        "# avancar ate decidir",
        font_size=14,
    )
    add_textbox(
        s, Inches(8.2), Inches(2.8), Inches(4.6), Inches(0.4),
        "Codegen: só mais um SETcc", font_size=15, bold=True,
        color=COLOR_ACCENT,
    )
    add_code_panel(
        s, Inches(8.2), Inches(3.2), Inches(4.6), Inches(2.2),
        "<=  →  setle %cl\n"
        ">=  →  setge %cl\n"
        "!=  →  setne %cl",
        font_size=15,
    )
    add_multiline(
        s, MARGIN_X, Inches(5.7), CONTENT_W, Inches(1.2),
        [{"text": "'!' sozinho não existe em Fun (sem operador de negação) "
                  "— vira erro léxico.", "bullet": True, "size": 15}],
    )
    add_footer(s, 4, TOTAL_SLIDES, "Nathan")


def slide_ext2_atribuicao(prs):
    s = new_blank_slide(prs)
    add_section_header(s, "Extensão 2", "Atribuição composta")
    add_multiline(
        s, MARGIN_X, Inches(2.0), CONTENT_W, Inches(0.6),
        [{"text": "+=, -=, *=, /= — desmontados no PARSER, sem nó de AST novo.",
          "size": 17}],
    )
    add_code_panel(
        s, MARGIN_X, Inches(2.8), CONTENT_W, Inches(2.2),
        "x += 5;              vira exatamente       x = x + 5;\n"
        "\n"
        "Atrib(x, OpBin(SOMA, Var(x), Const(5)))",
        font_size=16,
    )
    add_multiline(
        s, MARGIN_X, Inches(5.4), CONTENT_W, Inches(1.6),
        [
            {"text": "Semântica e codegen não mudam nada — processam o Atrib "
                     "resultante como sempre processaram.", "bullet": True,
             "size": 16},
            {"text": "Teste garante: assembly de x += 5; é byte a byte idêntico "
                     "ao de x = x + 5;", "bullet": True, "size": 16,
             "color": COLOR_OK},
        ],
    )
    add_footer(s, 5, TOTAL_SLIDES, "Nathan")


def slide_ext2_por_que(prs):
    s = new_blank_slide(prs)
    add_section_header(s, "Extensão 2", "Por que açúcar sintático?")
    add_multiline(
        s, MARGIN_X, Inches(2.2), CONTENT_W, Inches(3.5),
        [
            {"text": "Alternativa considerada: um nó AtribComposta próprio, "
                     "com sua própria verificação semântica e geração de "
                     "código.", "size": 17},
            {"text": "", "size": 10},
            {"text": "Por que não: um Atrib já representa perfeitamente uma "
                     "atribuição — a única diferença é como o valor é "
                     "calculado, não que tipo de comando é.", "size": 17},
            {"text": "", "size": 10},
            {"text": "Resultado: menos código, e a prova de corretude fica "
                     "trivial (compara o assembly das duas formas).",
             "size": 17, "color": COLOR_OK, "bold": True},
        ],
        line_spacing=1.35,
    )
    add_footer(s, 6, TOTAL_SLIDES, "Nathan")


def slide_ext3_problema(prs):
    s = new_blank_slide(prs)
    add_section_header(s, "Extensão 3", "return como comando: o problema")
    add_code_panel(
        s, MARGIN_X, Inches(2.0), CONTENT_W, Inches(1.6),
        "<corpo> ::= <cmd>* 'return' <exp> ';' '}'\n"
        "                        ^^^^^^ obrigatorio, sempre por ultimo",
        font_size=16,
    )
    add_multiline(
        s, MARGIN_X, Inches(4.0), CONTENT_W, Inches(2.8),
        [
            {"text": "Queremos permitir return também dentro de if/while, "
                     "não só como última instrução.", "size": 17},
            {"text": "", "size": 10},
            {"text": "Problema: se return pode aparecer em qualquer lugar, "
                     "como o parser sabe qual é o obrigatório (o do fim) e "
                     "qual é antecipado?", "size": 17, "italic": True,
             "color": COLOR_MUTED},
        ],
        line_spacing=1.3,
    )
    add_footer(s, 7, TOTAL_SLIDES, "João Vitor")


def slide_ext3_solucao(prs):
    s = new_blank_slide(prs)
    add_section_header(s, "Extensão 3", "A solução: peek de 1 token")
    add_code_panel(
        s, MARGIN_X, Inches(2.0), Inches(7.2), Inches(3.4),
        "ao encontrar 'return':\n"
        "  consome 'return' <exp> ';'\n"
        "  olha o token seguinte\n"
        "  se for '}':\n"
        "    e o return FINAL -> vira exp_final\n"
        "  senao:\n"
        "    e um return ANTECIPADO -> vira Cmd Return\n"
        "    continua reconhecendo comandos",
        font_size=14,
    )
    add_textbox(
        s, Inches(8.4), Inches(2.0), Inches(4.4), Inches(0.4),
        "sinal(n) usando return", font_size=15, bold=True,
        color=COLOR_ACCENT,
    )
    add_code_panel(
        s, Inches(8.4), Inches(2.4), Inches(4.4), Inches(3.0),
        "fun sinal(n) {\n"
        "  if n < 0 {\n"
        "    return 0-1;\n"
        "  } else {}\n"
        "  if n == 0 {\n"
        "    return 0;\n"
        "  } else {}\n"
        "  return 1;\n"
        "}",
        font_size=13,
    )
    add_multiline(
        s, MARGIN_X, Inches(5.7), CONTENT_W, Inches(1.2),
        [{"text": "Dentro de if/while não há ambiguidade: lá, todo return é "
                  "sempre antecipado.", "bullet": True, "size": 15}],
    )
    add_footer(s, 8, TOTAL_SLIDES, "João Vitor")


def slide_ext3_codegen(prs):
    s = new_blank_slide(prs)
    add_section_header(s, "Extensão 3", "Geração de código do return antecipado")
    add_code_panel(
        s, MARGIN_X, Inches(2.0), CONTENT_W, Inches(3.6),
        "<nome>:\n"
        "    push %rbp\n"
        "    ...\n"
        "    <comandos, pode conter Return>\n"
        "    <expressao final>\n"
        "Lfim_<nome>:              # rotulo de saida, SEMPRE emitido\n"
        "    add $8*L, %rsp        # epilogo (igual Atividade 10)\n"
        "    pop %rbp\n"
        "    ret",
        font_size=15,
    )
    add_multiline(
        s, MARGIN_X, Inches(5.9), CONTENT_W, Inches(1.2),
        [{"text": "Um Return so calcula a expressao (em %rax) e da jmp direto "
                  "pra Lfim_<nome> — pula o resto do corpo.",
          "bullet": True, "size": 16}],
    )
    add_footer(s, 9, TOTAL_SLIDES, "João Vitor")


def slide_demo(prs):
    s = new_blank_slide(prs)
    add_section_header(s, "Demo", "As três extensões juntas")
    add_textbox(
        s, MARGIN_X, Inches(2.0), Inches(6.2), Inches(0.4),
        "$ python compfun.py exemplos/valido8_extensoes_combinadas.fun",
        font_size=13, font_name=MONO_FONT, color=COLOR_ACCENT,
    )
    add_code_panel(
        s, MARGIN_X, Inches(2.4), Inches(6.2), Inches(4.6),
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
        font_size=13,
    )
    add_textbox(
        s, Inches(7.5), Inches(2.0), Inches(5.3), Inches(0.4),
        "Trecho do assembly gerado", font_size=14, bold=True,
        color=COLOR_ACCENT,
    )
    add_code_panel(
        s, Inches(7.5), Inches(2.4), Inches(5.3), Inches(3.4),
        "classifica:\n"
        "    ...\n"
        "    setle %cl        # n <= 0\n"
        "    ...\n"
        "    jmp Lfim_classifica\n"
        "    ...\n"
        "    setge %cl        # n >= 100\n"
        "    ...\n"
        "Lfim_classifica:\n"
        "    pop %rbp\n"
        "    ret",
        font_size=13,
    )
    add_multiline(
        s, Inches(7.5), Inches(6.0), Inches(5.3), Inches(1.0),
        [{"text": "Executado, imprime 3.", "size": 15, "color": COLOR_OK,
          "bold": True}],
    )
    add_footer(s, 10, TOTAL_SLIDES, "Gabriel")


def slide_testes(prs):
    s = new_blank_slide(prs)
    add_section_header(s, "Validação", "Testes")
    add_multiline(
        s, MARGIN_X, Inches(2.0), CONTENT_W, Inches(0.8),
        [{"text": "40 testes da Atividade 10 continuam passando sem nenhuma "
                  "alteração — zero regressão.", "size": 17}],
    )
    add_code_panel(
        s, MARGIN_X, Inches(2.9), CONTENT_W, Inches(2.1),
        "$ python tests/test_fun.py\n"
        "----------------------------------------------------------------------\n"
        "Ran 66 tests in 2.0s\n"
        "\n"
        "OK",
        font_size=16,
    )
    add_multiline(
        s, MARGIN_X, Inches(5.3), CONTENT_W, Inches(1.8),
        [
            {"text": "+26 testes novos cobrindo as três extensões, incluindo "
                     "um caso combinado e return antecipado dentro de "
                     "recursão.", "bullet": True, "size": 16},
            {"text": "O simulador de equivalência semântica (que já pegou 2 "
                     "bugs reais na Atividade 10) só precisou de 3 linhas "
                     "novas — setle/setge/setne.", "bullet": True, "size": 16,
             "color": COLOR_OK},
        ],
    )
    add_footer(s, 11, TOTAL_SLIDES, "Gabriel")


def slide_escopo(prs):
    s = new_blank_slide(prs)
    add_section_header(s, "Escopo", "O que ficou de fora")
    add_multiline(
        s, MARGIN_X, Inches(2.2), CONTENT_W, Inches(1.0),
        [{"text": "Enunciado: 1 extensão média/alta OU pelo menos 3 simples "
                  "— escolhemos 3 simples.", "size": 17}],
    )
    col_w = (CONTENT_W - Inches(0.6)) // 2
    add_textbox(
        s, MARGIN_X, Inches(3.3), col_w, Inches(0.4),
        "Escolhidas", font_size=15, bold=True, color=COLOR_OK,
    )
    add_multiline(
        s, MARGIN_X, Inches(3.8), col_w, Inches(2.5),
        [
            {"text": "<=, >=, !=", "bullet": True, "size": 16},
            {"text": "+=, -=, *=, /=", "bullet": True, "size": 16},
            {"text": "return como comando", "bullet": True, "size": 16},
        ],
    )
    right_x = MARGIN_X + col_w + Inches(0.6)
    add_textbox(
        s, right_x, Inches(3.3), col_w, Inches(0.4),
        "Não escolhidas (fora de escopo)", font_size=15, bold=True,
        color=COLOR_MUTED,
    )
    add_multiline(
        s, right_x, Inches(3.8), col_w, Inches(2.5),
        [
            {"text": "Operadores lógicos (E, OU, NÃO)", "bullet": True,
             "size": 16, "color": COLOR_MUTED},
            {"text": "Strings e booleanos como tipo", "bullet": True,
             "size": 16, "color": COLOR_MUTED},
            {"text": "Funções primitivas pré-definidas", "bullet": True,
             "size": 16, "color": COLOR_MUTED},
            {"text": "Qualquer extensão média/alta", "bullet": True,
             "size": 16, "color": COLOR_MUTED},
        ],
    )
    add_footer(s, 12, TOTAL_SLIDES, "Gabriel")


def slide_encerramento(prs):
    s = new_blank_slide(prs)
    add_filled_rect(s, Inches(0), Inches(0), SLIDE_W, Inches(1.5), COLOR_PRIMARY)
    add_textbox(
        s, MARGIN_X, Inches(0.5), CONTENT_W, Inches(0.8),
        "Projeto Final — Encerramento", font_size=32, bold=True,
        color=RGBColor(0xFF, 0xFF, 0xFF), align=PP_ALIGN.CENTER,
    )
    add_multiline(
        s, MARGIN_X, Inches(2.2), CONTENT_W, Inches(2.5),
        [
            {"text": "Compilador Fun estendido:", "size": 22, "bold": True,
             "color": COLOR_PRIMARY, "align": PP_ALIGN.CENTER},
            {"text": "comparações novas · atribuição composta · "
                     "return como comando",
             "size": 18, "italic": True, "color": COLOR_MUTED,
             "align": PP_ALIGN.CENTER},
        ],
        line_spacing=1.3,
    )
    add_textbox(
        s, MARGIN_X, Inches(4.5), CONTENT_W, Inches(0.6),
        "Repositório no GitHub", font_size=14, bold=True,
        color=COLOR_ACCENT, align=PP_ALIGN.CENTER,
    )
    add_textbox(
        s, MARGIN_X, Inches(5.0), CONTENT_W, Inches(0.6),
        "github.com/gabrielbribeiroo/CompilerConstruction_UFPB",
        font_size=18, font_name=MONO_FONT, color=COLOR_TEXT,
        align=PP_ALIGN.CENTER,
    )
    add_textbox(
        s, MARGIN_X, Inches(6.3), CONTENT_W, Inches(0.5),
        "Obrigado!", font_size=26, bold=True,
        color=COLOR_PRIMARY, align=PP_ALIGN.CENTER,
    )
    add_footer(s, 13, TOTAL_SLIDES)


# --------------------------------------------------------------------- #

def build(path):
    prs = Presentation()
    prs.slide_width = SLIDE_W
    prs.slide_height = SLIDE_H

    slide_capa(prs)                # 1   Davi
    slide_desde_marco1(prs)        # 2   Davi
    slide_fun_rapido(prs)          # 3   Davi
    slide_ext1_comparacoes(prs)    # 4   Nathan
    slide_ext2_atribuicao(prs)     # 5   Nathan
    slide_ext2_por_que(prs)        # 6   Nathan
    slide_ext3_problema(prs)       # 7   João Vitor
    slide_ext3_solucao(prs)        # 8   João Vitor
    slide_ext3_codegen(prs)        # 9   João Vitor
    slide_demo(prs)                # 10  Gabriel
    slide_testes(prs)              # 11  Gabriel
    slide_escopo(prs)              # 12  Gabriel
    slide_encerramento(prs)        # 13  encerramento

    prs.save(path)


if __name__ == "__main__":
    import os
    out = os.path.join(os.path.dirname(__file__), "apresentacao.pptx")
    build(out)
    print(f"gerado: {out}")
