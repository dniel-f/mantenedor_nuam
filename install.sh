#!/bin/bash
# install.sh
# Script de instalación automático para el Mantenedor NUAM en Linux

echo "--- Iniciando la instalación del Mantenedor NUAM ---"

# Definir el nombre del entorno virtual
VENV_NAME="venv"
PYTHON_VERSION="python3.13"

# 1. Comprobar si Python 3.13 está instalado
if ! command -v $PYTHON_VERSION &> /dev/null
then
    echo "ERROR: Python 3.13 ($PYTHON_VERSION) no se encuentra."
    echo "Por favor, instala Python 3.13 y vuelve a intentarlo."
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
echo "1. Configura tu archivo .env (copia .env.example)."
echo "2. Configura la base de datos (ver README.md)."
echo "3. Activa el entorno en tu terminal ejecutando:"
echo "   source $VENV_NAME/bin/activate"
echo "4. Ejecuta las migraciones (si es necesario) y corre el servidor."