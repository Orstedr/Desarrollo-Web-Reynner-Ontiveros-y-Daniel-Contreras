from typing import List

from pydantic import BaseModel, Field


class Item(BaseModel):
    nombre: str = Field(min_length=1)
    precio: float = Field(gt=0)
    tags: List[str] = Field(default_factory=list)
    activo: bool = True


class ItemIn(Item):
    pass


class ItemOut(Item):
    id: str


def doc_to_itemout(doc) -> ItemOut:
    return ItemOut(
        id=str(doc["_id"]),
        nombre=doc["nombre"],
        precio=doc["precio"],
        tags=doc.get("tags", []),
        activo=doc.get("activo", True),
    )
