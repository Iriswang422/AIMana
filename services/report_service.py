# -*- coding: utf-8 -*-
import json
from models.report import ReportRepository, Report, ReportData, ReportKPI


class ReportService:
    """报告业务逻辑服务"""

    def __init__(self):
        self.repo = ReportRepository()

    def create_report(self, period, title, raw_filename, parsed_data):
        """创建新报告"""
        # 检查是否已存在
        existing = self.repo.get_report_by_period(period)
        if existing:
            self.repo.delete_report(existing.id)

        # 创建报告记录
        report = Report(
            period=period,
            title=title,
            raw_filename=raw_filename,
            status='draft'
        )
        report = self.repo.save_report(report)

        # 保存各部分数据
        self._save_report_sections(report.id, parsed_data)

        # 保存KPI索引
        self._save_kpi_index(report.id, parsed_data)

        return report

    def _save_report_sections(self, report_id, data):
        """保存报告各部分数据"""
        sections = [
            ('概览', None, data.get('overview')),
            ('项目分析', None, data.get('projects')),
            ('收入实收', None, data.get('revenue')),
            ('服务器费用', None, data.get('server_cost')),
            ('人力成本', None, data.get('labor_cost')),
            ('机动资金', None, data.get('contingency')),
            ('要点', None, data.get('highlights'))
        ]

        for section, subsection, content in sections:
            if content:
                report_data = ReportData(
                    report_id=report_id,
                    section=section,
                    subsection=subsection,
                    data_json=json.dumps(content, ensure_ascii=False)
                )
                self.repo.save_report_data(report_data)

    def _save_kpi_index(self, report_id, data):
        """保存KPI索引"""
        # 从概览中提取KPI
        overview = data.get('overview', [])
        for kpi_data in overview:
            kpi = ReportKPI(
                report_id=report_id,
                metric_name=kpi_data.get('metric_name'),
                section='概览',
                actual=kpi_data.get('actual'),
                budget=kpi_data.get('budget'),
                prior_year=kpi_data.get('prior_year'),
                unit=kpi_data.get('unit')
            )
            self.repo.save_report_kpi(kpi)

    def get_report_summary(self, period):
        """获取报告摘要"""
        report = self.repo.get_report_by_period(period)
        if not report:
            return None

        # 获取KPI
        kpis = self.repo.get_report_kpis(report.id, section='概览')

        # 获取要点
        highlights_data = self.repo.get_report_data(report.id, section='要点')
        highlights = []
        if highlights_data:
            highlights = json.loads(highlights_data[0].data_json)

        return {
            'report': report.to_dict(),
            'kpis': [k.to_dict() for k in kpis],
            'highlights': highlights
        }

    def get_budget_comparison(self, period):
        """获取预算vs实际对比数据"""
        report = self.repo.get_report_by_period(period)
        if not report:
            return None

        # 获取项目分析数据
        projects_data = self.repo.get_report_data(report.id, section='项目分析')
        projects = []
        if projects_data:
            projects = json.loads(projects_data[0].data_json)

        # 获取概览KPI
        kpis = self.repo.get_report_kpis(report.id, section='概览')
        overview = {k.metric_name: k.to_dict() for k in kpis}

        return {
            'overview': overview,
            'projects': projects
        }

    def get_project_analysis(self, period, project_name=None):
        """获取项目分析"""
        report = self.repo.get_report_by_period(period)
        if not report:
            return None

        projects_data = self.repo.get_report_data(report.id, section='项目分析')
        if not projects_data:
            return {'projects': []}

        projects = json.loads(projects_data[0].data_json)

        if project_name:
            projects = [p for p in projects if p.get('project') == project_name]

        return {'projects': projects}

    def get_revenue_analysis(self, period, project_name=None):
        """获取收入分析"""
        report = self.repo.get_report_by_period(period)
        if not report:
            return None

        revenue_data = self.repo.get_report_data(report.id, section='收入实收')
        if not revenue_data:
            return {'revenue': []}

        revenue = json.loads(revenue_data[0].data_json)

        if project_name:
            revenue = [r for r in revenue if r.get('project') == project_name]

        return {'revenue': revenue}

    def get_cost_analysis(self, period, project_name=None):
        """获取成本分析"""
        report = self.repo.get_report_by_period(period)
        if not report:
            return None

        # 服务器费用
        server_data = self.repo.get_report_data(report.id, section='服务器费用')
        server_cost = []
        if server_data:
            server_cost = json.loads(server_data[0].data_json)
            if project_name:
                server_cost = [s for s in server_cost if s.get('project') == project_name]

        # 人力成本
        labor_data = self.repo.get_report_data(report.id, section='人力成本')
        labor_cost = []
        if labor_data:
            labor_cost = json.loads(labor_data[0].data_json)
            if project_name:
                labor_cost = [l for l in labor_cost if l.get('project') == project_name]

        return {
            'server_cost': server_cost,
            'labor_cost': labor_cost
        }

    def get_contingency_fund(self, period):
        """获取机动资金使用情况"""
        report = self.repo.get_report_by_period(period)
        if not report:
            return None

        contingency_data = self.repo.get_report_data(report.id, section='机动资金')
        if not contingency_data:
            return {'contingency': []}

        contingency = json.loads(contingency_data[0].data_json)
        return {'contingency': contingency}

    def compare_periods(self, period1, period2):
        """对比两个期间"""
        report1 = self.repo.get_report_by_period(period1)
        report2 = self.repo.get_report_by_period(period2)

        if not report1 or not report2:
            return None

        kpis1 = {k.metric_name: k.to_dict() for k in
                 self.repo.get_report_kpis(report1.id, section='概览')}
        kpis2 = {k.metric_name: k.to_dict() for k in
                 self.repo.get_report_kpis(report2.id, section='概览')}

        comparison = {}
        for metric in set(kpis1.keys()) | set(kpis2.keys()):
            k1 = kpis1.get(metric, {})
            k2 = kpis2.get(metric, {})

            comparison[metric] = {
                'period1': k1,
                'period2': k2,
                'change': self._calculate_change(k1.get('actual'), k2.get('actual'))
            }

        return {
            'period1': period1,
            'period2': period2,
            'comparison': comparison
        }

    def _calculate_change(self, val1, val2):
        """计算变化"""
        if val1 is None or val2 is None:
            return None
        if val2 == 0:
            return None
        return {
            'absolute': val1 - val2,
            'percentage': (val1 - val2) / val2 * 100
        }

    def publish_report(self, period):
        """发布报告"""
        report = self.repo.get_report_by_period(period)
        if not report:
            return None

        self.repo.update_report_status(report.id, 'published')
        report.status = 'published'
        return report

    def unpublish_report(self, period):
        """取消发布报告"""
        report = self.repo.get_report_by_period(period)
        if not report:
            return None

        self.repo.update_report_status(report.id, 'draft')
        report.status = 'draft'
        return report

    def list_reports(self, status=None):
        """列出所有报告"""
        reports = self.repo.get_all_reports()
        if status:
            reports = [r for r in reports if r.status == status]
        return [r.to_dict() for r in reports]
