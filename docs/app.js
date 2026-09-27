const $ = (selector, root = document) => root.querySelector(selector);
const state = { items: [], publishedAt: null };

function esc(value = "") {
  const node = document.createElement("div");
  node.textContent = value ?? "";
  return node.innerHTML;
}

function people(contributors = []) {
  return contributors.map(person => person.role ? `${person.name} (${person.role})` : person.name).join(", ");
}

function itemLocation(item) {
  return [item.stack && `Stack ${item.stack}`, item.shelf_row && `Row ${item.shelf_row}`, item.shelf_position].filter(Boolean).join(", ");
}

function volume(item) {
  return item.volume_label || (item.volume_number != null ? `Volume ${item.volume_number}` : "");
}

function setOptions(selector, values, label) {
  $(selector).innerHTML = `<option value="">${label}</option>` + [...new Set(values.filter(Boolean))].sort().map(value => `<option>${esc(value)}</option>`).join("");
}

function matchingContents(item, query) {
  if (!query) return [];
  const terms = query.toLocaleLowerCase().split(/\s+/).filter(Boolean);
  return (item.contents || []).filter(content => {
    const text = JSON.stringify(content).toLocaleLowerCase();
    return terms.every(term => text.includes(term));
  }).slice(0, 2);
}

function render() {
  const query = $("#search").value.trim().toLocaleLowerCase();
  const category = $("#category").value;
  const stack = $("#stack").value;
  const row = $("#row").value;
  const terms = query.split(/\s+/).filter(Boolean);
  const filtered = state.items.filter(item => {
    const text = JSON.stringify(item).toLocaleLowerCase();
    return (!category || item.media_category === category) && (!stack || item.stack === stack) &&
      (!row || item.shelf_row === row) && terms.every(term => text.includes(term));
  });
  $("#count").textContent = `${filtered.length} ${filtered.length === 1 ? "item" : "items"}`;
  $("#results").innerHTML = filtered.map(item => {
    const index = state.items.indexOf(item);
    const matches = matchingContents(item, query);
    return `<button class="result" data-index="${index}">
      <span class="spine ${(item.contents || []).length > 1 ? "multi" : ""}">${esc((item.media_category || "Item").slice(0,3).toUpperCase())}</span>
      <span><span class="result-title">${esc(item.title)}</span><span class="result-sub">${esc([people(item.contributors),item.publisher,item.publication_date].filter(Boolean).join(" · "))}</span><span class="result-meta">${(item.contents || []).length ? `${item.contents.length} indexed ${(item.contents || []).length === 1 ? "work" : "works"}` : ""}</span>${matches.map(work => `<span class="match">Matched: ${esc(work.title)}${work.page_start ? ` · p. ${esc(work.page_start)}` : ""}</span>`).join("")}</span>
      <span class="set">${esc([item.set_name,volume(item)].filter(Boolean).join(" · "))}</span>
      <span class="location"><small>Location</small>${esc(itemLocation(item) || "Not assigned")}</span>
      <span class="arrow">→</span>
    </button>`;
  }).join("");
  $("#empty").hidden = filtered.length > 0;
}

const detailLabels = {
  subtitle:"Subtitle", publication_date:"Publication date", publisher:"Publisher", edition:"Edition",
  identifier:"ISBN / identifier", language:"Language", item_type:"Record type", set_name:"Set / series",
  volume_label:"Volume", volume_number:"Volume number", media_category:"Media category",
};

function openDetails(index) {
  const item = state.items[index];
  $("#detail-category").textContent = item.media_category || "Catalogue item";
  $("#detail-title").textContent = item.title;
  const fields = Object.entries(detailLabels).filter(([key]) => item[key] != null && item[key] !== "");
  $("#detail-body").innerHTML = `
    <div class="detail-grid">
      ${item.contributors?.length ? `<div class="detail-field"><small>Contributors</small>${esc(people(item.contributors))}</div>` : ""}
      ${fields.map(([key,label]) => `<div class="detail-field"><small>${label}</small>${esc(item[key])}</div>`).join("")}
      <div class="detail-field"><small>Location</small>${esc(itemLocation(item) || "Not assigned")}</div>
      ${item.description ? `<div class="detail-field detail-description"><small>Description</small>${esc(item.description)}</div>` : ""}
    </div>
    ${(item.contents || []).length ? `<section class="contents"><h3>Contents</h3>${item.contents.map(work => `<div class="content"><strong>${esc(work.title)}</strong><span>${esc([work.work_type,people(work.contributors),work.publication_date,work.page_start && `p. ${work.page_start}${work.page_end && work.page_end !== work.page_start ? `–${work.page_end}` : ""}`].filter(Boolean).join(" · "))}</span></div>`).join("")}</section>` : ""}`;
  $("#details").showModal();
}

document.addEventListener("click", event => {
  const result = event.target.closest(".result");
  if (result) openDetails(Number(result.dataset.index));
});
$("#close-details").addEventListener("click", () => $("#details").close());
$("#search").addEventListener("input", render);
$("#category").addEventListener("change", render);
$("#stack").addEventListener("change", render);
$("#row").addEventListener("change", render);
$("#clear").addEventListener("click", () => { $("#category").value = $("#stack").value = $("#row").value = ""; render(); });

fetch("catalogue.json").then(response => {
  if (!response.ok) throw new Error("Catalogue data could not be loaded");
  return response.json();
}).then(data => {
  state.items = data.items || [];
  state.publishedAt = data.published_at;
  setOptions("#category", state.items.map(item => item.media_category), "All media");
  setOptions("#stack", state.items.map(item => item.stack), "All stacks");
  setOptions("#row", state.items.map(item => item.shelf_row), "All rows");
  if (state.publishedAt) $("#published").textContent = `Updated ${new Date(state.publishedAt).toLocaleDateString()}`;
  render();
}).catch(error => {
  $("#count").textContent = "Unavailable";
  $("#results").innerHTML = `<div class="empty"><h2>Catalogue unavailable</h2><p>${esc(error.message)}</p></div>`;
});
