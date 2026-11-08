"""Tabelas de alíquotas e fontes oficiais usadas pela calculadora.

Alíquotas em pontos percentuais (18 = 18%). Conferidas em novembro de 2026.
"""

from dataclasses import dataclass, field
from datetime import date

DATA_REFERENCIA = "novembro de 2026"


@dataclass(frozen=True)
class Fonte:
    titulo: str
    orgao: str
    url: str
    resumo: str


@dataclass(frozen=True)
class Estado:
    uf: str
    nome: str
    icms: float  # alíquota interna modal
    fcp: float = 0  # adicional geral de fundo de combate à pobreza


@dataclass(frozen=True)
class Periodo:
    """Valor de um tributo ou de uma mistura num intervalo de datas (aberto se None)."""

    valor: float
    fonte: str
    inicio: date | None = None
    fim: date | None = None
    rotulo: str = ""
    nota: str = ""


@dataclass(frozen=True)
class Combustivel:
    """Tributos ad rem, em R$ por litro (ou por kg) do produto fóssil."""

    unidade: str  # unidade de venda ao consumidor
    sigla: str  # unidade física das alíquotas: "L" ou "kg"
    fossil: str  # nome do derivado de petróleo puro
    icms: tuple[Periodo, ...]
    pis: tuple[Periodo, ...]
    cofins: tuple[Periodo, ...]
    cide: tuple[Periodo, ...]
    # Parte fóssil da mistura vendida na bomba; o ICMS incide sobre o volume todo.
    mistura: tuple[Periodo, ...] = ()
    quantidade: float = 1  # unidades físicas por unidade de venda (13 kg no botijão)


@dataclass(frozen=True)
class Categoria:
    id: str
    nome: str
    grupo: str
    ncm: str
    tipo: str = "mercadoria"  # "mercadoria", "servico" ou "combustivel"
    ipi: float = 0
    pis_cofins_zero: bool = False
    icms: float | None = None  # None = alíquota modal do estado
    iss: float = 0
    nota: str = ""
    fontes: tuple[str, ...] = field(default_factory=tuple)


PLANALTO = "https://www.planalto.gov.br/ccivil_03"

