// JavaScript para la aplicación de análisis de datos

// Configuración
const API_BASE_URL = 'http://localhost:5000';

// Elementos del DOM
const uploadForm = document.getElementById('uploadForm');
const csvFileInput = document.getElementById('csvFile');
const analyzeBtn = document.getElementById('analyzeBtn');
const loadingArea = document.getElementById('loadingArea');
const resultsSection = document.getElementById('resultsSection');
const errorArea = document.getElementById('errorArea');
const selectedFileName = document.getElementById('selectedFileName');
const progressFill = document.getElementById('progressFill');
const progressPercentage = document.getElementById('progressPercentage');
const progressStatus = document.getElementById('progressStatus');
const downloadPdfBtn = document.getElementById('downloadPdfBtn');

// Event Listeners
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

uploadForm.addEventListener('submit', handleFormSubmit);
csvFileInput.addEventListener('change', handleFileSelect);
downloadPdfBtn.addEventListener('click', handleDownloadPDF);

// Funciones principales
function initializeApp() {
    console.log('DataApp1 inicializada');
    hideAllSections();
}

function handleFileSelect(event) {
    const file = event.target.files[0];
    const fileLabel = document.querySelector('.file-text');
    
    if (file) {
        fileLabel.textContent = file.name;
        analyzeBtn.disabled = false;
    } else {
        fileLabel.textContent = 'Seleccionar archivo CSV';
        analyzeBtn.disabled = true;
    }
}

async function handleFormSubmit(event) {
    event.preventDefault();
    
    const file = csvFileInput.files[0];
    if (!file) {
        showError('Por favor selecciona un archivo CSV');
        return;
    }
    
    if (!file.name.toLowerCase().endsWith('.csv')) {
        showError('Por favor selecciona un archivo con extensión .csv');
        return;
    }
    
    await analyzeData(file);
}

async function analyzeData(file) {
    try {
        showLoading(file.name);
        
        const formData = new FormData();
        formData.append('file', file);
        
        // Iniciar progreso inmediatamente después de mostrar loading
        setTimeout(() => {
            simulateProgress();
        }, 200);
        
        const response = await fetch(`${API_BASE_URL}/analyze`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(`Error del servidor: ${response.status}`);
        }
        
        const results = await response.json();
        completeProgress();
        
        // Guardar resultados para descarga PDF
        window.lastAnalysisResults = results;
        window.lastFileName = file.name;
        
        // Esperar un poco antes de mostrar resultados para que se vea el 100%
        setTimeout(() => {
            displayResults(results);
        }, 1000);
        
    } catch (error) {
        console.error('Error durante el análisis:', error);
        if (window.currentProgressInterval) {
            clearInterval(window.currentProgressInterval);
        }
        showError('Error al analizar el archivo. Verifica que el servidor esté ejecutándose.');
    }
}

function displayResults(results) {
    hideAllSections();
    resultsSection.classList.remove('hidden');
    
    // Habilitar el botón de análisis nuevamente
    analyzeBtn.disabled = false;
    
    // Mostrar información del dataset
    displayDatasetInfo(results.basic_info);
    
    // Mostrar estadísticos básicos
    displayBasicStats(results.statistical_summary);
    
    // Mostrar valores nulos
    if (results.basic_info?.null_values) {
        displayNullValues(results.basic_info.null_values);
    }
    
    // Mostrar distribución de columnas
    if (results.basic_info?.data_types) {
        displayColumnDistribution(results.basic_info.data_types);
    }
    
    // Mostrar visualizaciones
    displayVisualizations(results);
    
    // Mostrar insights de IA
    if (results.ai_insights) {
        displayAIInsights(results.ai_insights);
    }
}

