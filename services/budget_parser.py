# -*- coding: utf-8 -*-
import pandas as pd


class BudgetExcelParser:
    """解析3页签预算Excel：预算数 / 预实对比 / 实际数"""

    BASE_COLS = ['项目', 'Tag', '业务场景', '供应商', '明细', '负责人']

    def __init__(self, file_path):
        self.file_path = file_path
        self.errors = []
        self.warnings = []

    def parse_all(self):
        """解析全部3个页签，返回统一结构"""
        try:
            xl = pd.ExcelFile(self.file_path, engine='openpyxl')
        except Exception as e:
            self.errors.append(f'无法读取Excel: {str(e)}')
            return None

        sheet_names = xl.sheet_names
        result = {
            'items': [],
            'budget_monthly': [],
            'actual_monthly': [],
        }

        item_map = {}

        for sheet in sheet_names:
            df = pd.read_excel(self.file_path, sheet_name=sheet, header=0, engine='openpyxl')
            df.columns = [str(c).strip() for c in df.columns]

            if sheet == '预算数':
                self._parse_budget_sheet(df, item_map, result)
            elif sheet == '预实对比':
                self._parse_comparison_sheet(df, item_map, result)
            elif sheet == '实际数':
                self._parse_actuals_sheet(df, item_map, result)

        result['items'] = list(item_map.values())
        return result

    def _get_base_key(self, row):
        def _val(field):
            v = row.get(field, '')
            if pd.isna(v):
                return ''
            return str(v).strip()
        project = _val('项目')
        tag = _val('Tag')
        business_scene = _val('业务场景')
        vendor = _val('供应商')
        detail = _val('明细')
        owner = _val('负责人')
        return (project, tag, business_scene, vendor, detail, owner)

    def _is_summary_row(self, row):
        project = row.get('项目', '')
        if pd.isna(project):
            return True
        project = str(project).strip()
        if not project or project == 'nan':
            return True
        if '合计' in project or '小计' in project:
            return True
        detail = row.get('明细', '')
        if pd.isna(detail):
            return True
        detail = str(detail).strip()
        if not detail or detail == 'nan':
            return True
        return False

    def _ensure_item(self, row, item_map):
        if self._is_summary_row(row):
            return None
        key = self._get_base_key(row)
        if key not in item_map:
            item_map[key] = {
                'project': key[0],
                'tag': key[1],
                'business_scene': key[2],
                'vendor': key[3],
                'detail': key[4],
                'owner': key[5],
            }
        return key

    def _to_float(self, value):
        if pd.isna(value):
            return 0.0
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0.0

    def _parse_budget_sheet(self, df, item_map, result):
        for _, row in df.iterrows():
            key = self._ensure_item(row, item_map)
            if key is None:
                continue
            for m in range(1, 13):
                col_name = f'{m}月预算'
                if col_name in df.columns:
                    amount = self._to_float(row.get(col_name))
                    if amount != 0:
                        result['budget_monthly'].append({
                            'key': key,
                            'month': m,
                            'amount': amount,
                        })

    def _parse_comparison_sheet(self, df, item_map, result):
        for _, row in df.iterrows():
            self._ensure_item(row, item_map)

    def _parse_actuals_sheet(self, df, item_map, result):
        for _, row in df.iterrows():
            key = self._ensure_item(row, item_map)
            if key is None:
                continue
            for m in range(1, 13):
                col_name = f'{m}月实际'
                if col_name in df.columns:
                    amount = self._to_float(row.get(col_name))
                    if amount != 0:
                        result['actual_monthly'].append({
                            'key': key,
                            'month': m,
                            'amount': amount,
                        })

    def get_preview(self):
        """预览导入数据"""
        data = self.parse_all()
        if data is None:
            return None

        items = data['items']
        budget_count = len(data['budget_monthly'])
        actual_count = len(data['actual_monthly'])

        unique_projects = set(i['project'] for i in items if i['project'])
        unique_tags = set(i['tag'] for i in items if i['tag'])
        unique_owners = set(i['owner'] for i in items if i['owner'])

        return {
            'items_count': len(items),
            'budget_records': budget_count,
            'actual_records': actual_count,
            'projects': sorted(unique_projects),
            'tags': sorted(unique_tags),
            'owners': sorted(unique_owners),
            'preview_items': items[:10],
        }

    def get_errors(self):
        return self.errors

    def get_warnings(self):
        return self.warnings
