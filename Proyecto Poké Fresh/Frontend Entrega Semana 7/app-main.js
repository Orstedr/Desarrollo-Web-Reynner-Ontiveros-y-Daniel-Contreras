/**
 * Genera un número de boleta correlativo simulado.
 */
function generarNumeroBoleta() {
  STATE.contadorBoleta += 1;
  guardarEnStorage(LS_KEYS.boleta, STATE.contadorBoleta);
  const anio = new Date().getFullYear();
  return `POK-${anio}-${String(STATE.contadorBoleta).padStart(6, "0")}`;
}

// =====================================================================
// --- CONTROLADORES DE RENDERIZADO (DOM) ---
// =====================================================================

/* ---------- 1. Configurador "Arma tu bowl" ---------- */

function calcularTotalBowl() {
  let total = CONFIG_BASE.precioBase;

  const base = STATE.bowlActual.base ? buscarPorId(DB_BASES, STATE.bowlActual.base) : null;
  if (base) total += base.precio;

  const proteina = STATE.bowlActual.proteina ? buscarPorId(DB_PROTEINAS, STATE.bowlActual.proteina) : null;
  if (proteina) total += proteina.precio;

  const salsa = STATE.bowlActual.salsa ? buscarPorId(DB_SALSAS, STATE.bowlActual.salsa) : null;
  if (salsa) total += salsa.precio;

  STATE.bowlActual.toppings.forEach((toppingId) => {
    const topping = buscarPorId(DB_TOPPINGS, toppingId);
    if (topping) total += topping.precio;
  });

  return total;
}

function renderBowlResumen() {
  const cont = document.getElementById("resumen-bowl-lineas");
  const totalEl = document.getElementById("resumen-bowl-total");
  const btnAgregar = document.getElementById("btn-agregar-bowl");
  if (!cont || !totalEl) return;

  const lineas = [];

  const base = buscarPorId(DB_BASES, STATE.bowlActual.base);
  lineas.push(["Base", base ? base.nombre : "Sin seleccionar"]);

  const proteina = buscarPorId(DB_PROTEINAS, STATE.bowlActual.proteina);
  lineas.push(["Proteína", proteina ? proteina.nombre : "Sin seleccionar"]);

  const nombresToppings = STATE.bowlActual.toppings
    .map((id) => buscarPorId(DB_TOPPINGS, id))
    .filter(Boolean)
    .map((t) => t.nombre);
  lineas.push(["Toppings", nombresToppings.length ? nombresToppings.join(", ") : "Sin seleccionar"]);

  const salsa = buscarPorId(DB_SALSAS, STATE.bowlActual.salsa);
  lineas.push(["Salsa", salsa ? salsa.nombre : "Sin seleccionar"]);

  cont.innerHTML = lineas
    .map(
      ([etiqueta, valor]) => `
      <div class="linea-resumen">
        <span class="linea-resumen__etiqueta">${etiqueta}</span>
        <span class="linea-resumen__puntos" aria-hidden="true"></span>
        <span class="linea-resumen__valor">${valor}</span>
      </div>`
    )
    .join("");

  totalEl.textContent = formatCLP(calcularTotalBowl());

  const listo = STATE.bowlActual.base && STATE.bowlActual.proteina && STATE.bowlActual.salsa;
  if (btnAgregar) btnAgregar.disabled = !listo;
}

