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
                <button type="button" class="btn btn-primary" data-bs-toggle="modal" data-bs-target="#myModal">Acceder</button>               
            </div>
        </nav>
        <!-- Container -->
        <div class="container-fluid bg-warning py-4">
            <form action="empresa.php">
                <div class="mb-3 mt-3">
                    <label for="email" class="form-label">Email:</label>
                    <input type="email" class="form-control" id="email" placeholder="Enter email" name="email">
                </div>
                <label for="comment">Comentarios:</label>
                <textarea class="form-control" rows="5" id="comment" name="text"></textarea>
                <button type="submit" class="btn btn-primary mt-1">Enviar</button>
            </form>
        </div>
        <!-- Footer -->   
        <div class="container-fluid bg-burdeo mt-auto py-3">
            <div class="row">
                <div class="col-12 text-center" style="color:#E3AB46">
                    <strong>ChocoSneaky@gmail.com | Telf: 809 999980 902</strong>
                </div>
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
                            <input type="email" class="form-control" id="email" placeholder="Ingrese email" name="email">
                        </div>
                        <div class="mb-3">
                            <label for="pwd" class="form-label">Contraseña:</label>
                            <input type="password" class="form-control" id="pwd" placeholder="Ingrese contraseña" name="pswd">
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