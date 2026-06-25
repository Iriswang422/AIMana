let currentFile = null;
let resultFilename = null;
let filterOptions = {};

async function handleUpload() {
    const fileInput = document.getElementById('file-input');
    const statusDiv = document.getElementById('upload-status');

    if (!fileInput.files.length) {
        statusDiv.className = 'status-error';
        statusDiv.textContent = '请选择文件';
        return;
    }

    const file = fileInput.files[0];
    const formData = new FormData();
    formData.append('file', file);

    statusDiv.textContent = '上传中...';
    statusDiv.className = '';

    try {
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.success) {
            currentFile = {
                filename: data.filename,
                original_filename: data.original_filename,
                file_path: data.file_path,
                fields: data.fields
            };

            statusDiv.className = 'status-success';
            statusDiv.textContent = '上传成功！';

            document.getElementById('file-info').style.display = 'block';
            document.getElementById('filename').textContent = data.original_filename;

            await loadFilterOptions();
        } else {
            statusDiv.className = 'status-error';
            statusDiv.textContent = '上传失败：' + data.error;
        }
    } catch (error) {
        statusDiv.className = 'status-error';
        statusDiv.textContent = '上传失败：' + error.message;
    }
}

async function loadFilterOptions() {
    try {
        const response = await fetch(`/api/filter-options/${currentFile.filename}`);
        const data = await response.json();

        if (data.success) {
            filterOptions = data.options;

            populateSelect('filter-project', data.options['项目'] || []);
            populateSelect('filter-month', data.options['采购发包月'] || []);
            populateSelect('filter-fee-unit', data.options['费用子单元'] || []);

            document.getElementById('filter-section').style.display = 'block';
        } else {
            alert('加载筛选选项失败：' + (data.error || '未知错误'));
        }
    } catch (error) {
        console.error('加载筛选选项失败:', error);
        alert('加载筛选选项失败：' + error.message);
    }
}

function populateSelect(elementId, options) {
    const select = document.getElementById(elementId);
    select.innerHTML = '';

    options.forEach(option => {
        const opt = document.createElement('option');
        opt.value = option;
        opt.textContent = option || '(空)';
        select.appendChild(opt);
    });
}

async function showPreview() {
    if (!currentFile) return;

    const response = await fetch(`/api/preview/${currentFile.filename}`);
    const data = await response.json();

    const container = document.getElementById('preview-container');
    const table = document.getElementById('preview-table');

    let html = '<thead><tr>';
    data.fields.forEach(field => {
        html += `<th>${field}</th>`;
    });
    html += '</tr></thead><tbody>';

    data.rows.forEach(row => {
        html += '<tr>';
        row.forEach(cell => {
            html += `<td>${cell}</td>`;
        });
        html += '</tr>';
    });
    html += '</tbody>';

    table.innerHTML = html;
    container.style.display = 'block';
}

function getSelectedValues(elementId) {
    const select = document.getElementById(elementId);
    const selected = Array.from(select.selectedOptions).map(opt => opt.value);
    return selected;
}

async function executeFilter() {
    if (!currentFile) {
        alert('请先上传文件');
        return;
    }

    const projects = getSelectedValues('filter-project');
    const months = getSelectedValues('filter-month');
    const feeUnits = getSelectedValues('filter-fee-unit');

    const conditions = [];

    if (projects.length > 0) {
        conditions.push({ field: '项目', operator: 'in', value: projects });
    }

    if (months.length > 0) {
        conditions.push({ field: '采购发包月', operator: 'in', value: months });
    }

    if (feeUnits.length > 0) {
        conditions.push({ field: '费用子单元', operator: 'in', value: feeUnits });
    }

    try {
        const response = await fetch('/api/filter', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                file_path: currentFile.file_path,
                conditions: conditions,
                original_filename: currentFile.original_filename
            })
        });

        const data = await response.json();

        if (data.success) {
            resultFilename = data.result_filename;
            document.getElementById('result-row-count').textContent = data.row_count;
            document.getElementById('result-section').style.display = 'block';
        } else {
            alert('筛选失败：' + data.error);
        }
    } catch (error) {
        alert('筛选失败：' + error.message);
    }
}

function downloadResult() {
    if (resultFilename) {
        window.location.href = `/api/download/${resultFilename}`;
    }
}