function inicializarConfigurador() {
  const grupoBase = document.getElementById("opciones-base");
  const grupoProteina = document.getElementById("opciones-proteina");
  const grupoToppings = document.getElementById("opciones-toppings");
  const grupoSalsa = document.getElementById("opciones-salsa");

  grupoBase.innerHTML = DB_BASES.map((op) => plantillaOpcionUnica("base", op)).join("");
  grupoProteina.innerHTML = DB_PROTEINAS.map((op) => plantillaOpcionUnica("proteina", op)).join("");
  grupoToppings.innerHTML = DB_TOPPINGS.map((op) => plantillaOpcionMultiple(op)).join("");
  grupoSalsa.innerHTML = DB_SALSAS.map((op) => plantillaOpcionUnica("salsa", op)).join("");

  document.querySelectorAll('input[name="base"]').forEach((input) =>
    input.addEventListener("change", (e) => {
      STATE.bowlActual.base = e.target.value;
      renderBowlResumen();
    })
  );
  document.querySelectorAll('input[name="proteina"]').forEach((input) =>
    input.addEventListener("change", (e) => {
      STATE.bowlActual.proteina = e.target.value;
      renderBowlResumen();
    })
  );
  document.querySelectorAll('input[name="salsa"]').forEach((input) =>
    input.addEventListener("change", (e) => {
      STATE.bowlActual.salsa = e.target.value;
      renderBowlResumen();
    })
  );
  document.querySelectorAll('input[name="topping"]').forEach((input) =>
    input.addEventListener("change", (e) => {
      const id = e.target.value;
      if (id === "ninguno" && e.target.checked) {
        // Seleccionar "Ninguno" limpia el resto de los toppings
        document.querySelectorAll('input[name="topping"]').forEach((chk) => {
          if (chk.value !== "ninguno") chk.checked = false;
        });
        STATE.bowlActual.toppings = ["ninguno"];
      } else {
        // Elegir cualquier otro topping desmarca "Ninguno"
        const chkNinguno = document.querySelector('input[name="topping"][value="ninguno"]');
        if (chkNinguno) chkNinguno.checked = false;
        STATE.bowlActual.toppings = Array.from(
          document.querySelectorAll('input[name="topping"]:checked')
        )
          .map((chk) => chk.value)
          .filter((v) => v !== "ninguno");
      }
      renderBowlResumen();
    })
  );

  renderBowlResumen();
}

function plantillaOpcionUnica(grupo, opcion) {
  const extra = opcion.precio > 0 ? `+${formatCLP(opcion.precio)}` : "";
  return `
    <label class="opcion-card">
      <input type="radio" name="${grupo}" value="${opcion.id}" />
      <span class="opcion-card__icono" aria-hidden="true">${opcion.icono}</span>
      <span class="opcion-card__texto">
        <span class="opcion-card__nombre">${opcion.nombre}</span>
        ${extra ? `<span class="opcion-card__precio">${extra}</span>` : ""}
      </span>
    </label>`;
}

function plantillaOpcionMultiple(opcion) {
  const extra = opcion.precio > 0 ? `+${formatCLP(opcion.precio)}` : "";
  return `
    <label class="opcion-card">
      <input type="checkbox" name="topping" value="${opcion.id}" />
      <span class="opcion-card__icono" aria-hidden="true">${opcion.icono}</span>
      <span class="opcion-card__texto">
        <span class="opcion-card__nombre">${opcion.nombre}</span>
        ${extra ? `<span class="opcion-card__precio">${extra}</span>` : ""}
      </span>
    </label>`;
}

function agregarBowlAlCarrito() {
  const base = buscarPorId(DB_BASES, STATE.bowlActual.base);
  const proteina = buscarPorId(DB_PROTEINAS, STATE.bowlActual.proteina);
  const salsa = buscarPorId(DB_SALSAS, STATE.bowlActual.salsa);
  if (!base || !proteina || !salsa) return;

  const toppings = STATE.bowlActual.toppings
    .map((id) => buscarPorId(DB_TOPPINGS, id))
    .filter(Boolean);

  const detalle = [
    base.nombre,
    proteina.nombre,
    toppings.length ? toppings.map((t) => t.nombre).join(", ") : "sin toppings",
    salsa.nombre,
  ].join(" · ");

  const item = {
    id: `bowl-${Date.now()}`,
    nombre: "Bowl personalizado",
    precioUnitario: calcularTotalBowl(),
    cantidad: 1,
    tipo: "bowl",
    detalle,
  };

  STATE.carrito.push(item);
  persistirCarrito();
  actualizarContadorCarrito();
  mostrarToast("Bowl agregado a tu pedido 🍚");

  // Reset del configurador
  STATE.bowlActual = { base: null, proteina: null, toppings: [], salsa: null };
  document
    .querySelectorAll('#configurador input[type="radio"], #configurador input[type="checkbox"]')
    .forEach((el) => (el.checked = false));
  renderBowlResumen();
}

/* ---------- 2. Menú y especiales ---------- */

