#!/bin/bash
# install.sh
# Script de instalación automático para el Mantenedor NUAM en Linux
# Incluye verificaciones de dependencias del sistema operativo.

echo "========================================================"
echo "   Iniciando la instalación del Mantenedor NUAM"
echo "========================================================"

# Definir variables de configuración
VENV_NAME="venv"
PYTHON_VERSION="python3.11"

# --------------------------------------------------------
# 1. Verificaciones de Prerrequisitos del Sistema
# --------------------------------------------------------
echo "[1/4] Verificando dependencias del sistema..."

# Verificar si Python 3.11 está instalado
if ! command -v $PYTHON_VERSION &> /dev/null
then
    echo "   ERROR CRÍTICO: Python 3.11 ($PYTHON_VERSION) no se encuentra."
    echo "   Por favor, instálalo ejecutando:"
    echo "   sudo apt install python3.11 python3.11-venv"
    exit 1
fi
echo "   ✅ Python 3.11 detectado."

# Verificar pkg-config (Indicador de que faltan herramientas de compilación para MySQL)
if ! command -v pkg-config &> /dev/null; then
    echo "   ERROR CRÍTICO: Faltan librerías de desarrollo del sistema."
    echo "   El conector de base de datos (mysqlclient) fallará sin ellas."
    echo ""
    echo "   >>> SOLUCIÓN: Ejecuta este comando antes de continuar:"
    echo "   sudo apt-get update && sudo apt-get install python3-dev default-libmysqlclient-dev build-essential pkg-config"
    echo ""
    exit 1
fi
echo "   ✅ Librerías de desarrollo detectadas."

# --------------------------------------------------------
# 2. Crear el Entorno Virtual
# --------------------------------------------------------
echo ""
echo "[2/4] Creando entorno virtual en ./$VENV_NAME/..."

$PYTHON_VERSION -m venv $VENV_NAME

if [ $? -ne 0 ]; then
    echo "   ERROR: No se pudo crear el entorno virtual."
    echo "   Asegúrate de tener 'python3.11-venv' instalado."
    exit 1
fi

# --------------------------------------------------------
# 3. Activar el Entorno Virtual
# --------------------------------------------------------
echo "[3/4] Activando entorno virtual..."
source $VENV_NAME/bin/activate

# --------------------------------------------------------
# 4. Instalar Dependencias de Python
# --------------------------------------------------------
echo "[4/4] Instalando dependencias desde requirements.txt..."

# Actualizar pip primero para evitar advertencias
pip install --upgrade pip

# Instalar los paquetes
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "   ERROR: Falló la instalación de dependencias de Python."
    echo "   Es probable que falten librerías del sistema para compilar mysqlclient o cryptography."
    exit 1
fi

# --------------------------------------------------------
# Finalización
# --------------------------------------------------------
echo ""
echo "========================================================"
echo "         ¡INSTALACIÓN COMPLETADA EXITOSAMENTE!"
echo "========================================================"
echo ""
echo "PRÓXIMOS PASOS PARA EJECUTAR EL PROYECTO:"
echo "1. Mueve tus archivos secretos (.env y la llave .json) a la raíz del proyecto."
echo "2. Abre una NUEVA terminal e inicia el Cloud SQL Proxy."
echo "3. En esta terminal, activa el entorno:"
echo "   source $VENV_NAME/bin/activate"
echo "4. Carga los datos de prueba:"
echo "   ./seed.sh"
echo "5. Inicia el servidor:"
echo "   python mantenedor_nuam/manage.py runserver"
echo ""