### Pruebas realizadas

#### 1. Crear un item

**Método:** POST
**Endpoint:** `/items`

**Request Body:**

```json
{
  "nombre": "Mouse",
  "precio": 15990,
  "tags": ["computacion"],
  "activo": true
}
```

**Resultado:** `201 Created`

**Response Body:**

```json
{
  "id": "ID_GENERADO",
  "nombre": "Mouse",
  "precio": 15990,
  "tags": ["computacion"],
  "activo": true
}
```

---

#### 2. Listar items

**Método:** GET
**Endpoint:** `/items?skip=0&limit=50`

**Resultado:** `200 OK`

**Response Body:**

```json
[
  {
    "id": "ID_GENERADO",
    "nombre": "Mouse",
    "precio": 15990,
    "tags": ["computacion"],
    "activo": true
  }
]
```

---

#### 3. Buscar items por nombre

**Método:** GET
**Endpoint:** `/items?q=mouse`

**Resultado:** `200 OK`

**Response Body:**

```json
[
  {
    "id": "ID_GENERADO",
    "nombre": "Mouse",
    "precio": 15990,
    "tags": ["computacion"],
    "activo": true
  }
]
```

---

#### 4. Obtener un item por ID

**Método:** GET
**Endpoint:** `/items/{item_id}`

**Resultado:** `200 OK`

**Response Body:**

```json
{
  "id": "ID_GENERADO",
  "nombre": "Mouse",
  "precio": 15990,
  "tags": ["computacion"],
  "activo": true
}
```

---

#### 5. Actualizar un item

**Método:** PUT
**Endpoint:** `/items/{item_id}`

**Request Body:**

```json
{
  "nombre": "Teclado actualizado",
  "precio": 24990,
  "tags": ["computacion", "perifericos"],
  "activo": true
}
```

**Resultado:** `200 OK`

**Response Body:**

```json
{
  "id": "ID_GENERADO",
  "nombre": "Teclado actualizado",
  "precio": 24990,
  "tags": ["computacion", "perifericos"],
  "activo": true
}
```

---

#### 6. Eliminar un item

**Método:** DELETE
**Endpoint:** `/items/{item_id}`

**Resultado:** `204 No Content`

El endpoint elimina correctamente el item y no devuelve un Response Body, según lo esperado para una respuesta `204`.

---

#### 7. ID inválido

**Método:** GET
**Endpoint:** `/items/123`

**Resultado:** `400 Bad Request`

**Response Body:**

```json
{
  "detail": "ID invalido"
}
```

---

#### 8. Item inexistente

**Método:** GET
**Endpoint:** `/items/507f1f77bcf86cd799439011`

**Resultado:** `404 Not Found`

**Response Body:**

```json
{
  "detail": "Item no encontrado"
}
```

---

#### 9. Datos inválidos

**Método:** POST
**Endpoint:** `/items`

**Request Body:**

```json
{
  "nombre": "",
  "precio": -100,
  "tags": [],
  "activo": true
}
```

**Resultado:** `422 Unprocessable Entity`

La API rechaza los datos debido a las validaciones definidas para `nombre` y `precio`.

---

#### 10. Persistencia de datos

Se creó un item y posteriormente se detuvo y reinició el servidor FastAPI. Luego se realizó nuevamente una consulta `GET /items`.

**Resultado:** `200 OK`

El item creado continuó disponible después del reinicio de FastAPI, demostrando que los datos permanecen almacenados en MongoDB.
