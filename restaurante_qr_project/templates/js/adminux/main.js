document.addEventListener("DOMContentLoaded", () => {
  /* ===== LOADER ===== */
  const loader = document.getElementById("loader");
  if (loader) {
    setTimeout(() => {
      loader.style.transition = "opacity 0.25s ease";
      loader.style.opacity = "0";
      loader.style.pointerEvents = "none";
      setTimeout(() => (loader.style.display = "none"), 260);
    }, 700);
  }

  /* ===== RELOJ ===== */
  const clockTime = document.getElementById("clockTime");
  const clockDate = document.getElementById("clockDate");

  function updateClock() {
    const now = new Date();
    if (clockTime) {
      clockTime.textContent = now
        .toLocaleTimeString("es-BO", {
          hour: "2-digit",
          minute: "2-digit",
          second: "2-digit",
        })
        .replace(/:/g, " : ");
    }
    if (clockDate) {
      clockDate.textContent = now.toLocaleDateString("es-BO", {
        weekday: "long",
        day: "2-digit",
        month: "long",
        year: "numeric",
      });
    }
  }
  updateClock();
  setInterval(updateClock, 1000);

  /* ===== NAV SPA ===== */
  const navItems = document.querySelectorAll(".nav-item[data-target]");
  const sections = document.querySelectorAll(".page-section[data-section]");

  function setActiveSection(target) {
    sections.forEach((sec) =>
      sec.classList.toggle("active", sec.dataset.section === target)
    );
  }

  // ===== BADGES EN EL SIDEBAR =====
  function setNavBadge(key, count) {
    const badge = document.querySelector(
      `.nav-counter[data-nav-badge="${key}"]`
    );
    if (!badge) return;

    if (!count || count <= 0) {
      badge.textContent = "0";
      badge.classList.add("hidden");
    } else {
      badge.textContent = String(count);
      badge.classList.remove("hidden");
    }
  }

  navItems.forEach((item) => {
    item.addEventListener("click", (e) => {
      e.preventDefault();
      const target = item.dataset.target;
      if (!target) return;

      navItems.forEach((n) => n.classList.remove("active"));
      item.classList.add("active");
      setActiveSection(target);

      if (target === "mesas") {
        initMesas();
      } else if (target === "productos") {
        initProductos();
      } else if (target === "inventario") {
        initInventario();
      } else if (target === "reservas") {
        initReservas();
      } else if (target === "usuarios") {
        initUsuarios();
      } else if (target === "reportes") {
        initReportes();
      } else if (target === "configuracion") {
        initConfiguracion();
      }

      // Cerrar menú en móvil y desmarcar burger
      if (window.innerWidth <= 1024) {
        document.body.classList.remove("sidebar-open");
        const burgerCheckbox = document.getElementById("burgerToggle");
        if (burgerCheckbox) burgerCheckbox.checked = false;
      }
    });
  });

  /* ===== NOTIFICACIONES GLOBALES (campanita) ===== */

  const notifBell = document.getElementById("notifBell");
  const notifDropdown = document.getElementById("notifDropdown");
  const notifList = document.getElementById("notifList");
  const notifBadge = document.getElementById("notifBadge");
  const notifClearBtn = document.getElementById("notifClear");

  let notifications = [];

  function renderNotificationUI() {
    if (!notifList) return;

    notifList.innerHTML = "";

    if (!notifications.length) {
      const li = document.createElement("li");
      li.className = "notif-empty";
      li.textContent = "Sin notificaciones por el momento.";
      notifList.appendChild(li);

      if (notifBadge) {
        notifBadge.classList.add("hidden");
      }
      return;
    }

    notifications.forEach((n) => {
      const li = document.createElement("li");
      li.className = "notif-item";
      li.dataset.id = String(n.id);
      li.dataset.targetSection = n.target || "";

      li.innerHTML = `
        <span class="notif-item-title">${n.label}</span>
        ${
          n.detail
            ? `<span class="notif-item-meta">${n.detail}</span>`
            : ""
        }
        ${
          n.tag
            ? `<span class="notif-item-tag">${n.tag}</span>`
            : ""
        }
      `;

      notifList.appendChild(li);
    });

    if (notifBadge) {
      notifBadge.textContent = String(notifications.length);
      notifBadge.classList.remove("hidden");
    }
  }

  // Reemplaza todas las notificaciones de un tipo (ej: "inventario")
  function updateNotifications(type, items) {
    notifications = notifications.filter((n) => n.type !== type);
    notifications = notifications.concat(items);
    renderNotificationUI();
  }

  function closeNotifications() {
    notifDropdown?.classList.add("hidden");
  }

  function toggleNotifications() {
    if (!notifDropdown) return;
    notifDropdown.classList.toggle("hidden");
  }

  // Ir a una sección del SPA (Mesas, Inventario, etc.) usando el menú lateral
  function goToSection(target) {
    const navItem = Array.from(navItems).find(
      (n) => n.dataset.target === target
    );
    if (navItem) {
      navItem.click();
    }
  }

  // Eventos UI
  notifBell?.addEventListener("click", (e) => {
    e.stopPropagation();
    toggleNotifications();
  });

  notifClearBtn?.addEventListener("click", () => {
    notifications = [];
    renderNotificationUI();
    closeNotifications();
  });

  // Click en una notificación → ir a la sección y marcarla como leída
  notifList?.addEventListener("click", (e) => {
    const item = e.target.closest(".notif-item");
    if (!item) return;

    const notifId = item.dataset.id;
    const targetSection = item.dataset.targetSection;

    if (notifId) {
      notifications = notifications.filter((n) => String(n.id) !== notifId);
      renderNotificationUI();
    }

    if (targetSection) {
      goToSection(targetSection);
    }

    closeNotifications();
  });

  // Cerrar al hacer click fuera
  document.addEventListener("click", (e) => {
    if (!notifDropdown || notifDropdown.classList.contains("hidden")) return;

    const isBell = notifBell?.contains(e.target);
    const isPanel = notifDropdown.contains(e.target);
    if (!isBell && !isPanel) {
      closeNotifications();
    }
  });

  /* ===== SIDEBAR MOBILE con burger ===== */
  const burgerCheckbox = document.getElementById("burgerToggle");
  if (burgerCheckbox) {
    burgerCheckbox.addEventListener("change", () => {
      if (burgerCheckbox.checked) {
        document.body.classList.add("sidebar-open");
      } else {
        document.body.classList.remove("sidebar-open");
      }
    });
  }

  const initialSection = document.querySelector(
    '.page-section.active[data-section]'
  );
  if (initialSection) {
    const target = initialSection.dataset.section;
    if (target === "mesas") {
      initMesas();
    } else if (target === "productos") {
      initProductos();
    } else if (target === "inventario") {
      initInventario();
    } else if (target === "reservas") {
      initReservas();
    } else if (target === "usuarios") {
      initUsuarios();
    } else if (target === "reportes") {
      initReportes();
    } else if (target === "configuracion") {
      initConfiguracion();
    }
  }

  /* ===== DASHBOARD: VENTAS / RESERVAS / ACTIVIDADES / TOP PRODUCTOS ===== */

  const ventasData = {
    hoy: [15, 22, 40, 60, 55, 48, 30, 25],
    semana: [700, 850, 640, 900, 760, 820, 950],
    mes: [3200, 4100, 3800, 4500, 3900, 4200, 4700, 4300, 4800, 5000],
  };

  const ventasCanvas = document.getElementById("ventasChart");
  const ventasPeriodoLabel = document.getElementById("ventasPeriodoLabel");
  const ventasSubtitle = document.getElementById("ventasSubtitle");
  const periodoButtons = document.querySelectorAll(
    "#periodoControl .radio-pill"
  );

  let currentPeriodo = "hoy";

  function getCanvasSize(canvas) {
    const w = canvas.parentElement.clientWidth;
    const h = 300; // alto fijo
    canvas.width = w;
    canvas.height = h;
    return { width: w, height: h };
  }

  function clearCanvas(ctx, w, h) {
    ctx.clearRect(0, 0, w, h);
  }

  function getLabelsForPeriodo(periodo, length) {
    const now = new Date();
    if (periodo === "hoy") {
      const startHour = 10;
      return Array.from({ length }, (_, i) => `${startHour + i}:00`);
    }

    if (periodo === "semana") {
      return Array.from({ length }, (_, i) => {
        const d = new Date(now);
        d.setDate(now.getDate() - (length - 1 - i));
        const dia = d.getDate().toString().padStart(2, "0");
        const mes = (d.getMonth() + 1).toString().padStart(2, "0");
        return `${dia}/${mes}`;
      });
    }

    return Array.from({ length }, (_, i) => {
      const d = new Date(now);
      d.setDate(now.getDate() - (length - 1 - i) * 3);
      const dia = d.getDate().toString().padStart(2, "0");
      const mes = (d.getMonth() + 1).toString().padStart(2, "0");
      return `${dia}/${mes}`;
    });
  }

  function setVentasSubtitle(periodo) {
    if (!ventasSubtitle) return;
    if (periodo === "hoy") {
      ventasSubtitle.textContent = "Rendimiento por hora (hoy).";
    } else if (periodo === "semana") {
      ventasSubtitle.textContent = "Rendimiento por día (últimos 7 días).";
    } else {
      ventasSubtitle.textContent =
        "Rendimiento por bloques de días (últimos 30 días).";
    }
  }

  function renderVentasChart(periodo) {
    if (!ventasCanvas) return;
    const { width, height } = getCanvasSize(ventasCanvas);
    const ctx = ventasCanvas.getContext("2d");
    clearCanvas(ctx, width, height);

    const data = ventasData[periodo] || ventasData.hoy;
    const labels = getLabelsForPeriodo(periodo, data.length);
    const max = Math.max(...data) || 1;
    const paddingX = 40;
    const paddingY = 30;
    const chartWidth = width - paddingX * 2;
    const chartHeight = height - paddingY * 2;
    const barWidth = chartWidth / data.length - 12;

    ctx.fillStyle = "#0b1017";
    ctx.fillRect(0, 0, width, height);

    ctx.strokeStyle = "#1f2937";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(paddingX, paddingY);
    ctx.lineTo(paddingX, paddingY + chartHeight);
    ctx.lineTo(paddingX + chartWidth, paddingY + chartHeight);
    ctx.stroke();

    data.forEach((value, index) => {
      const x =
        paddingX +
        index * (chartWidth / data.length) +
        (chartWidth / data.length - barWidth) / 2;
      const barHeight = (value / max) * (chartHeight - 10);
      const y = paddingY + chartHeight - barHeight;

      ctx.fillStyle = "#84b067";
      ctx.fillRect(x, y, barWidth, barHeight);

      ctx.fillStyle = "#9ca3af";
      ctx.font = "10px system-ui";
      ctx.textAlign = "center";
      ctx.fillText(value, x + barWidth / 2, y - 4);
    });

    ctx.fillStyle = "#9ca3af";
    ctx.font = "10px system-ui";
    ctx.textAlign = "center";
    labels.forEach((label, index) => {
      const x =
        paddingX +
        index * (chartWidth / data.length) +
        (chartWidth / data.length) / 2;
      const y = paddingY + chartHeight + 14;
      ctx.fillText(label, x, y);
    });

    if (ventasPeriodoLabel) {
      ventasPeriodoLabel.textContent =
        periodo === "hoy"
          ? "Hoy"
          : periodo === "semana"
          ? "Semana"
          : "Mes";
    }
    setVentasSubtitle(periodo);
  }

  periodoButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      const periodo = btn.dataset.periodo;
      if (!periodo || periodo === currentPeriodo) return;

      periodoButtons.forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      currentPeriodo = periodo;
      renderVentasChart(periodo);
    });
  });

  renderVentasChart(currentPeriodo);
  window.addEventListener("resize", () => renderVentasChart(currentPeriodo));

  const estadoCajaBtn = document.getElementById("estadoCajaBtn");
  let cajaOnline = false;

  function renderCajaEstado() {
    if (!estadoCajaBtn) return;
    estadoCajaBtn.classList.toggle("estado-caja--online", cajaOnline);
    estadoCajaBtn.classList.toggle("estado-caja--offline", !cajaOnline);
    estadoCajaBtn.textContent = cajaOnline ? "Caja en línea" : "Caja cerrada";
  }

  if (estadoCajaBtn) {
    estadoCajaBtn.addEventListener("click", () => {
      cajaOnline = !cajaOnline;
      renderCajaEstado();
    });
    renderCajaEstado();
  }

  const reservasList = document.getElementById("reservasList");
  if (reservasList) {
    const reservasDemo = [
      {
        nombre: "Juan Pérez",
        mesa: "Mesa 4",
        personas: 2,
        fecha: "Hoy · 19:30",
      },
      {
        nombre: "Ana López",
        mesa: "Mesa 7",
        personas: 4,
        fecha: "Hoy · 20:00",
      },
      {
        nombre: "Carlos Díaz",
        mesa: "Terraza 1",
        personas: 3,
        fecha: "Hoy · 21:15",
      },
    ];

    reservasList.innerHTML = reservasDemo
      .map(
        (r) => `
      <li class="reserva-item">
        <div class="reserva-main">
          <span class="reserva-title">${r.nombre}</span>
          <span class="reserva-meta">${r.fecha} · ${r.mesa} · ${r.personas} personas</span>
        </div>
        <span class="reserva-tag">Reserva</span>
      </li>`
      )
      .join("");
  }

  const activityList = document.getElementById("activityList");
  if (activityList) {
    const actividadesDemo = [
      {
        titulo: "Apertura de caja",
        meta: "Hoy · 09:00 · Usuario: admin",
        tag: "Caja",
      },
      {
        titulo: "Nueva reserva",
        meta: "Hoy · 09:30 · Mesa 4 · 2 personas · Usuario: karady",
        tag: "Reservas",
      },
      {
        titulo: "Comanda enviada",
        meta: "Hoy · 09:45 · Mesa 2 · 3 ítems · Usuario: mozo01",
        tag: "Comandas",
      },
      {
        titulo: "Nuevo usuario",
        meta: "Ayer · 18:00 · mozo01 creado por admin",
        tag: "Usuarios",
      },
    ];

    activityList.innerHTML = actividadesDemo
      .map(
        (a) => `
      <li class="activity-item">
        <div class="activity-main">
          <span class="activity-title">${a.titulo}</span>
          <span class="activity-meta">${a.meta}</span>
        </div>
        <span class="activity-tag">${a.tag}</span>
      </li>`
      )
      .join("");
  }

  const topProductosList = document.getElementById("topProductosList");
  if (topProductosList) {
    const productosDemo = [
      { nombre: "Hamburguesa clásica", ventas: 120 },
      { nombre: "Pizza pepperoni", ventas: 98 },
      { nombre: "Alitas BBQ", ventas: 76 },
      { nombre: "Papas fritas", ventas: 65 },
      { nombre: "Refresco cola", ventas: 60 },
    ];

    topProductosList.innerHTML = productosDemo
      .map(
        (p) => `
      <li class="topproductos-item">
        <span class="topproductos-nombre">${p.nombre}</span>
        <span class="topproductos-ventas">${p.ventas} ventas</span>
      </li>`
      )
      .join("");
  }

  /* ===== MESAS ===== */
  const TOTAL_SLOTS_DEFAULT = 40;

  let zonas = [
    {
      id: "planta-baja",
      nombre: "Planta baja",
      totalSlots: TOTAL_SLOTS_DEFAULT,
    },
    { id: "piso-1", nombre: "Piso 1", totalSlots: TOTAL_SLOTS_DEFAULT },
    { id: "jardin", nombre: "Jardín", totalSlots: TOTAL_SLOTS_DEFAULT },
  ];

  let mesas = [
    {
      id: 1,
      numero: "Mesa 1",
      zonaId: "planta-baja",
      estado: "Libre",
      capacidad: 2,
      disponible: true,
      combinada: false,
      activa: true,
      slotIndex: 0,
      grupoId: null,
      esPrincipal: false,
    },
    {
      id: 2,
      numero: "Mesa 2",
      zonaId: "planta-baja",
      estado: "Ocupada",
      capacidad: 4,
      disponible: true,
      combinada: false,
      activa: true,
      slotIndex: 1,
      grupoId: null,
      esPrincipal: false,
    },
    {
      id: 3,
      numero: "Terraza 1",
      zonaId: "jardin",
      estado: "Reservada",
      capacidad: 4,
      disponible: true,
      combinada: false,
      activa: true,
      slotIndex: 0,
      grupoId: null,
      esPrincipal: false,
    },
  ];

  let mesaEditandoId = null;
  let mesaModalId = null;
  let zonaActualId = zonas[0].id;
  let modoSeleccion = false;
  let mesasSeleccionadas = [];

  const filtroBusquedaMesa = document.getElementById("filtroBusquedaMesa");
  const filtroEstadoMesa = document.getElementById("filtroEstadoMesa");
  const btnMostrarFormMesa = document.getElementById("btnMostrarFormMesa");

  const mesaFormSection = document.getElementById("mesaFormSection");
  const mesaFormTitulo = document.getElementById("mesaFormTitulo");
  const mesaForm = document.getElementById("mesaForm");

  const inputNumero = document.getElementById("mesaNumero");
  const selectZona = document.getElementById("mesaZona");
  const selectEstado = document.getElementById("mesaEstado");
  const inputCapacidad = document.getElementById("mesaCapacidad");
  const btnCancelar = document.getElementById("mesaCancelar");

  const mesasTableBody = document.getElementById("mesasTableBody");

  const mapaZonaSelect = document.getElementById("mapaZonaSelect");
  const btnNuevaZona = document.getElementById("btnNuevaZona");
  const btnSeleccionarMesas = document.getElementById("btnSeleccionarMesas");
  const btnCombinarSeleccionadas = document.getElementById("btnCombinarSeleccionadas");
  const btnSepararGrupo = document.getElementById("btnSepararGrupo");
  const mapaMesasGrid = document.getElementById("mapaMesasGrid");

  const mesaModal = document.getElementById("mesaModal");
  const modalBackdrop = mesaModal?.querySelector(".modal-backdrop");
  const modalCloseBtns =
    mesaModal?.querySelectorAll("[data-close-modal]") || [];

  const modalTituloMesa = document.getElementById("mesaModalTituloMesa");
  const modalNumero = document.getElementById("mesaModalNumero");
  const modalZona = document.getElementById("mesaModalZona");
  const modalCapacidad = document.getElementById("mesaModalCapacidad");
  const modalEstadoBadge = document.getElementById("mesaModalEstadoBadge");
  const modalEstadoChips =
    mesaModal?.querySelectorAll(".estado-chip") || [];

  const btnModalEliminar = document.getElementById("mesaModalEliminar");
  const btnModalGuardar = document.getElementById("mesaModalGuardar");

  const findZonaById = (id) => zonas.find((z) => z.id === id);
  const findMesaById = (id) => mesas.find((m) => m.id === id);

  function findFirstFreeSlot(zonaId, totalSlots) {
    const ocupados = new Set(
      mesas
        .filter((m) => m.zonaId === zonaId && m.slotIndex !== null)
        .map((m) => m.slotIndex)
    );
    for (let i = 0; i < totalSlots; i++) {
      if (!ocupados.has(i)) return i;
    }
    return null;
  }

  const generarIdMesa = () =>
    mesas.length ? Math.max(...mesas.map((m) => m.id)) + 1 : 1;

  function getEstadoBadgeClass(estado) {
    if (estado === "Libre") return "badge badge--libre";
    if (estado === "Ocupada") return "badge badge--ocupada";
    if (estado === "Reservada") return "badge badge--reservada";
    return "badge";
  }

  function getPillEstadoClass(estado) {
    if (estado === "Libre") return "mesa-pill mesa-pill--libre";
    if (estado === "Ocupada") return "mesa-pill mesa-pill--ocupada";
    if (estado === "Reservada") return "mesa-pill mesa-pill--reservada";
    return "mesa-pill";
  }

  function renderSelectZonas() {
    if (!selectZona || !mapaZonaSelect || !modalZona) return;

    selectZona.innerHTML = "";
    mapaZonaSelect.innerHTML = "";
    modalZona.innerHTML = "";

    zonas.forEach((zona) => {
      const o1 = new Option(zona.nombre, zona.id);
      const o2 = new Option(zona.nombre, zona.id);
      const o3 = new Option(zona.nombre, zona.id);
      selectZona.add(o1);
      mapaZonaSelect.add(o2);
      modalZona.add(o3);
    });

    if (!zonas.some((z) => z.id === zonaActualId)) {
      zonaActualId = zonas[0]?.id || "";
    }

    if (zonaActualId) {
      mapaZonaSelect.value = zonaActualId;
      selectZona.value = zonaActualId;
    }
  }

  function renderTablaMesas() {
    if (!mesasTableBody) return;

    const texto = (filtroBusquedaMesa?.value || "").toLowerCase();
    const estadoFiltro = filtroEstadoMesa?.value || "todos";

    mesasTableBody.innerHTML = "";

    mesas
      .slice()
      .sort((a, b) => a.id - b.id)
      .forEach((mesa, index) => {
        const zonaNombre = findZonaById(mesa.zonaId)?.nombre || "N/D";

        const coincideTexto =
          !texto ||
          mesa.numero.toLowerCase().includes(texto) ||
          zonaNombre.toLowerCase().includes(texto);

        const coincideEstado =
          estadoFiltro === "todos" || mesa.estado === estadoFiltro;

        if (!coincideTexto || !coincideEstado) return;

        const tr = document.createElement("tr");
        tr.innerHTML = `
          <td>${index + 1}</td>
          <td>${mesa.numero}</td>
          <td>${zonaNombre}</td>
          <td>
            <span class="${getEstadoBadgeClass(mesa.estado)}">
              ${mesa.estado}
            </span>
          </td>
          <td>${mesa.capacidad}</td>
          <td>
            <label class="mini-switch">
              <input
                type="checkbox"
                class="mini-switch-input"
                data-comb-id="${mesa.id}"
                ${mesa.combinada ? "checked" : ""}
              />
              <span class="mini-switch-slider"></span>
            </label>
          </td>
          <td>
            <label class="mini-switch">
              <input
                type="checkbox"
                class="mini-switch-input"
                data-activa-id="${mesa.id}"
                ${mesa.activa ? "checked" : ""}
              />
              <span class="mini-switch-slider"></span>
            </label>
          </td>
          <td>
            <div class="actions-cell">
              <button class="action-btn" data-edit="${mesa.id}">Editar</button>
              <button class="action-btn" data-delete="${mesa.id}">🗑</button>
            </div>
          </td>
        `;
        mesasTableBody.appendChild(tr);
      });

    mesasTableBody.querySelectorAll("[data-edit]").forEach((btn) =>
      btn.addEventListener("click", () =>
        abrirEdicionMesa(Number(btn.getAttribute("data-edit")))
      )
    );

    mesasTableBody.querySelectorAll("[data-delete]").forEach((btn) =>
      btn.addEventListener("click", () =>
        eliminarMesa(Number(btn.getAttribute("data-delete")))
      )
    );

    mesasTableBody
      .querySelectorAll('.mini-switch-input[data-comb-id]')
      .forEach((input) => {
        input.addEventListener("change", () => {
          const id = Number(input.getAttribute("data-comb-id"));
          const mesa = findMesaById(id);
          if (!mesa) return;
          mesa.combinada = input.checked;
          renderTablaMesas();
        });
      });

    mesasTableBody
      .querySelectorAll('.mini-switch-input[data-activa-id]')
      .forEach((input) => {
        input.addEventListener("change", () => {
          const id = Number(input.getAttribute("data-activa-id"));
          const mesa = findMesaById(id);
          if (!mesa) return;
          mesa.activa = input.checked;
          renderTablaMesas();
          renderMapaMesas();
        });
      });
  }

  function renderMapaMesas() {
    if (!mapaMesasGrid || !zonaActualId) return;
    const zona = findZonaById(zonaActualId);
    if (!zona) return;

    mapaMesasGrid.innerHTML = "";

    for (let i = 0; i < zona.totalSlots; i++) {
      const slot = document.createElement("div");
      slot.className = "mapa-slot";

      const mesaEnSlot = mesas.find(
        (m) => m.zonaId === zona.id && m.slotIndex === i && m.activa
      );

      if (mesaEnSlot) {
        const pill = document.createElement("div");
        pill.className = getPillEstadoClass(mesaEnSlot.estado);
        pill.textContent = mesaEnSlot.numero;
        pill.draggable = true;
        pill.dataset.mesaId = String(mesaEnSlot.id);

        // Agregar clase combinada si pertenece a un grupo
        if (mesaEnSlot.grupoId) {
          pill.classList.add("combinada");
        }

        // Agregar clase selected si está en el array de seleccionadas
        if (mesasSeleccionadas.includes(mesaEnSlot.id)) {
          pill.classList.add("selected");
        }

        pill.addEventListener("dragstart", (e) => {
          e.dataTransfer?.setData("text/plain", String(mesaEnSlot.id));
        });

        pill.addEventListener("click", () => {
          if (modoSeleccion) {
            toggleSeleccionMesa(mesaEnSlot.id);
          } else {
            abrirMesaModal(mesaEnSlot.id);
          }
        });

        slot.appendChild(pill);
      }

      slot.addEventListener("dragover", (e) => {
        e.preventDefault();
        slot.classList.add("drag-over");
      });
      slot.addEventListener("dragleave", () => {
        slot.classList.remove("drag-over");
      });
      slot.addEventListener("drop", (e) => {
        e.preventDefault();
        slot.classList.remove("drag-over");
        const mesaId = Number(e.dataTransfer?.getData("text/plain"));
        if (!Number.isNaN(mesaId)) {
          moverMesaEnMapa(mesaId, i);
        }
      });

      mapaMesasGrid.appendChild(slot);
    }
  }

  function mostrarFormMesa(modo) {
    mesaFormSection?.classList.remove("hidden");
    mesaFormTitulo.textContent =
      modo === "editar" ? "Editar mesa" : "Nueva mesa";
  }

  function ocultarFormMesa() {
    mesaFormSection?.classList.add("hidden");
    mesaEditandoId = null;
    mesaForm?.reset();
    if (selectZona && zonaActualId) selectZona.value = zonaActualId;
    if (selectEstado) selectEstado.value = "Libre";
  }

  function abrirEdicionMesa(id) {
    const mesa = findMesaById(id);
    if (!mesa) return;

    mesaEditandoId = id;
    mostrarFormMesa("editar");

    inputNumero.value = mesa.numero;
    selectZona.value = mesa.zonaId;
    selectEstado.value = mesa.estado;
    inputCapacidad.value = String(mesa.capacidad);
  }

  function eliminarMesa(id) {
    if (!confirm("¿Eliminar esta mesa?")) return;
    mesas = mesas.filter((m) => m.id !== id);
    if (mesaModalId === id) cerrarMesaModal();
    renderTablaMesas();
    renderMapaMesas();
  }

  function moverMesaEnMapa(mesaId, slotIndex) {
    const mesa = findMesaById(mesaId);
    const zona = findZonaById(zonaActualId);
    if (!mesa || !zona) return;

    mesa.zonaId = zona.id;
    mesa.slotIndex = slotIndex;

    renderTablaMesas();
    renderMapaMesas();
  }

  function abrirMesaModal(id) {
    const mesa = findMesaById(id);
    if (!mesa || !mesaModal) return;

    mesaModalId = id;
    mesaModal.classList.remove("hidden");

    modalTituloMesa.textContent = mesa.numero;
    modalNumero.value = mesa.numero;
    modalCapacidad.value = String(mesa.capacidad);

    modalZona.innerHTML = "";
    zonas.forEach((z) => {
      const opt = new Option(z.nombre, z.id);
      modalZona.add(opt);
    });
    modalZona.value = mesa.zonaId;

    actualizarBadgeEstadoModal(mesa.estado);
    modalEstadoChips.forEach((chip) =>
      chip.classList.toggle("active", chip.dataset.estado === mesa.estado)
    );
  }

  function cerrarMesaModal() {
    if (!mesaModal) return;
    mesaModal.classList.add("hidden");
    mesaModalId = null;
  }

  function actualizarBadgeEstadoModal(estado) {
    modalEstadoBadge.textContent = estado;
    modalEstadoBadge.className = getEstadoBadgeClass(estado);
  }

  modalBackdrop?.addEventListener("click", cerrarMesaModal);
  modalCloseBtns.forEach((btn) =>
    btn.addEventListener("click", cerrarMesaModal)
  );

  modalEstadoChips.forEach((chip) => {
    chip.addEventListener("click", () => {
      const estado = chip.dataset.estado;
      if (!estado || mesaModalId == null) return;
      const mesa = findMesaById(mesaModalId);
      if (!mesa) return;

      mesa.estado = estado;
      actualizarBadgeEstadoModal(estado);

      modalEstadoChips.forEach((c) => c.classList.remove("active"));
      chip.classList.add("active");

      renderTablaMesas();
      renderMapaMesas();
    });
  });

  btnModalEliminar?.addEventListener("click", () => {
    if (mesaModalId == null) return;
    eliminarMesa(mesaModalId);
  });

  btnModalGuardar?.addEventListener("click", () => {
    if (mesaModalId == null) return;
    const mesa = findMesaById(mesaModalId);
    if (!mesa) return;

    const nuevaCap = Number(modalCapacidad.value) || 1;

    // Validación de capacidad
    if (nuevaCap < 1) {
      alert("La capacidad no puede ser menor a 1.");
      return;
    }

    mesa.capacidad = nuevaCap;
    const nuevaZonaId = modalZona.value;

    if (mesa.zonaId !== nuevaZonaId) {
      const zona = findZonaById(nuevaZonaId);
      const slotLibre = findFirstFreeSlot(
        nuevaZonaId,
        zona?.totalSlots || TOTAL_SLOTS_DEFAULT
      );
      mesa.zonaId = nuevaZonaId;
      mesa.slotIndex = slotLibre;
      zonaActualId = nuevaZonaId;
      if (mapaZonaSelect) mapaZonaSelect.value = nuevaZonaId;
    }

    renderTablaMesas();
    renderMapaMesas();
    cerrarMesaModal();
  });

  btnMostrarFormMesa?.addEventListener("click", () => {
    mesaEditandoId = null;
    mostrarFormMesa("crear");
  });

  btnCancelar?.addEventListener("click", ocultarFormMesa);

  mesaForm?.addEventListener("submit", (e) => {
    e.preventDefault();

    const numero = inputNumero.value.trim();
    const zonaId = selectZona.value;
    const estado = selectEstado.value;
    const capacidad = Number(inputCapacidad.value) || 1;
    const disponible = true;

    if (!numero || !zonaId) return;

    // Validación de capacidad
    if (capacidad < 1) {
      alert("La capacidad no puede ser menor a 1.");
      return;
    }

    const duplicada = mesas.some(
      (m) =>
        m.numero.toLowerCase() === numero.toLowerCase() &&
        m.zonaId === zonaId &&
        (!mesaEditandoId || m.id !== mesaEditandoId)
    );
    if (duplicada) {
      alert("Ya existe una mesa con ese nombre en esa zona.");
      return;
    }

    if (mesaEditandoId) {
      const mesa = findMesaById(mesaEditandoId);
      if (!mesa) return;

      if (mesa.zonaId !== zonaId) {
        const zona = findZonaById(zonaId);
        mesa.slotIndex = findFirstFreeSlot(
          zonaId,
          zona?.totalSlots || TOTAL_SLOTS_DEFAULT
        );
      }

      mesa.numero = numero;
      mesa.zonaId = zonaId;
      mesa.estado = estado;
      mesa.capacidad = capacidad;
      mesa.disponible = disponible;
    } else {
      const zona = findZonaById(zonaId);
      const slotLibre = findFirstFreeSlot(
        zonaId,
        zona?.totalSlots || TOTAL_SLOTS_DEFAULT
      );

      mesas.push({
        id: generarIdMesa(),
        numero,
        zonaId,
        estado,
        capacidad,
        disponible,
        combinada: false,
        activa: true,
        slotIndex: slotLibre,
      });
    }
    ocultarFormMesa();
    renderTablaMesas();
    renderMapaMesas();
  });

  filtroBusquedaMesa?.addEventListener("input", renderTablaMesas);
  filtroEstadoMesa?.addEventListener("change", renderTablaMesas);

  mapaZonaSelect?.addEventListener("change", () => {
    zonaActualId = mapaZonaSelect.value;
    renderMapaMesas();
  });

  btnNuevaZona?.addEventListener("click", () => {
    const nombre = prompt("Nombre de la nueva zona:");
    if (!nombre) return;

    const id = nombre
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .replace(/\s+/g, "-")
      .replace(/[^a-z0-9\-]/g, "");

    if (zonas.some((z) => z.id === id)) {
      alert("Ya existe una zona con ese nombre.");
      return;
    }

    zonas.push({ id, nombre, totalSlots: TOTAL_SLOTS_DEFAULT });
    zonaActualId = id;

    renderSelectZonas();
    renderMapaMesas();
  });

  // === FUNCIONES DE SELECCIÓN Y COMBINACIÓN DE MESAS ===

  function toggleSeleccionMesa(mesaId) {
    const index = mesasSeleccionadas.indexOf(mesaId);
    if (index > -1) {
      mesasSeleccionadas.splice(index, 1);
    } else {
      mesasSeleccionadas.push(mesaId);
    }
    renderMapaMesas();
    actualizarBotonCombinar();
  }

  function actualizarBotonCombinar() {
    if (btnCombinarSeleccionadas) {
      btnCombinarSeleccionadas.style.display =
        mesasSeleccionadas.length >= 2 ? "inline-block" : "none";
    }
  }

  function activarModoSeleccion() {
    modoSeleccion = !modoSeleccion;

    if (modoSeleccion) {
      btnSeleccionarMesas?.classList.add("btn--primary");
      btnSeleccionarMesas?.classList.remove("btn--ghost");
      if (btnSeleccionarMesas) btnSeleccionarMesas.textContent = "Cancelar selección";
    } else {
      btnSeleccionarMesas?.classList.remove("btn--primary");
      btnSeleccionarMesas?.classList.add("btn--ghost");
      if (btnSeleccionarMesas) btnSeleccionarMesas.textContent = "Seleccionar mesas";
      mesasSeleccionadas = [];
      actualizarBotonCombinar();
      renderMapaMesas();
    }
  }

  function combinarMesasSeleccionadas() {
    if (mesasSeleccionadas.length < 2) {
      alert("Debes seleccionar al menos 2 mesas para combinar.");
      return;
    }

    // Verificar que todas estén activas
    const mesasACombinar = mesas.filter(m => mesasSeleccionadas.includes(m.id));
    if (mesasACombinar.some(m => !m.activa)) {
      alert("Solo puedes combinar mesas activas.");
      return;
    }

    // Crear grupo
    const grupoId = "grupo-" + Date.now();

    // Asignar grupo a todas las mesas
    mesasACombinar.forEach((mesa, index) => {
      mesa.grupoId = grupoId;
      mesa.esPrincipal = index === 0; // Primera mesa es la principal
      mesa.combinada = true;
    });

    // Resetear modo selección
    modoSeleccion = false;
    mesasSeleccionadas = [];
    activarModoSeleccion();
    renderMapaMesas();
    renderTablaMesas();

    alert(`${mesasACombinar.length} mesas combinadas exitosamente.`);
  }

  function separarGrupo() {
    const mesaId = prompt("Ingresa el número de una mesa del grupo a separar:");
    if (!mesaId) return;

    const mesaBuscada = mesas.find(m =>
      m.numero.toLowerCase() === mesaId.toLowerCase()
    );

    if (!mesaBuscada) {
      alert("Mesa no encontrada.");
      return;
    }

    if (!mesaBuscada.grupoId) {
      alert("Esta mesa no pertenece a ningún grupo combinado.");
      return;
    }

    const grupoId = mesaBuscada.grupoId;
    const mesasDelGrupo = mesas.filter(m => m.grupoId === grupoId);

    if (!confirm(`¿Separar el grupo de ${mesasDelGrupo.length} mesas?`)) {
      return;
    }

    // Separar todas las mesas del grupo
    mesasDelGrupo.forEach(mesa => {
      mesa.grupoId = null;
      mesa.esPrincipal = false;
      mesa.combinada = false;
    });

    renderMapaMesas();
    renderTablaMesas();

    alert("Grupo separado exitosamente.");
  }

  // Event listeners para botones de combinación
  btnSeleccionarMesas?.addEventListener("click", activarModoSeleccion);
  btnCombinarSeleccionadas?.addEventListener("click", combinarMesasSeleccionadas);
  btnSepararGrupo?.addEventListener("click", separarGrupo);

  function initMesas() {
    renderSelectZonas();
    renderTablaMesas();
    renderMapaMesas();
  }

  initMesas();

  /* ===== INVENTARIO ===== */

  let categoriasInsumos = [
    { id: "alimentos-secos", nombre: "Alimentos secos" },
    { id: "vegetales", nombre: "Vegetales" },
    { id: "limpieza", nombre: "Limpieza" },
  ];

  let insumos = [
    {
      id: 1,
      nombre: "Harina de trigo",
      categoriaId: "alimentos-secos",
      unidad: "kg",
      stockActual: 25,
      stockMinimo: 10,
      nota: "Saco 25kg",
    },
    {
      id: 2,
      nombre: "Tomate",
      categoriaId: "vegetales",
      unidad: "kg",
      stockActual: 4,
      stockMinimo: 5,
      nota: "",
    },
  ];

  // Filtros
  const filtroBusquedaInsumo = document.getElementById("filtroBusquedaInsumo");
  const filtroCategoriaInsumo = document.getElementById("filtroCategoriaInsumo");
  const btnResetFiltrosInsumo = document.getElementById("btnResetFiltrosInsumo");

  // Formulario
  const insumoFormSection = document.getElementById("insumoFormSection");
  const insumoFormTitulo = document.getElementById("insumoFormTitulo");
  const insumoForm = document.getElementById("insumoForm");
  const insumoNombre = document.getElementById("insumoNombre");
  const insumoCategoria = document.getElementById("insumoCategoria");
  const insumoUnidad = document.getElementById("insumoUnidad");
  const insumoNota = document.getElementById("insumoNota");
  const insumoStock = document.getElementById("insumoStock");
  const insumoStockMin = document.getElementById("insumoStockMin");
  const insumoCancelar = document.getElementById("insumoCancelar");
  const btnMostrarFormInsumo = document.getElementById("btnMostrarFormInsumo");

  // Tabla + alertas
  const insumosTableBody = document.getElementById("insumosTableBody");
  const insumoStockAlertList = document.getElementById("insumoStockAlertList");

  // Modal categorías insumos
  const insumoCategoriasModal = document.getElementById("insumoCategoriasModal");
  const insumoCategoriasModalBackdrop = document.getElementById("insumoCategoriasModalBackdrop");
  const insumoCategoriasModalCerrar = document.getElementById("insumoCategoriasModalCerrar");
  const btnInsumoCategorias = document.getElementById("btnInsumoCategorias");

  const insumoCategoriasTableBody = document.getElementById("insumoCategoriasTableBody");
  const insumoCatNombreInput = document.getElementById("insumoCatNombreInput");
  const insumoCatGuardarBtn = document.getElementById("insumoCatGuardarBtn");
  const insumoCatCancelarEdicionBtn = document.getElementById("insumoCatCancelarEdicionBtn");

  let insumoEditandoId = null;
  let insumoCategoriaEditandoId = null;

  // Funciones auxiliares
  const generarIdInsumo = () =>
    insumos.length ? Math.max(...insumos.map((i) => i.id)) + 1 : 1;

  const findCategoriaInsumoById = (id) =>
    categoriasInsumos.find((c) => c.id === id);

  function renderSelectCategoriasInsumo() {
    if (!filtroCategoriaInsumo || !insumoCategoria) return;

    // Filtro
    filtroCategoriaInsumo.innerHTML = "";
    const optAll = new Option("Todas", "todas");
    filtroCategoriaInsumo.add(optAll);

    // Select del formulario
    insumoCategoria.innerHTML = "";

    categoriasInsumos.forEach((c) => {
      const o1 = new Option(c.nombre, c.id);
      const o2 = new Option(c.nombre, c.id);
      filtroCategoriaInsumo.add(o1);
      insumoCategoria.add(o2);
    });

    filtroCategoriaInsumo.value = "todas";
  }

  function mostrarFormInsumo(modo) {
    if (!insumoFormSection) return;
    insumoFormSection.classList.remove("hidden");
    insumoFormTitulo.textContent =
      modo === "editar" ? "Editar insumo" : "Nuevo insumo";
  }

  function ocultarFormInsumo() {
    if (!insumoFormSection) return;
    insumoFormSection.classList.add("hidden");
    insumoEditandoId = null;
    insumoForm?.reset();
    if (insumoStock) insumoStock.value = "0";
    if (insumoStockMin) insumoStockMin.value = "5";
  }

  function renderInsumoStockAlerts() {
    if (!insumoStockAlertList) return;

    const enAlerta = insumos.filter(
      (i) =>
        i.stockMinimo > 0 &&
        i.stockActual <= i.stockMinimo
    );

    insumoStockAlertList.innerHTML = "";

    // 🔔 Sin alertas → limpiar notificaciones de tipo "inventario"
    if (!enAlerta.length) {
      const li = document.createElement("li");
      li.className = "stock-alert-item";
      li.innerHTML =
        '<span class="stock-alert-meta">Sin alertas por el momento.</span>';
      insumoStockAlertList.appendChild(li);

      // Vaciar notificaciones de inventario
      updateNotifications("inventario", []);
      setNavBadge("inventario", 0);
      return;
    }

    const notifItems = [];

    enAlerta.forEach((i) => {
      const catNombre =
        findCategoriaInsumoById(i.categoriaId)?.nombre || "Sin categoría";

      const li = document.createElement("li");
      li.className = "stock-alert-item";
      li.innerHTML = `
        <span class="stock-alert-name">${i.nombre}</span>
        <span class="stock-alert-meta">${catNombre} · ${i.stockActual} ${i.unidad} / min ${i.stockMinimo}</span>
        <span class="stock-alert-badge">Stock bajo</span>
      `;
      insumoStockAlertList.appendChild(li);

      // Para la campanita
      notifItems.push({
        id: `inv-${i.id}`,
        type: "inventario",
        label: `Stock bajo: ${i.nombre}`,
        detail: `${catNombre} · ${i.stockActual} ${i.unidad} / min ${i.stockMinimo}`,
        tag: "Inventario",
        target: "inventario",
      });
    });

    // 🔔 Actualizar notificaciones globales (tipo inventario)
    updateNotifications("inventario", notifItems);

    // 🔢 Actualizar número en el menú lateral
    setNavBadge("inventario", enAlerta.length);
  }

  function renderTablaInsumos() {
    if (!insumosTableBody) return;

    const texto = (filtroBusquedaInsumo?.value || "").toLowerCase();
    const cat = filtroCategoriaInsumo?.value || "todas";

    insumosTableBody.innerHTML = "";

    insumos
      .slice()
      .sort((a, b) => a.id - b.id)
      .forEach((i, idx) => {
        const catNombre =
          findCategoriaInsumoById(i.categoriaId)?.nombre || "Sin categoría";

        const coincideTexto =
          !texto ||
          i.nombre.toLowerCase().includes(texto) ||
          catNombre.toLowerCase().includes(texto);

        const coincideCat = cat === "todas" || i.categoriaId === cat;

        if (!coincideTexto || !coincideCat) return;

        const tr = document.createElement("tr");
        tr.innerHTML = `
          <td>${idx + 1}</td>
          <td>${i.nombre}</td>
          <td>${catNombre}</td>
          <td>${i.unidad}</td>
          <td class="price-cell">${i.stockActual}</td>
          <td class="price-cell">${i.stockMinimo}</td>
          <td>
            <div class="actions-cell">
              <button class="action-btn" data-edit-insumo="${i.id}">Editar</button>
              <button class="action-btn" data-del-insumo="${i.id}">🗑</button>
            </div>
          </td>
        `;
        insumosTableBody.appendChild(tr);
      });

    // Eventos de los botones
    insumosTableBody
      .querySelectorAll("[data-edit-insumo]")
      .forEach((btn) => {
        btn.addEventListener("click", () => {
          const id = Number(btn.getAttribute("data-edit-insumo"));
          abrirEdicionInsumo(id);
        });
      });

    insumosTableBody
      .querySelectorAll("[data-del-insumo]")
      .forEach((btn) => {
        btn.addEventListener("click", () => {
          const id = Number(btn.getAttribute("data-del-insumo"));
          eliminarInsumo(id);
        });
      });

    renderInsumoStockAlerts();
  }

  function abrirEdicionInsumo(id) {
    const insumo = insumos.find((i) => i.id === id);
    if (!insumo) return;

    insumoEditandoId = id;
    mostrarFormInsumo("editar");

    insumoNombre.value = insumo.nombre;
    insumoCategoria.value = insumo.categoriaId;
    insumoUnidad.value = insumo.unidad;
    insumoNota.value = insumo.nota || "";
    insumoStock.value = String(insumo.stockActual);
    insumoStockMin.value = String(insumo.stockMinimo);
  }

  function eliminarInsumo(id) {
    if (!confirm("¿Eliminar este insumo?")) return;
    insumos = insumos.filter((i) => i.id !== id);
    renderTablaInsumos();
  }

  insumoForm?.addEventListener("submit", (e) => {
    e.preventDefault();

    const nombre = (insumoNombre.value || "").trim();
    const categoriaId = insumoCategoria.value;
    const unidad = insumoUnidad.value;
    const nota = (insumoNota.value || "").trim();
    const stockActual = Number(insumoStock.value) || 0;
    const stockMinimo = Number(insumoStockMin.value) || 0;

    if (!nombre) {
      alert("El nombre del insumo es obligatorio.");
      return;
    }
    if (!categoriaId) {
      alert("Selecciona una categoría.");
      return;
    }
    if (stockActual < 0 || stockMinimo < 0) {
      alert("El stock no puede ser negativo.");
      return;
    }

    const duplicado = insumos.some(
      (i) =>
        i.nombre.toLowerCase() === nombre.toLowerCase() &&
        i.categoriaId === categoriaId &&
        (!insumoEditandoId || i.id !== insumoEditandoId)
    );
    if (duplicado) {
      alert("Ya existe un insumo con ese nombre en esa categoría.");
      return;
    }

    if (insumoEditandoId) {
      const insumo = insumos.find((i) => i.id === insumoEditandoId);
      if (!insumo) return;

      insumo.nombre = nombre;
      insumo.categoriaId = categoriaId;
      insumo.unidad = unidad;
      insumo.nota = nota;
      insumo.stockActual = stockActual;
      insumo.stockMinimo = stockMinimo;
    } else {
      insumos.push({
        id: generarIdInsumo(),
        nombre,
        categoriaId,
        unidad,
        nota,
        stockActual,
        stockMinimo,
      });
    }

    ocultarFormInsumo();
    renderTablaInsumos();
  });

  btnMostrarFormInsumo?.addEventListener("click", () => {
    insumoEditandoId = null;
    insumoForm?.reset();
    if (insumoStock) insumoStock.value = "0";
    if (insumoStockMin) insumoStockMin.value = "5";
    mostrarFormInsumo("crear");
  });

  insumoCancelar?.addEventListener("click", ocultarFormInsumo);

  filtroBusquedaInsumo?.addEventListener("input", renderTablaInsumos);
  filtroCategoriaInsumo?.addEventListener("change", renderTablaInsumos);
  btnResetFiltrosInsumo?.addEventListener("click", () => {
    if (filtroBusquedaInsumo) filtroBusquedaInsumo.value = "";
    if (filtroCategoriaInsumo) filtroCategoriaInsumo.value = "todas";
    renderTablaInsumos();
  });

  function abrirInsumoCategoriasModal() {
    insumoCategoriaEditandoId = null;
    if (insumoCatNombreInput) insumoCatNombreInput.value = "";
    if (insumoCatGuardarBtn) insumoCatGuardarBtn.textContent = "Añadir";
    insumoCatCancelarEdicionBtn?.classList.add("hidden");
    insumoCategoriasModal?.classList.remove("hidden");
    renderInsumoCategoriasTabla();
    setTimeout(() => insumoCatNombreInput?.focus(), 50);
  }

  function cerrarInsumoCategoriasModal() {
    insumoCategoriasModal?.classList.add("hidden");
  }

  btnInsumoCategorias?.addEventListener("click", abrirInsumoCategoriasModal);
  insumoCategoriasModalCerrar?.addEventListener("click", cerrarInsumoCategoriasModal);
  insumoCategoriasModalBackdrop?.addEventListener("click", cerrarInsumoCategoriasModal);

  function renderInsumoCategoriasTabla() {
    if (!insumoCategoriasTableBody) return;
    insumoCategoriasTableBody.innerHTML = "";

    categoriasInsumos.forEach((cat, idx) => {
      const count = insumos.filter((i) => i.categoriaId === cat.id).length;

      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${idx + 1}</td>
        <td>${cat.nombre}</td>
        <td>${count}</td>
        <td>
          <div class="actions-cell">
            <button class="action-btn" data-edit-insumocat="${cat.id}">Editar</button>
            <button class="action-btn" data-del-insumocat="${cat.id}">🗑</button>
          </div>
        </td>
      `;
      insumoCategoriasTableBody.appendChild(tr);
    });

    insumoCategoriasTableBody
      .querySelectorAll("[data-edit-insumocat]")
      .forEach((btn) => {
        btn.addEventListener("click", () => {
          const id = btn.getAttribute("data-edit-insumocat");
          const cat = categoriasInsumos.find((c) => c.id === id);
          if (!cat) return;
          insumoCategoriaEditandoId = id;
          insumoCatNombreInput.value = cat.nombre;
          insumoCatGuardarBtn.textContent = "Guardar";
          insumoCatCancelarEdicionBtn.classList.remove("hidden");
          insumoCatNombreInput.focus();
        });
      });

    insumoCategoriasTableBody
      .querySelectorAll("[data-del-insumocat]")
      .forEach((btn) => {
        btn.addEventListener("click", () => {
          const id = btn.getAttribute("data-del-insumocat");
          const cat = categoriasInsumos.find((c) => c.id === id);
          if (!cat) return;
          if (
            !confirm(
              `¿Eliminar la categoría "${cat.nombre}"?\nLos insumos quedarán sin categoría.`
            )
          )
            return;

          categoriasInsumos = categoriasInsumos.filter((c) => c.id !== id);
          insumos.forEach((i) => {
            if (i.categoriaId === id) i.categoriaId = "";
          });

          renderSelectCategoriasInsumo();
          renderTablaInsumos();
          renderInsumoCategoriasTabla();
        });
      });
  }

  insumoCatGuardarBtn?.addEventListener("click", () => {
    const nombre = (insumoCatNombreInput.value || "").trim();
    if (!nombre) return;

    const slug = slugify(nombre);
    if (!slug) {
      alert("El nombre no es válido.");
      return;
    }

    const existe = categoriasInsumos.some(
      (c) => c.id === slug && c.id !== insumoCategoriaEditandoId
    );
    if (existe) {
      alert("Ya existe una categoría con un nombre muy similar.");
      return;
    }

    if (insumoCategoriaEditandoId) {
      const cat = categoriasInsumos.find((c) => c.id === insumoCategoriaEditandoId);
      if (!cat) return;
      const oldId = cat.id;
      cat.nombre = nombre;
      cat.id = slug;

      if (oldId !== slug) {
        insumos.forEach((i) => {
          if (i.categoriaId === oldId) i.categoriaId = slug;
        });
      }
    } else {
      categoriasInsumos.push({ id: slug, nombre });
    }

    insumoCategoriaEditandoId = null;
    insumoCatNombreInput.value = "";
    insumoCatGuardarBtn.textContent = "Añadir";
    insumoCatCancelarEdicionBtn.classList.add("hidden");

    renderSelectCategoriasInsumo();
    renderTablaInsumos();
    renderInsumoCategoriasTabla();
  });

  insumoCatCancelarEdicionBtn?.addEventListener("click", () => {
    insumoCategoriaEditandoId = null;
    insumoCatNombreInput.value = "";
    insumoCatGuardarBtn.textContent = "Añadir";
    insumoCatCancelarEdicionBtn.classList.add("hidden");
  });

  function initInventario() {
    renderSelectCategoriasInsumo();
    renderTablaInsumos();
    renderInsumoCategoriasTabla();
  }

  /* ===== RESERVAS ===== */

  let reservas = [
    {
      id: 1,
      cliente: "Juan Pérez",
      telefono: "77712345",
      email: "demo@correo.com",
      personas: 2,
      fecha: new Date().toISOString().slice(0, 10), // hoy
      hora: "19:30",
      mesa: "Mesa 4",
      estado: "pendiente",
      nota: "Aniversario",
    },
  ];

  const reservasTableBody = document.getElementById("reservasTableBody");
  const reservasResumenList = document.getElementById("reservasResumenList");

  const filtroReservaFecha = document.getElementById("filtroReservaFecha");
  const filtroReservaEstado = document.getElementById("filtroReservaEstado");
  const filtroReservaTexto = document.getElementById("filtroReservaTexto");
  const btnResetFiltrosReserva = document.getElementById("btnResetFiltrosReserva");

  const reservaFormSection = document.getElementById("reservaFormSection");
  const reservaFormTitulo = document.getElementById("reservaFormTitulo");
  const reservaForm = document.getElementById("reservaForm");
  const resCliente = document.getElementById("resCliente");
  const resTelefono = document.getElementById("resTelefono");
  const resEmail = document.getElementById("resEmail");
  const resPersonas = document.getElementById("resPersonas");
  const resFecha = document.getElementById("resFecha");
  const resHora = document.getElementById("resHora");
  const resMesa = document.getElementById("resMesa");
  const resEstado = document.getElementById("resEstado");
  const resNota = document.getElementById("resNota");
  const reservaCancelar = document.getElementById("reservaCancelar");
  const btnNuevaReserva = document.getElementById("btnNuevaReserva");

  const btnFechaAyer = document.getElementById("btnFechaAyer");
  const btnFechaHoy = document.getElementById("btnFechaHoy");
  const btnFechaManana = document.getElementById("btnFechaManana");

  const btnCalendarioReserva = document.getElementById("btnCalendarioReserva");
  const calendarioModal = document.getElementById("calendarioModal");
  const calendarioBackdrop = document.getElementById("calendarioBackdrop");
  const calendarioCerrar = document.getElementById("calendarioCerrar");
  const calendarioGrid = document.getElementById("calendarioGrid");
  const calPrevMes = document.getElementById("calPrevMes");
  const calNextMes = document.getElementById("calNextMes");
  const calTituloMes = document.getElementById("calTituloMes");

  const MESES_ES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"
  ];

  let calAnioActual = new Date().getFullYear();
  let calMesActual = new Date().getMonth(); // 0-11

  let reservaEditandoId = null;

  const generarIdReserva = () =>
    reservas.length ? Math.max(...reservas.map((r) => r.id)) + 1 : 1;

  function shiftReservaFecha(offset) {
    if (!filtroReservaFecha) return;

    // Leer la fecha actual del input
    const actual = filtroReservaFecha.value
      ? new Date(filtroReservaFecha.value)
      : new Date();

    // Moverla X días
    actual.setDate(actual.getDate() + offset);

    // Guardar en input
    const iso = actual.toISOString().slice(0, 10);
    filtroReservaFecha.value = iso;

    // Actualizar tabla
    renderTablaReservas();
  }

  function abrirCalendarioReserva() {
    // Usar la fecha del filtro si hay, si no hoy
    const base = filtroReservaFecha?.value
      ? new Date(filtroReservaFecha.value)
      : new Date();

    calAnioActual = base.getFullYear();
    calMesActual = base.getMonth();

    renderCalendarioMes();
    calendarioModal?.classList.remove("hidden");
  }

  function cerrarCalendarioReserva() {
    calendarioModal?.classList.add("hidden");
  }

  function renderCalendarioMes() {
    if (!calendarioGrid) return;

    calendarioGrid.innerHTML = "";

    // Título "noviembre 2025"
    if (calTituloMes) {
      calTituloMes.textContent =
        MESES_ES[calMesActual] + " " + calAnioActual;
    }

    const primerDia = new Date(calAnioActual, calMesActual, 1);
    const ultimoDia = new Date(calAnioActual, calMesActual + 1, 0);

    // Queremos que la semana empiece en lunes
    let offset = primerDia.getDay(); // 0=Dom,1=Lun
    offset = (offset + 6) % 7; // ahora 0=Lun,6=Dom

    // Celdas vacías al inicio
    for (let i = 0; i < offset; i++) {
      const empty = document.createElement("div");
      empty.className = "calendar-day calendar-day--empty";
      calendarioGrid.appendChild(empty);
    }

    const fechaFiltro = filtroReservaFecha?.value || "";

    for (let dia = 1; dia <= ultimoDia.getDate(); dia++) {
      const fechaISO = `${calAnioActual}-${String(calMesActual + 1).padStart(
        2,
        "0"
      )}-${String(dia).padStart(2, "0")}`;

      const div = document.createElement("div");
      div.className = "calendar-day";
      div.textContent = dia;

      // Cuántas reservas hay ese día
      const count = (reservas || []).filter((r) => r.fecha === fechaISO).length;

      if (count > 0) {
        div.classList.add("calendar-day--has-reservas");

        // Intensidad según cantidad
        if (count <= 2) div.classList.add("calendar-day--level-1");
        else if (count <= 5) div.classList.add("calendar-day--level-2");
        else div.classList.add("calendar-day--level-3");

        const badge = document.createElement("span");
        badge.className = "calendar-day-badge";
        badge.textContent = count;
        div.appendChild(badge);
      }

      // Día seleccionado
      if (fechaFiltro === fechaISO) {
        div.classList.add("calendar-day--selected");
      }

      // Click: seleccionar fecha y cerrar
      div.addEventListener("click", () => {
        if (filtroReservaFecha) filtroReservaFecha.value = fechaISO;
        cerrarCalendarioReserva();
        renderTablaReservas();
      });

      calendarioGrid.appendChild(div);
    }
  }

  function cambiarMesCalendario(delta) {
    calMesActual += delta;
    if (calMesActual < 0) {
      calMesActual = 11;
      calAnioActual--;
    } else if (calMesActual > 11) {
      calMesActual = 0;
      calAnioActual++;
    }
    renderCalendarioMes();
  }

  function mostrarFormReserva(modo) {
    reservaFormSection?.classList.remove("hidden");
    reservaFormTitulo.textContent =
      modo === "editar" ? "Editar reserva" : "Nueva reserva";
  }

  function ocultarFormReserva() {
    reservaFormSection?.classList.add("hidden");
    reservaEditandoId = null;
    reservaForm?.reset();
    resPersonas.value = "2";
  }

  function renderReservasResumen(fechaFiltro) {
    if (!reservasResumenList) return;
    reservasResumenList.innerHTML = "";

    if (!fechaFiltro) {
      const li = document.createElement("li");
      li.className = "stock-alert-item";
      li.innerHTML =
        '<span class="stock-alert-meta">Selecciona una fecha para ver el resumen.</span>';
      reservasResumenList.appendChild(li);
      return;
    }

    const delDia = reservas.filter((r) => r.fecha === fechaFiltro);
    if (!delDia.length) {
      const li = document.createElement("li");
      li.className = "stock-alert-item";
      li.innerHTML =
        '<span class="stock-alert-meta">No hay reservas para esta fecha.</span>';
      reservasResumenList.appendChild(li);
      return;
    }

    delDia.forEach((r) => {
      const li = document.createElement("li");
      li.className = "stock-alert-item";
      li.innerHTML = `
        <span class="stock-alert-name">${r.cliente}</span>
        <span class="stock-alert-meta">${r.hora} · ${r.mesa} · ${r.personas} personas · ${r.estado}</span>
      `;
      reservasResumenList.appendChild(li);
    });
  }

  function renderTablaReservas() {
    if (!reservasTableBody) return;

    const fechaFiltro = filtroReservaFecha?.value || "";
    const estadoFiltro = filtroReservaEstado?.value || "todas";
    const texto = (filtroReservaTexto?.value || "").toLowerCase();

    reservasTableBody.innerHTML = "";

    reservas
      .slice()
      .sort((a, b) => (a.fecha + a.hora).localeCompare(b.fecha + b.hora))
      .forEach((r, idx) => {
        const coincideFecha = !fechaFiltro || r.fecha === fechaFiltro;
        const coincideEstado =
          estadoFiltro === "todas" || r.estado === estadoFiltro;
        const coincideTexto =
          !texto ||
          r.cliente.toLowerCase().includes(texto) ||
          (r.mesa || "").toLowerCase().includes(texto) ||
          (r.telefono || "").toLowerCase().includes(texto);

        if (!coincideFecha || !coincideEstado || !coincideTexto) return;

        const tr = document.createElement("tr");
        tr.innerHTML = `
          <td>${idx + 1}</td>
          <td>${r.cliente}</td>
          <td>${r.personas}</td>
          <td>${r.fecha}</td>
          <td>${r.hora}</td>
          <td>${r.mesa || "-"}</td>
          <td>
            <span class="badge">${r.estado}</span>
          </td>
          <td>
            <div class="actions-cell">
              <button class="action-btn" data-edit-reserva="${r.id}">Editar</button>
              <button class="action-btn" data-del-reserva="${r.id}">🗑</button>
            </div>
          </td>
        `;
        reservasTableBody.appendChild(tr);
      });

    reservasTableBody
      .querySelectorAll("[data-edit-reserva]")
      .forEach((btn) => {
        btn.addEventListener("click", () => {
          const id = Number(btn.getAttribute("data-edit-reserva"));
          abrirEdicionReserva(id);
        });
      });

    reservasTableBody
      .querySelectorAll("[data-del-reserva]")
      .forEach((btn) => {
        btn.addEventListener("click", () => {
          const id = Number(btn.getAttribute("data-del-reserva"));
          eliminarReserva(id);
        });
      });

    renderReservasResumen(fechaFiltro);
  }

  function abrirEdicionReserva(id) {
    const r = reservas.find((x) => x.id === id);
    if (!r) return;

    reservaEditandoId = id;
    mostrarFormReserva("editar");

    resCliente.value = r.cliente;
    resTelefono.value = r.telefono || "";
    resEmail.value = r.email || "";
    resPersonas.value = String(r.personas);
    resFecha.value = r.fecha;
    resHora.value = r.hora;
    resMesa.value = r.mesa || "";
    resEstado.value = r.estado;
    resNota.value = r.nota || "";
  }

  function eliminarReserva(id) {
    if (!confirm("¿Eliminar esta reserva?")) return;
    reservas = reservas.filter((r) => r.id !== id);
    renderTablaReservas();
  }

  reservaForm?.addEventListener("submit", (e) => {
    e.preventDefault();

    const cliente = (resCliente.value || "").trim();
    const telefono = (resTelefono.value || "").trim();
    const email = (resEmail.value || "").trim();
    const personas = Number(resPersonas.value) || 1;
    const fecha = resFecha.value;
    const hora = resHora.value;
    const mesa = (resMesa.value || "").trim();
    const estado = resEstado.value;
    const nota = (resNota.value || "").trim();

    if (!cliente || !fecha || !hora) {
      alert("Cliente, fecha y hora son obligatorios.");
      return;
    }
    if (personas < 1) {
      alert("Las personas no pueden ser menos de 1.");
      return;
    }

    if (reservaEditandoId) {
      const r = reservas.find((x) => x.id === reservaEditandoId);
      if (!r) return;
      r.cliente = cliente;
      r.telefono = telefono;
      r.email = email;
      r.personas = personas;
      r.fecha = fecha;
      r.hora = hora;
      r.mesa = mesa;
      r.estado = estado;
      r.nota = nota;
    } else {
      reservas.push({
        id: generarIdReserva(),
        cliente,
        telefono,
        email,
        personas,
        fecha,
        hora,
        mesa,
        estado,
        nota,
      });
    }

    // Sincronizar datos con Clientes
    upsertClienteDesdeReserva({
      nombre: cliente,
      telefono,
      email,
      nota,
    });

    ocultarFormReserva();
    renderTablaReservas();
  });

  btnNuevaReserva?.addEventListener("click", () => {
    reservaEditandoId = null;
    reservaForm?.reset();
    resPersonas.value = "2";
    mostrarFormReserva("crear");
  });

  reservaCancelar?.addEventListener("click", ocultarFormReserva);

  filtroReservaFecha?.addEventListener("change", renderTablaReservas);
  filtroReservaEstado?.addEventListener("change", renderTablaReservas);
  filtroReservaTexto?.addEventListener("input", renderTablaReservas);
  btnResetFiltrosReserva?.addEventListener("click", () => {
    if (filtroReservaFecha) filtroReservaFecha.value = "";
    if (filtroReservaEstado) filtroReservaEstado.value = "todas";
    if (filtroReservaTexto) filtroReservaTexto.value = "";
    renderTablaReservas();
  });

  btnFechaAyer?.addEventListener("click", () => {
    shiftReservaFecha(-1);
  });

  btnFechaHoy?.addEventListener("click", () => {
    const hoy = new Date().toISOString().slice(0, 10);
    filtroReservaFecha.value = hoy;
    renderTablaReservas();
  });

  btnFechaManana?.addEventListener("click", () => {
    shiftReservaFecha(1);
  });

  btnCalendarioReserva?.addEventListener("click", abrirCalendarioReserva);
  calendarioCerrar?.addEventListener("click", cerrarCalendarioReserva);
  calendarioBackdrop?.addEventListener("click", cerrarCalendarioReserva);

  calPrevMes?.addEventListener("click", () => cambiarMesCalendario(-1));
  calNextMes?.addEventListener("click", () => cambiarMesCalendario(1));

  function initReservas() {
    // por defecto, filtrar por hoy
    if (filtroReservaFecha && !filtroReservaFecha.value) {
      filtroReservaFecha.value = new Date().toISOString().slice(0, 10);
    }
    renderTablaReservas();
  }

  function upsertClienteDesdeReserva({ nombre, telefono, email, nota }) {
    if (!nombre && !telefono && !email) return;
    if (!Array.isArray(clientes)) return; // por si todavía no se definió

    // Buscar primero por teléfono, luego por email
    let encontrado =
      (telefono && clientes.find((c) => c.telefono === telefono)) ||
      (email && clientes.find((c) => c.email === email));

    if (!encontrado) {
      // Crear nuevo cliente
      clientes.push({
        id: generarIdCliente(),
        nombre: nombre || "Sin nombre",
        telefono: telefono || "",
        email: email || "",
        nota: nota || "",
      });
    } else {
      // Actualizar datos faltantes del cliente existente
      if (nombre && !encontrado.nombre) encontrado.nombre = nombre;
      if (telefono && !encontrado.telefono) encontrado.telefono = telefono;
      if (email && !encontrado.email) encontrado.email = email;
      if (nota && !encontrado.nota) encontrado.nota = nota;
    }

    // Si ya está montada la tabla de clientes, refrescar
    if (typeof renderTablaClientes === "function") {
      renderTablaClientes();
    }
  }

  /* ===== USUARIOS ===== */

  // Configuración de roles
  const ROL_CONFIG = {
    admin: {
      tipoLogin: "password",
      permisos: ["admin", "caja", "mesas", "reservas", "inventario", "reportes", "configuracion"],
    },
    cajero: {
      tipoLogin: "pin",
      permisos: ["caja", "reportes-caja"],
    },
    mesero: {
      tipoLogin: "qr",
      permisos: ["mesero", "cocina"], // Mesero ve su panel y cocina
    },
    cocinero: {
      tipoLogin: "qr",
      permisos: ["cocina", "mesero"], // Cocina ve su panel y el de mesero
    },
  };

  let usuarios = [
    {
      id: 1,
      nombre: "Admin General",
      usuario: "admin",
      rol: "admin",
      tipoLogin: "password",
      pin: "",
      qrToken: "",
      permisos: ["admin", "caja", "mesas", "reservas", "inventario", "reportes", "configuracion"],
      activo: true,
      nota: "Cuenta principal",
    },
    {
      id: 2,
      nombre: "Cajero Demo",
      usuario: "",
      rol: "cajero",
      tipoLogin: "pin",
      pin: "1000",
      qrToken: "",
      permisos: ["caja", "reportes-caja"],
      activo: true,
      nota: "",
    },
    {
      id: 3,
      nombre: "Mesero Demo",
      usuario: "",
      rol: "mesero",
      tipoLogin: "qr",
      pin: "",
      qrToken: "MESERO_DEMO_ABC123",
      permisos: ["mesero", "cocina"],
      activo: true,
      nota: "",
    },
  ];

  const usuariosTableBody = document.getElementById("usuariosTableBody");
  const filtroUsuarioTexto = document.getElementById("filtroUsuarioTexto");
  const filtroUsuarioRol = document.getElementById("filtroUsuarioRol");
  const btnResetFiltrosUsuario = document.getElementById("btnResetFiltrosUsuario");

  const usuarioFormSection = document.getElementById("usuarioFormSection");
  const usuarioFormTitulo = document.getElementById("usuarioFormTitulo");
  const usuarioForm = document.getElementById("usuarioForm");
  const usrNombre = document.getElementById("usrNombre");
  const usrUsuario = document.getElementById("usrUsuario");
  const usrRol = document.getElementById("usrRol");
  const usrActivo = document.getElementById("usrActivo");
  const usrNota = document.getElementById("usrNota");
  const usuarioCancelar = document.getElementById("usuarioCancelar");
  const btnNuevoUsuario = document.getElementById("btnNuevoUsuario");

  // Nuevos campos de acceso
  const bloqueLoginPassword = document.getElementById("bloqueLoginPassword");
  const bloqueLoginPin = document.getElementById("bloqueLoginPin");
  const bloqueLoginQr = document.getElementById("bloqueLoginQr");
  const usrPin = document.getElementById("usrPin");
  const usrQrToken = document.getElementById("usrQrToken");
  const usrAreas = document.getElementById("usrAreas");
  const btnGenerarPin = document.getElementById("btnGenerarPin");
  const btnGenerarQr = document.getElementById("btnGenerarQr");

  let usuarioEditandoId = null;

  const generarIdUsuario = () =>
    usuarios.length ? Math.max(...usuarios.map((u) => u.id)) + 1 : 1;

  // Generar PIN de 4 dígitos
  function generarPinCorto() {
    return String(Math.floor(Math.random() * 9000) + 1000);
  }

  // Generar token QR único
  function generarQrToken() {
    const random = Math.random().toString(36).substring(2, 10);
    const timestamp = Date.now().toString(36);
    return `QR_${random}_${timestamp}`;
  }

  function mostrarFormUsuario(modo) {
    usuarioFormSection?.classList.remove("hidden");
    usuarioFormTitulo.textContent =
      modo === "editar" ? "Editar usuario" : "Nuevo usuario";
  }

  function ocultarFormUsuario() {
    usuarioFormSection?.classList.add("hidden");
    usuarioEditandoId = null;
    usuarioForm?.reset();
  }

  function actualizarAreasPorRol() {
    if (!usrRol || !usrAreas) return;

    const rol = usrRol.value;
    let areas = "";

    if (rol === "administrador" || rol === "admin") {
      areas = "admin, caja, mesas, reservas, inventario, reportes, configuracion";
    } else if (rol === "cajero") {
      areas = "caja, reportes-caja";
    } else if (rol === "mesero") {
      // Mesero ve su panel y cocina
      areas = "mesero, cocina";
    } else if (rol === "cocinero") {
      // Cocina ve su panel y el de mesero
      areas = "cocina, mesero";
    } else {
      areas = "";
    }

    usrAreas.value = areas;
  }

  function renderTablaUsuarios() {
    if (!usuariosTableBody) return;

    const texto = (filtroUsuarioTexto?.value || "").toLowerCase();
    const rol = filtroUsuarioRol?.value || "todos";

    usuariosTableBody.innerHTML = "";

    usuarios
      .slice()
      .sort((a, b) => a.id - b.id)
      .forEach((u, idx) => {
        const coincideTexto =
          !texto ||
          u.nombre.toLowerCase().includes(texto) ||
          u.usuario.toLowerCase().includes(texto);
        const coincideRol = rol === "todos" || u.rol === rol;
        if (!coincideTexto || !coincideRol) return;

        // Determinar tipo de acceso
        let tipoAcceso = "Sin acceso";
        if (u.tipoLogin === "password") tipoAcceso = "Password";
        else if (u.tipoLogin === "pin") tipoAcceso = "PIN";
        else if (u.tipoLogin === "qr") tipoAcceso = "QR";

        // Determinar áreas
        const areas = (u.permisos || []).join(", ") || "-";

        const tr = document.createElement("tr");
        tr.innerHTML = `
          <td>${idx + 1}</td>
          <td>${u.nombre}</td>
          <td>${u.usuario || "-"}</td>
          <td>${u.rol}</td>
          <td>${tipoAcceso}</td>
          <td>${areas}</td>
          <td>${u.activo ? "Activo" : "Inactivo"}</td>
          <td>
            <div class="actions-cell">
              <button class="action-btn" data-edit-usuario="${u.id}">Editar</button>
              <button class="action-btn" data-del-usuario="${u.id}">🗑</button>
            </div>
          </td>
        `;
        // TODO: cuando exista login real, ocultar botón Eliminar si usuarioActual.rol === "cajero"
        usuariosTableBody.appendChild(tr);
      });

    usuariosTableBody
      .querySelectorAll("[data-edit-usuario]")
      .forEach((btn) => {
        btn.addEventListener("click", () => {
          const id = Number(btn.getAttribute("data-edit-usuario"));
          abrirEdicionUsuario(id);
        });
      });

    usuariosTableBody
      .querySelectorAll("[data-del-usuario]")
      .forEach((btn) => {
        btn.addEventListener("click", () => {
          const id = Number(btn.getAttribute("data-del-usuario"));
          eliminarUsuario(id);
        });
      });
  }

  function abrirEdicionUsuario(id) {
    const u = usuarios.find((x) => x.id === id);
    if (!u) return;
    usuarioEditandoId = id;
    mostrarFormUsuario("editar");

    usrNombre.value = u.nombre;
    usrUsuario.value = u.usuario || "";
    usrRol.value = u.rol;
    usrActivo.value = u.activo ? "true" : "false";
    usrNota.value = u.nota || "";

    // Cargar campos de acceso
    if (usrPin) usrPin.value = u.pin || "";
    if (usrQrToken) usrQrToken.value = u.qrToken || "";
    if (usrAreas) usrAreas.value = (u.permisos || []).join(", ");

    // Trigger cambio de rol para mostrar bloques correctos
    usrRol?.dispatchEvent(new Event("change"));
  }

  function eliminarUsuario(id) {
    if (!confirm("¿Eliminar este usuario?")) return;
    usuarios = usuarios.filter((u) => u.id !== id);
    renderTablaUsuarios();
  }

  usuarioForm?.addEventListener("submit", (e) => {
    e.preventDefault();

    const nombre = (usrNombre.value || "").trim();
    const usuario = (usrUsuario.value || "").trim();
    const rol = usrRol.value;
    const activo = usrActivo.value === "true";
    const nota = (usrNota.value || "").trim();

    // Obtener configuración del rol
    const config = ROL_CONFIG[rol];
    if (!config) {
      alert("Rol no válido.");
      return;
    }

    const tipoLogin = config.tipoLogin;
    const pin = (usrPin.value || "").trim();
    const qrToken = (usrQrToken.value || "").trim();
    const permisos = (usrAreas.value || "")
      .split(",")
      .map((x) => x.trim())
      .filter(Boolean);

    // Validación básica
    if (!nombre) {
      alert("El nombre es obligatorio.");
      return;
    }

    // Validar según tipo de login
    if (tipoLogin === "password" && !usuario) {
      alert("El usuario es obligatorio para administradores.");
      return;
    }

    if (tipoLogin === "password") {
      const duplicado = usuarios.some(
        (u) =>
          u.usuario.toLowerCase() === usuario.toLowerCase() &&
          (!usuarioEditandoId || u.id !== usuarioEditandoId)
      );
      if (duplicado) {
        alert("Ya existe un usuario con ese nombre de usuario.");
        return;
      }
    }

    if (usuarioEditandoId) {
      const u = usuarios.find((x) => x.id === usuarioEditandoId);
      if (!u) return;
      u.nombre = nombre;
      u.usuario = tipoLogin === "password" ? usuario : "";
      u.rol = rol;
      u.tipoLogin = tipoLogin;
      u.pin = tipoLogin === "pin" ? pin : "";
      u.qrToken = tipoLogin === "qr" ? qrToken : "";
      u.permisos = permisos;
      u.activo = activo;
      u.nota = nota;
    } else {
      usuarios.push({
        id: generarIdUsuario(),
        nombre,
        usuario: tipoLogin === "password" ? usuario : "",
        rol,
        tipoLogin,
        pin: tipoLogin === "pin" ? pin : "",
        qrToken: tipoLogin === "qr" ? qrToken : "",
        permisos,
        activo,
        nota,
      });
    }

    ocultarFormUsuario();
    renderTablaUsuarios();
  });

  // Listener para cambio de rol - mostrar/ocultar bloques de acceso
  usrRol?.addEventListener("change", () => {
    const rol = usrRol.value;
    const config = ROL_CONFIG[rol];

    if (!config) return;

    // Ocultar todos los bloques primero
    bloqueLoginPassword?.classList.add("hidden");
    bloqueLoginPin?.classList.add("hidden");
    bloqueLoginQr?.classList.add("hidden");

    // Mostrar el bloque correspondiente según tipoLogin
    if (config.tipoLogin === "password") {
      bloqueLoginPassword?.classList.remove("hidden");
    } else if (config.tipoLogin === "pin") {
      bloqueLoginPin?.classList.remove("hidden");
    } else if (config.tipoLogin === "qr") {
      bloqueLoginQr?.classList.remove("hidden");
    }

    // Llenar áreas permitidas usando la función
    actualizarAreasPorRol();
  });

  // Generar PIN
  btnGenerarPin?.addEventListener("click", () => {
    if (usrPin) usrPin.value = generarPinCorto();
  });

  // Generar QR Token
  btnGenerarQr?.addEventListener("click", () => {
    if (usrQrToken) usrQrToken.value = generarQrToken();
  });

  btnNuevoUsuario?.addEventListener("click", () => {
    usuarioEditandoId = null;
    usuarioForm?.reset();
    mostrarFormUsuario("crear");
    // Trigger cambio de rol para mostrar bloques correctos
    usrRol?.dispatchEvent(new Event("change"));
  });

  usuarioCancelar?.addEventListener("click", ocultarFormUsuario);

  filtroUsuarioTexto?.addEventListener("input", renderTablaUsuarios);
  filtroUsuarioRol?.addEventListener("change", renderTablaUsuarios);
  btnResetFiltrosUsuario?.addEventListener("click", () => {
    if (filtroUsuarioTexto) filtroUsuarioTexto.value = "";
    if (filtroUsuarioRol) filtroUsuarioRol.value = "todos";
    renderTablaUsuarios();
  });

  function initUsuarios() {
    renderTablaUsuarios();
  }

  /* ===== CLIENTES ===== */

  let clientes = [
    {
      id: 1,
      nombre: "Cliente demo",
      telefono: "70000000",
      email: "",
      nota: "Ejemplo",
    },
  ];

  const clientesTableBody = document.getElementById("clientesTableBody");
  const filtroClienteTexto = document.getElementById("filtroClienteTexto");
  const btnResetFiltrosCliente = document.getElementById("btnResetFiltrosCliente");

  const clienteFormSection = document.getElementById("clienteFormSection");
  const clienteFormTitulo = document.getElementById("clienteFormTitulo");
  const clienteForm = document.getElementById("clienteForm");
  const cliNombre = document.getElementById("cliNombre");
  const cliTelefono = document.getElementById("cliTelefono");
  const cliEmail = document.getElementById("cliEmail");
  const cliNota = document.getElementById("cliNota");
  const clienteCancelar = document.getElementById("clienteCancelar");
  const btnNuevoCliente = document.getElementById("btnNuevoCliente");

  let clienteEditandoId = null;

  const generarIdCliente = () =>
    clientes.length ? Math.max(...clientes.map((c) => c.id)) + 1 : 1;

  function mostrarFormCliente(modo) {
    clienteFormSection?.classList.remove("hidden");
    clienteFormTitulo.textContent =
      modo === "editar" ? "Editar cliente" : "Nuevo cliente";
  }

  function ocultarFormCliente() {
    clienteFormSection?.classList.add("hidden");
    clienteEditandoId = null;
    clienteForm?.reset();
  }

  function renderTablaClientes() {
    if (!clientesTableBody) return;

    const texto = (filtroClienteTexto?.value || "").toLowerCase();
    clientesTableBody.innerHTML = "";

    clientes
      .slice()
      .sort((a, b) => a.id - b.id)
      .forEach((c, idx) => {
        const coincideTexto =
          !texto ||
          c.nombre.toLowerCase().includes(texto) ||
          (c.telefono || "").toLowerCase().includes(texto) ||
          (c.email || "").toLowerCase().includes(texto);
        if (!coincideTexto) return;

        const tr = document.createElement("tr");
        tr.innerHTML = `
          <td>${idx + 1}</td>
          <td>${c.nombre}</td>
          <td>${c.telefono || "-"}</td>
          <td>${c.email || "-"}</td>
          <td>${c.nota || "-"}</td>
          <td>
            <div class="actions-cell">
              <button class="action-btn" data-edit-cliente="${c.id}">Editar</button>
              <button class="action-btn" data-del-cliente="${c.id}">🗑</button>
            </div>
          </td>
        `;
        clientesTableBody.appendChild(tr);
      });

    clientesTableBody
      .querySelectorAll("[data-edit-cliente]")
      .forEach((btn) => {
        btn.addEventListener("click", () => {
          const id = Number(btn.getAttribute("data-edit-cliente"));
          abrirEdicionCliente(id);
        });
      });

    clientesTableBody
      .querySelectorAll("[data-del-cliente]")
      .forEach((btn) => {
        btn.addEventListener("click", () => {
          const id = Number(btn.getAttribute("data-del-cliente"));
          eliminarCliente(id);
        });
      });
  }

  function abrirEdicionCliente(id) {
    const c = clientes.find((x) => x.id === id);
    if (!c) return;
    clienteEditandoId = id;
    mostrarFormCliente("editar");

    cliNombre.value = c.nombre;
    cliTelefono.value = c.telefono || "";
    cliEmail.value = c.email || "";
    cliNota.value = c.nota || "";
  }

  function eliminarCliente(id) {
    if (!confirm("¿Eliminar este cliente?")) return;
    clientes = clientes.filter((c) => c.id !== id);
    renderTablaClientes();
  }

  clienteForm?.addEventListener("submit", (e) => {
    e.preventDefault();

    const nombre = (cliNombre.value || "").trim();
    const telefono = (cliTelefono.value || "").trim();
    const email = (cliEmail.value || "").trim();
    const nota = (cliNota.value || "").trim();

    if (!nombre) {
      alert("El nombre es obligatorio.");
      return;
    }

    if (clienteEditandoId) {
      const c = clientes.find((x) => x.id === clienteEditandoId);
      if (!c) return;
      c.nombre = nombre;
      c.telefono = telefono;
      c.email = email;
      c.nota = nota;
    } else {
      clientes.push({
        id: generarIdCliente(),
        nombre,
        telefono,
        email,
        nota,
      });
    }

    ocultarFormCliente();
    renderTablaClientes();
  });

  btnNuevoCliente?.addEventListener("click", () => {
    clienteEditandoId = null;
    clienteForm?.reset();
    mostrarFormCliente("crear");
  });

  clienteCancelar?.addEventListener("click", ocultarFormCliente);

  filtroClienteTexto?.addEventListener("input", renderTablaClientes);
  btnResetFiltrosCliente?.addEventListener("click", () => {
    if (filtroClienteTexto) filtroClienteTexto.value = "";
    renderTablaClientes();
  });

  function initClientes() {
    renderTablaClientes();
  }

  /* ===== REPORTES ===== */

  // Elementos de la UI
  const repFechasLista = document.getElementById("repFechasLista");
  const repBuscarFecha = document.getElementById("repBuscarFecha");

  const repDetalleCard = document.getElementById("repDetalleCard");
  const repDetalleFechaLabel = document.getElementById("repDetalleFechaLabel");

  const repGraficoHoraCanvas = document.getElementById(
    "repGraficoHoraCanvas"
  );

  const repCajaInicio = document.getElementById("repCajaInicio");
  const repCajaCierre = document.getElementById("repCajaCierre");
  const repCajaDiferencia = document.getElementById("repCajaDiferencia");
  const repVentasDia = document.getElementById("repVentasDia");
  const repTicketsDia = document.getElementById("repTicketsDia");

  const repTopProductosLista = document.getElementById("repTopProductosLista");
  const repProductosDetalleLista = document.getElementById(
    "repProductosDetalleLista"
  );

  const repModoDiaBtn = document.getElementById("repModoDia");
  const repModoMesBtn = document.getElementById("repModoMes");
  const repModoAnioBtn = document.getElementById("repModoAnio");

  // Estado de filtro
  let repModoActual = "dia"; // "dia" | "mes" | "anio"
  let repPeriodoActual = null; // "YYYY-MM-DD" | "YYYY-MM" | "YYYY"

  // DEMO: ventas por fecha/hora y producto
  const ventasDemoPorDia = [
    {
      fecha: "2025-11-16",
      hora: "10:00",
      producto: "Pique Macho",
      cantidad: 3,
      total: 105,
    },
    {
      fecha: "2025-11-16",
      hora: "12:00",
      producto: "Hamburguesa",
      cantidad: 2,
      total: 60,
    },
    {
      fecha: "2025-11-16",
      hora: "14:00",
      producto: "Limonada",
      cantidad: 4,
      total: 40,
    },
    {
      fecha: "2025-11-15",
      hora: "11:00",
      producto: "Pique Macho",
      cantidad: 1,
      total: 35,
    },
    {
      fecha: "2025-11-15",
      hora: "13:00",
      producto: "Pollo a la brasa",
      cantidad: 2,
      total: 70,
    },
  ];

  // DEMO: caja por día (apertura/cierre)
  const cajaDemoPorDia = {
    "2025-11-16": { apertura: 20, cierre: 2000 },
    "2025-11-15": { apertura: 50, cierre: 500 },
  };

  const MESES_LARGO = [
    "enero",
    "febrero",
    "marzo",
    "abril",
    "mayo",
    "junio",
    "julio",
    "agosto",
    "septiembre",
    "octubre",
    "noviembre",
    "diciembre",
  ];

  function formatearFechaLarga(iso) {
    if (!iso) return "";
    const [y, m, d] = iso.split("-");
    const mesNombre = MESES_LARGO[Number(m) - 1] || "";
    return `${Number(d)} de ${mesNombre} de ${y}`;
  }

  function formatearMesLargo(key) {
    // key: "YYYY-MM"
    const [y, m] = key.split("-");
    const mesNombre = MESES_LARGO[Number(m) - 1] || "";
    return `${mesNombre} de ${y}`;
  }

  function agruparPorDia() {
    const map = new Map();
    ventasDemoPorDia.forEach((v) => {
      const existente = map.get(v.fecha) || {
        id: v.fecha,
        label: formatearFechaLarga(v.fecha),
        total: 0,
        tickets: 0,
      };
      existente.total += v.total;
      existente.tickets += 1;
      map.set(v.fecha, existente);
    });
    return Array.from(map.values()).sort((a, b) => a.id.localeCompare(b.id));
  }

  function agruparPorMes() {
    const map = new Map();
    ventasDemoPorDia.forEach((v) => {
      const key = v.fecha.slice(0, 7); // YYYY-MM
      const existente = map.get(key) || {
        id: key,
        label: formatearMesLargo(key),
        total: 0,
        tickets: 0,
      };
      existente.total += v.total;
      existente.tickets += 1;
      map.set(key, existente);
    });
    return Array.from(map.values()).sort((a, b) => a.id.localeCompare(b.id));
  }

  function agruparPorAnio() {
    const map = new Map();
    ventasDemoPorDia.forEach((v) => {
      const key = v.fecha.slice(0, 4); // YYYY
      const existente = map.get(key) || {
        id: key,
        label: key,
        total: 0,
        tickets: 0,
      };
      existente.total += v.total;
      existente.tickets += 1;
      map.set(key, existente);
    });
    return Array.from(map.values()).sort((a, b) => a.id.localeCompare(b.id));
  }

  function obtenerResumenSegunModo() {
    if (repModoActual === "mes") return agruparPorMes();
    if (repModoActual === "anio") return agruparPorAnio();
    return agruparPorDia();
  }

  function actualizarBotonesModo() {
    const map = {
      dia: repModoDiaBtn,
      mes: repModoMesBtn,
      anio: repModoAnioBtn,
    };
    Object.entries(map).forEach(([modo, btn]) => {
      if (!btn) return;
      btn.classList.toggle("rep-modo-btn--active", modo === repModoActual);
    });
  }

  function setRepModo(nuevoModo) {
    repModoActual = nuevoModo;
    repPeriodoActual = null;
    actualizarBotonesModo();
    renderReportes();
  }

  function renderListaFechas() {
    if (!repFechasLista) return;

    const filtro =
      repBuscarFecha?.value?.toLowerCase().trim() || "";

    const resumen = obtenerResumenSegunModo().filter((d) => {
      const texto = `${d.id} ${d.label}`.toLowerCase();
      return texto.includes(filtro);
    });

    if (!resumen.length) {
      repFechasLista.innerHTML = `
        <li class="activity-item">
          <div class="activity-main">
            <span class="activity-title">Sin datos registrados (demo)</span>
          </div>
        </li>`;
      return;
    }

    repFechasLista.innerHTML = resumen
      .map(
        (d) => `
        <li class="activity-item" data-periodo="${d.id}">
          <div class="activity-main">
            <span class="activity-title">${d.label}</span>
            <span class="activity-meta">
              ${d.tickets} tickets · Bs ${d.total.toFixed(2)}
            </span>
          </div>
        </li>`
      )
      .join("");

    repFechasLista.querySelectorAll("[data-periodo]").forEach((li) => {
      li.addEventListener("click", () => {
        const id = li.getAttribute("data-periodo");
        repPeriodoActual = id;
        renderDetalleSeleccion();
      });
    });
  }

  function renderGraficoPeriodo(modo, ventasPeriodo) {
    if (!repGraficoHoraCanvas) return;

    const { width, height } = getCanvasSize(repGraficoHoraCanvas);
    const ctx = repGraficoHoraCanvas.getContext("2d");
    clearCanvas(ctx, width, height);

    if (!ventasPeriodo.length) {
      ctx.fillStyle = "#0b1017";
      ctx.fillRect(0, 0, width, height);
      ctx.fillStyle = "#9ca3af";
      ctx.font = "14px system-ui";
      ctx.fillText("Sin datos para este periodo.", 24, height / 2);
      return;
    }

    let puntos = [];

    if (modo === "dia") {
      // agrupar por hora
      const map = new Map();
      ventasPeriodo.forEach((v) => {
        const key = v.hora || "00:00";
        const existente = map.get(key) || { etiqueta: key, total: 0 };
        existente.total += v.total;
        map.set(key, existente);
      });
      puntos = Array.from(map.values()).sort((a, b) =>
        a.etiqueta.localeCompare(b.etiqueta)
      );
    } else if (modo === "mes") {
      // agrupar por día del mes
      const map = new Map();
      ventasPeriodo.forEach((v) => {
        const dia = v.fecha.split("-")[2];
        const key = Number(dia).toString();
        const existente = map.get(key) || { etiqueta: key, total: 0 };
        existente.total += v.total;
        map.set(key, existente);
      });
      puntos = Array.from(map.values()).sort(
        (a, b) => Number(a.etiqueta) - Number(b.etiqueta)
      );
    } else if (modo === "anio") {
      // agrupar por mes
      const map = new Map();
      ventasPeriodo.forEach((v) => {
        const [_, m] = v.fecha.split("-");
        const idx = Number(m) - 1;
        const key = MESES_LARGO[idx].slice(0, 3); // ene, feb, ...
        const existente = map.get(key) || { etiqueta: key, total: 0 };
        existente.total += v.total;
        map.set(key, existente);
      });
      puntos = Array.from(map.values());
    }

    const paddingX = 48;
    const paddingY = 32;
    const chartWidth = width - paddingX * 2;
    const chartHeight = height - paddingY * 2;

    const maxValor = Math.max(...puntos.map((p) => p.total));
    const barWidth = chartWidth / puntos.length - 12;

    ctx.fillStyle = "#0b1017";
    ctx.fillRect(0, 0, width, height);

    ctx.strokeStyle = "#1f2937";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(paddingX, paddingY);
    ctx.lineTo(paddingX, paddingY + chartHeight);
    ctx.lineTo(paddingX + chartWidth, paddingY + chartHeight);
    ctx.stroke();

    puntos.forEach((p, index) => {
      const x = paddingX + index * (barWidth + 12) + 6;
      const h = (p.total / maxValor || 0) * chartHeight;
      const y = paddingY + chartHeight - h;

      ctx.fillStyle = "#84B067"; // Color verde permanente
      ctx.fillRect(x, y, barWidth, h);

      ctx.fillStyle = "#9ca3af";
      ctx.font = "11px system-ui";
      ctx.save();
      ctx.translate(x + barWidth / 2, paddingY + chartHeight + 14);
      ctx.rotate(-Math.PI / 6);
      ctx.fillText(p.etiqueta, 0, 0);
      ctx.restore();
    });
  }

  function renderDetalleSeleccion() {
    if (!repDetalleCard) return;

    if (!repPeriodoActual) {
      if (repDetalleFechaLabel)
        repDetalleFechaLabel.textContent = "Selecciona un día, mes o año.";
      renderGraficoPeriodo("dia", []);
      if (repCajaInicio) repCajaInicio.textContent = "—";
      if (repCajaCierre) repCajaCierre.textContent = "—";
      if (repCajaDiferencia) repCajaDiferencia.textContent = "—";
      if (repVentasDia) repVentasDia.textContent = "—";
      if (repTicketsDia) repTicketsDia.textContent = "—";
      if (repTopProductosLista) repTopProductosLista.innerHTML = "";
      if (repProductosDetalleLista) repProductosDetalleLista.innerHTML = "";
      return;
    }

    let etiquetaPeriodo = "";
    let filtroFn = null;
    let modoGrafico = "dia";

    if (repModoActual === "dia") {
      etiquetaPeriodo = formatearFechaLarga(repPeriodoActual);
      filtroFn = (v) => v.fecha === repPeriodoActual;
      modoGrafico = "dia";
    } else if (repModoActual === "mes") {
      etiquetaPeriodo = formatearMesLargo(repPeriodoActual);
      filtroFn = (v) => v.fecha.slice(0, 7) === repPeriodoActual;
      modoGrafico = "mes";
    } else {
      etiquetaPeriodo = repPeriodoActual;
      filtroFn = (v) => v.fecha.slice(0, 4) === repPeriodoActual;
      modoGrafico = "anio";
    }

    if (repDetalleFechaLabel)
      repDetalleFechaLabel.textContent = etiquetaPeriodo;

    const ventasPeriodo = ventasDemoPorDia.filter(filtroFn);
    const totalPeriodo = ventasPeriodo.reduce(
      (acc, v) => acc + v.total,
      0
    );
    const ticketsPeriodo = ventasPeriodo.length;

    if (repVentasDia)
      repVentasDia.textContent = `Bs ${totalPeriodo.toFixed(2)}`;
    if (repTicketsDia)
      repTicketsDia.textContent = String(ticketsPeriodo);

    // Caja solo por día (para mes/año mostramos —)
    if (repModoActual === "dia") {
      const infoCaja = cajaDemoPorDia[repPeriodoActual];
      if (infoCaja) {
        const dif = infoCaja.cierre - infoCaja.apertura;
        if (repCajaInicio)
          repCajaInicio.textContent = `Bs ${infoCaja.apertura.toFixed(2)}`;
        if (repCajaCierre)
          repCajaCierre.textContent = `Bs ${infoCaja.cierre.toFixed(2)}`;
        if (repCajaDiferencia)
          repCajaDiferencia.textContent = `Bs ${dif.toFixed(2)}`;
      } else {
        if (repCajaInicio) repCajaInicio.textContent = "—";
        if (repCajaCierre) repCajaCierre.textContent = "—";
        if (repCajaDiferencia) repCajaDiferencia.textContent = "—";
      }
    } else {
      if (repCajaInicio) repCajaInicio.textContent = "—";
      if (repCajaCierre) repCajaCierre.textContent = "—";
      if (repCajaDiferencia) repCajaDiferencia.textContent = "—";
    }

    // Agrupar productos del periodo
    const mapProductos = new Map();
    ventasPeriodo.forEach((v) => {
      const existente =
        mapProductos.get(v.producto) || {
          nombre: v.producto,
          cantidad: 0,
          total: 0,
        };
      existente.cantidad += v.cantidad;
      existente.total += v.total;
      mapProductos.set(v.producto, existente);
    });

    const productosAgrupados = Array.from(mapProductos.values()).sort(
      (a, b) => b.total - a.total
    );

    // Top 10
    if (repTopProductosLista) {
      const top10 = productosAgrupados.slice(0, 10);
      repTopProductosLista.innerHTML = top10
        .map(
          (p) => `
          <li class="activity-item">
            <div class="activity-main">
              <span class="activity-title">${p.nombre}</span>
              <span class="activity-meta">
                ${p.cantidad} uds · Bs ${p.total.toFixed(2)}
              </span>
            </div>
          </li>`
        )
        .join("");
    }

    // Lista completa
    if (repProductosDetalleLista) {
      repProductosDetalleLista.innerHTML = productosAgrupados
        .map(
          (p) => `
          <li class="activity-item">
            <div class="activity-main">
              <span class="activity-title">${p.nombre}</span>
              <span class="activity-meta">
                ${p.cantidad} uds · Bs ${p.total.toFixed(2)}
              </span>
            </div>
          </li>`
        )
        .join("");
    }

    renderGraficoPeriodo(modoGrafico, ventasPeriodo);
  }

  function renderReportes() {
    renderListaFechas();
    renderDetalleSeleccion();
  }

  repBuscarFecha?.addEventListener("input", () => {
    renderReportes();
  });

  repModoDiaBtn?.addEventListener("click", () => setRepModo("dia"));
  repModoMesBtn?.addEventListener("click", () => setRepModo("mes"));
  repModoAnioBtn?.addEventListener("click", () => setRepModo("anio"));

  function initReportes() {
    const resumen = obtenerResumenSegunModo();
    if (!repPeriodoActual && resumen.length) {
      repPeriodoActual = resumen[resumen.length - 1].id; // último periodo
    }
    actualizarBotonesModo();
    renderReportes();
  }

  /* ===== CONFIGURACIÓN ===== */

  const configForm = document.getElementById("configForm");

  const cfgNombre = document.getElementById("cfgNombre");
  const cfgLema = document.getElementById("cfgLema");
  const cfgLogo = document.getElementById("cfgLogo");

  const cfgMoneda = document.getElementById("cfgMoneda");
  const cfgZonaHoraria = document.getElementById("cfgZonaHoraria");
  const cfgIdioma = document.getElementById("cfgIdioma");

  const cfgImpuesto = document.getElementById("cfgImpuesto");
  const cfgPropina = document.getElementById("cfgPropina");
  const cfgNit = document.getElementById("cfgNit");

  const cfgHoraApertura = document.getElementById("cfgHoraApertura");
  const cfgHoraCierre = document.getElementById("cfgHoraCierre");
  const cfgReservaMaxMinutos = document.getElementById(
    "cfgReservaMaxMinutos"
  );
  const cfgReservaToleranciaMinutos = document.getElementById(
    "cfgReservaToleranciaMinutos"
  );

  const cfgTicketFooter = document.getElementById("cfgTicketFooter");
  const cfgTema = document.getElementById("cfgTema");

  const cfgDias = document.querySelectorAll('input[name="cfgDias"]');

  // Para actualizar la cabecera (esquina superior derecha)
  const topbarEnv = document.querySelector(".topbar-env");

  const configState = {
    nombre: "Karady Admin · Restaurante",
    lema: "",
    moneda: "BOB",
    zonaHoraria: "America/La_Paz",
    idioma: "es-BO",

    diasApertura: ["lun", "mar", "mie", "jue", "vie", "sab", "dom"],
    horaApertura: "09:00",
    horaCierre: "23:00",
    reservaMaxMinutos: 120,
    reservaToleranciaMinutos: 15,

    impuesto: 13,
    propina: 0,
    nit: "",
    ticketFooter: "Gracias por su visita.",

    tema: "dark-green",
  };

  function aplicarConfigEnUI() {
    if (topbarEnv && configState.nombre) {
      topbarEnv.textContent = configState.nombre;
    }
    document.title = configState.nombre || "Karady Admin";

    // APLICAR TEMA
    const themeClasses = [
      "theme-dark-green",
      "theme-dark-orange",
      "theme-dark-blue",
      "theme-dark-purple",
      "theme-dark-cyan",
    ];

    document.body.classList.remove(...themeClasses);

    if (configState.tema) {
      document.body.classList.add("theme-" + configState.tema);
    }
  }

  function cargarConfigEnForm() {
    if (!configForm) return;

    if (cfgNombre) cfgNombre.value = configState.nombre;
    if (cfgLema) cfgLema.value = configState.lema || "";

    if (cfgMoneda) cfgMoneda.value = configState.moneda;
    if (cfgZonaHoraria) cfgZonaHoraria.value = configState.zonaHoraria;
    if (cfgIdioma) cfgIdioma.value = configState.idioma;

    if (cfgImpuesto) cfgImpuesto.value = configState.impuesto;
    if (cfgPropina) cfgPropina.value = configState.propina;
    if (cfgNit) cfgNit.value = configState.nit;

    if (cfgHoraApertura) cfgHoraApertura.value = configState.horaApertura;
    if (cfgHoraCierre) cfgHoraCierre.value = configState.horaCierre;
    if (cfgReservaMaxMinutos)
      cfgReservaMaxMinutos.value = configState.reservaMaxMinutos;
    if (cfgReservaToleranciaMinutos)
      cfgReservaToleranciaMinutos.value =
        configState.reservaToleranciaMinutos;

    if (cfgTicketFooter) cfgTicketFooter.value = configState.ticketFooter;
    if (cfgTema) cfgTema.value = configState.tema;

    if (cfgDias && configState.diasApertura) {
      cfgDias.forEach((chk) => {
        chk.checked = configState.diasApertura.includes(chk.value);
      });
    }
  }

  configForm?.addEventListener("submit", (e) => {
    e.preventDefault();
    if (!configForm) return;

    configState.nombre = cfgNombre.value || configState.nombre;
    configState.lema = cfgLema.value || "";

    configState.moneda = cfgMoneda.value || configState.moneda;
    configState.zonaHoraria =
      cfgZonaHoraria.value || configState.zonaHoraria;
    configState.idioma =
      (cfgIdioma && cfgIdioma.value) || configState.idioma;

    configState.impuesto =
      cfgImpuesto && cfgImpuesto.value !== ""
        ? Number(cfgImpuesto.value)
        : configState.impuesto;

    configState.propina =
      cfgPropina && cfgPropina.value !== ""
        ? Number(cfgPropina.value)
        : configState.propina;

    configState.nit =
      (cfgNit && cfgNit.value) || configState.nit;

    configState.horaApertura =
      cfgHoraApertura && cfgHoraApertura.value
        ? cfgHoraApertura.value
        : configState.horaApertura;

    configState.horaCierre =
      cfgHoraCierre && cfgHoraCierre.value
        ? cfgHoraCierre.value
        : configState.horaCierre;

    configState.reservaMaxMinutos =
      cfgReservaMaxMinutos && cfgReservaMaxMinutos.value !== ""
        ? Number(cfgReservaMaxMinutos.value)
        : configState.reservaMaxMinutos;

    configState.reservaToleranciaMinutos =
      cfgReservaToleranciaMinutos &&
      cfgReservaToleranciaMinutos.value !== ""
        ? Number(cfgReservaToleranciaMinutos.value)
        : configState.reservaToleranciaMinutos;

    configState.ticketFooter =
      cfgTicketFooter.value || configState.ticketFooter;

    configState.tema =
      (cfgTema && cfgTema.value) || configState.tema;

    if (cfgDias && cfgDias.length) {
      configState.diasApertura = Array.from(cfgDias)
        .filter((chk) => chk.checked)
        .map((chk) => chk.value);
    }

    aplicarConfigEnUI();
    alert("Configuración guardada (demo, solo en memoria).");
  });

  function initConfiguracion() {
    cargarConfigEnForm();
    aplicarConfigEnUI();
  }

  /* ===== PRODUCTOS ===== */
  let categorias = [
    { id: "entradas", nombre: "Entradas", activa: true },
    { id: "platos", nombre: "Platos Principales", activa: true },
    { id: "bebidas", nombre: "Bebidas", activa: true },
    { id: "postres", nombre: "Postres", activa: true },
  ];

let productos = [
  {
    id: 1,
    nombre: "Pique Macho",
    descripcion: "Clásico boliviano",
    precio: 35.0,
    categoriaId: "platos",
    imagenes: [],
    requiereInventario: false,
    stockActual: 0,
    stockMinimo: 0,
    disponible: true,
    opciones: [],
    receta: [], // { insumoId, cantidad, unidad }
  },
  {
    id: 2,
    nombre: "Coca 500ml",
    descripcion: "",
    precio: 8.0,
    categoriaId: "bebidas",
    imagenes: [],
    requiereInventario: true,
    stockActual: 24,
    stockMinimo: 6,
    disponible: true,
    opciones: [],
    receta: [],
  },
  {
    id: 3,
    nombre: "Flan casero",
    descripcion: "",
    precio: 12.0,
    categoriaId: "postres",
    imagenes: [],
    requiereInventario: false,
    stockActual: 0,
    stockMinimo: 0,
    disponible: true,
    opciones: [],
    receta: [],
  },
];

  let productoOpcionesTemp = [];
  let productoRecetaTemp = []; // { insumoId, insumoNombre, cantidad, unidad }
  let productoEditandoId = null;
  let productoImagenesTemp = [];
  let grupoEditandoIndex = null;
  let grupoItemsTemp = [];

  const filtroBusquedaProducto = document.getElementById(
    "filtroBusquedaProducto"
  );
  const filtroCategoriaProducto = document.getElementById(
    "filtroCategoriaProducto"
  );
  const filtroEstadoProducto =
    document.getElementById("filtroEstadoProducto");
  const btnResetFiltrosProducto = document.getElementById(
    "btnResetFiltrosProducto"
  );
  const btnMostrarFormProducto = document.getElementById(
    "btnMostrarFormProducto"
  );
  const btnGestionCategorias =
    document.getElementById("btnGestionCategorias");

  const productoFormSection = document.getElementById("productoFormSection");
  const productoFormTitulo = document.getElementById("productoFormTitulo");
  const productoForm = document.getElementById("productoForm");

  const prodNombre = document.getElementById("prodNombre");
  const prodDescripcion = document.getElementById("prodDescripcion");
  const prodPrecio = document.getElementById("prodPrecio");
  const prodCategoria = document.getElementById("prodCategoria");
  const prodDisponible = document.getElementById("prodDisponible");

  const prodReqInv = document.getElementById("prodReqInv");
  const prodStock = document.getElementById("prodStock");
  const prodStockMin = document.getElementById("prodStockMin");

  const prodAddImageBtn = document.getElementById("prodAddImageBtn");
  const prodImagen = document.getElementById("prodImagen");
  const prodImagesGrid = document.getElementById("prodImagesGrid");

  const productoCancelar = document.getElementById("productoCancelar");
  const productosTableBody =
    document.getElementById("productosTableBody");

  const stockAlertList = document.getElementById("stockAlertList");

  const generarIdProducto = () =>
    productos.length ? Math.max(...productos.map((p) => p.id)) + 1 : 1;
  const findCategoriaById = (id) => categorias.find((c) => c.id === id);

  function slugify(str) {
  return (str || "")
    .toLowerCase()
    .normalize("NFD").replace(/[\u0300-\u036f]/g, "")
    .replace(/\s+/g, "-")
    .replace(/[^a-z0-9\-]/g, "");
}


  const prodHasOptions = document.getElementById("prodHasOptions");
  const productOptionsContent = document.getElementById("productOptionsContent");
  const optionGroupsTableBody = document.getElementById("optionGroupsTableBody");
  const btnAddOptionGroup = document.getElementById("btnAddOptionGroup");
  const optionGroupEditor = document.getElementById("optionGroupEditor");
  const optGroupNombre = document.getElementById("optGroupNombre");
  const optItemNombre = document.getElementById("optItemNombre");
  const optItemPrecio = document.getElementById("optItemPrecio");
  const btnAddOptItem = document.getElementById("btnAddOptItem");
  const optItemsTableBody = document.getElementById("optItemsTableBody");
  const btnGuardarGrupo = document.getElementById("btnGuardarGrupo");

  // === RECETAS ===
  const prodHasReceta = document.getElementById("prodHasReceta");
  const productRecetaContent = document.getElementById("productRecetaContent");
  const recetaTableBody = document.getElementById("recetaTableBody");
  const btnAddIngrediente = document.getElementById("btnAddIngrediente");
  const btnCancelarGrupo = document.getElementById("btnCancelarGrupo");


  function getInvBadgeClass(p) {
    if (!p.requiereInventario) return "badge badge--inv";
    if (p.stockActual <= p.stockMinimo)
      return "badge badge--inv badge--inv-low";
    return "badge badge--inv badge--inv-ok";
  }
  function renderOptionGroupsTable() {
  if (!optionGroupsTableBody) return;
  optionGroupsTableBody.innerHTML = "";

  if (!productoOpcionesTemp.length) {
    const tr = document.createElement("tr");
    tr.innerHTML =
      '<td colspan="4" class="empty-cell">Sin grupos definidos.</td>';
    optionGroupsTableBody.appendChild(tr);
    return;
  }

  productoOpcionesTemp.forEach((g, index) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${index + 1}</td>
      <td>${g.nombre}</td>
      <td>${(g.items || []).length}</td>
      <td>
        <div class="actions-cell">
          <button type="button" class="action-btn" data-edit-group="${index}">Editar</button>
          <button type="button" class="action-btn" data-del-group="${index}">🗑</button>
        </div>
      </td>
    `;
    optionGroupsTableBody.appendChild(tr);
  });

  optionGroupsTableBody
    .querySelectorAll("[data-edit-group]")
    .forEach((btn) => {
      btn.addEventListener("click", () => {
        const idx = Number(btn.getAttribute("data-edit-group"));
        startEditarGrupo(idx);
      });
    });

  optionGroupsTableBody
    .querySelectorAll("[data-del-group]")
    .forEach((btn) => {
      btn.addEventListener("click", () => {
        const idx = Number(btn.getAttribute("data-del-group"));
        eliminarGrupo(idx);
      });
    });
}

