"""
DataApp1 - Backend Flask Application
Aplicación para análisis exploratorio de datos con IA
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import pandas as pd
from werkzeug.utils import secure_filename
import logging
from data_analysis import DataAnalyzer
import json
from datetime import datetime

# Configuración de la aplicación
app = Flask(__name__)
CORS(app)

# Configuración
UPLOAD_FOLDER = '../uploads'
STATIC_FOLDER = '../static'
ALLOWED_EXTENSIONS = {'csv'}

app.config['UPLOAD_FOLDER'] = os.path.abspath(UPLOAD_FOLDER)
app.config['STATIC_FOLDER'] = os.path.abspath(STATIC_FOLDER)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Crear directorios si no existen
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(os.path.join(app.config['STATIC_FOLDER'], 'plots'), exist_ok=True)

def allowed_file(filename):
    """Verificar si el archivo tiene una extensión permitida"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """Ruta principal que sirve la página web"""
    frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend')
    return send_from_directory(frontend_dir, 'index.html')

# Rutas específicas para archivos estáticos del frontend
@app.route('/script.js')
def serve_script():
    """Servir el archivo JavaScript principal"""
    frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend')
    return send_from_directory(frontend_dir, 'script.js')

@app.route('/style.css')
def serve_style():
    """Servir el archivo CSS principal"""
    frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend')
    return send_from_directory(frontend_dir, 'style.css')

@app.route('/favicon.ico')
def serve_favicon():
    """Servir el favicon"""
    return send_from_directory(os.path.abspath('../frontend'), 'favicon.ico')

@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint para verificar el estado del servidor"""
    return jsonify({
        'status': 'healthy',
        'message': 'DataApp1 Backend está funcionando correctamente'
    })

@app.route('/analyze', methods=['POST'])
def analyze_data():
    """Endpoint principal para analizar datos CSV"""
    try:
        # Verificar que se envió un archivo
        if 'file' not in request.files:
            return jsonify({'error': 'No se encontró archivo en la solicitud'}), 400
        
        file = request.files['file']
        
        # Verificar que se seleccionó un archivo
        if file.filename == '':
            return jsonify({'error': 'No se seleccionó ningún archivo'}), 400
        
        # Verificar extensión del archivo
        if not allowed_file(file.filename):
            return jsonify({'error': 'Tipo de archivo no permitido. Solo se aceptan archivos CSV'}), 400
        
        # Guardar archivo de forma segura
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        logger.info(f"Archivo guardado: {filepath}")
        
        # Crear analizador y procesar datos
        analyzer = DataAnalyzer(file_path=filepath)
        results = analyzer.analyze()
        
        # Verificar si el análisis fue exitoso
        if not results.get('success', False):
            error_msg = results.get('error', 'Error desconocido durante el análisis')
            logger.error(f"Error en el análisis: {error_msg}")
            return jsonify({'error': error_msg}), 400
        
        # Limpiar archivo temporal
        try:
            os.remove(filepath)
        except Exception:
            pass
        
        logger.info("Análisis completado exitosamente")
        return jsonify(results)
        
    except pd.errors.EmptyDataError as e:
        logger.error(f"EmptyDataError: {str(e)}")
        return jsonify({'error': 'El archivo CSV está vacío o no contiene datos válidos'}), 400
    except pd.errors.ParserError as e:
        logger.error(f"ParserError: {str(e)}")
        return jsonify({'error': f'Error al parsear el archivo CSV. Verifica que el archivo tenga el formato correcto y use separadores como , o ; entre columnas. Error: {str(e)}'}), 400
    except UnicodeDecodeError as e:
        logger.error(f"UnicodeDecodeError: {str(e)}")
        return jsonify({'error': 'Error de codificación del archivo. Verifica que el archivo esté guardado en UTF-8, Latin-1 o Windows-1252'}), 400
    except FileNotFoundError as e:
        logger.error(f"FileNotFoundError: {str(e)}")
        return jsonify({'error': 'No se pudo encontrar el archivo subido'}), 400
    except Exception as e:
        logger.error(f"Error durante el análisis: {str(e)}", exc_info=True)
        return jsonify({'error': f'Error interno del servidor: {str(e)}'}), 500

@app.route('/static/<path:filename>')
def serve_static(filename):
    """Servir archivos estáticos (gráficos)"""
    return send_from_directory(app.config['STATIC_FOLDER'], filename)

@app.route('/plots/<path:filename>')
def serve_plots(filename):
    """Servir gráficos generados"""
    plots_dir = os.path.join(app.config['STATIC_FOLDER'], 'plots')
    return send_from_directory(plots_dir, filename)

