from datetime import date, datetime, timezone

import pytest

from app import calculo, dados
from app.calculo import ErroCalculo, calcular

HOJE = date(2026, 11, 8)


def valores(resultado):
    return {t.codigo: t.valor for t in resultado.tributos}


def test_roupa_em_sp_tem_icms_por_dentro_e_pis_cofins_sem_icms():
    r = calcular(100, "camiseta", "SP")
    assert valores(r) == {"icms": 18.0, "ipi": 0.0, "pis": 1.35, "cofins": 6.23}
    assert r.total_impostos == 25.58
    assert r.carga_sobre_preco == 25.58
    assert r.valor_sem_impostos == 74.42
    assert r.acrescimo_sobre_valor == 34.37


def test_smartphone_inclui_ipi_por_fora():
    r = calcular(1000, "smartphone", "SP")
    assert valores(r) == {"icms": 180.0, "ipi": 130.43, "pis": 13.53, "cofins": 62.32}
    assert r.total_impostos == 386.28
    assert r.carga_sobre_preco == 38.63


def test_zona_franca_zera_ipi():
    r = calcular(1000, "smartphone", "SP", zona_franca=True)
    assert valores(r)["ipi"] == 0
    assert r.total_impostos == 255.85
    assert any("Zona Franca" in aviso for aviso in r.avisos)


def test_margem_da_loja_reduz_base_do_ipi():
    r = calcular(1000, "smartphone", "SP", margem_varejo=100)
    assert valores(r)["ipi"] == 65.22


def test_rio_de_janeiro_soma_fcp_ao_icms():
    r = calcular(100, "camiseta", "RJ")
    assert valores(r) == {"icms": 20.0, "fcp": 2.0, "ipi": 0.0, "pis": 1.29, "cofins": 5.93}
    assert r.total_impostos == 29.22


def test_servico_usa_iss_e_pis_cofins_cumulativo():
    r = calcular(100, "servico", "SP")
    assert r.regime == "cumulativo"
    assert valores(r) == {"iss": 5.0, "pis": 0.65, "cofins": 3.0}
    assert r.total_impostos == 8.65


def test_tema_69_do_stf_so_e_citado_quando_o_icms_sai_da_base():
    fontes_servico = {t.codigo: t.fontes for t in calcular(100, "servico", "SP").tributos}
    fontes_produto = {t.codigo: t.fontes for t in calcular(100, "camiseta", "SP").tributos}
    assert "stf69" not in fontes_servico["pis"]
    assert "stf69" in fontes_produto["cofins"]


def test_livro_e_imune():
    r = calcular(50, "livro", "SP")
    assert r.total_impostos == 0
    assert r.carga_sobre_preco == 0


def test_cesta_basica_usa_icms_reduzido_sem_fcp():
    r = calcular(100, "cesta_basica", "RJ")
    assert valores(r) == {"icms": 7.0, "ipi": 0.0, "pis": 0.0, "cofins": 0.0}


def test_regime_cumulativo_para_mercadoria():
    r = calcular(100, "camiseta", "SP", regime="cumulativo")
    assert valores(r)["pis"] == 0.53  # 82 × 0,65%
    assert valores(r)["cofins"] == 2.46  # 82 × 3%


def test_ajustes_substituem_aliquotas_da_lei():
    r = calcular(100, "camiseta", "SP", ajustes={"icms": 12, "ipi": None})
    assert valores(r) == {"icms": 12.0, "ipi": 0.0, "pis": 1.45, "cofins": 6.69}
    assert r.padrao.icms == 18
    assert r.aliquotas.icms == 12


def test_aliquotas_que_somam_100_por_cento_sao_rejeitadas():
    with pytest.raises(ErroCalculo):
        calcular(100, "camiseta", "SP", ajustes={"icms": 100})


@pytest.mark.parametrize(
    "argumentos",
    [
        {"categoria_id": "nada", "uf": "SP"},
        {"categoria_id": "camiseta", "uf": "XX"},
        {"categoria_id": "camiseta", "uf": "SP", "regime": "simples"},
    ],
)
def test_entradas_desconhecidas(argumentos):
    with pytest.raises(ErroCalculo):
        calcular(100, **argumentos)


