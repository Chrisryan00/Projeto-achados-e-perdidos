const API = "/api/v1/items";
const mineKey = "cesmac-lost-found-owned-v1";
const matchFeedbackKey = "cesmac-lost-found-match-feedback-v1";
const categories = {
  "Acessórios": "✦", "Documentos": "▤", "Eletrônicos": "⌁",
  "Material de estudo": "▧", "Roupas e acessórios": "◇", Chaves: "⌕", Outros: "✳",
};
const state = { kind: "", status: "all", mineOnly: false, source: "all", items: [], loading: false };
const byId = (id) => document.getElementById(id);
const grid = byId("items-grid");
const resolvedGrid = byId("resolved-grid");
const owned = () => {
  try { return JSON.parse(localStorage.getItem(mineKey) || "{}"); }
  catch { return {}; }
};
const saveOwned = (value) => localStorage.setItem(mineKey, JSON.stringify(value));
const readMatchFeedback = () => {
  try {
    const value = JSON.parse(localStorage.getItem(matchFeedbackKey) || "{}");
    return value && typeof value === "object" && !Array.isArray(value) ? value : {};
  }
  catch { return {}; }
};

function node(tag, className, text) {
  const element = document.createElement(tag);
  if (className) element.className = className;
  if (text !== undefined) element.textContent = text;
  return element;
}

function formatDate(value) {
  return new Intl.DateTimeFormat("pt-BR", { day: "2-digit", month: "short" }).format(new Date(`${value}T12:00:00`));
}

function setMessage(message, isError = false) {
  const target = byId("page-message");
  target.textContent = message;
  target.classList.toggle("error", isError);
}

function syncMyCount() {
  byId("my-posts-count").textContent = Object.keys(owned()).length;
}

function currentParams() {
  const params = new URLSearchParams();
  params.set("status", state.status);
  if (state.kind) params.set("kind", state.kind);
  if (byId("category-filter").value) params.set("category", byId("category-filter").value);
  if (byId("search-input").value.trim()) params.set("q", byId("search-input").value.trim());
  return params;
}

function addContactActions(actions, item) {
  const contactLabel = item.kind === "lost" ? "Falar com quem perdeu" : "Falar com quem encontrou";
  if (item.contactPhone) {
    const link = node("a", "button button-whatsapp", "WhatsApp");
    let digits = item.contactPhone.replace(/\D/g, "");
    if (digits.length === 10 || digits.length === 11) digits = `55${digits}`;
    link.href = `https://wa.me/${digits}?text=${encodeURIComponent(`Olá, ${item.contactName}! Estou entrando em contato pelo anúncio "${item.title}" no mural de Achados & Perdidos do CESMAC.`)}`;
    link.target = "_blank";
    link.rel = "noopener noreferrer";
    link.setAttribute("aria-label", `${contactLabel} pelo WhatsApp`);
    actions.append(link);
  }
}

function addLocalPhotoControl(actions, item) {
  const input = node("input", "demo-photo-input");
  input.type = "file";
  input.accept = "image/jpeg,image/png,image/webp";
  input.id = `demo-photo-${item.id}`;
  const label = node("label", "demo-photo-upload", item.photoUrl ? "Trocar foto" : "Adicionar foto");
  label.htmlFor = input.id;
  input.addEventListener("change", async () => {
    const file = input.files?.[0];
    if (!file) return;
    label.textContent = "Salvando foto…";
    try {
      const photo = await compressPhoto(file);
      const response = await fetch(`${API}/${item.id}/photo`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ photo }),
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.error?.message || "Não foi possível salvar a foto.");
      await loadItems();
      setMessage("Foto adicionada ao cartão.");
    } catch (error) {
      label.textContent = item.photoUrl ? "Trocar foto" : "Adicionar foto";
      setMessage(error.message, true);
    }
  });
  actions.append(label, input);
}