@app.route('/generate-pdf', methods=['POST'])
def generate_pdf():
    """Generar y descargar PDF del análisis"""
    try:
        data = request.get_json()
        if not data or 'results' not in data:
            return jsonify({'error': 'No se proporcionaron datos para el PDF'}), 400
        
        results = data['results']
        filename = data.get('filename', 'analisis')
        
        # Crear PDF usando reportlab
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        from io import BytesIO
        
        # Crear buffer en memoria
        buffer = BytesIO()
        
        # Crear documento PDF
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
        
        # Estilos
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=24, spaceAfter=30, textColor=colors.darkblue)
        heading_style = ParagraphStyle('CustomHeading', parent=styles['Heading2'], fontSize=16, spaceAfter=12, textColor=colors.darkgreen)
        normal_style = styles['Normal']
        
        # Contenido del PDF
        story = []
        
        # Título
        title = Paragraph(f"📊 Análisis Exploratorio de Datos", title_style)
        story.append(title)
        story.append(Spacer(1, 12))
        
        # Información del archivo
        file_info = Paragraph(f"<b>Archivo:</b> {filename}<br/><b>Fecha:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')}", normal_style)
        story.append(file_info)
        story.append(Spacer(1, 20))
        
        # Información del dataset
        if 'basic_info' in results:
            story.append(Paragraph("📋 Información General del Dataset", heading_style))
            info = results['basic_info']
            
            # Dimensiones del dataset
            if 'dimensions' in info:
                dataset_data = [
                    ['Métrica', 'Valor'],
                    ['Número de filas', str(info['dimensions']['rows'])],
                    ['Número de columnas', str(info['dimensions']['columns'])]
                ]
                
                dataset_table = Table(dataset_data)
                dataset_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 14),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                
                story.append(dataset_table)
                story.append(Spacer(1, 20))
            
            # Tipos de datos
            if 'data_types' in info:
                story.append(Paragraph("🔤 Tipos de Datos", heading_style))
                
                # Contar tipos
                type_counts = {}
                for col, dtype in info['data_types'].items():
                    type_counts[dtype] = type_counts.get(dtype, 0) + 1
                
                # Tabla de resumen de tipos
                type_summary_data = [['Tipo de Dato', 'Cantidad', 'Porcentaje']]
                total_cols = len(info['data_types'])
                for dtype, count in type_counts.items():
                    percentage = (count / total_cols) * 100
                    type_summary_data.append([dtype, str(count), f"{percentage:.1f}%"])
                
                type_table = Table(type_summary_data, colWidths=[2*inch, 1*inch, 1*inch])
                type_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.darkblue),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                
                story.append(type_table)
                story.append(Spacer(1, 15))
                
                # Detalle por columna
                columns_data = [['Columna', 'Tipo de Dato']]
                for col, dtype in info['data_types'].items():
                    columns_data.append([col, dtype])
                
                columns_table = Table(columns_data, colWidths=[3*inch, 2*inch])
                columns_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.lightcyan),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                
                story.append(columns_table)
                story.append(Spacer(1, 20))
            
            # Valores nulos
            if 'null_values' in info:
                story.append(Paragraph("🔍 Análisis de Valores Nulos", heading_style))
                
                null_data = [['Columna', 'Valores Nulos', 'Porcentaje']]
                has_nulls = False
                
                for col, null_info in info['null_values'].items():
                    null_count = null_info['count']
                    null_percentage = null_info['percentage']
                    if null_count > 0:
                        has_nulls = True
                    null_data.append([col, str(null_count), f"{null_percentage}%"])
                
                null_table = Table(null_data, colWidths=[2.5*inch, 1.5*inch, 1*inch])
                null_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.orange),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.lightyellow),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                
                story.append(null_table)
                
                # Resumen de valores nulos
                if has_nulls:
                    story.append(Spacer(1, 10))
                    story.append(Paragraph("⚠️ <b>Se detectaron valores nulos en el dataset.</b> Considere técnicas de imputación o eliminación según el contexto del análisis.", normal_style))
                else:
                    story.append(Spacer(1, 10))
                    story.append(Paragraph("✅ <b>Excelente:</b> No se detectaron valores nulos en el dataset.", normal_style))
                
                story.append(Spacer(1, 20))
        
        # Estadísticas básicas
        if 'statistical_summary' in results:
            story.append(PageBreak())
            story.append(Paragraph("📈 Estadísticas Descriptivas", heading_style))
            stats = results['statistical_summary']
            
            if stats:
                for column, column_stats in stats.items():
                    story.append(Paragraph(f"<b>Variable: {column}</b>", normal_style))
                    
                    stats_data = [['Estadística', 'Valor']]
                    stats_data.append(['Conteo', str(column_stats.get('count', 'N/A'))])
                    stats_data.append(['Media', str(column_stats.get('mean', 'N/A'))])
                    stats_data.append(['Mediana', str(column_stats.get('median', 'N/A'))])
                    stats_data.append(['Desviación Estándar', str(column_stats.get('std', 'N/A'))])
                    stats_data.append(['Mínimo', str(column_stats.get('min', 'N/A'))])
                    stats_data.append(['Cuartil 25%', str(column_stats.get('q25', 'N/A'))])
                    stats_data.append(['Cuartil 75%', str(column_stats.get('q75', 'N/A'))])
                    stats_data.append(['Máximo', str(column_stats.get('max', 'N/A'))])
                    
                    stats_table = Table(stats_data, colWidths=[2.5*inch, 2*inch])
                    stats_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.darkblue),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 12),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black)
                    ]))
                    
                    story.append(stats_table)
                    story.append(Spacer(1, 15))
            else:
                story.append(Paragraph("No hay variables numéricas para mostrar estadísticas descriptivas.", normal_style))
                story.append(Spacer(1, 20))
        
        # Muestra de datos
        if 'data_preview' in results and results['data_preview']:
            story.append(PageBreak())
            story.append(Paragraph("👀 Muestra de Datos (Primeras 10 filas)", heading_style))
            
            preview_data = results['data_preview']
            if preview_data:
                # Obtener las columnas del primer registro
                columns = list(preview_data[0].keys())
                
                # Crear tabla con headers
                table_data = [columns]
                
                # Agregar hasta 10 filas de datos
                for row in preview_data[:10]:
                    row_data = []
                    for col in columns:
                        value = row.get(col, 'N/A')
                        # Truncar valores largos
                        if isinstance(value, str) and len(str(value)) > 20:
                            value = str(value)[:17] + "..."
                        row_data.append(str(value))
                    table_data.append(row_data)
                
                # Ajustar anchos de columna dinámicamente
                col_width = 6.5 / len(columns) * inch
                col_widths = [col_width] * len(columns)
                
                preview_table = Table(table_data, colWidths=col_widths)
                preview_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.darkgreen),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.lightgreen),
                    ('FONTSIZE', (0, 1), (-1, -1), 8),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP')
                ]))
                
                story.append(preview_table)
                story.append(Spacer(1, 20))
            else:
                story.append(Paragraph("No hay datos de muestra disponibles.", normal_style))
                story.append(Spacer(1, 20))
        
        # Información sobre visualizaciones
        story.append(PageBreak())
        story.append(Paragraph("📊 Visualizaciones Generadas", heading_style))
        
        viz_info = []
        if 'correlation_heatmap' in results and results['correlation_heatmap']:
            viz_info.append("• Matriz de Correlación (Heatmap) - Muestra las relaciones entre variables numéricas")
        
        if 'histograms' in results and results['histograms']:
            viz_info.append(f"• {len(results['histograms'])} Histogramas - Distribución de variables numéricas con estadísticas")
        
        if 'boxplots' in results and results['boxplots']:
            viz_info.append(f"• {len(results['boxplots'])} Boxplots - Detección de outliers y distribuciones")
        
        if viz_info:
            story.append(Paragraph("Las siguientes visualizaciones fueron generadas para el análisis:", normal_style))
            story.append(Spacer(1, 10))
            for info in viz_info:
                story.append(Paragraph(info, normal_style))
                story.append(Spacer(1, 5))
            story.append(Spacer(1, 10))
            story.append(Paragraph("<b>Nota:</b> Las visualizaciones están disponibles en la interfaz web de la aplicación.", normal_style))
        else:
            story.append(Paragraph("No se generaron visualizaciones para este dataset.", normal_style))
        
        story.append(Spacer(1, 20))
        
        # Insights de IA
        if 'ai_insights' in results:
            story.append(PageBreak())
            story.append(Paragraph("🤖 Insights Generados por IA", heading_style))
            
            insights = results['ai_insights']
            if isinstance(insights, list) and insights:
                story.append(Paragraph("Análisis automático realizado por inteligencia artificial:", normal_style))
                story.append(Spacer(1, 15))
                
                for i, insight in enumerate(insights, 1):
                    # Limpiar emojis y caracteres especiales para PDF
                    clean_insight = insight.replace('📊', '').replace('📈', '').replace('📝', '').replace('🔗', '').replace('📉', '').replace('⚠️', '').replace('🚨', '').replace('✅', '').replace('💡', '')
                    insight_text = Paragraph(f"{i}. {clean_insight.strip()}", normal_style)
                    story.append(insight_text)
                    story.append(Spacer(1, 8))
            else:
                story.append(Paragraph("No se generaron insights específicos para este dataset.", normal_style))
        
        # Conclusiones y recomendaciones
        story.append(PageBreak())
        story.append(Paragraph("📋 Conclusiones y Recomendaciones", heading_style))
        
        conclusions = []
        
        # Análisis del tamaño del dataset
        if 'basic_info' in results and 'dimensions' in results['basic_info']:
            rows = results['basic_info']['dimensions']['rows']
            cols = results['basic_info']['dimensions']['columns']
            
            if rows > 10000:
                conclusions.append(f"Dataset de gran tamaño ({rows:,} registros) - Ideal para análisis estadísticos robustos y machine learning.")
            elif rows < 100:
                conclusions.append(f"Dataset pequeño ({rows} registros) - Los resultados pueden tener alta variabilidad. Considere obtener más datos.")
            else:
                conclusions.append(f"Dataset de tamaño moderado ({rows:,} registros) - Adecuado para análisis exploratorio.")
        
        # Análisis de calidad de datos
        if 'basic_info' in results and 'null_values' in results['basic_info']:
            total_nulls = sum(null_info['count'] for null_info in results['basic_info']['null_values'].values())
            if total_nulls == 0:
                conclusions.append("Excelente calidad de datos: No se detectaron valores nulos.")
            else:
                conclusions.append(f"Se detectaron {total_nulls} valores nulos. Considere técnicas de limpieza de datos.")
        
        # Recomendaciones generales
        recommendations = [
            "Utilice las visualizaciones generadas para identificar patrones y anomalías en los datos.",
            "Revise los insights de IA para obtener perspectivas adicionales sobre el dataset.",
            "Considere análisis más profundos según el objetivo específico de su proyecto.",
            "Para análisis predictivo, evalúe la correlación entre variables y la presencia de outliers.",
            "Documente los hallazgos principales para futuras referencias y análisis."
        ]
        
        if conclusions:
            story.append(Paragraph("<b>Conclusiones:</b>", normal_style))
            story.append(Spacer(1, 10))
            for conclusion in conclusions:
                story.append(Paragraph(f"• {conclusion}", normal_style))
                story.append(Spacer(1, 5))
            story.append(Spacer(1, 15))
        
        story.append(Paragraph("<b>Recomendaciones:</b>", normal_style))
        story.append(Spacer(1, 10))
        for recommendation in recommendations:
            story.append(Paragraph(f"• {recommendation}", normal_style))
            story.append(Spacer(1, 5))
        
        # Pie de página
        story.append(Spacer(1, 30))
        footer_style = ParagraphStyle('Footer', parent=styles['Normal'], fontSize=10, textColor=colors.grey, alignment=1)
        story.append(Paragraph(f"Reporte generado por DataApp1 - {datetime.now().strftime('%d/%m/%Y %H:%M')}", footer_style))
        
        # Construir PDF
        doc.build(story)
        
        # Obtener contenido del buffer
        pdf_content = buffer.getvalue()
        buffer.close()
        
        # Crear respuesta con el PDF
        from flask import make_response
        response = make_response(pdf_content)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=analisis_{filename.replace(".csv", "")}_{datetime.now().strftime("%Y%m%d")}.pdf'
        
        return response
        
    except ImportError:
        return jsonify({'error': 'reportlab no está instalado. Ejecuta: pip install reportlab'}), 500
    except Exception as e:
        logger.error(f"Error al generar PDF: {str(e)}")
        return jsonify({'error': f'Error al generar PDF: {str(e)}'}), 500

@app.errorhandler(413)
def too_large(e):
    """Manejar archivos demasiado grandes"""
    return jsonify({'error': 'El archivo es demasiado grande. Máximo 50MB permitido'}), 413

@app.errorhandler(404)
def not_found(e):
    """Manejar rutas no encontradas"""
    return jsonify({'error': 'Endpoint no encontrado'}), 404

@app.errorhandler(500)
def internal_error(e):
    """Manejar errores internos del servidor"""
    return jsonify({'error': 'Error interno del servidor'}), 500

if __name__ == '__main__':
    print("🚀 Iniciando DataApp1 Backend...")
    print("📊 Servidor de análisis de datos con IA")
    print("🌐 Disponible en: http://localhost:5000")
    print("📝 Endpoints disponibles:")
    print("   - GET  /health - Verificar estado del servidor")
    print("   - POST /analyze - Analizar archivo CSV")
    print("   - GET  /static/<filename> - Servir archivos estáticos")
    print("   - GET  /plots/<filename> - Servir gráficos")
    print("-" * 50)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
