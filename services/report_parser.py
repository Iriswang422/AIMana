# -*- coding: utf-8 -*-
import pandas as pd
import json


class ReportParser:
    """解析月报Excel文件"""

    REQUIRED_SHEETS = ['概览', '项目分析', '收入实收', '服务器费用',
                       '人力成本', '机动资金', '要点']

    def __init__(self, file_path):
        self.file_path = file_path
        self.errors = []
        self.warnings = []

    def validate_sheets(self, xl_file):
        """验证必需的sheet是否存在"""
        sheet_names = xl_file.sheet_names
        missing = [s for s in self.REQUIRED_SHEETS if s not in sheet_names]

        if missing:
            self.errors.append(f'缺少必需的sheet: {", ".join(missing)}')
            return False
        return True

    def parse_overview(self, df):
        """解析概览sheet"""
        required_cols = ['metric_name', 'actual', 'budget']
        missing_cols = [c for c in required_cols if c not in df.columns]

        if missing_cols:
            self.errors.append(f'概览sheet缺少列: {", ".join(missing_cols)}')
            return None

        kpis = []
        for _, row in df.iterrows():
            kpi = {
                'metric_name': str(row.get('metric_name', '')).strip(),
                'actual': self._to_float(row.get('actual')),
                'budget': self._to_float(row.get('budget')),
                'prior_year': self._to_float(row.get('prior_year')),
                'unit': str(row.get('unit', '')).strip()
            }
            if kpi['metric_name']:
                kpis.append(kpi)

        return kpis

    def parse_project_analysis(self, df):
        """解析项目分析sheet"""
        required_cols = ['project', 'revenue_actual', 'revenue_budget']
        missing_cols = [c for c in required_cols if c not in df.columns]

        if missing_cols:
            self.errors.append(f'项目分析sheet缺少列: {", ".join(missing_cols)}')
            return None

        projects = []
        for _, row in df.iterrows():
            project = {
                'project': str(row.get('project', '')).strip(),
                'revenue_actual': self._to_float(row.get('revenue_actual')),
                'revenue_budget': self._to_float(row.get('revenue_budget')),
                'cost_actual': self._to_float(row.get('cost_actual')),
                'cost_budget': self._to_float(row.get('cost_budget')),
                'headcount': self._to_int(row.get('headcount'))
            }
            if project['project']:
                # 计算差异
                if project['revenue_actual'] and project['revenue_budget']:
                    project['revenue_variance'] = (
                        project['revenue_actual'] - project['revenue_budget']
                    )
                    project['revenue_achievement'] = (
                        project['revenue_actual'] / project['revenue_budget']
                        if project['revenue_budget'] != 0 else 0
                    )
                projects.append(project)

        return projects

    def parse_revenue_collection(self, df):
        """解析收入实收sheet"""
        required_cols = ['project', 'month', 'revenue_confirmed']
        missing_cols = [c for c in required_cols if c not in df.columns]

        if missing_cols:
            self.errors.append(f'收入实收sheet缺少列: {", ".join(missing_cols)}')
            return None

        data = []
        for _, row in df.iterrows():
            item = {
                'project': str(row.get('project', '')).strip(),
                'month': str(row.get('month', '')).strip(),
                'revenue_confirmed': self._to_float(row.get('revenue_confirmed')),
                'cash_collected': self._to_float(row.get('cash_collected')),
                'collection_rate': self._to_float(row.get('collection_rate'))
            }
            if item['project'] and item['month']:
                data.append(item)

        return data

    def parse_server_cost(self, df):
        """解析服务器费用sheet"""
        required_cols = ['project', 'month', 'server_cost']
        missing_cols = [c for c in required_cols if c not in df.columns]

        if missing_cols:
            self.errors.append(f'服务器费用sheet缺少列: {", ".join(missing_cols)}')
            return None

        data = []
        for _, row in df.iterrows():
            item = {
                'project': str(row.get('project', '')).strip(),
                'month': str(row.get('month', '')).strip(),
                'server_cost': self._to_float(row.get('server_cost')),
                'budget': self._to_float(row.get('budget')),
                'unit_cost': self._to_float(row.get('unit_cost'))
            }
            if item['project'] and item['month']:
                data.append(item)

        return data

    def parse_labor_cost(self, df):
        """解析人力成本sheet"""
        required_cols = ['project', 'month', 'hc_actual']
        missing_cols = [c for c in required_cols if c not in df.columns]

        if missing_cols:
            self.errors.append(f'人力成本sheet缺少列: {", ".join(missing_cols)}')
            return None

        data = []
        for _, row in df.iterrows():
            item = {
                'project': str(row.get('project', '')).strip(),
                'month': str(row.get('month', '')).strip(),
                'hc_actual': self._to_int(row.get('hc_actual')),
                'hc_budget': self._to_int(row.get('hc_budget')),
                'avg_cost_per_head': self._to_float(row.get('avg_cost_per_head'))
            }
            if item['project'] and item['month']:
                data.append(item)

        return data

    def parse_contingency_fund(self, df):
        """解析机动资金sheet"""
        required_cols = ['item', 'allocated', 'used']
        missing_cols = [c for c in required_cols if c not in df.columns]

        if missing_cols:
            self.errors.append(f'机动资金sheet缺少列: {", ".join(missing_cols)}')
            return None

        data = []
        for _, row in df.iterrows():
            item = {
                'item': str(row.get('item', '')).strip(),
                'allocated': self._to_float(row.get('allocated')),
                'used': self._to_float(row.get('used')),
                'remaining': self._to_float(row.get('remaining'))
            }
            if item['item']:
                # 计算剩余（如果没有提供）
                if item['remaining'] is None and item['allocated'] and item['used']:
                    item['remaining'] = item['allocated'] - item['used']
                data.append(item)

        return data

    def parse_highlights(self, df):
        """解析要点sheet"""
        required_cols = ['section', 'priority', 'text']
        missing_cols = [c for c in required_cols if c not in df.columns]

        if missing_cols:
            self.errors.append(f'要点sheet缺少列: {", ".join(missing_cols)}')
            return None

        data = []
        for _, row in df.iterrows():
            item = {
                'section': str(row.get('section', '')).strip(),
                'priority': str(row.get('priority', '')).strip().lower(),
                'text': str(row.get('text', '')).strip()
            }
            if item['section'] and item['text']:
                # 验证priority值
                if item['priority'] not in ['high', 'medium', 'low']:
                    self.warnings.append(
                        f"要点'{item['text'][:20]}...'的priority值'{item['priority']}'无效，"
                        f"应为high/medium/low"
                    )
                    item['priority'] = 'medium'
                data.append(item)

        return data

    def parse(self):
        """解析整个Excel文件"""
        try:
            xl_file = pd.ExcelFile(self.file_path, engine='openpyxl')
        except Exception as e:
            self.errors.append(f'无法读取Excel文件: {str(e)}')
            return None

        if not self.validate_sheets(xl_file):
            return None

        result = {}

        # 解析每个sheet
        try:
            df = xl_file.parse('概览')
            result['overview'] = self.parse_overview(df)
        except Exception as e:
            self.errors.append(f'解析概览sheet失败: {str(e)}')

        try:
            df = xl_file.parse('项目分析')
            result['projects'] = self.parse_project_analysis(df)
        except Exception as e:
            self.errors.append(f'解析项目分析sheet失败: {str(e)}')

        try:
            df = xl_file.parse('收入实收')
            result['revenue'] = self.parse_revenue_collection(df)
        except Exception as e:
            self.errors.append(f'解析收入实收sheet失败: {str(e)}')

        try:
            df = xl_file.parse('服务器费用')
            result['server_cost'] = self.parse_server_cost(df)
        except Exception as e:
            self.errors.append(f'解析服务器费用sheet失败: {str(e)}')

        try:
            df = xl_file.parse('人力成本')
            result['labor_cost'] = self.parse_labor_cost(df)
        except Exception as e:
            self.errors.append(f'解析人力成本sheet失败: {str(e)}')

        try:
            df = xl_file.parse('机动资金')
            result['contingency'] = self.parse_contingency_fund(df)
        except Exception as e:
            self.errors.append(f'解析机动资金sheet失败: {str(e)}')

        try:
            df = xl_file.parse('要点')
            result['highlights'] = self.parse_highlights(df)
        except Exception as e:
            self.errors.append(f'解析要点sheet失败: {str(e)}')

        if self.errors:
            return None

        return result

    def _to_float(self, value):
        """转换为浮点数"""
        if pd.isna(value):
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    def _to_int(self, value):
        """转换为整数"""
        if pd.isna(value):
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None

    def get_errors(self):
        """获取错误列表"""
        return self.errors

    def get_warnings(self):
        """获取警告列表"""
        return self.warnings