async function manageItem(item, action) {
  const token = owned()[item.id];
  if (!token) return;
  const question = action === "delete"
    ? "Remover este anúncio do mural? Essa ação não pode ser desfeita."
    : "Marcar este anúncio como resolvido? Ele deixará de aparecer entre os itens em aberto.";
  if (!window.confirm(question)) return;
  try {
    const response = await fetch(`${API}/${item.id}`, {
      method: action === "delete" ? "DELETE" : "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ managementToken: token, status: item.kind === "lost" ? "recovered" : "returned" }),
    });
    if (!response.ok && response.status !== 204) {
      const result = await response.json();
      throw new Error(result.error?.message || "Não foi possível atualizar o anúncio.");
    }
    if (action === "delete") {
      const current = owned();
      delete current[item.id];
      saveOwned(current);
    } else {
      state.status = "resolved";
      document.querySelectorAll(".status-tab").forEach((tab) => tab.classList.toggle("active", tab.dataset.status === "resolved"));
    }
    syncMyCount();
    setMessage(action === "delete" ? "Anúncio removido." : "Que bom! O anúncio foi marcado como resolvido.");
    await loadItems();
  } catch (error) { setMessage(error.message, true); }
}

function makeItemCard(item) {
  const isExample = item.demo || /^(?:DEMO|EXEMPLO) ·/.test(item.title);
  const card = node("article", `item-card${item.status === "resolved" ? " is-resolved" : ""}${item.urgent && item.status === "open" ? " is-urgent" : ""}`);
  card.id = `item-${item.id}`;
  const visual = node("div", `item-visual ${item.kind === "lost" ? "visual-lost" : "visual-found"}`);
  if (item.photoUrl) {
    const photo = node("img", "item-photo");
    photo.src = item.photoUrl;
    photo.alt = `Foto do item: ${item.title}`;
    visual.append(photo);
  } else {
    visual.append(node("span", "category-icon", categories[item.category] || "✳"));
  }
  const sticker = node("span", `type-sticker ${item.kind}`, item.kind === "lost" ? "PERDIDO" : "ENCONTRADO");
  visual.append(sticker);
  if (item.urgent && item.status === "open") visual.append(node("span", "urgent-sticker", "URGENTE"));
  if (item.status === "resolved") visual.append(node("span", "resolved-sticker", "RESOLVIDO"));
  card.append(visual);

  const content = node("div", "item-content");
  const meta = node("div", "item-meta");
  meta.append(node("span", "category-label", item.category));
  meta.append(node("span", "meta-separator", "·"));
  meta.append(node("span", "item-date", formatDate(item.eventDate)));
  const sourceLabel = isExample
    ? (item.contactPhone ? "WHATSAPP REAL · DEMO" : "EXEMPLO FICTÍCIO")
    : "COMUNIDADE";
  meta.append(node("span", `source-badge ${isExample ? "source-demo" : "source-community"}`, sourceLabel));
  content.append(meta);
  content.append(node("h3", "item-title", isExample ? item.title.replace(/^(?:DEMO|EXEMPLO) ·\s*/, "") : item.title));
  content.append(node("p", "item-description", item.description));
  const where = node("p", "item-location");
  where.append(node("span", "location-pin", "⌖"), document.createTextNode(` ${item.location}`));
  content.append(where);
  const publisher = item.contactName || "Pessoa da comunidade";
  const initials = publisher.trim().split(/\s+/).slice(0, 2).map((part) => part[0]).join("").toLocaleUpperCase("pt-BR");
  const publisherLine = node("div", "publisher-line");
  publisherLine.append(node("span", "publisher-avatar", initials), node("span", "publisher-name", `Publicado por ${publisher}`));
  content.append(publisherLine);

  if (item.status === "resolved") {
    content.append(node("span", "resolved-label", item.kind === "lost" ? "✓ Recuperado" : "✓ Devolvido"));
  }

  const actions = node("div", "item-actions");
  const token = owned()[item.id];
  if (item.photoEditable) addLocalPhotoControl(actions, item);
  if (token) {
    if (item.status === "open") {
      const done = node("button", "button button-contact", item.kind === "lost" ? "Marcar recuperado" : "Marcar devolvido");
      done.type = "button";
      done.addEventListener("click", () => manageItem(item, "resolve"));
      actions.append(done);
    }
    const remove = node("button", "manage-remove", "Remover anúncio");
    remove.type = "button";
    remove.addEventListener("click", () => manageItem(item, "delete"));
    actions.append(remove);
  } else if (item.status === "open" && item.contactPhone) {
    addContactActions(actions, item);
  }
  if (item.status === "open") {
    const matchesButton = node("button", "match-toggle", "✦ Ver possíveis correspondências");
    matchesButton.type = "button";
    matchesButton.addEventListener("click", () => findMatches(item, content, matchesButton));
    content.append(matchesButton);
  }
  if (actions.childElementCount) content.append(actions);
  card.append(content);
  return card;
}

