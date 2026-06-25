# -*- coding: utf-8 -*-
from flask import Blueprint, request, jsonify, send_file
import os
from datetime import datetime
from werkzeug.utils import secure_filename
from services.budget_service import BudgetService
from services.budget_parser import BudgetParser

budget_bp = Blueprint('budget', __name__, url_prefix='/api/budget')

UPLOAD_FOLDER = 'uploads/actuals'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

budget_service = BudgetService()


@budget_bp.route('/tree', methods=['GET'])
def get_tree():
    """获取完整三层树结构"""
    tree = budget_service.get_tree()
    return jsonify({'success': True, 'data': tree})


@budget_bp.route('/owner', methods=['POST'])
def add_owner():
    """新增负责人"""
    data = request.json
    owner = budget_service.add_owner(
        name=data.get('name'),
        feishu_group=data.get('feishu_group')
    )
    return jsonify({'success': True, 'data': owner.to_dict()})


@budget_bp.route('/category', methods=['POST'])
def add_category():
    """新增预算板块"""
    data = request.json
    category = budget_service.add_category(
        owner_id=data.get('owner_id'),
        name=data.get('name')
    )
    return jsonify({'success': True, 'data': category.to_dict()})


@budget_bp.route('/item', methods=['POST'])
def add_item():
    """新增预算明细"""
    data = request.json
    item = budget_service.add_item(
        category_id=data.get('category_id'),
        item_name=data.get('item_name'),
        original_budget=data.get('original_budget', 0),
        current_budget=data.get('current_budget', 0)
    )
    return jsonify({'success': True, 'data': item.to_dict()})


@budget_bp.route('/item/<int:item_id>', methods=['PUT'])
def update_item(item_id):
    """编辑预算明细（触发变更记录）"""
    data = request.json
    result = budget_service.update_item_budget(
        item_id,
        new_budget=data.get('current_budget'),
        changed_by=data.get('changed_by')
    )
    if result:
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False, 'error': '明细不存在'}), 404


@budget_bp.route('/actuals/upload', methods=['POST'])
def upload_actuals():
    """上传Excel实际数"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': '没有文件'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': '没有选择文件'}), 400

    # 保存文件
    filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{secure_filename(file.filename)}"
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(file_path)

    # 解析Excel
    parser = BudgetParser(file_path)
    results = parser.parse()

    if results is None:
        return jsonify({
            'success': False,
            'error': '解析失败',
            'details': parser.get_errors()
        }), 400

    # 匹配并保存实际数
    saved_count = 0
    tree = budget_service.get_tree()

    for result in results:
        # 查找匹配的item
        item_id = _find_item_id(tree, result)
        if item_id:
            budget_service.set_actual(
                item_id,
                result['month'],
                result['actual_amount'],
                result.get('reason')
            )
            saved_count += 1

    return jsonify({
        'success': True,
        'saved_count': saved_count,
        'total_count': len(results),
        'warnings': parser.get_warnings()
    })


@budget_bp.route('/actuals/<int:item_id>', methods=['GET'])
def get_actuals(item_id):
    """获取单项实际数"""
    actuals = budget_service.repo.get_actuals_by_item(item_id)
    return jsonify({'success': True, 'data': [a.to_dict() for a in actuals]})


@budget_bp.route('/actuals/<int:item_id>/<month>', methods=['PUT'])
def update_actual(item_id, month):
    """编辑实际数/理由"""
    data = request.json
    actual = budget_service.set_actual(
        item_id,
        month,
        data.get('actual_amount', 0),
        data.get('reason')
    )
    return jsonify({'success': True, 'data': actual.to_dict()})


@budget_bp.route('/analysis', methods=['GET'])
def get_analysis():
    """获取预实对比分析"""
    month = request.args.get('month')
    risk_level = request.args.get('level')
    analysis = budget_service.get_analysis(month, risk_level)
    return jsonify({'success': True, 'data': analysis})


@budget_bp.route('/risk-summary', methods=['GET'])
def get_risk_summary():
    """获取风险汇总"""
    summary = budget_service.get_risk_summary()
    return jsonify({'success': True, 'data': summary})


@budget_bp.route('/risk-items', methods=['GET'])
def get_risk_items():
    """按风险类型筛选明细"""
    level = request.args.get('level')
    analysis = budget_service.get_analysis(risk_level=level)
    return jsonify({'success': True, 'data': analysis})


@budget_bp.route('/risk-rules', methods=['GET'])
def get_risk_rules():
    """获取风险规则配置"""
    rules = budget_service.get_risk_rules()
    return jsonify({'success': True, 'data': rules})


@budget_bp.route('/risk-rules', methods=['PUT'])
def update_risk_rules():
    """更新风险规则"""
    data = request.json
    budget_service.update_risk_rules(data.get('rules', []))
    return jsonify({'success': True})


@budget_bp.route('/change-log', methods=['GET'])
def get_change_log():
    """获取预算变更历史"""
    item_id = request.args.get('item_id', type=int)
    logs = budget_service.get_change_log(item_id)
    return jsonify({'success': True, 'data': logs})


@budget_bp.route('/permissions', methods=['GET'])
def get_permissions():
    """获取权限列表"""
    perms = budget_service.get_permissions()
    return jsonify({'success': True, 'data': perms})


@budget_bp.route('/permissions', methods=['POST'])
def add_permission():
    """添加权限"""
    data = request.json
    perm = budget_service.add_permission(
        user_id=data.get('user_id'),
        role=data.get('role', 'viewer'),
        owner_id=data.get('owner_id'),
        feishu_group=data.get('feishu_group')
    )
    return jsonify({'success': True, 'data': perm.to_dict()})


@budget_bp.route('/init-sample', methods=['POST'])
def init_sample():
    """初始化1-5月示例数据"""
    result = budget_service.init_sample_data()
    return jsonify(result)


@budget_bp.route('/preview-upload', methods=['POST'])
def preview_upload():
    """预览Excel内容（不保存）"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': '没有文件'}), 400

    file = request.files['file']
    filename = f"preview_{secure_filename(file.filename)}"
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(file_path)

    parser = BudgetParser(file_path)
    results = parser.parse()
    unique_values = parser.get_unique_values()

    if results is None:
        return jsonify({
            'success': False,
            'error': '解析失败',
            'details': parser.get_errors()
        }), 400

    return jsonify({
        'success': True,
        'preview': results[:20],
        'unique_values': unique_values,
        'total_rows': len(results),
        'warnings': parser.get_warnings()
    })


