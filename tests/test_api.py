from fastapi.testclient import TestClient

from app.main import app

cliente = TestClient(app)


def test_pagina_inicial_lista_fontes_oficiais():
    resposta = cliente.get("/")
    assert resposta.status_code == 200
    assert "Fontes oficiais" in resposta.text
    assert "planalto.gov.br" in resposta.text
    assert "receitafederal" in resposta.text


def test_arquivos_estaticos_usam_caminho_relativo():
    # URL absoluta sairia como http:// atrás do proxy HTTPS e seria bloqueada.
    pagina = cliente.get("/").text
    assert 'href="/static/style.css"' in pagina
    assert 'src="/static/app.js"' in pagina
    assert cliente.get("/static/app.js").status_code == 200


def test_saude():
    assert cliente.get("/saude").json() == {"status": "ok"}


def test_calcular():
    resposta = cliente.post("/api/calcular", json={"preco": 1000, "categoria": "smartphone", "uf": "sp"})
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["total_impostos"] == 386.28
    assert [t["codigo"] for t in corpo["tributos"]] == ["icms", "ipi", "pis", "cofins"]


def test_calcular_com_ajustes():
    resposta = cliente.post(
        "/api/calcular",
        json={"preco": 100, "categoria": "camiseta", "uf": "SP", "ajustes": {"icms": 12}},
    )
    assert resposta.json()["aliquotas"]["icms"] == 12


def test_calcular_combustivel_em_uma_data():
    resposta = cliente.post(
        "/api/calcular", json={"preco": 6.5, "categoria": "gasolina", "uf": "SP", "data": "2026-11-10"}
    )
    corpo = resposta.json()
    assert corpo["total_impostos"] == 2.18
    assert corpo["unidade"] == "litro"
    assert corpo["aliquotas"] is None
    assert corpo["tributos"][0]["aliquota_texto"] == "R$ 1,57/L"


def test_erros_de_entrada_retornam_422():
    assert cliente.post("/api/calcular", json={"preco": 100, "categoria": "camiseta", "uf": "XX"}).status_code == 422
    assert cliente.post("/api/calcular", json={"preco": -1, "categoria": "camiseta", "uf": "SP"}).status_code == 422
    assert cliente.post(
        "/api/calcular", json={"preco": 100, "categoria": "camiseta", "uf": "SP", "ajustes": {"icms": 100}}
    ).status_code == 422


def test_listas():
    assert len(cliente.get("/api/estados").json()) == 27
    assert any(c["id"] == "livro" for c in cliente.get("/api/categorias").json())
    assert "lei12741" in cliente.get("/api/fontes").json()