function renderMenu() {
  const cont = document.getElementById("grid-menu");
  if (!cont) return;

  const productosFiltrados = STATE.filtrosMenuActivos.has("todos")
    ? DB_PRODUCTOS
    : DB_PRODUCTOS.filter((p) => STATE.filtrosMenuActivos.has(p.categoria));

  cont.innerHTML = productosFiltrados
    .map(
      (p) => `
      <article class="card-producto">
        <div class="card-producto__imagen" aria-hidden="true">${p.imagenEmoji}</div>
        <div class="card-producto__cuerpo">
          <h3>${p.nombre}</h3>
          <p class="card-producto__desc">${p.descripcion}</p>
          <div class="card-producto__pie">
            <span class="card-producto__precio">${formatCLP(p.precio)}</span>
            <button class="btn btn--small btn--primary" data-agregar-producto="${p.id}">Agregar</button>
          </div>
        </div>
      </article>`
    )
    .join("");

  document.querySelectorAll("[data-agregar-producto]").forEach((btn) =>
    btn.addEventListener("click", () => {
      const producto = buscarPorId(DB_PRODUCTOS, btn.dataset.agregarProducto);
      agregarProductoAlCarrito(producto, "producto");
    })
  );
}

function renderEspeciales() {
  const cont = document.getElementById("grid-especiales");
  if (!cont) return;

  cont.innerHTML = DB_ESPECIALES.map(
    (e) => `
      <article class="card-especial">
        <span class="card-especial__badge">${e.titulo}</span>
        <div class="card-especial__imagen" aria-hidden="true">${e.imagenEmoji}</div>
        <h3>${e.nombre}</h3>
        <p class="card-especial__desc">${e.descripcion}</p>
        <div class="card-especial__precios">
          <span class="card-especial__precio-normal">${formatCLP(e.precioNormal)}</span>
          <span class="card-especial__precio">${formatCLP(e.precio)}</span>
        </div>
        <button class="btn btn--primary btn--full" data-agregar-especial="${e.id}">Agregar al pedido</button>
      </article>`
  ).join("");

  document.querySelectorAll("[data-agregar-especial]").forEach((btn) =>
    btn.addEventListener("click", () => {
      const especial = buscarPorId(DB_ESPECIALES, btn.dataset.agregarEspecial);
      agregarProductoAlCarrito(
        { id: especial.id, nombre: especial.nombre, precio: especial.precio },
        "especial"
      );
    })
  );
}

function agregarProductoAlCarrito(producto, tipo) {
  if (!producto) return;
  const existente = STATE.carrito.find((item) => item.id === producto.id);
  if (existente) {
    existente.cantidad += 1;
  } else {
    STATE.carrito.push({
      id: producto.id,
      nombre: producto.nombre,
      precioUnitario: producto.precio,
      cantidad: 1,
      tipo,
      detalle: "",
    });
  }
  persistirCarrito();
  actualizarContadorCarrito();
  renderCarrito(); // refresca la lista/total del modal aunque ya esté abierto
  mostrarToast(`${producto.nombre} agregado 🥢`);
}

function inicializarFiltrosMenu() {
  const casillas = document.querySelectorAll("[data-filtro-menu]");
  const casillaTodos = document.querySelector('[data-filtro-menu="todos"]');

  casillas.forEach((casilla) =>
    casilla.addEventListener("change", () => {
      if (casilla.dataset.filtroMenu === "todos") {
        casillas.forEach((c) => {
          if (c !== casilla) c.checked = false;
        });
        casilla.checked = true; // "Todos" no puede quedar desmarcada por sí sola
      } else {
        casillaTodos.checked = false;
      }

      const activos = Array.from(casillas)
        .filter((c) => c.checked)
        .map((c) => c.dataset.filtroMenu);

      if (activos.length === 0) {
        casillaTodos.checked = true;
        STATE.filtrosMenuActivos = new Set(["todos"]);
      } else {
        STATE.filtrosMenuActivos = new Set(activos);
      }

      renderMenu();
    })
  );
}

/* ---------- 3. Carrito / Checkout ---------- */

function persistirCarrito() {
  guardarEnStorage(LS_KEYS.carrito, STATE.carrito);
}

function calcularTotalCarrito() {
  return STATE.carrito.reduce((acc, item) => acc + item.precioUnitario * item.cantidad, 0);
}

function actualizarContadorCarrito() {
  const badge = document.getElementById("contador-carrito");
  if (!badge) return;
  const cantidadTotal = STATE.carrito.reduce((acc, item) => acc + item.cantidad, 0);
  badge.textContent = cantidadTotal;
  badge.classList.toggle("oculto", cantidadTotal === 0);
}