function render(items) {
  const ownedIds = new Set(Object.keys(owned()));
  let visible = items.filter((item) => state.source === "all"
    || (state.source === "examples" ? item.demo : !item.demo));
  if (state.mineOnly) visible = visible.filter((item) => ownedIds.has(String(item.id)));
  visible = [...visible].sort((a, b) => {
    const resolvedOrder = Number(a.status === "resolved") - Number(b.status === "resolved");
    if (resolvedOrder) return resolvedOrder;
    if (byId("sort-filter").value === "urgent" && a.urgent !== b.urgent) return Number(b.urgent) - Number(a.urgent);
    return b.createdAt.localeCompare(a.createdAt);
  });
  const resolved = visible.filter((item) => item.status === "resolved");
  const open = visible.filter((item) => item.status !== "resolved");
  grid.replaceChildren(...open.map(makeItemCard));
  resolvedGrid.replaceChildren(...resolved.map(makeItemCard));
  byId("resolved-section").hidden = resolved.length === 0;
  byId("results-count").textContent = state.mineOnly
    ? `${visible.length} ${visible.length === 1 ? "publicação sua" : "publicações suas"}`
    : `${visible.length} ${visible.length === 1 ? "anúncio encontrado" : "anúncios encontrados"}`;
  byId("empty-state").hidden = visible.length !== 0;
}

async function loadItems() {
  state.loading = true;
  byId("results-count").textContent = "Buscando no mural…";
  try {
    const response = await fetch(`${API}?${currentParams()}`);
    if (!response.ok) throw new Error("Não foi possível carregar os anúncios.");
    const data = await response.json();
    state.items = data.items;
    byId("stat-lost").textContent = data.stats.lost;
    byId("stat-found").textContent = data.stats.found;
    byId("stat-resolved").textContent = data.stats.resolved;
    render(state.items);
    setMessage("");
  } catch (error) {
    grid.replaceChildren();
    resolvedGrid.replaceChildren();
    byId("resolved-section").hidden = true;
    byId("results-count").textContent = "Mural indisponível";
    byId("empty-state").hidden = true;
    setMessage(`${error.message} Confirme se o servidor está rodando em http://127.0.0.1:8000.`, true);
  } finally { state.loading = false; }
}

let searchTimer;
byId("search-input").addEventListener("input", () => {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(loadItems, 220);
});
byId("category-filter").addEventListener("change", loadItems);
byId("source-filter").addEventListener("change", (event) => {
  state.source = event.currentTarget.value;
  render(state.items);
});
byId("sort-filter").addEventListener("change", () => render(state.items));
document.querySelectorAll(".filter-tab").forEach((button) => button.addEventListener("click", () => {
  document.querySelectorAll(".filter-tab").forEach((tab) => tab.classList.toggle("active", tab === button));
  state.kind = button.dataset.kind;
  loadItems();
}));

document.querySelectorAll(".status-tab").forEach((button) => button.addEventListener("click", () => {
  state.status = button.dataset.status;
  document.querySelectorAll(".status-tab").forEach((tab) => tab.classList.toggle("active", tab === button));
  loadItems();
}));