def _find_item_id(tree, result):
    """在树结构中查找匹配的item_id"""
    for owner in tree:
        if owner['name'] != result['owner']:
            continue
        for cat in owner['categories']:
            if cat['name'] != result['category']:
                continue
            for item in cat['items']:
                if item['item_name'] == result['item_name']:
                    return item['id']
    return None


@budget_bp.route('/import-preview', methods=['POST'])
def import_preview():
    """预览预算 Excel 导入内容"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': '没有文件'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': '没有选择文件'}), 400

    filename = f"import_preview_{secure_filename(file.filename)}"
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(file_path)

    try:
        import pandas as pd
        df = pd.read_excel(file_path, engine='openpyxl')

        # 期望的列：负责人，板块，明细名称，原预算，当前预算
        required_cols = ['负责人', '板块', '明细名称']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            return jsonify({
                'success': False,
                'error': f'缺少列：{", ".join(missing_cols)}。需要列：负责人，板块，明细名称，原预算，当前预算'
            }), 400

        # 解析数据
        rows = []
        warnings = []
        owners_set = set()
        categories_set = set()

        for idx, row in df.iterrows():
            owner = str(row.get('负责人', '')).strip()
            category = str(row.get('板块', '')).strip()
            item_name = str(row.get('明细名称', '')).strip()

            if not owner or not category or not item_name:
                warnings.append(f'第{idx+2}行：负责人/板块/明细名称为空，已跳过')
                continue

            original_budget = float(row.get('原预算', 0) or 0)
            current_budget = float(row.get('当前预算', 0) or 0)

            rows.append({
                'owner': owner,
                'category': category,
                'item_name': item_name,
                'original_budget': original_budget,
                'current_budget': current_budget
            })
            owners_set.add(owner)
            categories_set.add(category)

        # 清理临时文件
        os.remove(file_path)

        return jsonify({
            'success': True,
            'total_rows': len(rows),
            'owners_count': len(owners_set),
            'categories_count': len(categories_set),
            'items_count': len(rows),
            'warnings': warnings[:10],  # 最多10条警告
            'preview': rows[:20]  # 预览前20条
        })
    except Exception as e:
        # 清理临时文件
        if os.path.exists(file_path):
            os.remove(file_path)
        return jsonify({'success': False, 'error': f'解析失败：{str(e)}'}), 500


@budget_bp.route('/import', methods=['POST'])
def import_budget():
    """批量导入预算数据"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': '没有文件'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': '没有选择文件'}), 400

    filename = f"import_{secure_filename(file.filename)}"
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(file_path)

    try:
        import pandas as pd
        df = pd.read_excel(file_path, engine='openpyxl')

        required_cols = ['负责人', '板块', '明细名称']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            return jsonify({
                'success': False,
                'error': f'缺少列：{", ".join(missing_cols)}'
            }), 400

        # 按负责人分组导入
        owners_created = 0
        categories_created = 0
        items_created = 0

        for owner_name in df['负责人'].unique():
            owner_df = df[df['负责人'] == owner_name]

            # 创建或获取负责人
            owner = budget_service.add_owner(owner_name, None)
            owners_created += 1

            for category_name in owner_df['板块'].unique():
                cat_df = owner_df[owner_df['板块'] == category_name]

                # 创建或获取板块
                cat = budget_service.add_category(owner.id, category_name)
                categories_created += 1

                for _, row in cat_df.iterrows():
                    item_name = str(row.get('明细名称', '')).strip()
                    if not item_name:
                        continue

                    original_budget = float(row.get('原预算', 0) or 0)
                    current_budget = float(row.get('当前预算', 0) or 0)

                    # 创建明细
                    budget_service.add_item(cat.id, item_name, original_budget, current_budget)
                    items_created += 1

        # 清理临时文件
        os.remove(file_path)

        return jsonify({
            'success': True,
            'owners_count': owners_created,
            'categories_count': categories_created,
            'items_count': items_created
        })
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        return jsonify({'success': False, 'error': f'导入失败：{str(e)}'}), 500