@pytest.mark.parametrize("categoria", list(dados.CATEGORIAS))
@pytest.mark.parametrize("uf", ["SP", "RJ"])
def test_todas_as_fontes_citadas_existem(categoria, uf):
    assert set(dados.CATEGORIAS[categoria].fontes) <= set(dados.FONTES)
    r = calcular(100, categoria, uf, zona_franca=True)
    for tributo in r.tributos:
        assert tributo.fontes, tributo.codigo
        assert set(tributo.fontes) <= set(dados.FONTES)


def test_gasolina_com_pis_cofins_e_cide_zerados_ate_9_de_novembro():
    r = calcular(6.50, "gasolina", "SP", data=HOJE)
    assert valores(r) == {"icms": 1.57, "pis": 0.0, "cofins": 0.0, "cide": 0.0}
    assert r.carga_sobre_preco == 24.15
    assert r.unidade == "litro"
    assert any("09/11/2026" in aviso for aviso in r.avisos)


def test_gasolina_volta_a_pagar_tributos_federais_sobre_a_parte_fossil_do_e32():
    r = calcular(6.50, "gasolina", "SP", data=date(2026, 11, 10))
    # 68% de gasolina A: PIS 0,1411 × 0,68; Cofins 0,6514 × 0,68; Cide 0,10 × 0,68
    assert valores(r) == {"icms": 1.57, "pis": 0.10, "cofins": 0.44, "cide": 0.07}
    assert r.total_impostos == 2.18


def test_gasolina_no_periodo_do_decreto_13116():
    r = calcular(6.50, "gasolina", "SP", data=date(2026, 9, 20))
    assert valores(r) == {"icms": 1.57, "pis": 0.02, "cofins": 0.09, "cide": 0.07}


def test_gasolina_volta_ao_e30_quando_acaba_o_e32():
    r = calcular(6.50, "gasolina", "SP", data=date(2027, 2, 1))
    assert valores(r) == {"icms": 1.57, "pis": 0.10, "cofins": 0.46, "cide": 0.07}


def test_icms_dos_combustiveis_e_igual_em_todos_os_estados():
    assert valores(calcular(6.50, "gasolina", "SP", data=HOJE)) == valores(
        calcular(6.50, "gasolina", "MA", data=HOJE)
    )


def test_diesel_b15():
    r = calcular(6.00, "diesel", "SP", data=HOJE)
    assert valores(r) == {"icms": 1.17, "pis": 0.05, "cofins": 0.25, "cide": 0.0}
    assert r.total_impostos == 1.47
    assert any("01/02/2027" in aviso for aviso in r.avisos)


def test_diesel_com_pis_cofins_zerado_em_abril_e_icms_novo_em_2027():
    assert valores(calcular(6.00, "diesel", "SP", data=date(2026, 4, 1)))["pis"] == 0
    assert valores(calcular(6.00, "diesel", "SP", data=date(2027, 2, 1)))["icms"] == 1.30


def test_botijao_de_gas_paga_icms_por_quilo():
    r = calcular(120, "glp", "SP", data=HOJE)
    assert valores(r) == {"icms": 19.11, "pis": 0.0, "cofins": 0.0, "cide": 0.0}
    assert r.carga_sobre_preco == 15.93
    assert valores(calcular(120, "glp", "SP", data=date(2027, 2, 1)))["icms"] == 20.02


def test_preco_menor_que_o_imposto_fixo_e_rejeitado():
    with pytest.raises(ErroCalculo, match="litro"):
        calcular(1.00, "gasolina", "SP", data=HOJE)


def test_hoje_usa_o_horario_de_brasilia(monkeypatch):
    # 9/11 às 23h30 em Brasília já é 10/11 em UTC, horário do servidor.
    class Relogio(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime(2026, 11, 10, 2, 30, tzinfo=timezone.utc).astimezone(tz)

    monkeypatch.setattr(calculo, "datetime", Relogio)
    assert calculo.hoje() == date(2026, 11, 9)


def test_todos_os_estados_tem_icms_modal_entre_17_e_23():
    assert len(dados.ESTADOS) == 27
    assert all(17 <= e.icms <= 23 for e in dados.ESTADOS.values())
