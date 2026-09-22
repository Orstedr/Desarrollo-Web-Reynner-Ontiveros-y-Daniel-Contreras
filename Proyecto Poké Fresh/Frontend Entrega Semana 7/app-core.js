// =====================================================================
// --- ESTADO GLOBAL (STATE) ---
// =====================================================================
// Único objeto que representa "lo que está pasando ahora" en la app.
// Se persiste parcialmente en localStorage (carrito, usuarios, pedidos)
// para simular continuidad sin backend real.

const STATE = {
  vista: "home", // "home" | "admin"  -> controla qué sección se muestra
  usuarioActual: null, // objeto usuario o null si no hay sesión
  usuarios: [], // usuarios "registrados" (simulados, en localStorage)
  carrito: [], // items del carrito: {id, nombre, precioUnitario, cantidad, tipo, detalle}
  bowlActual: {
    base: null,
    proteina: null,
    toppings: [], // array de ids (selección múltiple)
    salsa: null,
  },
  pedidosConfirmados: [], // pedidos ya pagados (para el módulo de anulación CU7)
  filtrosMenuActivos: new Set(["todos"]),
  indiceSugerencia: 0,
  contadorBoleta: 1000, // correlativo simulado de boletas
};

// Claves usadas en localStorage (persistencia local de esta etapa)
const LS_KEYS = {
  usuarios: "pokefresh_usuarios",
  carrito: "pokefresh_carrito",
  pedidos: "pokefresh_pedidos",
  sesion: "pokefresh_sesion",
  boleta: "pokefresh_correlativo_boleta",
};

// =====================================================================
// --- VALIDACIONES Y UTILIDADES ---
// =====================================================================

/**
 * Formatea un número como moneda CLP usando la API Intl del navegador.
 * Centraliza el formato de precios para que toda la UI se vea consistente.
 */
function formatCLP(numero) {
  return new Intl.NumberFormat("es-CL", {
    style: "currency",
    currency: "CLP",
    maximumFractionDigits: 0,
  }).format(numero);
}

/**
 * Valida un correo electrónico con una expresión regular estándar.
 */
function validarEmail(email) {
  const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return regex.test(String(email).trim());
}

/**
 * Valida un RUN chileno (formato + dígito verificador, algoritmo Módulo 11).
 * Acepta formatos como "12.345.678-5" o "123456785".
 * Retorna { valido: boolean, mensaje: string }
 */
function validarRUN(runInput) {
  if (!runInput) return { valido: false, mensaje: "El RUN es obligatorio." };

  // 1. Limpiar puntos y guion, dejar solo cuerpo + dígito verificador
  const runLimpio = String(runInput).replace(/\./g, "").replace(/-/g, "").trim().toUpperCase();

  if (!/^[0-9]{7,8}[0-9K]$/.test(runLimpio)) {
    return { valido: false, mensaje: "Formato de RUN inválido. Ej: 12345678-9" };
  }

  const cuerpo = runLimpio.slice(0, -1);
  const dv = runLimpio.slice(-1);

  // 2. Algoritmo Módulo 11
  let suma = 0;
  let multiplicador = 2;
  for (let i = cuerpo.length - 1; i >= 0; i--) {
    suma += parseInt(cuerpo[i], 10) * multiplicador;
    multiplicador = multiplicador === 7 ? 2 : multiplicador + 1;
  }
  const resto = 11 - (suma % 11);
  let dvEsperado;
  if (resto === 11) dvEsperado = "0";
  else if (resto === 10) dvEsperado = "K";
  else dvEsperado = String(resto);

  if (dvEsperado !== dv) {
    return { valido: false, mensaje: "El dígito verificador del RUN no es correcto." };
  }

  return { valido: true, mensaje: "RUN válido." };
}

/**
 * Formatea un RUN limpio (sin puntos ni guion) al formato "12.345.678-9"
 * solo para mostrarlo bonito en la UI (no se usa para validar).
 */
function formatearRUN(runInput) {
  const limpio = String(runInput).replace(/\./g, "").replace(/-/g, "").trim().toUpperCase();
  if (limpio.length < 2) return runInput;
  const cuerpo = limpio.slice(0, -1);
  const dv = limpio.slice(-1);
  const cuerpoFormateado = cuerpo.replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  return `${cuerpoFormateado}-${dv}`;
}

/**
 * Helpers genéricos de localStorage con manejo de errores.
 */
function guardarEnStorage(clave, valor) {
  try {
    localStorage.setItem(clave, JSON.stringify(valor));
  } catch (err) {
    console.warn("No se pudo guardar en localStorage:", err);
  }
}
function leerDeStorage(clave, valorPorDefecto) {
  try {
    const raw = localStorage.getItem(clave);
    return raw ? JSON.parse(raw) : valorPorDefecto;
  } catch (err) {
    console.warn("No se pudo leer de localStorage:", err);
    return valorPorDefecto;
  }
}