FONTES: dict[str, Fonte] = {
    "lei12741": Fonte(
        "Lei nº 12.741/2012 — Lei da Transparência Fiscal",
        "Presidência da República",
        f"{PLANALTO}/_ato2011-2014/2012/lei/l12741.htm",
        "Obriga informar ao consumidor o valor aproximado dos tributos embutidos no preço: "
        "ICMS, ISS, IPI, IOF, PIS, Cofins e Cide (art. 1º, § 5º).",
    ),
    "cf88": Fonte(
        "Constituição Federal de 1988",
        "Presidência da República",
        f"{PLANALTO}/constituicao/constituicao.htm",
        "Define quem cobra cada tributo (arts. 153, 155, 156 e 195), as imunidades — como a dos "
        "livros (art. 150, VI, d) — e os fundos de combate à pobreza (ADCT, art. 82).",
    ),
    "lc87": Fonte(
        "Lei Complementar nº 87/1996 (Lei Kandir) — ICMS",
        "Presidência da República",
        f"{PLANALTO}/leis/lcp/lcp87.htm",
        "Normas gerais do ICMS. Art. 13, § 1º, I: o montante do próprio imposto integra a sua base "
        "de cálculo (cálculo “por dentro”).",
    ),
    "confaz": Fonte(
        "CONFAZ — Conselho Nacional de Política Fazendária",
        "Ministério da Fazenda",
        "https://www.confaz.fazenda.gov.br/",
        "Reúne estados e União para os convênios de ICMS. As alíquotas internas são fixadas pela "
        "lei de cada estado.",
    ),
    "conv128": Fonte(
        "Convênio ICMS nº 128/1994 — cesta básica",
        "CONFAZ / Ministério da Fazenda",
        "https://www.confaz.fazenda.gov.br/legislacao/convenios/1994/CV128_94",
        "Autoriza os estados a reduzir o ICMS dos produtos da cesta básica até a carga mínima de 7%.",
    ),
    "tipi": Fonte(
        "TIPI — Tabela de Incidência do IPI",
        "Receita Federal",
        "https://www.gov.br/receitafederal/pt-br/acesso-a-informacao/legislacao/"
        "tipi-tabela-de-incidencia-do-imposto-sobre-produtos-industrializados",
        "Alíquota de IPI de cada produto pelo código NCM. Valores desta calculadora conferidos na "
        "versão atualizada até o ADE RFB nº 1/2026.",
    ),
    "dec11158": Fonte(
        "Decreto nº 11.158/2022 — aprova a TIPI",
        "Presidência da República",
        f"{PLANALTO}/_ato2019-2022/2022/decreto/d11158.htm",
        "Decreto que aprova a tabela do IPI em vigor.",
    ),
    "dl288": Fonte(
        "Decreto-Lei nº 288/1967 — Zona Franca de Manaus",
        "Presidência da República",
        f"{PLANALTO}/decreto-lei/del0288.htm",
        "Art. 9º: isenção de IPI para mercadorias produzidas na Zona Franca de Manaus.",
    ),
    "lei10637": Fonte(
        "Lei nº 10.637/2002 — PIS não cumulativo",
        "Presidência da República",
        f"{PLANALTO}/leis/2002/l10637.htm",
        "Art. 2º: alíquota de 1,65% do PIS/Pasep para empresas do lucro real.",
    ),
    "lei10833": Fonte(
        "Lei nº 10.833/2003 — Cofins não cumulativa",
        "Presidência da República",
        f"{PLANALTO}/leis/2003/l10.833.htm",
        "Art. 2º: alíquota de 7,6% da Cofins para empresas do lucro real.",
    ),
    "lei9715": Fonte(
        "Lei nº 9.715/1998 — PIS cumulativo",
        "Presidência da República",
        f"{PLANALTO}/leis/l9715.htm",
        "Art. 8º, I: alíquota de 0,65% do PIS/Pasep sobre o faturamento.",
    ),
    "lei9718": Fonte(
        "Lei nº 9.718/1998 — Cofins cumulativa",
        "Presidência da República",
        f"{PLANALTO}/leis/l9718compilada.htm",
        "Art. 8º: alíquota de 3% da Cofins no regime cumulativo (lucro presumido).",
    ),
    "stf69": Fonte(
        "STF, Tema 69 (RE 574.706) — ICMS fora da base do PIS/Cofins",
        "Supremo Tribunal Federal",
        "https://portal.stf.jus.br/jurisprudenciaRepercussao/verAndamentoProcesso.asp"
        "?incidente=2585258&numeroProcesso=574706&classeProcesso=RE&numeroTema=69",
        "O ICMS não compõe a base de cálculo do PIS e da Cofins.",
    ),
    "lei10925": Fonte(
        "Lei nº 10.925/2004 — alíquota zero da cesta básica",
        "Presidência da República",
        f"{PLANALTO}/_ato2004-2006/2004/lei/l10.925.htm",
        "Art. 1º: PIS/Cofins zero para arroz, feijão, leite, carnes, café, açúcar, óleo, manteiga, "
        "entre outros.",
    ),
    "lei10865": Fonte(
        "Lei nº 10.865/2004 — PIS/Cofins zero para livros",
        "Presidência da República",
        f"{PLANALTO}/_ato2004-2006/2004/lei/l10.865.htm",
        "Art. 28, VI: PIS/Cofins zero na venda de livros no mercado interno.",
    ),
    "lei10147": Fonte(
        "Lei nº 10.147/2000 — PIS/Cofins de medicamentos e cosméticos",
        "Presidência da República",
        f"{PLANALTO}/leis/l10147.htm",
        "Regime monofásico: a cobrança é concentrada na indústria. Medicamentos da “lista positiva” "
        "recebem crédito que anula a contribuição.",
    ),
    "lei13097": Fonte(
        "Lei nº 13.097/2015 — tributação de bebidas frias",
        "Presidência da República",
        f"{PLANALTO}/_ato2015-2018/2015/lei/l13097.htm",
        "Regime próprio de PIS/Cofins e IPI para águas, refrigerantes e cervejas.",
    ),
    "lc116": Fonte(
        "Lei Complementar nº 116/2003 — ISS",
        "Presidência da República",
        f"{PLANALTO}/leis/lcp/lcp116.htm",
        "Arts. 8º e 8º-A: o ISS vai de 2% a 5%; cada município fixa a sua alíquota.",
    ),
    "ec132": Fonte(
        "Emenda Constitucional nº 132/2023 — Reforma Tributária",
        "Presidência da República",
        f"{PLANALTO}/constituicao/emendas/emc/emc132.htm",
        "Cria IBS, CBS e Imposto Seletivo e fixa a transição de 2026 a 2033 (ADCT, arts. 125 a 129).",
    ),
    "lc214": Fonte(
        "Lei Complementar nº 214/2025 — regulamenta IBS, CBS e IS",
        "Presidência da República",
        f"{PLANALTO}/leis/lcp/lcp214.htm",
        "Regras do IBS e da CBS, incluindo o ano-teste de 2026 (CBS 0,9% e IBS 0,1%, compensáveis "
        "com PIS/Cofins).",
    ),
    "lc192": Fonte(
        "Lei Complementar nº 192/2022 — ICMS monofásico dos combustíveis",
        "Presidência da República",
        f"{PLANALTO}/leis/lcp/lcp192.htm",
        "O ICMS de gasolina, diesel e GLP é cobrado uma única vez, em valor fixo por litro ou quilo "
        "(ad rem), igual em todo o país.",
    ),
    "conv112_25": Fonte(
        "Convênio ICMS nº 112/2025 — ICMS da gasolina",
        "CONFAZ / Ministério da Fazenda",
        "https://www.confaz.fazenda.gov.br/legislacao/convenios/2025/CV112_25",
        "Fixa o ICMS em R$ 1,57 por litro de gasolina e etanol anidro a partir de 1º/1/2026.",
    ),
    "conv113_25": Fonte(
        "Convênio ICMS nº 113/2025 — ICMS do diesel e do GLP",
        "CONFAZ / Ministério da Fazenda",
        "https://www.confaz.fazenda.gov.br/legislacao/convenios/2025/CV113_25",
        "Fixa o ICMS em R$ 1,17 por litro de diesel e biodiesel e R$ 1,47 por kg de GLP a partir de "
        "1º/1/2026.",
    ),
    "conv128_26": Fonte(
        "Convênio ICMS nº 128/2026 — novo ICMS do diesel e do GLP",
        "CONFAZ / Ministério da Fazenda",
        "https://www.confaz.fazenda.gov.br/legislacao/convenios/2026/CV128_26",
        "Eleva o ICMS para R$ 1,30 por litro de diesel e R$ 1,54 por kg de GLP a partir de 1º/2/2027.",
    ),
    "dec5059": Fonte(
        "Decreto nº 5.059/2004 — PIS/Cofins dos combustíveis",
        "Presidência da República",
        f"{PLANALTO}/_ato2004-2006/2004/decreto/d5059.htm",
        "Art. 2º: R$ 141,10 + R$ 651,40 por m³ de gasolina, R$ 62,61 + R$ 288,89 por m³ de diesel e "
        "zero para o GLP em botijão de até 13 kg.",
    ),
    "dec5060": Fonte(
        "Decreto nº 5.060/2004 — Cide-Combustíveis",
        "Presidência da República",
        f"{PLANALTO}/_ato2004-2006/2004/decreto/d5060.htm",
        "Art. 1º: Cide de R$ 100 por m³ de gasolina; zero para diesel e GLP.",
    ),
    "dec13116": Fonte(
        "Decreto nº 13.116/2026 — redução do PIS/Cofins da gasolina",
        "Presidência da República",
        f"{PLANALTO}/_ato2023-2026/2026/decreto/D13116.htm",
        "Reduz o PIS/Cofins da gasolina para R$ 28,49 + R$ 131,51 por m³ de 10/9 a 9/10/2026.",
    ),
    "dec13134": Fonte(
        "Decreto nº 13.134/2026 — PIS/Cofins e Cide da gasolina zerados",
        "Presidência da República",
        f"{PLANALTO}/_ato2023-2026/2026/decreto/d13134.htm",
        "Zera o PIS/Cofins e a Cide da gasolina de 10/10 a 9/11/2026.",
    ),
    "dec12875": Fonte(
        "Decreto nº 12.875/2026 — PIS/Cofins do diesel zerado",
        "Presidência da República",
        f"{PLANALTO}/_Ato2023-2026/2026/Decreto/D12875.htm",
        "Praticamente zera o PIS/Cofins do diesel até 31/5/2026.",
    ),
    "cnpe9_26": Fonte(
        "Resolução CNPE nº 9/2026 — gasolina E32",
        "Conselho Nacional de Política Energética / MME",
        "https://www.gov.br/mme/pt-br/assuntos/conselhos-e-comites/cnpe/resolucoes-do-cnpe/2026/"
        "resolucao-9-dou.pdf",
        "32% de etanol anidro na gasolina comum por 180 dias a partir de 1º/8/2026.",
    ),
    "cnpe2025": Fonte(
        "Resoluções CNPE nº 8 e nº 9/2025 — misturas B15 e E30",
        "Conselho Nacional de Política Energética / MME",
        "https://www.gov.br/mme/pt-br/assuntos/conselhos-e-comites/cnpe/resolucoes-do-cnpe/2025",
        "Fixam 15% de biodiesel no diesel e 30% de etanol anidro na gasolina.",
    ),
}

