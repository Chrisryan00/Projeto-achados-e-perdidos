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
  byId("assistant-photo-field").hidden = assistantMode() !== "draft";
});
document.querySelectorAll("[data-example]").forEach((button) => button.addEventListener("click", () => {
  assistantForm.elements.mode.value = button.dataset.mode || "search";
  byId("assistant-text").value = button.dataset.example;
  byId("assistant-photo-field").hidden = assistantMode() !== "draft";
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
    const photo = mode === "draft" ? await compressPhoto(byId("assistant-photo").files[0]) : "";
    const response = await fetch("/api/v1/ai/assist", { method: "POST", signal: controller.signal,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mode, text: byId("assistant-text").value, photo, consent: byId("assistant-consent").checked }) });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error?.message || "Não foi possível consultar a IA.");
    assistantResults.replaceChildren(node("span", "ai-result-label", "✦ RESPOSTA DO GEMINI"), node("p", "assistant-answer", result.message));
    (result.matches || []).forEach((item) => {
      const link = node("button", "assistant-match");
      link.type = "button";
      link.append(node("strong", "", item.title), node("span", "", `${item.kind === "found" ? "Encontrado" : "Perdido"} · ${item.location}${item.demo ? " · Exemplo fictício" : ""} →`));
      link.addEventListener("click", () => openCatalogItem(item.id));
      assistantResults.append(link);
    });
    if (mode === "search" && !result.matches?.length) assistantResults.append(node("p", "", "Nenhum item foi selecionado no catálogo em aberto. Você pode publicar um anúncio ou tentar a busca tradicional."));
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
const linkedItem = new URLSearchParams(location.search).get("item");
if (linkedItem && /^\d+$/.test(linkedItem)) openCatalogItem(Number(linkedItem));
