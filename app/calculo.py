"""Cálculo do imposto embutido no preço pago pelo consumidor.

Modelo (preço final P, já com todos os tributos):

* ICMS = P × alíquota. É cobrado "por dentro": o imposto faz parte da própria
  base (LC 87/1996, art. 13, § 1º, I). O FCP é um adicional do ICMS.
* PIS e Cofins = (P − ICMS) × alíquota. O ICMS sai da base (STF, Tema 69).
  Como PIS/Cofins não cumulativos geram crédito ao longo da cadeia, o total
  pago por todas as etapas equivale à alíquota sobre o preço final.
* IPI = P × t / ((1 + t) × (1 + m)). O IPI é cobrado "por fora" na saída da
  fábrica; t é a alíquota da TIPI e m a margem da loja sobre o preço de fábrica.
  Com m = 0 o IPI é estimado sobre o preço final (estimativa máxima).
* ISS (serviços) = P × alíquota, e o PIS/Cofins incide sobre P inteiro.
* Combustíveis: ICMS, PIS/Cofins e Cide são valores fixos por litro (ad rem).
  O ICMS incide sobre o volume todo; os federais, só sobre a parte fóssil da
  mistura (gasolina A no E32, diesel A no B15). Valem as alíquotas da data.
"""

from dataclasses import dataclass, field, replace
from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal
from zoneinfo import ZoneInfo

from . import dados

CENTAVO = Decimal("0.01")
CEM = Decimal(100)
FUSO = ZoneInfo("America/Sao_Paulo")


def hoje() -> date:
    """Data no horário de Brasília; o servidor pode estar em UTC."""
    return datetime.now(FUSO).date()


class ErroCalculo(ValueError):
    pass


@dataclass
class Aliquotas:
    """Alíquotas em pontos percentuais (18 = 18%)."""

    icms: float = 0
    fcp: float = 0
    ipi: float = 0
    pis: float = 0
    cofins: float = 0
    iss: float = 0


@dataclass
class Tributo:
    codigo: str
    nome: str
    esfera: str
    aliquota: float  # % ou, nos tributos ad rem, R$ por litro/kg
    aliquota_texto: str
    base: float  # R$ ou, nos tributos ad rem, litros/kg
    valor: float
    percentual_do_preco: float
    calculo: str
    fontes: list[str]


@dataclass
class Resultado:
    preco: float
    total_impostos: float
    valor_sem_impostos: float
    carga_sobre_preco: float
    acrescimo_sobre_valor: float
    tributos: list[Tributo]
    aliquotas: Aliquotas | None
    padrao: Aliquotas | None
    regime: str | None
    zona_franca: bool
    margem_varejo: float
    avisos: list[str] = field(default_factory=list)
    unidade: str | None = None  # combustíveis: preço por litro ou por botijão
    data: str = ""


def _d(valor: float | Decimal) -> Decimal:
    return Decimal(str(valor))


def _reais(valor: Decimal) -> Decimal:
    return valor.quantize(CENTAVO, rounding=ROUND_HALF_UP)


def _percentual(parte: Decimal, todo: Decimal) -> float:
    return float(_reais(parte / todo * CEM))


def _brl(valor: float | Decimal, casas: int = 2) -> str:
    v = _d(valor).quantize(Decimal(1).scaleb(-casas), rounding=ROUND_HALF_UP)
    inteiro, _, fracao = f"{v:,.{casas}f}".partition(".")
    return f"R$ {inteiro.replace(',', '.')},{fracao.rstrip('0').ljust(2, '0')}"


def _pct(valor: float | Decimal) -> str:
    texto = f"{_d(valor).normalize():f}".replace(".", ",")
    return f"{texto}%"


def _tributo(codigo, nome, esfera, aliquota, aliquota_texto, base, valor, preco, calculo, fontes):
    valor = _reais(valor)
    return Tributo(
        codigo=codigo,
        nome=nome,
        esfera=esfera,
        aliquota=aliquota,
        aliquota_texto=aliquota_texto,
        base=float(_reais(_d(base))),
        valor=float(valor),
        percentual_do_preco=_percentual(valor, preco),
        calculo=calculo,
        fontes=list(fontes),
    )


def _vigente(periodos: tuple[dados.Periodo, ...], data: date) -> dados.Periodo:
    for periodo in periodos:
        if (periodo.inicio is None or periodo.inicio <= data) and (periodo.fim is None or data <= periodo.fim):
            return periodo
    raise ErroCalculo(f"Não há valor cadastrado para {data:%d/%m/%Y}.")


