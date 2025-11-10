# Mantenedor NUAM (Calificaciones Tributarias)

Este proyecto es un sistema web modular de mantenimiento y administración (Mantenedor) para calificaciones tributarias, desarrollado en Django 5.2.7 y conectado a una base de datos legada de Google Cloud SQL (MySQL).

El sistema incluye gestión de usuarios por roles (Corredor, Administrador, Auditor), un CRUD completo de calificaciones, y un sistema de carga masiva (Factores y Montos) con lógica de cálculo y validación.

## Requisitos Previos

* Linux (Probado en Ubuntu/Debian)
* Python 3.11 (o superior)
* Acceso a un servidor de base de datos MySQL (local o remoto).
* `git` para clonar el repositorio.

---

## 1. Instalación (Script Automático)

El script `install.sh` automatizará la creación del entorno virtual y la instalación de dependencias.

```bash
# 1. Clona el repositorio
git clone https://github.com/dniel-f/mantenedor_nuam
cd mantenedor_nuam

# 2. Da permisos de ejecución al script
chmod +x install.sh

# 3. Ejecuta el script de instalación
./install.sh

# 4. Activa el entorno virtual en tu sesión actual
# (Debes hacer esto CADA VEZ que abras una nueva terminal)
source venv/bin/activate
```

---

## 2. Configuración de la Base de Datos (Manual)

Este proyecto está diseñado para conectarse a una base de datos MySQL existente y legada.

### 2.1. Creación del Esquema

Asegúrate de que la base de datos exista en tu servidor MySQL.

```sql
CREATE SCHEMA IF NOT EXISTS `mantenedor_calificaciones` DEFAULT CHARACTER SET utf8mb4;
USE `mantenedor_calificaciones`;
```
*(Si ya tienes el DDL completo, puedes ejecutarlo aquí)*.

### 2.2. Configuración de Django (.env)

El proyecto utiliza un archivo `.env` para manejar las contraseñas de forma segura (este archivo está en el `.gitignore` y nunca debe subirse a GitHub).

**1. Crea un archivo `.env`** en la raíz del proyecto (junto a `manage.py`):
```bash
touch .env
```

**2. Edita el archivo `.env`** y añade tus credenciales de base de datos:
```ini
# .env
DEBUG=True
SECRET_KEY=tu_secret_key_de_django_muy_larga_y_segura

# Configuración de la Base de Datos
DB_NAME=mantenedor_calificaciones
DB_USER=tu_usuario_de_mysql
DB_PASSWORD=tu_contraseña_de_mysql
DB_HOST=127.0.0.1
DB_PORT=3306
```

**3. (Si es la primera vez) Configura `settings.py`** para leer este archivo:
*Abre `mantenedor_nuam/settings.py` y añade esto al inicio:*
```python
import os
from dotenv import load_dotenv
load_dotenv() # Carga las variables del archivo .env
```
*Luego, busca la sección `DATABASES` y modifícala para usar estas variables:*
```python
# settings.py
SECRET_KEY = os.getenv('SECRET_KEY')
DEBUG = os.getenv('DEBUG', 'False') == 'True'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT'),
    }
}
```

---

## 3. Creación del Superusuario (Criterio 8)

Debido a que usamos una tabla `usuario` personalizada, el proceso de creación de superusuario requiere dos pasos manuales:

### Paso 3.1: Insertar Roles y Estados Base

Asegúrate de que la tabla `usuario` pueda encontrar sus `Roles` y `Estados`.

```sql
# Inserta los estados básicos (Ajusta los IDs si es necesario)
INSERT INTO estado (id_estado, nombre, descripcion) VALUES (5, 'Activo', 'Usuario habilitado');
INSERT INTO estado (id_estado, nombre, descripcion) VALUES (6, 'Invalido', 'Registro con errores');
# (Añade otros estados si los tienes)

# Inserta los roles básicos
INSERT INTO rol (id_rol, nombre, descripcion) VALUES (4, 'Administrador', 'Rol con todos los permisos');
INSERT INTO rol (id_rol, nombre, descripcion) VALUES (5, 'Corredor', 'Usuario de Corredora');
INSERT INTO rol (id_rol, nombre, descripcion) VALUES (6, 'Auditor', 'Usuario supervisor de solo lectura');
```

### Paso 3.2: Crear el Usuario

1.  **Crea el usuario en Django (para el panel /admin):**
    ```bash
    (venv) $ python manage.py createsuperuser
    # Sigue las instrucciones (Email: admin@mail.com, Pass: ...)
    ```

2.  **Crea el usuario en la App (para el Login/Auditoría):**
    Ejecuta este SQL en tu base de datos, **asegurándote de que el `correo` coincida exactamente con el email que usaste en el paso 1**.

    ```sql
    # Asume que el ID de Rol 'Administrador' es 4 y el ID de Estado 'Activo' es 5
    INSERT INTO usuario 
    (nombre, correo, contrasena_hash, id_rol, id_estado, fecha_creacion) 
    VALUES 
    ('Admin Principal', 'admin@mail.com', 'hash_placeholder', 4, 5, NOW());
    ```

3.  **Actualiza la Contraseña (¡Importante!):**
    El `hash_placeholder` no funcionará. Debes generar un hash `bcrypt` real y actualizarlo.
    * Ejecuta el script `crear_hash.py` (que hicimos anteriormente).
    * Copia el hash que genera.
    * Ejecuta el SQL:
        ```sql
        UPDATE usuario SET contrasena_hash = 'pega_el_hash_de_bcrypt_aqui' 
        WHERE correo = 'admin@mail.com';
        ```

---

## 4. Ejecutar el Servidor

¡Todo listo! Con el entorno activado (`source venv/bin/activate`), ejecuta el servidor:

```bash
(venv) $ python manage.py runserver
```

El sitio estará disponible en `http://127.0.0.1:8000/`.