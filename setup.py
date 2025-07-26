#!/usr/bin/env python3
"""
Setup script para DataApp1 - Análisis Exploratorio de Datos
Instala dependencias y configura el entorno
"""

import subprocess
import sys
import os

def run_command(command, description):
    """Ejecutar comando con manejo de errores"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completado")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error en {description}: {e.stderr}")
        return False

def main():
    """Función principal de setup"""
    print("🚀 DataApp1 - Setup e Instalación")
    print("=" * 50)
    
    # Verificar Python
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
        print("❌ Se requiere Python 3.8 o superior")
        sys.exit(1)
    
    print(f"✅ Python {python_version.major}.{python_version.minor}.{python_version.micro} detectado")
    
    # Crear entorno virtual
    if not os.path.exists("venv"):
        if not run_command("python -m venv venv", "Creando entorno virtual"):
            print("❌ Error al crear entorno virtual")
            sys.exit(1)
    else:
        print("✅ Entorno virtual ya existe")
    
    # Activar entorno virtual e instalar dependencias
    if sys.platform == "win32":
        activate_cmd = "venv\\Scripts\\activate"
        pip_cmd = "venv\\Scripts\\pip"
    else:
        activate_cmd = "source venv/bin/activate"
        pip_cmd = "venv/bin/pip"
    
    # Instalar dependencias
    install_commands = [
        f"{pip_cmd} install --upgrade pip",
        f"{pip_cmd} install -r backend/requirements.txt"
    ]
    
    for cmd in install_commands:
        if not run_command(cmd, f"Ejecutando: {cmd}"):
            print("❌ Error durante la instalación")
            sys.exit(1)
    
    # Crear directorios necesarios
    directories = ["uploads", "static/plots"]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ Directorio {directory} creado/verificado")
    
    print("\n🎉 ¡Setup completado exitosamente!")
    print("\n📋 Próximos pasos:")
    print("1. Activar el entorno virtual:")
    if sys.platform == "win32":
        print("   venv\\Scripts\\activate")
    else:
        print("   source venv/bin/activate")
    
    print("2. Ejecutar el backend:")
    print("   cd backend")
    print("   python app.py")
    
    print("3. Abrir frontend/index.html en tu navegador")
    
    print("\n📊 Para usar el Jupyter Notebook:")
    print("   jupyter notebook notebooks/exploratory_analysis.ipynb")

if __name__ == "__main__":
    main()
