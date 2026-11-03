# Mensajería asíncrona con ActiveMQ y STOMP

Aplicación en Python que envía y recibe pedidos mediante la cola `/queue/pedidos` de Apache ActiveMQ Classic. Permite intercambiar mensajes en texto libre, ancho fijo, JSON y XML.

El productor envía los mensajes al broker. El consumidor los recibe, interpreta su formato y confirma su procesamiento mediante ACK. El productor puede enviar mensajes mientras el consumidor está detenido, siempre que ActiveMQ esté funcionando.

## Archivos

| Archivo | Función |
| --- | --- |
| `productor.py` | Construye el mensaje y lo envía a la cola. |
| `consumidor.py` | Escucha la cola, interpreta el mensaje y muestra su contenido. |

## Requisitos

- Windows y PowerShell.
- Miniconda o Anaconda con Conda disponible en la terminal.
- Python 3.11 dentro del entorno del proyecto.
- Apache ActiveMQ Classic y una versión de Java compatible con la versión de ActiveMQ instalada.
- Librería `stomp.py`.

`argparse`, `json`, `decimal`, `time` y `xml.etree.ElementTree` forman parte de Python y no requieren instalación adicional.

## 1. Preparar el entorno

Ejecutar en PowerShell o en la terminal de VS Code:

```powershell
conda create -n API_GATEWAY python=3.11 pip
conda activate API_GATEWAY
python -m pip install stomp.py
```

La creación del entorno y la instalación de la librería se realizan una sola vez. Si el entorno ya existe, basta con activarlo.

Comprobar los imports:

```powershell
python -c "import stomp, json; print('Entorno listo')"
```

## 2. Habilitar STOMP en ActiveMQ

Con ActiveMQ detenido, abrir `conf/activemq.xml` dentro de su carpeta de instalación. Dentro de `<transportConnectors>`, habilitar o agregar el siguiente conector, conservando los conectores existentes:

```xml
<transportConnector name="stomp" uri="stomp://127.0.0.1:61613?maximumConnections=1000&amp;wireFormat.maxFrameSize=10485760"/>
```

Si el conector STOMP está entre `<!--` y `-->`, quitar esos marcadores para habilitarlo. Mantener una sola definición STOMP en ese puerto.

Guardar el archivo. En PowerShell, abrir la carpeta `bin` de ActiveMQ e iniciar el broker:

```powershell
.\activemq.bat console
```

Confirmar que aparezca `Connector stomp started`. Dejar esta terminal abierta durante las pruebas. Los cambios de configuración requieren reiniciar ActiveMQ.

## 3. Iniciar el consumidor

En otra terminal, ubicarse en la carpeta que contiene los archivos Python:

```powershell
conda activate API_GATEWAY
python consumidor.py
```

Debe aparecer:

```text
Escuchando /queue/pedidos. Presiona Ctrl+C para salir.
```

Dejar el consumidor ejecutándose para recibir los mensajes.

## 4. Ejecutar el productor

Abrir una tercera terminal en la misma carpeta y activar el entorno:

```powershell
conda activate API_GATEWAY
```

Ejecutar los siguientes comandos uno por uno.

### Texto libre

```powershell
python productor.py --formato texto --mensaje "Hola mundo Stomp"
```

### Ancho fijo

```powershell
python productor.py --formato fijo --id 123 --cliente "Ernesto Vivanco" --monto 123.45
```

El registro contiene 36 caracteres: 6 para el identificador, 20 para el cliente y 10 para el monto. El identificador se completa con ceros a la izquierda, el cliente con espacios a la derecha y el monto con ceros a la izquierda y dos decimales.

### JSON

```powershell
python productor.py --formato json --id 456 --cliente "Maria Soto" --monto 2500.75
```

### XML

```powershell
python productor.py --formato xml --id 789 --cliente "Pedro Gonzalez" --monto 980.50
```

El productor debe mostrar `Mensaje enviado a /queue/pedidos`, seguido del formato y del contenido enviado. El consumidor debe mostrar `[RECIBIDO] formato=...` y el contenido interpretado. En JSON y XML, el monto se transporta como texto según la implementación.

## Parámetros de conexión

Los dos programas usan por defecto:

| Parámetro | Valor |
| --- | --- |
| Host | `127.0.0.1` |
| Puerto STOMP | `61613` |
| Usuario | `demo` |
| Clave | `demo123` |
| Cola | `/queue/pedidos` |

El usuario y la clave definidos en el código no crean una cuenta en ActiveMQ. Si el broker tiene autenticación habilitada, utilizar las credenciales configuradas allí. Por ejemplo:

```powershell
python consumidor.py --usuario USUARIO --clave CLAVE
python productor.py --formato texto --mensaje "Prueba de conexion" --usuario USUARIO --clave CLAVE
```

Reemplazar `USUARIO` y `CLAVE` por los valores del broker.

## Prueba de recepción posterior

1. Detener el consumidor con `Ctrl+C`, manteniendo ActiveMQ abierto.
2. Enviar un mensaje:

   ```powershell
   python productor.py --formato texto --mensaje "Mensaje pendiente de recepcion"
   ```

3. Iniciar nuevamente el consumidor:

   ```powershell
   python consumidor.py
   ```

4. Comprobar que reciba el mensaje pendiente. Para esta prueba, no dejar otros consumidores conectados a la misma cola, ya que podrían recibirlo ellos.

## Prueba de validación

```powershell
python productor.py --formato fijo --id ABC --cliente "Cliente Prueba" --monto 123.45
```

El productor debe rechazar el identificador porque el formato fijo admite hasta seis dígitos ASCII. Este intento no debe enviar un mensaje a la cola.

## Finalizar la ejecución

- El productor termina después de enviar el mensaje.
- Detener el consumidor con `Ctrl+C` en su terminal.
- Detener ActiveMQ con `Ctrl+C` en la terminal del broker.
- Opcionalmente, ejecutar `conda deactivate` para salir del entorno.

## Problemas frecuentes

| Problema | Revisión |
| --- | --- |
| `conda` no se reconoce | Inicializar PowerShell con `conda init powershell` desde Anaconda Prompt y reiniciar la terminal o VS Code. |
| `EnvironmentNameNotFound` | Crear el entorno `API_GATEWAY` antes de activarlo. |
| `ModuleNotFoundError: No module named 'stomp'` | Activar el entorno e instalar `stomp.py` con `python -m pip install stomp.py`. |
| Conexión rechazada en `127.0.0.1:61613` | Comprobar que ActiveMQ esté iniciado y el conector STOMP habilitado. El conector OpenWire en `61616` usa otro protocolo. |
| El consumidor no muestra `[RECIBIDO]` | Guardar los archivos, reiniciar el consumidor y enviar un mensaje nuevo. Verificar que ambos usan la misma cola y que `on_message` está definido al mismo nivel que los demás métodos de `Escuchador`. |
| `unrecognized arguments` | Revisar los nombres de los parámetros y usar dos guiones normales, por ejemplo `--mensaje`. |

## Referencia

- [Configuración de STOMP en Apache ActiveMQ Classic](https://activemq.apache.org/components/classic/documentation/stomp)
