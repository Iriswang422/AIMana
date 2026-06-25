# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify, send_file, render_template_string, render_template
import pandas as pd
import os
from datetime import datetime
from db import init_db

app = Flask(__name__)

# 注册报告Blueprint
from routes.report import report_bp
app.register_blueprint(report_bp)

# 注册预算Blueprint
from routes.budget import budget_bp
app.register_blueprint(budget_bp)

init_db()

UPLOAD_FOLDER = 'uploads'
DOWNLOAD_FOLDER = 'downloads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

OUTPUT_COLUMNS = [
    '采购发包月', '项目', '费用子单元', '商品信息', '采购品类',
    '工序类型', '工序品级', '含税总价', '订单币种', '实付金额',
    '结算币种', '研运项目二类', '业务线', '结算状态', '供应商',
    '付款主体', '数据源', '应计提金额'
]

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/report')
def report_dashboard():
    return render_template('report/dashboard.html')

@app.route('/budget')
def budget_dashboard():
    return render_template('budget/dashboard.html')

@app.route('/api/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({'error': '没有文件'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400

    filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(file_path)

    df = pd.read_excel(file_path, engine='openpyxl')

    # 添加计算字段
    if '采购发包日' in df.columns:
        df['采购发包月'] = df['采购发包日'].apply(
            lambda x: str(int(pd.to_datetime(x).month)) if pd.notna(x) else ''
        )

    # 获取筛选选项
    options = {}
    available_filters = []
    missing_filters = []

    for col in ['项目', '采购发包月', '费用子单元']:
        if col in df.columns:
            available_filters.append(col)
            unique_vals = [str(x) for x in df[col].dropna().unique()]
            options[col] = sorted([v for v in unique_vals if v])
        else:
            missing_filters.append(col)

    return jsonify({
        'success': True,
        'filename': filename,
        'options': options,
        'row_count': len(df),
        'columns_found': list(df.columns),
        'available_filters': available_filters,
        'missing_filters': missing_filters
    })

@app.route('/api/filter', methods=['POST'])
def do_filter():
    data = request.json
    file_path = os.path.join(UPLOAD_FOLDER, data['filename'])

    if not os.path.exists(file_path):
        return jsonify({'error': '文件不存在'}), 404

    df = pd.read_excel(file_path, engine='openpyxl')

    # 添加计算字段
    if '采购发包日' in df.columns:
        df['采购发包月'] = df['采购发包日'].apply(
            lambda x: str(int(pd.to_datetime(x).month)) if pd.notna(x) else ''
        )

    # 应用筛选
    conditions = data.get('conditions', {})

    if conditions.get('项目'):
        df = df[df['项目'].isin(conditions['项目'])]
    if conditions.get('采购发包月'):
        df = df[df['采购发包月'].isin(conditions['采购发包月'])]
    if conditions.get('费用子单元'):
        df['费用子单元'] = df['费用子单元'].apply(lambda x: str(x).replace('-', '—') if pd.notna(x) else x)
        df = df[df['费用子单元'].isin(conditions['费用子单元'])]

    # 准备输出
    df['数据源'] = '发行美宣'
    if '订单币种' in df.columns:
        df['订单币种'] = df['订单币种'].fillna('CNY')
    else:
        df['订单币种'] = 'CNY'

    # 计算应计提金额
    if '实付金额' in df.columns and '含税总价' in df.columns:
        def calc_accrual(row):
            try:
                paid = pd.to_numeric(row.get('实付金额', 0), errors='coerce')
                total = pd.to_numeric(row.get('含税总价', 0), errors='coerce')
                if pd.isna(paid) or pd.isna(total) or total == 0:
                    return 0
                ratio = paid / total
                return 0 if ratio >= 0.8 else total - paid
            except:
                return 0
        df['应计提金额'] = df.apply(calc_accrual, axis=1)

    # 选择输出列
    available_cols = [col for col in OUTPUT_COLUMNS if col in df.columns]
    result = df[available_cols]

    # 保存
    result_filename = f"result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    result_path = os.path.join(DOWNLOAD_FOLDER, result_filename)
    result.to_excel(result_path, index=False, engine='openpyxl')

    return jsonify({
        'success': True,
        'result_filename': result_filename,
        'row_count': len(result)
    })

@app.route('/api/download/<filename>')
def download(filename):
    file_path = os.path.join(DOWNLOAD_FOLDER, filename)
    if not os.path.exists(file_path):
        return jsonify({'error': '文件不存在'}), 404
    return send_file(file_path, as_attachment=True)

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>发行美宣预提小工具</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 40px auto; padding: 20px; }
        h1 { color: #2c3e50; text-align: center; }
        .section { margin-bottom: 30px; padding: 20px; background: #f9f9f9; border-radius: 8px; }
        button { padding: 10px 20px; background: #3498db; color: white; border: none; border-radius: 4px; cursor: pointer; }
        button:hover { background: #2980b9; }
        .primary-btn { background: #27ae60; }
        .primary-btn:hover { background: #229954; }
        select { width: 100%; min-height: 100px; margin: 10px 0; }
        .hint { font-size: 12px; color: #999; }
        #status { margin-top: 10px; padding: 8px; border-radius: 4px; }
        .success { background: #d4edda; color: #155724; }
        .error { background: #f8d7da; color: #721c24; }
    </style>
</head>
<body>
    <h1>发行美宣预提小工具</h1>

    <div class="section">
        <h2>1. 上传文件</h2>
        <input type="file" id="file-input" accept=".xlsx">
        <button onclick="uploadFile()">上传</button>
        <div id="status"></div>
    </div>

    <div class="section" id="filter-section" style="display:none;">
        <h2>2. 设置筛选条件</h2>
        <p>数据行数：<span id="row-count"></span></p>

        <div id="project-group">
            <label><strong>项目：</strong></label>
            <select id="filter-project" multiple></select>
            <span class="hint">按住 Ctrl 可多选</span>
        </div>

        <div id="month-group">
            <label><strong>采购发包月：</strong></label>
            <select id="filter-month" multiple></select>
            <span class="hint">按住 Ctrl 可多选</span>
        </div>

        <div id="fee-unit-group">
            <label><strong>费用子单元：</strong></label>
            <select id="filter-fee-unit" multiple></select>
            <span class="hint">按住 Ctrl 可多选</span>
        </div>

        <br><br>
        <button onclick="doFilter()" class="primary-btn">执行筛选并导出</button>
    </div>

    <div class="section" id="result-section" style="display:none;">
        <h2>3. 下载结果</h2>
        <p>筛选完成，共 <strong id="result-count"></strong> 行</p>
        <button onclick="downloadResult()" class="primary-btn">下载 Excel</button>
    </div>

    <script>
        let currentFile = null;
        let resultFile = null;

        async function uploadFile() {
            const input = document.getElementById('file-input');
            const status = document.getElementById('status');

            if (!input.files.length) {
                status.className = 'error';
                status.textContent = '请选择文件';
                return;
            }

            const formData = new FormData();
            formData.append('file', input.files[0]);

            status.textContent = '上传中...';

            try {
                const res = await fetch('/api/upload', { method: 'POST', body: formData });
                const data = await res.json();

                if (data.success) {
                    currentFile = data.filename;
                    status.className = 'success';

                    // 显示调试信息
                    let debugInfo = '上传成功！';
                    if (data.missing_filters && data.missing_filters.length > 0) {
                        debugInfo += '\\n警告：未找到筛选字段：' + data.missing_filters.join(', ');
                    }
                    if (data.available_filters) {
                        debugInfo += '\\n可用筛选：' + data.available_filters.join(', ');
                    }
                    status.textContent = debugInfo;

                    document.getElementById('row-count').textContent = data.row_count;

                    // 填充筛选选项
                    populateSelect('filter-project', data.options['项目'] || []);
                    populateSelect('filter-month', data.options['采购发包月'] || []);
                    populateSelect('filter-fee-unit', data.options['费用子单元'] || []);

                    // 显示或隐藏筛选项
                    document.getElementById('project-group').style.display = data.options['项目'] ? 'block' : 'none';
                    document.getElementById('month-group').style.display = data.options['采购发包月'] ? 'block' : 'none';
                    document.getElementById('fee-unit-group').style.display = data.options['费用子单元'] ? 'block' : 'none';

                    document.getElementById('filter-section').style.display = 'block';

                    // 控制台输出详细信息
                    console.log('上传响应:', data);
                    console.log('所有列:', data.columns_found);
                } else {
                    status.className = 'error';
                    status.textContent = '上传失败：' + data.error;
                }
            } catch (e) {
                status.className = 'error';
                status.textContent = '上传失败：' + e.message;
                console.error('上传错误:', e);
            }
        }

        function populateSelect(id, options) {
            const select = document.getElementById(id);
            select.innerHTML = '';
            options.forEach(opt => {
                const option = document.createElement('option');
                option.value = opt;
                option.textContent = opt || '(空)';
                select.appendChild(option);
            });
        }

        async function doFilter() {
            const conditions = {
                '项目': getSelected('filter-project'),
                '采购发包月': getSelected('filter-month'),
                '费用子单元': getSelected('filter-fee-unit')
            };

            try {
                const res = await fetch('/api/filter', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ filename: currentFile, conditions })
                });
                const data = await res.json();

                if (data.success) {
                    resultFile = data.result_filename;
                    document.getElementById('result-count').textContent = data.row_count;
                    document.getElementById('result-section').style.display = 'block';
                } else {
                    alert('筛选失败：' + data.error);
                }
            } catch (e) {
                alert('筛选失败：' + e.message);
            }
        }

        function getSelected(id) {
            const select = document.getElementById(id);
            return Array.from(select.selectedOptions).map(o => o.value);
        }

        function downloadResult() {
            if (resultFile) {
                window.location.href = '/api/download/' + resultFile;
            }
        }
    </script>
</body>
</html>
'''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)