function renderCarrito() {
  const cont = document.getElementById("lista-carrito");
  const totalEl = document.getElementById("carrito-total");
  const vacioEl = document.getElementById("carrito-vacio");
  if (!cont || !totalEl) return;

  if (STATE.carrito.length === 0) {
    cont.innerHTML = "";
    if (vacioEl) vacioEl.classList.remove("oculto");
  } else {
    if (vacioEl) vacioEl.classList.add("oculto");
    cont.innerHTML = STATE.carrito
      .map(
        (item, index) => `
        <li class="item-carrito">
          <div class="item-carrito__info">
            <span class="item-carrito__nombre">${item.nombre}</span>
            ${item.detalle ? `<span class="item-carrito__detalle">${item.detalle}</span>` : ""}
            <span class="item-carrito__precio-unit">${formatCLP(item.precioUnitario)} c/u</span>
          </div>
          <div class="item-carrito__cantidad">
            <button class="btn-cantidad" data-restar="${index}" aria-label="Restar cantidad">−</button>
            <span>${item.cantidad}</span>
            <button class="btn-cantidad" data-sumar="${index}" aria-label="Sumar cantidad">+</button>
          </div>
          <button class="btn-eliminar" data-eliminar="${index}" aria-label="Eliminar ítem">🗑️</button>
        </li>`
      )
      .join("");
  }

  totalEl.textContent = formatCLP(calcularTotalCarrito());

  document.querySelectorAll("[data-sumar]").forEach((btn) =>
    btn.addEventListener("click", () => {
      STATE.carrito[btn.dataset.sumar].cantidad += 1;
      persistirCarrito();
      renderCarrito();
      actualizarContadorCarrito();
    })
  );
  document.querySelectorAll("[data-restar]").forEach((btn) =>
    btn.addEventListener("click", () => {
      const item = STATE.carrito[btn.dataset.restar];
      item.cantidad -= 1;
      if (item.cantidad <= 0) STATE.carrito.splice(btn.dataset.restar, 1);
      persistirCarrito();
      renderCarrito();
      actualizarContadorCarrito();
    })
  );
  document.querySelectorAll("[data-eliminar]").forEach((btn) =>
    btn.addEventListener("click", () => {
      STATE.carrito.splice(btn.dataset.eliminar, 1);
      persistirCarrito();
      renderCarrito();
      actualizarContadorCarrito();
    })
  );
}

/**
 * "Anular carrito": vacía la selección ANTES de pagar. No requiere motivo
 * porque el pedido aún no existe como tal — es solo limpiar lo elegido.
 * Distinto del módulo de ANULACIÓN DE PEDIDO (CU7) más abajo, que reversa
 * un pedido YA confirmado y sí exige motivo.
 */
function anularCarrito() {
  if (STATE.carrito.length === 0) return;
  STATE.carrito = [];
  persistirCarrito();
  renderCarrito();
  actualizarContadorCarrito();
  mostrarToast("Carrito vaciado.");
}

function confirmarPago() {
  if (STATE.carrito.length === 0) return;

  const metodoPago = document.querySelector('input[name="metodo-pago"]:checked');
  if (!metodoPago) {
    mostrarToast("Selecciona un método de pago.", true);
    return;
  }

  const cliente = STATE.usuarioActual || {
    nombreCompleto: "Cliente sin sesión",
    email: "sin-correo@pokefresh.cl",
  };

  const numeroBoleta = generarNumeroBoleta();
  const pedido = {
    id: `pedido-${Date.now()}`,
    numeroBoleta,
    fecha: new Date().toLocaleString("es-CL"),
    items: JSON.parse(JSON.stringify(STATE.carrito)),
    total: calcularTotalCarrito(),
    metodoPago: metodoPago.value,
    cliente: { nombre: cliente.nombreCompleto || cliente.email, email: cliente.email },
    estado: "confirmado",
  };

  STATE.pedidosConfirmados.push(pedido);
  guardarEnStorage(LS_KEYS.pedidos, STATE.pedidosConfirmados);

  STATE.carrito = [];
  persistirCarrito();
  renderCarrito();
  actualizarContadorCarrito();

  cerrarModal("modal-carrito");
  mostrarBoleta(pedido);
}

