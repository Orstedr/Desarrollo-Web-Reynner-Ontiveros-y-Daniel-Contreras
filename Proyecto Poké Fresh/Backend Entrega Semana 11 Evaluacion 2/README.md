# Poké Fresh · Backend local en Windows

Instala [Python 3.14](https://www.python.org/downloads/), [MongoDB Community 8.0](https://www.mongodb.com/try/download/community) y [Vault](https://developer.hashicorp.com/vault/install). La versión anterior del proyecto se comprobó en Windows con Python 3.14.9, MongoDB 8.3.8 y Vault 2.1.1. Descarga MongoDB y Vault como ZIP de Windows y extrae sus binarios. El iniciador ejecuta su propia instancia de MongoDB, por lo que el puerto 27017 debe estar libre.

## Arrancar

Abre PowerShell en la carpeta extraída que contiene `run.py`. Ajusta las dos rutas a tus binarios. Si `mongod.exe` y `vault.exe` ya están en PATH, omite esas dos líneas.

```powershell
$env:MONGOD_EXE = 'C:\Herramientas\mongodb\bin\mongod.exe'
$env:VAULT_EXE = 'C:\Herramientas\vault\vault.exe'
python --version  # Debe indicar Python 3.14.x
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe run.py
```

En el primer arranque, escribe una clave ficticia de 12 a 128 caracteres cuando se solicite. Puedes usar `ADMIN_PASSWORD` como variable de entorno para iniciar sin ese diálogo. Deja abierta la terminal y, desde otra ventana de PowerShell, comprueba la salud.

```powershell
curl.exe -i http://127.0.0.1:8000/health
```

Cuando responda `200` y `status: ok`, abre [Swagger](http://127.0.0.1:8000/docs). Si el navegador no carga los recursos de Swagger, usa `curl.exe` o Postman con los contratos del informe.

1. Inicia sesión en `POST /auth/login` con `admin@pokefresh.test` y tu clave. Pega `access_token` en **Authorize**. La sesión dura 15 minutos.
2. Crea cuentas ficticias con los roles `cajero`, `despacho` y `dueno` en `POST /api/v1/admin/users`.
3. Registra un cliente ficticio. Como admin, lee el código local en `GET /api/v1/admin/mail/{recipient_id}`, canjéalo mediante `POST /auth/verify` e inicia sesión como cliente.
4. Consulta `GET /api/v1/delivery/zones` y cotiza con `POST /api/v1/orders/quote`. Para crear un pedido, envía una cabecera `Idempotency-Key` de 8 a 64 caracteres, nueva por compra.

## Datos y detención

El iniciador configura MongoDB como réplica local de un miembro (`pf`), conserva datos en `.local/mongo` y registra su arranque en `.local/mongo.log`. Vault opera en memoria, en modo dev, y recibe claves nuevas al arrancar. Gateway, servicios privados, MongoDB y Vault escuchan exclusivamente en loopback. Las rutas privadas también exigen credenciales internas. Usa únicamente datos ficticios.

La carga inicial se ejecuta al arrancar. Con el backend en ejecución, puedes repetirla desde otra terminal con `.\.venv\Scripts\python.exe run.py seed`. Conserva los registros existentes y la clave del administrador. El origen de despacho se configura con `ORIGIN_LAT` y `ORIGIN_LON` antes de arrancar. Las dos direcciones de cobertura, el correo, el pago y la boleta son de laboratorio.

Presiona **Ctrl+C** en la primera terminal para cerrar los procesos. Vuelve a ejecutar `.\.venv\Scripts\python.exe run.py` para iniciarlos de nuevo.


## Propiedad de datos y reintentos

Los procesos comparten MongoDB, con escrituras separadas por dominio en el código. Inventory
escribe catálogo y reservas. Orders escribe pedidos. Payments escribe intentos, ventas, boletas
y avisos de venta. Auth administra identidad, sesiones y códigos de cuenta. Clients administra
actualizaciones del perfil y delega el registro de identidad y la activación a Auth. Para datos
anteriores, Clients usa el perfil inicial guardado en la cuenta si aún no hay un perfil actualizado.
La bandeja administrativa combina avisos de cuenta, avisos históricos y avisos de venta.

- Checkout: Orders guarda un registro provisional por cliente y clave antes de pedir la reserva.
  Inventory registra por ID de pedido el descuento y el importe dentro de su transacción. Si una
  dependencia falla, repite el mismo cuerpo con la misma clave. Un checkout en curso se omite
  del listado hasta que Orders complete el alta. Un rechazo de inventario puede reintentarse
  con el mismo cuerpo si se repone el stock.
- Confirmación: Orders registra que la referencia está en confirmación. Payments guarda la
  venta, boleta y aviso juntos y luego pide a Orders que marque el pedido como pagado. Si se
  interrumpe el flujo, el cajero puede repetir la misma referencia. Durante una confirmación
  pendiente, Orders bloquea la anulación.
- Anulación: Orders registra el primer motivo y bloquea el despacho. Payments cierra el pago
  e Inventory libera la reserva con operaciones repetibles. Orders marca el pedido como
  anulado al finalizar. Si una dependencia falla, repite la anulación del mismo pedido.

Los pasos entre procesos pueden quedar pendientes hasta un reintento del solicitante. Se
mantienen los contratos públicos y se agregan operaciones privadas limitadas al servicio
llamante con secretos por tramo. La separación de escrituras está aplicada por los procesos
de aplicación. La instancia MongoDB de laboratorio conserva la configuración local del README.

## Pruebas reproducibles

Con el backend activo, abre otra terminal en la carpeta de `run.py`. Usa una base de
laboratorio con el catálogo inicial y al menos una unidad disponible de `prod-001`.

```powershell
.\.venv\Scripts\python.exe pruebas.py
```

La prueba comprueba la salud del Gateway y los seis servicios, el catálogo, las opciones
del bowl, una cotización válida y el rechazo de una cotización sin ítems. Cada verificación
muestra `OK`; si hay un fallo, el script informa el motivo y devuelve código de salida 1.

Para comprobar también la sesión, la creación y el reintento del pedido, y la consulta
GraphQL, usa un cliente ficticio ya registrado y verificado según los pasos de arranque.

```powershell
.\.venv\Scripts\python.exe pruebas.py --cliente cliente@example.test
```

El script solicita la clave sin mostrarla. Crea un pedido de prueba, verifica que el
reintento devuelva el mismo ID y luego lo anula. El pedido anulado queda en el historial.
Ejecuta este modo únicamente con datos ficticios.
