async function cargarCalendario() {
    const vista = document.getElementById("selector-vista").value;
    const tbody = document.getElementById("tabla-asistencias");

    tbody.innerHTML = `
        <tr><td colspan="7" class="text-center">Cargando...</td></tr>
    `;

    try {
        const resp = await fetch("/bedelia/asistencias/calendario");
        if (!resp.ok) throw new Error("Error al solicitar datos");

        const data = await resp.json();

        const lista = data[vista];
        renderTabla(lista, vista);

        document.getElementById("ultima-actualizacion").textContent =
            new Date().toLocaleTimeString("es-AR", {
                hour12: false,
                timeZone: "America/Argentina/Buenos_Aires"
            });

    } catch (err) {
        console.error(err);
        tbody.innerHTML = `
            <tr><td colspan="7" class="text-center text-danger">
                Error al cargar asistencias.
            </td></tr>
        `;
    }
}


// -----------------------------
// Render de tabla
// -----------------------------
function renderTabla(lista, vista) {
    const tbody = document.getElementById("tabla-asistencias");
    tbody.innerHTML = "";

    if (!lista || lista.length === 0) {
        tbody.innerHTML = `
            <tr><td colspan="7" class="text-center text-muted">
                No hay datos para mostrar.
            </td></tr>
        `;
        return;
    }

    // FUTURAS = TURNOS
    if (vista === "futuras") {
        lista.forEach(t => {
            tbody.innerHTML += `
                <tr>
                    <td>-</td>
                    <td>${t.docente}</td>
                    <td>${t.materia ?? "-"}</td>
                    <td>${t.punto ?? "-"}</td>

                    <td>
                        <span class="badge-estado estado-programado">
                            PROGRAMADO
                        </span>
                    </td>

                    <td>-</td>
                    <td>${t.inicio} - ${t.fin}</td>
                </tr>
            `;
        });
        return;
    }

    // HOY / PASADAS = ASISTENCIAS
    lista.forEach(a => {
        const estadoClass = `estado-${a.estado.toLowerCase()}`;

        tbody.innerHTML += `
            <tr>
                <td>${a.id}</td>
                <td>${a.docente}</td>
                <td>${a.materia ?? "-"}</td>
                <td>${a.punto ?? "-"}</td>

                <td>
                    <span class="badge-estado ${estadoClass}">
                        ${a.estado}
                    </span>
                </td>

                <td>${a.motivo ?? "-"}</td>
                <td>${a.hora}</td>
            </tr>
        `;
    });
}


// -----------------------------
// Eventos
// -----------------------------
document.getElementById("selector-vista")
    .addEventListener("change", cargarCalendario);

document.getElementById("btn-recargar")
    .addEventListener("click", cargarCalendario);


// Primera carga
cargarCalendario();
setInterval(cargarCalendario, 60000);  // cada 60s



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


