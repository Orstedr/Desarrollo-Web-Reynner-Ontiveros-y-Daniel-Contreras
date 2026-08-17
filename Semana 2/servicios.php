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
            color: white;
            line-height: 2;
            }

            .container-servicios {
            background-color: #000000;
            color: white;
            }

            .container-servicios a {
            color: white;
            }
            .texto-servicios {
            font-size: 14px;
            }
            .container-servicios {
            background-color: #000000;
            color: white;
            padding-top:5px;
            
            
            }
            .tarjeta-servicio {
            background-color: #57060c;
            color: white;
            border: 2px solid #E3AB46;
            padding: 20px;
            text-align: center;
            height: 100%;
            
            }

            .tarjeta-servicio h3 {
            color: #E3AB46;
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
            </div>
        </nav>       
        <!-- Container -->
        <div class="container-fluid container-servicios">
    
    <p style="padding-top: 5px;">
        En ChocoSneaky creemos que siempre hay un buen momento para disfrutar de un chocolate.
        Descubre nuestra variedad de sabores y productos, creados para compartir, disfrutar y hacerte feliz.
    </p>

    <div class="row mt-4">

        <div class="col-md-4 mb-3">
            <div class="tarjeta-servicio">
                <h3>🍫 Variedad</h3>
                <p>
                    Disfruta de una gran variedad de chocolates y sabores
                    pensados para todos los gustos.
                </p>
            </div>
        </div>

        <div class="col-md-4 mb-3">
            <div class="tarjeta-servicio">
                <h3>🎁 Regalos</h3>
                <p>
                    Encuentra el regalo perfecto para cumpleaños,
                    celebraciones y ocasiones especiales.
                </p>
            </div>
        </div>

        <div class="col-md-4 mb-3">
            <div class="tarjeta-servicio">
                <h3>❤️ Felicidad</h3>
                <p>
                    Creamos nuestros productos pensando en entregar
                    momentos dulces y hacer feliz a cada cliente.
                    
                </p>
            </div>
        </div>
        <!-- Footer -->   
        <div class="container-fluid bg-burdeo">
            <div class="row">
                <div class="col-4"></div>
                <div class="col-4 text-center" style="color:#E3AB46"><strong>ChocoSneaky@2026</strong></div>
                <div class="col-4"></div>
            </div>
        </div>
        <!-- Modal -->     
    </body>
</html>