function mostrarBoleta(pedido) {
  const modal = document.getElementById("modal-boleta");
  const cuerpo = document.getElementById("boleta-cuerpo");

  cuerpo.innerHTML = `
    <p class="boleta-numero">Boleta N° ${pedido.numeroBoleta}</p>
    <p class="boleta-fecha">${pedido.fecha}</p>
    <hr />
    <p><strong>Cliente:</strong> ${pedido.cliente.nombre}</p>
    <p><strong>Correo:</strong> ${pedido.cliente.email}</p>
    <p><strong>Método de pago:</strong> ${pedido.metodoPago === "webpay" ? "Webpay" : "Transferencia"}</p>
    <hr />
    <ul class="boleta-items">
      ${pedido.items
        .map(
          (item) => `
        <li>
          <span>${item.cantidad} × ${item.nombre}</span>
          <span>${formatCLP(item.precioUnitario * item.cantidad)}</span>
        </li>`
        )
        .join("")}
    </ul>
    <hr />
    <p class="boleta-total"><strong>Total:</strong> ${formatCLP(pedido.total)}</p>
    <p class="boleta-aviso">📧 Copia enviada a su correo.</p>
  `;

  abrirModal("modal-boleta");
  renderPedidosCancelables();
}

/* ---------- Columna derecha del carrito: dirección y despacho ---------- */

function prellenarDireccionCarrito() {
  const input = document.getElementById("carrito-direccion");
  const caja = document.getElementById("caja-radio-despacho");
  if (input && !input.value && STATE.usuarioActual && STATE.usuarioActual.direccion) {
    input.value = STATE.usuarioActual.direccion;
  }
  if (caja) {
    caja.textContent = `Radio de despacho: ${CONFIG_DESPACHO.radioGratuitoKm}km`;
  }
}

/* ---------- Sugerencias dentro del carrito ---------- */

function renderSugerencias() {
  const cont = document.getElementById("sugerencias-lista");
  if (!cont) return;

  const idsEnCarrito = new Set(STATE.carrito.map((item) => item.id));
  const disponibles = DB_PRODUCTOS.filter((p) => !idsEnCarrito.has(p.id));
  if (disponibles.length === 0) {
    cont.innerHTML = `<span class="texto-muted" style="font-size:0.8rem;">Ya agregaste todo el menú 🎉</span>`;
    return;
  }

  if (STATE.indiceSugerencia >= disponibles.length) STATE.indiceSugerencia = 0;
  if (STATE.indiceSugerencia < 0) STATE.indiceSugerencia = disponibles.length - 1;

  const sugerencia = disponibles[STATE.indiceSugerencia];
  cont.innerHTML = `
    <span class="sugerencia-item">
      ${sugerencia.imagenEmoji} ${sugerencia.nombre}
      <button type="button" data-agregar-sugerencia="${sugerencia.id}" aria-label="Agregar ${sugerencia.nombre}">+</button>
    </span>`;

  const btn = cont.querySelector("[data-agregar-sugerencia]");
  if (btn) {
    btn.addEventListener("click", () => {
      agregarProductoAlCarrito(sugerencia, "producto");
      renderSugerencias();
    });
  }
}

/* ---------- 4. Módulo de Anulación de Pedido (CU7) ---------- */
// Distinto de "anular carrito": aquí el pedido YA fue pagado/confirmado,
// por lo que anularlo es una reversa formal que exige un motivo.

function renderPedidosCancelables() {
  const cont = document.getElementById("lista-pedidos-cancelables");
  if (!cont) return;

  const pedidosActivos = STATE.pedidosConfirmados.filter((p) => p.estado === "confirmado");

  if (pedidosActivos.length === 0) {
    cont.innerHTML = `<p class="texto-muted">No tienes pedidos confirmados para anular.</p>`;
    return;
  }

  cont.innerHTML = pedidosActivos
    .map(
      (p) => `
      <div class="pedido-cancelable">
        <div>
          <strong>Boleta ${p.numeroBoleta}</strong>
          <span class="texto-muted"> — ${formatCLP(p.total)}</span>
        </div>
        <button class="btn btn--small btn--danger" data-anular-pedido="${p.id}">Anular pedido</button>
      </div>`
    )
    .join("");

  document.querySelectorAll("[data-anular-pedido]").forEach((btn) =>
    btn.addEventListener("click", () => abrirFormularioAnulacion(btn.dataset.anularPedido))
  );
}

let pedidoEnProcesoDeAnulacion = null;

function abrirFormularioAnulacion(pedidoId) {
  pedidoEnProcesoDeAnulacion = pedidoId;
  document.getElementById("form-anulacion-pedido").classList.remove("oculto");
  document.getElementById("motivo-anulacion").value = "";
  document.getElementById("motivo-anulacion").focus();
}

