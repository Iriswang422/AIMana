# -*- coding: utf-8 -*-
from datetime import datetime
from db import get_connection, translate_create_table


class BudgetItem:
    def __init__(self, id=None, project=None, tag=None, business_scene=None,
                 vendor=None, detail=None, owner=None, created_at=None, updated_at=None):
        self.id = id
        self.project = project
        self.tag = tag
        self.business_scene = business_scene
        self.vendor = vendor
        self.detail = detail
        self.owner = owner
        self.created_at = created_at
        self.updated_at = updated_at

    def to_dict(self):
        return {
            'id': self.id,
            'project': self.project,
            'tag': self.tag,
            'business_scene': self.business_scene,
            'vendor': self.vendor,
            'detail': self.detail,
            'owner': self.owner,
        }


class BudgetMonthly:
    def __init__(self, id=None, item_id=None, month=None, amount=0):
        self.id = id
        self.item_id = item_id
        self.month = month
        self.amount = amount

    def to_dict(self):
        return {
            'id': self.id,
            'item_id': self.item_id,
            'month': self.month,
            'amount': self.amount,
        }


class ActualMonthly:
    def __init__(self, id=None, item_id=None, month=None, amount=0,
                 reason=None, risk_level=None):
        self.id = id
        self.item_id = item_id
        self.month = month
        self.amount = amount
        self.reason = reason
        self.risk_level = risk_level

    def to_dict(self):
        return {
            'id': self.id,
            'item_id': self.item_id,
            'month': self.month,
            'amount': self.amount,
            'reason': self.reason,
            'risk_level': self.risk_level,
        }


class BudgetChangeLog:
    def __init__(self, id=None, item_id=None, month=None, changed_at=None,
                 old_amount=0, new_amount=0, changed_by=None):
        self.id = id
        self.item_id = item_id
        self.month = month
        self.changed_at = changed_at
        self.old_amount = old_amount
        self.new_amount = new_amount
        self.changed_by = changed_by

    def to_dict(self):
        return {
            'id': self.id,
            'item_id': self.item_id,
            'month': self.month,
            'changed_at': self.changed_at,
            'old_amount': self.old_amount,
            'new_amount': self.new_amount,
            'changed_by': self.changed_by,
        }


class RiskRule:
    def __init__(self, id=None, level=None, label=None,
                 condition_type=None, threshold=0, is_active=1):
        self.id = id
        self.level = level
        self.label = label
        self.condition_type = condition_type
        self.threshold = threshold
        self.is_active = is_active

    def to_dict(self):
        return {
            'id': self.id,
            'level': self.level,
            'label': self.label,
            'condition_type': self.condition_type,
            'threshold': self.threshold,
            'is_active': self.is_active,
        }


class VarianceNote:
    def __init__(self, id=None, item_id=None, month=None, note=None,
                 updated_by=None, updated_at=None):
        self.id = id
        self.item_id = item_id
        self.month = month
        self.note = note
        self.updated_by = updated_by
        self.updated_at = updated_at

    def to_dict(self):
        return {
            'id': self.id,
            'item_id': self.item_id,
            'month': self.month,
            'note': self.note,
            'updated_by': self.updated_by,
            'updated_at': self.updated_at,
        }


