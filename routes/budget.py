# -*- coding: utf-8 -*-
from flask import Blueprint, request, jsonify, render_template
import os
from datetime import datetime
from services.budget_service import BudgetService

budget_bp = Blueprint('budget', __name__, url_prefix='/api/budget')

UPLOAD_FOLDER = 'uploads/budget'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

budget_service = BudgetService()


@budget_bp.route('/import-excel', methods=['POST'])
def import_excel():
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': '没有文件'}), 400
    file = request.files['file']
    if not file.filename:
        return jsonify({'success': False, 'error': '没有选择文件'}), 400

    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{ts}_{file.filename}"
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(file_path)

    result = budget_service.import_excel(file_path)
    return jsonify(result)


@budget_bp.route('/import-preview', methods=['POST'])
def import_preview():
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': '没有文件'}), 400
    file = request.files['file']
    if not file.filename:
        return jsonify({'success': False, 'error': '没有选择文件'}), 400

    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{ts}_{file.filename}"
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(file_path)

    result = budget_service.preview_excel(file_path)
    return jsonify(result)


@budget_bp.route('/budget-data', methods=['GET'])
def get_budget_data():
    project = request.args.get('project')
    tag = request.args.get('tag')
    owner = request.args.get('owner')
    data = budget_service.get_budget_data(project, tag, owner)
    return jsonify({'success': True, 'data': data})


@budget_bp.route('/comparison-data', methods=['GET'])
def get_comparison_data():
    project = request.args.get('project')
    tag = request.args.get('tag')
    owner = request.args.get('owner')
    data = budget_service.get_comparison_data(project, tag, owner)
    return jsonify({'success': True, 'data': data})


@budget_bp.route('/actuals-data', methods=['GET'])
def get_actuals_data():
    project = request.args.get('project')
    tag = request.args.get('tag')
    owner = request.args.get('owner')
    data = budget_service.get_actuals_data(project, tag, owner)
    return jsonify({'success': True, 'data': data})


@budget_bp.route('/item/<int:item_id>/budget', methods=['PUT'])
def update_budget(item_id):
    data = request.json
    month = data.get('month')
    amount = data.get('amount', 0)
    changed_by = data.get('changed_by')
    result = budget_service.update_budget(item_id, month, amount, changed_by)
    return jsonify({'success': True, 'data': result})


@budget_bp.route('/item/<int:item_id>/actual', methods=['PUT'])
def update_actual(item_id):
    data = request.json
    month = data.get('month')
    amount = data.get('amount', 0)
    reason = data.get('reason')
    changed_by = data.get('changed_by')
    result = budget_service.update_actual(item_id, month, amount, reason, changed_by)
    return jsonify({'success': True, 'data': result})


@budget_bp.route('/item/<int:item_id>/reason', methods=['PUT'])
def update_reason(item_id):
    data = request.json
    month = data.get('month')
    reason = data.get('reason')
    budget_service.update_reason(item_id, month, reason)
    return jsonify({'success': True})


@budget_bp.route('/filter-options', methods=['GET'])
def get_filter_options():
    options = budget_service.get_filter_options()
    return jsonify({'success': True, 'data': options})


@budget_bp.route('/risk-summary', methods=['GET'])
def get_risk_summary():
    summary = budget_service.get_risk_summary()
    return jsonify({'success': True, 'data': summary})


@budget_bp.route('/change-log', methods=['GET'])
def get_change_log():
    item_id = request.args.get('item_id', type=int)
    logs = budget_service.get_change_log(item_id)
    return jsonify({'success': True, 'data': [l for l in logs]})


@budget_bp.route('/risk-rules', methods=['GET'])
def get_risk_rules():
    rules = budget_service.get_risk_rules()
    return jsonify({'success': True, 'data': rules})


@budget_bp.route('/risk-rules', methods=['PUT'])
def update_risk_rules():
    data = request.json
    rules = data.get('rules', [])
    budget_service.update_risk_rules(rules)
    return jsonify({'success': True})
