const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const fileInfo = document.getElementById('file-info');
const uploadContent = document.querySelector('.upload-content');
const removeFileBtn = document.getElementById('remove-file');
const reconcileBtn = document.getElementById('reconcile-btn');
const statusArea = document.getElementById('status-area');
const loader = document.querySelector('.loader');
const btnText = document.querySelector('.btn-text');

const dashboard = document.getElementById('dashboard');
const downloadBtn = document.getElementById('download-btn');
const resetBtn = document.getElementById('reset-btn');

let currentFile = null;
let currentDownloadUrl = null;

// Drag & Drop
dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('drag-over');
});

dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('drag-over');
});

dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('drag-over');
    const files = e.dataTransfer.files;
    handleFiles(files);
});

dropZone.addEventListener('click', () => {
    if (!currentFile) {
        fileInput.click();
    }
});

fileInput.addEventListener('change', (e) => {
    handleFiles(e.target.files);
});

removeFileBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    resetFile();
});

function handleFiles(files) {
    if (files.length > 0) {
        const file = files[0];
        if (file.name.endsWith('.xlsx') || file.name.endsWith('.xls')) {
            currentFile = file;
            updateUIState(true);
        } else {
            showStatus('Please upload a valid Excel file (.xlsx, .xls)', 'error');
        }
    }
}

function updateUIState(hasFile) {
    if (hasFile) {
        uploadContent.style.display = 'none';
        fileInfo.style.display = 'flex';
        document.querySelector('.file-name').textContent = currentFile.name;
        reconcileBtn.disabled = false;
        dropZone.style.borderColor = 'var(--success)';
        showStatus('', '');
    } else {
        uploadContent.style.display = 'block';
        fileInfo.style.display = 'none';
        reconcileBtn.disabled = true;
        dropZone.style.borderColor = 'var(--glass-border)';
    }
}

function resetFile() {
    currentFile = null;
    fileInput.value = '';
    updateUIState(false);
}

function showStatus(msg, type) {
    statusArea.textContent = msg;
    statusArea.className = 'status-area';
    if (type) statusArea.classList.add(`status-${type}`);
}

reconcileBtn.addEventListener('click', async () => {
    if (!currentFile) return;

    setLoading(true);
    showStatus('Processing reconciliation... This usually takes less than a minute.', 'normal');

    // Hide upload zone while processing
    document.querySelector('.upload-zone').style.display = 'none';

    const formData = new FormData();
    formData.append('file', currentFile);

    try {
        const response = await fetch('/api/reconcile', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const errorText = await response.json();
            throw new Error(errorText.detail || 'Reconciliation failed');
        }

        const data = await response.json();

        // Handle Success
        handleSuccess(data);

    } catch (error) {
        console.error(error);
        showStatus(`❌ Error: ${error.message}`, 'error');
        document.querySelector('.upload-zone').style.display = 'block'; // Show upload again on error
    } finally {
        setLoading(false);
    }
});

// Chart instances
let pChart = null;
let bChart = null;

function handleSuccess(data) {
    showStatus('✅ Reconciliation Complete!', 'success');
    currentDownloadUrl = data.download_url;

    // Populate Dashboard
    renderStats('p', data.stats.portal);
    renderStats('b', data.stats.books);

    // Render Charts
    renderChart('p', data.stats.portal);
    renderChart('b', data.stats.books);

    // Show Dashboard
    dashboard.style.display = 'block';
}

