# -*- coding: utf-8 -*-
from flask import Blueprint, request, jsonify, send_file, render_template
import os
from datetime import datetime
from werkzeug.utils import secure_filename
from services.report_parser import ReportParser
from services.report_service import ReportService

report_bp = Blueprint('report', __name__, url_prefix='/api/report')

UPLOAD_FOLDER = 'uploads/reports'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

report_service = ReportService()


@report_bp.route('/list', methods=['GET'])
def list_reports():
    """列出所有报告"""
    status = request.args.get('status')
    reports = report_service.list_reports(status=status)
    return jsonify({
        'success': True,
        'reports': reports
    })


@report_bp.route('/upload', methods=['POST'])
def upload_report():
    """上传并解析新月度报告"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': '没有文件'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': '没有选择文件'}), 400

    if not file.filename.endswith(('.xlsx', '.xls')):
        return jsonify({'success': False, 'error': '只支持Excel文件(.xlsx, .xls)'}), 400

    # 获取期间和标题
    period = request.form.get('period')
    title = request.form.get('title', f'{period} 竞技工作室经营月报')

    if not period:
        return jsonify({'success': False, 'error': '必须提供期间(period)'}), 400

    # 保存文件
    filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{secure_filename(file.filename)}"
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(file_path)

    # 解析文件
    parser = ReportParser(file_path)
    parsed_data = parser.parse()

    if parsed_data is None:
        errors = parser.get_errors()
        return jsonify({
            'success': False,
            'error': '解析失败',
            'details': errors
        }), 400

    # 创建报告
    try:
        report = report_service.create_report(
            period=period,
            title=title,
            raw_filename=filename,
            parsed_data=parsed_data
        )

        return jsonify({
            'success': True,
            'report': report.to_dict(),
            'warnings': parser.get_warnings()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'保存报告失败: {str(e)}'
        }), 500


@report_bp.route('/<period>/summary', methods=['GET'])
def get_summary(period):
    """获取报告摘要"""
    summary = report_service.get_report_summary(period)
    if not summary:
        return jsonify({'success': False, 'error': '报告不存在'}), 404

    return jsonify({
        'success': True,
        'data': summary
    })


@report_bp.route('/<period>/budget', methods=['GET'])
def get_budget(period):
    """获取预算vs实际对比"""
    budget = report_service.get_budget_comparison(period)
    if not budget:
        return jsonify({'success': False, 'error': '报告不存在'}), 404

    return jsonify({
        'success': True,
        'data': budget
    })


@report_bp.route('/<period>/projects', methods=['GET'])
def get_projects(period):
    """获取所有项目概览"""
    project_name = request.args.get('project')
    projects = report_service.get_project_analysis(period, project_name)
    if not projects:
        return jsonify({'success': False, 'error': '报告不存在'}), 404

    return jsonify({
        'success': True,
        'data': projects
    })


@report_bp.route('/<period>/project/<name>', methods=['GET'])
def get_project_detail(period, name):
    """获取单个项目详情"""
    projects = report_service.get_project_analysis(period, name)
    if not projects or not projects['projects']:
        return jsonify({'success': False, 'error': '项目不存在'}), 404

    return jsonify({
        'success': True,
        'data': projects['projects'][0]
    })


@report_bp.route('/<period>/revenue', methods=['GET'])
def get_revenue(period):
    """获取收入分析"""
    project_name = request.args.get('project')
    revenue = report_service.get_revenue_analysis(period, project_name)
    if not revenue:
        return jsonify({'success': False, 'error': '报告不存在'}), 404

    return jsonify({
        'success': True,
        'data': revenue
    })


@report_bp.route('/<period>/cost', methods=['GET'])
def get_cost(period):
    """获取成本分析"""
    project_name = request.args.get('project')
    cost = report_service.get_cost_analysis(period, project_name)
    if not cost:
        return jsonify({'success': False, 'error': '报告不存在'}), 404

    return jsonify({
        'success': True,
        'data': cost
    })


@report_bp.route('/<period>/contingency', methods=['GET'])
def get_contingency(period):
    """获取机动资金使用情况"""
    contingency = report_service.get_contingency_fund(period)
    if not contingency:
        return jsonify({'success': False, 'error': '报告不存在'}), 404

    return jsonify({
        'success': True,
        'data': contingency
    })


@report_bp.route('/compare', methods=['GET'])
def compare_periods():
    """对比两个期间"""
    period1 = request.args.get('from')
    period2 = request.args.get('to')

    if not period1 or not period2:
        return jsonify({
            'success': False,
            'error': '必须提供from和to参数'
        }), 400

    comparison = report_service.compare_periods(period1, period2)
    if not comparison:
        return jsonify({'success': False, 'error': '一个或两个报告不存在'}), 404

    return jsonify({
        'success': True,
        'data': comparison
    })


@report_bp.route('/<period>/publish', methods=['POST'])
def publish_report(period):
    """发布报告"""
    report = report_service.publish_report(period)
    if not report:
        return jsonify({'success': False, 'error': '报告不存在'}), 404

    return jsonify({
        'success': True,
        'report': report.to_dict()
    })


@report_bp.route('/<period>/unpublish', methods=['POST'])
def unpublish_report(period):
    """取消发布报告"""
    report = report_service.unpublish_report(period)
    if not report:
        return jsonify({'success': False, 'error': '报告不存在'}), 404

    return jsonify({
        'success': True,
        'report': report.to_dict()
    })


@report_bp.route('/<period>/delete', methods=['DELETE'])
def delete_report(period):
    """删除报告"""
    report = report_service.repo.get_report_by_period(period)
    if not report:
        return jsonify({'success': False, 'error': '报告不存在'}), 404

    report_service.repo.delete_report(report.id)

    return jsonify({
        'success': True,
        'message': '报告已删除'
    })


@report_bp.route('/template', methods=['GET'])
def download_template():
    """下载Excel模板"""
    template_path = 'templates/report_template.xlsx'
    if not os.path.exists(template_path):
        return jsonify({'success': False, 'error': '模板文件不存在'}), 404

    return send_file(
        template_path,
        as_attachment=True,
        download_name='月报模板.xlsx'
    )