function confirmarAnulacionPedido(e) {
  e.preventDefault();
  const motivo = document.getElementById("motivo-anulacion").value.trim();
  if (!motivo) {
    mostrarToast("Debes ingresar un motivo para anular el pedido.", true);
    return;
  }
  const pedido = STATE.pedidosConfirmados.find((p) => p.id === pedidoEnProcesoDeAnulacion);
  if (pedido) {
    pedido.estado = "anulado";
    pedido.motivoAnulacion = motivo;
    guardarEnStorage(LS_KEYS.pedidos, STATE.pedidosConfirmados);
    mostrarToast(`Pedido ${pedido.numeroBoleta} anulado.`);
  }
  document.getElementById("form-anulacion-pedido").classList.add("oculto");
  pedidoEnProcesoDeAnulacion = null;
  renderPedidosCancelables();
}

/* ---------- 5. Autenticación (Login / Registro) ---------- */

function cambiarTabAuth(nombreTab) {
  document.querySelectorAll("[data-tab-auth]").forEach((t) =>
    t.classList.toggle("tab--activa", t.dataset.tabAuth === nombreTab)
  );
  document.querySelectorAll(".panel-auth").forEach((p) => p.classList.add("oculto"));
  document.getElementById(`form-${nombreTab}`).classList.remove("oculto");
}

function inicializarAuth() {
  document.querySelectorAll("[data-tab-auth]").forEach((tab) =>
    tab.addEventListener("click", () => cambiarTabAuth(tab.dataset.tabAuth))
  );

  // Enlaces "¿No tienes cuenta? Regístrate" / "¿Ya tienes cuenta? Inicia sesión"
  document.querySelectorAll("[data-ir-a-tab-auth]").forEach((enlace) =>
    enlace.addEventListener("click", (e) => {
      e.preventDefault();
      cambiarTabAuth(enlace.dataset.irATabAuth);
    })
  );

  document.getElementById("link-olvide-password").addEventListener("click", (e) => {
    e.preventDefault();
    mostrarToast("Te enviaremos instrucciones a tu correo para recuperar tu contraseña.");
  });

  document.querySelectorAll('input[name="sexo"]').forEach((input) =>
    input.addEventListener("change", () => {
      document
        .querySelectorAll(".pill-sexo")
        .forEach((pill) => pill.classList.toggle("pill-sexo--activa", pill.querySelector("input").checked));
    })
  );

  document.getElementById("form-login").addEventListener("submit", manejarLogin);
  document.getElementById("form-registro").addEventListener("submit", manejarRegistro);
}

function manejarLogin(e) {
  e.preventDefault();
  const email = document.getElementById("login-email").value.trim();
  const password = document.getElementById("login-password").value;
  const errorEl = document.getElementById("login-error");

  if (!validarEmail(email)) {
    errorEl.textContent = "Ingresa un correo válido.";
    errorEl.classList.remove("oculto");
    return;
  }

  const usuario = STATE.usuarios.find((u) => u.email === email && u.password === password);
  if (!usuario) {
    errorEl.textContent = "Correo o contraseña incorrectos.";
    errorEl.classList.remove("oculto");
    return;
  }

  errorEl.classList.add("oculto");
  iniciarSesion(usuario);
  cerrarModal("modal-auth");
}

