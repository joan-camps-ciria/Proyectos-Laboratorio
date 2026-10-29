"""Gestor de tareas por línea de comandos con persistencia en JSON."""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# En Kubernetes se apunta a un volumen persistente con la variable TAREAS_FILE
ARCHIVO_TAREAS = Path(os.environ.get("TAREAS_FILE", Path(__file__).parent / "tareas.json"))
PRIORIDADES = {"alta": "\033[91m", "media": "\033[93m", "baja": "\033[92m"}
RESET = "\033[0m"
TACHADO = "\033[9m"


def cargar_tareas():
    if not ARCHIVO_TAREAS.exists():
        return []
    try:
        return json.loads(ARCHIVO_TAREAS.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        sys.exit(f"Error: {ARCHIVO_TAREAS.name} está corrupto.")


def guardar_tareas(tareas):
    ARCHIVO_TAREAS.parent.mkdir(parents=True, exist_ok=True)
    ARCHIVO_TAREAS.write_text(
        json.dumps(tareas, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def buscar_tarea(tareas, id_tarea):
    for tarea in tareas:
        if tarea["id"] == id_tarea:
            return tarea
    sys.exit(f"Error: no existe ninguna tarea con id {id_tarea}.")


def cmd_añadir(args):
    tareas = cargar_tareas()
    nuevo_id = max((t["id"] for t in tareas), default=0) + 1
    tareas.append({
        "id": nuevo_id,
        "texto": " ".join(args.texto),
        "prioridad": args.prioridad,
        "hecha": False,
        "creada": datetime.now().strftime("%Y-%m-%d %H:%M"),
    })
    guardar_tareas(tareas)
    print(f"✅ Tarea {nuevo_id} añadida.")


def cmd_listar(args):
    tareas = cargar_tareas()
    if not args.todas:
        tareas = [t for t in tareas if not t["hecha"]]
    if not tareas:
        print("🎉 No hay tareas pendientes.")
        return

    orden = list(PRIORIDADES)
    tareas.sort(key=lambda t: (t["hecha"], orden.index(t["prioridad"]), t["id"]))
    print(f"{'ID':>3}  {'PRIORIDAD':<9}  {'CREADA':<16}  TAREA")
    for t in tareas:
        color = PRIORIDADES[t["prioridad"]]
        texto = f"{TACHADO}{t['texto']}{RESET}" if t["hecha"] else t["texto"]
        print(f"{t['id']:>3}  {color}{t['prioridad']:<9}{RESET}  {t['creada']:<16}  {texto}")


def cmd_completar(args):
    tareas = cargar_tareas()
    buscar_tarea(tareas, args.id)["hecha"] = True
    guardar_tareas(tareas)
    print(f"✔️  Tarea {args.id} completada.")


def cmd_borrar(args):
    tareas = cargar_tareas()
    tarea = buscar_tarea(tareas, args.id)
    tareas.remove(tarea)
    guardar_tareas(tareas)
    print(f"🗑️  Tarea {args.id} borrada.")


def cmd_resumen(args):
    tareas = cargar_tareas()
    total = len(tareas)
    hechas = sum(t["hecha"] for t in tareas)
    porcentaje = hechas / total * 100 if total else 0
    barra = "█" * int(porcentaje // 5) + "░" * (20 - int(porcentaje // 5))
    print(f"Total: {total} | Hechas: {hechas} | Pendientes: {total - hechas}")
    print(f"[{barra}] {porcentaje:.0f}%")


def main():
    parser = argparse.ArgumentParser(description="Gestor de tareas por terminal.")
    sub = parser.add_subparsers(dest="comando", required=True)

    p = sub.add_parser("añadir", help="Añade una tarea nueva")
    p.add_argument("texto", nargs="+", help="Descripción de la tarea")
    p.add_argument("-p", "--prioridad", choices=PRIORIDADES, default="media")
    p.set_defaults(func=cmd_añadir)

    p = sub.add_parser("listar", help="Muestra las tareas pendientes")
    p.add_argument("-t", "--todas", action="store_true", help="Incluye las completadas")
    p.set_defaults(func=cmd_listar)

    p = sub.add_parser("completar", help="Marca una tarea como hecha")
    p.add_argument("id", type=int)
    p.set_defaults(func=cmd_completar)

    p = sub.add_parser("borrar", help="Elimina una tarea")
    p.add_argument("id", type=int)
    p.set_defaults(func=cmd_borrar)

    p = sub.add_parser("resumen", help="Muestra el progreso")
    p.set_defaults(func=cmd_resumen)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
