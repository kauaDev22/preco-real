(() => {
  const $ = (seletor) => document.querySelector(seletor);
  const brl = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });
  const num = (valor) => valor.toLocaleString("pt-BR", { maximumFractionDigits: 2 });
  const cor = (codigo) => `var(--c-${codigo})`;
  const NOME_CURTO = { fcp: "FCP", cide: "Cide" };
  const LITROS_TANQUE = 50;

  const campos = {
    preco: $("#preco"),
    categoria: $("#categoria"),
    uf: $("#uf"),
    regime: $("#regime"),
    zonaFranca: $("#zona_franca"),
    margem: $("#margem_varejo"),
  };
  const inputsAjuste = [...document.querySelectorAll("[data-ajuste]")];
  // Alíquotas alteradas à mão; o resto vem da lei.
  let ajustes = {};
  let unidadeExibida = null;
  let ultimoPedido = 0;
  let espera;

  function lerPreco(texto) {
    let limpo = texto.replace(/[R$\s]/g, "");
    if (limpo.includes(",")) limpo = limpo.replace(/\./g, "").replace(",", ".");
    const valor = Number(limpo);
    return limpo && Number.isFinite(valor) && valor > 0 ? valor : null;
  }

  function el(tag, props = {}, ...filhos) {
    const elemento = Object.assign(document.createElement(tag), props);
    elemento.append(...filhos.filter((f) => f !== null && f !== undefined));
    return elemento;
  }

  function linkFonte(chave) {
    const fonte = window.FONTES[chave];
    if (!fonte) return null;
    return el("a", {
      href: fonte.url,
      target: "_blank",
      rel: "noopener noreferrer",
      title: fonte.titulo,
      textContent: fonte.titulo.split(" — ")[0],
    });
  }

  function tipoAtual() {
    return campos.categoria.selectedOptions[0].dataset.tipo;
  }

  function atualizarFormulario() {
    const opcao = campos.categoria.selectedOptions[0];
    const tipo = opcao.dataset.tipo;
    const ipi = Number(opcao.dataset.ipi);
    const unidade = opcao.dataset.unidade;
    const combustivel = tipo === "combustivel";

    if (combustivel) {
      const porLitro = unidade === "litro";
      $("#preco-rotulo").textContent = porLitro ? "Preço do litro" : "Preço do botijão (13 kg)";
      $("#preco-ajuda").textContent = porLitro ? "O preço na bomba do posto." : "O preço na revenda de gás.";
      $("#categoria-info").textContent = `Tributos em valor fixo por ${porLitro ? "litro" : "quilo"}, iguais em todo o país`;
    } else {
      $("#preco-rotulo").textContent = "Preço pago";
      $("#preco-ajuda").textContent = "O valor final, como aparece na etiqueta ou na nota.";
      $("#categoria-info").textContent =
        tipo === "servico" ? "Serviço — tributado pelo ISS" : `NCM ${opcao.dataset.ncm} · IPI de ${num(ipi)}% na TIPI`;
    }
    $("#campo-uf").hidden = combustivel;
    $("#campo-regime").hidden = combustivel;
    $("#ajustes").hidden = combustivel;
    const semZfm = tipo !== "mercadoria" || ipi === 0;
    $("#campo-zfm").hidden = semZfm;
    if (semZfm) campos.zonaFranca.checked = false;
    document.querySelectorAll(".grade-ajustes [data-tipo]").forEach((campo) => {
      campo.hidden = campo.dataset.tipo !== tipo;
    });
    unidadeExibida = unidade || "valor";
  }

  function salvarNaUrl() {
    const params = new URLSearchParams({
      preco: campos.preco.value.trim(),
      produto: campos.categoria.value,
      uf: campos.uf.value,
    });
    if (campos.zonaFranca.checked) params.set("zfm", "1");
    history.replaceState(null, "", `?${params}`);
  }

  function lerUrl() {
    const params = new URLSearchParams(location.search);
    if (params.has("preco")) campos.preco.value = params.get("preco");
    const produto = params.get("produto");
    if (produto && campos.categoria.querySelector(`option[value="${CSS.escape(produto)}"]`)) {
      campos.categoria.value = produto;
    }
    const uf = (params.get("uf") || "").toUpperCase();
    if (uf && campos.uf.querySelector(`option[value="${CSS.escape(uf)}"]`)) campos.uf.value = uf;
    campos.regime.value = tipoAtual() === "servico" ? "cumulativo" : "nao_cumulativo";
    atualizarFormulario();
    campos.zonaFranca.checked = params.get("zfm") === "1" && !$("#campo-zfm").hidden;
  }

  function mostrarMensagem(texto, erro = false) {
    $("#conteudo").hidden = true;
    const vazio = $("#vazio");
    vazio.hidden = false;
    vazio.textContent = texto;
    vazio.classList.toggle("erro", erro);
  }

  function mensagemDeErro(corpo) {
    if (typeof corpo?.detail === "string") return corpo.detail;
    if (Array.isArray(corpo?.detail) && corpo.detail.length) return `Valor inválido: ${corpo.detail[0].msg}`;
    return "Não foi possível calcular.";
  }

  function agendar() {
    clearTimeout(espera);
    espera = setTimeout(calcular, 200);
  }

  async function calcular() {
    const preco = lerPreco(campos.preco.value);
    campos.preco.classList.toggle("invalido", preco === null && campos.preco.value.trim() !== "");
    salvarNaUrl();
    if (preco === null) {
      mostrarMensagem("Digite um preço para ver o cálculo.");
      return;
    }

    const pedido = {
      preco,
      categoria: campos.categoria.value,
      uf: campos.uf.value,
      regime: campos.regime.value,
      zona_franca: campos.zonaFranca.checked,
      margem_varejo: Number(campos.margem.value) || 0,
      ajustes,
    };
    const id = ++ultimoPedido;
    try {
      const resposta = await fetch("/api/calcular", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(pedido),
      });
      const corpo = await resposta.json();
      if (id !== ultimoPedido) return;
      if (!resposta.ok) {
        mostrarMensagem(mensagemDeErro(corpo), true);
        return;
      }
      renderizar(corpo);
    } catch {
      if (id === ultimoPedido) mostrarMensagem("Não foi possível calcular agora. Tente de novo.", true);
    }
  }

  function renderizar(r) {
    $("#vazio").hidden = true;
    $("#conteudo").hidden = false;

    $("#total").textContent = brl.format(r.total_impostos);
    $("#carga").textContent = `${num(r.carga_sobre_preco)}%`;
    $("#total-tabela").textContent = brl.format(r.total_impostos);
    $("#carga-tabela").textContent = `${num(r.carga_sobre_preco)}%`;
    let semImpostos =
      `Sem impostos, custaria ${brl.format(r.valor_sem_impostos)}. ` +
      `Os impostos acrescentam ${num(r.acrescimo_sobre_valor)}% a esse valor.`;
    if (r.unidade === "litro") {
      semImpostos += ` Num tanque de ${LITROS_TANQUE} litros, são ${brl.format(r.total_impostos * LITROS_TANQUE)} em impostos.`;
    }
    $("#sem-impostos").textContent = semImpostos;

    const comValor = r.tributos.filter((t) => t.valor > 0);
    const produtoPct = 100 - r.carga_sobre_preco;
    const barra = $("#barra");
    barra.replaceChildren(
      el("span", { style: `width:${produtoPct}%;background:var(--c-produto)`, title: "Produto sem impostos" }),
      ...comValor.map((t) =>
        el("span", { style: `width:${t.percentual_do_preco}%;background:${cor(t.codigo)}`, title: `${t.nome}: ${brl.format(t.valor)}` }),
      ),
    );
    barra.setAttribute(
      "aria-label",
      `Produto sem impostos ${num(produtoPct)}%` + comValor.map((t) => `, ${t.nome} ${num(t.percentual_do_preco)}%`).join(""),
    );
    $("#legenda").replaceChildren(
      el("li", {}, el("i", { style: "background:var(--c-produto)" }), `Produto ${num(produtoPct)}%`),
      ...comValor.map((t) =>
        el("li", {}, el("i", { style: `background:${cor(t.codigo)}` }), `${NOME_CURTO[t.codigo] || t.nome} ${num(t.percentual_do_preco)}%`),
      ),
    );

    $("#linhas").replaceChildren(
      ...r.tributos.map((t) =>
        el(
          "tr",
          { className: t.valor > 0 ? "" : "tributo--zero" },
          el(
            "td",
            {},
            el("span", { className: "tributo__nome" }, el("i", { style: `background:${cor(t.codigo)}` }), t.nome),
            el("span", { className: "tributo__esfera", textContent: t.esfera }),
            el("span", { className: "tributo__calculo", textContent: t.calculo }),
            el("span", { className: "tributo__fontes" }, ...t.fontes.map(linkFonte)),
          ),
          el("td", { className: "num", textContent: t.aliquota_texto }),
          el("td", { className: "num", textContent: brl.format(t.valor) }),
          el("td", { className: "num", textContent: `${num(t.percentual_do_preco)}%` }),
        ),
      ),
    );

    $("#avisos").replaceChildren(...r.avisos.map((aviso) => el("li", { textContent: aviso })));

    if (r.aliquotas) {
      for (const input of inputsAjuste) {
        if (input !== document.activeElement) input.value = r.aliquotas[input.dataset.ajuste];
      }
    }
  }

  campos.preco.addEventListener("input", agendar);
  campos.margem.addEventListener("input", agendar);
  campos.categoria.addEventListener("change", () => {
    ajustes = {};
    const tipo = tipoAtual();
    campos.regime.value = tipo === "servico" ? "cumulativo" : "nao_cumulativo";
    // Preço de produto não serve como preço do litro, nem o do litro como o do botijão.
    if ((campos.categoria.selectedOptions[0].dataset.unidade || "valor") !== unidadeExibida) {
      campos.preco.value = "";
      campos.preco.focus();
    }
    atualizarFormulario();
    calcular();
  });
  campos.uf.addEventListener("change", () => {
    delete ajustes.icms;
    delete ajustes.fcp;
    calcular();
  });
  campos.regime.addEventListener("change", () => {
    delete ajustes.pis;
    delete ajustes.cofins;
    calcular();
  });
  campos.zonaFranca.addEventListener("change", () => {
    delete ajustes.ipi;
    calcular();
  });
  for (const input of inputsAjuste) {
    input.addEventListener("input", () => {
      const valor = input.value.trim();
      if (valor === "" || !Number.isFinite(Number(valor))) delete ajustes[input.dataset.ajuste];
      else ajustes[input.dataset.ajuste] = Number(valor);
      agendar();
    });
  }
  $("#restaurar").addEventListener("click", () => {
    ajustes = {};
    campos.margem.value = 0;
    calcular();
  });
  $("#form").addEventListener("submit", (evento) => {
    evento.preventDefault();
    calcular();
  });

  lerUrl();
  calcular();
})();
