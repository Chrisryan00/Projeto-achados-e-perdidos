/* AI responses are rendered as text; only server-validated catalog IDs become links. */
const assistantForm = byId("assistant-form");
const assistantResults = byId("assistant-results");
const assistantMode = () => new FormData(assistantForm).get("mode");

async function openCatalogItem(id) {
  state.kind = "";
  state.status = "all";
  state.source = "all";
  state.mineOnly = false;
  state.favoritesOnly = false;
  byId("search-input").value = "";
  byId("category-filter").value = "";
  byId("source-filter").value = "all";
  byId("favorites-filter").setAttribute("aria-pressed", "false");
  byId("my-posts-button").classList.remove("selected");
  byId("my-posts-button").setAttribute("aria-pressed", "false");
  document.querySelectorAll(".filter-tab").forEach((tab) => tab.classList.toggle("active", !tab.dataset.kind));
  document.querySelectorAll(".status-tab").forEach((tab) => tab.classList.toggle("active", tab.dataset.status === "all"));
  await loadItems();
  if (!state.items.some((item) => item.id === id)) {
    try {
      const response = await fetch(`${API}/${id}`);
      const result = await response.json();
      if (!response.ok) throw new Error(result.error?.message || "Anúncio indisponível.");
      state.items.push(result.item);
      render(state.items);
    } catch (error) {
      setMessage(error.message, true);
      return;
    }
  }
  const card = byId(`item-${id}`);
  if (card) {
    card.scrollIntoView({ behavior: "smooth", block: "center" });
    card.classList.add("item-highlight");
    setTimeout(() => card.classList.remove("item-highlight"), 4000);
  } else setMessage("Este anúncio não está disponível.", true);
}

assistantForm.addEventListener("change", () => {
  byId("radar-search-options").hidden = assistantMode() !== "search";
});
document.querySelectorAll("[data-example]").forEach((button) => button.addEventListener("click", () => {
  assistantForm.elements.mode.value = button.dataset.mode || "search";
  byId("assistant-text").value = button.dataset.example;
  byId("radar-search-options").hidden = assistantMode() !== "search";
  byId("assistant-text").focus();
}));

fetch("/api/v1/ai/status").then(async (response) => {
  if (!response.ok) throw new Error();
  const status = await response.json();
  byId("ai-status").textContent = status.configured ? "✦ Gemini configurado" : "○ IA aguardando ativação";
  byId("ai-status").title = status.message;
  byId("ai-status").classList.toggle("is-configured", status.configured);
}).catch(() => { byId("ai-status").textContent = "Não foi possível verificar a IA"; });

assistantForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const button = byId("assistant-submit");
  const mode = assistantMode();
  button.disabled = true;
  button.textContent = "Analisando…";
  assistantResults.hidden = false;
  assistantResults.setAttribute("aria-busy", "true");
  assistantResults.replaceChildren(node("p", "", "Consultando o Gemini. Isso pode levar alguns segundos…"));
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 35000);
  try {
    const photo = await compressPhoto(byId("assistant-photo").files[0]);
    const queryText = byId("assistant-text").value;
    const lookingFor = byId("radar-looking-for").value;
    const includeExamples = byId("radar-include-examples").checked;
    const response = await fetch("/api/v1/ai/assist", { method: "POST", signal: controller.signal,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mode, text: queryText, photo, lookingFor, includeExamples, consent: byId("assistant-consent").checked }) });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error?.message || "Não foi possível consultar a IA.");
    assistantResults.replaceChildren(node("span", "ai-result-label", "✦ RESPOSTA DO GEMINI"), node("p", "assistant-answer", result.message));
    if (mode === "search") assistantResults.append(node("p", "radar-scope", `${result.catalogCount} anúncios em aberto analisados · ${result.includesExamples ? "inclui exemplos fictícios" : "somente comunidade"} · fotos dos anúncios não analisadas`));
    (result.matches || []).forEach((item) => {
      const evidence = node("article", "radar-evidence");
      const link = node("button", "assistant-match");
      link.type = "button";
      link.append(node("strong", "", item.title), node("span", "", `${item.kind === "found" ? "Encontrado" : "Perdido"} · ${item.location}${item.demo ? " · Exemplo fictício" : ""} →`));
      link.addEventListener("click", () => openCatalogItem(item.id));
      evidence.append(link);
      const analysis = result.assessments?.find((entry) => entry.id === item.id);
      if (analysis) {
        for (const [field, title] of [["signals", "O que combina"], ["uncertainties", "O que falta confirmar"], ["questions", "Pergunte antes de devolver"]]) {
          if (!analysis[field]?.length) continue;
          const section = node("div", `evidence-section evidence-${field}`);
          section.append(node("strong", "", title));
          const list = node("ul", "");
          analysis[field].forEach((entry) => list.append(node("li", "", entry)));
          section.append(list);
          evidence.append(section);
        }
      } else evidence.append(node("p", "radar-scope", "Confira características, local e data diretamente com quem publicou."));
      const message = node("button", "utility-button", "Copiar mensagem para conferir →");
      message.type = "button";
      message.addEventListener("click", async () => {
        const text = `Olá! Vi o anúncio "${item.title}" no CESMAC Achados & Perdidos. Podemos comparar os detalhes do objeto? ${analysis?.questions?.[0] || "Você consegue descrever alguma característica específica?"}`;
        try { await navigator.clipboard.writeText(text); message.textContent = "Mensagem copiada ✓"; }
        catch { window.prompt("Copie a mensagem e envie pelo contato do anúncio:", text); }
      });
      evidence.append(message);
      assistantResults.append(evidence);
    });
    if (mode === "search" && !result.matches?.length) assistantResults.append(node("p", "", "Nenhum item foi selecionado no catálogo em aberto. Você pode publicar um anúncio ou tentar a busca tradicional."));
    if (mode === "search" && result.followUpQuestions?.length) {
      const followup = node("div", "radar-followup");
      followup.append(node("strong", "", "Vamos melhorar as pistas?"), node("p", "radar-scope", "Complete o que souber. Suas respostas serão enviadas na próxima consulta que você fizer."));
      const inputs = result.followUpQuestions.map((question) => {
        const label = node("label", "field", question);
        const input = node("input", "");
        input.type = "text";
        input.maxLength = 180;
        input.placeholder = "Responda sem dados pessoais";
        label.append(input);
        followup.append(label);
        return { question, input };
      });
      const refine = node("button", "button button-outline", "Acrescentar respostas ao relato ↑");
      refine.type = "button";
      refine.addEventListener("click", () => {
        const additions = inputs.filter(({input}) => input.value.trim()).map(({question, input}) => `${question} ${input.value.trim()}`).join("\n");
        if (!additions) return inputs[0].input.focus();
        const combined = `${queryText}\n${additions}`;
        if (combined.length > 1500) { refine.textContent = "Encurte as respostas: o relato aceita 1500 caracteres."; return; }
        byId("assistant-text").value = combined;
        byId("assistant-text").focus();
        byId("assistant-text").scrollIntoView({behavior: "smooth", block: "center"});
        refine.textContent = "Pronto: revise o relato e consulte o Radar ↑";
      });
      followup.append(refine);
      assistantResults.append(followup);
    }
    if (mode === "search" && result.searchPlan?.length) {
      const plan = node("div", "radar-plan");
      plan.append(node("strong", "", "Seu próximo passo"));
      const steps = node("ol", "assistant-tips");
      result.searchPlan.forEach((step) => steps.append(node("li", "", step)));
      const save = node("button", "button button-dark", "Salvar meu plano de busca ✓");
      save.type = "button";
      save.addEventListener("click", () => {
        const record = {text: queryText, lookingFor, includeExamples, savedAt: new Date().toISOString(), steps: result.searchPlan.map((text) => ({text, done: false}))};
        try { localStorage.setItem(notebookKey, JSON.stringify(record)); renderNotebook(); save.textContent = "Plano salvo neste navegador ✓"; }
        catch { save.textContent = "Não foi possível salvar neste navegador."; }
      });
      plan.append(steps, save);
      assistantResults.append(plan);
    }
    if (result.tips?.length) {
      const tips = node("ul", "assistant-tips");
      result.tips.forEach((tip) => tips.append(node("li", "", tip)));
      assistantResults.append(tips);
    }
    if (result.draft) {
      const preview = node("div", "draft-preview");
      preview.append(node("strong", "", result.draft.title), node("p", "", result.draft.description), node("small", "", `${result.draft.category} · ${result.draft.location || "Local a preencher"}`));
      const use = node("button", "button button-dark", "Revisar e completar anúncio →");
      use.type = "button";
      use.addEventListener("click", () => {
        const form = byId("report-form");
        for (const field of ["title", "description", "category", "location", "kind"]) form.elements[field].value = result.draft[field];
        // Keep a selected photo attached only with an explicit review in the report form.
        byId("dialog-title").textContent = "Revise o rascunho da IA";
        openReport();
        byId("form-error").textContent = "Confira os detalhes, informe a data e seus contatos. Para publicar a foto, selecione-a também no campo de foto abaixo.";
      });
      preview.append(use);
      assistantResults.append(preview);
    }
  } catch (error) {
    assistantResults.replaceChildren(node("p", "form-error", error.name === "AbortError" ? "A consulta demorou demais. Tente novamente em instantes." : error.message));
    const fallback = node("a", "text-link", "Usar a busca do mural →");
    fallback.href = "#anuncios";
    assistantResults.append(fallback);
  } finally {
    clearTimeout(timer);
    button.disabled = false;
    button.textContent = "Analisar com IA ✦";
    assistantResults.setAttribute("aria-busy", "false");
  }
});