ESTADOS: dict[str, Estado] = {
    e.uf: e
    for e in [
        Estado("AC", "Acre", 19),
        Estado("AL", "Alagoas", 20.5),
        Estado("AP", "Amapá", 18),
        Estado("AM", "Amazonas", 20),
        Estado("BA", "Bahia", 20.5),
        Estado("CE", "Ceará", 20),
        Estado("DF", "Distrito Federal", 20),
        Estado("ES", "Espírito Santo", 17),
        Estado("GO", "Goiás", 19),
        Estado("MA", "Maranhão", 23),
        Estado("MT", "Mato Grosso", 17),
        Estado("MS", "Mato Grosso do Sul", 17),
        Estado("MG", "Minas Gerais", 18),
        Estado("PA", "Pará", 19),
        Estado("PB", "Paraíba", 20),
        Estado("PR", "Paraná", 19.5),
        Estado("PE", "Pernambuco", 20.5),
        Estado("PI", "Piauí", 22.5),
        Estado("RJ", "Rio de Janeiro", 20, fcp=2),
        Estado("RN", "Rio Grande do Norte", 20),
        Estado("RS", "Rio Grande do Sul", 17),
        Estado("RO", "Rondônia", 19.5),
        Estado("RR", "Roraima", 20),
        Estado("SC", "Santa Catarina", 17),
        Estado("SP", "São Paulo", 18),
        Estado("SE", "Sergipe", 19),
        Estado("TO", "Tocantins", 20),
    ]
}

