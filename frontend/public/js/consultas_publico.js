async function cargarConsultas() {
    let dia = document.getElementById("select-dia").value;

    const resp = await fetch(`/publico/consultas?dia=${dia}`);
    const lista = await resp.json();

    const cont = document.getElementById("contenedor-consultas");
    cont.innerHTML = "";

    if (lista.length === 0) {
        cont.innerHTML = `<p class="text-center">No hay consultas para este día.</p>`;
        return;
    }

    lista.forEach(c => {
        const color = {
            PRESENTE: "#2ecc71",
            TARDE: "#e67e22",
            AUSENTE: "#e74c3c",
            PROGRAMADO: "#3498db",
            FINALIZADO: "#7f8c8d",
            SIN_ASISTENCIA: "#95a5a6"
        }[c.estado] || "#bdc3c7";

        cont.innerHTML += `
            <div class="consulta-card">
                <h5>${c.materia}</h5>
                <p class="m-0"><strong>Docente:</strong> ${c.docente}</p>
                <p class="m-0"><strong>Punto:</strong> ${c.punto}</p>
                <p class="m-0"><strong>Horario:</strong> ${c.hora_inicio} - ${c.hora_fin}</p>

                <p class="mt-2">
                    <span class="estado-dot" style="background:${color};"></span>
                    <strong>${c.estado}</strong>
                    <span class="text-muted">(${c.hora_registro})</span>
                </p>
            </div>
        `;
    });
}

document.getElementById("select-dia").addEventListener("change", cargarConsultas);

cargarConsultas();