function manejarRegistro(e) {
  e.preventDefault();
  const errorEl = document.getElementById("registro-error");
  errorEl.classList.add("oculto");

  const datos = {
    run: document.getElementById("registro-run").value.trim(),
    nombreCompleto: document.getElementById("registro-nombre").value.trim(),
    fechaNacimiento: document.getElementById("registro-fecha-nacimiento").value,
    direccion: document.getElementById("registro-direccion").value.trim(),
    comuna: document.getElementById("registro-comuna").value.trim(),
    provincia: document.getElementById("registro-provincia").value.trim(),
    region: document.getElementById("registro-region").value.trim(),
    email: document.getElementById("registro-email").value.trim(),
    telefono: document.getElementById("registro-telefono").value.trim(),
    sexo: (document.querySelector('input[name="sexo"]:checked') || {}).value || "",
    password: document.getElementById("registro-password").value,
  };

  // Validaciones
  const resultadoRUN = validarRUN(datos.run);
  if (!resultadoRUN.valido) return mostrarErrorRegistro(errorEl, resultadoRUN.mensaje);
  if (!datos.nombreCompleto) return mostrarErrorRegistro(errorEl, "El nombre completo es obligatorio.");
  if (!datos.fechaNacimiento) return mostrarErrorRegistro(errorEl, "La fecha de nacimiento es obligatoria.");
  if (!datos.direccion || !datos.comuna || !datos.provincia || !datos.region)
    return mostrarErrorRegistro(errorEl, "Completa dirección, comuna, provincia y región.");
  if (!validarEmail(datos.email)) return mostrarErrorRegistro(errorEl, "Ingresa un correo electrónico válido.");
  if (!datos.telefono) return mostrarErrorRegistro(errorEl, "El teléfono es obligatorio.");
  if (!datos.sexo) return mostrarErrorRegistro(errorEl, "Selecciona una opción de sexo.");
  if (!datos.password || datos.password.length < 6)
    return mostrarErrorRegistro(errorEl, "La contraseña debe tener al menos 6 caracteres.");
  if (STATE.usuarios.some((u) => u.email === datos.email))
    return mostrarErrorRegistro(errorEl, "Ya existe una cuenta con ese correo.");

  datos.run = formatearRUN(datos.run);
  STATE.usuarios.push(datos);
  guardarEnStorage(LS_KEYS.usuarios, STATE.usuarios);

  iniciarSesion(datos);
  cerrarModal("modal-auth");
  mostrarToast(`¡Bienvenido/a, ${datos.nombreCompleto}!`);
}

function mostrarErrorRegistro(errorEl, mensaje) {
  errorEl.textContent = mensaje;
  errorEl.classList.remove("oculto");
}

function iniciarSesion(usuario) {
  STATE.usuarioActual = usuario;
  guardarEnStorage(LS_KEYS.sesion, usuario.email);
  actualizarBotonSesion();
}

function cerrarSesion() {
  STATE.usuarioActual = null;
  localStorage.removeItem(LS_KEYS.sesion);
  actualizarBotonSesion();
  mostrarToast("Sesión cerrada.");
}

function actualizarBotonSesion() {
  const btn = document.getElementById("btn-cuenta");
  if (!btn) return;
  if (STATE.usuarioActual) {
    const nombre = STATE.usuarioActual.nombreCompleto || STATE.usuarioActual.email;
    btn.textContent = `👤 ${nombre.split(" ")[0]}`;
    btn.dataset.sesionActiva = "true";
  } else {
    btn.textContent = "Mi cuenta";
    btn.dataset.sesionActiva = "false";
  }
}

/* ---------- 6. Panel Administrador ---------- */

function renderAdminDashboard() {
  const cont = document.getElementById("admin-dashboard-stats");
  if (!cont) return;
  cont.innerHTML = `
    <div class="stat-card">
      <span class="stat-card__valor">${DB_PRODUCTOS.length}</span>
      <span class="stat-card__etiqueta">Productos activos</span>
    </div>
    <div class="stat-card">
      <span class="stat-card__valor">${DB_ADMIN_CLIENTES.length}</span>
      <span class="stat-card__etiqueta">Clientes registrados</span>
    </div>
    <div class="stat-card">
      <span class="stat-card__valor">${DB_REPORTE_VENTAS.cantidadPedidos}</span>
      <span class="stat-card__etiqueta">Pedidos del período</span>
    </div>
    <div class="stat-card">
      <span class="stat-card__valor">${formatCLP(DB_REPORTE_VENTAS.totalVentas)}</span>
      <span class="stat-card__etiqueta">Ventas del período</span>
    </div>
  `;
}

function renderAdminProductos() {
  const cont = document.getElementById("admin-tabla-productos");
  if (!cont) return;
  cont.innerHTML = `
    <table class="tabla-admin">
      <thead><tr><th>Producto</th><th>Categoría</th><th>Precio</th></tr></thead>
      <tbody>
        ${DB_PRODUCTOS.map(
          (p) => `<tr><td>${p.nombre}</td><td>${p.categoria}</td><td>${formatCLP(p.precio)}</td></tr>`
        ).join("")}
      </tbody>
    </table>`;
}

function renderAdminClientes() {
  const cont = document.getElementById("admin-tabla-clientes");
  if (!cont) return;
  cont.innerHTML = `
    <table class="tabla-admin">
      <thead><tr><th>Nombre</th><th>Correo</th><th>N° Pedidos</th></tr></thead>
      <tbody>
        ${DB_ADMIN_CLIENTES.map(
          (c) => `<tr><td>${c.nombre}</td><td>${c.email}</td><td>${c.pedidos}</td></tr>`
        ).join("")}
      </tbody>
    </table>`;
}

