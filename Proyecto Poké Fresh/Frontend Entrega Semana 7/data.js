// =====================================================================
// data.js
// --- BASE DE DATOS LOCAL / DATOS SIMULADOS ---
// -----------------------------------------------------------------------
// Este archivo es el ÚNICO punto de "datos" del sistema en esta etapa.
// Todo lo que aquí aparece son valores de EJEMPLO (mock data) pensados
// para ser reemplazados, en la entrega de backend, por llamadas fetch()
// a una API real (ej: fetch('/api/productos')) SIN tener que tocar la
// lógica de renderizado ni de cálculo en app.js.
//
// Regla de oro del proyecto: ningún precio se escribe "a mano" dentro
// de una función de cálculo. Todo cálculo de totales debe LEER el
// precio desde alguno de los objetos definidos aquí.
// =====================================================================

// ---------------------------------------------------------------------
// 1. CONFIGURADOR "ARMA TU BOWL"
// ---------------------------------------------------------------------
// Cada opción tiene id, nombre, precio (CLP) e ícono (emoji, para no
// depender de librerías de íconos externas). El precio base del bowl
// vive aparte, en CONFIG_BASE.

const DB_BASES = [
  { id: "arroz", nombre: "Arroz blanco", precio: 0, icono: "🍚" },
  { id: "arroz-integral", nombre: "Arroz integral", precio: 300, icono: "🍙" },
  { id: "hojas-verdes", nombre: "Mix de hojas verdes", precio: 300, icono: "🥬" },
  { id: "fideos-soba", nombre: "Fideos soba", precio: 500, icono: "🍜" },
];

const DB_PROTEINAS = [
  { id: "salmon", nombre: "Salmón", precio: 2200, icono: "🐟" },
  { id: "atun", nombre: "Atún", precio: 2000, icono: "🐠" },
  { id: "pollo-teriyaki", nombre: "Pollo teriyaki", precio: 1600, icono: "🍗" },
  { id: "tofu", nombre: "Tofu", precio: 1200, icono: "🧈" },
];

const DB_TOPPINGS = [
  { id: "mango", nombre: "Mango", precio: 500, icono: "🥭" },
  { id: "palta", nombre: "Palta", precio: 600, icono: "🥑" },
  { id: "edamame", nombre: "Edamame", precio: 500, icono: "🫛" },
  { id: "alga-wakame", nombre: "Alga wakame", precio: 500, icono: "🌿" },
  { id: "cebolla-crocante", nombre: "Cebolla crocante", precio: 400, icono: "🧅" },
  { id: "sesamo", nombre: "Sésamo", precio: 300, icono: "✨" },
  { id: "ninguno", nombre: "Ninguno", precio: 0, icono: "🚫" },
];

const DB_SALSAS = [
  { id: "soya", nombre: "Soya", precio: 0, icono: "🟤" },
  { id: "spicy-mayo", nombre: "Spicy mayo", precio: 300, icono: "🌶️" },
  { id: "ponzu", nombre: "Ponzu", precio: 300, icono: "🍋" },
  { id: "anguila", nombre: "Anguila", precio: 400, icono: "🍯" },
];

// Precio base del bowl personalizado (antes de sumar extras).
// Se lee desde acá y nunca queda "hardcodeado" en app.js.
const CONFIG_BASE = {
  precioBase: 4990,
  moneda: "CLP",
};

