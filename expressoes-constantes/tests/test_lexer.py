"""Suite de testes do analisador lexico EC1 (Atividade 04).

43 testes em 9 classes, seguindo a distribuicao documentada em
RELATORIO.md/README.md:

    Numeros (tipo, lexema, posicao)   5
    Operadores (+, -, *, /)           4
    Parenteses                        3
    Expressoes completas              7
    Espacos em branco                 8
    Comentarios (extensao #)          4
    Erros lexicos                     7
    Token EOF                         2
    Representacao str                 3
    Total                            43
"""

from __future__ import annotations

import os
import sys
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from lexer import AnalisadorLexico, ErroLexico, Token, TipoToken  # noqa: E402


class TestNumeros(unittest.TestCase):
    def test_numero_digito_unico(self) -> None:
        (tok,) = AnalisadorLexico("5").tokenizar()
        self.assertEqual(tok, Token(TipoToken.NUMERO, "5", 0))

    def test_numero_multiplos_digitos(self) -> None:
        (tok,) = AnalisadorLexico("12345").tokenizar()
        self.assertEqual(tok, Token(TipoToken.NUMERO, "12345", 0))

    def test_numero_com_zeros_a_esquerda(self) -> None:
        # o lexema preserva os zeros a esquerda; nao ha conversao para int
        (tok,) = AnalisadorLexico("007").tokenizar()
        self.assertEqual(tok.lexema, "007")

    def test_numero_grande(self) -> None:
        (tok,) = AnalisadorLexico("999999999").tokenizar()
        self.assertEqual(tok.lexema, "999999999")

    def test_numero_posicao_correta_apos_espacos(self) -> None:
        (tok,) = AnalisadorLexico("   42").tokenizar()
        self.assertEqual(tok.posicao, 3)


class TestOperadores(unittest.TestCase):
    def test_soma(self) -> None:
        (tok,) = AnalisadorLexico("+").tokenizar()
        self.assertEqual(tok, Token(TipoToken.SOMA, "+", 0))

    def test_subtracao(self) -> None:
        (tok,) = AnalisadorLexico("-").tokenizar()
        self.assertEqual(tok, Token(TipoToken.SUB, "-", 0))

    def test_multiplicacao(self) -> None:
        (tok,) = AnalisadorLexico("*").tokenizar()
        self.assertEqual(tok, Token(TipoToken.MULT, "*", 0))

    def test_divisao(self) -> None:
        (tok,) = AnalisadorLexico("/").tokenizar()
        self.assertEqual(tok, Token(TipoToken.DIV, "/", 0))


class TestParenteses(unittest.TestCase):
    def test_paren_esq(self) -> None:
        (tok,) = AnalisadorLexico("(").tokenizar()
        self.assertEqual(tok, Token(TipoToken.PAREN_ESQ, "(", 0))

    def test_paren_dir(self) -> None:
        (tok,) = AnalisadorLexico(")").tokenizar()
        self.assertEqual(tok, Token(TipoToken.PAREN_DIR, ")", 0))

    def test_par_de_parenteses_aninhados(self) -> None:
        toks = AnalisadorLexico("(())").tokenizar()
        self.assertEqual(
            [t.tipo for t in toks],
            [
                TipoToken.PAREN_ESQ, TipoToken.PAREN_ESQ,
                TipoToken.PAREN_DIR, TipoToken.PAREN_DIR,
            ],
        )


class TestExpressoesCompletas(unittest.TestCase):
    def test_exemplo_do_enunciado(self) -> None:
        # verifica token por token (tipo, lexema e posicao) contra o
        # exemplo literal do enunciado
        toks = AnalisadorLexico("(33 + (912 * 11))").tokenizar()
        esperado = [
            Token(TipoToken.PAREN_ESQ, "(", 0),
            Token(TipoToken.NUMERO, "33", 1),
            Token(TipoToken.SOMA, "+", 4),
            Token(TipoToken.PAREN_ESQ, "(", 6),
            Token(TipoToken.NUMERO, "912", 7),
            Token(TipoToken.MULT, "*", 11),
            Token(TipoToken.NUMERO, "11", 13),
            Token(TipoToken.PAREN_DIR, ")", 15),
            Token(TipoToken.PAREN_DIR, ")", 16),
        ]
        self.assertEqual(toks, esperado)

    def test_expressao_so_um_numero(self) -> None:
        (tok,) = AnalisadorLexico("42").tokenizar()
        self.assertEqual(tok, Token(TipoToken.NUMERO, "42", 0))

    def test_soma_simples(self) -> None:
        toks = AnalisadorLexico("(3 + 4)").tokenizar()
        self.assertEqual(len(toks), 5)

    def test_subtracao_simples(self) -> None:
        toks = AnalisadorLexico("(10 - 2)").tokenizar()
        self.assertEqual(len(toks), 5)

    def test_multiplicacao_simples(self) -> None:
        toks = AnalisadorLexico("(6 * 7)").tokenizar()
        self.assertEqual(len(toks), 5)

    def test_divisao_simples(self) -> None:
        toks = AnalisadorLexico("(20 / 4)").tokenizar()
        self.assertEqual(len(toks), 5)

    def test_expressao_aninhada_multipla(self) -> None:
        # exemplo adicional (valido2.ec1): duas subexpressoes somadas,
        # uma delas com uma multiplicacao aninhada
        toks = AnalisadorLexico("((427 / 7) + (11 * (231 + 5)))").tokenizar()
        self.assertEqual(len(toks), 17)
        self.assertEqual(toks[0].tipo, TipoToken.PAREN_ESQ)
        self.assertEqual(toks[-1].tipo, TipoToken.PAREN_DIR)


