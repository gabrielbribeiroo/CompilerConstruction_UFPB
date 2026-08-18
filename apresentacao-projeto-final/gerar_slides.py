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
    add_section_header(s, "Contexto", "De onde a gente partiu")

    y = Inches(2.3)
    h = Inches(1.0)
    gap = Inches(0.2)
    n = 5
    box_w = (CONTENT_W - gap * (n - 1)) // n
    x = MARGIN_X
    items = [
        ("Marco 1\nsó expressões", COLOR_MUTED),
        ("Depois\nvariáveis", COLOR_PRIMARY),
        ("Depois\nif / while", COLOR_PRIMARY),
        ("Atividade 10\nfunções", COLOR_PRIMARY),
        ("Agora\nProjeto Final", COLOR_PRIMARY),
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
            {"text": "No Marco 1, o compilador só entendia contas com "
                     "números.", "bullet": True},
            {"text": "Depois foi ganhando variáveis, if, while — até virar "
                     "uma linguagem de verdade.", "bullet": True},
            {"text": "Na última atividade, chegamos em funções: com "
                     "parâmetros e até recursão.", "bullet": True},
            {"text": "O Projeto Final é a gente melhorando esse compilador "
                     "de funções.", "bullet": True, "bold": True,
             "color": COLOR_OK},
        ],
        font_size=17,
    )
    add_footer(s, 2, TOTAL_SLIDES, "Davi")


def slide_fun_rapido(prs):
    s = new_blank_slide(prs)
    add_section_header(s, "As novidades", "O que a gente escolheu adicionar")
    col_w = (CONTENT_W - Inches(0.6)) // 2
    add_textbox(
        s, MARGIN_X, Inches(2.0), col_w, Inches(0.4),
        "Um programa em Fun", font_size=16, bold=True, color=COLOR_ACCENT,
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
        "As três coisas que adicionamos", font_size=16, bold=True,
        color=COLOR_ACCENT,
    )
    add_multiline(
        s, right_x, Inches(2.5), col_w, Inches(3.4),
        [
            {"text": "1. Comparações novas (menor ou igual, etc.)",
             "bullet": True, "size": 17},
            {"text": "2. Um atalho pra atualizar variáveis (+=, -=...)",
             "bullet": True, "size": 17},
            {"text": "3. Sair de uma função mais cedo com return",
             "bullet": True, "size": 17},
            {"text": "", "size": 8},
            {"text": "Todas deixam a linguagem mais fácil de usar no "
                     "dia a dia, sem mudar nada do que já funcionava.",
             "italic": True, "color": COLOR_MUTED, "size": 14},
        ],
        line_spacing=1.3,
    )
    add_footer(s, 3, TOTAL_SLIDES, "Davi")


def slide_ext1_comparacoes(prs):
    s = new_blank_slide(prs)
    add_section_header(s, "Extensão 1", "Comparações novas")
    add_multiline(
        s, MARGIN_X, Inches(2.0), CONTENT_W, Inches(0.9),
        [{"text": "A linguagem já tinha 'menor que', 'maior que' e 'igual'. "
                  "Faltavam três bem comuns:", "size": 18}],
    )
    add_code_panel(
        s, MARGIN_X, Inches(2.9), Inches(6.6), Inches(2.4),
        "<=   menor ou igual\n"
        ">=   maior ou igual\n"
        "!=   diferente",
        font_size=20,
    )
    add_textbox(
        s, Inches(7.8), Inches(2.9), Inches(5.0), Inches(0.4),
        "Exemplo de uso", font_size=15, bold=True,
        color=COLOR_ACCENT,
    )
    add_code_panel(
        s, Inches(7.8), Inches(3.3), Inches(5.0), Inches(2.0),
        "if idade >= 60 {\n"
        "  return 2;\n"
        "}",
        font_size=16,
    )
    add_multiline(
        s, MARGIN_X, Inches(5.7), CONTENT_W, Inches(1.2),
        [{"text": "Por dentro, foi tranquilo: reaproveitamos quase todo o "
                  "código que já traduzia as comparações antigas.",
          "bullet": True, "size": 15}],
    )
    add_footer(s, 4, TOTAL_SLIDES, "Nathan")


