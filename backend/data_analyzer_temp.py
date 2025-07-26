import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
from io import StringIO
import chardet
import os
import tempfile
import base64
from typing import Dict, List, Any, Tuple, Optional

# Suppress warnings
warnings.filterwarnings('ignore')

# Set style for plots
plt.style.use('default')
sns.set_palette("husl")

class DataAnalyzer:
    def __init__(self, csv_content: str = None, file_path: str = None):
        """
        Initialize DataAnalyzer with CSV content or file path.
        """
        self.df = None
        self.analysis_results = {}
        self.plot_paths = []
        
        if csv_content:
            self.load_from_content(csv_content)
        elif file_path:
            self.load_from_file(file_path)
    
    def detect_separator(self, sample_text: str) -> str:
        """
        Detect the separator used in CSV file.
        """
        # Common separators to test
        separators = [',', ';', '\t', '|']
        separator_counts = {}
        
        lines = sample_text.split('\n')[:5]  # Check first 5 lines
        
        for sep in separators:
            counts = []
            for line in lines:
                if line.strip():
                    counts.append(line.count(sep))
            
            if counts:
                # Check if separator count is consistent across lines
                if len(set(counts)) <= 2 and max(counts) > 0:
                    separator_counts[sep] = max(counts)
        
        if separator_counts:
            return max(separator_counts, key=separator_counts.get)
        return ','  # Default to comma
    
    def detect_encoding(self, file_content: bytes) -> str:
        """
        Detect file encoding.
        """
        detected = chardet.detect(file_content)
        return detected.get('encoding', 'utf-8') if detected['confidence'] > 0.7 else 'utf-8'
    
    def load_from_content(self, csv_content: str):
        """
        Load data from CSV content string.
        """
        try:
            # Detect separator
            separator = self.detect_separator(csv_content)
            
            # Try to read with detected separator
            self.df = pd.read_csv(StringIO(csv_content), sep=separator)
            
            # If dataframe has only one column, try with comma
            if len(self.df.columns) == 1 and separator != ',':
                self.df = pd.read_csv(StringIO(csv_content), sep=',')
            
            print(f"Loaded data with separator '{separator}': {self.df.shape}")
            
        except Exception as e:
            print(f"Error loading CSV: {e}")
            # Fallback: try common separators
            for sep in [',', ';', '\t']:
                try:
                    self.df = pd.read_csv(StringIO(csv_content), sep=sep)
                    if len(self.df.columns) > 1:
                        break
                except:
                    continue
    
    def load_from_file(self, file_path: str):
        """
        Load data from CSV file.
        """
        try:
            # Read file as bytes to detect encoding
            with open(file_path, 'rb') as f:
                raw_data = f.read()
            
            # Detect encoding
            encoding = self.detect_encoding(raw_data)
            
            # Read as text to detect separator
            text_content = raw_data.decode(encoding)
            separator = self.detect_separator(text_content)
            
            # Load with detected parameters
            self.df = pd.read_csv(file_path, sep=separator, encoding=encoding)
            
        except Exception as e:
            print(f"Error loading file: {e}")
            # Fallback
            try:
                self.df = pd.read_csv(file_path)
            except:
                self.df = pd.read_csv(file_path, sep=';')
    
    def get_basic_info(self) -> Dict[str, Any]:
        """
        Get basic information about the dataset.
        """
        if self.df is None:
            return {}
        
        # Dataset dimensions
        dimensions = {
            'rows': int(self.df.shape[0]),
            'columns': int(self.df.shape[1])
        }
        
        # Data types
        data_types = {}
        for col in self.df.columns:
            dtype = str(self.df[col].dtype)
            if dtype.startswith('int'):
                data_types[col] = 'Entero'
            elif dtype.startswith('float'):
                data_types[col] = 'Decimal'
            elif dtype.startswith('object'):
                data_types[col] = 'Texto'
            elif dtype.startswith('datetime'):
                data_types[col] = 'Fecha'
            else:
                data_types[col] = dtype
        
        # Null values
        null_values = {}
        for col in self.df.columns:
            null_count = int(self.df[col].isnull().sum())
            null_percentage = round((null_count / len(self.df)) * 100, 2)
            null_values[col] = {
                'count': null_count,
                'percentage': null_percentage
            }
        
        return {
            'dimensions': dimensions,
            'data_types': data_types,
            'null_values': null_values
        }
    
    def get_statistical_summary(self) -> Dict[str, Any]:
        """
        Get statistical summary for numerical columns.
        """
        if self.df is None:
            return {}
        
        numerical_cols = self.df.select_dtypes(include=[np.number]).columns
        stats = {}
        
        for col in numerical_cols:
            col_stats = {
                'count': int(self.df[col].count()),
                'mean': round(float(self.df[col].mean()), 4),
                'median': round(float(self.df[col].median()), 4),
                'std': round(float(self.df[col].std()), 4),
                'min': round(float(self.df[col].min()), 4),
                'max': round(float(self.df[col].max()), 4),
                'q25': round(float(self.df[col].quantile(0.25)), 4),
                'q75': round(float(self.df[col].quantile(0.75)), 4)
            }
            stats[col] = col_stats
        
        return stats
    
    def create_correlation_heatmap(self) -> str:
        """
        Create correlation heatmap for numerical variables.
        """
        if self.df is None:
            return ""
        
        numerical_cols = self.df.select_dtypes(include=[np.number]).columns
        
        if len(numerical_cols) < 2:
            return ""
        
        try:
            plt.figure(figsize=(10, 8))
            correlation_matrix = self.df[numerical_cols].corr()
            
            # Create heatmap
            sns.heatmap(correlation_matrix, 
                       annot=True, 
                       cmap='coolwarm', 
                       center=0,
                       square=True,
                       fmt='.2f',
                       cbar_kws={'shrink': 0.8})
            
            plt.title('Matriz de Correlación', fontsize=16, fontweight='bold')
            plt.tight_layout()
            
            # Save plot
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png', dir='../frontend/plots')
            plt.savefig(temp_file.name, dpi=300, bbox_inches='tight')
            plt.close()
            
            # Convert to base64 for web display
            with open(temp_file.name, 'rb') as f:
                img_data = base64.b64encode(f.read()).decode()
            
            self.plot_paths.append(temp_file.name)
            return f"data:image/png;base64,{img_data}"
            
        except Exception as e:
            print(f"Error creating correlation heatmap: {e}")
            return ""
    
    def create_histograms(self) -> List[str]:
        """
        Create histograms for numerical variables.
        """
        if self.df is None:
            return []
        
        numerical_cols = self.df.select_dtypes(include=[np.number]).columns
        histogram_plots = []
        
        for col in numerical_cols:
            try:
                plt.figure(figsize=(8, 6))
                
                # Create histogram
                plt.hist(self.df[col].dropna(), bins=30, alpha=0.7, color='skyblue', edgecolor='black')
                plt.title(f'Histograma de {col}', fontsize=14, fontweight='bold')
                plt.xlabel(col)
                plt.ylabel('Frecuencia')
                plt.grid(True, alpha=0.3)
                
                # Add statistics text
                mean_val = self.df[col].mean()
                median_val = self.df[col].median()
                plt.axvline(mean_val, color='red', linestyle='--', label=f'Media: {mean_val:.2f}')
                plt.axvline(median_val, color='green', linestyle='--', label=f'Mediana: {median_val:.2f}')
                plt.legend()
                
                plt.tight_layout()
                
                # Save plot
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png', dir='../frontend/plots')
                plt.savefig(temp_file.name, dpi=300, bbox_inches='tight')
                plt.close()
                
                # Convert to base64
                with open(temp_file.name, 'rb') as f:
                    img_data = base64.b64encode(f.read()).decode()
                
                self.plot_paths.append(temp_file.name)
                histogram_plots.append(f"data:image/png;base64,{img_data}")
                
            except Exception as e:
                print(f"Error creating histogram for {col}: {e}")
                continue
        
        return histogram_plots
    
    def create_boxplots(self) -> List[str]:
        """
        Create boxplots for numerical variables grouped by categorical variables.
        """
        if self.df is None:
            return []
        
        numerical_cols = self.df.select_dtypes(include=[np.number]).columns
        categorical_cols = self.df.select_dtypes(include=['object']).columns
        
        boxplot_images = []
        
        # If no categorical columns, create simple boxplots for numerical columns
        if len(categorical_cols) == 0:
            for col in numerical_cols:
                try:
                    plt.figure(figsize=(8, 6))
                    plt.boxplot(self.df[col].dropna())
                    plt.title(f'Boxplot de {col}', fontsize=14, fontweight='bold')
                    plt.ylabel(col)
                    plt.grid(True, alpha=0.3)
                    plt.tight_layout()
                    
                    # Save plot
                    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png', dir='../frontend/plots')
                    plt.savefig(temp_file.name, dpi=300, bbox_inches='tight')
                    plt.close()
                    
                    # Convert to base64
                    with open(temp_file.name, 'rb') as f:
                        img_data = base64.b64encode(f.read()).decode()
                    
                    self.plot_paths.append(temp_file.name)
                    boxplot_images.append(f"data:image/png;base64,{img_data}")
                    
                except Exception as e:
                    print(f"Error creating boxplot for {col}: {e}")
                    continue
        else:
            # Create boxplots with categorical grouping
            for num_col in numerical_cols:
                for cat_col in categorical_cols:
                    # Limit categories to avoid overcrowded plots
                    unique_categories = self.df[cat_col].value_counts().head(10).index
                    filtered_df = self.df[self.df[cat_col].isin(unique_categories)]
                    
                    if len(unique_categories) < 2:
                        continue
                    
                    try:
                        plt.figure(figsize=(12, 6))
                        
                        # Create boxplot
                        sns.boxplot(data=filtered_df, x=cat_col, y=num_col)
                        plt.title(f'Boxplot de {num_col} por {cat_col}', fontsize=14, fontweight='bold')
                        plt.xticks(rotation=45)
                        plt.grid(True, alpha=0.3)
                        plt.tight_layout()
                        
                        # Save plot
                        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png', dir='../frontend/plots')
                        plt.savefig(temp_file.name, dpi=300, bbox_inches='tight')
                        plt.close()
                        
                        # Convert to base64
                        with open(temp_file.name, 'rb') as f:
                            img_data = base64.b64encode(f.read()).decode()
                        
                        self.plot_paths.append(temp_file.name)
                        boxplot_images.append(f"data:image/png;base64,{img_data}")
                        
                        # Limit to avoid too many plots
                        if len(boxplot_images) >= 5:
                            break
                            
                    except Exception as e:
                        print(f"Error creating boxplot for {num_col} by {cat_col}: {e}")
                        continue
                
                if len(boxplot_images) >= 5:
                    break
        
        return boxplot_images
    
    def generate_ai_insights(self) -> List[str]:
        """
        Generate AI-powered insights from the data analysis.
        """
        if self.df is None:
            return []
        
        insights = []
        
        # Dataset size insights
        rows, cols = self.df.shape
        if rows > 10000:
            insights.append(f"📊 Dataset grande con {rows:,} registros - ideal para análisis estadísticos robustos.")
        elif rows < 100:
            insights.append(f"⚠️ Dataset pequeño con {rows} registros - los resultados pueden tener alta variabilidad.")
        
        # Missing data insights
        missing_percentage = (self.df.isnull().sum().sum() / (rows * cols)) * 100
        if missing_percentage > 20:
            insights.append(f"🚨 Alto porcentaje de datos faltantes ({missing_percentage:.1f}%) - considere técnicas de imputación.")
        elif missing_percentage > 5:
            insights.append(f"⚠️ Datos faltantes moderados ({missing_percentage:.1f}%) - revisar patrones de missingness.")
        elif missing_percentage == 0:
            insights.append("✅ Excelente: No hay datos faltantes en el dataset.")
        
        # Data types insights
        numerical_cols = len(self.df.select_dtypes(include=[np.number]).columns)
        categorical_cols = len(self.df.select_dtypes(include=['object']).columns)
        
        if numerical_cols > categorical_cols:
            insights.append(f"📈 Dataset principalmente numérico ({numerical_cols} numéricas vs {categorical_cols} categóricas) - ideal para análisis estadísticos y machine learning.")
        elif categorical_cols > numerical_cols:
            insights.append(f"📝 Dataset principalmente categórico ({categorical_cols} categóricas vs {numerical_cols} numéricas) - considere técnicas de encoding para ML.")
        
        # Correlation insights
        if numerical_cols >= 2:
            corr_matrix = self.df.select_dtypes(include=[np.number]).corr()
            high_corr_pairs = []
            for i in range(len(corr_matrix.columns)):
                for j in range(i+1, len(corr_matrix.columns)):
                    corr_val = abs(corr_matrix.iloc[i, j])
                    if corr_val > 0.8:
                        high_corr_pairs.append((corr_matrix.columns[i], corr_matrix.columns[j], corr_val))
            
            if high_corr_pairs:
                insights.append(f"🔗 Detectadas {len(high_corr_pairs)} correlaciones altas (>0.8) - posible multicolinealidad.")
            else:
                insights.append("✅ No se detectaron correlaciones excesivamente altas entre variables.")
        
        # Outlier detection insights
        numerical_data = self.df.select_dtypes(include=[np.number])
        outlier_columns = []
        for col in numerical_data.columns:
            Q1 = numerical_data[col].quantile(0.25)
            Q3 = numerical_data[col].quantile(0.75)
            IQR = Q3 - Q1
            outliers = numerical_data[(numerical_data[col] < Q1 - 1.5*IQR) | (numerical_data[col] > Q3 + 1.5*IQR)]
            if len(outliers) > 0:
                outlier_columns.append(col)
        
        if outlier_columns:
            insights.append(f"📉 Detectados outliers en {len(outlier_columns)} variables - revisar valores atípicos en los boxplots.")
        
        # Distribution insights
        for col in numerical_data.columns:
            skewness = numerical_data[col].skew()
            if abs(skewness) > 2:
                direction = "derecha" if skewness > 0 else "izquierda"
                insights.append(f"📊 Variable '{col}' tiene distribución muy asimétrica hacia la {direction} (skew: {skewness:.2f}).")
        
        # Data quality insights
        duplicate_rows = self.df.duplicated().sum()
        if duplicate_rows > 0:
            insights.append(f"⚠️ Detectadas {duplicate_rows} filas duplicadas - considere eliminarlas para mejorar la calidad del análisis.")
        
        # Recommendations
        insights.append("💡 Recomendaciones basadas en IA:")
        if numerical_cols >= 2:
            insights.append("   • Use la matriz de correlación para identificar relaciones entre variables")
        if categorical_cols > 0:
            insights.append("   • Analice los boxplots para entender distribuciones por categorías")
        if outlier_columns:
            insights.append("   • Investigue outliers - pueden ser errores o insights valiosos")
        insights.append("   • Considere técnicas de visualización adicionales según sus objetivos analíticos")
        
        return insights
    
    def analyze(self) -> Dict[str, Any]:
        """
        Perform complete analysis of the dataset.
        """
        if self.df is None:
            return {'error': 'No data loaded'}
        
        # Ensure plots directory exists
        plots_dir = '../frontend/plots'
        if not os.path.exists(plots_dir):
            os.makedirs(plots_dir)
        
        try:
            # Basic information
            basic_info = self.get_basic_info()
            
            # Statistical summary
            stats = self.get_statistical_summary()
            
            # Create visualizations
            correlation_heatmap = self.create_correlation_heatmap()
            histograms = self.create_histograms()
            boxplots = self.create_boxplots()
            
            # Generate AI insights
            ai_insights = self.generate_ai_insights()
            
            # Data preview
            data_preview = []
            if not self.df.empty:
                preview_df = self.df.head(10)
                for _, row in preview_df.iterrows():
                    data_preview.append(row.to_dict())
            
            results = {
                'basic_info': basic_info,
                'statistical_summary': stats,
                'data_preview': data_preview,
                'correlation_heatmap': correlation_heatmap,
                'histograms': histograms,
                'boxplots': boxplots,
                'ai_insights': ai_insights,
                'success': True
            }
            
            self.analysis_results = results
            return results
            
        except Exception as e:
            print(f"Error during analysis: {e}")
            return {
                'error': f'Error durante el análisis: {str(e)}',
                'success': False
            }
    
    def cleanup_plots(self):
        """
        Clean up temporary plot files.
        """
        for plot_path in self.plot_paths:
            try:
                if os.path.exists(plot_path):
                    os.remove(plot_path)
            except Exception as e:
                print(f"Error removing plot file {plot_path}: {e}")
        self.plot_paths = []

    def get_column_info(self) -> Dict[str, str]:
        """
        Get information about each column in the dataset.
        """
        if self.df is None:
            return {}
        
        column_info = {}
        for col in self.df.columns:
            unique_count = self.df[col].nunique()
            total_count = len(self.df[col])
            
            if self.df[col].dtype in ['int64', 'float64']:
                col_type = 'Numérica'
            elif unique_count / total_count < 0.1 and unique_count < 50:
                col_type = 'Categórica'
            else:
                col_type = 'Texto'
            
            column_info[col] = col_type
        
        return column_info
