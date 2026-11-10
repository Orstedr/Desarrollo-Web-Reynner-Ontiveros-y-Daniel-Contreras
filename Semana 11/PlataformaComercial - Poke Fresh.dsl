workspace "Poké Fresh" "Arquitectura objetivo de Poké Fresh con integración prevista del frontend y el backend en localhost" {
    !identifiers hierarchical

    model {
        visitante = person "Visitante" "Consulta el catálogo, las opciones para armar un bowl y la cobertura de despacho."
        cliente = person "Cliente" "Gestiona su cuenta y sus pedidos e inicia el pago."
        admin = person "Administrador" "Gestiona usuarios, clientes, inventario y operaciones."
        cajero = person "Cajero" "Confirma pagos de laboratorio y consulta boletas."
        despacho = person "Personal de despacho" "Consulta pedidos habilitados para despacho y actualiza su estado."
        dueno = person "Dueño" "Gestiona inventario y consulta reportes de ventas."

        sistema = softwareSystem "Poké Fresh" "Catálogo de bowls, pedidos, pagos de laboratorio y despacho." {
            frontend = container "Frontend web de Poké Fresh" "Interfaz web de catálogo, armado de bowls, carrito, pedidos y administración. En la arquitectura objetivo consume la API de Poké Fresh a través del Gateway." "HTML, CSS y JavaScript" {
                tags "Frontend"
            }
            swagger = container "Swagger UI" "Interfaz de pruebas de FastAPI servida desde /docs y ejecutada en el navegador." "Swagger UI / OpenAPI" {
                tags "PruebasAPI"
            }
            apiGateway = container "API Gateway" "Publica la API y Swagger UI en /docs. Valida sesiones y roles de rutas protegidas y reenvía solicitudes." "Python / FastAPI" {
                tags "Gateway"
                entrada = component "Publicación de rutas" "gateway_app registra las rutas de los servicios expuestas a través del gateway y publica OpenAPI." "FastAPI"
                acceso = component "Control de acceso" "identify solicita introspección de sesión y ProxyRoute comprueba los roles permitidos." "main.py"
                proxy = component "Proxy de solicitudes" "ProxyRoute reenvía método, ruta, parámetros e identidad mediante el cliente HTTP interno." "main.py / common.py"
            }
            authService = container "Auth" "Gestiona identidad, credenciales, sesiones, activación y recuperación de cuentas." "Python / FastAPI" {
                api = component "Rutas de identidad" "Reciben login, introspección, cierre de sesión y operaciones de cuenta." "accounts.py / FastAPI"
                sesiones = component "Credenciales y sesiones" "Verifica credenciales y consulta la vigencia del token opaco." "accounts.py"
                cuentas = component "Gestión de cuentas" "Registra identidades, cambia el estado de las cuentas y emite códigos de activación o recuperación para la bandeja local." "accounts.py"
            }
            inventory = container "Inventory" "Publica catálogo y opciones para bowls. Gestiona disponibilidad, stock, cotizaciones y reservas." "Python / FastAPI"
            orders = container "Orders" "Gestiona cobertura, cotización, pedidos, anulación y despacho." "Python / FastAPI" {
                api = component "Rutas de pedidos y despacho" "Reciben cotizaciones, checkout, consultas, anulaciones y cambios de estado de despacho." "commerce.py / FastAPI"
                acceso = component "Acceso a pedidos" "order_access verifica titularidad y estados visibles según el rol." "commerce.py"
                checkout = component "Alta idempotente del pedido" "create_order identifica reintentos por cliente y clave, guarda el pedido provisional y lo completa tras la reserva." "commerce.py"
                operaciones = component "Operaciones de pedidos" "Coordina cotizaciones, anulaciones, confirmación de pago y cambios de estado de despacho." "commerce.py"
            }
            clients = container "Clients" "Gestiona perfiles de clientes, expone contactos para boletas y permite consultar la bandeja local." "Python / FastAPI"
            payments = container "Payments" "Gestiona pagos de laboratorio, ventas, boletas PDF, avisos y reportes." "Python / FastAPI"
            graphqlGateway = container "Servicio GraphQL" "Consulta un pedido y, cuando se solicita y el rol lo permite, sus datos de pago." "Python / FastAPI / graphql-core" {
                api = component "Endpoint GraphQL" "execute recibe POST /api/v1/graphql y devuelve los datos y errores de la operación." "graph.py / FastAPI"
                validacion = component "Validación de consultas" "Aplica límites de tamaño, tokens, profundidad y campos. Comprueba el esquema permitido." "graph.py / graphql-core"
                resolvers = component "Resolvers de pedido y pago" "Consultan Orders y Payments con la identidad de la solicitud y restringen los campos pago y referencia según el rol." "graph.py / graphql-core"
            }
            mongo = container "Base de datos pokefresh" "Base compartida con colecciones por dominio para cuentas, sesiones, perfiles, catálogo, reservas, pedidos, pagos, ventas y avisos." "MongoDB / réplica local pf" {
                tags "BaseDatos"
            }
            vault = container "Vault" "Entrega a cada proceso sus secretos de comunicación interna durante el arranque. Opera en memoria en modo dev." "HashiCorp Vault / KV v2" {
                tags "Secretos"
            }
        }

        visitante -> sistema "Explora el menú y las opciones de compra"
        cliente -> sistema "Gestiona su cuenta y sus pedidos"
        admin -> sistema "Administra la operación"
        cajero -> sistema "Confirma pagos"
        despacho -> sistema "Gestiona el despacho"
        dueno -> sistema "Supervisa inventario y ventas"

        visitante -> sistema.frontend "Explora el menú y arma un bowl" "Navegador"
        cliente -> sistema.frontend "Arma su pedido, consulta su estado e inicia el pago" "Navegador"
        admin -> sistema.frontend "Gestiona la operación desde el panel de administración" "Navegador"

        cajero -> sistema.frontend "Confirma pagos y consulta boletas" "Navegador"
        despacho -> sistema.frontend "Consulta y actualiza el despacho" "Navegador"
        dueno -> sistema.frontend "Gestiona inventario y consulta ventas" "Navegador"

        sistema.frontend -> sistema.apiGateway "Consume la API de Poké Fresh (integración prevista)" "HTTP/JSON"
        sistema.frontend -> sistema.apiGateway.entrada "Invoca las rutas publicadas (integración prevista)" "HTTP/JSON"

        visitante -> sistema.swagger "Consulta catálogo, cobertura y cotizaciones" "Navegador"
        cliente -> sistema.swagger "Prueba cuenta, pedidos y pagos" "Navegador"
        admin -> sistema.swagger "Prueba operaciones de administración" "Navegador"
        cajero -> sistema.swagger "Prueba confirmación de pagos y consulta de boletas" "Navegador"
        despacho -> sistema.swagger "Prueba la consulta y actualización de despacho" "Navegador"
        dueno -> sistema.swagger "Prueba inventario y reportes de ventas" "Navegador"

        sistema.swagger -> sistema.apiGateway "Ejecuta operaciones de la API local" "HTTP"
        sistema.swagger -> sistema.apiGateway.entrada "Invoca las rutas publicadas" "HTTP"

        sistema.apiGateway -> sistema.authService "Reenvía operaciones de cuenta e introspecciona sesiones" "HTTP/JSON"
        sistema.apiGateway -> sistema.inventory "Reenvía consultas de catálogo y operaciones de inventario" "HTTP/JSON"
        sistema.apiGateway -> sistema.orders "Reenvía solicitudes de pedidos y despacho" "HTTP"
        sistema.apiGateway -> sistema.clients "Reenvía solicitudes de clientes y bandeja" "HTTP/JSON"
        sistema.apiGateway -> sistema.payments "Reenvía solicitudes de pagos, boletas y reportes" "HTTP"
        sistema.apiGateway -> sistema.graphqlGateway "Reenvía consultas con la identidad validada" "HTTP/GraphQL"

        sistema.clients -> sistema.authService "Delega registro y activación de identidades" "HTTP/JSON"
        sistema.clients -> sistema.orders "Consulta conteos de pedidos por cliente" "HTTP/JSON"
        sistema.orders -> sistema.clients "Consulta el perfil para el checkout" "HTTP/JSON"
        sistema.orders -> sistema.inventory "Cotiza, reserva y libera stock" "HTTP/JSON"
        sistema.orders -> sistema.payments "Anula el pago asociado al pedido" "HTTP/JSON"
        sistema.payments -> sistema.orders "Consulta el pedido y coordina la confirmación del pago" "HTTP/JSON"
        sistema.payments -> sistema.clients "Consulta el contacto para la boleta" "HTTP/JSON"
        sistema.graphqlGateway -> sistema.orders "Consulta el pedido visible para el solicitante" "HTTP/JSON"
        sistema.graphqlGateway -> sistema.payments "Consulta el pago cuando se solicita y el rol lo permite" "HTTP/JSON"

        sistema.authService -> sistema.mongo "Persiste identidades, sesiones y avisos de cuenta" "PyMongo"
        sistema.clients -> sistema.mongo "Gestiona perfiles y consulta avisos de la bandeja local" "PyMongo"
        sistema.inventory -> sistema.mongo "Gestiona catálogo y reservas" "PyMongo"
        sistema.orders -> sistema.mongo "Persiste pedidos y estados" "PyMongo"
        sistema.payments -> sistema.mongo "Persiste pagos, ventas, boletas y avisos" "PyMongo"

        sistema.apiGateway -> sistema.vault "Carga sus secretos al iniciar" "HTTP"
        sistema.authService -> sistema.vault "Carga sus secretos al iniciar" "HTTP"
        sistema.inventory -> sistema.vault "Carga sus secretos al iniciar" "HTTP"
        sistema.orders -> sistema.vault "Carga sus secretos al iniciar" "HTTP"
        sistema.clients -> sistema.vault "Carga sus secretos al iniciar" "HTTP"
        sistema.payments -> sistema.vault "Carga sus secretos al iniciar" "HTTP"
        sistema.graphqlGateway -> sistema.vault "Carga sus secretos al iniciar" "HTTP"

        sistema.apiGateway.entrada -> sistema.apiGateway.acceso "Aplica controles en rutas protegidas"
        sistema.apiGateway.entrada -> sistema.apiGateway.proxy "Procesa solicitudes de las rutas expuestas"
        sistema.apiGateway.acceso -> sistema.apiGateway.proxy "Entrega identidad validada para el reenvío"
        sistema.apiGateway.acceso -> sistema.authService "Introspecciona la sesión" "HTTP/JSON"
        sistema.apiGateway.proxy -> sistema.authService "Reenvía operaciones de identidad" "HTTP/JSON"
        sistema.apiGateway.proxy -> sistema.inventory "Reenvía operaciones de inventario" "HTTP/JSON"
        sistema.apiGateway.proxy -> sistema.orders "Reenvía operaciones de pedidos y despacho" "HTTP"
        sistema.apiGateway.proxy -> sistema.clients "Reenvía operaciones de clientes" "HTTP/JSON"
        sistema.apiGateway.proxy -> sistema.payments "Reenvía operaciones de pago y ventas" "HTTP"
        sistema.apiGateway.proxy -> sistema.graphqlGateway "Reenvía consultas GraphQL" "HTTP/GraphQL"

        sistema.authService.api -> sistema.authService.sesiones "Procesa login e introspección"
        sistema.authService.api -> sistema.authService.cuentas "Procesa operaciones de cuenta"
        sistema.authService.sesiones -> sistema.mongo "Consulta usuarios y gestiona sesiones" "PyMongo"
        sistema.authService.cuentas -> sistema.mongo "Actualiza cuentas y escribe avisos locales" "PyMongo"

        sistema.apiGateway -> sistema.orders.api "Reenvía el checkout" "HTTP/JSON"
        sistema.orders.api -> sistema.orders.acceso "Comprueba acceso a pedidos"
        sistema.orders.api -> sistema.orders.checkout "Ejecuta el alta del pedido"
        sistema.orders.api -> sistema.orders.operaciones "Ejecuta operaciones de pedidos y despacho"
        sistema.orders.checkout -> sistema.clients "Consulta el perfil de checkout" "HTTP/JSON"
        sistema.orders.checkout -> sistema.inventory "Reserva stock por identificador de pedido" "HTTP/JSON"
        sistema.orders.checkout -> sistema.mongo "Busca el pedido por clave y guarda su estado" "PyMongo"
        sistema.orders.operaciones -> sistema.mongo "Lee pedidos y guarda cambios de estado" "PyMongo"
        sistema.orders.operaciones -> sistema.inventory "Cotiza o libera una reserva" "HTTP/JSON"
        sistema.orders.operaciones -> sistema.payments "Cierra el intento de pago durante la anulación" "HTTP/JSON"

        sistema.apiGateway -> sistema.graphqlGateway.api "Reenvía el documento GraphQL" "HTTP/GraphQL"
        sistema.graphqlGateway.api -> sistema.graphqlGateway.validacion "Comprueba límites y esquema"
        sistema.graphqlGateway.api -> sistema.graphqlGateway.resolvers "Ejecuta la consulta validada"
        sistema.graphqlGateway.resolvers -> sistema.orders "Lee el pedido con la identidad de la solicitud" "HTTP/JSON"
        sistema.graphqlGateway.resolvers -> sistema.payments "Lee el pago si se pide y está autorizado" "HTTP/JSON"

        pruebas = deploymentEnvironment "Pruebas_Integradas" {
            deploymentNode "Equipo de pruebas local" "Ejecuta pruebas de integración entre servicios con datos ficticios." "Windows" {
                deploymentNode "Navegador" "Ejecuta Swagger UI para probar la API local." "Navegador web" {
                    containerInstance sistema.swagger
                }
                deploymentNode "Backend local" "Procesos Uvicorn iniciados por run.py y accesibles por loopback." "Python / Uvicorn" {
                    deploymentNode "Gateway :8000" "127.0.0.1:8000" "Uvicorn" {
                        containerInstance sistema.apiGateway
                    }
                    deploymentNode "Auth :8100" "127.0.0.1:8100" "Uvicorn" {
                        containerInstance sistema.authService
                    }
                    deploymentNode "Inventory :9000" "127.0.0.1:9000" "Uvicorn" {
                        containerInstance sistema.inventory
                    }
                    deploymentNode "Orders :9100" "127.0.0.1:9100" "Uvicorn" {
                        containerInstance sistema.orders
                    }
                    deploymentNode "Clients :9200" "127.0.0.1:9200" "Uvicorn" {
                        containerInstance sistema.clients
                    }
                    deploymentNode "Payments :9300" "127.0.0.1:9300" "Uvicorn" {
                        containerInstance sistema.payments
                    }
                    deploymentNode "GraphQL :9400" "127.0.0.1:9400" "Uvicorn" {
                        containerInstance sistema.graphqlGateway
                    }
                }
                deploymentNode "MongoDB :27017" "Réplica pf de un miembro con datos en .local/mongo." "mongod" {
                    containerInstance sistema.mongo
                }
                deploymentNode "Vault :8200" "Servicio de secretos local en modo dev." "Vault" {
                    containerInstance sistema.vault
                }
            }
        }

        local = deploymentEnvironment "Desarrollo_Local" {
            deploymentNode "Equipo local" "Despliegue local previsto para el frontend integrado y el backend." "Windows" {
                deploymentNode "Navegador" "Ejecuta el frontend de Poké Fresh y permite abrir Swagger UI para pruebas manuales." "Navegador web" {
                    containerInstance sistema.frontend
                    containerInstance sistema.swagger
                }
                deploymentNode "Backend local" "Procesos Uvicorn iniciados por run.py y accesibles por loopback." "Python / Uvicorn" {
                    deploymentNode "Gateway :8000" "127.0.0.1:8000" "Uvicorn" {
                        containerInstance sistema.apiGateway
                    }
                    deploymentNode "Auth :8100" "127.0.0.1:8100" "Uvicorn" {
                        containerInstance sistema.authService
                    }
                    deploymentNode "Inventory :9000" "127.0.0.1:9000" "Uvicorn" {
                        containerInstance sistema.inventory
                    }
                    deploymentNode "Orders :9100" "127.0.0.1:9100" "Uvicorn" {
                        containerInstance sistema.orders
                    }
                    deploymentNode "Clients :9200" "127.0.0.1:9200" "Uvicorn" {
                        containerInstance sistema.clients
                    }
                    deploymentNode "Payments :9300" "127.0.0.1:9300" "Uvicorn" {
                        containerInstance sistema.payments
                    }
                    deploymentNode "GraphQL :9400" "127.0.0.1:9400" "Uvicorn" {
                        containerInstance sistema.graphqlGateway
                    }
                }
                deploymentNode "MongoDB :27017" "Réplica pf de un miembro con datos en .local/mongo." "mongod" {
                    containerInstance sistema.mongo
                }
                deploymentNode "Vault :8200" "Servicio de secretos local en modo dev." "Vault" {
                    containerInstance sistema.vault
                }
            }
        }
    }

    views {
        systemContext sistema "C1_Contexto" {
            title "C1 - Contexto de Poké Fresh"
            include *
            autoLayout lr
        }
        container sistema "C2_Contenedores" {
            title "C2 - Contenedores de Poké Fresh"
            include *
            autoLayout lr
        }
        container sistema "C2_Catalogo" {
            title "C2 - Catálogo de Poké Fresh"
            include visitante sistema.frontend sistema.apiGateway sistema.inventory sistema.mongo
            autoLayout lr
        }
        container sistema "C2_Pedidos" {
            title "C2 - Pedidos de Poké Fresh"
            include cliente sistema.frontend sistema.apiGateway sistema.authService sistema.orders sistema.clients sistema.inventory sistema.payments sistema.mongo
            autoLayout lr
        }
        component sistema.apiGateway "C3_API_Gateway" {
            title "C3 - API Gateway"
            include *
            autoLayout lr
        }
        component sistema.authService "C3_Auth_Service" {
            title "C3 - Auth Service"
            include *
            autoLayout lr
        }
        component sistema.orders "C3_Orders" {
            title "C3 - orders"
            include *
            autoLayout lr
        }
        component sistema.graphqlGateway "C3_GraphQL" {
            title "C3 - GraphQL Gateway"
            include *
            autoLayout lr
        }

        dynamic sistema "D_F01_Exito" "Consulta pública de catálogo a través de la API local." {
            title "F01 - Consulta de catálogo: éxito"
            visitante -> sistema.frontend "Abre el catálogo de Poké Fresh"
            sistema.frontend -> sistema.apiGateway "GET /api/v1/catalog"
            sistema.apiGateway -> sistema.inventory "Reenvía la consulta pública"
            sistema.inventory -> sistema.mongo "Lee productos publicados y su disponibilidad"
            autoLayout lr
        }
        dynamic sistema "D_F01_Recuperacion" "La API informa la caída de Inventory y permite reintentar tras recuperarlo." {
            title "F01 - Fallo controlado y recuperación"
            visitante -> sistema.frontend "Abre el catálogo durante la indisponibilidad de Inventory"
            sistema.frontend -> sistema.apiGateway "GET /api/v1/catalog"
            sistema.apiGateway -> sistema.inventory "Intenta contactar Inventory y responde 503 si no está disponible"
            visitante -> sistema.frontend "Reintenta después de levantar Inventory"
            sistema.frontend -> sistema.apiGateway "Repite GET /api/v1/catalog"
            sistema.apiGateway -> sistema.inventory "Reenvía la consulta tras la recuperación"
            sistema.inventory -> sistema.mongo "Lee el catálogo para responder"
            autoLayout lr
        }
        dynamic sistema "D_F02_Exito" "Creación de un pedido y reserva de stock." {
            title "F02 - Registro de pedido: éxito"
            cliente -> sistema.frontend "Confirma el pedido desde el carrito"
            sistema.frontend -> sistema.apiGateway "POST /api/v1/orders con sesión y clave de idempotencia"
            sistema.apiGateway -> sistema.authService "POST /auth/introspect"
            sistema.authService -> sistema.mongo "Comprueba sesión e identidad"
            sistema.apiGateway -> sistema.orders "Reenvía la solicitud del cliente"
            sistema.orders -> sistema.clients "Consulta los datos del cliente para el checkout"
            sistema.orders -> sistema.mongo "Busca la clave y guarda el pedido provisional"
            sistema.orders -> sistema.inventory "Solicita la reserva por ID de pedido"
            sistema.inventory -> sistema.mongo "Registra la reserva y descuenta el stock en una transacción"
            sistema.orders -> sistema.mongo "Completa el alta con el importe calculado"
            autoLayout lr
        }
        dynamic sistema "D_F02_Reintento" "Repetición del checkout con la misma clave y el mismo cuerpo." {
            title "F02 - Reintento de pedido: sin duplicación"
            cliente -> sistema.frontend "Repite la operación de checkout"
            sistema.frontend -> sistema.apiGateway "POST /api/v1/orders con la misma Idempotency-Key"
            sistema.apiGateway -> sistema.authService "Introspecciona la sesión"
            sistema.apiGateway -> sistema.orders "Reenvía el checkout repetido"
            sistema.orders -> sistema.clients "Consulta el perfil del cliente"
            sistema.orders -> sistema.mongo "Recupera el pedido ya creado y devuelve su mismo identificador"
            autoLayout lr
        }
        dynamic sistema.orders "D_F02_Idempotencia_C3" "El mismo cuerpo y clave permiten recuperar un pedido ya creado." {
            title "F02 - Idempotencia: componentes internos"
            sistema.apiGateway -> sistema.orders.api "Reenvía el mismo checkout"
            sistema.orders.api -> sistema.orders.checkout "Procesa el reintento"
            sistema.orders.checkout -> sistema.clients "Consulta los datos del cliente"
            sistema.orders.checkout -> sistema.mongo "Encuentra el pedido completado y devuelve el registro existente"
            autoLayout lr
        }
        dynamic sistema "D_F03_Propio" "Consulta de un pedido propio desde el frontend." {
            title "F03 - Consulta protegida: pedido propio"
            cliente -> sistema.frontend "Abre la operación de consulta"
            sistema.frontend -> sistema.apiGateway "GET /api/v1/orders/{order_id}"
            sistema.apiGateway -> sistema.authService "Introspecciona la sesión"
            sistema.apiGateway -> sistema.orders "Reenvía la consulta con la identidad del cliente"
            sistema.orders -> sistema.mongo "Lee el pedido y confirma que pertenece al cliente antes de responder"
            autoLayout lr
        }
        dynamic sistema "D_F03_Ajeno" "Una sesión válida de cliente no da acceso a un pedido ajeno." {
            title "F03 - Consulta protegida: recurso ajeno"
            cliente -> sistema.frontend "Intenta consultar un pedido de otro cliente"
            sistema.frontend -> sistema.apiGateway "GET /api/v1/orders/{order_id} con sesión válida"
            sistema.apiGateway -> sistema.authService "Introspecciona la sesión"
            sistema.apiGateway -> sistema.orders "Reenvía la consulta con la identidad del cliente"
            sistema.orders -> sistema.mongo "Lee el pedido y comprueba su titularidad y responde 404 si pertenece a otro cliente"
            autoLayout lr
        }
        dynamic sistema "D_F03_Expirada" "El gateway rechaza el acceso cuando la sesión ha expirado." {
            title "F03 - Sesión expirada: rechazo temprano"
            cliente -> sistema.frontend "Abre un pedido con una sesión vencida"
            sistema.frontend -> sistema.apiGateway "Solicita un pedido con una sesión expirada"
            sistema.apiGateway -> sistema.authService "Introspecciona el token antes de reenviar"
            sistema.authService -> sistema.mongo "Verifica la vigencia del token. La sesión expirada provoca una respuesta 401"
            autoLayout lr
        }
        dynamic sistema "D_F04_GraphQL_Exito" "Consulta combinada de un pedido y su pago." {
            title "F04 - GraphQL: pedido y pago"
            cliente -> sistema.frontend "Abre el detalle de su pedido y su pago"
            sistema.frontend -> sistema.apiGateway "POST /api/v1/graphql solicitando el pedido propio y el estado de pago"
            sistema.apiGateway -> sistema.authService "Introspecciona la sesión"
            sistema.apiGateway -> sistema.graphqlGateway "Reenvía la consulta con identidad validada"
            sistema.graphqlGateway -> sistema.orders "Obtiene el pedido autorizado"
            sistema.graphqlGateway -> sistema.payments "Obtiene el estado de pago solicitado"
            autoLayout lr
        }
        dynamic sistema "D_F04_GraphQL_Parcial" "GraphQL entrega el pedido con el campo de pago nulo y un error si Payments falla." {
            title "F04 - GraphQL: dependencia fallida"
            cliente -> sistema.frontend "Solicita un pedido propio y su pago"
            sistema.frontend -> sistema.apiGateway "POST /api/v1/graphql"
            sistema.apiGateway -> sistema.authService "Introspecciona la sesión"
            sistema.apiGateway -> sistema.graphqlGateway "Reenvía la consulta con la identidad validada"
            sistema.graphqlGateway -> sistema.orders "Obtiene el pedido autorizado"
            sistema.graphqlGateway -> sistema.payments "No logra obtener el pago y añade el error a la respuesta GraphQL"
            autoLayout lr
        }
        dynamic sistema.graphqlGateway "D_F04_GraphQL_Limite_C3" "La validación rechaza consultas fuera de los límites antes de ejecutarlas." {
            title "F04 - GraphQL: consulta excede el límite"
            sistema.apiGateway -> sistema.graphqlGateway.api "Reenvía una consulta que excede la profundidad permitida"
        sistema.apiGateway -> sistema.graphqlGateway.api "Reenvía el documento GraphQL" "HTTP/GraphQL"
            sistema.graphqlGateway.api -> sistema.graphqlGateway.validacion "Comprueba la profundidad y rechaza la consulta con 400"
            autoLayout lr
        }
        dynamic sistema "D_Confirmacion_Pago" "El cajero confirma un pago de laboratorio y se registra la venta." {
            cajero -> sistema.frontend "Confirma el pago desde el panel de caja"
            sistema.frontend -> sistema.apiGateway "POST /api/v1/orders/{order_id}/payment/confirm"
            sistema.apiGateway -> sistema.authService "Introspecciona la sesión y aplica el rol cajero"
            sistema.apiGateway -> sistema.payments "Reenvía la confirmación"
            sistema.payments -> sistema.orders "Consulta el pedido y registra la confirmación en curso"
            sistema.payments -> sistema.mongo "Guarda la venta, la boleta y el aviso en una transacción"
            sistema.payments -> sistema.orders "Solicita marcar el pedido como pagado"
            sistema.orders -> sistema.mongo "Actualiza el estado del pedido"
            autoLayout lr
        }
        deployment sistema pruebas "DEP_Pruebas" "Pruebas integradas de la API y los servicios en localhost." {
            title "Despliegue - Pruebas integradas en localhost"
            include *
            autoLayout lr
        }
        deployment sistema local "DEP_Local" "Despliegue objetivo con el frontend integrado al API Gateway en localhost, sin Docker." {
            title "Despliegue - Desarrollo local"
            include *
            autoLayout lr
        }

        styles {
            element "Person" {
                shape person
                background #37665D
                color #FFFFFF
            }
            element "Software System" {
                background #24584D
                color #FFFFFF
            }
            element "Container" {
                background #DCEDE7
                color #183F36
            }
            element "Frontend" {
                shape webbrowser
            }
            element "PruebasAPI" {
                shape webbrowser
                background #E3ECF3
                color #23445A
            }
            element "Gateway" {
                background #285E53
                color #FFFFFF
            }
            element "BaseDatos" {
                shape cylinder
                background #E3ECF3
                color #23445A
            }
            element "Secretos" {
                background #EEE5F1
                color #4C3555
            }
            element "Component" {
                background #EAF3EF
                color #183F36
            }
            element "Deployment Node" {
                background #EEF3F1
                color #183F36
            }
        }
    }
}
