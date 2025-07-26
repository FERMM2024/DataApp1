"""
Pruebas de rendimiento para DataApp1
"""

import unittest
import time
import pandas as pd
import numpy as np
import psutil
import os
import sys
from memory_profiler import profile
import tempfile
import shutil

# Agregar el path del backend
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))


class TestPerformance(unittest.TestCase):
    """Pruebas de rendimiento de la aplicación"""

    def setUp(self):
        """Configuración inicial para pruebas de rendimiento"""
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Limpieza después de cada prueba"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_large_dataset_processing(self):
        """Probar procesamiento de datasets grandes"""
        # Crear un dataset grande
        n_rows = 10000
        large_data = {
            'id': range(n_rows),
            'value1': np.random.randn(n_rows),
            'value2': np.random.randn(n_rows),
            'category': np.random.choice(['A', 'B', 'C', 'D', 'E'], n_rows),
            'flag': np.random.choice([True, False], n_rows),
            'score': np.random.uniform(0, 100, n_rows)
        }
        
        # Medir tiempo de creación
        start_time = time.time()
        df = pd.DataFrame(large_data)
        creation_time = time.time() - start_time
        
        # Verificar que se creó correctamente
        self.assertEqual(len(df), n_rows)
        self.assertLess(creation_time, 2.0)  # Debería ser rápido
        
        # Medir tiempo de operaciones básicas
        start_time = time.time()
        _ = df.describe()
        stats_time = time.time() - start_time
        
        start_time = time.time()
        _ = df.corr()
        corr_time = time.time() - start_time
        
        start_time = time.time()
        _ = df.groupby('category')['value1'].mean()
        group_time = time.time() - start_time
        
        # Verificar tiempos razonables
        self.assertLess(stats_time, 1.0)
        self.assertLess(corr_time, 2.0)
        self.assertLess(group_time, 1.0)

    def test_memory_usage(self):
        """Probar uso de memoria"""
        # Obtener uso de memoria inicial
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Crear múltiples DataFrames
        dataframes = []
        for i in range(10):
            data = {
                'col1': np.random.randn(1000),
                'col2': np.random.randn(1000),
                'col3': np.random.choice(['X', 'Y', 'Z'], 1000)
            }
            df = pd.DataFrame(data)
            dataframes.append(df)
        
        # Medir uso de memoria después
        peak_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = peak_memory - initial_memory
        
        # Limpiar DataFrames
        del dataframes
        
        # El aumento de memoria debería ser razonable
        self.assertLess(memory_increase, 100)  # Menos de 100 MB

    def test_csv_reading_performance(self):
        """Probar rendimiento de lectura de CSV"""
        # Crear un CSV grande
        n_rows = 5000
        csv_data = {
            'name': [f'User{i}' for i in range(n_rows)],
            'age': np.random.randint(18, 80, n_rows),
            'salary': np.random.randint(30000, 100000, n_rows),
            'department': np.random.choice(['IT', 'Sales', 'Marketing', 'HR'], n_rows),
            'score': np.random.uniform(0, 100, n_rows)
        }
        
        df = pd.DataFrame(csv_data)
        csv_file = os.path.join(self.temp_dir, 'large_test.csv')
        
        # Medir tiempo de escritura
        start_time = time.time()
        df.to_csv(csv_file, index=False)
        write_time = time.time() - start_time
        
        # Medir tiempo de lectura
        start_time = time.time()
        df_read = pd.read_csv(csv_file)
        read_time = time.time() - start_time
        
        # Verificar que los datos son correctos
        self.assertEqual(len(df_read), n_rows)
        self.assertEqual(len(df_read.columns), 5)
        
        # Verificar tiempos razonables
        self.assertLess(write_time, 5.0)
        self.assertLess(read_time, 3.0)

    def test_concurrent_operations(self):
        """Probar operaciones concurrentes simuladas"""
        import threading
        import queue
        
        results_queue = queue.Queue()
        
        def process_data(data_id):
            """Función para procesar datos en paralelo"""
            start_time = time.time()
            
            # Simular procesamiento de datos
            data = {
                'id': range(1000),
                'value': np.random.randn(1000)
            }
            df = pd.DataFrame(data)
            
            # Operaciones típicas
            _ = df.describe()
            _ = df.mean()
            _ = df.std()
            
            processing_time = time.time() - start_time
            results_queue.put((data_id, processing_time))
        
        # Crear múltiples threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=process_data, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Esperar a que terminen todos los threads
        for thread in threads:
            thread.join()
        
        # Recoger resultados
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())
        
        # Verificar que todos los procesos terminaron
        self.assertEqual(len(results), 5)
        
        # Verificar tiempos razonables
        avg_time = sum(result[1] for result in results) / len(results)
        self.assertLess(avg_time, 2.0)

    def test_data_transformation_performance(self):
        """Probar rendimiento de transformaciones de datos"""
        # Crear dataset para transformaciones
        n_rows = 5000
        df = pd.DataFrame({
            'date': pd.date_range('2020-01-01', periods=n_rows, freq='H'),
            'value': np.random.randn(n_rows),
            'category': np.random.choice(['A', 'B', 'C'], n_rows),
            'flag': np.random.choice([0, 1], n_rows)
        })
        
        # Prueba 1: Operaciones de agrupación
        start_time = time.time()
        grouped = df.groupby(['category', 'flag'])['value'].agg(['mean', 'std', 'count'])
        group_time = time.time() - start_time
        
        # Prueba 2: Operaciones de fecha
        start_time = time.time()
        df['year'] = df['date'].dt.year
        df['month'] = df['date'].dt.month
        df['day'] = df['date'].dt.day
        date_time = time.time() - start_time
        
        # Prueba 3: Operaciones de filtrado
        start_time = time.time()
        filtered = df[df['value'] > 0]
        filter_time = time.time() - start_time
        
        # Prueba 4: Operaciones de ordenamiento
        start_time = time.time()
        sorted_df = df.sort_values(['category', 'value'])
        sort_time = time.time() - start_time
        
        # Verificar resultados
        self.assertGreater(len(grouped), 0)
        self.assertIn('year', df.columns)
        self.assertGreater(len(filtered), 0)
        self.assertEqual(len(sorted_df), len(df))
        
        # Verificar tiempos
        self.assertLess(group_time, 1.0)
        self.assertLess(date_time, 1.0)
        self.assertLess(filter_time, 0.5)
        self.assertLess(sort_time, 1.0)


