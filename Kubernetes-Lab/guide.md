## ☸️ GUÍA RÁPIDA: COMANDOS ESENCIALES DE KUBERNETES (kubectl)

Una chuleta práctica con los comandos más utilizados en el día a día para administrar clústeres, desplegar aplicaciones y solucionar problemas.

---

### 🔍 1. Inspección del Clúster y Estado General
Comandos básicos para verificar que los nodos, componentes y recursos generales están levantados y estables.

# Ver el estado y la versión de todos los nodos del clúster
```bash
kubectl get nodes -o wide
```
*Resultado esperado:*
```text
NAME             STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE
minikube-node1   Ready    control-plane   2d5h   v1.28.2   192.168.49.2  <none>        Ubuntu 22.04 LTS
```

# Listar absolutamente todos los recursos (Pods, Services, Deployments) en el espacio de nombres por defecto
```bash
kubectl get all
```

---

### 📦 2. Gestión de Pods y Despliegues
Comandos para crear, listar y eliminar las unidades de ejecución de tus aplicaciones (Pods) y sus controladores (Deployments).

# Listar todos los Pods en un Namespace específico (ej: kube-system)
```bash
kubectl get pods -n kube-system
```

# Crear un despliegue rápido de un contenedor Nginx directamente desde la terminal
```bash
kubectl create deployment mi-servidor-web --image=nginx
```
*Resultado esperado:*
```text
deployment.apps/mi-servidor-web created
```

# Escalar el despliegue para tener 3 réplicas idénticas corriendo en paralelo
```bash
kubectl scale deployment mi-servidor-web --replicas=3
```

---

### 🌐 3. Conectividad y Acceso a Servicios
Cómo exponer tus aplicaciones al exterior o acceder a ellas de forma temporal para realizar pruebas.

# Exponer el despliegue de Nginx mediante un puerto interno (ClusterIP)
```bash
kubectl expose deployment mi-servidor-web --port=80 --target-port=80 --type=ClusterIP
```

# Realizar un Port-Forward temporal para mapear el servicio a tu máquina local
# (Permite acceder desde tu navegador local a http://localhost:8080)
```bash
kubectl port-forward service/mi-servidor-web 8080:80
```
*Resultado esperado:*
```text
Forwarding from 127.0.0.1:8080 -> 80
Forwarding from [::1]:8080 -> 80
Handling connection for 8080
```

---

### 🪵 4. Depuración y Resolución de Problemas (Troubleshooting)
Cuando algo falla, estos comandos son fundamentales para auditar los recursos, ver los logs y meterse "dentro" de los contenedores.

# Obtener una radiografía detallada con la configuración, eventos y errores de un Pod específico
```bash
kubectl describe pod mi-servidor-web-746b9ff-xyz12
```

# Ver las últimas líneas de logs (salida estándar) de un contenedor en tiempo real
```bash
kubectl logs -f mi-servidor-web-746b9ff-xyz12
```

# Abrir una terminal interactiva (Shell) dentro de un contenedor en ejecución para inspeccionar archivos
```bash
kubectl exec -it mi-servidor-web-746b9ff-xyz12 -- /bin/sh
```

---

### 🧹 5. Limpieza de Recursos

# Eliminar por completo el servicio y el despliegue creados anteriormente
```bash
kubectl delete service mi-servidor-web
kubectl delete deployment mi-servidor-web
```

---
💡 **Consejo Pro:** Puedes añadir el alias `alias k='kubectl'` en tu archivo `.bashrc` o `.zshrc` para ejecutar todos estos comandos usando simplemente la letra `k`.