class TestEspacosEmBranco(unittest.TestCase):
    def test_espaco_simples(self) -> None:
        toks = AnalisadorLexico("1 + 2").tokenizar()
        self.assertEqual(len(toks), 3)

    def test_tab(self) -> None:
        toks = AnalisadorLexico("1\t+\t2").tokenizar()
        self.assertEqual(len(toks), 3)

    def test_nova_linha(self) -> None:
        toks = AnalisadorLexico("1\n+\n2").tokenizar()
        self.assertEqual(len(toks), 3)

    def test_retorno_de_carro(self) -> None:
        toks = AnalisadorLexico("1\r+\r2").tokenizar()
        self.assertEqual(len(toks), 3)

    def test_multiplos_espacos_entre_tokens(self) -> None:
        toks = AnalisadorLexico("1     +     2").tokenizar()
        self.assertEqual(len(toks), 3)

    def test_espacos_no_inicio(self) -> None:
        (tok,) = AnalisadorLexico("    7").tokenizar()
        self.assertEqual(tok.posicao, 4)

    def test_espacos_no_fim(self) -> None:
        toks = AnalisadorLexico("7    ").tokenizar()
        self.assertEqual(len(toks), 1)

    def test_posicao_com_espacos(self) -> None:
        # a posicao e a do caractere de inicio do token na string
        # ORIGINAL, nao o indice do token na sequencia
        toks = AnalisadorLexico("  1  +  2").tokenizar()
        self.assertEqual([t.posicao for t in toks], [2, 5, 8])


class TestComentarios(unittest.TestCase):
    def test_comentario_de_linha_inteira(self) -> None:
        toks = AnalisadorLexico("# comentario\n42").tokenizar()
        self.assertEqual(toks, [Token(TipoToken.NUMERO, "42", 13)])

    def test_comentario_apos_expressao(self) -> None:
        toks = AnalisadorLexico("(6 * 7)   # resultado: 42").tokenizar()
        self.assertEqual(len(toks), 5)

    def test_comentario_sem_quebra_de_linha_final(self) -> None:
        # comentario que vai ate o fim do arquivo, sem \n final
        toks = AnalisadorLexico("42 # ate o fim do arquivo").tokenizar()
        self.assertEqual(toks, [Token(TipoToken.NUMERO, "42", 0)])

    def test_comentario_entre_tokens_em_linhas_diferentes(self) -> None:
        fonte = "(6\n  # comentario no meio\n  + 7)"
        toks = AnalisadorLexico(fonte).tokenizar()
        self.assertEqual(len(toks), 5)


class TestErrosLexicos(unittest.TestCase):
    def test_caractere_invalido_letra(self) -> None:
        with self.assertRaises(ErroLexico):
            AnalisadorLexico("x").tokenizar()

    def test_caractere_invalido_simbolo(self) -> None:
        with self.assertRaises(ErroLexico):
            AnalisadorLexico("%").tokenizar()

    def test_erro_no_meio_da_expressao(self) -> None:
        # exemplo do enunciado/README: erro na posicao 4
        with self.assertRaises(ErroLexico) as ctx:
            AnalisadorLexico("(12 x 5)").tokenizar()
        self.assertEqual(ctx.exception.posicao, 4)

    def test_erro_guarda_o_caractere_ofensor(self) -> None:
        with self.assertRaises(ErroLexico) as ctx:
            AnalisadorLexico("(12 x 5)").tokenizar()
        self.assertEqual(ctx.exception.caractere, "x")

    def test_erro_mensagem_contem_codigo_ascii(self) -> None:
        with self.assertRaises(ErroLexico) as ctx:
            AnalisadorLexico("(12 x 5)").tokenizar()
        self.assertIn("ASCII 120", str(ctx.exception))

    def test_erro_na_primeira_posicao(self) -> None:
        with self.assertRaises(ErroLexico) as ctx:
            AnalisadorLexico("$123").tokenizar()
        self.assertEqual(ctx.exception.posicao, 0)

    def test_erro_em_caractere_especial(self) -> None:
        with self.assertRaises(ErroLexico) as ctx:
            AnalisadorLexico("(1 @ 2)").tokenizar()
        self.assertEqual(ctx.exception.caractere, "@")


class TestTokenEOF(unittest.TestCase):
    def test_eof_em_entrada_vazia(self) -> None:
        tok = AnalisadorLexico("").proximo_token()
        self.assertEqual(tok, Token(TipoToken.EOF, "", 0))

    def test_eof_apos_ultimo_token(self) -> None:
        lex = AnalisadorLexico("(1)")
        for _ in range(3):
            lex.proximo_token()
        tok = lex.proximo_token()
        self.assertEqual(tok, Token(TipoToken.EOF, "", 3))


class TestRepresentacaoStr(unittest.TestCase):
    def test_str_numero(self) -> None:
        self.assertEqual(str(Token(TipoToken.NUMERO, "42", 0)), '<Numero, "42", 0>')

    def test_str_parenteses(self) -> None:
        self.assertEqual(
            str(Token(TipoToken.PAREN_ESQ, "(", 3)), '<ParenEsq, "(", 3>'
        )

    def test_str_eof(self) -> None:
        self.assertEqual(str(Token(TipoToken.EOF, "", 5)), '<EOF, "", 5>')


if __name__ == "__main__":
    unittest.main(verbosity=2)
