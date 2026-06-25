# -*- coding: utf-8 -*-
import pandas as pd


class BudgetParser:
    """解析实际数Excel文件"""

    # 期望的列名映射（支持中英文变体）
    COLUMN_MAPPING = {
        '负责人': ['负责人', 'owner', 'owner_name', 'manager'],
        '预算板块': ['预算板块', 'category', 'budget_category', '板块'],
        '预算明细': ['预算明细', 'item', 'item_name', '明细', '费用项'],
        '月份': ['月份', 'month', '月份/期间'],
        '实际数': ['实际数', 'actual', 'actual_amount', '实际金额', '实际发生'],
        '理由': ['理由', 'reason', '变动理由', '说明', '备注']
    }

    def __init__(self, file_path):
        self.file_path = file_path
        self.errors = []
        self.warnings = []

    def parse(self, df=None):
        """解析Excel文件"""
        if df is None:
            try:
                df = pd.read_excel(self.file_path, engine='openpyxl')
            except Exception as e:
                self.errors.append(f'无法读取Excel: {str(e)}')
                return None

        # 规范化列名
        df = self._normalize_columns(df)

        # 验证必需列
        required = ['负责人', '预算板块', '预算明细', '月份', '实际数']
        missing = [c for c in required if c not in df.columns]
        if missing:
            self.errors.append(f'缺少必需列: {", ".join(missing)}')
            return None

        # 解析数据
        results = []
        for _, row in df.iterrows():
            item_data = {
                'owner': str(row.get('负责人', '')).strip(),
                'category': str(row.get('预算板块', '')).strip(),
                'item_name': str(row.get('预算明细', '')).strip(),
                'month': self._normalize_month(row.get('月份')),
                'actual_amount': self._to_float(row.get('实际数')),
                'reason': str(row.get('理由', '')).strip() if pd.notna(row.get('理由')) else None
            }

            if item_data['owner'] and item_data['item_name'] and item_data['month']:
                results.append(item_data)
            else:
                self.warnings.append(f'跳过无效行: {row.to_dict()}')

        if self.errors:
            return None

        return results

    def _normalize_columns(self, df):
        """规范化列名"""
        normalized = {}
        for col in df.columns:
            col_str = str(col).strip()
            for standard_name, variants in self.COLUMN_MAPPING.items():
                if col_str in variants or col_str.lower() in [v.lower() for v in variants]:
                    normalized[col_str] = standard_name
                    break
            else:
                normalized[col_str] = col_str

        return df.rename(columns=normalized)

    def _normalize_month(self, value):
        """规范化月份格式"""
        if pd.isna(value):
            return None

        value = str(value).strip()

        # 处理各种格式
        if '-' in value:
            parts = value.split('-')
            if len(parts) == 2:
                year, month = parts
                return f'{year}-{month.zfill(2)}'
            elif len(parts) == 3:
                return f'{parts[0]}-{parts[1].zfill(2)}'

        # 纯数字（如 1, 01, 202601）
        if value.isdigit():
            if len(value) <= 2:
                return f'2026-{value.zfill(2)}'
            elif len(value) == 6:
                return f'{value[:4]}-{value[4:].zfill(2)}'

        return value

    def _to_float(self, value):
        if pd.isna(value):
            return 0
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0

    def get_errors(self):
        return self.errors

    def get_warnings(self):
        return self.warnings

    def get_unique_values(self, df=None):
        """获取Excel中的唯一值（用于匹配）"""
        if df is None:
            try:
                df = pd.read_excel(self.file_path, engine='openpyxl')
            except:
                return None

        df = self._normalize_columns(df)

        return {
            'owners': sorted([str(x) for x in df.get('负责人', []).dropna().unique()]),
            'categories': sorted([str(x) for x in df.get('预算板块', []).dropna().unique()]),
            'items': sorted([str(x) for x in df.get('预算明细', []).dropna().unique()]),
            'months': sorted([self._normalize_month(x) for x in df.get('月份', []).dropna().unique() if self._normalize_month(x)])
        }