const reportDialog = byId("report-dialog");
const successDialog = byId("success-dialog");
function openReport() {
  byId("form-error").textContent = "";
  reportDialog.showModal();
}
[
  "open-report", "hero-report", "section-report", "mobile-report", "empty-report",
].forEach((id) => byId(id).addEventListener("click", openReport));
byId("close-dialog").addEventListener("click", () => reportDialog.close());
byId("cancel-dialog").addEventListener("click", () => reportDialog.close());
reportDialog.addEventListener("click", (event) => {
  if (event.target === reportDialog) reportDialog.close();
});
byId("report-form").addEventListener("change", (event) => {
  if (event.target.name === "kind") {
    const kind = new FormData(byId("report-form")).get("kind");
    byId("dialog-title").textContent = kind === "lost" ? "Publicar item perdido" : "Publicar item encontrado";
    byId("submit-report").innerHTML = kind === "lost" ? "Publicar item perdido <span aria-hidden=\"true\">→</span>" : "Publicar item encontrado <span aria-hidden=\"true\">→</span>";
  }
});

const dateInput = byId("report-form").elements.eventDate;
dateInput.max = new Date().toISOString().slice(0, 10);
const photoInput = byId("photo-input");
const photoPreview = byId("photo-preview");
let previewObjectUrl = "";
photoInput.addEventListener("change", () => {
  if (previewObjectUrl) URL.revokeObjectURL(previewObjectUrl);
  const file = photoInput.files?.[0];
  if (!file) { previewObjectUrl = ""; photoPreview.hidden = true; photoPreview.removeAttribute("src"); return; }
  previewObjectUrl = URL.createObjectURL(file);
  photoPreview.src = previewObjectUrl;
  photoPreview.hidden = false;
});

async function compressPhoto(file) {
  if (!file) return "";
  if (!file.type.startsWith("image/") || file.size > 10_000_000) {
    throw new Error("Escolha uma imagem válida de até 10 MB.");
  }
  const image = new Image();
  image.src = URL.createObjectURL(file);
  await image.decode();
  const scale = Math.min(1, 1000 / Math.max(image.naturalWidth, image.naturalHeight));
  const canvas = document.createElement("canvas");
  canvas.width = Math.round(image.naturalWidth * scale);
  canvas.height = Math.round(image.naturalHeight * scale);
  canvas.getContext("2d").drawImage(image, 0, 0, canvas.width, canvas.height);
  URL.revokeObjectURL(image.src);
  let quality = 0.82;
  let photo = canvas.toDataURL("image/jpeg", quality);
  while (photo.length > 650_000 && quality > 0.5) {
    quality -= 0.08;
    photo = canvas.toDataURL("image/jpeg", quality);
  }
  if (photo.length > 700_000) throw new Error("A foto ficou grande demais. Escolha uma imagem menor.");
  return photo;
}