class TestScalability(unittest.TestCase):
    """Pruebas de escalabilidad"""

    def test_increasing_dataset_sizes(self):
        """Probar con tamaños crecientes de datasets"""
        sizes = [100, 1000, 5000, 10000]
        times = []
        
        for size in sizes:
            data = {
                'id': range(size),
                'value1': np.random.randn(size),
                'value2': np.random.randn(size),
                'category': np.random.choice(['A', 'B', 'C'], size)
            }
            
            start_time = time.time()
            df = pd.DataFrame(data)
            _ = df.describe()
            _ = df.groupby('category').mean()
            processing_time = time.time() - start_time
            
            times.append(processing_time)
        
        # Verificar que el tiempo crece de manera razonable
        # (no exponencialmente)
        for i in range(1, len(times)):
            ratio = times[i] / times[i-1]
            size_ratio = sizes[i] / sizes[i-1]
            # El tiempo no debería crecer más rápido que el tamaño
            self.assertLess(ratio, size_ratio * 2)

    def test_column_scalability(self):
        """Probar escalabilidad con número creciente de columnas"""
        base_rows = 1000
        column_counts = [5, 10, 20, 50]
        times = []
        
        for n_cols in column_counts:
            data = {}
            for i in range(n_cols):
                if i % 3 == 0:
                    data[f'col_{i}'] = np.random.randn(base_rows)
                elif i % 3 == 1:
                    data[f'col_{i}'] = np.random.choice(['X', 'Y', 'Z'], base_rows)
                else:
                    data[f'col_{i}'] = np.random.choice([True, False], base_rows)
            
            start_time = time.time()
            df = pd.DataFrame(data)
            _ = df.describe()
            _ = df.dtypes
            processing_time = time.time() - start_time
            
            times.append(processing_time)
        
        # Verificar que el procesamiento sea razonable
        for t in times:
            self.assertLess(t, 5.0)  # Menos de 5 segundos


if __name__ == '__main__':
    # Instalar memory_profiler si no está disponible
    try:
        import memory_profiler
    except ImportError:
        print("Warning: memory_profiler no está instalado. Algunas pruebas pueden fallar.")
    
    unittest.main()