/**
 * Busca un objeto por id dentro de un arreglo del mock data.
 */
function buscarPorId(lista, id) {
  return lista.find((item) => item.id === id) || null;
}

// =====================================================================
// --- NAVEGACIÓN / RUTEO SIMPLE (#/ y #/admin) ---
// =====================================================================

function manejarRuta() {
  const hash = window.location.hash;
  const vistaHome = document.getElementById("vista-home");
  const vistaAdmin = document.getElementById("vista-admin");

  if (hash === "#/admin") {
    STATE.vista = "admin";
    vistaHome.classList.add("oculto");
    vistaAdmin.classList.remove("oculto");
  } else {
    STATE.vista = "home";
    vistaAdmin.classList.add("oculto");
    vistaHome.classList.remove("oculto");
  }
}

// =====================================================================
// --- MODALES GENÉRICOS ---
// =====================================================================
// Solo abren/cierran el modal. Cualquier lógica de "qué renderizar al
// abrir tal modal" vive en app-main.js y se engancha, con guardas
// typeof, desde inicializarEventosFeature() para no crear una
// dependencia dura de este archivo hacia el de funcionalidades.

function abrirModal(idModal) {
  const modal = document.getElementById(idModal);
  if (!modal) return;
  modal.classList.remove("oculto");
  document.body.classList.add("bloquear-scroll");
}

function cerrarModal(idModal) {
  const modal = document.getElementById(idModal);
  if (!modal) return;
  modal.classList.add("oculto");
  document.body.classList.remove("bloquear-scroll");
}

// =====================================================================
// --- TOASTS (avisos breves) ---
// =====================================================================

let toastTimeout = null;
function mostrarToast(mensaje, esError) {
  const toast = document.getElementById("toast");
  if (!toast) return;
  toast.textContent = mensaje;
  toast.classList.toggle("toast--error", Boolean(esError));
  toast.classList.remove("oculto");
  toast.classList.add("toast--visible");
  clearTimeout(toastTimeout);
  toastTimeout = setTimeout(() => {
    toast.classList.remove("toast--visible");
    setTimeout(() => toast.classList.add("oculto"), 200);
  }, 2600);
}

// =====================================================================
// --- MENÚ HAMBURGUESA (móvil) ---
// =====================================================================

function inicializarMenuMovil() {
  const btn = document.getElementById("btn-hamburguesa");
  const nav = document.getElementById("nav-principal");
  if (!btn || !nav) return;
  btn.addEventListener("click", () => {
    nav.classList.toggle("nav--abierta");
    btn.classList.toggle("hamburguesa--abierta");
  });
  nav.querySelectorAll("a").forEach((link) =>
    link.addEventListener("click", () => {
      nav.classList.remove("nav--abierta");
      btn.classList.remove("hamburguesa--abierta");
    })
  );
}

// =====================================================================
// --- CARGA DE ESTADO E INICIALIZACIÓN BASE ---
// =====================================================================

function cargarEstadoDesdeStorage() {
  STATE.usuarios = leerDeStorage(LS_KEYS.usuarios, []);
  STATE.carrito = leerDeStorage(LS_KEYS.carrito, []);
  STATE.pedidosConfirmados = leerDeStorage(LS_KEYS.pedidos, []);
  STATE.contadorBoleta = leerDeStorage(LS_KEYS.boleta, 1000);

  const emailSesion = leerDeStorage(LS_KEYS.sesion, null);
  if (emailSesion) {
    STATE.usuarioActual = STATE.usuarios.find((u) => u.email === emailSesion) || null;
  }
}

function inicializarEventosGlobales() {
  document.querySelectorAll("[data-abrir-modal]").forEach((btn) =>
    btn.addEventListener("click", () => {
      const idModal = btn.dataset.abrirModal;
      if (idModal === "modal-carrito") {
        if (typeof renderCarrito === "function") renderCarrito();
        if (typeof prellenarDireccionCarrito === "function") prellenarDireccionCarrito();
        if (typeof renderSugerencias === "function") renderSugerencias();
      }
      abrirModal(idModal);
    })
  );
  document.querySelectorAll("[data-cerrar-modal]").forEach((btn) =>
    btn.addEventListener("click", () => cerrarModal(btn.dataset.cerrarModal))
  );
  document.querySelectorAll(".modal-fondo").forEach((fondo) =>
    fondo.addEventListener("click", (e) => {
      if (e.target === fondo) cerrarModal(fondo.closest(".modal").id);
    })
  );
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      document.querySelectorAll(".modal:not(.oculto)").forEach((m) => cerrarModal(m.id));
    }
  });

  // Ruteo por hash (para el panel #/admin)
  window.addEventListener("hashchange", manejarRuta);
}

function init() {
  cargarEstadoDesdeStorage();
  inicializarMenuMovil();
  inicializarEventosGlobales();
  manejarRuta();
}

document.addEventListener("DOMContentLoaded", init);
