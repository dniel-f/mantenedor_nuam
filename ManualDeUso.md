# 📖 Manual de Usuario - Mantenedor NUAM

## 1. Introducción

Bienvenido al Manual de Usuario del Mantenedor de Calificaciones Tributarias. Esta guía detalla cómo utilizar las funcionalidades del sistema según su rol asignado.

El sistema identifica tres roles principales:
* **Corredor:** Usuario principal. Puede gestionar (Crear, Modificar, Eliminar) sus propias calificaciones y realizar cargas masivas.
* **Administrador:** Tiene control total. Puede gestionar todos los registros, administrar usuarios y ver auditorías.
* **Auditor:** Rol de solo lectura. Puede ver todos los registros y consultar los logs de auditoría, pero no puede modificar datos.

---

## 2. Acceso al Sistema

Para ingresar al sistema, siga estos pasos:

1.  Navegue a la URL de inicio: `http://127.0.0.1:8000/`
2.  Si no ha iniciado sesión, será redirigido a la página de Login (`/usuarios/login/`).
3.  Ingrese el **Correo Electrónico** y la **Contraseña** asociados a su cuenta de la aplicación (la que se encuentra en la tabla `usuario`, no la del panel `/admin/`).
4.  Haga clic en **"Ingresar"**.

Al cerrar sesión, será redirigido de vuelta a esta página.

---

## 3. Flujo de Trabajo: Corredor

Esta sección detalla todas las operaciones disponibles para el rol "Corredor".

### 3.1. Dashboard (Página de Inicio)

Al iniciar sesión, lo primero que verá es el Dashboard. Este panel muestra:
* **Tarjetas de Estadísticas:** Un conteo rápido del total de calificaciones, cuántas son de ingreso "Manual" (suyas o de otros corredores) y cuántas son del "Sistema" (cargadas por Archivo o API).
* **Gráficos:**
    * **Calificaciones por Estado:** Un gráfico de dona que muestra la proporción de registros "Válido", "Inválido" o "Activo".
    * **Top 5 Mercados:** Un gráfico de barras que muestra los mercados con más calificaciones registradas.

### 3.2. Consultar Calificaciones (La Grilla)

Esta es la pantalla principal del mantenedor.

1.  **Acceso:** Haga clic en **"Mis Calificaciones"** en la barra de navegación.
2.  **Filtros:** Puede buscar registros específicos usando los filtros en la parte superior. Puede filtrar por **Mercado**, **Año Comercial** y **Origen**.
    * Haga clic en **"Buscar"** para aplicar los filtros.
    * Haga clic en el botón **"Limpiar"** (ícono de borrador) para ver todos los registros.
3.  **Lógica de Visualización (Localidad):**
    * Usted verá **todas** las calificaciones de "Archivo" (cargadas por el sistema).
    * Usted verá **solamente** las calificaciones "Manuales" que usted haya creado. No verá los registros manuales de otros corredores.
4.  **Columnas Clave:**
    * **Origen:** Muestra si el registro es "Manual" o "Archivo". Pase el mouse sobre la etiqueta para ver detalles (el usuario creador o el nombre del archivo CSV).
    * **Estado:** Muestra si el registro es "Válido" (verde) o "Inválido" (rojo), según las validaciones de la carga masiva.
    * **Acciones:**
        * (Lápiz): Le permite **Modificar** el registro.
        * (Basurero): Le permite **Eliminar** el registro.
        * (Candado): Aparece en los registros de "Archivo" que usted no puede modificar ni eliminar.

### 3.3. Ingresar una Calificación (Manual)

El sistema ofrece dos formas de ingresar un registro manualmente.

1.  En la grilla, haga clic en el botón verde **"Ingresar Calificación"**.
2.  Complete los **"Datos Generales"** (Mercado, Instrumento, Fecha Pago, Año, etc.).

#### Flujo A: Ingreso por Factores (Directo)

Este flujo se usa si usted ya conoce los factores finales (ej. 0.4, 0.6).

1.  Asegúrese de que el *switch* **"Ingreso por Montos"** esté **APAGADO**.
2.  Vaya a la sección "Factores Tributarios" e ingrese los valores decimales (ej. `0.25`).
3.  **Validación:** El sistema no le permitirá grabar si la suma de los factores F08 a F19 es mayor que 1.
4.  Haga clic en **"Grabar"**.

#### Flujo B: Ingreso por Montos (Recomendado)

Este flujo se usa si usted tiene los montos en pesos (DJ1948) y desea que el sistema calcule los factores.

1.  Asegúrese de que el *switch* **"Ingreso por Montos"** esté **ENCENDIDO**.
2.  Verá que las etiquetas cambian a "Monto-08", "Monto-09", etc.
3.  Ingrese los valores en pesos (ej. `50000`, `150000`).
4.  Haga clic en el botón azul **"Calcular"**.
5.  **¡Magia!** El sistema:
    * Calculará los factores (ej. F08 = 50000 / 200000 = 0.25).
    * Rellenará los campos de factores con los valores calculados.
    * Desactivará el *switch* "Ingreso por Montos".
    * Ocultará el botón "Calcular" y volverá a mostrar el botón "Grabar".
6.  Revise los factores calculados y haga clic en **"Grabar"**.