byId("report-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const reportForm = event.currentTarget;
  byId("form-error").textContent = "";
  const button = byId("submit-report");
  button.disabled = true;
  button.textContent = "Publicando…";
  const form = new FormData(event.currentTarget);
  const payload = Object.fromEntries(form.entries());
  payload.urgent = form.has("urgent");
  try {
    payload.photo = await compressPhoto(form.get("photo"));
    const response = await fetch(API, {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error?.message || "Não foi possível publicar o anúncio.");
    const current = owned();
    current[data.item.id] = data.managementToken;
    saveOwned(current);
    syncMyCount();
    byId("management-code").textContent = `${data.item.id}.${data.managementToken}`;
    const postMatches = byId("post-match-results");
    postMatches.hidden = false;
    postMatches.replaceChildren(node("strong", "matches-heading", data.item.kind === "lost" ? "Encontrados que podem combinar" : "Perdidos que podem combinar"));
    postMatches.append(node("p", "matches-empty", "Procurando anúncios parecidos…"));
    reportDialog.close();
    successDialog.showModal();
    reportForm.reset();
    if (previewObjectUrl) URL.revokeObjectURL(previewObjectUrl);
    previewObjectUrl = "";
    photoPreview.hidden = true;
    photoPreview.removeAttribute("src");
    byId("dialog-title").textContent = "Publicar um item";
    byId("submit-report").innerHTML = "Publicar anúncio <span aria-hidden=\"true\">→</span>";
    state.status = "all";
    state.kind = "";
    state.source = "all";
    state.mineOnly = false;
    byId("source-filter").value = "all";
    byId("search-input").value = "";
    byId("category-filter").value = "";
    byId("my-posts-button").classList.remove("selected");
    byId("my-posts-button").setAttribute("aria-pressed", "false");
    document.querySelectorAll(".status-tab").forEach((tab) => tab.classList.toggle("active", tab.dataset.status === "all"));
    document.querySelectorAll(".filter-tab").forEach((tab) => tab.classList.toggle("active", !tab.dataset.kind));
    loadItems();
    requestMatches(data.item, postMatches);
  } catch (error) {
    byId("form-error").textContent = error.message;
  } finally {
    button.disabled = false;
    button.innerHTML = "Publicar anúncio <span aria-hidden=\"true\">→</span>";
  }
});

byId("copy-code").addEventListener("click", async () => {
  try {
    await navigator.clipboard.writeText(byId("management-code").textContent);
    byId("copy-code").textContent = "Copiado!";
  } catch { byId("copy-code").textContent = "Selecione e copie"; }
});
byId("success-close").addEventListener("click", () => {
  successDialog.close();
  byId("post-match-results").hidden = true;
  document.querySelector("#anuncios").scrollIntoView({ behavior: "smooth" });
});
byId("my-posts-button").addEventListener("click", () => {
  if (!state.mineOnly && Object.keys(owned()).length === 0) {
    const backupCode = window.prompt("Cole o código de gerenciamento recebido ao publicar seu anúncio:");
    if (backupCode) {
      const separator = backupCode.indexOf(".");
      const id = backupCode.slice(0, separator);
      const token = backupCode.slice(separator + 1);
      if (separator > 0 && /^\d+$/.test(id) && token.length >= 20) {
        const current = owned();
        current[id] = token;
        saveOwned(current);
        syncMyCount();
      } else {
        window.alert("Código inválido. Confira se copiou o código completo.");
        return;
      }
    }
  }
  state.mineOnly = !state.mineOnly;
  byId("my-posts-button").classList.toggle("selected", state.mineOnly);
  byId("my-posts-button").setAttribute("aria-pressed", String(state.mineOnly));
  if (state.mineOnly) {
    state.kind = "";
    byId("search-input").value = "";
    byId("category-filter").value = "";
    document.querySelectorAll(".filter-tab").forEach((tab) => tab.classList.toggle("active", !tab.dataset.kind));
  }
  loadItems();
  document.querySelector("#anuncios").scrollIntoView({ behavior: "smooth" });
});

document.addEventListener("keydown", (event) => {
  if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
    event.preventDefault();
    byId("search-input").focus();
  }
});

syncMyCount();
loadItems();

function saveMatchFeedback(originalId, candidateId, value) {
  const feedback = readMatchFeedback();
  feedback[originalId] = { ...(feedback[originalId] || {}), [candidateId]: value };
  try { localStorage.setItem(matchFeedbackKey, JSON.stringify(feedback)); }
  catch { /* Suggestions remain usable when browser storage is unavailable. */ }
}

