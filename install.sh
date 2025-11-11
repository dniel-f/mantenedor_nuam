#!/bin/bash
# install.sh
# Script de instalación automático para el Mantenedor NUAM en Linux

echo "--- Iniciando la instalación del Mantenedor NUAM ---"

# Definir el nombre del entorno virtual
VENV_NAME="venv"
PYTHON_VERSION="python3.11"

# 1. Comprobar si Python 3.11 está instalado
if ! command -v $PYTHON_VERSION &> /dev/null
then
    echo "ERROR: Python 3.11 ($PYTHON_VERSION) no se encuentra."
    echo "Por favor, instala Python 3.11 y vuelve a intentarlo."
    exit 1
fi

# 2. Crear el entorno virtual
echo "Creando entorno virtual en ./$VENV_NAME/..."
$PYTHON_VERSION -m venv $VENV_NAME

if [ $? -ne 0 ]; then
    echo "ERROR: No se pudo crear el entorno virtual."
    exit 1
fi

# 3. Activar el entorno virtual (para este script)
echo "Activando entorno virtual..."
source $VENV_NAME/bin/activate

# 4. Instalar dependencias
echo "Instalando dependencias desde requirements.txt..."
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "ERROR: Falló la instalación de dependencias."
    exit 1
fi

echo ""
echo "--- ¡Instalación completada! ---"
echo ""
echo "Próximos pasos:"
echo "1. Configura tu archivo .env (Sección 2.2 del README)."
echo "2. Inicia el Cloud SQL Proxy (Sección 2.3 del README)."
echo "3. Carga los datos (Sección 3 del README)."
echo "4. Activa el entorno en tu terminal ejecutando:"
echo "   source $VENV_NAME/bin/activate"
echo "5. Corre el servidor (Sección 4 del README)."