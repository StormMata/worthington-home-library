const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];

const state = { options: {}, importFile: null, importContent: "", importFormat: "", isbnResult: null };
const form = $("#item-form");
const dialog = $("#editor-dialog");

async function api(url, options = {}) {
  const response = await fetch(url, {
    ...options,
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "Something went wrong");
  return data;
}

function toast(message) {
  const node = $("#toast");
  node.textContent = message;
  node.classList.add("show");
  clearTimeout(toast.timer);
  toast.timer = setTimeout(() => node.classList.remove("show"), 2600);
}

function escapeHtml(value = "") {
  const div = document.createElement("div");
  div.textContent = value ?? "";
  return div.innerHTML;
}

function addTemplate(templateId, target, data = {}) {
  const node = $(templateId).content.firstElementChild.cloneNode(true);
  Object.entries(data).forEach(([key, value]) => {
    const input = node.querySelector(`[data-field="${key}"]`);
    if (input) input.value = value ?? "";
  });
  $(target).append(node);
  return node;
}

function addContributor(data) { return addTemplate("#contributor-template", "#item-contributors", data); }
function addMetadata(key = "", value = "") { return addTemplate("#metadata-template", "#metadata-list", { key, value }); }
function addContent(data = {}) {
  const contributor = data.contributors?.[0] || {};
  return addTemplate("#content-template", "#contents-list", {
    ...data,
    contributor_name: contributor.name,
    contributor_role: contributor.role || "Author",
  });
}
function addDigitalFile(data = {}) {
  const node = addTemplate("#digital-file-template", "#digital-files-list", data);
  const openLink = $(".digital-file-open", node);
  const missing = $(".digital-file-missing", node);
  if (data.url && data.exists) {
    openLink.href = data.url;
    openLink.hidden = false;
  } else if (data.relative_path && data.exists === false) {
    missing.hidden = false;
  }
  return node;
}

function switchView(name) {
  $$(".view").forEach(el => el.classList.toggle("active", el.id === `${name}-view`));
  $$("[data-view]").forEach(el => el.classList.toggle("active", el.dataset.view === name && el.classList.contains("nav-button")));
  if (name === "catalogue") $("#search").focus();
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function renderOptions() {
  const populate = (selector, values, label) => {
    const select = $(selector), selected = select.value;
    select.innerHTML = `<option value="">${label}</option>` + values.map(v => `<option>${escapeHtml(v)}</option>`).join("");
    select.value = selected;
  };
  populate("#filter-category", state.options.categories || [], "All media");
  populate("#filter-stack", state.options.stacks || [], "All stacks");
  populate("#filter-row", state.options.rows || [], "All rows");
  $("#category-list").innerHTML = (state.options.categories || []).map(v => `<option value="${escapeHtml(v)}">`).join("");
  $("#content-count").textContent = `${state.options.counts?.contents || 0} indexed contents`;
}

async function refreshOptions() {
  state.options = await api("/api/options");
  renderOptions();
}

let searchTimer;
async function search() {
  const params = new URLSearchParams({
    q: $("#search").value,
    category: $("#filter-category").value,
    stack: $("#filter-stack").value,
    row: $("#filter-row").value,
  });
  $("#search-status").textContent = "Searching…";
  try {
    const { items } = await api(`/api/search?${params}`);
    renderResults(items);
    $("#search-status").textContent = "";
  } catch (error) {
    $("#search-status").textContent = error.message;
  }
}

function queueSearch() {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(search, 120);
}

function renderResults(items) {
  $("#result-count").textContent = `${items.length} ${items.length === 1 ? "item" : "items"}`;
  $("#results").innerHTML = items.map(item => `
    <button class="result-card" data-id="${item.id}">
      <span class="spine ${item.content_count > 1 ? "anthology" : ""}">${escapeHtml((item.media_category || "Item").slice(0, 3).toUpperCase())}</span>
      <span>
        <span class="result-title">${escapeHtml(item.title)}</span>
        <span class="result-sub">${escapeHtml([item.contributors, item.publisher, item.publication_date].filter(Boolean).join(" · "))}</span>
        <span class="result-meta">${item.content_count ? `${item.content_count} indexed ${item.content_count === 1 ? "work" : "works"}` : "No contained works indexed"}${item.digital_file_count ? ` · ${item.digital_file_count} digital ${item.digital_file_count === 1 ? "file" : "files"}` : ""}</span>
        ${(item.matched_contents || []).map(match => `<span class="content-match"><b>Matched:</b> ${escapeHtml(match.title)}${match.contributors ? ` — ${escapeHtml(match.contributors)}` : ""}${match.page_start ? ` · p. ${escapeHtml(match.page_start)}${match.page_end && match.page_end !== match.page_start ? `–${escapeHtml(match.page_end)}` : ""}` : ""}</span>`).join("")}
      </span>
      <span class="result-set">${escapeHtml([item.set_name, item.volume_display].filter(Boolean).join(" · "))}</span>
      <span class="location"><small>Location</small>${escapeHtml(item.location || "Not assigned")}</span>
      <span class="arrow" aria-hidden="true">→</span>
    </button>`).join("");
  const completelyEmpty = !items.length && !$("#search").value && !$("#filter-category").value && !$("#filter-stack").value && !$("#filter-row").value;
  $("#empty-state").hidden = !completelyEmpty;
  if (!items.length && !completelyEmpty) {
    $("#results").innerHTML = `<div class="empty-state"><h2>No matching shelf</h2><p>Try fewer words or clear one of the filters.</p></div>`;
  }
}

function resetEditor() {
  form.reset();
  form.elements.id.value = "";
  form.elements.media_category.value = "Book";
  $("#item-contributors").innerHTML = "";
  $("#contents-list").innerHTML = "";
  $("#digital-files-list").innerHTML = "";
  $("#metadata-list").innerHTML = "";
  $("#isbn-lookup-result").hidden = true;
  $("#isbn-lookup-result").innerHTML = "";
  state.isbnResult = null;
  $("#editor-kicker").textContent = "New catalogue record";
  $("#editor-title").textContent = "Add an item";
  $("#delete-item").hidden = true;
  addContributor({ role: "Author" });
}

function currentContributors() {
  return rowsToData("#item-contributors .contributor-row").filter(person => person.name);
}

function sameValue(first, second) {
  return String(first || "").trim().toLocaleLowerCase() === String(second || "").trim().toLocaleLowerCase();
}

function renderIsbnResult(result) {
  state.isbnResult = result;
  const panel = $("#isbn-lookup-result");
  const labels = {
    title: "Title", subtitle: "Subtitle", publication_date: "Publication date",
    publisher: "Publisher", identifier: "ISBN", language: "Language", description: "Description",
  };
  const rows = Object.entries(result.fields).map(([field, fetched]) => {
    const current = form.elements[field]?.value || "";
    const matches = sameValue(current, fetched);
    return `<label class="comparison-row ${matches ? "matches" : "differs"}">
      <input type="checkbox" data-lookup-field="${field}" ${!matches && !current ? "checked" : ""} ${matches ? "disabled" : ""}>
      <span class="comparison-name">${escapeHtml(labels[field] || field)}</span>
      <span class="comparison-values"><small>Catalogue</small>${escapeHtml(current || "Empty")}<small>Open Library</small>${escapeHtml(fetched)}</span>
      <strong>${matches ? "Match" : current ? "Different" : "Missing"}</strong>
    </label>`;
  });
  if (result.contributors?.length) {
    const current = currentContributors().map(person => `${person.name} (${person.role})`).join(", ");
    const fetched = result.contributors.map(person => `${person.name} (${person.role})`).join(", ");
    const matches = sameValue(current, fetched);
    rows.push(`<label class="comparison-row ${matches ? "matches" : "differs"}">
      <input type="checkbox" data-lookup-field="contributors" ${!matches && !current ? "checked" : ""} ${matches ? "disabled" : ""}>
      <span class="comparison-name">Contributors</span>
      <span class="comparison-values"><small>Catalogue</small>${escapeHtml(current || "Empty")}<small>Open Library</small>${escapeHtml(fetched)}</span>
      <strong>${matches ? "Match" : current ? "Different" : "Missing"}</strong>
    </label>`);
  }
  const additions = Object.entries(result.additional || {}).filter(([, value]) => value);
  panel.hidden = false;
  panel.innerHTML = `
    <div class="lookup-heading">
      <div><strong>Open Library comparison</strong><span>${result.cached ? "Saved lookup" : "Live lookup"} · ${escapeHtml(result.isbn)}</span></div>
      <button type="button" class="text-button" id="refresh-isbn">Check again</button>
    </div>
    <div class="comparison-list">${rows.join("")}</div>
    ${additions.length ? `<div class="lookup-additional">${additions.map(([key, value]) => `<span><b>${escapeHtml(key)}</b>${escapeHtml(value)}</span>`).join("")}</div>` : ""}
    <div class="lookup-actions">
      <a href="${escapeHtml(result.source_url)}" target="_blank" rel="noreferrer">View Open Library record</a>
      <button type="button" class="button button-secondary" id="apply-isbn">Apply selected fields</button>
    </div>`;
}

async function lookupIsbn(refresh = false) {
  const isbn = form.elements.identifier.value.trim();
  const panel = $("#isbn-lookup-result");
  panel.hidden = false;
  if (!isbn) {
    panel.innerHTML = `<div class="lookup-error"><strong>ISBN required</strong><span>Enter an ISBN-10 or ISBN-13 first.</span></div>`;
    return;
  }
  panel.innerHTML = `<div class="lookup-loading">Checking Open Library…</div>`;
  $("#lookup-isbn").disabled = true;
  try {
    const suffix = refresh ? "?refresh=1" : "";
    renderIsbnResult(await api(`/api/isbn/${encodeURIComponent(isbn)}${suffix}`));
  } catch (error) {
    state.isbnResult = null;
    panel.innerHTML = `<div class="lookup-error"><strong>Lookup unsuccessful</strong><span>${escapeHtml(error.message)}</span></div>`;
  } finally {
    $("#lookup-isbn").disabled = false;
  }
}

function applyIsbnSelection() {
  if (!state.isbnResult) return;
  const selected = $$("[data-lookup-field]:checked", $("#isbn-lookup-result")).map(input => input.dataset.lookupField);
  selected.forEach(field => {
    if (field === "contributors") {
      $("#item-contributors").innerHTML = "";
      state.isbnResult.contributors.forEach(addContributor);
    } else if (form.elements[field]) {
      form.elements[field].value = state.isbnResult.fields[field] || "";
    }
  });
  renderIsbnResult(state.isbnResult);
  toast(selected.length ? `${selected.length} field${selected.length === 1 ? "" : "s"} applied` : "No fields selected");
}

function openNewEditor() {
  resetEditor();
  dialog.showModal();
}

async function editItem(id) {
  const item = await api(`/api/items/${id}`);
  resetEditor();
  Object.entries(item).forEach(([key, value]) => {
    if (form.elements[key] && value != null && typeof value !== "object") form.elements[key].value = value;
  });
  $("#item-contributors").innerHTML = "";
  item.contributors.forEach(addContributor);
  $("#contents-list").innerHTML = "";
  item.contents.forEach(addContent);
  $("#digital-files-list").innerHTML = "";
  (item.digital_files || []).forEach(addDigitalFile);
  Object.entries(item.metadata || {}).forEach(([key, value]) => addMetadata(key, typeof value === "string" ? value : JSON.stringify(value)));
  $("#editor-kicker").textContent = item.media_category || "Catalogue record";
  $("#editor-title").textContent = "Edit item";
  $("#delete-item").hidden = false;
  dialog.showModal();
}

function rowsToData(selector) {
  return $$(selector).map(row => Object.fromEntries($$("[data-field]", row).map(input => [input.dataset.field, input.value.trim()])));
}

function formPayload() {
  const data = Object.fromEntries(new FormData(form));
  delete data.id;
  data.contributors = rowsToData("#item-contributors .contributor-row").filter(c => c.name);
  data.contents = rowsToData("#contents-list .content-editor").filter(c => c.title).map((content, index) => ({
    ...content,
    sequence_no: index + 1,
    contributors: content.contributor_name ? [{ name: content.contributor_name, role: content.contributor_role || "Author" }] : [],
  }));
  data.digital_files = rowsToData("#digital-files-list .digital-file-row").filter(file => file.relative_path);
  data.metadata = Object.fromEntries(rowsToData("#metadata-list .metadata-row").filter(m => m.key).map(m => [m.key, m.value]));
  return data;
}

async function saveEditor(event) {
  event.preventDefault();
  const id = form.elements.id.value;
  try {
    await api(id ? `/api/items/${id}` : "/api/items", { method: id ? "PUT" : "POST", body: JSON.stringify(formPayload()) });
    dialog.close();
    toast(id ? "Item updated" : "Item added to your catalogue");
    await Promise.all([refreshOptions(), search()]);
  } catch (error) { toast(error.message); }
}

async function deleteItem() {
  const id = form.elements.id.value;
  if (!id || !confirm("Delete this item and all of its indexed contents? This cannot be undone.")) return;
  try {
    await api(`/api/items/${id}`, { method: "DELETE" });
    dialog.close();
    toast("Item deleted");
    await Promise.all([refreshOptions(), search()]);
  } catch (error) { toast(error.message); }
}

async function previewImport(file) {
  state.importFile = file;
  state.importContent = await file.text();
  state.importFormat = file.name.toLowerCase().endsWith(".csv") ? "csv" : "json";
  const preview = $("#import-preview");
  preview.hidden = false;
  preview.innerHTML = "Reading file…";
  try {
    const result = await api("/api/import/preview", { method: "POST", body: JSON.stringify({ format: state.importFormat, content: state.importContent }) });
    preview.innerHTML = `
      <strong>${result.valid} valid ${result.valid === 1 ? "record" : "records"}</strong>
      ${result.errors.length ? `<p>${result.errors.length} problem(s): ${escapeHtml(result.errors.slice(0, 3).map(e => `Row ${e.row}: ${e.message}`).join("; "))}</p>` : "<p>No validation problems found.</p>"}
      <button class="button button-primary" id="confirm-import" ${result.valid ? "" : "disabled"}>Import ${result.valid} item${result.valid === 1 ? "" : "s"}</button>`;
  } catch (error) { preview.innerHTML = `<strong>Could not read this file</strong><p>${escapeHtml(error.message)}</p>`; }
}

async function commitImport() {
  const button = $("#confirm-import");
  button.disabled = true;
  button.textContent = "Importing…";
  try {
    const result = await api("/api/import/commit", { method: "POST", body: JSON.stringify({ format: state.importFormat, content: state.importContent }) });
    $("#import-preview").innerHTML = `<strong>Import complete</strong><p>${result.imported} item${result.imported === 1 ? "" : "s"} added to your catalogue.</p>`;
    toast("Import complete");
    await Promise.all([refreshOptions(), search()]);
  } catch (error) { toast(error.message); button.disabled = false; }
}

async function generatePublicSite() {
  const button = $("#generate-public-site");
  const status = $("#public-publish-status");
  button.disabled = true;
  button.textContent = "Generating…";
  status.hidden = true;
  try {
    const result = await api("/api/publish", { method: "POST", body: "{}" });
    status.hidden = false;
    status.innerHTML = `<strong>Public site prepared</strong><span>${result.items} item${result.items === 1 ? "" : "s"} included. Commit and push the <code>docs</code> folder to publish.</span>`;
    toast("Public catalogue generated");
  } catch (error) {
    status.hidden = false;
    status.innerHTML = `<strong>Could not generate the site</strong><span>${escapeHtml(error.message)}</span>`;
  } finally {
    button.disabled = false;
    button.textContent = "Generate public site";
  }
}

document.addEventListener("click", event => {
  const view = event.target.closest("[data-view]");
  if (view) switchView(view.dataset.view);
  if (event.target.closest("#new-item, [data-action='new']")) openNewEditor();
  if (event.target.closest("[data-action='close']")) dialog.close();
  if (event.target.closest("[data-action='add-contributor']")) addContributor({ role: "Author" });
  if (event.target.closest("[data-action='add-content']")) addContent();
  if (event.target.closest("[data-action='add-digital-file']")) addDigitalFile();
  if (event.target.closest("[data-action='add-metadata']")) addMetadata();
  const removeRow = event.target.closest(".remove-row");
  if (removeRow) removeRow.closest(".repeat-row").remove();
  const removeContent = event.target.closest(".remove-content");
  if (removeContent) removeContent.closest(".content-editor").remove();
  const removeDigitalFile = event.target.closest(".remove-digital-file");
  if (removeDigitalFile) removeDigitalFile.closest(".digital-file-row").remove();
  const card = event.target.closest(".result-card");
  if (card) editItem(card.dataset.id).catch(error => toast(error.message));
  if (event.target.closest("#confirm-import")) commitImport();
  if (event.target.closest("#lookup-isbn")) lookupIsbn();
  if (event.target.closest("#refresh-isbn")) lookupIsbn(true);
  if (event.target.closest("#apply-isbn")) applyIsbnSelection();
  if (event.target.closest("#generate-public-site")) generatePublicSite();
});

$("#search").addEventListener("input", queueSearch);
$$('#filter-category, #filter-stack, #filter-row').forEach(select => select.addEventListener("change", search));
$("#clear-filters").addEventListener("click", () => {
  $("#filter-category").value = $("#filter-stack").value = $("#filter-row").value = "";
  search();
});
$("#import-file").addEventListener("change", event => event.target.files[0] && previewImport(event.target.files[0]));
$("#delete-item").addEventListener("click", deleteItem);
form.addEventListener("submit", saveEditor);
document.addEventListener("keydown", event => {
  if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
    event.preventDefault(); switchView("catalogue"); $("#search").focus();
  }
  if (event.key === "Escape" && dialog.open) dialog.close();
});

Promise.all([refreshOptions(), search()]).catch(error => toast(error.message));