NOTA_ZFM = (
    "Muitos modelos são fabricados na Zona Franca de Manaus, onde o IPI é isento "
    "(Decreto-Lei 288/1967, art. 9º). Marque a opção se for o caso."
)
NOTA_MONOFASICO = (
    "O PIS/Cofins destes produtos é monofásico (Lei 10.147/2000): é pago só pela indústria, com "
    "alíquota maior. Usamos a alíquota geral como aproximação. Alguns estados também cobram ICMS "
    "maior que o modal sobre perfumes e cosméticos."
)
NOTA_BEBIDA_FRIA = (
    "Bebidas frias têm regime próprio de PIS/Cofins (Lei 13.097/2015); usamos a alíquota geral "
    "como aproximação."
)
NOTA_ALCOOL = " Alguns estados cobram ICMS maior que o modal sobre bebidas alcoólicas."
NOTA_EFICIENCIA = (
    "Modelos com índice de eficiência energética A pagam IPI de 6,5% "
    "(Nota Complementar NC 84-3 da TIPI). Ajuste nas alíquotas se for o caso."
)

ALIMENTOS = "Alimentos e bebidas"
BELEZA = "Higiene e beleza"
ELETRONICOS = "Eletrônicos e eletrodomésticos"
VESTUARIO = "Vestuário"
OUTROS = "Outros"
COMBUSTIVEIS_GRUPO = "Combustíveis"
SERVICOS = "Serviços"

NOTA_COMBUSTIVEL = (
    "Combustíveis pagam valores fixos por litro (ad rem): o imposto é o mesmo com o litro a "
    "R$ 5 ou a R$ 7, então a porcentagem muda com o preço da bomba. Não pagam IPI (CF, art. 155, "
    "§ 3º). O etanol hidratado não está incluído, pois o ICMS dele ainda varia por estado."
)

