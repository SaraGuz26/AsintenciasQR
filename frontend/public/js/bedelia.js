const API = window.location.origin;

async function cargarResumen(params = {}) {
  const url = new URL(API + "/bedelia/resumen");
  Object.entries(params).forEach(([k,v]) => v && url.searchParams.set(k, v));
  try {
    const res = await fetch(url, { headers: { "Accept": "application/json" }});
    if (!res.ok) throw new Error("HTTP " + res.status);
    const data = await res.json();
    render(data);
  } catch (e) {
    console.error(e);
    document.getElementById("tbody").innerHTML =
      `<tr><td colspan="4" class="text-danger">No se pudo cargar</td></tr>`;
  }
}

function render(rows) {
  const tbody = document.getElementById("tbody");
  if (!rows || !rows.length) {
    tbody.innerHTML = `<tr><td colspan="4" class="text-muted">Sin datos</td></tr>`;
    return;
  }
  tbody.innerHTML = rows.map(r => `
    <tr>
      <td>${r.profesor}</td>
      <td>${r.presentes}</td>
      <td>${r.ausentes}</td>
      <td>${r.tardanzas}</td>
    </tr>
  `).join("");
}

document.getElementById("filtros").addEventListener("submit", (e) => {
  e.preventDefault();
  const fecha = document.getElementById("fecha").value;
  const docente = document.getElementById("docente").value.trim();
  cargarResumen({ fecha, docente });
});

// link export
document.getElementById("btnExport").addEventListener("click", (e) => {
  e.preventDefault();
  const fecha = document.getElementById("fecha").value || "";
  const docente = document.getElementById("docente").value.trim() || "";
  const url = new URL(API + "/bedelia/export.csv");
  if (fecha) url.searchParams.set("fecha", fecha);
  if (docente) url.searchParams.set("docente", docente);
  window.location.href = url.toString();
});

// setear hoy por defecto
document.getElementById("fecha").value = new Date().toISOString().slice(0,10);
cargarResumen({ fecha: document.getElementById("fecha").value });
