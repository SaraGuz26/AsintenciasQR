const token = localStorage.getItem("token");

if (!token) {
    window.location.href = "/frontend/bedelia/login.html";
}

// Variables de paginaciom

let paginaActual = 1;
const filasPorPagina = 10;
let listaActual = [];

// Para poner etiquetas coloquiales de fecha
function formatearFechaColoquial(fechaStr) {
    const fecha = new Date(fechaStr + "T00:00:00");
    const hoy = new Date();

    // limpiar horas
    hoy.setHours(0,0,0,0);
    fecha.setHours(0,0,0,0);

    const diff = (hoy - fecha) / (1000 * 60 * 60 * 24);

    if (diff === 0) return "Hoy";
    if (diff === 1) return "Ayer";
    if (diff <= 6) return `Hace ${diff} días`;

    return fechaStr; 
}

// Darle colores al calendario

function claseBadgeFecha(fechaStr) {
    const fecha = new Date(fechaStr + "T00:00:00");
    const hoy = new Date();

    hoy.setHours(0,0,0,0);
    fecha.setHours(0,0,0,0);

    const diff = (hoy - fecha) / (1000 * 60 * 60 * 24);

    if (diff === 0) return "bg-success";   //  Hoy
    if (diff === 1) return "bg-warning text-dark"; //  Ayer
    if (diff <= 6) return "bg-info text-dark"; //  semana
    return "bg-secondary"; //  viejo
}

// Para aplicar a los colores de los estados
function claseEstado(estado) {
    const map = {
        "PRESENTE": "estado-en_consulta",
        "TARDE": "estado-tarde",
        "AUSENTE": "estado-invalido",
        "FINALIZADO": "estado-finalizado",
        "PROGRAMADO": "estado-programado"
    };

    return map[estado] || "estado-programado";
}

//Para las etiquetas de las fechas futuras coloquiales
function etiquetaFechaFutura(fechaStr) {
    const fecha = new Date(fechaStr + "T00:00:00");
    const hoy = new Date();

    hoy.setHours(0,0,0,0);
    fecha.setHours(0,0,0,0);

    const diff = (fecha - hoy) / (1000 * 60 * 60 * 24);

    if (diff === 0) return "Hoy";
    if (diff === 1) return "Mañana";
    if (diff <= 6) return `En ${diff} días`;

    return fechaStr;
}

//FILTRADO
let datosOriginales = [];

function aplicarFiltros() {
    let filtrados = [...datosOriginales];

    const docente = document.getElementById("filtro-docente").value.toLowerCase();
    const materia = document.getElementById("filtro-materia").value.toLowerCase();
    const punto = document.getElementById("filtro-punto").value.toLowerCase();
    const estado = document.getElementById("filtro-estado").value;

    filtrados = filtrados.filter(a => {

        return (
            (!docente || (a.docente ?? "").toLowerCase().includes(docente)) &&
            (!materia || (a.materia ?? "").toLowerCase().includes(materia)) &&
            (!punto || (a.punto ?? "").toLowerCase().includes(punto)) &&
            (!estado || a.estado === estado)
        );
    });

    const vista = document.getElementById("selector-vista").value;
    listaActual = filtrados;
    paginaActual = 1;
    renderTablaPaginada(listaActual);
}

// Funcion de paginado

function renderTablaPaginada(lista) {
    const inicio = (paginaActual - 1) * filasPorPagina;
    const fin = inicio + filasPorPagina;

    const pagina = lista.slice(inicio, fin);

    renderTabla(pagina, document.getElementById("selector-vista").value);

    renderPaginacion(lista.length);
}

// Renderizacion de paginado

function renderPaginacion(total) {
    const cont = document.getElementById("paginacion");

    const totalPaginas = Math.ceil(total / filasPorPagina);

    cont.innerHTML = `
        <div class="d-flex justify-content-between align-items-center mt-3">

            <button class="btn btn-outline-primary btn-sm"
                ${paginaActual === 1 ? "disabled" : ""}
                onclick="cambiarPagina(-1)">
                ⬅️ Anterior
            </button>

            <span class="small">
                Página ${paginaActual} de ${totalPaginas}
            </span>

            <button class="btn btn-outline-primary btn-sm"
                ${paginaActual === totalPaginas ? "disabled" : ""}
                onclick="cambiarPagina(1)">
                Siguiente ➡️
            </button>

        </div>
    `;
}

function cambiarPagina(delta) {
    const totalPaginas = Math.ceil(listaActual.length / filasPorPagina);

    paginaActual += delta;

    if (paginaActual < 1) paginaActual = 1;
    if (paginaActual > totalPaginas) paginaActual = totalPaginas;

    renderTablaPaginada(listaActual);
}

//Cargar calendario