def slide_ext2_atribuicao(prs):
    s = new_blank_slide(prs)
    add_section_header(s, "Extensão 2", "Um atalho pra atualizar variáveis")
    add_multiline(
        s, MARGIN_X, Inches(2.0), CONTENT_W, Inches(0.7),
        [{"text": "Em vez de repetir o nome da variável duas vezes, agora dá "
                  "pra escrever direto:", "size": 18}],
    )
    add_code_panel(
        s, MARGIN_X, Inches(2.9), CONTENT_W, Inches(1.8),
        "total += 5;      é a mesma coisa que      total = total + 5;",
        font_size=17,
    )
    add_multiline(
        s, MARGIN_X, Inches(5.1), CONTENT_W, Inches(1.9),
        [
            {"text": "Funciona também com -=, *= e /=.", "bullet": True,
             "size": 17},
            {"text": "Deixa o código bem mais limpo, principalmente dentro "
                     "de laços.", "bullet": True, "size": 17},
        ],
    )
    add_footer(s, 5, TOTAL_SLIDES, "Nathan")


def slide_ext2_por_que(prs):
    s = new_blank_slide(prs)
    add_section_header(s, "Extensão 2", "Um detalhe legal dessa implementação")
    add_multiline(
        s, MARGIN_X, Inches(2.4), CONTENT_W, Inches(3.0),
        [
            {"text": "A gente não criou nada novo por trás dos panos.",
             "size": 19, "bold": True, "color": COLOR_PRIMARY},
            {"text": "", "size": 10},
            {"text": "O += simplesmente vira, na hora de compilar, a mesma "
                     "coisa que escrever por extenso — zero código novo pra "
                     "gerar o resultado.", "size": 18},
            {"text": "", "size": 10},
            {"text": "E testamos justamente isso: as duas formas geram "
                     "exatamente o mesmo resultado, sem diferença nenhuma.",
             "size": 18, "color": COLOR_OK},
        ],
        line_spacing=1.35,
    )
    add_footer(s, 6, TOTAL_SLIDES, "Nathan")


