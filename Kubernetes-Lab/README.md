# 🚀 Levantar un clúster de Kubernetes de laboratorio

Una guía de como levantar un clúster de Kubernetes en local usando minikube para poder realizarpruebas o ejercicios

---

## 📌 Tabla de Contenidos
1. [Requisitos Previos](#-requisitos-previos)
2. [Paso 1: Instalación](#paso-1-instalación)
3. [Paso 2: Configuración Inicial](#paso-2-configuración-inicial)
4. [Preguntas Frecuentes](#-preguntas-frecuentes)

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

## 💬 Preguntas Frecuentes

<details>
<summary><b>¿Qué hago si obtengo un error de puerto ocupado?</b></summary>
Puedes cambiar el puerto `8080` en el archivo <code>config.js</code> por cualquier otro número libre, como el `3000`.
</details>

<details>
<summary><b>¿Este tutorial sirve para producción?</b></summary>
No, está diseñado exclusivamente para entornos de desarrollo local.
</details>

---

Hecho con ❤️ por [Joan Camps](https://github.com/joan-camps-ciria)