class BudgetRepository:
    def __init__(self):
        self._init_tables()
        self._init_risk_rules()

    def _get_conn(self):
        return get_connection()

    def _init_tables(self):
        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute(translate_create_table('''
            CREATE TABLE IF NOT EXISTS budget_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project TEXT,
                tag TEXT,
                business_scene TEXT,
                vendor TEXT,
                detail TEXT,
                owner TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        '''))

        cursor.execute(translate_create_table('''
            CREATE TABLE IF NOT EXISTS budget_monthly (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER NOT NULL,
                month INTEGER NOT NULL,
                amount REAL DEFAULT 0,
                UNIQUE(item_id, month),
                FOREIGN KEY (item_id) REFERENCES budget_items(id)
            )
        '''))

        cursor.execute(translate_create_table('''
            CREATE TABLE IF NOT EXISTS actual_monthly (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER NOT NULL,
                month INTEGER NOT NULL,
                amount REAL DEFAULT 0,
                reason TEXT,
                risk_level TEXT,
                UNIQUE(item_id, month),
                FOREIGN KEY (item_id) REFERENCES budget_items(id)
            )
        '''))

        cursor.execute(translate_create_table('''
            CREATE TABLE IF NOT EXISTS budget_change_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER NOT NULL,
                month INTEGER,
                changed_at TEXT,
                old_amount REAL,
                new_amount REAL,
                changed_by TEXT,
                FOREIGN KEY (item_id) REFERENCES budget_items(id)
            )
        '''))

        cursor.execute(translate_create_table('''
            CREATE TABLE IF NOT EXISTS variance_notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER NOT NULL,
                month INTEGER NOT NULL,
                note TEXT,
                updated_by TEXT,
                updated_at TEXT,
                UNIQUE(item_id, month),
                FOREIGN KEY (item_id) REFERENCES budget_items(id)
            )
        '''))

        cursor.execute(translate_create_table('''
            CREATE TABLE IF NOT EXISTS risk_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                level TEXT NOT NULL UNIQUE,
                label TEXT,
                condition_type TEXT,
                threshold REAL,
                is_active INTEGER DEFAULT 1
            )
        '''))

        conn.commit()
        conn.close()

    def _init_risk_rules(self):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM risk_rules")
        count = cursor.fetchone()[0]
        if count == 0:
            rules = [
                ('P0', '超支5%以上', 'over_budget', 0.05),
                ('P1', '未使用满10%以上', 'under_used', 0.90),
                ('P2', '当期未使用预算', 'no_usage', 0),
                ('P3', '预算内', 'within_budget', 0),
            ]
            for level, label, cond_type, threshold in rules:
                cursor.execute(
                    "INSERT INTO risk_rules (level, label, condition_type, threshold) VALUES (?, ?, ?, ?)",
                    (level, label, cond_type, threshold)
                )
            conn.commit()
        conn.close()

    # ===== Item CRUD =====
    def save_item(self, item):
        conn = self._get_conn()
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        if item.id:
            cursor.execute(
                "UPDATE budget_items SET project=?, tag=?, business_scene=?, vendor=?, detail=?, owner=?, updated_at=? WHERE id=?",
                (item.project, item.tag, item.business_scene, item.vendor, item.detail, item.owner, now, item.id)
            )
        else:
            cursor.execute(
                "INSERT INTO budget_items (project, tag, business_scene, vendor, detail, owner, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (item.project, item.tag, item.business_scene, item.vendor, item.detail, item.owner, now, now)
            )
            item.id = cursor.lastrowid
        conn.commit()
        conn.close()
        return item

    def find_item(self, project, tag, business_scene, vendor, detail, owner):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM budget_items WHERE project=? AND tag=? AND business_scene=? AND vendor=? AND detail=? AND owner=?",
            (project, tag, business_scene, vendor, detail, owner)
        )
        row = cursor.fetchone()
        conn.close()
        if row:
            return BudgetItem(id=row[0], project=row[1], tag=row[2], business_scene=row[3],
                              vendor=row[4], detail=row[5], owner=row[6],
                              created_at=row[7], updated_at=row[8])
        return None

    def get_all_items(self):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM budget_items ORDER BY project, tag, business_scene, owner, detail")
        rows = cursor.fetchall()
        conn.close()
        return [BudgetItem(id=r[0], project=r[1], tag=r[2], business_scene=r[3],
                           vendor=r[4], detail=r[5], owner=r[6],
                           created_at=r[7], updated_at=r[8]) for r in rows]

    def get_item_by_id(self, item_id):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM budget_items WHERE id = ?", (item_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return BudgetItem(id=row[0], project=row[1], tag=row[2], business_scene=row[3],
                              vendor=row[4], detail=row[5], owner=row[6],
                              created_at=row[7], updated_at=row[8])
        return None

    def delete_all_items(self):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM actual_monthly")
        cursor.execute("DELETE FROM budget_monthly")
        cursor.execute("DELETE FROM budget_change_log")
        cursor.execute("DELETE FROM budget_items")
        conn.commit()
        conn.close()

    # ===== Budget Monthly =====
    def set_budget(self, item_id, month, amount):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, amount FROM budget_monthly WHERE item_id=? AND month=?",
            (item_id, month)
        )
        row = cursor.fetchone()
        if row:
            cursor.execute("UPDATE budget_monthly SET amount=? WHERE id=?", (amount, row[0]))
        else:
            cursor.execute(
                "INSERT INTO budget_monthly (item_id, month, amount) VALUES (?, ?, ?)",
                (item_id, month, amount)
            )
        conn.commit()
        conn.close()

    def get_budgets_for_item(self, item_id):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM budget_monthly WHERE item_id=? ORDER BY month", (item_id,))
        rows = cursor.fetchall()
        conn.close()
        return {r[2]: r[3] for r in rows}

    def get_all_budgets(self):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT item_id, month, amount FROM budget_monthly ORDER BY item_id, month")
        rows = cursor.fetchall()
        conn.close()
        result = {}
        for r in rows:
            if r[0] not in result:
                result[r[0]] = {}
            result[r[0]][r[1]] = r[2]
        return result

    # ===== Actual Monthly =====
    def set_actual(self, item_id, month, amount, reason=None, risk_level=None):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id FROM actual_monthly WHERE item_id=? AND month=?",
            (item_id, month)
        )
        row = cursor.fetchone()
        if row:
            cursor.execute(
                "UPDATE actual_monthly SET amount=?, reason=?, risk_level=? WHERE id=?",
                (amount, reason, risk_level, row[0])
            )
        else:
            cursor.execute(
                "INSERT INTO actual_monthly (item_id, month, amount, reason, risk_level) VALUES (?, ?, ?, ?, ?)",
                (item_id, month, amount, reason, risk_level)
            )
        conn.commit()
        conn.close()

    def get_actuals_for_item(self, item_id):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM actual_monthly WHERE item_id=? ORDER BY month", (item_id,))
        rows = cursor.fetchall()
        conn.close()
        return {r[2]: {'amount': r[3], 'reason': r[4], 'risk_level': r[5]} for r in rows}

    def get_all_actuals(self):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT item_id, month, amount, reason, risk_level FROM actual_monthly ORDER BY item_id, month")
        rows = cursor.fetchall()
        conn.close()
        result = {}
        for r in rows:
            if r[0] not in result:
                result[r[0]] = {}
            result[r[0]][r[1]] = {'amount': r[2], 'reason': r[3], 'risk_level': r[4]}
        return result

    def update_actual_reason(self, item_id, month, reason):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE actual_monthly SET reason=? WHERE item_id=? AND month=?",
            (reason, item_id, month)
        )
        conn.commit()
        conn.close()

    # ===== Change Log =====
    def add_change_log(self, item_id, month, old_amount, new_amount, changed_by=None):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO budget_change_log (item_id, month, changed_at, old_amount, new_amount, changed_by) VALUES (?, ?, ?, ?, ?, ?)",
            (item_id, month, datetime.now().isoformat(), old_amount, new_amount, changed_by)
        )
        conn.commit()
        conn.close()

    def get_change_log(self, item_id=None):
        conn = self._get_conn()
        cursor = conn.cursor()
        if item_id:
            cursor.execute("SELECT * FROM budget_change_log WHERE item_id=? ORDER BY changed_at DESC", (item_id,))
        else:
            cursor.execute("SELECT * FROM budget_change_log ORDER BY changed_at DESC")
        rows = cursor.fetchall()
        conn.close()
        return [BudgetChangeLog(id=r[0], item_id=r[1], month=r[2], changed_at=r[3],
                                old_amount=r[4], new_amount=r[5], changed_by=r[6]) for r in rows]

    # ===== Risk Rules =====
    def get_risk_rules(self):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM risk_rules ORDER BY level")
        rows = cursor.fetchall()
        conn.close()
        return [RiskRule(id=r[0], level=r[1], label=r[2],
                         condition_type=r[3], threshold=r[4], is_active=r[5]) for r in rows]

    def update_risk_rules(self, rules):
        conn = self._get_conn()
        cursor = conn.cursor()
        for rule in rules:
            cursor.execute(
                "UPDATE risk_rules SET label=?, condition_type=?, threshold=?, is_active=? WHERE level=?",
                (rule['label'], rule['condition_type'], rule['threshold'], rule['is_active'], rule['level'])
            )
        conn.commit()
        conn.close()

    # ===== Filter Options =====
    def get_filter_options(self):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT project FROM budget_items WHERE project IS NOT NULL ORDER BY project")
        projects = [r[0] for r in cursor.fetchall()]
        cursor.execute("SELECT DISTINCT tag FROM budget_items WHERE tag IS NOT NULL ORDER BY tag")
        tags = [r[0] for r in cursor.fetchall()]
        cursor.execute("SELECT DISTINCT owner FROM budget_items WHERE owner IS NOT NULL ORDER BY owner")
        owners = [r[0] for r in cursor.fetchall()]
        conn.close()
        return {'projects': projects, 'tags': tags, 'owners': owners}

    # ===== Variance Notes =====
    def set_variance_note(self, item_id, month, note, updated_by=None):
        conn = self._get_conn()
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        cursor.execute("SELECT id FROM variance_notes WHERE item_id=? AND month=?", (item_id, month))
        row = cursor.fetchone()
        if row:
            cursor.execute("UPDATE variance_notes SET note=?, updated_by=?, updated_at=? WHERE id=?",
                           (note, updated_by, now, row[0]))
        else:
            cursor.execute("INSERT INTO variance_notes (item_id, month, note, updated_by, updated_at) VALUES (?, ?, ?, ?, ?)",
                           (item_id, month, note, updated_by, now))
        conn.commit()
        conn.close()

    def get_variance_notes(self, item_ids=None, month=None):
        conn = self._get_conn()
        cursor = conn.cursor()
        if item_ids and month:
            placeholders = ','.join(['?'] * len(item_ids))
            cursor.execute(f"SELECT * FROM variance_notes WHERE item_id IN ({placeholders}) AND month=?",
                           list(item_ids) + [month])
        elif item_ids:
            placeholders = ','.join(['?'] * len(item_ids))
            cursor.execute(f"SELECT * FROM variance_notes WHERE item_id IN ({placeholders})", list(item_ids))
        else:
            cursor.execute("SELECT * FROM variance_notes")
        rows = cursor.fetchall()
        conn.close()
        return [VarianceNote(id=r[0], item_id=r[1], month=r[2], note=r[3],
                             updated_by=r[4], updated_at=r[5]) for r in rows]

    def get_all_variance_notes(self):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT item_id, month, note, updated_by, updated_at FROM variance_notes")
        rows = cursor.fetchall()
        conn.close()
        result = {}
        for r in rows:
            if r[0] not in result:
                result[r[0]] = {}
            result[r[0]][r[1]] = {'note': r[2], 'updated_by': r[3], 'updated_at': r[4]}
        return result
