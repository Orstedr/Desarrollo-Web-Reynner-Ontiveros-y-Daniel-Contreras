<!DOCTYPE html>
<html lang="es">
    <head>
        <title>Primera pagina</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/css/bootstrap.min.css" rel="stylesheet">
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/js/bootstrap.bundle.min.js"></script>        
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css">
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
        <div class="container bg-warning">
            <div id="demo" class="carousel slide" data-bs-ride="carousel">
                <!-- Indicators/dots -->
                <div class="carousel-indicators">
                    <button type="button" data-bs-target="#demo" data-bs-slide-to="0" class="active"></button>
                    <button type="button" data-bs-target="#demo" data-bs-slide-to="1"></button>
                    <button type="button" data-bs-target="#demo" data-bs-slide-to="2"></button>
                </div>
                <!-- The slideshow/carousel -->
                <div class="carousel-inner">
                    <div class="carousel-item active">
                    <img src="img/Tienda.jpg" alt="Tienda Wonka" class="d-block w-100" style="height: 1000px; object-fit: cover;">
                    </div>
                    <div class="carousel-item">
                    <img src="img/CHOCO.jpg" alt="Chocolate" class="d-block w-100" style="height: 1000px; object-fit: cover;">
                    </div>
                    <div class="carousel-item">
                    <img src="img/Fabrica.jpg" alt="Fabrica" class="d-block w-100" style="height: 1000px; object-fit: cover;">
                    </div>
                    
                </div>
                <!-- Left and right controls/icons -->
                <button class="carousel-control-prev" type="button" data-bs-target="#demo" data-bs-slide="prev">
                    <span class="carousel-control-prev-icon"></span>
                </button>
                <button class="carousel-control-next" type="button" data-bs-target="#demo" data-bs-slide="next">
                    <span class="carousel-control-next-icon"></span>
                </button>
            </div>
        </div>
        <div class="container text-center mt-5 mb-5">
            <h1 class="display-4 fw-bold mb-4" style="color: #57060c;">
                Quiénes Somos
            </h1>
            
            <p class="lead mx-auto" style="max-width: 800px;">
                Somos amantes de la tradición y la calidad. Creemos que entregar el mejor chocolate del mundo va de la mano con una atención cálida y un excelente servicio de mesón. 
            </p>
            <p class="fs-5 text-muted mx-auto" style="max-width: 800px;">
                Nos esforzamos cada día para asegurar que cada persona que nos visita se lleve no solo un producto excepcional, sino también una recomendación experta y una experiencia inolvidable.
            </p>
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
                            <input type="email" class="form-control" id="email" placeholder="Enter email" name="email">
                        </div>
                        <div class="mb-3">
                            <label for="pwd" class="form-label">Password:</label>
                            <input type="password" class="form-control" id="pwd" placeholder="Enter password" name="pswd">
                        </div>
                        <div class="form-check mb-3">
                            <label class="form-check-label">
                            <input class="form-check-input" type="checkbox" name="remember"> Remember me
                            </label>
                        </div>
                        <button type="submit" class="btn btn-primary">Login</button>
                        </form>
                    </div>
                    <!-- Modal footer -->
                    <div class="modal-footer">
                        <button type="button" class="btn btn-danger" data-bs-dismiss="modal">Close</button>
                    </div>
                </div>
            </div>
        </div>  
    </body>
</html>