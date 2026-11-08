import unicodedata
from dataclasses import asdict
from datetime import date
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from . import dados
from .calculo import ErroCalculo, calcular

PASTA = Path(__file__).parent

app = FastAPI(
    title="Preço Real",
    description="Calcula quanto do preço de um produto no Brasil é imposto, com as fontes oficiais.",
    version="1.0.0",
)
app.mount("/static", StaticFiles(directory=PASTA / "static"), name="static")
templates = Jinja2Templates(directory=PASTA / "templates")
templates.env.filters["pct"] = lambda valor: f"{valor:g}".replace(".", ",") + "%"


class Ajustes(BaseModel):
    icms: float | None = Field(None, ge=0, le=100)
    fcp: float | None = Field(None, ge=0, le=100)
    ipi: float | None = Field(None, ge=0, le=400)
    pis: float | None = Field(None, ge=0, le=100)
    cofins: float | None = Field(None, ge=0, le=100)
    iss: float | None = Field(None, ge=0, le=100)


class PedidoCalculo(BaseModel):
    preco: float = Field(..., gt=0, le=1_000_000_000, description="Preço pago pelo consumidor, em reais")
    categoria: str = Field(..., examples=["smartphone"])
    uf: str = Field(..., min_length=2, max_length=2, examples=["SP"])
    regime: Literal["nao_cumulativo", "cumulativo"] | None = None
    zona_franca: bool = False
    margem_varejo: float = Field(0, ge=0, le=1000, description="Margem da loja sobre o preço de fábrica, em %")
    ajustes: Ajustes | None = None
    data: date | None = Field(None, description="Data das alíquotas de combustíveis; padrão: hoje")


def _sem_acento(texto: str) -> str:
    return unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode().lower()


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def inicio(request: Request):
    grupos: dict[str, list[dados.Categoria]] = {}
    for categoria in dados.CATEGORIAS.values():
        grupos.setdefault(categoria.grupo, []).append(categoria)
    fontes = [
        (titulo, [(chave, dados.FONTES[chave]) for chave in chaves])
        for titulo, chaves in dados.GRUPOS_FONTES
    ]
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "grupos": grupos,
            "unidades": {chave: c.unidade for chave, c in dados.COMBUSTIVEIS.items()},
            "estados": sorted(dados.ESTADOS.values(), key=lambda e: _sem_acento(e.nome)),
            "regimes": dados.REGIMES,
            "fontes": fontes,
            "fontes_js": {chave: {"titulo": f.titulo, "url": f.url} for chave, f in dados.FONTES.items()},
            "data_referencia": dados.DATA_REFERENCIA,
        },
    )


@app.get("/saude", include_in_schema=False)
def saude():
    return {"status": "ok"}


@app.get("/api/estados")
def listar_estados():
    return [asdict(e) for e in dados.ESTADOS.values()]


@app.get("/api/categorias")
def listar_categorias():
    return [asdict(c) for c in dados.CATEGORIAS.values()]


@app.get("/api/fontes")
def listar_fontes():
    return {chave: asdict(f) for chave, f in dados.FONTES.items()}


@app.post("/api/calcular")
def calcular_preco(pedido: PedidoCalculo):
    try:
        resultado = calcular(
            preco=pedido.preco,
            categoria_id=pedido.categoria,
            uf=pedido.uf,
            regime=pedido.regime,
            zona_franca=pedido.zona_franca,
            ajustes=pedido.ajustes.model_dump() if pedido.ajustes else None,
            margem_varejo=pedido.margem_varejo,
            data=pedido.data,
        )
    except ErroCalculo as erro:
        raise HTTPException(status_code=422, detail=str(erro))
    return asdict(resultado)