### 3.4. Modificar una Calificación

1.  En la grilla, haga clic en el ícono de lápiz del registro que desea modificar.
2.  Será llevado al formulario, que estará **pre-rellenado** con todos los datos de esa calificación (incluyendo los factores).
3.  Realice los cambios que necesite. Puede incluso usar el flujo "Ingreso por Montos" y "Calcular" para recalcular todo.
4.  Haga clic en **"Grabar"**.

**Regla de Negocio Importante (Prioridad):** Si usted modifica un registro que originalmente era de "Archivo" (un registro 🔒), al grabarlo, el sistema le asignará la propiedad. El registro se convertirá en "Manual" y será suyo permanentemente.

### 3.5. Eliminar una Calificación

Solo puede eliminar registros que sean "Manuales" y de su propiedad.

1.  En la grilla, haga clic en el ícono de basurero.
2.  Será llevado a una pantalla de confirmación.
3.  Haga clic en el botón rojo **"Sí, Eliminar"**.

**Nota:** Esta acción es un **borrado lógico**. El registro no se borra de la base de datos, solo se marca como inactivo (`activo=False`) y desaparece de la vista. Esta acción queda registrada en el Monitor de Auditoría.

### 3.6. Carga Masiva (Factores vs. Montos)

El sistema permite cargar dos tipos de archivos CSV. Ambos botones se encuentran en la parte superior de la grilla de calificaciones.

#### A. Carga Masiva (Factores)

1.  Haga clic en **"Carga Masiva (Factores)"**.
2.  Prepare un archivo CSV que siga el formato especificado en la página (ej. columnas `Factor 8`, `Factor 9`... y fecha `DD-MM-AAAA`).
3.  Suba el archivo y haga clic en **"Procesar Archivo"**.
4.  El sistema procesará el archivo **fila por fila**.
5.  Si una fila es válida (suma de factores <= 1), se guardará como "Válido".
6.  Si una fila es inválida (suma > 1), se guardará como "Inválido" (¡pero se guarda!).
7.  Recibirá un resumen (ej. "2 válidos, 1 inválido").

#### B. Carga Masiva (Montos)

1.  Haga clic en **"Carga Masiva (Montos)"**.
2.  Prepare un archivo CSV que siga el formato de Montos (DJ1948) (ej. columnas `Monto_08`, `Monto_09`... y fecha `AAAA-MM-DD`).
3.  Suba el archivo y haga clic en **"Procesar Archivo"**.
4.  El sistema leerá los montos, **calculará los factores** por usted, y guardará los resultados.
5.  Si una fila tiene un error de formato (ej. fecha incorrecta), será marcada como inválida en el log.

---

## 4. Flujo de Trabajo: Administrador y Auditor

Los roles de Administrador y Auditor tienen vistas adicionales accesibles desde el Navbar.

### 4.1. Mantenedor General (Admin y Auditor)

Este es el mismo enlace que "Mis Calificaciones", pero con superpoderes:
* Usted verá **TODOS** los registros, incluyendo los "Manuales" de **todos** los corredores.
* Puede filtrar y consultar cualquier dato del sistema.

### 4.2. Monitor de Auditoría (Admin y Auditor)

1.  Haga clic en **"Monitor de Auditoría"** en el Navbar.
2.  Verá una grilla con todos los cambios que han ocurrido en el sistema (INSERT, UPDATE, DELETE, IMPORT).
3.  Puede filtrar por **Acción**, **Usuario** o **Rango de Fechas**.
4.  **Enlaces de ID:**
    * Si un log (ej. `INSERT` ID 25) apunta a una calificación que aún existe, puede hacer clic en el ID (25) para ir a su vista de modificación.
    * Si un log (ej. `DELETE` ID 22) apunta a una calificación borrada, el ID (22) no tendrá enlace, evitando errores.

### 4.3. Gestionar Usuarios (Solo Administrador)

1.  Haga clic en **"Gestionar Usuarios"** en el Navbar.
2.  Verá una grilla con todos los usuarios del sistema (Corredores, Admins, etc.).
3.  Puede **Crear** un nuevo usuario. El formulario le pedirá una contraseña, y el sistema la *hasheará* (encriptará) automáticamente con `bcrypt`.
4.  Puede **Modificar** un usuario existente (cambiar su rol, estado o asignarle una nueva contraseña).

### 4.4. Exportar Reportes (Solo Administrador)

1.  Vaya al **"Mantenedor General"**.
2.  Aplique los filtros que desee (ej. Año 2025 y Mercado ACN).
3.  Haga clic en el botón de **Exportar** (ícono de hoja de cálculo  spreadsheet) que está junto al botón "Buscar".
4.  El sistema generará y descargará un archivo `reporte_calificaciones.csv` que contiene **únicamente los datos que usted filtró**.

### 4.5. Poderes Especiales del Administrador

* **Modificación Global:** Cuando un Administrador modifica un registro de "Archivo" (de Bolsa), este **no** se convierte en "Manual". La modificación se considera una corrección global que todos los corredores verán.
* **Eliminación en Formulario:** Al "Modificar" una calificación, el Administrador verá un botón "Eliminar Calificación" en la esquina inferior izquierda del formulario, permitiéndole borrar el registro sin volver a la grilla.


---
