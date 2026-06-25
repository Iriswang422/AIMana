# -*- coding: utf-8 -*-
import sqlite3
import json
from datetime import datetime
from config import Config


class Report:
    def __init__(self, id=None, period=None, title=None, raw_filename=None,
                 created_at=None, status='draft'):
        self.id = id
        self.period = period
        self.title = title
        self.raw_filename = raw_filename
        self.created_at = created_at or datetime.now().isoformat()
        self.status = status

    def to_dict(self):
        return {
            'id': self.id,
            'period': self.period,
            'title': self.title,
            'raw_filename': self.raw_filename,
            'created_at': self.created_at,
            'status': self.status
        }


class ReportData:
    def __init__(self, id=None, report_id=None, section=None,
                 subsection=None, data_json=None):
        self.id = id
        self.report_id = report_id
        self.section = section
        self.subsection = subsection
        self.data_json = data_json

    def to_dict(self):
        return {
            'id': self.id,
            'report_id': self.report_id,
            'section': self.section,
            'subsection': self.subsection,
            'data': json.loads(self.data_json) if self.data_json else None
        }


class ReportKPI:
    def __init__(self, id=None, report_id=None, metric_name=None,
                 section=None, actual=None, budget=None,
                 prior_year=None, unit=None):
        self.id = id
        self.report_id = report_id
        self.metric_name = metric_name
        self.section = section
        self.actual = actual
        self.budget = budget
        self.prior_year = prior_year
        self.unit = unit

    def to_dict(self):
        return {
            'id': self.id,
            'report_id': self.report_id,
            'metric_name': self.metric_name,
            'section': self.section,
            'actual': self.actual,
            'budget': self.budget,
            'prior_year': self.prior_year,
            'unit': self.unit
        }


class ReportRepository:
    def __init__(self):
        self.db_path = Config.DATABASE_PATH
        self._init_tables()

    def _get_conn(self):
        return sqlite3.connect(self.db_path)

    def _init_tables(self):
        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                period TEXT NOT NULL UNIQUE,
                title TEXT,
                raw_filename TEXT,
                created_at TEXT,
                status TEXT DEFAULT 'draft'
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS report_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_id INTEGER NOT NULL,
                section TEXT NOT NULL,
                subsection TEXT,
                data_json TEXT,
                UNIQUE(report_id, section, subsection),
                FOREIGN KEY (report_id) REFERENCES reports(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS report_kpis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_id INTEGER NOT NULL,
                metric_name TEXT NOT NULL,
                section TEXT,
                actual REAL,
                budget REAL,
                prior_year REAL,
                unit TEXT,
                FOREIGN KEY (report_id) REFERENCES reports(id)
            )
        ''')

        conn.commit()
        conn.close()

    def save_report(self, report):
        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT OR REPLACE INTO reports
            (id, period, title, raw_filename, created_at, status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (report.id, report.period, report.title,
              report.raw_filename, report.created_at, report.status))

        report.id = cursor.lastrowid
        conn.commit()
        conn.close()
        return report

    def get_report_by_period(self, period):
        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM reports WHERE period = ?', (period,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return Report(
                id=row[0], period=row[1], title=row[2],
                raw_filename=row[3], created_at=row[4], status=row[5]
            )
        return None

    def get_all_reports(self):
        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM reports ORDER BY period DESC')
        rows = cursor.fetchall()
        conn.close()

        return [
            Report(id=row[0], period=row[1], title=row[2],
                   raw_filename=row[3], created_at=row[4], status=row[5])
            for row in rows
        ]

    def update_report_status(self, report_id, status):
        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute(
            'UPDATE reports SET status = ? WHERE id = ?',
            (status, report_id)
        )

        conn.commit()
        conn.close()

    def save_report_data(self, report_data):
        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT OR REPLACE INTO report_data
            (id, report_id, section, subsection, data_json)
            VALUES (?, ?, ?, ?, ?)
        ''', (report_data.id, report_data.report_id, report_data.section,
              report_data.subsection, report_data.data_json))

        report_data.id = cursor.lastrowid
        conn.commit()
        conn.close()
        return report_data

    def get_report_data(self, report_id, section=None):
        conn = self._get_conn()
        cursor = conn.cursor()

        if section:
            cursor.execute(
                'SELECT * FROM report_data WHERE report_id = ? AND section = ?',
                (report_id, section)
            )
        else:
            cursor.execute(
                'SELECT * FROM report_data WHERE report_id = ?',
                (report_id,)
            )

        rows = cursor.fetchall()
        conn.close()

        return [
            ReportData(
                id=row[0], report_id=row[1], section=row[2],
                subsection=row[3], data_json=row[4]
            )
            for row in rows
        ]

    def save_report_kpi(self, kpi):
        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO report_kpis
            (report_id, metric_name, section, actual, budget, prior_year, unit)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (kpi.report_id, kpi.metric_name, kpi.section,
              kpi.actual, kpi.budget, kpi.prior_year, kpi.unit))

        kpi.id = cursor.lastrowid
        conn.commit()
        conn.close()
        return kpi

    def get_report_kpis(self, report_id, section=None):
        conn = self._get_conn()
        cursor = conn.cursor()

        if section:
            cursor.execute(
                'SELECT * FROM report_kpis WHERE report_id = ? AND section = ?',
                (report_id, section)
            )
        else:
            cursor.execute(
                'SELECT * FROM report_kpis WHERE report_id = ?',
                (report_id,)
            )

        rows = cursor.fetchall()
        conn.close()

        return [
            ReportKPI(
                id=row[0], report_id=row[1], metric_name=row[2],
                section=row[3], actual=row[4], budget=row[5],
                prior_year=row[6], unit=row[7]
            )
            for row in rows
        ]

    def delete_report(self, report_id):
        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute('DELETE FROM report_kpis WHERE report_id = ?', (report_id,))
        cursor.execute('DELETE FROM report_data WHERE report_id = ?', (report_id,))
        cursor.execute('DELETE FROM reports WHERE id = ?', (report_id,))

        conn.commit()
        conn.close()