def aliquotas_padrao(
    categoria: dados.Categoria, estado: dados.Estado, regime: str, zona_franca: bool
) -> Aliquotas:
    if categoria.pis_cofins_zero:
        pis = cofins = 0.0
    else:
        pis = dados.REGIMES[regime]["pis"]
        cofins = dados.REGIMES[regime]["cofins"]

    if categoria.tipo == "servico":
        return Aliquotas(pis=pis, cofins=cofins, iss=categoria.iss)

    if categoria.icms is None:
        icms, fcp = estado.icms, estado.fcp
    else:
        icms, fcp = categoria.icms, 0.0
    ipi = 0.0 if zona_franca else categoria.ipi
    return Aliquotas(icms=icms, fcp=fcp, ipi=ipi, pis=pis, cofins=cofins)


def _tributos_combustivel(
    p: Decimal, combustivel: dados.Combustivel, data: date
) -> tuple[list[Tributo], list[str]]:
    quantidade = _d(combustivel.quantidade)
    sigla = combustivel.sigla
    por = "litro" if sigla == "L" else sigla
    mistura = _vigente(combustivel.mistura, data) if combustivel.mistura else None
    fracao = _d(mistura.valor) if mistura else Decimal(1)
    usados = [mistura] if mistura else []

    icms = _vigente(combustivel.icms, data)
    usados.append(icms)
    vezes = f" × {quantidade.normalize():f} {sigla}" if quantidade != 1 else ""
    tributos = [
        _tributo(
            "icms", "ICMS", "estadual", icms.valor, f"{_brl(icms.valor)}/{sigla}",
            quantidade, _d(icms.valor) * quantidade, p,
            f"{_brl(icms.valor)} por {por}{vezes} — valor fixo, igual em todo o país",
            ("lc192", icms.fonte),
        )
    ]
    for codigo, nome, periodos in (
        ("pis", "PIS/Pasep", combustivel.pis),
        ("cofins", "Cofins", combustivel.cofins),
        ("cide", "Cide-Combustíveis", combustivel.cide),
    ):
        periodo = _vigente(periodos, data)
        usados.append(periodo)
        if periodo.valor:
            calculo = f"{_brl(periodo.valor, 5)} por {por} de {combustivel.fossil}"
            if mistura:
                calculo += f" × {_pct(fracao * CEM)} de {combustivel.fossil} na mistura ({mistura.rotulo})"
            texto = f"{_brl(periodo.valor, 5)}/{sigla}"
        else:
            calculo = "Alíquota zero" + (f" até {periodo.fim:%d/%m/%Y}" if periodo.fim else "")
            texto = "zero"
        tributos.append(
            _tributo(
                codigo, nome, "federal", periodo.valor, texto, quantidade * fracao,
                _d(periodo.valor) * fracao * quantidade, p, calculo, (periodo.fonte,),
            )
        )
    notas = [periodo.nota for periodo in usados if periodo.nota]
    return tributos, list(dict.fromkeys(notas))