function renderOptItemsTable() {
  if (!optItemsTableBody) return;
  optItemsTableBody.innerHTML = "";

  if (!grupoItemsTemp.length) {
    const tr = document.createElement("tr");
    tr.innerHTML =
      '<td colspan="3" class="empty-cell">Sin opciones agregadas.</td>';
    optItemsTableBody.appendChild(tr);
    return;
  }

  grupoItemsTemp.forEach((item, index) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${item.nombre}</td>
      <td class="price-cell">Bs ${Number(item.deltaPrecio).toFixed(2)}</td>
      <td>
        <button type="button" class="action-btn" data-del-item="${index}">🗑</button>
      </td>
    `;
    optItemsTableBody.appendChild(tr);
  });

  optItemsTableBody.querySelectorAll("[data-del-item]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const idx = Number(btn.getAttribute("data-del-item"));
      grupoItemsTemp.splice(idx, 1);
      renderOptItemsTable();
    });
  });
}

function resetGrupoEditor() {
  grupoEditandoIndex = null;
  grupoItemsTemp = [];
  if (optGroupNombre) optGroupNombre.value = "";
  renderOptItemsTable();
}

function showGrupoEditor(show) {
  if (!optionGroupEditor) return;
  optionGroupEditor.classList.toggle("hidden", !show);
}

function startNuevoGrupo() {
  resetGrupoEditor();
  showGrupoEditor(true);
  optGroupNombre?.focus();
}

function startEditarGrupo(index) {
  const grupo = productoOpcionesTemp[index];
  if (!grupo) return;
  grupoEditandoIndex = index;
  grupoItemsTemp = Array.isArray(grupo.items) ? [...grupo.items] : [];
  if (optGroupNombre) optGroupNombre.value = grupo.nombre;
  showGrupoEditor(true);
  renderOptItemsTable();
  optGroupNombre?.focus();
}

function eliminarGrupo(index) {
  if (!confirm("¿Eliminar este grupo de opciones?")) return;
  productoOpcionesTemp.splice(index, 1);
  renderOptionGroupsTable();
}

function setOptionsEnabledFromCheckbox() {
  const enabled = !!prodHasOptions?.checked;
  if (!productOptionsContent) return;
  productOptionsContent.classList.toggle("hidden", !enabled);
  if (!enabled) {
    productoOpcionesTemp = [];
    resetGrupoEditor();
    renderOptionGroupsTable();
  }
}

// ===== RECETA: mostrar/ocultar =====
function setRecetaEnabledFromCheckbox() {
  const enabled = !!prodHasReceta?.checked;
  if (!productRecetaContent) return;

  productRecetaContent.classList.toggle("hidden", !enabled);

  // Si se desactiva, vaciamos la receta temporal
  if (!enabled) {
    productoRecetaTemp = [];
    renderRecetaTable();
  }
}

// ===== RECETA: renderizar tabla =====
function renderRecetaTable() {
  if (!recetaTableBody) return;

  recetaTableBody.innerHTML = "";

  if (!productoRecetaTemp.length) {
    const tr = document.createElement("tr");
    tr.innerHTML =
      '<td colspan="5" class="empty-cell">Sin ingredientes definidos.</td>';
    recetaTableBody.appendChild(tr);
    return;
  }

  productoRecetaTemp.forEach((item, index) => {
    const insumo = insumos.find((i) => i.id === item.insumoId);
    const catNombre = insumo
      ? (categoriasInsumos.find((c) => c.id === insumo.categoriaId)?.nombre ||
          "Sin categoría")
      : "Insumo eliminado";

    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${index + 1}</td>
      <td>
        <div class="stock-alert-name">${
          insumo ? insumo.nombre : "Insumo no encontrado"
        }</div>
        <div class="stock-alert-meta">${catNombre}</div>
      </td>
      <td style="text-align:right;">${item.cantidad}</td>
      <td>${item.unidad || (insumo?.unidad || "")}</td>
      <td>
        <div class="actions-cell">
          <button type="button" class="action-btn" data-del-receta="${index}">🗑</button>
        </div>
      </td>
    `;
    recetaTableBody.appendChild(tr);
  });

  recetaTableBody
    .querySelectorAll("[data-del-receta]")
    .forEach((btn) => {
      btn.addEventListener("click", () => {
        const index = Number(btn.getAttribute("data-del-receta"));
        if (Number.isNaN(index)) return;
        // Sin prompt(), eliminación directa
        productoRecetaTemp.splice(index, 1);
        renderRecetaTable();
      });
    });
}