byId("favorites-filter").addEventListener("click", () => {
  state.favoritesOnly = !state.favoritesOnly;
  byId("favorites-filter").setAttribute("aria-pressed", String(state.favoritesOnly));
  render(state.items);
});

const savedSearchKey = "cesmac-saved-searches-v1";
function readSearches() {
  try { const value = JSON.parse(localStorage.getItem(savedSearchKey) || "[]"); return Array.isArray(value) ? value.filter((entry) => entry && typeof entry.q === "string" && typeof entry.category === "string" && ["", "lost", "found"].includes(entry.kind)).slice(0, 6) : []; }
  catch { return []; }
}
function renderSearches() {
  const container = byId("saved-searches");
  container.replaceChildren();
  readSearches().forEach((entry, index) => {
    const chip = node("span", "saved-search-chip");
    const open = node("button", "", entry.q || entry.category || (entry.kind === "lost" ? "Perdidos" : "Encontrados"));
    open.type = "button";
    open.addEventListener("click", () => {
      byId("search-input").value = entry.q;
      byId("category-filter").value = entry.category;
      state.kind = entry.kind;
      state.status = "open";
      state.source = "all";
      state.mineOnly = false;
      state.favoritesOnly = false;
      byId("source-filter").value = "all";
      byId("favorites-filter").setAttribute("aria-pressed", "false");
      byId("my-posts-button").classList.remove("selected");
      byId("my-posts-button").setAttribute("aria-pressed", "false");
      document.querySelectorAll(".filter-tab").forEach((tab) => tab.classList.toggle("active", tab.dataset.kind === state.kind));
      document.querySelectorAll(".status-tab").forEach((tab) => tab.classList.toggle("active", tab.dataset.status === "open"));
      loadItems();
    });
    const remove = node("button", "", "×");
    remove.type = "button";
    remove.setAttribute("aria-label", `Remover busca ${open.textContent}`);
    remove.addEventListener("click", () => {
      try { localStorage.setItem(savedSearchKey, JSON.stringify(readSearches().filter((_, position) => position !== index))); renderSearches(); }
      catch { setMessage("Não foi possível atualizar as buscas salvas.", true); }
    });
    chip.append(open, remove);
    container.append(chip);
  });
}
byId("save-search").addEventListener("click", () => {
  const entry = { q: byId("search-input").value.trim(), category: byId("category-filter").value, kind: state.kind };
  if (!entry.q && !entry.category && !entry.kind) return setMessage("Digite um termo ou escolha uma categoria ou tipo antes de salvar.");
  try {
    const entries = readSearches().filter((old) => JSON.stringify(old) !== JSON.stringify(entry));
    localStorage.setItem(savedSearchKey, JSON.stringify([entry, ...entries].slice(0, 6)));
    renderSearches();
    setMessage("Busca salva. Clique nela para consultar o mural novamente; não são enviados alertas.");
  } catch { setMessage("Não foi possível salvar a busca neste navegador.", true); }
});
renderSearches();
const notebookKey = "cesmac-reunion-notebook-v1";
function readNotebook() {
  try {
    const value = JSON.parse(localStorage.getItem(notebookKey) || "null");
    if (!value || typeof value.text !== "string" || value.text.length > 1500 || !["lost", "found"].includes(value.lookingFor) || !Array.isArray(value.steps)) return null;
    return {...value, steps: value.steps.filter((step) => step && typeof step.text === "string" && typeof step.done === "boolean").slice(0, 4)};
  } catch { return null; }
}
function renderNotebook() {
  const record = readNotebook();
  byId("search-notebook").hidden = !record;
  if (!record) return;
  byId("notebook-summary").textContent = `${record.steps.filter((step) => step.done).length} de ${record.steps.length} passos concluídos · ${record.text.slice(0, 140)}${record.text.length > 140 ? "…" : ""}`;
  byId("notebook-steps").replaceChildren(...record.steps.map((step, index) => {
    const label = node("label", `notebook-step${step.done ? " is-done" : ""}`);
    const check = node("input", "");
    check.type = "checkbox";
    check.checked = step.done;
    check.addEventListener("change", () => {
      const current = readNotebook();
      if (!current?.steps[index] || current.steps[index].text !== step.text) return renderNotebook();
      current.steps[index].done = check.checked;
      try { localStorage.setItem(notebookKey, JSON.stringify(current)); renderNotebook(); }
      catch { check.checked = step.done; setMessage("Não foi possível atualizar o plano salvo.", true); }
    });
    label.append(check, node("span", "", step.text));
    return label;
  }));
}
byId("resume-radar").addEventListener("click", () => {
  const record = readNotebook();
  if (!record) return;
  assistantForm.elements.mode.value = "search";
  byId("radar-search-options").hidden = false;
  byId("assistant-text").value = record.text;
  byId("radar-looking-for").value = record.lookingFor;
  byId("radar-include-examples").checked = record.includeExamples === true;
  byId("assistant-photo").value = "";
  byId("assistant-consent").checked = false;
  assistantResults.hidden = true;
  byId("assistente").scrollIntoView({behavior: "smooth", block: "start"});
  byId("assistant-text").focus({preventScroll: true});
});
function prepareRadar(item) {
  assistantForm.elements.mode.value = "search";
  byId("radar-search-options").hidden = false;
  byId("radar-looking-for").value = item.kind === "lost" ? "found" : "lost";
  byId("radar-include-examples").checked = item.demo;
  byId("assistant-photo").value = "";
  byId("assistant-consent").checked = false;
  // Only public matching metadata is prefilled; never send a publisher's contacts.
  byId("assistant-text").value = `${item.kind === "lost" ? "Perdi" : "Encontrei"} ${item.title}. Categoria: ${item.category}. Local: ${item.location}. Data: ${item.eventDate}. Busque itens do tipo oposto e explique as pistas e dúvidas.`;
  assistantResults.hidden = true;
  byId("assistente").scrollIntoView({behavior: "smooth", block: "start"});
  byId("assistant-text").focus({preventScroll: true});
}
renderNotebook();
const linkedItem = new URLSearchParams(location.search).get("item");
if (linkedItem && /^\d+$/.test(linkedItem)) openCatalogItem(Number(linkedItem));
