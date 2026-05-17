/*
 * zeller.c – Verificação da Congruência de Zeller
 * Atividade 03 – Andrei Formiga
 *
 * Compila com:  gcc -o zeller zeller.c
 * Executa com:  ./zeller <dia> <mes> <ano>
 *
 * Exemplo:      ./zeller 16 5 2026   → Sexta-feira
 */

#include <stdio.h>
#include <stdlib.h>

/* Nomes dos dias: índice 0=sábado, 1=domingo, ..., 6=sexta */
static const char *dias[] = {
    "Sabado",
    "Domingo",
    "Segunda-feira",
    "Terca-feira",
    "Quarta-feira",
    "Quinta-feira",
    "Sexta-feira"
};

/*
 * zeller() – implementa a fórmula diretamente, espelhando o assembly.
 *
 * Parâmetros conforme a atividade:
 *   q  = dia do mês
 *   m  = mês ajustado (3=março … 14=fevereiro)
 *   k  = ano dentro do século
 *   j  = século
 *
 * Retorna h ∈ {0,…,6}.
 */
int zeller(int q, int m, int k, int j)
{
    int term1 = (13 * (m + 1)) / 5;   /* floor – divisão inteira positiva */
    int soma  = q + term1 + k + k/4 + j/4 - 2*j;

    /* Em C, o operador % pode retornar valor negativo; corrigir. */
    int h = soma % 7;
    if (h < 0) h += 7;
    return h;
}

/*
 * ajusta_data() – converte (dia, mês, ano) para os parâmetros q, m, k, j
 * conforme as regras da fórmula de Zeller:
 *   - Janeiro e fevereiro são tratados como meses 13 e 14 do ano anterior.
 */
void ajusta_data(int dia, int mes, int ano,
                 int *q, int *m, int *k, int *j)
{
    *q = dia;

    if (mes <= 2) {
        /* Janeiro=13, fevereiro=14 do ano anterior */
        *m   = mes + 12;
        ano -= 1;
    } else {
        *m = mes;
    }

    *k = ano % 100;   /* dois últimos dígitos */
    *j = ano / 100;   /* dois primeiros dígitos */
}

int main(int argc, char *argv[])
{
    int dia, mes, ano;

    if (argc == 4) {
        dia = atoi(argv[1]);
        mes = atoi(argv[2]);
        ano = atoi(argv[3]);
    } else {
        /* Valor padrão igual ao teste no assembly: 16/05/2026 */
        dia = 16; mes = 5; ano = 2026;
        printf("Uso: %s <dia> <mes> <ano>\n", argv[0]);
        printf("Usando data padrao: %02d/%02d/%04d\n\n", dia, mes, ano);
    }

    int q, m, k, j;
    ajusta_data(dia, mes, ano, &q, &m, &k, &j);

    printf("Data : %02d/%02d/%04d\n", dia, mes, ano);
    printf("  q  = %d\n", q);
    printf("  m  = %d\n", m);
    printf("  k  = %d\n", k);
    printf("  j  = %d\n", j);

    int h = zeller(q, m, k, j);
    printf("  h  = %d  →  %s\n", h, dias[h]);

    /* Tabela de verificação com datas conhecidas */
    printf("\n--- Tabela de verificacao ---\n");
    struct { int d, mo, a; const char *esperado; } testes[] = {
        {  1,  1, 2000, "Sabado"        },
        {  4,  7, 1776, "Quinta-feira"  },
        { 14,  3, 1879, "Sexta-feira"   },  /* nascimento de Einstein */
        { 16,  5, 2026, "Sexta-feira"   },
        { 29,  2, 2000, "Terca-feira"   },
    };
    int n = sizeof(testes) / sizeof(testes[0]);
    for (int i = 0; i < n; i++) {
        ajusta_data(testes[i].d, testes[i].mo, testes[i].a, &q, &m, &k, &j);
        h = zeller(q, m, k, j);
        const char *resultado = dias[h];
        const char *status = (resultado[0] == testes[i].esperado[0]) ? "OK" : "ERRO";
        printf("  %02d/%02d/%04d → %-15s [esperado: %-15s] %s\n",
               testes[i].d, testes[i].mo, testes[i].a,
               resultado, testes[i].esperado, status);
    }

    return 0;
}