FIM_E32 = date(2027, 1, 27)  # 180 dias a partir de 1º/8/2026
FIM_ZERO_GASOLINA = date(2026, 11, 9)
FIM_ICMS_2026 = date(2027, 1, 31)

COMBUSTIVEIS: dict[str, Combustivel] = {
    "gasolina": Combustivel(
        unidade="litro", sigla="L", fossil="gasolina A",
        mistura=(
            Periodo(0.68, "cnpe9_26", date(2026, 8, 1), FIM_E32, "E32",
                    "A gasolina comum tem 32% de etanol anidro (E32) até 27/01/2027, salvo "
                    "prorrogação (Resolução CNPE 9/2026)."),
            Periodo(0.70, "cnpe2025", rotulo="E30"),
        ),
        icms=(Periodo(1.57, "conv112_25"),),
        pis=(
            Periodo(0.02849, "dec13116", date(2026, 9, 10), date(2026, 10, 9)),
            Periodo(0, "dec13134", date(2026, 10, 10), FIM_ZERO_GASOLINA,
                    nota="PIS/Cofins e Cide da gasolina estão zerados até 09/11/2026 (Decreto "
                         "13.134/2026). Sem prorrogação, voltam a R$ 0,79 e R$ 0,10 por litro de "
                         "gasolina A."),
            Periodo(0.1411, "dec5059"),
        ),
        cofins=(
            Periodo(0.13151, "dec13116", date(2026, 9, 10), date(2026, 10, 9)),
            Periodo(0, "dec13134", date(2026, 10, 10), FIM_ZERO_GASOLINA),
            Periodo(0.6514, "dec5059"),
        ),
        cide=(
            Periodo(0, "dec13134", date(2026, 10, 10), FIM_ZERO_GASOLINA),
            Periodo(0.10, "dec5060"),
        ),
    ),
    "diesel": Combustivel(
        unidade="litro", sigla="L", fossil="diesel A",
        mistura=(Periodo(0.85, "cnpe2025", rotulo="B15"),),
        icms=(
            Periodo(1.17, "conv113_25", fim=FIM_ICMS_2026,
                    nota="O ICMS do diesel sobe para R$ 1,30 por litro em 01/02/2027 (Convênio "
                         "ICMS 128/2026)."),
            Periodo(1.30, "conv128_26", inicio=date(2027, 2, 1)),
        ),
        pis=(
            Periodo(0, "dec12875", date(2026, 3, 12), date(2026, 5, 31)),
            Periodo(0.06261, "dec5059"),
        ),
        cofins=(
            Periodo(0, "dec12875", date(2026, 3, 12), date(2026, 5, 31)),
            Periodo(0.28889, "dec5059"),
        ),
        cide=(Periodo(0, "dec5060"),),
    ),
    "glp": Combustivel(
        unidade="botijão de 13 kg", sigla="kg", fossil="GLP", quantidade=13,
        icms=(
            Periodo(1.47, "conv113_25", fim=FIM_ICMS_2026,
                    nota="O ICMS do gás de cozinha sobe para R$ 1,54 por kg em 01/02/2027 "
                         "(Convênio ICMS 128/2026)."),
            Periodo(1.54, "conv128_26", inicio=date(2027, 2, 1)),
        ),
        pis=(Periodo(0, "dec5059"),),
        cofins=(Periodo(0, "dec5059"),),
        cide=(Periodo(0, "dec5060"),),
    ),
}

