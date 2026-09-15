from typing import List, Optional

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Query, status

from database import get_collection
from models import ItemIn, ItemOut, doc_to_itemout

router = APIRouter(prefix="/items", tags=["items"])


@router.get("", response_model=List[ItemOut])
async def listar_items(
    q: Optional[str] = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
):
    coll = get_collection()
    query = {}
    if q:
        query = {"nombre": {"$regex": q, "$options": "i"}}

    items = []
    cursor = coll.find(query).skip(skip).limit(limit)
    async for doc in cursor:
        items.append(doc_to_itemout(doc))
    return items


@router.post("", response_model=ItemOut, status_code=status.HTTP_201_CREATED)
async def crear_item(item: ItemIn):
    coll = get_collection()
    data = item.model_dump()
    result = await coll.insert_one(data)
    doc = await coll.find_one({"_id": result.inserted_id})
    return doc_to_itemout(doc)


@router.get("/{item_id}", response_model=ItemOut)
async def obtener_item(item_id: str):
    coll = get_collection()
    if not ObjectId.is_valid(item_id):
        raise HTTPException(status_code=400, detail="ID invalido")

    doc = await coll.find_one({"_id": ObjectId(item_id)})
    if doc is None:
        raise HTTPException(status_code=404, detail="Item no encontrado")
    return doc_to_itemout(doc)


@router.put("/{item_id}", response_model=ItemOut)
async def actualizar_item(item_id: str, item: ItemIn):
    coll = get_collection()
    if not ObjectId.is_valid(item_id):
        raise HTTPException(status_code=400, detail="ID invalido")

    result = await coll.update_one(
        {"_id": ObjectId(item_id)},
        {"$set": item.model_dump()},
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Item no encontrado")

    doc = await coll.find_one({"_id": ObjectId(item_id)})
    return doc_to_itemout(doc)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_item(item_id: str):
    coll = get_collection()
    if not ObjectId.is_valid(item_id):
        raise HTTPException(status_code=400, detail="ID invalido")

    result = await coll.delete_one({"_id": ObjectId(item_id)})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Item no encontrado")

    return None