@budget_bp.route('/actuals-preview', methods=['POST'])
def actuals_preview():
    """预览实际数 Excel 内容"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': '没有文件'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': '没有选择文件'}), 400

    filename = f"actuals_preview_{secure_filename(file.filename)}"
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(file_path)

    try:
        import pandas as pd
        df = pd.read_excel(file_path, engine='openpyxl')

        required_cols = ['负责人', '板块', '明细名称', '月份', '实际金额']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            return jsonify({
                'success': False,
                'error': f'缺少列：{", ".join(missing_cols)}。需要列：负责人，板块，明细名称，月份，实际金额，变动理由'
            }), 400

        # 解析数据
        rows = []
        warnings = []
        matched_count = 0
        unmatched_count = 0

        tree = budget_service.get_tree()

        for idx, row in df.iterrows():
            owner = str(row.get('负责人', '')).strip()
            category = str(row.get('板块', '')).strip()
            item_name = str(row.get('明细名称', '')).strip()
            month = str(row.get('月份', '')).strip()
            actual_amount = float(row.get('实际金额', 0) or 0)
            reason = str(row.get('变动理由', '')).strip()

            if not owner or not category or not item_name or not month:
                warnings.append(f'第{idx+2}行：关键字段为空，已跳过')
                unmatched_count += 1
                continue

            # 匹配明细 ID
            item_id = find_item_id(tree, owner, category, item_name)

            if item_id:
                matched_count += 1
            else:
                unmatched_count += 1
                warnings.append(f'第{idx+2}行：未找到匹配的明细 [{owner}/{category}/{item_name}]')

            rows.append({
                'owner': owner,
                'category': category,
                'item_name': item_name,
                'month': month,
                'actual_amount': actual_amount,
                'reason': reason,
                'matched': item_id is not None
            })

        os.remove(file_path)

        return jsonify({
            'success': True,
            'total_rows': len(rows),
            'matched_count': matched_count,
            'unmatched_count': unmatched_count,
            'warnings': warnings[:10],
            'preview': rows[:20]
        })
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        return jsonify({'success': False, 'error': f'解析失败：{str(e)}'}), 500


@budget_bp.route('/actuals-upload', methods=['POST'])
def actuals_upload():
    """上传实际数数据"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': '没有文件'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': '没有选择文件'}), 400

    filename = f"actuals_{secure_filename(file.filename)}"
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(file_path)

    try:
        import pandas as pd
        df = pd.read_excel(file_path, engine='openpyxl')

        required_cols = ['负责人', '板块', '明细名称', '月份', '实际金额']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            return jsonify({
                'success': False,
                'error': f'缺少列：{", ".join(missing_cols)}'
            }), 400

        tree = budget_service.get_tree()
        matched_count = 0
        unmatched_count = 0

        for idx, row in df.iterrows():
            owner = str(row.get('负责人', '')).strip()
            category = str(row.get('板块', '')).strip()
            item_name = str(row.get('明细名称', '')).strip()
            month = str(row.get('月份', '')).strip()
            actual_amount = float(row.get('实际金额', 0) or 0)
            reason = str(row.get('变动理由', '')).strip()

            if not owner or not category or not item_name or not month:
                unmatched_count += 1
                continue

            item_id = find_item_id(tree, owner, category, item_name)

            if item_id:
                budget_service.set_actual(item_id, month, actual_amount, reason)
                matched_count += 1
            else:
                unmatched_count += 1

        os.remove(file_path)

        return jsonify({
            'success': True,
            'matched_count': matched_count,
            'unmatched_count': unmatched_count
        })
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        return jsonify({'success': False, 'error': f'上传失败：{str(e)}'}), 500


@budget_bp.route('/actuals-list', methods=['GET'])
def actuals_list():
    """获取所有实际数记录"""
    actuals = budget_service.get_all_actuals()
    return jsonify({'success': True, 'data': actuals})
