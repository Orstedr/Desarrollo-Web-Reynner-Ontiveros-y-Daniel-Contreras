// Carrito
let carrito = [];

function guardarCarrito() {
    localStorage.setItem("carrito", JSON.stringify(carrito));
}

function cargarCarritoGuardado() {
    const guardado = localStorage.getItem("carrito");
    carrito = guardado ? JSON.parse(guardado) : [];
}

function actualizarContadorCarrito() {
    const contador = document.getElementById("carritoContador");
    if (!contador) return; 
    contador.innerText = carrito.length;
}

function contarEnCarrito(id) {
    return carrito.filter((item) => item.id === id).length;
}

// Dropdown que muestra los productos del carrito

function toggleCarrito() {
    const lista = document.getElementById("listaCarrito");
    if (!lista) return;
    const abierto = lista.style.display === "block";
    lista.style.display = abierto ? "none" : "block";
    if (!abierto) renderizarListaCarrito();
}

function renderizarListaCarrito() {
    const lista = document.getElementById("listaCarrito");
    if (!lista) return;

    lista.innerHTML = ""; // limpiar antes de redibujar

    if (carrito.length === 0) {
        const vacio = document.createElement("p");
        vacio.className = "mb-0 text-muted small";
        vacio.innerText = "Tu carrito está vacío";
        lista.appendChild(vacio);
        return;
    }

    let total = 0;
    carrito.forEach((producto, index) => {
        total += producto.precio;

        const item = document.createElement("div");
        item.className = "carrito-item d-flex justify-content-between align-items-start mb-2";

        const texto = document.createElement("span");
        texto.className = "small";
        texto.innerText = `${producto.nombre} - $${producto.precio.toLocaleString("es-CL")}`;

        const btnQuitar = document.createElement("button");
        btnQuitar.type = "button";
        btnQuitar.className = "btn btn-sm btn-outline-danger ms-2";
        btnQuitar.innerText = "x";
        btnQuitar.onclick = function () {
            quitarDelCarrito(index);
        };

        item.appendChild(texto);
        item.appendChild(btnQuitar);
        lista.appendChild(item);
    });

    const totalDiv = document.createElement("div");
    totalDiv.className = "border-top mt-2 pt-2 fw-bold small";
    totalDiv.innerText = `Total: $${total.toLocaleString("es-CL")}`;
    lista.appendChild(totalDiv);
}

function quitarDelCarrito(index) {
    carrito.splice(index, 1);
    guardarCarrito();
    actualizarContadorCarrito();
    renderizarListaCarrito();

    if (typeof cargarProductos === "function") {
        cargarProductos();
    }
}

function mostrarToast(mensaje) {
    const toast = document.createElement("div");
    toast.innerText = mensaje;
    toast.style.position = "fixed";
    toast.style.bottom = "20px";
    toast.style.right = "20px";
    toast.style.backgroundColor = "#57060c";
    toast.style.color = "white";
    toast.style.padding = "10px 16px";
    toast.style.borderRadius = "6px";
    toast.style.zIndex = "9999";
    document.body.appendChild(toast);

    setTimeout(() => {
        toast.remove();
    }, 2000);
}

// Validación del formulario de login del modal

function limpiarError(inputId) {
    const existente = document.getElementById(`error-${inputId}`);
    if (existente) existente.remove();
}

function mostrarError(inputId, mensaje) {
    limpiarError(inputId);
    const input = document.getElementById(inputId);
    const error = document.createElement("div");
    error.id = `error-${inputId}`;
    error.style.color = "#ffb3b3";
    error.style.fontSize = "0.85em";
    error.innerText = mensaje;
    input.insertAdjacentElement("afterend", error);
}

function validarLogin() {
    const email = document.getElementById("email");
    const pwd = document.getElementById("pwd");
    let esValido = true;

    limpiarError("email");
    limpiarError("pwd");

    // Validación simple de formato de correo
    const regexEmail = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!regexEmail.test(email.value)) {
        mostrarError("email", "Ingresa un correo válido");
        esValido = false;
    }

    if (pwd.value.length < 4) {
        mostrarError("pwd", "La contraseña debe tener al menos 4 caracteres");
        esValido = false;
    }

    if (esValido) {
        mostrarToast("Inicio de sesión correcto");
    }

    // Evita que el form recargue la página
    return false;
}

window.addEventListener("load", function () {
    cargarCarritoGuardado();
    actualizarContadorCarrito();
});