function renderAdminReporte() {
  const cont = document.getElementById("admin-reporte-ventas");
  if (!cont) return;
  cont.innerHTML = `
    <p class="texto-muted">Período: ${DB_REPORTE_VENTAS.periodo}</p>
    <p class="reporte-total">${formatCLP(DB_REPORTE_VENTAS.totalVentas)}</p>
    <div class="reporte-detalle">
      <span>Pedidos: <strong>${DB_REPORTE_VENTAS.cantidadPedidos}</strong></span>
      <span>Ticket promedio: <strong>${formatCLP(DB_REPORTE_VENTAS.ticketPromedio)}</strong></span>
    </div>
  `;
}

function renderAdminDespacho() {
  const cont = document.getElementById("admin-tabla-despacho");
  if (!cont) return;
  cont.innerHTML = `
    <table class="tabla-admin">
      <thead><tr><th>Cliente</th><th>Dirección</th><th>Estado</th></tr></thead>
      <tbody>
        ${DB_ADMIN_DESPACHOS.map(
          (d) => `<tr><td>${d.cliente}</td><td>${d.direccion}</td><td><span class="badge-estado">${d.estado}</span></td></tr>`
        ).join("")}
      </tbody>
    </table>`;
}

function inicializarAdmin() {
  renderAdminDashboard();
  renderAdminProductos();
  renderAdminClientes();
  renderAdminReporte();
  renderAdminDespacho();

  document.querySelectorAll("[data-admin-tab]").forEach((tab) =>
    tab.addEventListener("click", () => {
      document.querySelectorAll("[data-admin-tab]").forEach((t) => t.classList.remove("admin-tab--activa"));
      tab.classList.add("admin-tab--activa");
      document.querySelectorAll(".admin-seccion").forEach((s) => s.classList.add("oculto"));
      document.getElementById(`admin-${tab.dataset.adminTab}`).classList.remove("oculto");
    })
  );

  const btnExportar = document.getElementById("btn-exportar-pdf");
  if (btnExportar) {
    btnExportar.addEventListener("click", () => {
      // Acción simulada: la generación real de PDF con datos reales
      // corresponde a la entrega de backend.
      mostrarToast("Reporte exportado (acción simulada — backend pendiente).");
    });
  }
}

// =====================================================================
// --- EVENT LISTENERS E INICIALIZACIÓN DE FUNCIONALIDADES ---
// =====================================================================
// Todos estos botones/formularios pertenecen a features de este archivo,
// por eso su cableado vive aquí y no en app-core.js.

function inicializarEventosFeature() {
  // Botón "Mi cuenta" (requiere iniciarSesion/cerrarSesion, definidas arriba)
  document.getElementById("btn-cuenta").addEventListener("click", () => {
    if (STATE.usuarioActual) {
      cerrarSesion();
    } else {
      abrirModal("modal-auth");
    }
  });

  // Configurador
  document.getElementById("btn-agregar-bowl").addEventListener("click", agregarBowlAlCarrito);

  // Carrito / checkout
  document.getElementById("btn-anular-carrito").addEventListener("click", anularCarrito);
  document.getElementById("btn-confirmar-pago").addEventListener("click", confirmarPago);
  document.getElementById("btn-agregar-otro-producto").addEventListener("click", () => {
    cerrarModal("modal-carrito");
    window.location.hash = "#menu";
  });
  document.getElementById("sugerencias-anterior").addEventListener("click", () => {
    STATE.indiceSugerencia -= 1;
    renderSugerencias();
  });
  document.getElementById("sugerencias-siguiente").addEventListener("click", () => {
    STATE.indiceSugerencia += 1;
    renderSugerencias();
  });

  // Anulación de pedido (CU7)
  document.getElementById("form-anulacion-pedido").addEventListener("submit", confirmarAnulacionPedido);
  document.getElementById("btn-cancelar-anulacion").addEventListener("click", () => {
    document.getElementById("form-anulacion-pedido").classList.add("oculto");
    pedidoEnProcesoDeAnulacion = null;
  });
}

function initFeatures() {
  inicializarConfigurador();
  inicializarFiltrosMenu();
  renderMenu();
  renderEspeciales();
  inicializarAuth();
  inicializarAdmin();
  inicializarEventosFeature();

  actualizarContadorCarrito();
  actualizarBotonSesion();
}

document.addEventListener("DOMContentLoaded", initFeatures);
