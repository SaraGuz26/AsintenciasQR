const DOCENTE_ID = 1;  // TODO: reemplazar con el del login real
let turnoEditando = null;

// ==============================
// Helper para fetch con JSON
// ==============================
async function fetchJson(url, options) {
    const resp = await fetch(url, options);
    if (!resp.ok) {
        console.error("Error en fetch", url, resp.status);
        return null;
    }
    return await resp.json();
}

// ==============================
// Toast de mensajes
// ==============================
function toast(msg) {
    const t = document.getElementById("toast");
    if (!t) {
        console.warn("No existe #toast en el HTML");
        return;
    }
    t.textContent = msg;
    t.className = "toast show";

    setTimeout(() => {
        t.className = t.className.replace("show", "");
    }, 2500);
}

// ==============================
// Cargar datos del docente
// ==============================
async function cargarDocente() {
    const d = await fetchJson(`/docentes/${DOCENTE_ID}`);
    if (!d) return;

    document.getElementById("doc_nombre").textContent = d.nombre + " " + d.apellido;
    document.getElementById("doc_legajo").textContent = d.legajo;
    document.getElementById("doc_email").textContent = d.email;
}

// ==============================
// Credencial y QR
// ==============================
async function cargarCredencial() {
    const d = await fetchJson(`/docentes/${DOCENTE_ID}/credencial`);
    if (!d) return;

    document.getElementById("cred_id").textContent = d.credencial_id;
    document.getElementById("cred_emitido").textContent = d.emitido_en;

    const qrData = JSON.stringify(d.qr_payload);
    const canvas = document.getElementById("qr-canvas");

    new QRious({
        element: canvas,
        size: 220,
        value: qrData
    });
}

async function regenerarQR() {
    await fetch(`/docentes/${DOCENTE_ID}/credencial/regenerar`, { method: "POST" });
    await cargarCredencial();
    toast("QR regenerado");
}

// ==============================
// Mostrar / ocultar formulario nuevo turno
// ==============================
function mostrarFormCreacion() {
    document.getElementById("form-turno").style.display = "block";
    cargarPuntos();
    cargarMaterias();
}

function ocultarForm() {
    document.getElementById("form-turno").style.display = "none";

    // limpiar campos
    document.getElementById("t_dia").value = "1";
    document.getElementById("t_inicio").value = "";
    document.getElementById("t_fin").value = "";
    document.getElementById("t_tol").value = "10";
    document.getElementById("t_punto").value = "";
    document.getElementById("t_materia").value = "";
}

