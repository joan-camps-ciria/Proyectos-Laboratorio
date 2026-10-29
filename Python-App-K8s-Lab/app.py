"""API web del gestor de tareas. Comparte el archivo de datos con la versión de terminal (main.py)."""

import threading
from datetime import datetime
from typing import Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from main import cargar_tareas, guardar_tareas

app = FastAPI(title="Gestor de tareas", version="2.0")

# FastAPI atiende varias peticiones a la vez; el candado evita que dos escrituras pisen el JSON
candado = threading.Lock()

Prioridad = Literal["alta", "media", "baja"]


class TareaNueva(BaseModel):
    texto: str = Field(min_length=1, examples=["Desplegar la API en minikube"])
    prioridad: Prioridad = "media"


class Tarea(TareaNueva):
    id: int
    hecha: bool
    creada: str


class Resumen(BaseModel):
    total: int
    hechas: int
    pendientes: int
    porcentaje: float


def buscar_tarea(tareas, id_tarea):
    for tarea in tareas:
        if tarea["id"] == id_tarea:
            return tarea
    raise HTTPException(status_code=404, detail=f"No existe ninguna tarea con id {id_tarea}")


@app.get("/salud", tags=["sistema"])
def salud():
    """Usado por Kubernetes para saber si el contenedor está vivo."""
    return {"estado": "ok"}


@app.get("/tareas", response_model=list[Tarea], tags=["tareas"])
def listar(todas: bool = False):
    tareas = cargar_tareas()
    if not todas:
        tareas = [t for t in tareas if not t["hecha"]]
    orden = ["alta", "media", "baja"]
    return sorted(tareas, key=lambda t: (t["hecha"], orden.index(t["prioridad"]), t["id"]))


@app.get("/tareas/{id_tarea}", response_model=Tarea, tags=["tareas"])
def obtener(id_tarea: int):
    return buscar_tarea(cargar_tareas(), id_tarea)


@app.post("/tareas", response_model=Tarea, status_code=201, tags=["tareas"])
def añadir(nueva: TareaNueva):
    with candado:
        tareas = cargar_tareas()
        tarea = {
            "id": max((t["id"] for t in tareas), default=0) + 1,
            "texto": nueva.texto,
            "prioridad": nueva.prioridad,
            "hecha": False,
            "creada": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }
        tareas.append(tarea)
        guardar_tareas(tareas)
    return tarea


@app.patch("/tareas/{id_tarea}/completar", response_model=Tarea, tags=["tareas"])
def completar(id_tarea: int):
    with candado:
        tareas = cargar_tareas()
        tarea = buscar_tarea(tareas, id_tarea)
        tarea["hecha"] = True
        guardar_tareas(tareas)
    return tarea


@app.delete("/tareas/{id_tarea}", status_code=204, tags=["tareas"])
def borrar(id_tarea: int):
    with candado:
        tareas = cargar_tareas()
        tareas.remove(buscar_tarea(tareas, id_tarea))
        guardar_tareas(tareas)


@app.get("/resumen", response_model=Resumen, tags=["tareas"])
def resumen():
    tareas = cargar_tareas()
    total = len(tareas)
    hechas = sum(t["hecha"] for t in tareas)
    return Resumen(
        total=total,
        hechas=hechas,
        pendientes=total - hechas,
        porcentaje=round(hechas / total * 100, 1) if total else 0,
    )