CATEGORIAS: dict[str, Categoria] = {
    c.id: c
    for c in [
        Categoria(
            "cesta_basica", "Arroz, feijão e leite (cesta básica)", ALIMENTOS,
            "1006.30 / 0713.33 / 0401.20", ipi=0, pis_cofins_zero=True, icms=7,
            nota="ICMS: os estados podem reduzir a carga da cesta básica até 7% (Convênio ICMS "
                 "128/94) e alguns isentam itens como arroz e feijão. Confira na Sefaz do seu estado.",
            fontes=("lei10925", "conv128", "tipi"),
        ),
        Categoria(
            "biscoito", "Biscoitos e bolachas", ALIMENTOS, "1905.31.00", ipi=0,
            fontes=("tipi",),
        ),
        Categoria(
            "chocolate", "Chocolate", ALIMENTOS, "1806.32.10", ipi=3.25,
            fontes=("tipi",),
        ),
        Categoria(
            "refrigerante", "Refrigerante", ALIMENTOS, "2202.10.00", ipi=2.6,
            nota=NOTA_BEBIDA_FRIA, fontes=("tipi", "lei13097"),
        ),
        Categoria(
            "cerveja", "Cerveja", ALIMENTOS, "2203.00.00", ipi=3.9,
            nota=NOTA_BEBIDA_FRIA + NOTA_ALCOOL, fontes=("tipi", "lei13097"),
        ),
        Categoria(
            "cachaca", "Cachaça e rum", ALIMENTOS, "2208.40.00", ipi=16.25,
            nota=NOTA_ALCOOL.strip(), fontes=("tipi",),
        ),
        Categoria(
            "destilado", "Vodca, uísque e licores", ALIMENTOS, "2208.60.00 / 2208.30.20", ipi=19.5,
            nota=NOTA_ALCOOL.strip(), fontes=("tipi",),
        ),
        Categoria(
            "perfume", "Perfume", BELEZA, "3303.00.10", ipi=27.3,
            nota=NOTA_MONOFASICO, fontes=("tipi", "lei10147"),
        ),
        Categoria(
            "colonia", "Água-de-colônia / deo colônia", BELEZA, "3303.00.20", ipi=7.8,
            nota=NOTA_MONOFASICO, fontes=("tipi", "lei10147"),
        ),
        Categoria(
            "creme", "Cremes e loções de beleza", BELEZA, "3304.99.10", ipi=14.3,
            nota=NOTA_MONOFASICO, fontes=("tipi", "lei10147"),
        ),
        Categoria(
            "xampu", "Xampu", BELEZA, "3305.10.00", ipi=4.55,
            nota=NOTA_MONOFASICO, fontes=("tipi", "lei10147"),
        ),
        Categoria(
            "sabonete", "Sabonete", BELEZA, "3401.11.90", ipi=3.25,
            fontes=("tipi",),
        ),
        Categoria(
            "smartphone", "Celular / smartphone", ELETRONICOS, "8517.13.00", ipi=15,
            nota=NOTA_ZFM, fontes=("tipi", "dl288"),
        ),
        Categoria(
            "notebook", "Notebook", ELETRONICOS, "8471.30.12", ipi=15,
            nota="Modelos fabricados no país com o benefício da Lei de Informática (Lei 8.248/1991) "
                 "podem ter IPI reduzido. " + NOTA_ZFM,
            fontes=("tipi", "dl288"),
        ),
        Categoria(
            "tv", "Televisor", ELETRONICOS, "8528.72.00", ipi=20,
            nota=NOTA_ZFM, fontes=("tipi", "dl288"),
        ),
        Categoria(
            "geladeira", "Geladeira (refrigerador com freezer)", ELETRONICOS, "8418.10.00", ipi=9.75,
            nota=NOTA_EFICIENCIA, fontes=("tipi",),
        ),
        Categoria(
            "lavadora", "Máquina de lavar roupa", ELETRONICOS, "8450.11.00 Ex 01", ipi=13,
            nota=NOTA_EFICIENCIA, fontes=("tipi",),
        ),
        Categoria(
            "fogao", "Fogão a gás", ELETRONICOS, "7321.11.00 Ex 01", ipi=2.6,
            fontes=("tipi",),
        ),
        Categoria(
            "camiseta", "Roupas (camisetas, calças, vestidos)", VESTUARIO, "Capítulos 61 e 62",
            ipi=0, fontes=("tipi",),
        ),
        Categoria(
            "calcado", "Calçados e tênis", VESTUARIO, "Capítulo 64 (ex.: 6404.11.00)", ipi=0,
            fontes=("tipi",),
        ),
        Categoria(
            "medicamento", "Medicamentos", OUTROS, "3004.90.99", ipi=0, pis_cofins_zero=True,
            nota="Considera medicamento da “lista positiva”, cujo PIS/Cofins é anulado por crédito "
                 "presumido (Lei 10.147/2000). Os da lista negativa pagam PIS/Cofins na indústria.",
            fontes=("tipi", "lei10147"),
        ),
        Categoria(
            "livro", "Livros", OUTROS, "4901.99.00", ipi=0, pis_cofins_zero=True, icms=0,
            nota="Livros têm imunidade constitucional de impostos (CF, art. 150, VI, d): sem ICMS e "
                 "sem IPI. O PIS/Cofins também é zero (Lei 10.865/2004, art. 28, VI).",
            fontes=("cf88", "lei10865"),
        ),
        Categoria(
            "brinquedo", "Brinquedos", OUTROS, "9503.00.99", ipi=6.5,
            fontes=("tipi",),
        ),
        Categoria(
            "moto", "Motocicleta (acima de 125 cc)", OUTROS, "8711.20.20", ipi=35,
            nota=NOTA_ZFM, fontes=("tipi", "dl288"),
        ),
        Categoria(
            "outro", "Outro produto (alíquotas gerais)", OUTROS, "—", ipi=0,
            nota="Aplica o ICMS modal do estado e o PIS/Cofins geral. Se o produto tiver IPI, "
                 "consulte a TIPI pelo código NCM e informe em “Ajustar alíquotas”.",
            fontes=("tipi",),
        ),
        Categoria(
            "gasolina", "Gasolina comum", COMBUSTIVEIS_GRUPO, "", tipo="combustivel",
            nota=NOTA_COMBUSTIVEL + " O PIS/Cofins do etanol anidro é zero na venda pela "
                 "distribuidora (Lei 9.718/1998, art. 5º, § 4º-C); não incluímos o cobrado do "
                 "produtor de etanol.",
            fontes=("lc192", "conv112_25", "dec5059", "dec5060"),
        ),
        Categoria(
            "diesel", "Diesel S10", COMBUSTIVEIS_GRUPO, "", tipo="combustivel",
            nota=NOTA_COMBUSTIVEL + " Não incluímos o PIS/Cofins do biodiesel, cobrado do produtor.",
            fontes=("lc192", "conv113_25", "dec5059", "dec5060"),
        ),
        Categoria(
            "glp", "Gás de cozinha (botijão de 13 kg)", COMBUSTIVEIS_GRUPO, "", tipo="combustivel",
            nota="O ICMS do gás de cozinha é um valor fixo por quilo, igual em todo o país (LC "
                 "192/2022). O PIS/Cofins é zero no botijão de até 13 kg para uso doméstico "
                 "(Decreto 5.059/2004, art. 2º, V) e a Cide também é zero.",
            fontes=("lc192", "conv113_25", "dec5059", "dec5060"),
        ),
        Categoria(
            "servico", "Serviços (salão, conserto, academia…)", SERVICOS, "LC 116/2003",
            tipo="servico", iss=5,
            nota="O ISS varia por município, de 2% a 5%; usamos 5%, o teto legal. Ajuste para a "
                 "alíquota da sua cidade.",
            fontes=("lc116",),
        ),
    ]
}

