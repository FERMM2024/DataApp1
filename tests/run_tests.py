"""
Suite principal de pruebas para DataApp1
Ejecuta todas las pruebas de la aplicación
"""

import unittest
import sys
import os
from io import StringIO

# Agregar el directorio del proyecto al path
project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'backend'))


def run_test_suite():
    """Ejecutar todas las pruebas"""
    # Crear un loader de pruebas
    loader = unittest.TestLoader()
    
    # Descubrir y cargar todas las pruebas
    test_dir = os.path.dirname(__file__)
    suite = loader.discover(test_dir, pattern='test_*.py')
    
    # Configurar el runner
    stream = StringIO()
    runner = unittest.TextTestRunner(
        stream=stream,
        verbosity=2,
        buffer=True
    )
    
    # Ejecutar las pruebas
    print("🧪 Ejecutando suite completa de pruebas para DataApp1...\n")
    result = runner.run(suite)
    
    # Obtener los resultados
    output = stream.getvalue()
    
    # Mostrar resumen
    print("=" * 70)
    print("📊 RESUMEN DE PRUEBAS")
    print("=" * 70)
    
    total_tests = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    skipped = len(result.skipped) if hasattr(result, 'skipped') else 0
    passed = total_tests - failures - errors - skipped
    
    print(f"✅ Pruebas ejecutadas: {total_tests}")
    print(f"🎉 Exitosas: {passed}")
    print(f"❌ Fallidas: {failures}")
    print(f"🚨 Errores: {errors}")
    print(f"⏭️  Omitidas: {skipped}")
    
    if failures > 0:
        print(f"\n❌ FALLAS ({failures}):")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback.split('AssertionError: ')[-1].split('\n')[0]}")
    
    if errors > 0:
        print(f"\n🚨 ERRORES ({errors}):")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback.split('\n')[-2]}")
    
    if hasattr(result, 'skipped') and skipped > 0:
        print(f"\n⏭️  OMITIDAS ({skipped}):")
        for test, reason in result.skipped:
            print(f"  - {test}: {reason}")
    
    # Calcular porcentaje de éxito
    if total_tests > 0:
        success_rate = (passed / total_tests) * 100
        print(f"\n📈 Tasa de éxito: {success_rate:.1f}%")
        
        if success_rate >= 80:
            print("🎯 ¡Excelente! La aplicación pasa la mayoría de las pruebas.")
        elif success_rate >= 60:
            print("⚠️  Aceptable, pero hay áreas que necesitan mejoras.")
        else:
            print("🔧 Se requieren correcciones significativas.")
    
    print("\n" + "=" * 70)
    
    return result


def run_specific_test_module(module_name):
    """Ejecutar un módulo específico de pruebas"""
    print(f"🧪 Ejecutando pruebas de {module_name}...\n")
    
    try:
        # Importar el módulo de pruebas
        test_module = __import__(module_name)
        
        # Crear suite
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromModule(test_module)
        
        # Ejecutar
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        return result
    
    except ImportError as e:
        print(f"❌ Error al importar {module_name}: {e}")
        return None


def generate_test_report():
    """Generar un reporte detallado de las pruebas"""
    report_file = os.path.join(os.path.dirname(__file__), '..', 'test_report.md')
    
    # Ejecutar pruebas
    result = run_test_suite()
    
    # Generar reporte en Markdown
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("# 📋 Reporte de Pruebas - DataApp1\n\n")
        f.write(f"**Fecha:** {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Resumen
        total_tests = result.testsRun
        failures = len(result.failures)
        errors = len(result.errors)
        skipped = len(result.skipped) if hasattr(result, 'skipped') else 0
        passed = total_tests - failures - errors - skipped
        
        f.write("## 📊 Resumen\n\n")
        f.write(f"- **Total de pruebas:** {total_tests}\n")
        f.write(f"- **Exitosas:** {passed} ✅\n")
        f.write(f"- **Fallidas:** {failures} ❌\n")
        f.write(f"- **Errores:** {errors} 🚨\n")
        f.write(f"- **Omitidas:** {skipped} ⏭️\n\n")
        
        if total_tests > 0:
            success_rate = (passed / total_tests) * 100
            f.write(f"**Tasa de éxito:** {success_rate:.1f}%\n\n")
        
        # Detalles de fallas
        if failures > 0:
            f.write("## ❌ Pruebas Fallidas\n\n")
            for test, traceback in result.failures:
                f.write(f"### {test}\n")
                f.write(f"```\n{traceback}\n```\n\n")
        
        # Detalles de errores
        if errors > 0:
            f.write("## 🚨 Errores\n\n")
            for test, traceback in result.errors:
                f.write(f"### {test}\n")
                f.write(f"```\n{traceback}\n```\n\n")
        
        # Pruebas omitidas
        if hasattr(result, 'skipped') and skipped > 0:
            f.write("## ⏭️ Pruebas Omitidas\n\n")
            for test, reason in result.skipped:
                f.write(f"- **{test}:** {reason}\n")
            f.write("\n")
        
        # Recomendaciones
        f.write("## 💡 Recomendaciones\n\n")
        
        if success_rate >= 90:
            f.write("🎉 **Excelente trabajo!** La aplicación tiene una cobertura de pruebas muy buena.\n\n")
        elif success_rate >= 70:
            f.write("👍 **Buen trabajo.** Considera revisar las pruebas fallidas para mejorar.\n\n")
        else:
            f.write("🔧 **Necesita trabajo.** Se recomienda revisar y corregir las pruebas fallidas.\n\n")
        
        f.write("### Próximos pasos:\n")
        f.write("1. Revisar y corregir pruebas fallidas\n")
        f.write("2. Agregar más casos de prueba si es necesario\n")
        f.write("3. Verificar cobertura de código\n")
        f.write("4. Ejecutar pruebas de rendimiento\n\n")
        
        f.write("---\n")
        f.write("*Reporte generado automáticamente por el sistema de pruebas de DataApp1*\n")
    
    print(f"📝 Reporte guardado en: {report_file}")
    return report_file


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Ejecutar pruebas de DataApp1')
    parser.add_argument('--module', '-m', help='Ejecutar un módulo específico de pruebas')
    parser.add_argument('--report', '-r', action='store_true', help='Generar reporte de pruebas')
    parser.add_argument('--verbose', '-v', action='store_true', help='Salida detallada')
    
    args = parser.parse_args()
    
    if args.module:
        run_specific_test_module(args.module)
    elif args.report:
        generate_test_report()
    else:
        run_test_suite()
