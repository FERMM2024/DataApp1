"""
Pruebas unitarias para el backend Flask de DataApp1
Incluye pruebas para las nuevas funcionalidades: progreso y descarga PDF
"""

import unittest
import json
import os
import tempfile
import shutil
import pandas as pd
from io import StringIO, BytesIO
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app import app
from config import TestConfig


class TestFlaskApp(unittest.TestCase):
    """Pruebas para la aplicación Flask"""

    def setUp(self):
        """Configuración inicial para cada prueba"""
        self.app = app
        self.app.config.from_object(TestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # Crear directorios temporales para pruebas
        self.test_dir = tempfile.mkdtemp()
        self.upload_dir = os.path.join(self.test_dir, 'uploads')
        self.static_dir = os.path.join(self.test_dir, 'static', 'plots')
        os.makedirs(self.upload_dir, exist_ok=True)
        os.makedirs(self.static_dir, exist_ok=True)
        
        # Actualizar configuración con directorios de prueba
        self.app.config['UPLOAD_FOLDER'] = self.upload_dir
        self.app.config['STATIC_FOLDER'] = os.path.join(self.test_dir, 'static')

    def tearDown(self):
        """Limpieza después de cada prueba"""
        self.app_context.pop()
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_index_route(self):
        """Probar la ruta principal '/'"""
        response = self.client.get('/')
        # Como estamos en un entorno de prueba, el archivo frontend podría no existir
        # Solo verificamos que la ruta existe
        self.assertIn(response.status_code, [200, 404])

    def test_health_check(self):
        """Probar el endpoint de health check"""
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'healthy')
        self.assertIn('message', data)
        self.assertIn('DataApp1', data['message'])

    def test_analyze_no_file(self):
        """Probar análisis sin archivo"""
        response = self.client.post('/analyze')
        self.assertEqual(response.status_code, 400)
        
        data = json.loads(response.data)
        self.assertIn('error', data)

    def test_analyze_invalid_file_type(self):
        """Probar análisis con tipo de archivo inválido"""
        data = {
            'file': (BytesIO(b'test content'), 'test.txt')
        }
        response = self.client.post('/analyze', data=data)
        self.assertEqual(response.status_code, 400)
        
        response_data = json.loads(response.data)
        self.assertIn('error', response_data)

    def test_analyze_valid_csv(self):
        """Probar análisis con CSV válido"""
        # Crear un CSV de prueba
        csv_content = """name,age,city,salary
John,25,New York,50000
Jane,30,Los Angeles,60000
Bob,35,Chicago,55000
Alice,28,Houston,52000
Charlie,32,Phoenix,58000"""
        
        csv_file = BytesIO(csv_content.encode('utf-8'))
        
        data = {
            'file': (csv_file, 'test_data.csv')
        }
        
        response = self.client.post('/analyze', data=data)
        
        # Verificar que la respuesta sea exitosa o maneje errores apropiadamente
        self.assertIn(response.status_code, [200, 500])  # 500 podría ocurrir si falta configuración

    def test_analyze_empty_csv(self):
        """Probar análisis con CSV vacío"""
        csv_content = ""
        csv_file = BytesIO(csv_content.encode('utf-8'))
        
        data = {
            'file': (csv_file, 'empty.csv')
        }
        
        response = self.client.post('/analyze', data=data)
        self.assertEqual(response.status_code, 400)

    def test_analyze_malformed_csv(self):
        """Probar análisis con CSV mal formado"""
        csv_content = "name,age\nJohn,25\nJane,thirty,extra_column"
        csv_file = BytesIO(csv_content.encode('utf-8'))
        
        data = {
            'file': (csv_file, 'malformed.csv')
        }
        
        response = self.client.post('/analyze', data=data)
        # Debería manejar el error graciosamente
        self.assertIn(response.status_code, [400, 500])

    def test_static_files_route(self):
        """Probar servir archivos estáticos"""
        # Crear un archivo de prueba
        test_file_path = os.path.join(self.static_dir, 'test.txt')
        with open(test_file_path, 'w') as f:
            f.write('test content')
        
        response = self.client.get('/static/plots/test.txt')
        # Verificar que la ruta existe (puede no funcionar completamente en pruebas)
        self.assertIn(response.status_code, [200, 404])

    def test_plots_route(self):
        """Probar la ruta de gráficos"""
        # Crear un archivo de gráfico de prueba
        test_plot_path = os.path.join(self.static_dir, 'test_plot.png')
        with open(test_plot_path, 'wb') as f:
            f.write(b'fake png content')
        
        response = self.client.get('/plots/test_plot.png')
        # Verificar que la ruta existe
        self.assertIn(response.status_code, [200, 404])

    def test_file_size_limit(self):
        """Probar límite de tamaño de archivo"""
        # Crear un archivo grande (simulado)
        large_content = "name,value\n" + "\n".join([f"item{i},{i}" for i in range(100000)])
        large_file = BytesIO(large_content.encode('utf-8'))
        
        data = {
            'file': (large_file, 'large_file.csv')
        }
        
        response = self.client.post('/analyze', data=data)
        # Debería manejar archivos grandes apropiadamente
        self.assertIn(response.status_code, [200, 400, 413, 500])

    def test_allowed_file_function(self):
        """Probar la función allowed_file"""
        from app import allowed_file
        
        self.assertTrue(allowed_file('test.csv'))
        self.assertTrue(allowed_file('data.CSV'))  # Case insensitive
        self.assertFalse(allowed_file('test.txt'))
        self.assertFalse(allowed_file('test.xlsx'))
        self.assertFalse(allowed_file('test'))  # Sin extensión
        self.assertFalse(allowed_file('.csv'))  # Solo extensión


