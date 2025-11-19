#!/bin/bash
# install.sh
# Script de instalación automático para el Mantenedor NUAM en Linux

# Colores para mensajes
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================================${NC}"
echo -e "${GREEN}   Iniciando la instalación del Mantenedor NUAM         ${NC}"
echo -e "${GREEN}========================================================${NC}"

# Definir el nombre del entorno virtual
VENV_NAME="venv"
PYTHON_VERSION="python3.11"

# [PASO 1] Verificaciones de Sistema (Pre-requisitos)
echo "[1/4] Verificando dependencias del sistema..."

if ! command -v $PYTHON_VERSION &> /dev/null; then
    echo -e "${RED}ERROR CRÍTICO: $PYTHON_VERSION no se encuentra.${NC}"
    echo "Por favor, instálalo ejecutando:"
    echo "   sudo apt install $PYTHON_VERSION"
    exit 1
else
    echo "   $PYTHON_VERSION detectado."
fi

# Verificar pkg-config (Necesario para mysqlclient)
if ! command -v pkg-config &> /dev/null; then
    echo -e "${RED}ERROR CRÍTICO: Faltan librerías de desarrollo.${NC}"
    echo "El conector MySQL no se podrá instalar."
    echo "Ejecuta:"
    echo "   sudo apt-get update && sudo apt-get install python3-dev default-libmysqlclient-dev build-essential pkg-config"
    exit 1
else
    echo "   Librerías de desarrollo detectadas."
fi

# --- ¡NUEVA VERIFICACIÓN! Módulo venv ---
# Intentamos importar el módulo venv. Si falla, falta el paquete.
$PYTHON_VERSION -c "import venv" 2>/dev/null
if [ $? -ne 0 ]; then
    echo -e "${RED}ERROR CRÍTICO: El módulo 'venv' no está instalado.${NC}"
    echo "Aunque tienes Python, te falta la herramienta para entornos virtuales."
    echo ""
    echo "POR FAVOR, EJECUTA ESTE COMANDO:"
    echo "   sudo apt-get install ${PYTHON_VERSION}-venv"
    exit 1
fi
# -----------------------------------------

# [PASO 2] Crear el entorno virtual
echo ""
echo "[2/4] Creando entorno virtual en ./$VENV_NAME/..."

# Si ya existe, lo borramos para una instalación limpia
if [ -d "$VENV_NAME" ]; then
    echo "   El entorno virtual ya existe. Recreándolo..."
    rm -rf "$VENV_NAME"
fi

$PYTHON_VERSION -m venv $VENV_NAME

if [ $? -ne 0 ]; then
    echo -e "${RED}ERROR: No se pudo crear el entorno virtual.${NC}"
    echo "Revisa los permisos de la carpeta o si tienes espacio en disco."
    exit 1
fi

# [PASO 3] Activar el entorno virtual
echo "[3/4] Activando entorno virtual..."
source $VENV_NAME/bin/activate

# [PASO 4] Instalar dependencias
echo "[4/4] Instalando dependencias desde requirements.txt..."
echo "      (Esto puede tardar unos minutos compilando mysqlclient)"

pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo -e "${RED}ERROR: Falló la instalación de dependencias.${NC}"
    echo "Revisa si tienes instaladas las librerías del sistema (libmysqlclient-dev)."
    exit 1
fi

echo ""
echo -e "${GREEN}========================================================${NC}"
echo -e "${GREEN}   ¡Instalación completada exitosamente!                ${NC}"
echo -e "${GREEN}========================================================${NC}"
echo ""
echo "Próximos pasos:"
echo "1. Mueve los archivos .env y la llave .json a la raíz."
echo "2. Inicia el Cloud SQL Proxy en otra terminal."
echo "3. Activa el entorno: source $VENV_NAME/bin/activate"
echo "4. Carga datos: ./seed.sh"
echo "5. Ejecuta: python mantenedor_nuam/manage.py runserver"
