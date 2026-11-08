# Preço Real

Calculadora web (FastAPI) que mostra quanto do preço de um produto ou serviço no Brasil é imposto:
ICMS, IPI, PIS, Cofins e ISS, com o valor em reais, a porcentagem sobre o preço e o link da lei de
cada alíquota.

## Como rodar

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows (no Linux/macOS: source .venv/bin/activate)
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

Abra http://localhost:8000. A API fica documentada em http://localhost:8000/docs.

Testes: `pytest`

## Deploy (Render)

O arquivo [`render.yaml`](render.yaml) descreve o serviço: plano gratuito, região Virgínia (a mais
perto do Brasil), Python 3.11.9 e health check em `/saude`. Para publicar:

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/kauaDev22/preco-real)

Ou, no painel do Render, escolha **New → Blueprint**, conecte o repositório e clique em **Apply**.

Cada push na branch principal publica uma nova versão. No plano gratuito o serviço dorme após
15 minutos sem acesso; a primeira visita depois disso leva cerca de um minuto.

A data usada nos valores dos combustíveis segue o horário de Brasília, mesmo com o servidor em UTC.

## API

`POST /api/calcular`

```json
{ "preco": 3499.90, "categoria": "smartphone", "uf": "SP", "zona_franca": false }
```

Campos opcionais: `regime` (`nao_cumulativo` ou `cumulativo`), `margem_varejo` (%) e `ajustes`
(`icms`, `fcp`, `ipi`, `pis`, `cofins`, `iss`, em %) para trocar alíquotas.

Também há `GET /api/categorias`, `GET /api/estados` e `GET /api/fontes`.

## Como o cálculo funciona

| Tributo | Fórmula | Base legal |
|---|---|---|
| ICMS | preço × alíquota modal do estado (+ FCP) — “por dentro” | LC 87/1996, art. 13, § 1º, I |
| PIS/Cofins | (preço − ICMS) × alíquota | Leis 10.637/2002 e 10.833/2003; STF Tema 69 |
| IPI | preço × t / ((1 + t) × (1 + margem)) — “por fora” | TIPI (Decreto 11.158/2022) |
| ISS | preço × alíquota do município | LC 116/2003 |
| Combustíveis | ICMS, PIS/Cofins e Cide em R$ fixos por litro (ou kg); os federais só sobre a parte fóssil da mistura | LC 192/2022; Convênios ICMS 112/25 e 113/25; Decretos 5.059 e 5.060/2004 |

Para combustíveis, `preco` é o preço do litro (ou do botijão de 13 kg) e o cálculo usa os valores
vigentes na data (campo opcional `data`, padrão hoje).

O escopo segue a Lei 12.741/2012 (Lei da Transparência Fiscal). IR/CSLL das empresas e encargos
sobre a folha não entram, e Simples Nacional, substituição tributária e importação não são
modelados.

## Onde atualizar os dados

Tudo fica em [`app/dados.py`](app/dados.py):

- `ESTADOS`: alíquota modal de ICMS de cada estado (conferida em novembro de 2026).
- `CATEGORIAS`: produtos, código NCM e IPI da TIPI (versão atualizada até o ADE RFB nº 1/2026).
- `COMBUSTIVEIS`: valores por litro/kg com período de vigência (`Periodo`). Mudam com frequência:
  o PIS/Cofins e a Cide da gasolina estão zerados só até 09/11/2026 (Decreto 13.134/2026), a
  mistura E32 vale até 27/01/2027 e o ICMS de diesel e GLP sobe em 01/02/2027. Ao sair um novo
  decreto ou convênio, acrescente um `Periodo` com as datas.
- `FONTES`: links oficiais (Planalto, Receita Federal, CONFAZ, CNPE, STF).

Pela reforma tributária (EC 132/2023), a partir de 2027 a CBS substitui PIS/Cofins e o IPI é
zerado, exceto para produtos com industrialização incentivada na Zona Franca de Manaus — os dados
precisarão ser revistos nessa data.
