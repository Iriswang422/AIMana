from flask import Blueprint, request, jsonify, current_app, send_file
from services.filter_service import FilterService
import os

filter_bp = Blueprint('filter', __name__)

@filter_bp.route('/api/filter', methods=['POST'])
def execute_filter():
    data = request.json
    file_path = data['file_path']
    original_filename = data.get('original_filename', os.path.basename(file_path))

    conditions = data.get('conditions', [])
    rule_id = data.get('rule_id')

    filter_service = current_app.config['FILTER_SERVICE']

    try:
        if rule_id:
            result = filter_service.process_filter(
                file_path,
                rule_id,
                original_filename
            )
        else:
            result = filter_service.process_filter_with_conditions(
                file_path,
                conditions,
                original_filename
            )

        return jsonify({
            'success': True,
            'row_count': result['row_count'],
            'result_filename': result['result_filename']
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@filter_bp.route('/api/download/<filename>')
def download_file(filename):
    file_path = os.path.join(current_app.config['DOWNLOAD_FOLDER'], filename)

    if not os.path.exists(file_path):
        return jsonify({'error': '文件不存在'}), 404

    return send_file(
        file_path,
        as_attachment=True,
        download_name=filename,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