// ===== RECETA: fila editor para añadir ingrediente =====
function showRecetaEditor() {
  if (!recetaTableBody) return;

  // Primero dibujamos la tabla actual
  renderRecetaTable();

  const tr = document.createElement("tr");
  tr.className = "receta-editor-row";
  tr.innerHTML = `
    <td>+</td>
    <td>
      <select class="mesa-form-input" data-receta-insumo>
        <option value="">Seleccionar insumo...</option>
      </select>
    </td>
    <td style="text-align:right;">
      <input type="number" min="0" step="0.01" class="mesa-form-input" data-receta-cantidad />
    </td>
    <td>
      <input type="text" class="mesa-form-input" placeholder="ej. kg, u, ml" data-receta-unidad />
    </td>
    <td>
      <div class="actions-cell">
        <button type="button" class="action-btn" data-save-receta>💾</button>
        <button type="button" class="action-btn" data-cancel-receta>✖</button>
      </div>
    </td>
  `;
  recetaTableBody.appendChild(tr);

  const sel = tr.querySelector("[data-receta-insumo]");
  const cantInput = tr.querySelector("[data-receta-cantidad]");
  const unidadInput = tr.querySelector("[data-receta-unidad]");
  const btnSave = tr.querySelector("[data-save-receta]");
  const btnCancel = tr.querySelector("[data-cancel-receta]");

  // Llenar select con insumos existentes
  insumos
    .slice()
    .sort((a, b) => a.nombre.localeCompare(b.nombre))
    .forEach((i) => {
      const opt = new Option(i.nombre, String(i.id));
      sel.add(opt);
    });

  // Al cambiar insumo, rellenar unidad si está vacía
  sel.addEventListener("change", () => {
    const id = Number(sel.value);
    const insumo = insumos.find((i) => i.id === id);
    if (insumo && !unidadInput.value) {
      unidadInput.value = insumo.unidad || "";
    }
  });

  btnSave?.addEventListener("click", () => {
    const insumoId = Number(sel.value);
    const cantidad = Number(cantInput.value) || 0;
    const unidad = (unidadInput.value || "").trim();

    if (!insumoId) {
      // sin prompt, solo no hace nada si está vacío
      sel.classList.add("input-error");
      return;
    }
    if (cantidad <= 0) {
      cantInput.classList.add("input-error");
      return;
    }

    const duplicado = productoRecetaTemp.some(
      (r) => r.insumoId === insumoId
    );
    if (duplicado) {
      // ya existe, no lo agregamos otra vez
      sel.classList.add("input-error");
      return;
    }

    const insumo = insumos.find((i) => i.id === insumoId);
    productoRecetaTemp.push({
      insumoId,
      cantidad,
      unidad: unidad || insumo?.unidad || "",
    });

    renderRecetaTable();
  });

  btnCancel?.addEventListener("click", () => {
    renderRecetaTable();
  });

  sel.focus();
}

