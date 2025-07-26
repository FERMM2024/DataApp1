#!/usr/bin/env python3
"""
Script principal para ejecutar todas las pruebas de DataApp1
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def main():
    """Función principal para ejecutar pruebas"""
    print("🧪 DataApp1 - Sistema de Pruebas Completo")
    print("=" * 50)
    
    # Verificar que estamos en el directorio correcto
    if not os.path.exists('backend') or not os.path.exists('tests'):
        print("❌ Error: Ejecuta este script desde el directorio raíz del proyecto")
        sys.exit(1)
    
    # Activar entorno virtual si existe
    venv_path = Path('.venv')
    if venv_path.exists():
        if sys.platform == 'win32':
            python_exe = venv_path / 'Scripts' / 'python.exe'
        else:
            python_exe = venv_path / 'bin' / 'python'
        
        if python_exe.exists():
            print(f"✅ Usando entorno virtual: {python_exe}")
        else:
            python_exe = sys.executable
    else:
        python_exe = sys.executable
    
    # Lista de comandos de prueba
    test_commands = [
        {
            'name': 'Pruebas Unitarias del Backend',
            'cmd': [str(python_exe), '-m', 'pytest', 'tests/test_app.py', '-v'],
            'timeout': 60
        },
        {
            'name': 'Pruebas del Módulo de Análisis',
            'cmd': [str(python_exe), '-m', 'pytest', 'tests/test_data_analysis.py', '-v'],
            'timeout': 120
        },
        {
            'name': 'Pruebas de Integración',
            'cmd': [str(python_exe), '-m', 'pytest', 'tests/test_integration.py', '-v'],
            'timeout': 180
        },
        {
            'name': 'Pruebas del Frontend',
            'cmd': [str(python_exe), '-m', 'pytest', 'tests/test_frontend.py', '-v'],
            'timeout': 60
        },
        {
            'name': 'Pruebas de Rendimiento',
            'cmd': [str(python_exe), '-m', 'pytest', 'tests/test_performance.py', '-v', '-m', 'not slow'],
            'timeout': 300
        }
    ]
    
    # Ejecutar cada grupo de pruebas
    results = {}
    total_start_time = time.time()
    
    for test_group in test_commands:
        print(f"\n🔍 Ejecutando: {test_group['name']}")
        print("-" * 40)
        
        start_time = time.time()
        
        try:
            # Ejecutar comando con timeout
            result = subprocess.run(
                test_group['cmd'],
                timeout=test_group['timeout'],
                capture_output=True,
                text=True
            )
            
            execution_time = time.time() - start_time
            
            if result.returncode == 0:
                print(f"✅ {test_group['name']}: EXITOSO ({execution_time:.2f}s)")
                results[test_group['name']] = {'status': 'EXITOSO', 'time': execution_time}
            else:
                print(f"❌ {test_group['name']}: FALLÓ ({execution_time:.2f}s)")
                print(f"Error: {result.stderr}")
                results[test_group['name']] = {'status': 'FALLÓ', 'time': execution_time, 'error': result.stderr}
        
        except subprocess.TimeoutExpired:
            print(f"⏰ {test_group['name']}: TIMEOUT")
            results[test_group['name']] = {'status': 'TIMEOUT', 'time': test_group['timeout']}
        
        except FileNotFoundError:
            print(f"❌ {test_group['name']}: pytest no encontrado")
            print("💡 Instala pytest: pip install pytest")
            results[test_group['name']] = {'status': 'ERROR', 'error': 'pytest no encontrado'}
    
    # Mostrar resumen final
    total_time = time.time() - total_start_time
    print("\n" + "=" * 50)
    print("📊 RESUMEN FINAL")
    print("=" * 50)
    
    successful = sum(1 for r in results.values() if r['status'] == 'EXITOSO')
    failed = sum(1 for r in results.values() if r['status'] in ['FALLÓ', 'TIMEOUT', 'ERROR'])
    
    print(f"✅ Grupos exitosos: {successful}")
    print(f"❌ Grupos fallidos: {failed}")
    print(f"⏱️  Tiempo total: {total_time:.2f}s")
    
    # Mostrar detalles
    for name, result in results.items():
        status_emoji = {
            'EXITOSO': '✅',
            'FALLÓ': '❌',
            'TIMEOUT': '⏰',
            'ERROR': '🚨'
        }
        emoji = status_emoji.get(result['status'], '❓')
        time_str = f" ({result['time']:.2f}s)" if 'time' in result else ""
        print(f"{emoji} {name}: {result['status']}{time_str}")
    
    print("\n💡 Consejos:")
    print("- Para ver más detalles, ejecuta las pruebas individualmente")
    print("- Para pruebas con cobertura: pytest --cov=backend tests/")
    print("- Para solo pruebas rápidas: pytest -m 'not slow'")
    
    # Script adicional de diagnóstico
    print("\n🔧 Diagnóstico rápido:")
    diagnostic_checks = [
        ("Python", [str(python_exe), "--version"]),
        ("Pandas", [str(python_exe), "-c", "import pandas; print(f'pandas {pandas.__version__}')"]),
        ("Flask", [str(python_exe), "-c", "import flask; print(f'Flask {flask.__version__}')"]),
        ("Pytest", [str(python_exe), "-c", "import pytest; print(f'pytest {pytest.__version__}')"]),
    ]
    
    for name, cmd in diagnostic_checks:
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print(f"✅ {name}: {result.stdout.strip()}")
            else:
                print(f"❌ {name}: Error")
        except:
            print(f"❌ {name}: No disponible")
    
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
