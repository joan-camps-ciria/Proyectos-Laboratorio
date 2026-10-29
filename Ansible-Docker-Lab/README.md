# 🤖 Laboratorio local de Ansible con nodos en Docker

Una guía para montar en tu máquina un entorno de prácticas de Ansible, parecido a lo que es minikube para Kubernetes: **los "servidores" son contenedores Docker** con systemd y distintas distribuciones (Ubuntu, Rocky Linux y Debian), y se gestionan con los mismos playbooks y roles que usarías con servidores reales.

Sobre ellos se despliega un caso real: **tres servidores web nginx detrás de un balanceador de carga**.

---

## 📌 Tabla de Contenidos
1. [Requisitos Previos](#-requisitos-previos)
2. [Arquitectura](#-arquitectura)
3. [Estructura del Proyecto](#-estructura-del-proyecto)
4. [Paso 1: Instalar Ansible](#paso-1-instalar-ansible)
5. [Paso 2: Levantar los nodos](#paso-2-levantar-los-nodos)
6. [Paso 3: El inventario](#paso-3-el-inventario)
7. [Paso 4: Comandos ad-hoc](#paso-4-comandos-ad-hoc)
8. [Paso 5: Los roles y el playbook](#paso-5-los-roles-y-el-playbook)
9. [Paso 6: Ejecutar el playbook](#paso-6-ejecutar-el-playbook)
10. [Paso 7: Probar el balanceador](#paso-7-probar-el-balanceador)
11. [Paso 8: Idempotencia y deriva](#paso-8-idempotencia-y-deriva)
12. [Paso 9: Previsualizar cambios con --check --diff](#paso-9-previsualizar-cambios-con---check---diff)
13. [Paso 10: Escalar añadiendo un nodo](#paso-10-escalar-añadiendo-un-nodo)
14. [Limpieza](#-limpieza)

---

## 🛠 Requisitos Previos

Antes de empezar, asegúrate de tener instalado:
*   [Docker.io](https://www.docker.com/) Los nodos del lab son contenedores
*   [Docker Compose](https://docs.docker.com/compose/) Para levantarlos todos con un comando (en Ubuntu con `docker.io`: `sudo apt install docker-compose-v2`)

---

## 🧩 Arquitectura

```text
┌──────────────────── Tu máquina (nodo de control) ────────────────────┐
│                                                                      │
│  ansible-playbook ── configura todos los nodos con "docker exec"     │
│                                                                      │
│  ┌─────────────────── Red Docker de "ansible-lab" ────────────────┐  │
│  │                                                                │  │
│  │                                 ┌──► web1 (nginx, Ubuntu)      │  │
│  │  localhost:8080 ──► lb1 ────────┼──► web2 (nginx, Rocky)       │  │
│  │                  (nginx, Ubuntu)└──► web3 (nginx, Debian)      │  │
│  │                                                                │  │
│  └────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────┘
```

| Nodo | Grupo | Sistema | Función |
|---|---|---|---|
| **lb1** | `lb` | Ubuntu 24.04 | Balanceador nginx: reparte las peticiones entre los nodos web. Publicado en `localhost:8080` |
| **web1** | `web` | Ubuntu 24.04 | Servidor web nginx |
| **web2** | `web` | Rocky Linux 9 | Servidor web nginx (familia RedHat: otro gestor de paquetes, otras rutas) |
| **web3** | `web` | Debian 12 | Servidor web nginx |

**Comparación con un entorno real:**

| | Entorno real | Este lab |
|---|---|---|
| Servidores | VMs o máquinas físicas | Contenedores con systemd |
| Crear servidores | Terraform, la consola del proveedor… | `docker compose up -d` |
| Conexión | SSH (por defecto) | `docker exec` (`ansible_connection=community.docker.docker`) |
| Playbooks y roles | — | **Los mismos** |

---

## 📂 Estructura del Proyecto

```text
Ansible-Docker-Lab/
├── docker-compose.yml           # Los "servidores" del lab
├── ansible.cfg                  # Configuración de Ansible para este proyecto
├── inventory.ini                # Nodos y grupos
├── site.yml                     # Playbook principal: qué rol va en cada grupo
├── group_vars/
│   └── web.yml                  # Variables del grupo web
└── roles/
    ├── web/                     # Servidores web
    │   ├── tasks/main.yml
    │   └── vars/
    │       ├── Debian.yml       # Carpeta de la web en Debian/Ubuntu
    │       └── RedHat.yml       # Carpeta de la web en Rocky/RHEL
    └── lb/                      # Balanceador
        ├── tasks/main.yml
        ├── handlers/main.yml
        └── templates/
            └── balanceador.conf.j2
```

> 💡 **Nota:** Todos los comandos de esta guía se ejecutan desde el directorio `Ansible-Docker-Lab/`. Ansible lee el `ansible.cfg` de la carpeta desde la que se ejecuta.

---

## Paso 1: Instalar Ansible

```bash
sudo apt install ansible
ansible --version
```
*Resultado esperado:*
```text
ansible [core 2.20.1]
  config file = None
  ...
```

El paquete `ansible` incluye `ansible-core` (el motor y los comandos `ansible` y `ansible-playbook`) y las colecciones más usadas, entre ellas `community.docker`, que permite a Ansible entrar en los contenedores.

> 💡 **Nota:** También se puede instalar con `pip install ansible` dentro de un entorno virtual de Python. Así tienes la versión más reciente, o una versión concreta por proyecto, a cambio de tener que activar el entorno en cada terminal.

---

## Paso 2: Levantar los nodos

Los nodos se definen en `docker-compose.yml`. Todos comparten unas opciones comunes, definidas una vez con un *ancla* de YAML (`&nodo`) y reutilizadas en cada servicio (`<<: *nodo`):

```yaml
x-nodo: &nodo
  # Necesario para que systemd funcione dentro del contenedor
  privileged: true
  cgroup: host
  volumes:
    - /sys/fs/cgroup:/sys/fs/cgroup:rw

services:
  lb1:
    <<: *nodo
    image: geerlingguy/docker-ubuntu2404-ansible
    container_name: lb1
    hostname: lb1
    ports:
      - "8080:80"
  # ...web1, web2 y web3
```

*   **Las imágenes `geerlingguy/docker-*-ansible`** están pensadas para probar Ansible. A diferencia de una imagen normal como `ubuntu:24.04`, traen **Python** (Ansible lo necesita en el nodo para ejecutar sus módulos) y arrancan **systemd** (necesario para gestionar servicios con `systemctl`).
*   **`privileged`, `cgroup: host` y el volumen `/sys/fs/cgroup`** son los permisos que necesita systemd dentro de un contenedor. Valen para un lab local, no para producción.
*   **`container_name`** hace que el contenedor se llame `web1` y no `ansible-lab-web1-1`. Ansible se conecta a los contenedores **por su nombre**, así que tiene que coincidir con el del inventario.
*   **La red**: Compose crea una red para todos los servicios y cada contenedor encuentra a los demás por su nombre. `lb1` usará esto para llegar a los servidores web.

Comprueba que el archivo es válido y levanta los nodos (la primera vez descarga las imágenes):

```bash
docker compose config --quiet && echo OK
docker compose up -d
docker compose ps
```
*Resultado esperado:*
```text
NAME   IMAGE                                    COMMAND                  SERVICE   CREATED          STATUS          PORTS
lb1    geerlingguy/docker-ubuntu2404-ansible    "/lib/systemd/systemd"   lb1       13 seconds ago   Up 13 seconds   0.0.0.0:8080->80/tcp, [::]:8080->80/tcp
web1   geerlingguy/docker-ubuntu2404-ansible    "/lib/systemd/systemd"   web1      13 seconds ago   Up 13 seconds
web2   geerlingguy/docker-rockylinux9-ansible   "/usr/lib/systemd/sy…"   web2      13 seconds ago   Up 13 seconds
web3   geerlingguy/docker-debian12-ansible      "/lib/systemd/systemd"   web3      13 seconds ago   Up 13 seconds
```

Comprueba que systemd ha arrancado dentro de un nodo:

```bash
docker exec web2 systemctl is-system-running
```
*Resultado esperado:*
```text
running
```

---

## Paso 3: El inventario

El **inventario** (`inventory.ini`) es la lista de servidores que gestiona Ansible, organizados en **grupos**:

```ini
[lb]
lb1

[web]
web1
web2
web3

[all:vars]
ansible_connection=community.docker.docker
```

*   **`[lb]` y `[web]`** son grupos. Además existe siempre el grupo **`all`**, con todos los nodos.
*   **`[all:vars]`** son variables para todos los nodos. `ansible_connection` le dice a Ansible *cómo* conectarse: por defecto usa SSH, y aquí usa `docker exec`. Por eso no hace falta configurar SSH ni claves.

`ansible.cfg` indica qué inventario usar, así no hace falta escribir `-i inventory.ini` en cada comando:

```ini
[defaults]
inventory = inventory.ini
interpreter_python = auto_silent
```

`interpreter_python = auto_silent` detecta el Python de cada nodo sin mostrar un aviso por cada uno.

```bash
ansible-inventory --graph
```
*Resultado esperado:*
```text
@all:
  |--@ungrouped:
  |--@lb:
  |  |--lb1
  |--@web:
  |  |--web1
  |  |--web2
  |  |--web3
```

Comprueba que Ansible llega a todos los nodos:

```bash
ansible all -m ping
```
*Resultado esperado (fragmento):*
```text
lb1 | SUCCESS => {
    "ansible_facts": {
        "discovered_interpreter_python": "/usr/bin/python3.12"
    },
    "changed": false,
    "ping": "pong"
}
web2 | SUCCESS => {
    "ansible_facts": {
        "discovered_interpreter_python": "/usr/bin/python3.9"
    },
    "changed": false,
    "ping": "pong"
}
```

`ping` no es un ping de red: Ansible entra en el nodo, ejecuta un pequeño script de Python y espera la respuesta `pong`. Fíjate en que ha **descubierto solo** el Python de cada sistema: 3.12 en Ubuntu y 3.9 en Rocky.

---

## Paso 4: Comandos ad-hoc

Un comando *ad-hoc* ejecuta **un solo módulo** sobre un grupo de nodos, sin escribir un playbook:

```text
ansible <grupo> -m <módulo> -a "<argumentos>"
```

**Ejecutar un comando** (si no indicas `-m`, se usa el módulo `command`):
```bash
ansible web -a "cat /etc/os-release"
```

**Consultar los *facts***, la información que Ansible recoge de cada nodo:
```bash
ansible all -m setup -a "filter=ansible_os_family"
```
Los Ubuntu y Debian son de la familia `Debian` y el Rocky de la familia `RedHat`. El rol `web` usará este dato para adaptarse a cada sistema.

**Instalar un paquete**:
```bash
ansible all -m package -a "name=tree state=present update_cache=true"
```
*Resultado esperado (fragmento):*
```text
web2 | CHANGED => {
    "changed": true,
    "results": [
        "Installed: tree-1.8.0-10.el9.x86_64"
    ]
}
```

No le dices "instala tree", sino "**tree debe estar presente**" (`state=present`). El módulo `package` usa `apt` o `dnf` según el sistema. Lánzalo **otra vez**:

```bash
ansible all -m package -a "name=tree state=present update_cache=true"
```
*Resultado esperado (fragmento):*
```text
web2 | SUCCESS => {
    "changed": false,
    "msg": "Nothing to do",
}
```

La segunda vez **no hace nada** (`"changed": false`): `tree` ya estaba. Esto es la **idempotencia**. Ansible comprueba el estado del nodo y solo actúa si no cumple lo que pides, así que puedes lanzar lo mismo cien veces sin miedo.

---

## Paso 5: Los roles y el playbook

Un **playbook** es una lista de tareas que se ejecutan en orden sobre un grupo de nodos. Para organizarlas se usan **roles**: carpetas con nombres fijos (`tasks/`, `handlers/`, `templates/`, `vars/`) donde Ansible sabe qué buscar.

El playbook principal, `site.yml`, solo dice qué rol va en cada grupo:

```yaml
- name: Servidores web
  hosts: web
  roles:
    - web

- name: Balanceador de carga
  hosts: lb
  roles:
    - lb
```

### Rol `web`: un mismo rol para distribuciones distintas

Ubuntu/Debian y Rocky sirven la web desde carpetas distintas. En vez de duplicar tareas, la diferencia está en un archivo de variables por familia:

| Archivo | Contenido |
|---|---|
| `roles/web/vars/Debian.yml` | `raiz_web: /var/www/html` |
| `roles/web/vars/RedHat.yml` | `raiz_web: /usr/share/nginx/html` |

```yaml
- name: Cargar las variables de la familia del sistema (Debian o RedHat)
  ansible.builtin.include_vars: "{{ ansible_facts['os_family'] }}.yml"

- name: Instalar nginx
  ansible.builtin.package:
    name: nginx
    state: present
    update_cache: true

- name: Arrancar nginx y activarlo al inicio
  ansible.builtin.service:
    name: nginx
    state: started
    enabled: true

- name: Publicar la página de inicio
  ansible.builtin.copy:
    content: "<h1>Hola desde {{ inventory_hostname }}</h1>\n<p>{{ mensaje }}</p>\n"
    dest: "{{ raiz_web }}/index.html"
```

*   **`{{ inventory_hostname }}`** es el nombre del nodo en el inventario: cada servidor tendrá una página distinta con la misma tarea.
*   **`{{ mensaje }}`** viene de `group_vars/web.yml`. Ansible carga automáticamente `group_vars/<grupo>.yml` para los nodos de ese grupo.

### Rol `lb`: plantillas y handlers

La configuración del balanceador es una **plantilla Jinja2** que se genera a partir del inventario:

```jinja
upstream web {
    zone web 64k;
{% for nodo in groups['web'] %}
    server {{ nodo }}:80;
{% endfor %}
}

server {
    listen 80 default_server;

    location / {
        proxy_pass http://web;
        add_header X-Servido-Por $upstream_addr always;
    }
}
```

*   **`groups['web']`** es la lista de nodos del grupo `web`. El bucle genera una línea `server` por cada uno, así que al añadir un nodo al inventario el balanceador lo incluye solo.
*   **`upstream`** es el grupo de servidores entre los que se reparte, y **`proxy_pass http://web`** reenvía cada petición a uno de ellos, por turnos (*round-robin*).
*   **`zone web 64k`** hace que todos los procesos de nginx compartan el turno de reparto (está explicado en las preguntas del final de la guía).

Las tareas que cambian la configuración avisan al **handler** `Recargar nginx`:

```yaml
- name: Configurar el balanceo hacia los nodos web
  ansible.builtin.template:
    src: balanceador.conf.j2
    dest: /etc/nginx/conf.d/balanceador.conf
  notify: Recargar nginx
```

Un handler se ejecuta **solo si alguna tarea que lo avisa ha cambiado algo**, **una sola vez** aunque lo avisen varias, y **al final del play**. Así nginx solo se recarga cuando hace falta.

---

## Paso 6: Ejecutar el playbook

Comprueba la sintaxis sin ejecutar nada y después lanza el playbook:

```bash
ansible-playbook site.yml --syntax-check
ansible-playbook site.yml
```
*Resultado esperado (final):*
```text
TASK [lb : Arrancar nginx y activarlo al inicio] *******************************
changed: [lb1]

RUNNING HANDLER [lb : Recargar nginx] ******************************************
changed: [lb1]

PLAY RECAP *********************************************************************
lb1                        : ok=6    changed=5    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
web1                       : ok=5    changed=3    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
web2                       : ok=5    changed=3    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
web3                       : ok=5    changed=3    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

Cómo leer el `PLAY RECAP`:

| Contador | Significado |
|---|---|
| `ok` | Tareas terminadas sin errores, **incluidas las que han cambiado algo** |
| `changed` | Tareas que han tenido que modificar algo en el nodo |
| `skipped` | Tareas que no se han ejecutado porque no cumplían su condición (`when`) |
| `failed` / `unreachable` | Tareas con error / nodos a los que no se ha podido conectar |

La primera tarea de cada play, `Gathering Facts`, no la has escrito tú: Ansible recoge los facts de cada nodo antes de empezar. Fíjate también en que el orden de los nodos cambia de una tarea a otra: Ansible ejecuta cada tarea **en paralelo en todos los nodos**, pero no empieza la siguiente hasta que todos han terminado.

Puedes ver la configuración que ha generado la plantilla en `lb1`:

```bash
ansible lb -a "cat /etc/nginx/conf.d/balanceador.conf"
```

---

## Paso 7: Probar el balanceador

El puerto 80 de `lb1` está publicado en el 8080 de tu máquina:

```bash
for i in 1 2 3 4 5 6; do curl -s localhost:8080 | head -1; done
```
*Resultado esperado:*
```text
<h1>Hola desde web1</h1>
<h1>Hola desde web2</h1>
<h1>Hola desde web3</h1>
<h1>Hola desde web1</h1>
<h1>Hola desde web2</h1>
<h1>Hola desde web3</h1>
```

La cabecera `X-Servido-Por` indica qué nodo ha servido cada respuesta:

```bash
curl -sI localhost:8080 | grep -i servido
```
*Resultado esperado:*
```text
X-Servido-Por: 172.19.0.3:80
```

El camino de una petición:

```text
curl localhost:8080
   │  Docker (ports: "8080:80")
   ▼
lb1: nginx en :80 ── proxy_pass http://web ──► upstream "web": web1 → web2 → web3 → web1…
                                                 (resuelve los nombres con el DNS de Docker)
```

En los logs de los nodos web se ve que la petición les llega **desde `lb1`**, no desde tu máquina:

```bash
ansible web -a "tail -n 2 /var/log/nginx/access.log"
```

---

## Paso 8: Idempotencia y deriva

Vuelve a ejecutar el playbook sin cambiar nada:

```bash
ansible-playbook site.yml
```
*Resultado esperado:*
```text
PLAY RECAP *********************************************************************
lb1                        : ok=5    changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
web1                       : ok=5    changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
web2                       : ok=5    changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
web3                       : ok=5    changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

**`changed=0`**: cada módulo ha comprobado el estado del nodo (el paquete está instalado, el servicio arrancado, el archivo tiene ese contenido) y no ha tenido que hacer nada. El handler no aparece porque nadie lo ha avisado. Ver `changed=0` contra un servidor significa que está **exactamente** como dice el código.

Ahora provoca una **deriva**, un cambio hecho a mano que aparta un servidor de su estado deseado. Para nginx en `web1`:

```bash
docker exec web1 systemctl stop nginx
for i in 1 2 3 4; do curl -s localhost:8080 | head -1; done
```

El balanceador detecta que `web1` no responde y reparte entre `web2` y `web3`. Ejecuta el playbook:

```bash
ansible-playbook site.yml
```
*Resultado esperado (fragmento):*
```text
TASK [web : Arrancar nginx y activarlo al inicio] ******************************
changed: [web1]
ok: [web2]
ok: [web3]
...
web1                       : ok=5    changed=1    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

Ansible ha detectado y corregido **solo** lo que no cuadraba. Repite el `curl` y `web1` vuelve a aparecer.

---

## Paso 9: Previsualizar cambios con --check --diff

Antes de aplicar un cambio en producción se mira qué va a cambiar, se prueba en un solo servidor y después se aplica al resto. Edita `group_vars/web.yml` y cambia el mensaje:

```yaml
mensaje: Versión 3, desplegada con Ansible
```

**A. Ver qué cambiaría, sin aplicar nada:**

```bash
ansible-playbook site.yml --check --diff
```
*Resultado esperado (fragmento):*
```text
TASK [web : Publicar la página de inicio] **************************************
@@ -1,2 +1,2 @@
 <h1>Hola desde web1</h1>
-<p>Versión 2, desplegada con Ansible</p>
+<p>Versión 3, desplegada con Ansible</p>

changed: [web1]
```

*   **`--check`**: modo simulación. Hace todas las comprobaciones, pero no toca nada.
*   **`--diff`**: muestra las diferencias línea a línea (`-` lo que se quita, `+` lo que se añade).

`curl -s localhost:8080` sigue mostrando la versión 2.

**B. Aplicarlo en un solo servidor** (despliegue *canario*):

```bash
ansible-playbook site.yml --limit web1
for i in 1 2 3; do curl -s localhost:8080; done
```

`web1` ya muestra la versión 3 y los demás todavía la 2.

**C. Aplicarlo en todos:**

```bash
ansible-playbook site.yml
```

Solo `web2` y `web3` salen con `changed=1`: `web1` ya estaba actualizado.

---

## Paso 10: Escalar añadiendo un nodo

Para añadir un servidor web, `web4`, solo hacen falta dos cambios. En `docker-compose.yml`, la "máquina":

```yaml
  web4:
    <<: *nodo
    image: geerlingguy/docker-rockylinux9-ansible
    container_name: web4
    hostname: web4
```

Y en `inventory.ini`, su papel:

```ini
[web]
web1
web2
web3
web4
```

Levanta el nodo nuevo (Compose solo crea lo que falta) y aplica la configuración:

```bash
docker compose up -d
ansible-playbook site.yml
```
*Resultado esperado (fragmento):*
```text
TASK [lb : Configurar el balanceo hacia los nodos web] *************************
changed: [lb1]
...
RUNNING HANDLER [lb : Recargar nginx] ******************************************
changed: [lb1]

PLAY RECAP *********************************************************************
lb1                        : ok=6    changed=2    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
web1                       : ok=5    changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
web2                       : ok=5    changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
web3                       : ok=5    changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
web4                       : ok=5    changed=3    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

*   **web4** se ha configurado desde cero. Al ser Rocky, ha usado `RedHat.yml` sin escribir nada nuevo.
*   **lb1** ha regenerado su configuración porque `groups['web']` tiene un nodo más, y el handler ha recargado nginx.
*   **web1, web2 y web3** no han cambiado.

No has tocado ni los roles, ni `site.yml`, ni la plantilla del balanceador.

---

## 🧹 Limpieza

```bash
docker compose stop      # Para los nodos; "docker compose start" los vuelve a arrancar tal cual
docker compose down      # Borra los contenedores y la red
```

Después de un `down`, el entorno se recrea igual con `docker compose up -d` y `ansible-playbook site.yml`: **la infraestructura es el código**.

---

<details>
<summary><b>Error <code>No package matching 'tree' is available</code> en los nodos Ubuntu</b></summary>
Las imágenes Docker de Ubuntu y Debian vienen con la lista de paquetes de apt vacía, para ocupar menos: es como si nunca se hubiera hecho un <code>apt update</code>. Añade <code>update_cache=true</code> al módulo <code>package</code> (en un playbook, <code>update_cache: true</code>). Rocky no tiene este problema porque <code>dnf</code> descarga la lista él solo cuando la necesita.
</details>

<details>
<summary><b>Error <code>mapping key "lb1" already defined</code> al levantar los nodos</b></summary>
En YAML no puede haber dos claves iguales en el mismo nivel: hay un servicio repetido en <code>docker-compose.yml</code>, normalmente por pegar un bloque dos veces. Busca la línea que indica el error y borra el duplicado. Con <code>docker compose config --quiet</code> puedes validar el archivo sin levantar nada.
</details>

<details>
<summary><b>¿Por qué el balanceador siempre responde web1 sin la línea <code>zone</code>?</b></summary>
nginx arranca un proceso <em>worker</em> por cada núcleo de CPU, y por defecto cada worker lleva su propio turno de <em>round-robin</em>. Cada <code>curl</code> abre una conexión nueva que suele caer en un worker distinto, y todos empiezan por el primer servidor de la lista. La directiva <code>zone web 64k;</code> guarda el estado del <code>upstream</code> en memoria compartida, de modo que todos los workers siguen el mismo turno.
</details>

<details>
<summary><b>Avisos <code>[WARNING]: Host 'lb1' is using the discovered Python interpreter</code></b></summary>
No son errores: Ansible avisa de que ha detectado el Python del nodo por su cuenta, y de que si se instala otro podría elegir uno distinto. En servidores reales a veces conviene fijarlo con <code>ansible_python_interpreter</code>. En el lab se silencian con <code>interpreter_python = auto_silent</code> en <code>ansible.cfg</code>.
</details>

<details>
<summary><b><code>systemctl</code> falla con <code>System has not been booted with systemd</code></b></summary>
El contenedor no tiene los permisos que necesita systemd. Comprueba que el servicio de <code>docker-compose.yml</code> incluye <code>&lt;&lt;: *nodo</code> (que aporta <code>privileged</code>, <code>cgroup: host</code> y el volumen <code>/sys/fs/cgroup</code>) y que usa una imagen <code>geerlingguy/docker-*-ansible</code>.
</details>

<details>
<summary><b>¿Cómo paso estos playbooks a servidores reales?</b></summary>
Los roles y <code>site.yml</code> no cambian. Solo cambia el inventario: quita <code>ansible_connection=community.docker.docker</code> (por defecto se usa SSH) e indica la dirección y el usuario de cada servidor, por ejemplo <code>web1 ansible_host=10.0.0.11 ansible_user=admin</code>. Si las tareas necesitan permisos de root, añade <code>become: true</code> a cada play (en los contenedores no hace falta porque Ansible ya entra como root).
</details>

---

Hecho con ❤️ por [Joan Camps](https://github.com/joan-camps-ciria)
