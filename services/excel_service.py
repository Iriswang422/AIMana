import pandas as pd
import os
from datetime import datetime

OUTPUT_COLUMNS = [
    '采购发包月',
    '项目',
    '费用子单元',
    '商品信息',
    '采购品类',
    '工序类型',
    '工序品级',
    '含税总价',
    '订单币种',
    '实付金额',
    '结算币种',
    '研运项目二类',
    '业务线',
    '结算状态',
    '供应商',
    '付款主体',
    '数据源',
    '应计提金额'
]

class ExcelService:
    def __init__(self, upload_folder, download_folder):
        self.upload_folder = upload_folder
        self.download_folder = download_folder
        os.makedirs(upload_folder, exist_ok=True)
        os.makedirs(download_folder, exist_ok=True)

    def read_excel(self, file_path):
        """读取Excel文件，返回DataFrame"""
        if file_path.endswith('.xlsx'):
            df = pd.read_excel(file_path, engine='openpyxl')
        else:
            df = pd.read_excel(file_path, engine='xlrd')
        return df

    def get_fields(self, file_path):
        """获取Excel字段列表"""
        df = self.read_excel(file_path)
        return list(df.columns)

    def preview(self, file_path, rows=10):
        """预览Excel前N行"""
        df = self.read_excel(file_path)
        fields = list(df.columns)
        preview_data = df.head(rows).fillna('').values.tolist()
        return {
            'fields': fields,
            'rows': preview_data,
            'total_rows': len(df)
        }

    def _add_purchase_month(self, df):
        """根据采购发包日添加采购发包月列"""
        if '采购发包日' in df.columns:
            df['采购发包月'] = df['采购发包日'].apply(
                lambda x: str(int(pd.to_datetime(x).month)) if pd.notna(x) else ''
            )
        return df

    def _normalize_fee_unit(self, df):
        """统一费用子单元格式，-变成—"""
        if '费用子单元' in df.columns:
            df['费用子单元'] = df['费用子单元'].apply(
                lambda x: str(x).replace('-', '—') if pd.notna(x) else x
            )
        return df

    def _add_calculated_fields(self, df):
        """添加计算字段"""
        df = self._add_purchase_month(df)
        df = self._normalize_fee_unit(df)

        df['数据源'] = '发行美宣'
        df['订单币种'] = df.get('订单币种', pd.Series([None]*len(df))).fillna('CNY')

        if '实付金额' in df.columns and '含税总价' in df.columns:
            def calc_accrual(row):
                try:
                    paid = pd.to_numeric(row.get('实付金额', 0), errors='coerce')
                    total = pd.to_numeric(row.get('含税总价', 0), errors='coerce')
                    if pd.isna(paid) or pd.isna(total) or total == 0:
                        return ''
                    ratio = paid / total if total != 0 else 0
                    if ratio >= 0.8:
                        return 0
                    else:
                        return total - paid
                except:
                    return ''

            df['应计提金额'] = df.apply(calc_accrual, axis=1)

        return df

    def apply_filter(self, file_path, conditions, logic_operator='AND'):
        """应用筛选规则"""
        df = self.read_excel(file_path)

        if not conditions:
            return df

        masks = []
        for condition in conditions:
            field = condition['field']
            operator = condition['operator']
            value = condition['value']

            if field not in df.columns:
                continue

            mask = self._create_mask(df[field], operator, value)
            masks.append(mask)

        if not masks:
            return df

        if logic_operator == 'AND':
            final_mask = masks[0]
            for mask in masks[1:]:
                final_mask = final_mask & mask
        else:
            final_mask = masks[0]
            for mask in masks[1:]:
                final_mask = final_mask | mask

        return df[final_mask]

    def _create_mask(self, series, operator, value):
        """创建单个筛选条件的mask"""
        try:
            if operator == 'in':
                return series.isin(value)

            if operator in ['>', '<', '>=', '<=']:
                value = float(value)
                series = pd.to_numeric(series, errors='coerce')

            if operator == '==':
                return series == value
            elif operator == '!=':
                return series != value
            elif operator == '>':
                return series > value
            elif operator == '<':
                return series < value
            elif operator == '>=':
                return series >= value
            elif operator == '<=':
                return series <= value
            elif operator == 'contains':
                return series.astype(str).str.contains(str(value), na=False)
            elif operator == 'not_contains':
                return ~series.astype(str).str.contains(str(value), na=False)
            elif operator == 'starts_with':
                return series.astype(str).str.startswith(str(value), na=False)
            elif operator == 'ends_with':
                return series.astype(str).str.endswith(str(value), na=False)
            elif operator == 'is_empty':
                return series.isna() | (series.astype(str).str.strip() == '')
            elif operator == 'is_not_empty':
                return ~series.isna() & (series.astype(str).str.strip() != '')
            else:
                return pd.Series([True] * len(series))
        except:
            return pd.Series([True] * len(series))

    def get_filter_options(self, file_path):
        """获取筛选字段的选项"""
        df = self.read_excel(file_path)

        df = self._add_purchase_month(df)
        df = self._normalize_fee_unit(df)

        options = {}

        if '项目' in df.columns:
            options['项目'] = sorted(df['项目'].dropna().unique().tolist())

        if '采购发包月' in df.columns:
            options['采购发包月'] = sorted(df['采购发包月'].dropna().unique().tolist())

        if '费用子单元' in df.columns:
            options['费用子单元'] = sorted(df['费用子单元'].dropna().unique().tolist())

        return options

    def prepare_output(self, df):
        """准备输出数据，只保留需要的列"""
        df = self._add_calculated_fields(df)

        available_columns = [col for col in OUTPUT_COLUMNS if col in df.columns]
        result = df[available_columns].copy()

        return result

    def save_filtered_excel(self, df, original_filename):
        """保存筛选后的DataFrame为Excel"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_filtered_{original_filename}"
        file_path = os.path.join(self.download_folder, filename)

        df.to_excel(file_path, index=False, engine='openpyxl')

        return file_path, filename

    def save_output_excel(self, df, original_filename):
        """保存输出Excel（指定列）"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_发行美宣预提_{original_filename}"
        file_path = os.path.join(self.download_folder, filename)

        df.to_excel(file_path, index=False, engine='openpyxl')

        return file_path, filename
