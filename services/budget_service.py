# -*- coding: utf-8 -*-
from models.budget import BudgetRepository, BudgetItem
from services.budget_parser import BudgetExcelParser


class BudgetService:
    def __init__(self):
        self.repo = BudgetRepository()

    def classify_risk(self, budget, actual):
        if budget is None or budget == 0:
            if actual and actual > 0:
                return 'P0'
            return 'P3'
        if actual is None or actual == 0:
            return 'P2'
        variance_rate = (actual - budget) / budget
        if variance_rate > 0.05:
            return 'P0'
        elif actual / budget < 0.90:
            return 'P1'
        else:
            return 'P3'

    # ===== Excel Import =====
    def import_excel(self, file_path):
        parser = BudgetExcelParser(file_path)
        data = parser.parse_all()
        if data is None:
            return {'success': False, 'error': '; '.join(parser.get_errors())}

        self.repo.delete_all_items()

        key_to_id = {}
        for item_data in data['items']:
            item = BudgetItem(
                project=item_data['project'],
                tag=item_data['tag'],
                business_scene=item_data['business_scene'],
                vendor=item_data['vendor'],
                detail=item_data['detail'],
                owner=item_data['owner'],
            )
            saved = self.repo.save_item(item)
            key = (item_data['project'], item_data['tag'], item_data['business_scene'],
                   item_data['vendor'], item_data['detail'], item_data['owner'])
            key_to_id[key] = saved.id

        budget_map = {}
        for rec in data['budget_monthly']:
            item_id = key_to_id.get(rec['key'])
            if item_id:
                k = (item_id, rec['month'])
                budget_map[k] = budget_map.get(k, 0) + rec['amount']

        for (item_id, month), amount in budget_map.items():
            self.repo.set_budget(item_id, month, amount)

        actual_map = {}
        for rec in data['actual_monthly']:
            item_id = key_to_id.get(rec['key'])
            if item_id:
                k = (item_id, rec['month'])
                actual_map[k] = actual_map.get(k, 0) + rec['amount']

        all_budgets = self.repo.get_all_budgets()
        for (item_id, month), amount in actual_map.items():
            budget_val = all_budgets.get(item_id, {}).get(month, 0)
            risk = self.classify_risk(budget_val, amount)
            self.repo.set_actual(item_id, month, amount, risk_level=risk)

        return {
            'success': True,
            'items_count': len(data['items']),
            'budget_records': len(data['budget_monthly']),
            'actual_records': len(data['actual_monthly']),
        }

    def preview_excel(self, file_path):
        parser = BudgetExcelParser(file_path)
        preview = parser.get_preview()
        if preview is None:
            return {'success': False, 'error': '; '.join(parser.get_errors())}
        preview['success'] = True
        return preview

    # ===== Tab Data =====
    def get_budget_data(self, project=None, tag=None, owner=None):
        items = self.repo.get_all_items()
        all_budgets = self.repo.get_all_budgets()
        return self._build_tab_data(items, all_budgets, 'budget', project, tag, owner)

    def get_comparison_data(self, project=None, tag=None, owner=None):
        items = self.repo.get_all_items()
        all_budgets = self.repo.get_all_budgets()
        all_actuals = self.repo.get_all_actuals()
        return self._build_comparison_data(items, all_budgets, all_actuals, project, tag, owner)

    def get_actuals_data(self, project=None, tag=None, owner=None):
        items = self.repo.get_all_items()
        all_actuals = self.repo.get_all_actuals()
        return self._build_tab_data(items, all_actuals, 'actual', project, tag, owner)

    def _filter_items(self, items, project=None, tag=None, owner=None):
        result = items
        if project:
            result = [i for i in result if i.project == project]
        if tag:
            result = [i for i in result if i.tag == tag]
        if owner:
            result = [i for i in result if i.owner == owner]
        return result

    def _build_tab_data(self, items, monthly_data, data_type, project=None, tag=None, owner=None):
        filtered = self._filter_items(items, project, tag, owner)
        rows = []
        for item in filtered:
            item_data = item.to_dict()
            months = monthly_data.get(item.id, {})
            monthly = {}
            total = 0
            for m in range(1, 13):
                if data_type == 'budget':
                    val = months.get(m, 0)
                else:
                    val = months.get(m, {}).get('amount', 0) if isinstance(months.get(m), dict) else months.get(m, 0)
                monthly[f'month_{m}'] = val
                total += val
            item_data['monthly'] = monthly
            item_data['total'] = total
            rows.append(item_data)
        return rows

    def _build_comparison_data(self, items, all_budgets, all_actuals, project=None, tag=None, owner=None):
        filtered = self._filter_items(items, project, tag, owner)
        rows = []
        for item in filtered:
            item_data = item.to_dict()
            budgets = all_budgets.get(item.id, {})
            actuals = all_actuals.get(item.id, {})
            months = {}
            total_budget = 0
            total_actual = 0
            for m in range(1, 13):
                b = budgets.get(m, 0)
                a_info = actuals.get(m, {})
                a = a_info.get('amount', 0) if isinstance(a_info, dict) else 0
                diff = a - b if b else 0
                risk = self.classify_risk(b, a)
                reason = a_info.get('reason') if isinstance(a_info, dict) else None
                months[f'month_{m}'] = {
                    'budget': b,
                    'actual': a,
                    'diff': diff,
                    'risk': risk,
                    'reason': reason,
                }
                total_budget += b
                total_actual += a
            item_data['monthly'] = months
            item_data['total_budget'] = total_budget
            item_data['total_actual'] = total_actual
            item_data['total_diff'] = total_actual - total_budget
            rows.append(item_data)
        return rows

    # ===== Edit Operations =====
    def update_budget(self, item_id, month, new_amount, changed_by=None):
        budgets = self.repo.get_budgets_for_item(item_id)
        old_amount = budgets.get(month, 0)
        self.repo.set_budget(item_id, month, new_amount)
        if old_amount != new_amount:
            self.repo.add_change_log(item_id, month, old_amount, new_amount, changed_by)
        return {'old': old_amount, 'new': new_amount}

    def update_actual(self, item_id, month, new_amount, reason=None, changed_by=None):
        actuals = self.repo.get_actuals_for_item(item_id)
        old_info = actuals.get(month, {})
        old_amount = old_info.get('amount', 0) if isinstance(old_info, dict) else 0

        budgets = self.repo.get_budgets_for_item(item_id)
        budget_val = budgets.get(month, 0)
        risk = self.classify_risk(budget_val, new_amount)

        self.repo.set_actual(item_id, month, new_amount, reason, risk)
        if old_amount != new_amount:
            self.repo.add_change_log(item_id, month, old_amount, new_amount, changed_by)
        return {'old': old_amount, 'new': new_amount, 'risk': risk}

    def update_reason(self, item_id, month, reason):
        self.repo.update_actual_reason(item_id, month, reason)

    # ===== Risk Summary =====
    def get_risk_summary(self):
        items = self.repo.get_all_items()
        all_budgets = self.repo.get_all_budgets()
        all_actuals = self.repo.get_all_actuals()

        counts = {'P0': 0, 'P1': 0, 'P2': 0, 'P3': 0}
        for item in items:
            budgets = all_budgets.get(item.id, {})
            actuals = all_actuals.get(item.id, {})
            for m in range(1, 13):
                b = budgets.get(m, 0)
                a_info = actuals.get(m, {})
                a = a_info.get('amount', 0) if isinstance(a_info, dict) else 0
                if b > 0 or a > 0:
                    risk = self.classify_risk(b, a)
                    counts[risk] = counts.get(risk, 0) + 1

        return counts

    # ===== Filter Options =====
    def get_filter_options(self):
        return self.repo.get_filter_options()

    # ===== Change Log =====
    def get_change_log(self, item_id=None):
        logs = self.repo.get_change_log(item_id)
        result = []
        for log in logs:
            item = self.repo.get_item_by_id(log.item_id)
            d = log.to_dict()
            if item:
                d['item_desc'] = f"{item.project}/{item.tag}/{item.detail}"
                d['owner'] = item.owner
            result.append(d)
        return result

    # ===== Risk Rules =====
    def get_risk_rules(self):
        return [r.to_dict() for r in self.repo.get_risk_rules()]

    def update_risk_rules(self, rules):
        self.repo.update_risk_rules(rules)
        self._reclassify_all()

    def _reclassify_all(self):
        items = self.repo.get_all_items()
        all_budgets = self.repo.get_all_budgets()
        all_actuals = self.repo.get_all_actuals()
        for item in items:
            budgets = all_budgets.get(item.id, {})
            actuals = all_actuals.get(item.id, {})
            for m in range(1, 13):
                a_info = actuals.get(m, {})
                if not isinstance(a_info, dict) or a_info.get('amount', 0) == 0:
                    continue
                b = budgets.get(m, 0)
                a = a_info['amount']
                risk = self.classify_risk(b, a)
                reason = a_info.get('reason')
                self.repo.set_actual(item.id, m, a, reason, risk)
