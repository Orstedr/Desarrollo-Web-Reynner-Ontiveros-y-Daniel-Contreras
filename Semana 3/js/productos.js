const respuestaProductos = {
    "status": 200,
    "message": "Productos obtenidos correctamente",
    "data": [
        {
            "id": 1,
            "nombre": "CHOCOLATE DE LECHE BEASTABLES",
            "descripcion": "Rico chocolate de leche creado con leche sin lactosa directamente de vacas felices",
            "precio": 10000,
            "img": "img/beastables.jpg",
            "stockInicial": 5
        },
        {
            "id": 2,
            "nombre": "CHOCOLATE NEGRO WILLY WONKA",
            "descripcion": "Exquisito chocolate que hará explotar tu mente a la segunda mordida",
            "precio": 5000,
            "img": "img/ChocolateWilly.jpg",
            "stockInicial": 5
        },
        {
            "id": 3,
            "nombre": "CHOCOLATE DE BROWNIE MILKA",
            "descripcion": "Sabroso chocolate de brownie con toques de sal y leche sin lactosa",
            "precio": 15000,
            "img": "img/Milka Chocolate.png",
            "stockInicial": 5
        },
        {
            "id": 4,
            "nombre": "CHOCOLATE DE ALMENDRAS SAHNE NUSS",
            "descripcion": "Delicioso chocolate de almendras sahne nuss traidas directamente de la india",
            "precio": 30000,
            "img": "img/Sahne nuss.png",
            "stockInicial": 5
        }
    ]
};


function stockDisponible(producto) {
    return producto.stockInicial - contarEnCarrito(producto.id);
}

//Agregar al carrito (valida stock antes de agregar)
function agregarAlCarrito(id, nombre, precio) {
    const producto = respuestaProductos.data.find((p) => p.id === id);

    if (producto && stockDisponible(producto) <= 0) {
        mostrarToast(`No quedan más unidades de "${nombre}"`);
        return;
    }

    carrito.push({ id: id, nombre: nombre, precio: precio });
    guardarCarrito();
    actualizarContadorCarrito();
    renderizarListaCarrito();
    cargarProductos(); // redibuja las cards para reflejar el nuevo stock
    mostrarToast(`"${nombre}" se agregó al carrito`);
}


//Render dinámico de productos
function cargarProductos() {
    const contenedor = document.getElementById("contenedorProductos");
    if (!contenedor) return;

    contenedor.innerHTML = ""; 

    respuestaProductos.data.forEach((producto) => {
        // col
        const col = document.createElement("div");
        col.className = "col-12 col-sm-6 col-md-4 col-lg-3";

        // card
        const card = document.createElement("div");
        card.className = "card h-100";

        // imagen
        const img = document.createElement("img");
        img.className = "card-img-top";
        img.src = producto.img;
        img.alt = producto.nombre;

        // body
        const body = document.createElement("div");
        body.className = "card-body d-flex flex-column";

        const titulo = document.createElement("h4");
        titulo.className = "card-title";
        titulo.innerText = producto.nombre;

        const desc = document.createElement("p");
        desc.className = "card-text";
        desc.innerText = producto.descripcion;

        const precio = document.createElement("h5");
        precio.className = "text-success";
        precio.innerText = `$${producto.precio.toLocaleString("es-CL")}`;

        const disponibles = stockDisponible(producto);

        const stockTexto = document.createElement("p");
        stockTexto.className = disponibles > 0 ? "small text-muted mb-1" : "small text-danger fw-bold mb-1";
        stockTexto.innerText = disponibles > 0 ? `Disponibles: ${disponibles}` : "Sin stock";

        const boton = document.createElement("button");
        boton.type = "button";
        boton.className = "btn btn-primary mt-auto";
        boton.disabled = disponibles <= 0;
        boton.innerText = disponibles > 0 ? "Añadir al carrito" : "Agotado";
        boton.onclick = function () {
            agregarAlCarrito(producto.id, producto.nombre, producto.precio);
        };

        body.appendChild(titulo);
        body.appendChild(desc);
        body.appendChild(precio);
        body.appendChild(stockTexto);
        body.appendChild(boton);

        card.appendChild(img);
        card.appendChild(body);
        col.appendChild(card);
        contenedor.appendChild(col);
    });
}


window.addEventListener("load", function () {
    cargarProductos();
});
