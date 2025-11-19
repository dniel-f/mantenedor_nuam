# Mantenedor NUAM (Calificaciones Tributarias)

Este proyecto es un sistema web modular de mantenimiento y administración (Mantenedor) para calificaciones tributarias, desarrollado en Django y conectado a una base de datos de Google Cloud SQL (MySQL).

El sistema incluye gestión de usuarios por roles (Corredor, Administrador, Auditor), un CRUD completo de calificaciones, un sistema de carga masiva (Factores y Montos) con lógica de cálculo, una API REST segura (JWT) y un dashboard de reportería.

## Requisitos Previos

* Linux (Probado en Ubuntu/Debian)
* Python 3.11
* `git` para clonar el repositorio.
* El ejecutable de **Cloud SQL Auth Proxy** (descargable [aquí](https://cloud.google.com/sql/docs/mysql/connect-auth-proxy#proxy-download-links)).
* **Dos archivos secretos** provistos por el desarrollador (ver Sección 2.1).

---

## 1. Instalación (Script Automático)

### 1.1. Preparación del Sistema (Librerías OS)

El conector de base de datos (`mysqlclient`) requiere librerías de desarrollo del sistema operativo para compilarse.
Ejecuta el siguiente comando en tu terminal para instalarlas (requiere permisos de administrador/sudo):

```bash
sudo apt-get update
sudo apt-get install python3-dev default-libmysqlclient-dev build-essential pkg-config
```

### 1.2. Ejecución del Script Automático
Una vez instaladas las librerías del sistema, el script install.sh automatizará la creación del entorno virtual de Python y la instalación de dependencias.


```bash
# 1. Clona el repositorio
git clone [https://github.com/dniel-f/mantenedor_nuam](https://github.com/dniel-f/mantenedor_nuam)
cd mantenedor_nuam

# 2. Da permisos de ejecución al script
chmod +x install.sh

# 3. Ejecuta el script de instalación
./install.sh
```

## 2. Configuración del Entorno
Este proyecto se conecta a una base de datos en Google Cloud. La conexión requiere dos archivos secretos y la ejecución del proxy.

## 2.1. Archivos Secretos
Has recibido dos (2) archivos del desarrollador por un canal seguro:

* .env: Un archivo de texto plano que contiene las credenciales (usuario, contraseña, puerto) de la base de datos.

* df-mantenedor-nuam-8da4c31e56a1.json (o similar): Esta es la llave de la Cuenta de Servicio de Google Cloud.

Acción: Mueve ambos archivos (.env y el archivo .json) a la carpeta raíz del proyecto (la misma carpeta donde está manage.py y install.sh).

## 2.2. Conexión Segura (Cloud SQL Auth Proxy)
Para conectar tu máquina local a la instancia de Google Cloud de forma segura, debes ejecutar el Cloud SQL Auth Proxy en una terminal separada.

* Asegúrate de que el archivo .json (del paso 2.1) esté en la raíz del proyecto.

* Asegúrate de que el ejecutable cloud-sql-proxy (de "Requisitos Previos") esté en la misma carpeta o en tu PATH.

* Abre una NUEVA TERMINAL (déjala abierta mientras trabajas) y ejecuta:


### Comando para iniciar el túnel seguro
### (Basado en la configuración del .env y los logs del proyecto)
```
./cloud-sql-proxy -c <<ruta_a_proyecto>>/df-mantenedor-nuam-8da4c31e56a1.json -p 3307 df-mantenedor-nuam:us-central1:bbdd-mantenedor-nuam
```
* -c: Apunta al archivo de credenciales JSON que moviste.

* -p 3307: Le dice al proxy que escuche en el puerto 3307 (como está definido en tu .env).

* "df-...": Es el nombre de conexión de la instancia en la nube.

Si tienes éxito, verás el mensaje: The proxy has started successfully and is ready for new connections!

## 3. Poblar la Base de Datos (Seed)
Este proyecto incluye un script (seed.sh) que carga datos de prueba (usuarios, calificaciones, logs) en la base de datos en la nube.

Abre una segunda terminal (deja el proxy corriendo en la primera).

Activa el entorno virtual:

```
source venv/bin/activate
```
Da permisos de ejecución al script de poblado:

```
chmod +x seed.sh
```
Ejecuta el script de poblado (esto puede tardar unos segundos):

```
(venv) $ ./seed.sh
```
Esto ejecutará python mantenedor_nuam/manage.py loaddata seed_data.json y cargará los datos de prueba.

Usuarios de Prueba (Seed)
La base de datos ahora contiene usuarios listos para usar. Contraseña para todos: admin123

* Rol Administrador: admin@mail.com

* Rol Corredor: corredor_a@mail.com

* Rol Corredor: corredor_b@mail.com

* Rol Auditor: auditor@mail.com

Ejecutar el Servidor

Verifica que el Cloud SQL Proxy esté corriendo en la Terminal 1.

En tu Terminal 2 (con el venv activado), ejecuta el servidor de Django:

```
(venv) $ python mantenedor_nuam/manage.py runserver
```
El sitio estará disponible en http://127.0.0.1:8000/.

# 5. (Opcional) Probar la API REST
Puedes probar la API (Criterio 5) usando Postman o Insomnia.

Obtener Token (Login API):

1. POST a http://127.0.0.1:8000/api/token/

2. Body (JSON): {"username": "admin@mail.com", "password": "admin123"}

3. Copia el access_token de la respuesta.

4. Probar Endpoint (Leer Calificaciones):

5. GET a http://127.0.0.1:8000/api/v1/calificaciones/

6. Autorización: Bearer Token (pega tu token de acceso).