function renderChart(prefix, stats) {
    const ctx = document.getElementById(`${prefix}-chart`).getContext('2d');

    // Destroy existing chart if any
    if (prefix === 'p' && pChart) pChart.destroy();
    if (prefix === 'b' && bChart) bChart.destroy();

    // Prepare Data for Bar Chart
    const labels = [];
    const dataValues = [];
    const backgroundColors = [];

    // Define colors for known categories
    // Dark Mode Theme Color Palette
    const colors = {
        'Exact Matched': '#10b981',      // Neon Green
        'Matched with multiple invoice in Portal data': '#3b82f6', // Bright Blue
        'Matched with multiple invoice in Books data': '#3b82f6', // Bright Blue
        'GSTIN Wise matched': '#8b5cf6', // Violet
        'Party wise matched': '#ec4899', // Pink
        'Unmatched': '#ef4444'           // Red
    };
    // Short Label Map for cleaner X-axis
    const shortLabels = {
        'Exact Matched': 'Exact',
        'Matched with multiple invoice in Portal data': 'Multi-Portal',
        'Matched with multiple invoice in Books data': 'Multi-Books',
        'GSTIN Wise matched': 'GSTIN',
        'Party wise matched': 'Party',
        'Unmatched': 'Unmatched'
    };
    // ... (labels loop same as before) ...

    // Add Matched Categories
    for (const [key, value] of Object.entries(stats.matched_breakdown)) {
        labels.push(shortLabels[key] || key);
        dataValues.push(value);
        backgroundColors.push(colors[key] || '#6366f1');
    }

    // Add Unmatched
    if (stats.unmatched > 0) {
        labels.push('Unmatched');
        dataValues.push(stats.unmatched);
        backgroundColors.push(colors['Unmatched']);
    }

    const config = {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Transactions',
                data: dataValues,
                backgroundColor: backgroundColors,
                borderWidth: 0,
                borderRadius: 8,
                barPercentage: 0.5,
                categoryPercentage: 0.8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: 'y',
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: 'rgba(15, 23, 42, 0.9)',
                    titleColor: '#f8fafc',
                    bodyColor: '#cbd5e1',
                    padding: 12,
                    cornerRadius: 8,
                    displayColors: true,
                    callbacks: {
                        label: function (context) {
                            let val = context.raw;
                            let total = stats.total;
                            let percentage = Math.round((val / total) * 100) + '%';
                            return ` ${val} (${percentage})`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: { display: false, drawBorder: false },
                    ticks: { display: false }
                },
                y: {
                    grid: { display: false, drawBorder: false },
                    ticks: {
                        color: '#94a3b8',
                        font: {
                            family: "'Outfit', sans-serif",
                            size: 11
                        },
                        autoSkip: false
                    }
                }
            },
            layout: {
                padding: { left: 0, right: 20 }
            }
        }
    };

    if (prefix === 'p') {
        pChart = new Chart(ctx, config);
    } else {
        bChart = new Chart(ctx, config);
    }
}

function renderStats(prefix, stats) {
    const matchedCount = stats.total - stats.unmatched;
    document.getElementById(`${prefix}-matched`).textContent = matchedCount;
    document.getElementById(`${prefix}-unmatched`).textContent = stats.unmatched;

    const detailsContainer = document.getElementById(`${prefix}-details`);
    detailsContainer.innerHTML = '';

    // Add Total row
    // const totalDiv = document.createElement('div');
    // totalDiv.className = 'detail-item';
    // totalDiv.innerHTML = `<span style="opacity:0.7">Total Records</span> <span>${stats.total}</span>`;
    // detailsContainer.appendChild(totalDiv);

    for (const [key, value] of Object.entries(stats.matched_breakdown)) {
        const div = document.createElement('div');
        div.className = 'detail-item';
        div.innerHTML = `<span>${key}</span> <span>${value}</span>`;
        detailsContainer.appendChild(div);
    }
}

downloadBtn.addEventListener('click', () => {
    if (currentDownloadUrl) {
        const a = document.createElement('a');
        a.href = currentDownloadUrl;
        a.download = 'GST_Reco_Output.xlsx';
        document.body.appendChild(a);
        a.click();

        // No auto remove since user might click again
    }
});

resetBtn.addEventListener('click', () => {
    dashboard.style.display = 'none';
    document.querySelector('.upload-zone').style.display = 'block';

    // Reset file selection
    resetFile();
    showStatus('', '');
});

function setLoading(isLoading) {
    if (isLoading) {
        reconcileBtn.disabled = true;
        btnText.style.visibility = 'hidden';
        loader.style.display = 'inline-block';
    } else {
        reconcileBtn.disabled = false;
        btnText.style.visibility = 'visible';
        loader.style.display = 'none';
    }
}

