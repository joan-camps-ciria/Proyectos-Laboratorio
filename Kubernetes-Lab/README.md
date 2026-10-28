# 🚀 Levantar un clúster de Kubernetes para labs

Una guía de como levantar un clúster de Kubernetes en local usando minikube para poder realizar pruebas o ejercicios

---

## 📌 Tabla de Contenidos
1. [Requisitos Previos](#-requisitos-previos)
2. [Paso 1: Instalación](#paso-1-instalación)
3. [Paso 2: Configuración Inicial](#paso-2-configuración-inicial)
4. [Comandos Esenciales K8s](#-comandos-esenciales)

---

## 🛠 Requisitos Previos

Antes de empezar, asegúrate de tener instalado:
*   [Docker.io](https://www.docker.com/) Necesario para levantar el clúster con minikube

---

## Paso 1: Instalación Minikube

Revisa la documentación de [Minikube](https://minikube.sigs.k8s.io/docs/)

Para la instalación en Linux x86-64:

```bash
curl -LO https://github.com/kubernetes/minikube/releases/latest/download/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube && rm minikube-linux-amd64
```

> 💡 **Nota:** Para otros sistemas operativos revisar la documentación.

---

## Paso 2: Iniciar Minikube

Tras la instalación podemos iniciar el clúster:

```bash
minikube start
```
![Captura de pantalla del arranque](img/minikube.png)



---

## Comandos Esenciales K8s

Adjunto un documento con comandos esenciales de K8s que son ideales para probar en nuestro clúster de pruebas de Kubernetes: [Guía Comandos Esenciales K8s](https://github.com/joan-camps-ciria/Proyectos-Laboratorio/tree/master/Kubernetes-Lab/guide.md)

<details>
<summary><b>¿Qué hago si obtengo un error al iniciar minikube con docker?</b></summary>
Probablemente tu usuario no tenga permisos para levantar contenedores con Docker, aplicar grupo al usuario con: <code>sudo usermod -aG docker $USER</code>
</details>

---

Hecho con ❤️ por [Joan Camps](https://github.com/joan-camps-ciria)

