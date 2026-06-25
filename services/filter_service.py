from services.excel_service import ExcelService
from models.filter_rule import FilterRule

class FilterService:
    def __init__(self, config):
        self.excel_service = ExcelService(
            config['UPLOAD_FOLDER'],
            config['DOWNLOAD_FOLDER']
        )
        self.rule_model = FilterRule(config['DATABASE'])

    def process_filter(self, file_path, rule_id, original_filename):
        """执行完整的筛选流程"""
        rule = self.rule_model.get_by_id(rule_id)
        if not rule:
            raise ValueError("规则不存在")

        conditions = rule['conditions']
        logic_operator = rule.get('logic_operator', 'AND')
        filtered_df = self.excel_service.apply_filter(file_path, conditions, logic_operator)

        output_df = self.excel_service.prepare_output(filtered_df)

        result_path, result_filename = self.excel_service.save_output_excel(
            output_df,
            original_filename
        )

        return {
            'row_count': len(output_df),
            'result_path': result_path,
            'result_filename': result_filename
        }

    def process_filter_with_conditions(self, file_path, conditions, original_filename):
        """使用条件直接筛选"""
        filtered_df = self.excel_service.apply_filter(file_path, conditions, 'AND')

        output_df = self.excel_service.prepare_output(filtered_df)

        result_path, result_filename = self.excel_service.save_output_excel(
            output_df,
            original_filename
        )

        return {
            'row_count': len(output_df),
            'result_path': result_path,
            'result_filename': result_filename
        }
