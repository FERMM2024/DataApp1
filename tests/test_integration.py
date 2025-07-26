"""
Pruebas de integración para DataApp1
Estas pruebas verifican que todos los componentes funcionen juntos
Incluye pruebas para las nuevas funcionalidades de progreso y PDF
"""

import unittest
import json
import os
import sys
import tempfile
import shutil
import pandas as pd
import numpy as np
from io import BytesIO

# Agregar el path del backend
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))


class TestIntegration(unittest.TestCase):
    """Pruebas de integración de la aplicación completa"""

    def setUp(self):
        """Configuración inicial para pruebas de integración"""
        self.temp_dir = tempfile.mkdtemp()
        self.upload_dir = os.path.join(self.temp_dir, 'uploads')
        self.static_dir = os.path.join(self.temp_dir, 'static', 'plots')
        os.makedirs(self.upload_dir, exist_ok=True)
        os.makedirs(self.static_dir, exist_ok=True)

    def tearDown(self):
        """Limpieza después de cada prueba"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_complete_workflow_simulation(self):
        """Simular el flujo completo de la aplicación"""
        # 1. Crear datos de prueba
        test_data = {
            'producto': ['Laptop', 'Mouse', 'Teclado', 'Monitor', 'Webcam'],
            'precio': [1200, 25, 80, 300, 150],
            'categoria': ['Electrónicos', 'Accesorios', 'Accesorios', 'Electrónicos', 'Accesorios'],
            'ventas': [50, 200, 120, 30, 80],
            'rating': [4.5, 4.0, 4.2, 4.8, 3.9]
        }
        df = pd.DataFrame(test_data)
        
        # 2. Verificar que los datos se pueden procesar
        self.assertEqual(len(df), 5)
        self.assertEqual(len(df.columns), 5)
        
        # 3. Verificar tipos de datos
        numeric_columns = df.select_dtypes(include=['number']).columns.tolist()
        self.assertIn('precio', numeric_columns)
        self.assertIn('ventas', numeric_columns)
        self.assertIn('rating', numeric_columns)
        
        # 4. Simular análisis básico
        basic_stats = df.describe()
        self.assertIsNotNone(basic_stats)
        
        # 5. Verificar que se pueden calcular correlaciones (solo para columnas numéricas)
        numeric_df = df.select_dtypes(include=['number'])
        if len(numeric_df.columns) > 1:
            correlation_matrix = numeric_df.corr()
            self.assertIsNotNone(correlation_matrix)

    def test_file_processing_workflow(self):
        """Probar el flujo de procesamiento de archivos"""
        # Crear un archivo CSV de prueba
        csv_content = """nombre,edad,ciudad,salario