async function cargarCalendario() {
    const vista = document.getElementById("selector-vista").value;
    const tbody = document.getElementById("tabla-asistencias");

    tbody.innerHTML = `
        <tr><td colspan="9" class="text-center">Cargando...</td></tr>
    `;

    try {

        /*Parte donde guarda el token para el login*/ 
        const token = localStorage.getItem("token");

        const resp = await fetch("/bedelia/asistencias/calendario", {
            headers: {
                "Authorization": "Bearer " + token
            }
        });

        if (!resp.ok) throw new Error("Error al solicitar datos");

        const data = await resp.json();

        const lista = data[vista];

        datosOriginales = lista;
        paginaActual = 1;
        aplicarFiltros();

        document.getElementById("ultima-actualizacion").textContent =
            new Date().toLocaleTimeString("es-AR", {
                hour12: false,
                timeZone: "America/Argentina/Buenos_Aires"
            });

    } catch (err) {
        console.error(err);
        tbody.innerHTML = `
            <tr><td colspan="9" class="text-center text-danger">
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
            <tr><td colspan="9" class="text-center text-muted">
                "No hay resultados con esos filtros"
            </td></tr>
        `;
        return;
    }

    // FUTURAS = TURNOS
    if (vista === "futuras") {

        // ordenar por fecha ASC (futuro cercano primero)
        lista.sort((a, b) => new Date(a.fecha) - new Date(b.fecha));

        let ultimaFecha = "";

        lista.forEach(t => {

            if (t.fecha !== ultimaFecha) {
                tbody.innerHTML += `
                    <tr class="table-primary">
                        <td colspan="9">
                            <strong>${etiquetaFechaFutura(t.fecha)}</strong>
                            <span class="ms-2">(${t.dia_semana})</span>
                        </td>
                    </tr>
                `;
                ultimaFecha = t.fecha;
            }

            tbody.innerHTML += `
                <tr>
                    <td>-</td>

                    <td class="text-primary fw-semibold">
                        ${t.fecha}
                    </td>

                    <td>${t.dia_semana ?? "-"}</td>

                    <td>${t.docente}</td>
                    <td>${t.materia ?? "-"}</td>
                    <td>${t.punto ?? "-"}</td>

                    <td>
                        <span class="badge-estado estado-programado">
                            PROGRAMADO
                        </span>
                    </td>

                    <td>${t.hora_inicio} - ${t.hora_fin}</td>
                </tr>
            `;
        });

        return;
    }

    // HOY / PASADAS = ASISTENCIAS
    // ordenar primero (más nuevo arriba)
    lista.sort((a, b) => new Date(b.fecha) - new Date(a.fecha));

    let ultimaFecha = "";

    lista.forEach(a => {
        const estadoClass = claseEstado(a.estado);

        // separador por fecha (tipo timeline)
        if (a.fecha !== ultimaFecha) {
            tbody.innerHTML += `
                <tr class="table-secondary">
                    <td colspan="9">
                        <strong>${formatearFechaColoquial(a.fecha)}</strong>
                        <span class="text-muted ms-2">(${a.dia_semana})</span>
                    </td>
                </tr>
            `;
            ultimaFecha = a.fecha;
        }

        tbody.innerHTML += `
            <tr>
                <td>${a.id}</td>

                <td>
                    <span class="badge ${claseBadgeFecha(a.fecha)}">
                        ${formatearFechaColoquial(a.fecha)}
                    </span>
                    <div class="small text-muted">${a.fecha}</div>
                </td>

                <td>${a.dia_semana ?? "-"}</td>
                <td>${a.docente}</td>
                <td>${a.materia ?? "-"}</td>
                <td>${a.punto ?? "-"}</td>

                <td>
                    <span class="badge-estado ${estadoClass}">
                        ${a.estado}
                    </span>
                </td>

                
                <td>${a.hora_inicio} - ${a.hora_fin}</td>
            </tr>
        `;
    });
}

// <td>${a.motivo ?? "-"}</td> Aun no usamos el motivo xq hay que pensar como se vera
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

// EVENTOS FILTROS
window.addEventListener("DOMContentLoaded", () => {
    document.getElementById("filtro-docente").addEventListener("input", aplicarFiltros);
    document.getElementById("filtro-materia").addEventListener("input", aplicarFiltros);
    document.getElementById("filtro-punto").addEventListener("input", aplicarFiltros);
    document.getElementById("filtro-estado").addEventListener("change", aplicarFiltros);
});


// Boton borrar seleccion de filtros
const btnLimpiar = document.getElementById("btn-limpiar");
if (btnLimpiar) {
    btnLimpiar.addEventListener("click", () => {
        document.getElementById("filtro-docente").value = "";
        document.getElementById("filtro-materia").value = "";
        document.getElementById("filtro-punto").value = "";
        document.getElementById("filtro-estado").value = "";
        aplicarFiltros();
    });
}

const API = window.location.origin;

async function cargarResumen(params = {}) {
  const url = new URL(API + "/bedelia/resumen");
  Object.entries(params).forEach(([k,v]) => v && url.searchParams.set(k, v));
  try {

    const token = localStorage.getItem("token");
    const res = await fetch(url, {
        headers: {
            "Accept": "application/json",
            "Authorization": "Bearer " + token
        }
    });

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