# PIS e Cofins por regime de apuração do vendedor.
REGIMES: dict[str, dict] = {
    "nao_cumulativo": {
        "nome": "Lucro real",
        "pis": 1.65,
        "cofins": 7.6,
        "fontes_pis": ("lei10637",),
        "fontes_cofins": ("lei10833",),
    },
    "cumulativo": {
        "nome": "Lucro presumido",
        "pis": 0.65,
        "cofins": 3.0,
        "fontes_pis": ("lei9715",),
        "fontes_cofins": ("lei9718",),
    },
}
REGIME_PADRAO = {"mercadoria": "nao_cumulativo", "servico": "cumulativo", "combustivel": "nao_cumulativo"}

# Agrupamento das fontes na página.
GRUPOS_FONTES: list[tuple[str, tuple[str, ...]]] = [
    ("Transparência e Constituição", ("lei12741", "cf88")),
    ("ICMS (estadual)", ("lc87", "confaz", "conv128")),
    ("IPI (federal)", ("tipi", "dec11158", "dl288")),
    ("PIS e Cofins (federais)", (
        "lei10637", "lei10833", "lei9715", "lei9718", "stf69",
        "lei10925", "lei10865", "lei10147", "lei13097",
    )),
    ("ISS (municipal)", ("lc116",)),
    ("Combustíveis", (
        "lc192", "conv112_25", "conv113_25", "conv128_26", "dec5059", "dec5060",
        "dec13116", "dec13134", "dec12875", "cnpe9_26", "cnpe2025",
    )),
    ("Reforma Tributária", ("ec132", "lc214")),
]