function displayDatasetInfo(info) {
    const container = document.getElementById('datasetInfo');
    
    let dtypesTable = '';
    if (info.dtypes && info.non_null_counts) {
        dtypesTable = `
        <div class="info-box">
            <h4>🔤 Tipos de Datos</h4>
            <table>
                <thead>
                    <tr>
                        <th>Columna</th>
                        <th>Tipo de Dato</th>
                        <th>Valores No Nulos</th>
                    </tr>
                </thead>
                <tbody>
                    ${Object.entries(info.dtypes).map(([col, dtype]) => `
                        <tr>
                            <td>${col}</td>
                            <td>${dtype}</td>
                            <td>${info.non_null_counts[col] || 'N/A'}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>`;
    }
    
    let columnsInfo = '';
    if (info.columns) {
        columnsInfo = `
        <div class="info-box">
            <h4>📋 Columnas del Dataset</h4>
            <p><strong>Total de columnas:</strong> ${info.columns.length}</p>
            <p><strong>Columnas numéricas:</strong> ${info.numeric_columns ? info.numeric_columns.length : 0}</p>
            <div class="columns-list">
                ${info.columns.map(col => `<span class="column-tag">${col}</span>`).join('')}
            </div>
        </div>`;
    }
    
    let memoryInfo = '';
    if (info.memory_usage) {
        memoryInfo = `<p><strong>Memoria utilizada:</strong> ${info.memory_usage}</p>`;
    }
    
    const html = `
        <div class="info-box">
            <h4>📊 Dimensiones del Dataset</h4>
            <p><strong>Filas:</strong> ${info.dimensions?.rows || (info.shape ? info.shape[0] : 'N/A')}</p>
            <p><strong>Columnas:</strong> ${info.dimensions?.columns || (info.shape ? info.shape[1] : 'N/A')}</p>
            ${memoryInfo}
        </div>
        
        ${dtypesTable}
        
        ${columnsInfo}
        
        ${info.head_html ? `
        <div class="info-box">
            <h4>👀 Primeras 5 filas</h4>
            <div style="overflow-x: auto;">
                ${info.head_html}
            </div>
        </div>` : ''}
    `;
    
    container.innerHTML = html;
}

function displayBasicStats(stats) {
    const container = document.getElementById('basicStats');
    
    if (!stats || Object.keys(stats).length === 0) {
        container.innerHTML = `
            <div class="info-box">
                <h4>📈 Estadísticos Descriptivos</h4>
                <p>No hay columnas numéricas para mostrar estadísticos.</p>
            </div>
        `;
        return;
    }
    
    let html = '<div class="info-box"><h4>📈 Estadísticos Descriptivos</h4>';
    
    // Si existe describe_html (formato anterior), úsalo
    if (stats.describe_html) {
        html += `<div style="overflow-x: auto;">${stats.describe_html}</div>`;
    } else {
        // Usar la nueva estructura de datos
        html += '<div class="stats-grid">';
        
        for (const [column, columnStats] of Object.entries(stats)) {
            html += `
                <div class="stat-column">
                    <h5>📊 ${column}</h5>
                    <table class="stats-table">
                        <tbody>
                            <tr><td><strong>Conteo:</strong></td><td>${columnStats.count}</td></tr>
                            <tr><td><strong>Media:</strong></td><td>${columnStats.mean}</td></tr>
                            <tr><td><strong>Mediana:</strong></td><td>${columnStats.median}</td></tr>
                            <tr><td><strong>Desv. Est.:</strong></td><td>${columnStats.std}</td></tr>
                            <tr><td><strong>Mínimo:</strong></td><td>${columnStats.min}</td></tr>
                            <tr><td><strong>Máximo:</strong></td><td>${columnStats.max}</td></tr>
                        </tbody>
                    </table>
                </div>
            `;
        }
        
        html += '</div>';
    }
    
    html += '</div>';
    container.innerHTML = html;
}

function displayNullValues(nullValues) {
    const container = document.getElementById('nullValues');
    
    // Verificar si nullValues existe y no es null/undefined
    if (!nullValues || typeof nullValues !== 'object') {
        container.innerHTML = `
            <div class="info-box">
                <h4>🔍 Valores Nulos</h4>
                <p>No se pudo obtener información sobre valores nulos.</p>
            </div>
        `;
        return;
    }
    
    const hasNulls = Object.values(nullValues).some(count => count > 0);
    
    let html = `
        <div class="${hasNulls ? 'warning-box' : 'success-box'}">
            <h4>🔍 Resumen de Valores Nulos</h4>
            ${hasNulls ? 
                '<p>⚠️ Se encontraron valores nulos en el dataset:</p>' : 
                '<p>✅ ¡Excelente! No se encontraron valores nulos en el dataset.</p>'
            }
        </div>
    `;
    
    if (hasNulls) {
        html += `
            <table>
                <thead>
                    <tr>
                        <th>Columna</th>
                        <th>Valores Nulos</th>
                        <th>Porcentaje</th>
                    </tr>
                </thead>
                <tbody>
                    ${Object.entries(nullValues).map(([col, count]) => `
                        <tr>
                            <td>${col}</td>
                            <td>${count}</td>
                            <td>${count > 0 ? ((count / 100) * 100).toFixed(2) : '0.00'}%</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
    }
    
    container.innerHTML = html;
}

function displayVisualizations(visualizations) {
    const container = document.getElementById('visualizations');
    
    if (!visualizations || visualizations.length === 0) {
        container.innerHTML = '<p>No se generaron visualizaciones.</p>';
        return;
    }
    
    const html = visualizations.map(viz => `
        <div class="plot-container">
            <div class="plot-title">${viz.title}</div>
            <img src="${API_BASE_URL}${viz.path}" alt="${viz.title}" />
            <p class="plot-description">${viz.description}</p>
        </div>
    `).join('');
    
    container.innerHTML = html;
}

function displayAIInsights(insights) {
    const container = document.getElementById('aiInsights');
    
    if (!insights || insights.length === 0) {
        container.innerHTML = '<p>No se generaron insights automáticos.</p>';
        return;
    }
    
    const html = `
        <div class="info-box">
            <h4>🤖 Análisis Automático</h4>
            ${insights.map(insight => `
                <div class="insight-item">
                    <h5>${insight.title}</h5>
                    <p>${insight.description}</p>
                    ${insight.recommendation ? `<p><strong>Recomendación:</strong> ${insight.recommendation}</p>` : ''}
                </div>
            `).join('<hr style="margin: 15px 0;">')}
        </div>
    `;
    
    container.innerHTML = html;
}

function showError(message) {
    hideAllSections();
    errorArea.classList.remove('hidden');
    document.getElementById('errorMessage').textContent = message;
    analyzeBtn.disabled = false;
}

function hideAllSections() {
    loadingArea.classList.add('hidden');
    resultsSection.classList.add('hidden');
    errorArea.classList.add('hidden');
}

// Utilidades
function formatNumber(num) {
    return new Intl.NumberFormat('es-ES', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(num);
}

function capitalizeFirst(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
}

// Manejo de errores globales
window.addEventListener('error', function(event) {
    console.error('Error global:', event.error);
    showError('Ocurrió un error inesperado. Por favor, recarga la página.');
});

// Nuevas funciones para las mejoras

// Función para mostrar loading con archivo seleccionado
function showLoading(fileName = '') {
    hideAllSections();
    loadingArea.classList.remove('hidden');
    
    if (fileName && selectedFileName) {
        selectedFileName.textContent = fileName;
    }
    
    // Resetear progreso inmediatamente
    setTimeout(() => {
        resetProgress();
    }, 100);
    
    // Habilitar botón después del análisis
    analyzeBtn.disabled = true;
}

// Función para simular progreso
function simulateProgress() {
    let currentStage = 0;
    const stages = [
        { percent: 10, message: "Validando archivo..." },
        { percent: 25, message: "Cargando datos..." },
        { percent: 40, message: "Analizando estructura..." },
        { percent: 60, message: "Calculando estadísticas..." },
        { percent: 80, message: "Generando visualizaciones..." },
        { percent: 95, message: "Aplicando IA..." }
    ];
    
    // Empezar inmediatamente con la primera etapa
    if (stages.length > 0) {
        updateProgress(stages[0].percent, stages[0].message);
        currentStage = 1;
    }
    
    const progressInterval = setInterval(() => {
        if (currentStage < stages.length) {
            const stage = stages[currentStage];
            updateProgress(stage.percent, stage.message);
            currentStage++;
        } else {
            clearInterval(progressInterval);
            window.currentProgressInterval = null;
        }
    }, 1000); // Cambiar cada 1 segundo para mejor visibilidad
    
    // Guardar referencia para poder limpiarlo si es necesario
    window.currentProgressInterval = progressInterval;
}

// Función para completar progreso
function completeProgress() {
    if (window.currentProgressInterval) {
        clearInterval(window.currentProgressInterval);
    }
    updateProgress(100, "¡Análisis completado!");
    
    // Esperar un momento antes de mostrar resultados
    setTimeout(() => {
        hideAllSections();
    }, 500);
}

// Función para actualizar progreso
function updateProgress(percent, message) {
    console.log(`Progreso: ${percent}% - ${message}`); // Para debugging
    
    // Verificar que los elementos existen
    const progressFillElement = document.getElementById('progressFill');
    const progressPercentageElement = document.getElementById('progressPercentage');
    const progressStatusElement = document.getElementById('progressStatus');
    
    if (progressFillElement) {
        progressFillElement.style.width = `${percent}%`;
    } else {
        console.error('Elemento progressFill no encontrado');
    }
    
    if (progressPercentageElement) {
        progressPercentageElement.textContent = `${percent}%`;
    } else {
        console.error('Elemento progressPercentage no encontrado');
    }
    
    if (progressStatusElement) {
        progressStatusElement.textContent = message;
    } else {
        console.error('Elemento progressStatus no encontrado');
    }
}

// Función para resetear progreso
function resetProgress() {
    updateProgress(0, "Iniciando análisis...");
}

// Función para manejar descarga de PDF
async function handleDownloadPDF() {
    if (!window.lastAnalysisResults || !window.lastFileName) {
        showError('No hay resultados de análisis disponibles para descargar.');
        return;
    }
    
    try {
        // Mostrar estado de carga en el botón
        const originalText = downloadPdfBtn.innerHTML;
        downloadPdfBtn.innerHTML = '<span class="btn-icon">⏳</span>Generando PDF...';
        downloadPdfBtn.disabled = true;
        
        const response = await fetch(`${API_BASE_URL}/generate-pdf`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                results: window.lastAnalysisResults,
                filename: window.lastFileName
            })
        });
        
        if (!response.ok) {
            throw new Error(`Error al generar PDF: ${response.status}`);
        }
        
        // Descargar el PDF
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `analisis_${window.lastFileName.replace('.csv', '')}_${new Date().toISOString().split('T')[0]}.pdf`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
        
        // Restaurar botón
        downloadPdfBtn.innerHTML = originalText;
        downloadPdfBtn.disabled = false;
        
    } catch (error) {
        console.error('Error al generar PDF:', error);
        showError('Error al generar el PDF. Intenta nuevamente.');
        
        // Restaurar botón en caso de error
        downloadPdfBtn.innerHTML = '<span class="btn-icon">📄</span>Descargar PDF';
        downloadPdfBtn.disabled = false;
    }
}

// Verificar si el servidor está disponible
async function checkServerStatus() {
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        if (!response.ok) {
            throw new Error('Servidor no disponible');
        }
        console.log('Servidor conectado correctamente');
    } catch (error) {
        console.warn('Servidor no disponible. Iniciando en modo sin conexión.');
        showError('No se puede conectar al servidor. Asegúrate de que esté ejecutándose en el puerto 5000.');
    }
}

function displayVisualizations(results) {
    const container = document.getElementById('visualizations');
    
    if (!container) {
        console.warn('Container for visualizations not found');
        return;
    }
    
    let html = '<div class="info-box"><h4>📊 Visualizaciones</h4>';
    
    // Matriz de correlación
    if (results.correlation_heatmap) {
        html += `
            <div class="visualization-section">
                <h5>🔥 Matriz de Correlación</h5>
                <div class="plot-container">
                    <img src="${results.correlation_heatmap}" alt="Matriz de Correlación" style="max-width: 100%; height: auto;">
                </div>
            </div>
        `;
    }
    
    // Histogramas
    if (results.histograms && results.histograms.length > 0) {
        html += '<div class="visualization-section"><h5>📈 Histogramas</h5><div class="plots-grid">';
        results.histograms.forEach((histogram, index) => {
            html += `
                <div class="plot-container">
                    <img src="${histogram}" alt="Histograma ${index + 1}" style="max-width: 100%; height: auto;">
                </div>
            `;
        });
        html += '</div></div>';
    }
    
    // Boxplots
    if (results.boxplots && results.boxplots.length > 0) {
        html += '<div class="visualization-section"><h5>📦 Boxplots</h5><div class="plots-grid">';
        results.boxplots.forEach((boxplot, index) => {
            html += `
                <div class="plot-container">
                    <img src="${boxplot}" alt="Boxplot ${index + 1}" style="max-width: 100%; height: auto;">
                </div>
            `;
        });
        html += '</div></div>';
    }
    
    // Si no hay visualizaciones
    if (!results.correlation_heatmap && (!results.histograms || results.histograms.length === 0) && (!results.boxplots || results.boxplots.length === 0)) {
        html += '<p>No se generaron visualizaciones para este dataset.</p>';
    }
    
    html += '</div>';
    container.innerHTML = html;
}

function displayAIInsights(insights) {
    const container = document.getElementById('aiInsights');
    
    if (!container) {
        console.warn('Container for AI insights not found');
        return;
    }
    
    if (!insights || insights.length === 0) {
        container.innerHTML = `
            <div class="info-box">
                <h4>🤖 Insights de IA</h4>
                <p>No se generaron insights para este dataset.</p>
            </div>
        `;
        return;
    }
    
    let html = `
        <div class="info-box">
            <h4>🤖 Insights de IA</h4>
            <div class="insights-list">
    `;
    
    insights.forEach(insight => {
        html += `<div class="insight-item">${insight}</div>`;
    });
    
    html += `
            </div>
        </div>
    `;
    
    container.innerHTML = html;
}

function displayColumnDistribution(dataTypes) {
    const container = document.getElementById('columnDistribution');
    
    if (!container) {
        console.warn('Container for column distribution not found');
        return;
    }
    
    if (!dataTypes || Object.keys(dataTypes).length === 0) {
        container.innerHTML = `
            <div class="info-box">
                <h4>📋 Distribución de Columnas</h4>
                <p>No se pudo obtener información sobre la distribución de columnas.</p>
            </div>
        `;
        return;
    }
    
    // Contar tipos de datos
    const typeCounts = {};
    Object.values(dataTypes).forEach(type => {
        typeCounts[type] = (typeCounts[type] || 0) + 1;
    });
    
    let html = `
        <div class="info-box">
            <h4>📋 Distribución de Columnas</h4>
            <div class="type-distribution">
    `;
    
    Object.entries(typeCounts).forEach(([type, count]) => {
        const percentage = ((count / Object.keys(dataTypes).length) * 100).toFixed(1);
        html += `
            <div class="type-item">
                <span class="type-label">${type}:</span>
                <span class="type-count">${count} columnas (${percentage}%)</span>
            </div>
        `;
    });
    
    html += `
            </div>
            <div class="columns-list">
                ${Object.entries(dataTypes).map(([col, type]) => 
                    `<span class="column-tag ${type.toLowerCase()}">${col} (${type})</span>`
                ).join('')}
            </div>
        </div>
    `;
    
    container.innerHTML = html;
}

// Verificar estado del servidor al cargar la página
checkServerStatus();