function renderMatches(target, item, data) {
  target.replaceChildren(node("strong", "matches-heading", item.kind === "lost" ? "Encontrados que podem combinar" : "Perdidos que podem combinar"));
  const feedback = readMatchFeedback()[item.id] || {};
  const visibleMatches = data.matches.filter((match) => feedback[match.id] !== false);
  if (!visibleMatches.length) {
    target.append(node("p", "matches-empty", data.matches.length
      ? "Você marcou as sugestões como não correspondentes. Tente novamente mais tarde."
      : "Não encontramos anúncios compatíveis em aberto. Tente novamente depois."));
  } else {
    visibleMatches.forEach((match) => {
      const row = node("div", "possible-match");
      const details = node("div", "possible-match-details");
      details.append(node("span", "possible-match-summary", `${match.title} · ${match.category} · ${match.location}`));
      details.append(node("span", "match-confidence", `similaridade ${match.score}/100`));
      const reasons = node("ul", "match-reasons");
      (match.reasons || []).forEach((reason) => reasons.append(node("li", "", reason)));
      if (reasons.childElementCount) details.append(reasons);
      const actions = node("div", "match-feedback");
      const yes = node("button", `match-feedback-button${feedback[match.id] === true ? " selected" : ""}`, feedback[match.id] === true ? "✓ Pode ser" : "Pode ser");
      yes.type = "button";
      yes.setAttribute("aria-pressed", String(feedback[match.id] === true));
      yes.addEventListener("click", () => {
        saveMatchFeedback(item.id, match.id, true);
        yes.textContent = "✓ Pode ser";
        yes.classList.add("selected");
        yes.setAttribute("aria-pressed", "true");
      });
      const no = node("button", "match-feedback-button match-negative", "Não é meu item");
      no.type = "button";
      no.addEventListener("click", () => {
        saveMatchFeedback(item.id, match.id, false);
        row.remove();
        if (!target.querySelector(".possible-match")) {
          target.append(node("p", "matches-empty", "Você marcou as sugestões como não correspondentes. Tente novamente mais tarde."));
        }
      });
      const open = node("button", "match-open", "Ver anúncio →");
      open.type = "button";
      open.addEventListener("click", async () => {
        if (successDialog.open && successDialog.contains(target)) {
          successDialog.close();
          target.hidden = true;
        }
        state.source = match.demo ? "examples" : "community";
        byId("source-filter").value = state.source;
        state.mineOnly = false;
        byId("my-posts-button").classList.remove("selected");
        byId("my-posts-button").setAttribute("aria-pressed", "false");
        state.kind = "";
        state.status = "open";
        document.querySelectorAll(".status-tab").forEach((tab) => tab.classList.toggle("active", tab.dataset.status === "open"));
        byId("search-input").value = "";
        byId("category-filter").value = "";
        document.querySelectorAll(".filter-tab").forEach((tab) => tab.classList.toggle("active", !tab.dataset.kind));
        await loadItems();
        document.getElementById(`item-${match.id}`)?.scrollIntoView({ behavior: "smooth", block: "center" });
      });
      actions.append(yes, no, open);
      row.append(details, actions);
      target.append(row);
    });
  }
  target.append(node("small", "matches-note", data.method === "gemini" ? "Sugestões organizadas pela IA. Confirme os detalhes com quem publicou." : "Sugestões por semelhança entre título, categoria, local e descrição. Confirme os detalhes com quem publicou."));
  target.append(node("small", "matches-note", "Sua avaliação fica salva somente neste navegador."));
}

async function requestMatches(item, target) {
  try {
    const response = await fetch(`${API}/${item.id}/matches`, { method: "POST" });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error?.message || "Não foi possível analisar os anúncios.");
    renderMatches(target, item, data);
  } catch (error) {
    target.replaceChildren(node("strong", "matches-heading", "Possíveis correspondências"));
    target.append(node("p", "matches-empty", error.message));
  }
}

async function findMatches(item, content, button) {
  if (content.querySelector(".possible-matches")) {
    content.querySelector(".possible-matches").remove();
    button.textContent = "✦ Ver possíveis correspondências";
    return;
  }
  button.disabled = true;
  button.textContent = "Analisando anúncios…";
  const results = node("div", "possible-matches");
  results.setAttribute("aria-live", "polite");
  results.append(node("p", "matches-empty", "Procurando anúncios parecidos…"));
  content.append(results);
  await requestMatches(item, results);
  button.disabled = false;
  button.textContent = "Ocultar sugestões";
}