def calcular(
    preco: float,
    categoria_id: str,
    uf: str,
    regime: str | None = None,
    zona_franca: bool = False,
    ajustes: dict[str, float] | None = None,
    margem_varejo: float = 0,
    data: date | None = None,
) -> Resultado:
    categoria = dados.CATEGORIAS.get(categoria_id)
    if categoria is None:
        raise ErroCalculo(f"Categoria desconhecida: {categoria_id}")
    estado = dados.ESTADOS.get(uf.upper())
    if estado is None:
        raise ErroCalculo(f"UF desconhecida: {uf}")
    regime = regime or dados.REGIME_PADRAO[categoria.tipo]
    if regime not in dados.REGIMES:
        raise ErroCalculo(f"Regime desconhecido: {regime}")
    if preco <= 0:
        raise ErroCalculo("O preço deve ser maior que zero.")
    data = data or hoje()

    p = _d(preco)
    avisos = [categoria.nota] if categoria.nota else []

    if categoria.tipo == "combustivel":
        combustivel = dados.COMBUSTIVEIS[categoria.id]
        tributos, notas = _tributos_combustivel(p, combustivel, data)
        avisos += notas + [f"Valores vigentes em {data:%d/%m/%Y}."]
        return _resultado(
            p, tributos, avisos, None, None, None, False, 0, data, unidade=combustivel.unidade,
            erro=f"O preço informado é menor que os tributos fixos por {combustivel.unidade}.",
        )

    padrao = aliquotas_padrao(categoria, estado, regime, zona_franca)
    aliq = replace(padrao, **{k: v for k, v in (ajustes or {}).items() if v is not None})

    servico = categoria.tipo == "servico"
    regime_info = dados.REGIMES[regime]
    tributos: list[Tributo] = []

    def adiciona(codigo, nome, esfera, aliquota, base, valor, calculo, fontes):
        tributos.append(
            _tributo(codigo, nome, esfera, aliquota, _pct(aliquota), base, valor, p, calculo, fontes)
        )

    if servico:
        iss = p * _d(aliq.iss) / CEM
        adiciona(
            "iss", "ISS", "municipal", aliq.iss, p, iss,
            f"{_pct(aliq.iss)} × {_brl(p)} (preço do serviço)",
            ("lc116",),
        )
        base_pis_cofins = p
        nota_base = "preço do serviço"
        fontes_base = ()
    else:
        icms = p * _d(aliq.icms) / CEM
        fontes_icms = ("lc87", "conv128") if categoria.id == "cesta_basica" else ("lc87", "confaz")
        if categoria.id == "livro":
            fontes_icms = ("cf88",)
        adiciona(
            "icms", "ICMS", "estadual", aliq.icms, p, icms,
            f"{_pct(aliq.icms)} × {_brl(p)} — cobrado “por dentro”: o imposto faz parte do "
            "próprio preço",
            fontes_icms,
        )
        fcp = p * _d(aliq.fcp) / CEM
        if aliq.fcp:
            adiciona(
                "fcp", "FCP (adicional de ICMS)", "estadual", aliq.fcp, p,
                fcp, f"{_pct(aliq.fcp)} × {_brl(p)} — Fundo de Combate à Pobreza", ("cf88",),
            )
        t = _d(aliq.ipi) / CEM
        m = _d(margem_varejo) / CEM
        base_ipi = p / ((1 + t) * (1 + m))
        texto_base_ipi = (
            "preço sem o IPI" if not m
            else f"preço de fábrica estimado (margem da loja de {_pct(margem_varejo)})"
        )
        adiciona(
            "ipi", "IPI", "federal", aliq.ipi, base_ipi, base_ipi * t,
            f"{_pct(aliq.ipi)} × {_brl(base_ipi)} ({texto_base_ipi}) — cobrado “por fora”, "
            "na saída da fábrica",
            ("tipi", "dl288") if zona_franca else ("tipi",),
        )
        base_pis_cofins = p - icms - fcp
        nota_base = "preço menos o ICMS"
        fontes_base = ("stf69",)

    fontes_zero = {"cesta_basica": ("lei10925",), "livro": ("lei10865",), "medicamento": ("lei10147",)}
    zero = fontes_zero.get(categoria.id) if categoria.pis_cofins_zero and not aliq.pis else None
    adiciona(
        "pis", "PIS/Pasep", "federal", aliq.pis, base_pis_cofins,
        base_pis_cofins * _d(aliq.pis) / CEM,
        f"{_pct(aliq.pis)} × {_brl(base_pis_cofins)} ({nota_base})",
        zero or regime_info["fontes_pis"] + fontes_base,
    )
    zero = fontes_zero.get(categoria.id) if categoria.pis_cofins_zero and not aliq.cofins else None
    adiciona(
        "cofins", "Cofins", "federal", aliq.cofins, base_pis_cofins,
        base_pis_cofins * _d(aliq.cofins) / CEM,
        f"{_pct(aliq.cofins)} × {_brl(base_pis_cofins)} ({nota_base})",
        zero or regime_info["fontes_cofins"] + fontes_base,
    )

    if zona_franca and categoria.ipi:
        avisos.append(
            "Produto da Zona Franca de Manaus: IPI isento (Decreto-Lei 288/1967, art. 9º), desde que "
            "cumprido o Processo Produtivo Básico."
        )
    if not servico and categoria.icms is None:
        avisos.append(
            f"ICMS: usamos a alíquota modal de {estado.nome} ({_pct(estado.icms)}"
            + (f" + {_pct(estado.fcp)} de FCP" if estado.fcp else "")
            + "). Alguns produtos têm alíquota própria definida na lei estadual."
        )

    return _resultado(
        p, tributos, avisos, aliq, padrao, regime, zona_franca, margem_varejo, data,
        erro="As alíquotas informadas somam 100% ou mais do preço.",
    )


def _resultado(
    p, tributos, avisos, aliquotas, padrao, regime, zona_franca, margem_varejo, data,
    erro, unidade=None,
) -> Resultado:
    total = sum((_d(t.valor) for t in tributos), Decimal(0))
    sem_impostos = p - total
    if sem_impostos <= 0:
        raise ErroCalculo(erro)
    return Resultado(
        preco=float(_reais(p)),
        total_impostos=float(total),
        valor_sem_impostos=float(_reais(sem_impostos)),
        carga_sobre_preco=_percentual(total, p),
        acrescimo_sobre_valor=_percentual(total, sem_impostos),
        tributos=tributos,
        aliquotas=aliquotas,
        padrao=padrao,
        regime=regime,
        zona_franca=zona_franca,
        margem_varejo=margem_varejo,
        avisos=avisos,
        unidade=unidade,
        data=data.isoformat(),
    )