// ---------------------------------------------------------------------
// 2. CATÁLOGO "MENÚ" (productos prediseñados)
// ---------------------------------------------------------------------
const DB_PRODUCTOS = [
  {
    id: "prod-001",
    nombre: "Clásico Hawaiano",
    categoria: "clasicos",
    descripcion: "Arroz blanco, atún, mango, palta y salsa soya.",
    precio: 6990,
    imagenEmoji: "🍚",
  },
  {
    id: "prod-002",
    nombre: "Poke Tradicional",
    categoria: "clasicos",
    descripcion: "Arroz blanco, salmón, edamame, cebolla crocante y ponzu.",
    precio: 7490,
    imagenEmoji: "🍣",
  },
  {
    id: "prod-003",
    nombre: "Bowl Aloha",
    categoria: "clasicos",
    descripcion: "Arroz integral, pollo teriyaki, mango y sésamo.",
    precio: 6790,
    imagenEmoji: "🌺",
  },
  {
    id: "prod-004",
    nombre: "Salmón Power",
    categoria: "proteicos",
    descripcion: "Doble porción de salmón, palta, edamame y spicy mayo.",
    precio: 8990,
    imagenEmoji: "🐟",
  },
  {
    id: "prod-005",
    nombre: "Atún Fuerte",
    categoria: "proteicos",
    descripcion: "Doble porción de atún, alga wakame, sésamo y anguila.",
    precio: 8790,
    imagenEmoji: "🐠",
  },
  {
    id: "prod-006",
    nombre: "Pollo Teriyaki Extra",
    categoria: "proteicos",
    descripcion: "Doble porción de pollo teriyaki, mango, cebolla crocante y soya.",
    precio: 7990,
    imagenEmoji: "🍗",
  },
  {
    id: "prod-007",
    nombre: "Veggie Fresh",
    categoria: "veggie",
    descripcion: "Mix de hojas verdes, tofu, palta, edamame y ponzu.",
    precio: 6490,
    imagenEmoji: "🥗",
  },
  {
    id: "prod-008",
    nombre: "Tofu Crunch",
    categoria: "veggie",
    descripcion: "Fideos soba, tofu, cebolla crocante, sésamo y spicy mayo.",
    precio: 6690,
    imagenEmoji: "🥢",
  },
  {
    id: "prod-009",
    nombre: "Garden Bowl",
    categoria: "veggie",
    descripcion: "Arroz integral, tofu, mango, alga wakame y soya.",
    precio: 6390,
    imagenEmoji: "🌱",
  },
];

// ---------------------------------------------------------------------
// 3. "LO ESPECIAL DEL DÍA"
// ---------------------------------------------------------------------
const DB_ESPECIALES = [
  {
    id: "esp-001",
    titulo: "1er especial",
    nombre: "Salmón Sunset",
    descripcion: "Salmón, mango, palta y spicy mayo. Precio del día.",
    precio: 5990,
    precioNormal: 7490,
    imagenEmoji: "🌅",
  },
  {
    id: "esp-002",
    titulo: "2do especial",
    nombre: "Atún Explosivo",
    descripcion: "Atún, edamame, cebolla crocante y anguila.",
    precio: 5790,
    precioNormal: 7290,
    imagenEmoji: "💥",
  },
  {
    id: "esp-003",
    titulo: "3er especial",
    nombre: "Veggie del Día",
    descripcion: "Tofu, hojas verdes, alga wakame y ponzu.",
    precio: 4990,
    precioNormal: 6390,
    imagenEmoji: "🥬",
  },
];

// ---------------------------------------------------------------------
// 4. DESPACHO
// ---------------------------------------------------------------------
const CONFIG_DESPACHO = {
  comuna: "Puente Alto",
  radioGratuitoKm: 3,
  costoFueraDeRadio: 1990,
};

// ---------------------------------------------------------------------
// 5. PANEL ADMINISTRADOR — datos simulados de gestión
// ---------------------------------------------------------------------
const DB_ADMIN_CLIENTES = [
  { id: "cl-001", nombre: "Javiera Muñoz", email: "javiera.munoz@correo.cl", pedidos: 12 },
  { id: "cl-002", nombre: "Benjamín Rojas", email: "brojas@correo.cl", pedidos: 5 },
  { id: "cl-003", nombre: "Camila Soto", email: "camila.soto@correo.cl", pedidos: 20 },
  { id: "cl-004", nombre: "Matías Fuentes", email: "mfuentes@correo.cl", pedidos: 3 },
];

const DB_ADMIN_DESPACHOS = [
  { id: "desp-001", cliente: "Javiera Muñoz", direccion: "Av. Concha y Toro 1250, Puente Alto", estado: "En camino" },
  { id: "desp-002", cliente: "Benjamín Rojas", direccion: "Camino a Talagante 890, Puente Alto", estado: "Preparando" },
  { id: "desp-003", cliente: "Camila Soto", direccion: "Av. Gabriela Mistral 430, Puente Alto", estado: "Entregado" },
];

// Reporte de ventas simulado: el total del período se LEE desde acá,
// nunca se escribe un número fijo directamente en la vista.
const DB_REPORTE_VENTAS = {
  periodo: "Septiembre 2026",
  totalVentas: 4823400,
  cantidadPedidos: 318,
  ticketPromedio: 15168,
};

// ---------------------------------------------------------------------
// 6. EXPORT (para mantener el código organizado; en el navegador estos
//    objetos quedan disponibles como variables globales del script,
//    dado que el proyecto no usa un bundler ni módulos ES en esta etapa)
// ---------------------------------------------------------------------
