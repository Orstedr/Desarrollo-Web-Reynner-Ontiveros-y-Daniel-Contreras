<!DOCTYPE html>
<html lang="es">
    <head>
        <title>Productos</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/css/bootstrap.min.css" rel="stylesheet">
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/js/bootstrap.bundle.min.js"></script>        
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css">
        <script src="js/carrito.js" defer></script>
        <script src="js/productos.js" defer></script>
        <style>
            .bg-burdeo {
                background-color: #57060c;
                color:white;
                line-height: 2;
            }
            .bg-lineas a {
                color:white;
            }
            .btn-primary {
                background-color: #d4a31c;
                border-color: #d4a31c;
            }
            .bg-dorado {
                background-color: #E3AB46;
            }

            .bg-dorado a {
                color: white;
            }
            .container-fluid.bg-dark a {
                color: white;
        }
            #listaCarrito {
                right: 0;
                left: auto;
                max-width: calc(100vw - 24px);
                width: 280px;
                word-break: break-word;
            }
            .carrito-item {
                flex-wrap: wrap;
                gap: 6px;
            }
            @media (max-width: 420px) {
                #listaCarrito {
                    position: fixed !important;
                    top: 60px;
                    left: 12px;
                    right: 12px;
                    width: auto;
                }
            }
        </style>
    </head>
    <body>
        <!-- Navbar -->
        <nav class="navbar navbar-expand-sm bg-burdeo navbar-dark">
            <div class="container-fluid"> 
                <a class="navbar-brand" href="index.php"><img src="img/wonka.png" width="55"></a>
                <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#collapsibleNavbar">
                    <span class="navbar-toggler-icon"></span>
                </button>
                <div class="collapse navbar-collapse" id="collapsibleNavbar">
                    <ul class="navbar-nav">
                        <li class="nav-item dropdown">
                            <a class="nav-link dropdown-toggle" href="#" role="button" data-bs-toggle="dropdown">Empresa</a>
                            <ul class="dropdown-menu">
                                <li><a class="dropdown-item" href="empresa.php">Quienes Somos</a></li>
                                <li><a class="dropdown-item" href="#">Nuestro Equipo</a></li>
                                <li><a class="dropdown-item" href="#">Mision</a></li>
                            </ul>
                        </li>                        
                        <li class="nav-item">
                            <a class="nav-link" href="productos.php">Productos</a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link" href="servicios.php">Servicios</a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link" href="contacto.php">Contacto</a>
                        </li>                                                 
                    </ul>
                </div> 
                <div class="position-relative me-3">
                    <span class="text-white" style="cursor:pointer;" onclick="toggleCarrito();">
                        <i class="fa fa-shopping-cart"></i> <span id="carritoContador">0</span>
                    </span>
                    <div id="listaCarrito" class="dropdown-menu dropdown-menu-end p-3" style="display:none;"></div>
                </div>
                <button type="button" class="btn btn-primary" data-bs-toggle="modal" data-bs-target="#myModal">Acceder</button>               
            </div> 
        </nav>
        <!-- Container -->
        <div class="container bg-warning">
           
            <div class="container-fluid">
                <!-- Este contenedor se llena dinámicamente vía JS (onload) -->
                <div class="row g-4" id="contenedorProductos"></div>
            </div>
        </div>
        <!-- Footer -->   
        <div class="container-fluid bg-burdeo" >
            <div class="row">
                <div class="col-4"></div>
                <div class="col-4 text-center" style="color:#E3AB46"><strong>ChocoSneaky@gmail.com</strong></div>
                <div class="col-4"></div>
            </div>
        </div>
        <!-- Modal -->
         <div class="modal fade" id="myModal">
            <div class="modal-dialog">
                <div class="modal-content">
                    <!-- Modal Header -->
                    <div class="modal-header">
                        <h4 class="modal-title">Autenticación</h4>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <!-- Modal body -->
                    <div class="modal-body">
                        <form action="empresa.php">
                        <div class="mb-3 mt-3">
                            <label for="email" class="form-label">Email:</label>
                            <input type="email" class="form-control" id="email" placeholder="Ingresar correo" name="email">
                        </div>
                        <div class="mb-3">
                            <label for="pwd" class="form-label">Contraseña:</label>
                            <input type="password" class="form-control" id="pwd" placeholder="Ingresar contraseña" name="pswd">
                        </div>
                        <div class="form-check mb-3">
                            <label class="form-check-label">
                            <input class="form-check-input" type="checkbox" name="remember"> Recuerdame
                            </label>
                        </div>
                        <button type="button" class="btn btn-primary" onclick="validarLogin();">Iniciar sesión</button>
                        </form>
                    </div>
                    <!-- Modal footer -->
                    <div class="modal-footer">
                        <button type="button" class="btn btn-danger" data-bs-dismiss="modal">Cerrar</button>
                    </div>
                </div>
            </div>
        </div>    
    </body>
</html>