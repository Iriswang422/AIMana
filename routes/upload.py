from flask import Blueprint, request, jsonify, current_app
import os
from werkzeug.utils import secure_filename
from datetime import datetime

upload_bp = Blueprint('upload', __name__)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

@upload_bp.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': '没有文件'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400

    if file and allowed_file(file.filename):
        original_filename = file.filename
        filename = secure_filename(original_filename)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
        filename = timestamp + filename

        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        excel_service = current_app.config['EXCEL_SERVICE']
        fields = excel_service.get_fields(file_path)

        return jsonify({
            'success': True,
            'filename': filename,
            'original_filename': original_filename,
            'file_path': file_path,
            'fields': fields
        })

    return jsonify({'error': '不支持的文件格式，只支持.xlsx和.xls'}), 400

@upload_bp.route('/api/preview/<filename>')
def preview_file(filename):
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(file_path):
        return jsonify({'error': '文件不存在'}), 404

    excel_service = current_app.config['EXCEL_SERVICE']
    preview_data = excel_service.preview(file_path)

    return jsonify(preview_data)

@upload_bp.route('/api/filter-options/<filename>')
def get_filter_options(filename):
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(file_path):
        return jsonify({'error': '文件不存在'}), 404

    excel_service = current_app.config['EXCEL_SERVICE']
    options = excel_service.get_filter_options(file_path)

    return jsonify({'success': True, 'options': options})