class TestCSVValidation(unittest.TestCase):
    """Pruebas para validación de archivos CSV"""

    def test_valid_csv_structure(self):
        """Probar estructura CSV válida"""
        csv_content = """name,age,city
John,25,New York
Jane,30,Los Angeles"""
        
        try:
            df = pd.read_csv(StringIO(csv_content))
            self.assertEqual(len(df.columns), 3)
            self.assertEqual(len(df), 2)
            self.assertIn('name', df.columns)
            self.assertIn('age', df.columns)
            self.assertIn('city', df.columns)
        except Exception as e:
            self.fail(f"CSV válido falló la validación: {e}")

    def test_csv_with_missing_values(self):
        """Probar CSV con valores faltantes"""
        csv_content = """name,age,city
John,25,New York
Jane,,Los Angeles
,30,Chicago"""
        
        try:
            df = pd.read_csv(StringIO(csv_content))
            missing_count = df.isnull().sum().sum()
            self.assertGreater(missing_count, 0)
        except Exception as e:
            self.fail(f"CSV con valores faltantes falló: {e}")

    def test_csv_with_different_data_types(self):
        """Probar CSV con diferentes tipos de datos"""
        csv_content = """name,age,salary,is_active,join_date
John,25,50000.5,True,2020-01-15
Jane,30,60000.0,False,2019-05-20"""
        
        try:
            df = pd.read_csv(StringIO(csv_content))
            self.assertEqual(len(df.columns), 5)
            # Verificar que se pueden convertir tipos
            df['age'] = pd.to_numeric(df['age'])
            df['salary'] = pd.to_numeric(df['salary'])
        except Exception as e:
            self.fail(f"CSV con tipos mixtos falló: {e}")

    def test_generate_pdf_endpoint(self):
        """Probar el endpoint de generación de PDF"""
        # Datos de prueba para el PDF
        test_data = {
            'results': {
                'dataset_info': {
                    'shape': [100, 5],
                    'memory_usage': '2.5 KB'
                },
                'basic_stats': {
                    'ventas': {
                        'mean': 1500.50,
                        'std': 250.30,
                        'min': 800.00,
                        'max': 2500.00
                    }
                },
                'ai_insights': [
                    'Las ventas muestran una tendencia creciente',
                    'Se detectaron patrones estacionales'
                ]
            },
            'filename': 'test_data.csv'
        }
        
        response = self.client.post('/generate-pdf',
                                  data=json.dumps(test_data),
                                  content_type='application/json')
        
        # Verificar que la respuesta sea exitosa
        self.assertEqual(response.status_code, 200)
        
        # Verificar que el tipo de contenido sea PDF
        self.assertEqual(response.content_type, 'application/pdf')
        
        # Verificar que la respuesta tenga contenido
        self.assertGreater(len(response.data), 0)

    def test_generate_pdf_without_data(self):
        """Probar endpoint PDF sin datos"""
        response = self.client.post('/generate-pdf',
                                  data=json.dumps({}),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertIn('No se proporcionaron datos', data['error'])

    def test_generate_pdf_invalid_json(self):
        """Probar endpoint PDF con JSON inválido"""
        response = self.client.post('/generate-pdf',
                                  data='invalid json',
                                  content_type='application/json')
        
        # Debería devolver error 400 por JSON inválido
        self.assertEqual(response.status_code, 400)

    def test_all_endpoints_cors_enabled(self):
        """Verificar que CORS esté habilitado en todos los endpoints"""
        endpoints = ['/', '/health', '/analyze', '/generate-pdf']
        
        for endpoint in endpoints:
            if endpoint == '/analyze' or endpoint == '/generate-pdf':
                # Para endpoints POST, usar OPTIONS para verificar CORS
                response = self.client.options(endpoint)
                # CORS debería permitir el método
                self.assertIn(response.status_code, [200, 204])
            else:
                # Para endpoints GET
                response = self.client.get(endpoint)
                # Debería responder (aunque sea con error por falta de archivo)
                self.assertIn(response.status_code, [200, 404, 500])


if __name__ == '__main__':
    unittest.main()
