# -*- coding: utf-8 -*-
from models.budget import (BudgetRepository, BudgetOwner, BudgetCategory,
                           BudgetItem, BudgetActual, RiskRule)


class BudgetService:
    def __init__(self):
        self.repo = BudgetRepository()

    # ===== 风险分类引擎 =====
    def classify_risk(self, budget, actual):
        """根据预算和实际数分类风险等级"""
        if budget is None or budget == 0:
            return None

        usage_rate = actual / budget if budget > 0 else 0
        variance_rate = (actual - budget) / budget

        if variance_rate > 0.05:
            return 'P0'
        elif usage_rate < 0.90:
            return 'P1'
        elif actual == 0:
            return 'P2'
        else:
            return 'P3'

    def classify_all_risks(self, item_id, budget):
        """对某个明细的所有月份进行风险分类"""
        actuals = self.repo.get_actuals_by_item(item_id)
        for actual in actuals:
            risk = self.classify_risk(budget, actual.actual_amount)
            actual.risk_level = risk
            self.repo.save_actual(actual)

    # ===== 三层结构 CRUD =====
    def get_tree(self):
        """获取完整三层树结构"""
        tree = self.repo.get_full_tree()

        # 为每个item附加实际数和风险分析
        for owner in tree:
            for cat in owner['categories']:
                for item in cat['items']:
                    actuals = self.repo.get_actuals_by_item(item['id'])
                    item['actuals'] = [a.to_dict() for a in actuals]

                    # 计算YTD累计
                    ytd_actual = sum(a.actual_amount for a in actuals)
                    item['ytd_actual'] = ytd_actual
                    item['variance'] = item['current_budget'] - ytd_actual
                    item['variance_rate'] = (
                        (item['current_budget'] - ytd_actual) / item['current_budget']
                        if item['current_budget'] > 0 else 0
                    )

        return tree

    def add_owner(self, name, feishu_group=None):
        owner = BudgetOwner(name=name, feishu_group=feishu_group)
        return self.repo.save_owner(owner)

    def add_category(self, owner_id, name):
        category = BudgetCategory(owner_id=owner_id, name=name)
        return self.repo.save_category(category)

    def add_item(self, category_id, item_name, original_budget=0, current_budget=0):
        item = BudgetItem(
            category_id=category_id,
            item_name=item_name,
            original_budget=original_budget,
            current_budget=current_budget
        )
        return self.repo.save_item(item)

    def update_item_budget(self, item_id, new_budget, changed_by=None):
        result = self.repo.update_item_budget(item_id, new_budget, changed_by)
        if result:
            # 重新计算风险
            self.classify_all_risks(item_id, new_budget)
        return result

    # ===== 实际数管理 =====
    def set_actual(self, item_id, month, actual_amount, reason=None):
        """设置某月实际数"""
        actual = BudgetActual(item_id=item_id, month=month, actual_amount=actual_amount)
        actual = self.repo.save_actual(actual)

        # 重新分类风险
        item = self.repo.get_item_by_id(item_id)
        if item:
            risk = self.classify_risk(item.current_budget, actual_amount)
            actual.risk_level = risk
            if reason:
                actual.reason = reason
            self.repo.save_actual(actual)

        return actual

    def batch_set_actuals(self, item_id, actuals_data):
        """批量设置实际数"""
        results = []
        for data in actuals_data:
            actual = self.set_actual(
                item_id,
                data['month'],
                data['actual_amount'],
                data.get('reason')
            )
            results.append(actual)
        return results

    # ===== 预实分析 =====
    def get_analysis(self, month=None, risk_level=None):
        """获取预实对比分析"""
        tree = self.get_tree()
        analysis = []

        for owner in tree:
            for cat in owner['categories']:
                for item in cat['items']:
                    actuals = item['actuals']

                    # 月份筛选
                    if month:
                        actuals = [a for a in actuals if a['month'] == month]

                    for actual in actuals:
                        # 风险筛选
                        if risk_level and actual.get('risk_level') != risk_level:
                            continue

                        analysis.append({
                            'owner_id': owner['id'],
                            'owner_name': owner['name'],
                            'category_name': cat['name'],
                            'item_id': item['id'],
                            'item_name': item['item_name'],
                            'budget': item['current_budget'],
                            'actual': actual['actual_amount'],
                            'month': actual['month'],
                            'variance': item['current_budget'] - actual['actual_amount'],
                            'variance_rate': (
                                (item['current_budget'] - actual['actual_amount']) / item['current_budget']
                                if item['current_budget'] > 0 else 0
                            ),
                            'risk_level': actual.get('risk_level'),
                            'reason': actual.get('reason')
                        })

        return analysis

    def get_risk_summary(self):
        """获取风险汇总统计"""
        tree = self.get_tree()
        summary = {'P0': 0, 'P1': 0, 'P2': 0, 'P3': 0}

        for owner in tree:
            for cat in owner['categories']:
                for item in cat['items']:
                    for actual in item['actuals']:
                        level = actual.get('risk_level')
                        if level and level in summary:
                            summary[level] += 1

        return summary

    # ===== 变更记录 =====
    def get_change_log(self, item_id=None):
        logs = self.repo.get_change_log(item_id)
        return [log.to_dict() for log in logs]

    # ===== 风险规则配置 =====
    def get_risk_rules(self):
        rules = self.repo.get_risk_rules()
        return [rule.to_dict() for rule in rules]

    def update_risk_rules(self, rules):
        self.repo.update_risk_rules(rules)
        # 重新分类所有风险
        tree = self.get_tree()
        for owner in tree:
            for cat in owner['categories']:
                for item in cat['items']:
                    self.classify_all_risks(item['id'], item['current_budget'])
        return True

    # ===== 权限管理 =====
    def get_permissions(self):
        perms = self.repo.get_permissions()
        return [p.to_dict() for p in perms]

    def add_permission(self, user_id, role='viewer', owner_id=None, feishu_group=None):
        from models.budget import Permission
        perm = Permission(user_id=user_id, role=role, owner_id=owner_id, feishu_group=feishu_group)
        return self.repo.save_permission(perm)

    # ===== 初始化示例数据 =====
    def init_sample_data(self):
        """初始化FY26真实预算数据（从Excel提取）"""
        import json
        import os

        # 读取真实数据
        json_path = os.path.join(os.path.dirname(__file__), '..', 'fy26_budget_data.json')
        if not os.path.exists(json_path):
            return {
                'success': False,
                'error': '未找到 fy26_budget_data.json 文件'
            }

        with open(json_path, 'r', encoding='utf-8') as f:
            data_rows = json.load(f)

        if not data_rows:
            return {
                'success': False,
                'error': '数据文件为空'
            }

        # 按项目（负责人）分组
        owners_map = {}
        for row in data_rows:
            project = row['project']
            if project not in owners_map:
                owners_map[project] = {
                    'owner': None,
                    'categories': {}
                }

            category = row['category']
            if category and category not in owners_map[project]['categories']:
                owners_map[project]['categories'][category] = {
                    'cat': None,
                    'items': []
                }

            owners_map[project]['categories'][category]['items'].append(row)

        # 创建负责人、板块、明细
        months_map = {
            'jan_actual': '2026-01',
            'feb_actual': '2026-02',
            'mar_actual': '2026-03',
            'apr_actual': '2026-04',
            'may_actual': '2026-05'
        }

        reasons_map = {
            '2026-01': 'jan_reason',
            '2026-02': 'feb_reason',
            '2026-03': 'mar_reason',
            '2026-04': 'apr_reason',
            '2026-05': 'may_reason'
        }

        created_count = 0
        for project, proj_data in owners_map.items():
            # 创建负责人
            owner = self.add_owner(project, None)
            proj_data['owner'] = owner

            for category, cat_data in proj_data['categories'].items():
                if not category:
                    continue

                # 创建板块
                cat = self.add_category(owner.id, category)
                cat_data['cat'] = cat

                for item_row in cat_data['items']:
                    item_name = item_row['item_name']
                    if not item_name:
                        continue

                    # 计算全年预算（取FY26预算合计）
                    # 这里先用YTD实际数的2倍作为当前预算估算
                    ytd_actual = sum([
                        item_row.get('jan_actual', 0),
                        item_row.get('feb_actual', 0),
                        item_row.get('mar_actual', 0),
                        item_row.get('apr_actual', 0),
                        item_row.get('may_actual', 0)
                    ])

                    # 预算估算：如果YTD有数据，按年化估算；否则设为0
                    estimated_budget = ytd_actual * 2.4 if ytd_actual > 0 else 0

                    # 创建明细
                    item = self.add_item(cat.id, item_name, estimated_budget, estimated_budget)

                    # 创建1-5月实际数
                    for month_key, month_str in months_map.items():
                        actual_amount = item_row.get(month_key, 0)
                        if actual_amount > 0 or month_key in ['jan_actual', 'feb_actual', 'mar_actual', 'apr_actual', 'may_actual']:
                            reason_key = reasons_map.get(month_str)
                            reason = item_row.get(reason_key, '') if reason_key else ''
                            self.set_actual(item.id, month_str, actual_amount, reason)

                    created_count += 1

        return {
            'success': True,
            'message': f'已初始化FY26真实数据：{created_count}条明细',
            'owners_count': len(owners_map),
            'items_count': created_count
        }

