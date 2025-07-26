"""
Pruebas unitarias para DataApp1
Este archivo configura el entorno de pruebas
"""

import os
import sys
import unittest
import tempfile
import shutil
from unittest.mock import patch, MagicMock

# Agregar el directorio backend al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Configurar variables de entorno para pruebas
os.environ['FLASK_ENV'] = 'testing'
