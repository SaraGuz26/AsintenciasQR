const API = window.location.origin; // mismo host:8000

function badge(estado) {
  switch ((estado || "").toLowerCase()) {
    case "en curso": return "text-bg-success";
    case "tarde": return "text-bg-warning";
    case "salida anticipada": return "text-bg-info";
    case "fuera de turno": return "text-bg-secondary";
    default: return "text-bg-light";
  }
}

async function cargarEstados(params = {}) {
  const url = new URL(API + "/public/estados");
  Object.entries(params).forEach(([k,v]) => v && url.searchParams.set(k, v));
  try {
    const res = await fetch(url);
    if (!res.ok) throw new Error("HTTP " + res.status);
    const data = await res.json();
    render(data);
  } catch (e) {
    console.error(e);
    document.getElementById("tbody").innerHTML =
      `<tr><td colspan="5" class="text-danger">No se pudo cargar</td></tr>`;
  }
}

function render(list) {
  const tbody = document.getElementById("tbody");
  if (!list || !list.length) {
    tbody.innerHTML = `<tr><td colspan="5" class="text-muted">Sin resultados</td></tr>`;
    return;
  }
  tbody.innerHTML = list.map(it => `
    <tr>
      <td>${it.profesor ?? "-"}</td>
      <td>${it.materia ?? "-"}</td>
      <td>${it.aula ?? "-"}</td>
      <td><span class="badge ${badge(it.estado)}">${it.estado ?? "-"}</span></td>
      <td>${it.desde ?? "-"}–${it.hasta ?? "-"}</td>
    </tr>
  `).join("");
}

document.getElementById("filtros").addEventListener("submit", (e) => {
  e.preventDefault();
  cargarEstados({
    ahora: "1",
    qDocente: document.getElementById("qDocente").value.trim(),
    qMateria: document.getElementById("qMateria").value.trim(),
    solo_presentes: document.getElementById("soloPresentes").value
  });
});

// primera carga
cargarEstados({ ahora: "1" });