// ==============================
// Listar turnos del docente
// ==============================
async function cargarTurnos() {
    const lista = await fetchJson(`/turnos/docente/${DOCENTE_ID}`);
    if (!lista) return;

    const tbody = document.getElementById("tabla_turnos");
    tbody.innerHTML = "";

    lista.forEach(t => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td>${diaNombre(t.dia_semana)}</td>
            <td>${t.hora_inicio}</td>
            <td>${t.hora_fin}</td>
            <td>${t.punto_nombre}</td>
            <td>${t.materia_nombre}</td>
            <td>
                <button onclick="editarTurno(${t.id})">Editar</button>
                <button onclick="eliminarTurno(${t.id})">Eliminar</button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

// ==============================
// Crear turno
// ==============================
async function crearTurno() {
    const inicio = document.getElementById("t_inicio").value;
    const fin = document.getElementById("t_fin").value;

    // validación simple fin > inicio
    if (!inicio || !fin || fin <= inicio) {
        toast("La hora de fin debe ser mayor que la hora de inicio");
        return;
    }

    const payload = {
        docente_id: DOCENTE_ID,
        dia_semana: parseInt(document.getElementById("t_dia").value),
        hora_inicio: inicio + ":00",
        hora_fin: fin + ":00",
        tolerancia_min: parseInt(document.getElementById("t_tol").value),
        materia_id: parseInt(document.getElementById("t_materia").value),
        punto_id_plan: parseInt(document.getElementById("t_punto").value),
        activo: true
    };

    const res = await fetch(`/turnos`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
    });

    if (!res.ok) {
        let err = {};
        try { err = await res.json(); } catch {}
        toast(err.detail || "Error al crear turno");
        return;
    }

    toast("Turno creado correctamente");
    ocultarForm();
    cargarTurnos();
}

// ==============================
// Eliminar turno
// ==============================
async function eliminarTurno(id) {

    if (!confirm("¿Seguro que querés eliminar este turno?")) {
        return;
    }

    const r = await fetch(`/turnos/${id}`, { method: "DELETE" });

    if (r.ok) {
        toast("Turno eliminado");
        cargarTurnos();
        cargarTurnosHoy();
    } else {
        toast("Error eliminando turno");
    }
}

// ==============================
// Cargar puntos y materias
// ==============================
async function cargarPuntos() {
    const lista = await fetchJson("/puntos");
    if (!lista) return;

    const select = document.getElementById("t_punto");
    select.innerHTML = "";
    lista.forEach(p => {
        select.innerHTML += `<option value="${p.id}">${p.etiqueta}</option>`;
    });

    const selEdit = document.getElementById("edit_punto");
    if (selEdit) {
        selEdit.innerHTML = "";
        lista.forEach(p => {
            selEdit.innerHTML += `<option value="${p.id}">${p.etiqueta}</option>`;
        });
    }
}

async function cargarMaterias() {
    const lista = await fetchJson("/materias");
    if (!lista) return;

    const select = document.getElementById("t_materia");
    select.innerHTML = "";
    lista.forEach(m => {
        select.innerHTML += `<option value="${m.id}">${m.nombre}</option>`;
    });

    const selEdit = document.getElementById("edit_materia");
    if (selEdit) {
        selEdit.innerHTML = "";
        lista.forEach(m => {
            selEdit.innerHTML += `<option value="${m.id}">${m.nombre}</option>`;
        });
    }
}

// ==============================
// Editar turno (abrir modal)
// ==============================
async function editarTurno(id) {
    turnoEditando = id;

    // los selects ya se cargan en cargarPuntos()/cargarMaterias() al inicio
    const t = await fetchJson(`/turnos/${id}`);
    if (!t) {
        toast("Error al cargar turno");
        return;
    }

    document.getElementById("edit_dia").value = t.dia_semana;
    document.getElementById("edit_inicio").value = t.hora_inicio.slice(0,5);
    document.getElementById("edit_fin").value = t.hora_fin.slice(0,5);
    document.getElementById("edit_tol").value = t.tolerancia_min;
    document.getElementById("edit_punto").value = t.punto_id_plan;
    document.getElementById("edit_materia").value = t.materia_id;

    document.getElementById("modalEditarTurno").style.display = "flex";
}

// ==============================
// Guardar cambios de turno
// ==============================
async function guardarEdicionTurno() {
    if (!turnoEditando) return;

    const inicio = document.getElementById("edit_inicio").value;
    const fin = document.getElementById("edit_fin").value;

    if (!inicio || !fin || fin <= inicio) {
        toast("La hora de fin debe ser mayor que la hora de inicio");
        return;
    }

    const data = {
        dia_semana: parseInt(document.getElementById("edit_dia").value),
        hora_inicio: inicio + ":00",
        hora_fin: fin + ":00",
        tolerancia_min: parseInt(document.getElementById("edit_tol").value),
        punto_id_plan: parseInt(document.getElementById("edit_punto").value),
        materia_id: parseInt(document.getElementById("edit_materia").value),
    };

    const res = await fetch(`/turnos/${turnoEditando}`, {
        method: "PUT",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(data)
    });

    if (!res.ok) {
        let err = {};
        try { err = await res.json(); } catch {}
        toast(err.detail || "Error al actualizar turno");
        return;
    }

    toast("Turno actualizado con éxito");
    cerrarModalEditar();
    cargarTurnos();
}

function cerrarModalEditar() {
    document.getElementById("modalEditarTurno").style.display = "none";
    turnoEditando = null;
}

function colorEstado(estado) {
    switch (estado) {
        case "EN_CONSULTA": return "#2ecc71";   // verde
        case "TARDE": return "#e67e22";         // naranja
        case "REUBICADO": return "#9b59b6";     // violeta
        case "PROGRAMADO": return "#f1c40f";    // amarillo
        case "FINALIZADO": return "#95a5a6";    // gris
        default: return "#bdc3c7";              // default
    }
}

async function cargarTurnosHoy() {
    const lista = await fetchJson(`/turnos/docente/${DOCENTE_ID}/estado-hoy`);
    const cont = document.getElementById("turnos_hoy");

    cont.innerHTML = "";

    if (!lista || lista.length === 0) {
        cont.innerHTML = "<p>No tenés turnos hoy.</p>";
        return;
    }

    lista.forEach(t => {
        const color = colorEstado(t.estado);

        cont.innerHTML += `
            <div class="turno-hoy-card">
                
                <div class="turno-hoy-header">${t.materia_nombre}</div>

                <div class="turno-hoy-sub">
                    📍 ${t.punto_nombre}<br>
                    🕒 ${t.hora_inicio} - ${t.hora_fin}
                </div>

                <div class="estado-box">
                    <span class="estado-dot" style="background:${color};"></span>
                    <strong>${t.estado}</strong>
                </div>
            </div>
        `;
    });
}


// ==============================
// Helper: nombre día
// ==============================
function diaNombre(n) {
    return ["","Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"][n];
}



// ==============================
// Inicialización del panel
// ==============================
cargarDocente();
cargarCredencial();
cargarPuntos();
cargarMaterias();
cargarTurnos();
cargarTurnosHoy();
