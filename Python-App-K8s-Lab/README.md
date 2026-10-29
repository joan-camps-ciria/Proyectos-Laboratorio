# 🐍 Desplegar una API de Python en Kubernetes

Una guía de cómo empaquetar una API web hecha con Python (FastAPI) en una imagen de contenedor y desplegarla en un clúster local de Kubernetes con minikube, usando un volumen persistente para no perder los datos.

La aplicación es un **gestor de tareas** que se puede usar de dos formas: como API web (`app.py`) o desde la terminal (`main.py`). Ambas comparten el mismo archivo de datos.

---

## 📌 Tabla de Contenidos
1. [Requisitos Previos](#-requisitos-previos)
2. [Estructura del Proyecto](#-estructura-del-proyecto)
3. [Paso 1: Probar la app en local](#paso-1-probar-la-app-en-local)
4. [Paso 2: Arrancar minikube](#paso-2-arrancar-minikube)
5. [Paso 3: Construir la imagen dentro de minikube](#paso-3-construir-la-imagen-dentro-de-minikube)
6. [Paso 4: Desplegar en Kubernetes](#paso-4-desplegar-en-kubernetes)
7. [Paso 5: Acceder a la API](#paso-5-acceder-a-la-api)
8. [Paso 6: Comprobar la persistencia de datos](#paso-6-comprobar-la-persistencia-de-datos)
9. [Limpieza](#-limpieza)

---

## 🛠 Requisitos Previos

Antes de empezar, asegúrate de tener instalado:
*   [Docker.io](https://www.docker.com/) Necesario para levantar el clúster con minikube
*   [Minikube](https://minikube.sigs.k8s.io/docs/) y [kubectl](https://kubernetes.io/docs/tasks/tools/)
*   [Python 3](https://www.python.org/downloads/) Solo si quieres probar la app en local (Paso 1)

> 💡 **Nota:** Si todavía no tienes minikube, sigue primero el tutorial [Levantar un clúster de Kubernetes para labs](../Kubernetes-Lab/README.md).

---

## 📂 Estructura del Proyecto

```text
Python-App-K8s-Lab/
├── app.py              # API web con FastAPI
├── main.py             # Versión de terminal (y funciones de guardado compartidas)
├── requirements.txt    # Dependencias: fastapi y uvicorn
├── Dockerfile          # Receta para construir la imagen
└── k8s/
    └── tareas.yaml     # PersistentVolumeClaim + Deployment + Service
```

> 💡 **Nota:** Todos los comandos de esta guía se ejecutan desde el directorio `Python-App-K8s-Lab/`.

---

## Paso 1: Probar la app en local

Crea un entorno virtual, instala las dependencias y arranca el servidor:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --reload
```

Abre http://localhost:8000/docs para ver la documentación interactiva de la API.

La versión de terminal también funciona sin servidor:

```bash
python3 main.py añadir Desplegar la API en minikube -p alta
python3 main.py listar
python3 main.py --help
```

> 💡 **Nota:** Este paso es opcional. Para desplegar en Kubernetes no hace falta tener Python instalado en tu máquina, todo se construye dentro de la imagen.

---

## Paso 2: Arrancar minikube

```bash
minikube start
```

Al arrancar verás `Enabled addons: default-storageclass, storage-provisioner`. Es el componente que creará automáticamente el disco cuando pidamos el volumen persistente.

---

## Paso 3: Construir la imagen dentro de minikube

minikube tiene su propio motor de contenedores, separado del Docker de tu máquina. Construimos la imagen directamente ahí para que el clúster la encuentre sin tener que subirla a un registro como Docker Hub:

```bash
minikube image build -t tareas:2.0 .
```
*Resultado esperado (últimas líneas):*
```text
#10 naming to docker.io/library/tareas:2.0 done
#10 DONE 0.7s
```

> 💡 **Nota:** Por eso en `k8s/tareas.yaml` pone `imagePullPolicy: Never`: Kubernetes usa la imagen local y no intenta descargarla. Si construyes con `docker build`, la imagen se queda en tu Docker y tendrás que copiarla con `minikube image load tareas:2.0`.

---

## Paso 4: Desplegar en Kubernetes

El archivo `k8s/tareas.yaml` define tres recursos:

| Recurso | Para qué sirve |
|---|---|
| **PersistentVolumeClaim** `tareas-datos` | Disco de 100 MiB donde se guarda `tareas.json`. Sobrevive aunque el pod se borre |
| **Deployment** `tareas` | Mantiene un pod con la API en marcha. Si muere, crea otro. Incluye *probes* que comprueban `/salud` |
| **Service** `tareas` | Dirección interna estable (puerto 80) que redirige al puerto 8000 del pod |

```bash
kubectl apply -f k8s/tareas.yaml
```
*Resultado esperado:*
```text
persistentvolumeclaim/tareas-datos created
deployment.apps/tareas created
service/tareas created
```

Comprueba que todo está levantado:

```bash
kubectl get pods,pvc,svc
```
*Resultado esperado:*
```text
NAME                          READY   STATUS    RESTARTS   AGE
pod/tareas-67cb5758dc-rwqzp   1/1     Running   0          7s

NAME                                 STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS
persistentvolumeclaim/tareas-datos   Bound    pvc-ec1dd00c-211e-4d7b-8e04-a2772b6bd906   100Mi      RWO            standard

NAME                 TYPE        CLUSTER-IP    EXTERNAL-IP   PORT(S)   AGE
service/tareas       ClusterIP   10.111.7.69   <none>        80/TCP    7s
```

El pod debe estar en `Running` y el PVC en `Bound`.

---

## Paso 5: Acceder a la API

Los pods y los Services solo tienen IPs internas del clúster. Con `port-forward` abrimos un túnel temporal desde tu máquina:

```bash
kubectl port-forward service/tareas 8080:80
```
*Resultado esperado:*
```text
Forwarding from 127.0.0.1:8080 -> 8000
Forwarding from [::1]:8080 -> 8000
```

```text
Navegador → localhost:8080 → kubectl → Service (80) → Pod uvicorn (8000) → /data/tareas.json
```

Mientras el comando está en marcha, abre **http://localhost:8080/docs** y prueba los endpoints con el botón *Try it out*.

| Método | Ruta | Qué hace |
|---|---|---|
| `GET` | `/tareas` | Lista las tareas pendientes (`?todas=true` incluye las completadas) |
| `GET` | `/tareas/{id}` | Obtiene una tarea |
| `POST` | `/tareas` | Crea una tarea |
| `PATCH` | `/tareas/{id}/completar` | Marca una tarea como hecha |
| `DELETE` | `/tareas/{id}` | Borra una tarea |
| `GET` | `/resumen` | Total, hechas, pendientes y porcentaje |
| `GET` | `/salud` | Usado por Kubernetes para saber si el contenedor está vivo |

También puedes probarla desde otra terminal con `curl`:

```bash
curl -X POST localhost:8080/tareas -H 'Content-Type: application/json' -d '{"texto":"Mi primera tarea en Kubernetes","prioridad":"alta"}'
```
*Resultado esperado:*
```text
{"texto":"Mi primera tarea en Kubernetes","prioridad":"alta","id":1,"hecha":false,"creada":"2026-10-29 16:02"}
```

La versión de terminal sigue disponible dentro del pod:

```bash
kubectl exec deploy/tareas -- python main.py listar
```

> 💡 **Nota:** `port-forward` es una herramienta de pruebas: el túnel se cierra al detener el comando (`Ctrl+C`). En un clúster real la app se expone con un Service de tipo `LoadBalancer` o con un **Ingress**.

---

## Paso 6: Comprobar la persistencia de datos

Borra el pod. El Deployment detectará que falta y creará uno nuevo:

```bash
kubectl delete pod -l app=tareas
kubectl get pods
```

El nuevo pod tendrá otro nombre, pero al consultar las tareas siguen ahí, porque están guardadas en el volumen y no en el contenedor:

```bash
kubectl exec deploy/tareas -- python main.py listar
```

---

## 🧹 Limpieza

Elimina todos los recursos creados (⚠️ al borrar el PVC también se borran las tareas) y detén el clúster:

```bash
kubectl delete -f k8s/tareas.yaml
minikube stop
```

---

<details>
<summary><b>¿Qué hago si el pod se queda en <code>ErrImageNeverPull</code>?</b></summary>
La imagen no está dentro de minikube. Seguramente la construiste con <code>docker build</code> en lugar de <code>minikube image build</code>. Vuelve a ejecutar el Paso 3 o cópiala con <code>minikube image load tareas:2.0</code>.
</details>

<details>
<summary><b>¿Qué hago si <code>python3 -m venv</code> da el error "ensurepip is not available"?</b></summary>
En Ubuntu/Debian falta el paquete de entornos virtuales, instálalo con: <code>sudo apt install python3-venv</code> (o la versión concreta que indique el error, por ejemplo <code>python3.14-venv</code>).
</details>

<details>
<summary><b>¿Por qué minikube avisa de que mi kubectl es de otra versión?</b></summary>
kubectl solo garantiza compatibilidad con una versión menor de diferencia respecto al clúster. Para los comandos de este lab no suele dar problemas, pero puedes usar el kubectl integrado de minikube con <code>minikube kubectl -- get pods</code> o actualizar el tuyo.
</details>

---

Hecho con ❤️ por [Joan Camps](https://github.com/joan-camps-ciria)