// Eventos de Receta
prodHasReceta?.addEventListener("change", setRecetaEnabledFromCheckbox);

btnAddIngrediente?.addEventListener("click", () => {
  if (!prodHasReceta?.checked) {
    prodHasReceta.checked = true;
    setRecetaEnabledFromCheckbox();
  }
  showRecetaEditor();
});

  function renderSelectCategoriasProducto() {
    if (!filtroCategoriaProducto || !prodCategoria) return;

    filtroCategoriaProducto.innerHTML = "";
    const optAll = new Option("Todas", "todas");
    filtroCategoriaProducto.add(optAll);

    prodCategoria.innerHTML = "";

    categorias
      .filter((c) => c.activa)
      .forEach((c) => {
        const o1 = new Option(c.nombre, c.id);
        const o2 = new Option(c.nombre, c.id);
        filtroCategoriaProducto.add(o1);
        prodCategoria.add(o2);
      });

    filtroCategoriaProducto.value = "todas";
  }

  function mostrarFormProducto(modo) {
    productoFormSection?.classList.remove("hidden");
    productoFormTitulo.textContent =
      modo === "editar" ? "Editar producto" : "Nuevo producto";
  }

  function ocultarFormProducto() {
    productoFormSection?.classList.add("hidden");
    productoEditandoId = null;
    productoForm?.reset();
    productoImagenesTemp = [];
    renderImagenesPreviews();
    document
      .querySelectorAll(".inv-field")
      .forEach((el) => el.classList.add("hidden"));

    // limpiar opciones
    productoOpcionesTemp = [];
    if (prodHasOptions) {
      prodHasOptions.checked = false;
      setOptionsEnabledFromCheckbox();
    }
    renderOptionGroupsTable();
    resetGrupoEditor();
    showGrupoEditor(false);

    // limpiar receta
    productoRecetaTemp = [];
    if (prodHasReceta) {
      prodHasReceta.checked = false;
      setRecetaEnabledFromCheckbox();
    }
    renderRecetaTable();
  }

  function renderImagenesPreviews() {
    if (!prodImagesGrid) return;
    prodImagesGrid.innerHTML = "";

    if (!productoImagenesTemp.length) {
      const empty = document.createElement("div");
      empty.className = "product-images-empty";
      empty.textContent = "Sin imágenes";
      prodImagesGrid.appendChild(empty);
      return;
    }

    productoImagenesTemp.forEach((src, index) => {
      const box = document.createElement("div");
      box.className = "product-images-box";

      const thumb = document.createElement("div");
      thumb.className = "product-images-thumb";
      thumb.style.backgroundImage = `url('${src}')`;

      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "product-images-remove";
      btn.innerHTML = "×";
      btn.dataset.index = String(index);

      box.appendChild(thumb);
      box.appendChild(btn);
      prodImagesGrid.appendChild(box);
    });
  }

  function renderStockAlerts() {
    if (!stockAlertList) return;

    const enAlerta = productos.filter(
      (p) =>
        p.requiereInventario &&
        p.stockMinimo > 0 &&
        p.stockActual <= p.stockMinimo
    );

    stockAlertList.innerHTML = "";

    if (!enAlerta.length) {
      const li = document.createElement("li");
      li.className = "stock-alert-item";
      li.innerHTML =
        '<span class="stock-alert-meta">Todos los productos están por encima del stock mínimo.</span>';
      stockAlertList.appendChild(li);

      // Limpiar notificaciones y badge
      updateNotifications("productos", []);
      setNavBadge("productos", 0);
      return;
    }

    enAlerta.forEach((p) => {
      const catNombre =
        findCategoriaById(p.categoriaId)?.nombre || "Sin categoría";
      const li = document.createElement("li");
      li.className = "stock-alert-item";
      li.innerHTML = `
      <span class="stock-alert-name">${p.nombre}</span>
      <span class="stock-alert-meta">${catNombre} · ${p.stockActual} / min ${p.stockMinimo}</span>
      <span class="stock-alert-badge">Stock bajo</span>
    `;
      stockAlertList.appendChild(li);
    });

    // 🔔 Actualizar notificaciones globales (campanita)
    updateNotifications(
      "productos",
      enAlerta.map((p) => ({
        id: "prod-" + p.id,
        type: "productos",
        label: `Stock bajo: ${p.nombre}`,
        detail: `Stock: ${p.stockActual} · Mínimo: ${p.stockMinimo}`,
        tag: "Productos",
        target: "productos",
      }))
    );

    // 🔢 Actualizar número en el menú lateral
    setNavBadge("productos", enAlerta.length);
  }

  function renderTablaProductos() {
    if (!productosTableBody) return;
    const texto = (filtroBusquedaProducto?.value || "").toLowerCase();
    const cat = filtroCategoriaProducto?.value || "todas";
    const est = filtroEstadoProducto?.value || "todos";

    productosTableBody.innerHTML = "";

    productos
      .slice()
      .sort((a, b) => a.id - b.id)
      .forEach((p, idx) => {
        const catNombre =
          findCategoriaById(p.categoriaId)?.nombre || "N/D";

        const coincideTexto =
          !texto ||
          p.nombre.toLowerCase().includes(texto) ||
          catNombre.toLowerCase().includes(texto);

        const coincideCat = cat === "todas" || p.categoriaId === cat;
        const coincideEstado =
          est === "todos" ||
          (est === "disponibles" && p.disponible) ||
          (est === "no-disponibles" && !p.disponible);

        if (!coincideTexto || !coincideCat || !coincideEstado) return;

        const primeraImagen =
          p.imagenes && p.imagenes.length ? p.imagenes[0] : "";

        const tr = document.createElement("tr");
        tr.innerHTML = `
      <td>${idx + 1}</td>
      <td><div class="prod-img" style="background-image:url('${primeraImagen}')"></div></td>
      <td>
        ${p.nombre}
        ${
          p.opciones && p.opciones.length
            ? '<span class="prod-config-badge">Configurable</span>'
            : ""
        }
      </td>
      <td>${catNombre}</td>
      <td class="price-cell">Bs ${Number(p.precio).toFixed(2)}</td>
      <td>
        <span class="${getInvBadgeClass(p)}">
          ${
            p.requiereInventario
              ? `${p.stockActual} / min ${p.stockMinimo}`
              : "—"
          }
        </span>
      </td>
      <td>
        <label class="mini-switch">
          <input type="checkbox" class="mini-switch-input" data-disp-id="${p.id}" ${
          p.disponible ? "checked" : ""
        }/>
          <span class="mini-switch-slider"></span>
        </label>
      </td>
      <td>
        <div class="actions-cell">
          <button class="action-btn" data-edit-prod="${p.id}">Editar</button>
          <button class="action-btn" data-del-prod="${p.id}">🗑</button>
        </div>
      </td>
    `;
        productosTableBody.appendChild(tr);
      });

    productosTableBody.querySelectorAll("[data-edit-prod]").forEach((btn) => {
      btn.addEventListener("click", () =>
        abrirEdicionProducto(
          Number(btn.getAttribute("data-edit-prod"))
        )
      );
    });
    productosTableBody.querySelectorAll("[data-del-prod]").forEach((btn) => {
      btn.addEventListener("click", () =>
        eliminarProducto(Number(btn.getAttribute("data-del-prod")))
      );
    });

    productosTableBody.querySelectorAll("[data-disp-id]").forEach((inp) => {
      inp.addEventListener("change", () => {
        const id = Number(inp.getAttribute("data-disp-id"));
        const p = productos.find((x) => x.id === id);
        if (!p) return;
        p.disponible = inp.checked;
        renderTablaProductos();
        renderStockAlerts();
      });
    });

    renderStockAlerts();
  }

  function abrirEdicionProducto(id) {
    const p = productos.find((x) => x.id === id);
    if (!p) return;

    productoEditandoId = id;
    mostrarFormProducto("editar");

    prodNombre.value = p.nombre;
    prodDescripcion.value = p.descripcion || "";
    prodPrecio.value = String(p.precio);
    prodCategoria.value = p.categoriaId;
    prodDisponible.checked = p.disponible;

    prodReqInv.checked = p.requiereInventario;
    document
      .querySelectorAll(".inv-field")
      .forEach((el) =>
        el.classList.toggle("hidden", !p.requiereInventario)
      );
    prodStock.value = String(p.stockActual || 0);
    prodStockMin.value = String(p.stockMinimo || 0);

    productoImagenesTemp = Array.isArray(p.imagenes)
      ? [...p.imagenes]
      : [];
    renderImagenesPreviews();

    productoOpcionesTemp = Array.isArray(p.opciones)
      ? JSON.parse(JSON.stringify(p.opciones))
      : [];
    grupoItemsTemp = [];
    grupoEditandoIndex = null;

    if (prodHasOptions) {
      prodHasOptions.checked = productoOpcionesTemp.length > 0;
    }
    setOptionsEnabledFromCheckbox();
    renderOptionGroupsTable();
    resetGrupoEditor();
    showGrupoEditor(false);

    // Cargar receta si existe
    productoRecetaTemp = Array.isArray(p.receta)
      ? JSON.parse(JSON.stringify(p.receta))
      : [];
    if (prodHasReceta) {
      prodHasReceta.checked = productoRecetaTemp.length > 0;
    }
    setRecetaEnabledFromCheckbox();
    renderRecetaTable();
  }

  function eliminarProducto(id) {
    if (!confirm("¿Eliminar este producto?")) return;
    productos = productos.filter((p) => p.id !== id);
    renderTablaProductos();
  }

  btnMostrarFormProducto?.addEventListener("click", () => {
    productoEditandoId = null;
    productoImagenesTemp = [];
    renderImagenesPreviews();
    productoOpcionesTemp = [];
    productoRecetaTemp = [];
    grupoItemsTemp = [];
    grupoEditandoIndex = null;
    if (prodHasOptions) {
      prodHasOptions.checked = false;
      setOptionsEnabledFromCheckbox();
    }
    if (prodHasReceta) {
      prodHasReceta.checked = false;
      setRecetaEnabledFromCheckbox();
    }
    renderOptionGroupsTable();
    renderRecetaTable();
    resetGrupoEditor();
    showGrupoEditor(false);
    mostrarFormProducto("crear");
  });

  productoCancelar?.addEventListener("click", ocultarFormProducto);

  productoForm?.addEventListener("submit", (e) => {
    e.preventDefault();

    const nombre = prodNombre.value.trim();
    const precio = Number(prodPrecio.value) || 0;
    const categoriaId = prodCategoria.value;
    const descripcion = (prodDescripcion.value || "").trim();
    const disponible = !!prodDisponible.checked;

    const requiereInventario = !!prodReqInv.checked;
    const stockActual = requiereInventario
      ? Number(prodStock.value) || 0
      : 0;
    const stockMinimo = requiereInventario
      ? Number(prodStockMin.value) || 0
      : 0;

    if (!nombre) return;
    if (!categoriaId) return;

    // Validación de números negativos
    if (precio < 0) {
      alert("El precio no puede ser negativo.");
      return;
    }

    if (stockActual < 0) {
      alert("El stock actual no puede ser negativo.");
      return;
    }

    if (stockMinimo < 0) {
      alert("El stock mínimo no puede ser negativo.");
      return;
    }

    const duplicado = productos.some(
      (p) =>
        p.nombre.toLowerCase() === nombre.toLowerCase() &&
        p.categoriaId === categoriaId &&
        (!productoEditandoId || p.id !== productoEditandoId)
    );
    if (duplicado) {
      alert("Ya existe un producto con ese nombre en esa categoría.");
      return;
    }

    if (productoEditandoId) {
      const p = productos.find((x) => x.id === productoEditandoId);
      if (!p) return;
      p.nombre = nombre;
      p.descripcion = descripcion;
      p.precio = precio;
      p.categoriaId = categoriaId;
      p.disponible = disponible;
      p.requiereInventario = requiereInventario;
      p.stockActual = stockActual;
      p.stockMinimo = stockMinimo;
      p.imagenes = [...productoImagenesTemp];
      p.opciones =
        prodHasOptions && prodHasOptions.checked
          ? JSON.parse(JSON.stringify(productoOpcionesTemp))
          : [];
      p.receta =
        prodHasReceta && prodHasReceta.checked
          ? JSON.parse(JSON.stringify(productoRecetaTemp))
          : [];
    } else {
      productos.push({
        id: generarIdProducto(),
        nombre,
        descripcion,
        precio,
        categoriaId,
        imagenes: [...productoImagenesTemp],
        requiereInventario,
        stockActual,
        stockMinimo,
        disponible,
        opciones:
          prodHasOptions && prodHasOptions.checked
            ? JSON.parse(JSON.stringify(productoOpcionesTemp))
            : [],
        receta:
          prodHasReceta && prodHasReceta.checked
            ? JSON.parse(JSON.stringify(productoRecetaTemp))
            : [],
      });
    }

    ocultarFormProducto();
    renderTablaProductos();
  });

  prodAddImageBtn?.addEventListener("click", () => {
    prodImagen?.click();
  });

  prodImagen?.addEventListener("change", () => {
    const files = Array.from(prodImagen.files || []);
    if (!files.length) return;

    files.forEach((file) => {
      const reader = new FileReader();
      reader.onload = () => {
        const dataUrl = reader.result;
        if (typeof dataUrl === "string") {
          productoImagenesTemp.push(dataUrl);
          renderImagenesPreviews();
        }
      };
      reader.readAsDataURL(file);
    });

    prodImagen.value = "";
  });

  prodImagesGrid?.addEventListener("click", (e) => {
    const target = e.target;
    if (!(target instanceof HTMLElement)) return;
    if (!target.classList.contains("product-images-remove")) return;

    const index = Number(target.dataset.index);
    if (Number.isNaN(index)) return;

    productoImagenesTemp.splice(index, 1);
    renderImagenesPreviews();
  });

  prodReqInv?.addEventListener("change", () => {
    const show = prodReqInv.checked;
    document
      .querySelectorAll(".inv-field")
      .forEach((el) => el.classList.toggle("hidden", !show));
  });

  filtroBusquedaProducto?.addEventListener("input", renderTablaProductos);
  filtroCategoriaProducto?.addEventListener("change", renderTablaProductos);
  filtroEstadoProducto?.addEventListener("change", renderTablaProductos);
  btnResetFiltrosProducto?.addEventListener("click", () => {
    filtroBusquedaProducto.value = "";
    filtroCategoriaProducto.value = "todas";
    filtroEstadoProducto.value = "todos";
    renderTablaProductos();
  });

  /* ===== MODAL CATEGORÍAS ===== */

  const categoriasModal = document.getElementById("categoriasModal");
  const categoriasModalBackdrop = document.getElementById(
    "categoriasModalBackdrop"
  );
  const categoriasModalCerrar = document.getElementById(
    "categoriasModalCerrar"
  );

  const categoriasTableBody = document.getElementById(
    "categoriasTableBody"
  );
  const catNombreInput = document.getElementById("catNombreInput");
  const catGuardarBtn = document.getElementById("catGuardarBtn");
  const catCancelarEdicionBtn = document.getElementById(
    "catCancelarEdicionBtn"
  );

  let categoriaEditandoId = null;

  function abrirCategoriasModal() {
    categoriaEditandoId = null;
    if (catNombreInput) catNombreInput.value = "";
    if (catGuardarBtn) catGuardarBtn.textContent = "Añadir";
    catCancelarEdicionBtn?.classList.add("hidden");
    categoriasModal?.classList.remove("hidden");
    renderCategoriasTabla();
    setTimeout(() => catNombreInput?.focus(), 50);
  }

  function cerrarCategoriasModal() {
    categoriasModal?.classList.add("hidden");
  }

  function renderCategoriasTabla() {
    if (!categoriasTableBody) return;
    categoriasTableBody.innerHTML = "";

    categorias.forEach((cat, idx) => {
      const count = productos.filter(
        (p) => p.categoriaId === cat.id
      ).length;

      const tr = document.createElement("tr");
      tr.innerHTML = `
      <td>${idx + 1}</td>
      <td>${cat.nombre}</td>
      <td>${count}</td>
      <td>
        <div class="actions-cell">
          <button class="action-btn" data-edit-cat="${cat.id}">Editar</button>
          <button class="action-btn" data-del-cat="${cat.id}">🗑</button>
        </div>
      </td>
    `;
      categoriasTableBody.appendChild(tr);
    });

    categoriasTableBody
      .querySelectorAll("[data-edit-cat]")
      .forEach((btn) => {
        btn.addEventListener("click", () => {
          const id = btn.getAttribute("data-edit-cat");
          const cat = categorias.find((c) => c.id === id);
          if (!cat) return;
          categoriaEditandoId = id;
          catNombreInput.value = cat.nombre;
          catGuardarBtn.textContent = "Guardar";
          catCancelarEdicionBtn.classList.remove("hidden");
          catNombreInput.focus();
        });
      });

    categoriasTableBody
      .querySelectorAll("[data-del-cat]")
      .forEach((btn) => {
        btn.addEventListener("click", () => {
          const id = btn.getAttribute("data-del-cat");
          const cat = categorias.find((c) => c.id === id);
          if (!cat) return;
          if (
            !confirm(
              `¿Eliminar la categoría "${cat.nombre}"?\nLos productos quedarán sin categoría.`
            )
          )
            return;

          categorias = categorias.filter((c) => c.id !== id);
          productos.forEach((p) => {
            if (p.categoriaId === id) p.categoriaId = "";
          });

          renderSelectCategoriasProducto();
          renderTablaProductos();
          renderCategoriasTabla();
          if (typeof renderStockAlerts === "function")
            renderStockAlerts();
        });
      });
  }

  catGuardarBtn?.addEventListener("click", () => {
    const nombre = (catNombreInput.value || "").trim();
    if (!nombre) return;

    const slug = nombre
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .replace(/\s+/g, "-")
      .replace(/[^a-z0-9\-]/g, "");

    if (!slug) {
      alert("El nombre no es válido.");
      return;
    }

    const existe = categorias.some(
      (c) => c.id === slug && c.id !== categoriaEditandoId
    );
    if (existe) {
      alert("Ya existe una categoría con un nombre muy similar.");
      return;
    }

    if (categoriaEditandoId) {
      const cat = categorias.find((c) => c.id === categoriaEditandoId);
      if (!cat) return;
      const oldId = cat.id;
      cat.nombre = nombre;
      cat.id = slug;

      if (oldId !== slug) {
        productos.forEach((p) => {
          if (p.categoriaId === oldId) p.categoriaId = slug;
        });
      }
    } else {
      categorias.push({ id: slug, nombre, activa: true });
    }

    categoriaEditandoId = null;
    catNombreInput.value = "";
    catGuardarBtn.textContent = "Añadir";
    catCancelarEdicionBtn.classList.add("hidden");

    renderSelectCategoriasProducto();
    renderTablaProductos();
    renderCategoriasTabla();
    if (typeof renderStockAlerts === "function") renderStockAlerts();
  });

  catCancelarEdicionBtn?.addEventListener("click", () => {
    categoriaEditandoId = null;
    catNombreInput.value = "";
    catGuardarBtn.textContent = "Añadir";
    catCancelarEdicionBtn.classList.add("hidden");
  });

  btnGestionCategorias?.addEventListener("click", abrirCategoriasModal);
  categoriasModalCerrar?.addEventListener("click", cerrarCategoriasModal);
  categoriasModalBackdrop?.addEventListener("click", cerrarCategoriasModal);

  function initProductos() {
    renderSelectCategoriasProducto();
    renderImagenesPreviews();
    renderTablaProductos();
    renderCategoriasTabla();
  }

  initProductos();
  prodHasOptions?.addEventListener("change", setOptionsEnabledFromCheckbox);

  // === RECETAS: Renderizar tabla ===
  function renderRecetaTable() {
    if (!recetaTableBody) return;

    if (!productoRecetaTemp.length) {
      recetaTableBody.innerHTML = `
        <tr>
          <td colspan="5" class="empty-cell">
            Sin ingredientes configurados.
          </td>
        </tr>
      `;
      return;
    }

    recetaTableBody.innerHTML = productoRecetaTemp
      .map(
        (item, index) => `
        <tr>
          <td>${index + 1}</td>
          <td>${item.insumoNombre}</td>
          <td style="text-align:right;">${item.cantidad}</td>
          <td>${item.unidad}</td>
          <td>
            <button type="button" data-receta-index="${index}" class="btn btn--ghost btn--tiny btn-delete-receta">
              Eliminar
            </button>
          </td>
        </tr>
      `
      )
      .join("");

    // Event listener para botones de eliminar
    recetaTableBody.querySelectorAll('.btn-delete-receta').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const index = Number(e.target.dataset.recetaIndex);
        productoRecetaTemp.splice(index, 1);
        renderRecetaTable();
      });
    });
  }