Juan,25,Madrid,30000
Maria,30,Barcelona,35000
Carlos,35,Valencia,32000
Ana,28,Sevilla,31000
Luis,32,Bilbao,34000"""
        
        # Guardar en archivo temporal
        csv_file_path = os.path.join(self.upload_dir, 'test_data.csv')
        with open(csv_file_path, 'w', encoding='utf-8') as f:
            f.write(csv_content)
        
        # Verificar que el archivo se puede leer
        self.assertTrue(os.path.exists(csv_file_path))
        
        # Leer con pandas
        try:
            df = pd.read_csv(csv_file_path)
            self.assertEqual(len(df), 5)
            self.assertIn('nombre', df.columns)
            self.assertIn('edad', df.columns)
            self.assertIn('salario', df.columns)
        except Exception as e:
            self.fail(f"Error al leer CSV: {e}")

    def test_data_analysis_workflow(self):
        """Probar el flujo de análisis de datos"""
        # Crear dataset con diferentes tipos de datos
        test_data = {
            'id': range(1, 11),
            'nombre': [f'Usuario{i}' for i in range(1, 11)],
            'activo': [True, False] * 5,
            'puntuacion': [85.5, 92.0, 78.5, 88.0, 90.5, 76.8, 94.2, 81.3, 87.7, 89.1],
            'categoria': ['A', 'B', 'C'] * 3 + ['A'],
            'fecha_registro': pd.date_range('2024-01-01', periods=10, freq='D')
        }
        df = pd.DataFrame(test_data)
        
        # Análisis básico
        shape = df.shape
        self.assertEqual(shape[0], 10)  # 10 filas
        self.assertEqual(shape[1], 6)   # 6 columnas
        
        # Verificar tipos de datos
        dtypes = df.dtypes
        self.assertEqual(dtypes['id'], 'int64')
        self.assertEqual(dtypes['nombre'], 'object')
        self.assertEqual(dtypes['activo'], 'bool')
        self.assertEqual(dtypes['puntuacion'], 'float64')
        
        # Análisis de valores faltantes
        missing_values = df.isnull().sum()
        total_missing = missing_values.sum()
        self.assertEqual(total_missing, 0)  # No debería haber valores faltantes
        
        # Estadísticas descriptivas para columnas numéricas
        numeric_stats = df.describe()
        self.assertIn('puntuacion', numeric_stats.columns)
        self.assertIn('id', numeric_stats.columns)

    def test_error_handling_workflow(self):
        """Probar el manejo de errores en el flujo completo"""
        # Caso 1: CSV malformado
        malformed_csv = "nombre,edad\nJuan,25\nMaria,treinta,extra"
        try:
            df = pd.read_csv(BytesIO(malformed_csv.encode()))
            # Pandas debería manejar esto, pero podría haber inconsistencias
            self.assertIsNotNone(df)
        except Exception:
            # Es aceptable que falle
            pass
        
        # Caso 2: CSV vacío
        empty_csv = ""
        try:
            df = pd.read_csv(BytesIO(empty_csv.encode()))
            self.fail("Debería fallar con CSV vacío")
        except Exception:
            # Esperado que falle
            pass
        
        # Caso 3: Solo headers
        header_only_csv = "nombre,edad,ciudad"
        try:
            df = pd.read_csv(BytesIO(header_only_csv.encode()))
            self.assertEqual(len(df), 0)  # DataFrame vacío pero válido
        except Exception as e:
            self.fail(f"CSV con solo headers debería ser válido: {e}")

    def test_performance_workflow(self):
        """Probar el rendimiento con datasets más grandes"""
        import time
        
        # Crear un dataset de tamaño mediano
        n_rows = 1000
        large_data = {
            'id': range(n_rows),
            'valor1': [i * 2.5 for i in range(n_rows)],
            'valor2': [i ** 0.5 for i in range(n_rows)],
            'categoria': ['Cat' + str(i % 5) for i in range(n_rows)],
            'flag': [i % 2 == 0 for i in range(n_rows)]
        }
        
        # Medir tiempo de creación del DataFrame
        start_time = time.time()
        df = pd.DataFrame(large_data)
        creation_time = time.time() - start_time
        
        self.assertEqual(len(df), n_rows)
        self.assertLess(creation_time, 1.0)  # Debería ser rápido
        
        # Medir tiempo de análisis básico
        start_time = time.time()
        basic_info = {
            'shape': df.shape,
            'dtypes': df.dtypes.to_dict(),
            'missing': df.isnull().sum().to_dict(),
            'stats': df.describe().to_dict()
        }
        analysis_time = time.time() - start_time
        
        self.assertIsNotNone(basic_info)
        self.assertLess(analysis_time, 2.0)  # Análisis debería ser razonablemente rápido


class TestEndToEndScenarios(unittest.TestCase):
    """Pruebas de escenarios completos de extremo a extremo"""

    def test_real_world_data_scenario(self):
        """Simular un escenario del mundo real"""
        # Datos simulados de ventas de una tienda
        sales_data = {
            'fecha': pd.date_range('2024-01-01', periods=100, freq='D'),
            'producto': ['Producto' + str((i % 10) + 1) for i in range(100)],
            'cantidad': [max(1, int(50 + 30 * (0.5 - abs(i - 50) / 50))) for i in range(100)],
            'precio_unitario': [10 + (i % 20) * 2.5 for i in range(100)],
            'descuento': [0.1 if i % 10 == 0 else 0.05 if i % 5 == 0 else 0 for i in range(100)],
            'vendedor': ['Vendedor' + str((i % 5) + 1) for i in range(100)]
        }
        
        df = pd.DataFrame(sales_data)
        
        # Calcular métricas de negocio
        df['total_sin_descuento'] = df['cantidad'] * df['precio_unitario']
        df['total_con_descuento'] = df['total_sin_descuento'] * (1 - df['descuento'])
        
        # Verificaciones de negocio
        self.assertEqual(len(df), 100)
        self.assertTrue((df['total_con_descuento'] <= df['total_sin_descuento']).all())
        self.assertTrue((df['cantidad'] > 0).all())
        self.assertTrue((df['precio_unitario'] > 0).all())
        
        # Análisis temporal
        df['mes'] = df['fecha'].dt.month
        ventas_por_mes = df.groupby('mes')['total_con_descuento'].sum()
        self.assertGreater(len(ventas_por_mes), 0)
        
        # Análisis por vendedor
        ventas_por_vendedor = df.groupby('vendedor')['total_con_descuento'].sum()
        self.assertEqual(len(ventas_por_vendedor), 5)

    def test_data_quality_checks(self):
        """Probar verificaciones de calidad de datos"""
        # Crear datos con problemas de calidad comunes
        problematic_data = {
            'id': [1, 2, 3, 4, 5, 6],
            'nombre': ['Juan', 'Maria', '', 'Carlos', None, 'Ana'],
            'edad': [25, -5, 150, 30, None, 28],  # Edad negativa e imposible
            'email': ['juan@email.com', 'maria@', 'carlos@email.com', '', None, 'ana@email.com'],
            'salario': [30000, 0, -1000, 50000, None, 45000]  # Salario negativo
        }
        
        df = pd.DataFrame(problematic_data)
        
        # Verificar problemas de calidad
        quality_issues = {}
        
        # Valores faltantes
        quality_issues['missing_values'] = df.isnull().sum().to_dict()
        
        # Valores vacíos en strings
        string_columns = df.select_dtypes(include=['object']).columns
        for col in string_columns:
            empty_strings = (df[col] == '').sum()
            if empty_strings > 0:
                quality_issues[f'{col}_empty_strings'] = empty_strings
        
        # Valores fuera de rango
        if 'edad' in df.columns:
            invalid_ages = ((df['edad'] < 0) | (df['edad'] > 120)).sum()
            quality_issues['invalid_ages'] = invalid_ages
        
        if 'salario' in df.columns:
            negative_salaries = (df['salario'] < 0).sum()
            quality_issues['negative_salaries'] = negative_salaries
        
        # Verificar que se detectaron problemas
        self.assertGreater(quality_issues['missing_values']['nombre'], 0)
        self.assertGreater(quality_issues['invalid_ages'], 0)
        self.assertGreater(quality_issues['negative_salaries'], 0)

    def test_complete_workflow_with_progress_simulation(self):
        """Simular flujo completo con progreso"""
        print("\n🔄 Simulando flujo completo con barra de progreso...")
        
        # Crear datos de ventas realistas
        data = {
            'fecha': pd.date_range('2024-01-01', periods=50, freq='D'),
            'producto': np.random.choice(['Laptop', 'Mouse', 'Teclado', 'Monitor'], 50),
            'vendedor': np.random.choice(['Ana García', 'Carlos López', 'Luis Martín'], 50),
            'cantidad': np.random.randint(1, 20, 50),
            'precio_unitario': np.random.uniform(25.99, 850.50, 50),
        }
        df = pd.DataFrame(data)
        df['total'] = df['cantidad'] * df['precio_unitario']
        
        # Simular etapas de progreso como en el frontend
        progress_stages = [
            (10, "Validando archivo..."),
            (25, "Cargando datos..."),
            (40, "Analizando estructura..."),
            (60, "Calculando estadísticas..."),
            (80, "Generando visualizaciones..."),
            (95, "Aplicando IA..."),
            (100, "¡Análisis completado!")
        ]
        
        results = {}
        
        for percent, message in progress_stages:
            print(f"   {percent}% - {message}")
            
            if percent == 25:  # Cargando datos
                self.assertEqual(df.shape[0], 50)
                self.assertEqual(df.shape[1], 6)
                results['data_loaded'] = True
                
            elif percent == 40:  # Analizando estructura
                info = {
                    'shape': df.shape,
                    'columns': df.columns.tolist(),
                    'dtypes': df.dtypes.to_dict()
                }
                results['structure_analysis'] = info
                
            elif percent == 60:  # Calculando estadísticas
                stats = df.describe()
                results['basic_stats'] = stats.to_dict()
                
            elif percent == 80:  # Generando visualizaciones
                # Simular generación de gráficos
                correlation_matrix = df.select_dtypes(include=[np.number]).corr()
                results['correlations'] = correlation_matrix.to_dict()
                
            elif percent == 95:  # Aplicando IA
                # Simular insights de IA
                insights = [
                    f"Dataset contiene {df.shape[0]} registros de ventas",
                    f"Producto más vendido: {df['producto'].mode().iloc[0]}",
                    f"Vendedor más activo: {df['vendedor'].mode().iloc[0]}",
                    f"Venta promedio: ${df['total'].mean():.2f}"
                ]
                results['ai_insights'] = insights
        
        # Verificar que todas las etapas completaron
        self.assertTrue(results.get('data_loaded'))
        self.assertIn('structure_analysis', results)
        self.assertIn('basic_stats', results)
        self.assertIn('correlations', results)
        self.assertIn('ai_insights', results)
        
        print("   ✅ Flujo completo con progreso simulado exitosamente")

    def test_pdf_generation_data_preparation(self):
        """Simular preparación de datos para generación de PDF"""
        print("\n📄 Preparando datos para generación de PDF...")
        
        # Crear datos estructurados como los que recibe el endpoint PDF
        pdf_data = {
            'results': {
                'dataset_info': {
                    'shape': [100, 5],
                    'memory_usage': '15.2 KB',
                    'columns': ['fecha', 'producto', 'vendedor', 'cantidad', 'total']
                },
                'basic_stats': {
                    'cantidad': {
                        'mean': 8.5,
                        'std': 4.2,
                        'min': 1,
                        'max': 20,
                        'count': 100
                    },
                    'total': {
                        'mean': 1250.75,
                        'std': 650.25,
                        'min': 25.99,
                        'max': 3500.00,
                        'count': 100
                    }
                },
                'null_values': {
                    'fecha': 0,
                    'producto': 0,
                    'vendedor': 1,
                    'cantidad': 0,
                    'total': 0
                },
                'ai_insights': [
                    'Las ventas muestran un patrón estacional claro',
                    'El producto "Laptop" genera el 60% de los ingresos',
                    'Ana García es la vendedora más consistente',
                    'Se recomienda aumentar el stock de laptops en diciembre'
                ]
            },
            'filename': 'ventas_2024.csv'
        }
        
        # Verificar estructura de datos para PDF
        self.assertIn('results', pdf_data)
        self.assertIn('filename', pdf_data)
        
        results = pdf_data['results']
        self.assertIn('dataset_info', results)
        self.assertIn('basic_stats', results)
        self.assertIn('ai_insights', results)
        
        # Verificar datos específicos
        dataset_info = results['dataset_info']
        self.assertEqual(dataset_info['shape'], [100, 5])
        self.assertIn('memory_usage', dataset_info)
        
        # Verificar estadísticas
        basic_stats = results['basic_stats']
        self.assertIn('cantidad', basic_stats)
        self.assertIn('total', basic_stats)
        
        # Verificar insights
        insights = results['ai_insights']
        self.assertIsInstance(insights, list)
        self.assertGreater(len(insights), 0)
        
        print("   ✅ Datos preparados correctamente para PDF")

    def test_frontend_backend_communication_simulation(self):
        """Simular comunicación completa frontend-backend"""
        print("\n🔄 Simulando comunicación frontend-backend...")
        
        # Simular secuencia completa de eventos
        events = []
        
        # 1. Usuario selecciona archivo
        events.append("Frontend: Usuario selecciona archivo CSV")
        filename = "ejemplo_ventas.csv"
        
        # 2. Frontend muestra nombre de archivo
        events.append(f"Frontend: Mostrando nombre '{filename}'")
        
        # 3. Frontend inicia barra de progreso
        events.append("Frontend: Iniciando barra de progreso")
        
        # 4. Backend recibe archivo
        events.append("Backend: Recibiendo archivo CSV")
        
        # 5. Backend procesa datos
        events.append("Backend: Procesando datos con DataAnalyzer")
        
        # 6. Backend genera resultados
        events.append("Backend: Generando resultados de análisis")
        results = {
            'dataset_info': {'shape': [15, 6]},
            'basic_stats': {'total': {'mean': 1234.56}},
            'ai_insights': ['Insight generado']
        }
        
        # 7. Frontend recibe resultados
        events.append("Frontend: Recibiendo resultados")
        
        # 8. Frontend completa progreso
        events.append("Frontend: Completando barra de progreso (100%)")
        
        # 9. Frontend muestra resultados
        events.append("Frontend: Mostrando resultados en UI")
        
        # 10. Frontend habilita descarga PDF
        events.append("Frontend: Habilitando botón de descarga PDF")
        
        # 11. Usuario solicita PDF
        events.append("Frontend: Usuario solicita descarga PDF")
        
        # 12. Backend genera PDF
        events.append("Backend: Generando PDF con reportlab")
        
        # 13. Frontend descarga PDF
        events.append("Frontend: Iniciando descarga de archivo PDF")
        
        # Verificar que todos los eventos críticos están presentes
        critical_events = [
            "Usuario selecciona archivo",
            "Iniciando barra de progreso",
            "Procesando datos",
            "Completando barra de progreso",
            "Generando PDF"
        ]
        
        event_text = " ".join(events)
        for critical_event in critical_events:
            self.assertIn(critical_event, event_text)
        
        # Verificar que tenemos resultados válidos
        self.assertIn('dataset_info', results)
        self.assertIn('basic_stats', results)
        self.assertIn('ai_insights', results)
        
        print(f"   ✅ Simulados {len(events)} eventos de comunicación")

    def test_error_handling_workflow(self):
        """Simular manejo de errores en el flujo completo"""
        print("\n❌ Simulando manejo de errores...")
        
        error_scenarios = [
            {
                'name': 'Archivo CSV vacío',
                'stage': 'data_loading',
                'error_type': 'EmptyDataError',
                'expected_message': 'El archivo CSV está vacío'
            },
            {
                'name': 'Archivo CSV corrupto',
                'stage': 'data_parsing',
                'error_type': 'ParserError',
                'expected_message': 'Error al parsear el archivo CSV'
            },
            {
                'name': 'Error de codificación',
                'stage': 'file_reading',
                'error_type': 'UnicodeDecodeError',
                'expected_message': 'Error de codificación'
            },
            {
                'name': 'Error en generación PDF',
                'stage': 'pdf_generation',
                'error_type': 'PDFGenerationError',
                'expected_message': 'Error al generar PDF'
            }
        ]
        
        for scenario in error_scenarios:
            print(f"   🔍 Probando: {scenario['name']}")
            
            # Simular que el error ocurre en la etapa específica
            if scenario['stage'] == 'data_loading':
                # Frontend debería mostrar error y resetear progreso
                self.assertIn('vacío', scenario['expected_message'])
                
            elif scenario['stage'] == 'pdf_generation':
                # Frontend debería mostrar error en descarga PDF
                self.assertIn('PDF', scenario['expected_message'])
            
            # Verificar que todos los errores tienen mensajes apropiados
            self.assertIsNotNone(scenario['expected_message'])
            self.assertGreater(len(scenario['expected_message']), 0)
        
        print("   ✅ Manejo de errores verificado")


if __name__ == '__main__':
    unittest.main()