def slide_ext3_problema(prs):
    s = new_blank_slide(prs)
    add_section_header(s, "Extensão 3", "Saindo de uma função mais cedo")
    add_multiline(
        s, MARGIN_X, Inches(2.0), CONTENT_W, Inches(1.4),
        [{"text": "Antes, uma função só podia terminar com return bem no "
                  "finalzinho dela. Se quisesse sair mais cedo — de dentro "
                  "de um if, por exemplo — não dava.",
          "size": 18}],
    )
    col_w = (CONTENT_W - Inches(0.6)) // 2
    add_textbox(
        s, MARGIN_X, Inches(3.3), col_w, Inches(0.4),
        "Antes: precisava de uma variável extra", font_size=14, bold=True,
        color=COLOR_MUTED,
    )
    add_code_panel(
        s, MARGIN_X, Inches(3.7), col_w, Inches(2.9),
        "fun sinal(n) {\n"
        "  var r = 0;\n"
        "  if n < 0 { r = 0-1; }\n"
        "  else {\n"
        "    if n == 0 { r = 0; }\n"
        "    else { r = 1; }\n"
        "  }\n"
        "  return r;\n"
        "}",
        font_size=13,
    )
    right_x = MARGIN_X + col_w + Inches(0.6)
    add_textbox(
        s, right_x, Inches(3.3), col_w, Inches(0.4),
        "Agora: sai na hora", font_size=14, bold=True,
        color=COLOR_OK,
    )
    add_code_panel(
        s, right_x, Inches(3.7), col_w, Inches(2.9),
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
    add_footer(s, 7, TOTAL_SLIDES, "João Vitor")


def slide_ext3_solucao(prs):
    s = new_blank_slide(prs)
    add_section_header(s, "Extensão 3", "O desafio de fazer isso funcionar")
    add_multiline(
        s, MARGIN_X, Inches(2.0), CONTENT_W, Inches(1.6),
        [{"text": "O compilador só conhecia um tipo de return: o do "
                  "finalzinho. Agora ele precisa diferenciar: esse return "
                  "aqui é o que encerra tudo, ou é um dos que aparecem no "
                  "meio do caminho?", "size": 18}],
    )
    add_code_panel(
        s, MARGIN_X, Inches(3.6), CONTENT_W, Inches(3.0),
        "fun sinal(n) {\n"
        "  if n < 0 { return 0-1; } else {}   <- antecipado, tem mais coisa depois\n"
        "  if n == 0 { return 0; } else {}    <- antecipado, tem mais coisa depois\n"
        "  return 1;                          <- esse sim e o ultimo de verdade\n"
        "}",
        font_size=13,
    )
    add_multiline(
        s, MARGIN_X, Inches(6.7), CONTENT_W, Inches(0.6),
        [{"text": "A solução: o compilador olha o que vem logo depois de "
                  "cada return pra decidir qual é qual.",
          "bullet": True, "size": 15, "color": COLOR_OK}],
    )
    add_footer(s, 8, TOTAL_SLIDES, "João Vitor")


def slide_ext3_codegen(prs):
    s = new_blank_slide(prs)
    add_section_header(s, "Extensão 3", "Como isso vira código de máquina")
    add_multiline(
        s, MARGIN_X, Inches(2.0), CONTENT_W, Inches(1.2),
        [{"text": "Cada função ganhou um 'ponto de saída' fixo. Quando um "
                  "return antecipado acontece, ele pula direto pra lá.",
          "size": 18}],
    )
    add_code_panel(
        s, MARGIN_X, Inches(3.2), CONTENT_W, Inches(2.6),
        "return 0 - 1;\n"
        "    → calcula o valor\n"
        "    → pula direto pro fim da função (ignora o resto)",
        font_size=17,
    )
    add_multiline(
        s, MARGIN_X, Inches(6.0), CONTENT_W, Inches(1.0),
        [{"text": "É tipo quando a gente pensa 'já achei a resposta, posso "
                  "parar por aqui' — só que em assembly.",
          "bullet": True, "size": 16, "italic": True, "color": COLOR_MUTED}],
    )
    add_footer(s, 9, TOTAL_SLIDES, "João Vitor")


def slide_demo(prs):
    s = new_blank_slide(prs)
    add_section_header(s, "Demo", "Mostrando tudo funcionando junto")
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
    add_section_header(s, "Confiança", "E continua tudo funcionando como antes")
    add_multiline(
        s, MARGIN_X, Inches(2.0), CONTENT_W, Inches(0.9),
        [{"text": "O mais importante: a gente não quebrou nada do que já "
                  "existia.", "size": 18, "bold": True, "color": COLOR_PRIMARY}],
    )
    add_code_panel(
        s, MARGIN_X, Inches(3.0), CONTENT_W, Inches(2.1),
        "$ python tests/test_fun.py\n"
        "----------------------------------------------------------------------\n"
        "Ran 66 tests in 2.0s\n"
        "\n"
        "OK",
        font_size=16,
    )
    add_multiline(
        s, MARGIN_X, Inches(5.4), CONTENT_W, Inches(1.6),
        [
            {"text": "Todos os testes de antes continuam passando do mesmo "
                     "jeito.", "bullet": True, "size": 16},
            {"text": "E escrevemos vários testes novos só pras três coisas "
                     "que adicionamos.", "bullet": True, "size": 16,
             "color": COLOR_OK},
        ],
    )
    add_footer(s, 11, TOTAL_SLIDES, "Gabriel")


def slide_escopo(prs):
    s = new_blank_slide(prs)
    add_section_header(s, "Pra fechar", "Por que só essas três")
    add_multiline(
        s, MARGIN_X, Inches(2.2), CONTENT_W, Inches(1.2),
        [{"text": "O enunciado dava a opção de fazer uma coisa mais "
                  "complexa, ou pelo menos três mais simples. A gente "
                  "preferiu as três simples.", "size": 18}],
    )
    add_multiline(
        s, MARGIN_X, Inches(3.7), CONTENT_W, Inches(2.6),
        [
            {"text": "Comparações novas", "bullet": True, "size": 18},
            {"text": "Atalho pra atualizar variáveis", "bullet": True,
             "size": 18},
            {"text": "Sair de uma função mais cedo", "bullet": True,
             "size": 18},
            {"text": "", "size": 10},
            {"text": "São mudanças que ajudam de verdade quem for programar "
                     "na linguagem — e deu pra testar tudo com calma.",
             "size": 17, "italic": True, "color": COLOR_MUTED},
        ],
        line_spacing=1.3,
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