btnAddOptionGroup?.addEventListener("click", () => {
  if (!prodHasOptions) return;
  if (!prodHasOptions.checked) {
    prodHasOptions.checked = true;
    setOptionsEnabledFromCheckbox();
  }
  startNuevoGrupo();
});

btnAddOptItem?.addEventListener("click", () => {
  const nombre = (optItemNombre?.value || "").trim();
  const delta = Number(optItemPrecio?.value || "0") || 0;
  if (!nombre) return;

  // Validación de precio extra negativo
  if (delta < 0) {
    alert("El precio extra no puede ser negativo.");
    return;
  }

  grupoItemsTemp.push({
    id: slugify(nombre),
    nombre,
    deltaPrecio: delta,
  });

  if (optItemNombre) optItemNombre.value = "";
  if (optItemPrecio) optItemPrecio.value = "";
  renderOptItemsTable();
});

btnGuardarGrupo?.addEventListener("click", () => {
  const nombreGrupo = (optGroupNombre?.value || "").trim();
  if (!nombreGrupo) {
    alert("El grupo debe tener un nombre.");
    return;
  }
  if (!grupoItemsTemp.length) {
    alert("El grupo debe tener al menos una opción.");
    return;
  }

  const idGrupo = slugify(nombreGrupo) || `grupo-${Date.now()}`;
  const grupoObj = {
    id: idGrupo,
    nombre: nombreGrupo,
    tipo: "multi", // multi por diseño
    items: [...grupoItemsTemp],
  };

  if (grupoEditandoIndex == null) {
    productoOpcionesTemp.push(grupoObj);
  } else {
    productoOpcionesTemp[grupoEditandoIndex] = grupoObj;
  }

  resetGrupoEditor();
  showGrupoEditor(false);
  renderOptionGroupsTable();
});

btnCancelarGrupo?.addEventListener("click", () => {
  resetGrupoEditor();
  showGrupoEditor(false);
});

});
