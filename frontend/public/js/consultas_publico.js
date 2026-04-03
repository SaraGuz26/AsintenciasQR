const API = window.location.origin;

// Colores por estado
function colorEstado(estado) {
    switch ((estado || "").toLowerCase()) {
        case "en_curso": return "#22c55e";   // verde
        case "tarde": return "#f59e0b";      // naranja
        case "finalizado": return "#94a3b8"; // gris
        case "programado": return "#8ebdf8"; // azul pastel
        default: return "#64748b";
    }
}

// Obtener lunes de la semana
function getMonday(date) {
    const d = new Date(date);
    const day = d.getDay() || 7;
    if (day !== 1) d.setDate(d.getDate() - day + 1);
    return d;
}

// Formato YYYY-MM-DD
function formatLocalDate(date) {
    return date.getFullYear() + "-" +
        String(date.getMonth() + 1).padStart(2, '0') + "-" +
        String(date.getDate()).padStart(2, '0');
}

// Cambiar vista según tamaño
function ajustarVista(calendar) {
    if (window.innerWidth < 768) {
        calendar.changeView("timeGridDay");
    } else {
        calendar.changeView("timeGridWeek");
    }
}

function ajustarToolbar(calendar) {
    if (window.innerWidth < 768) {
        calendar.setOption("headerToolbar", {
            left: 'prev,next',
            center: 'title',
            right: ''
        });
    } else {
        calendar.setOption("headerToolbar", {
            left: 'prev,next today',
            center: 'title',
            right: 'timeGridDay,timeGridWeek'
        });
    }
}

// Inicializar calendario
async function initCalendar() {
    try {
        const res = await fetch(API + "/publico/consultas/semana");
        const data = await res.json();

        console.log("DATA BACKEND:", data);

        const hoy = new Date();
        const lunes = getMonday(hoy);

        // Convertir datos a eventos
        const eventos = data.map(it => {
            const fecha = new Date(lunes);
            fecha.setDate(lunes.getDate() + (it.dia_semana - 1));

            const fechaStr = formatLocalDate(fecha);

            return {
                title: `${it.materia} - ${it.docente}`,
                start: `${fechaStr}T${it.hora_inicio}`,
                end: `${fechaStr}T${it.hora_fin}`,
                backgroundColor: colorEstado(it.estado),
                borderColor: colorEstado(it.estado),
                extendedProps: {
                    aula: it.punto,
                    estado: it.estado,
                    hora_registro: it.hora_registro
                }
            };
        });

        // Crear calendario
        const calendar = new FullCalendar.Calendar(document.getElementById("calendar"), {
            initialView: 'timeGridWeek',
            locale: 'es',
            allDaySlot: false,
            height: "auto",

            headerToolbar: {
                left: 'prev,next today',
                center: 'title',
                right: 'timeGridDay,timeGridWeek'
            },

            // Header personalizado
            dayHeaderContent: function(arg) {
                const fecha = arg.date;
                const dias = ["Dom", "Lun", "Mar", "Mié", "Jue", "Vie", "Sáb"];
                return dias[fecha.getDay()] + " " + fecha.getDate() + "/" + (fecha.getMonth() + 1);
            },

            // visual
            slotMinTime: "07:00:00",
            slotMaxTime: "23:00:00",
            nowIndicator: true,
            expandRows: true,
            contentHeight: "auto",
            aspectRatio: 1.5,

            slotLabelFormat: {
                hour: '2-digit',
                minute: '2-digit',
                hour12: false
            },

            events: eventos,

            // Eventos
            eventDisplay: 'block',
            eventClassNames: 'evento-custom',

            eventContent: function(arg) {
                return {
                    html: `
                        <div style="font-size:12px;">
                            <div><b>${arg.event.title}</b></div>
                            <div style="opacity:0.8;">📍 ${arg.event.extendedProps.aula}</div>
                            <div style="font-size:11px; margin-top:4px;">
                                ${arg.event.start.toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'})}
                                -
                                ${arg.event.end.toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'})}
                            </div>
                        </div>
                    `
                };
            },

            eventClick: function(info) {
                alert(
                    `📚 ${info.event.title}\n` +
                    `📍 Aula: ${info.event.extendedProps.aula}\n` +
                    `⏱ Estado: ${info.event.extendedProps.estado}\n` +
                    `🕓 Registro: ${info.event.extendedProps.hora_registro}`
                );
            }
        });

        // Renderizar
        calendar.render();

        // Ajustar vista inicial
        ajustarVista(calendar);
        ajustarToolbar(calendar);

        // Resize dinámico
        window.addEventListener("resize", () => {
            ajustarVista(calendar);
            ajustarToolbar(calendar);
        });

    } catch (error) {
        console.error("ERROR:", error);
    }
}

// Ejecutar
initCalendar();