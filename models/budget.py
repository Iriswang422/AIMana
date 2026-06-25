# -*- coding: utf-8 -*-
from datetime import datetime
from db import get_connection, translate_create_table


class BudgetOwner:
    def __init__(self, id=None, name=None, feishu_group=None, sort_order=0):
        self.id = id
        self.name = name
        self.feishu_group = feishu_group
        self.sort_order = sort_order

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'feishu_group': self.feishu_group,
            'sort_order': self.sort_order
        }


class BudgetCategory:
    def __init__(self, id=None, owner_id=None, name=None, sort_order=0):
        self.id = id
        self.owner_id = owner_id
        self.name = name
        self.sort_order = sort_order

    def to_dict(self):
        return {
            'id': self.id,
            'owner_id': self.owner_id,
            'name': self.name,
            'sort_order': self.sort_order
        }


class BudgetItem:
    def __init__(self, id=None, category_id=None, item_name=None,
                 original_budget=0, current_budget=0, sort_order=0):
        self.id = id
        self.category_id = category_id
        self.item_name = item_name
        self.original_budget = original_budget
        self.current_budget = current_budget
        self.sort_order = sort_order

    def to_dict(self):
        return {
            'id': self.id,
            'category_id': self.category_id,
            'item_name': self.item_name,
            'original_budget': self.original_budget,
            'current_budget': self.current_budget,
            'sort_order': self.sort_order
        }


class BudgetActual:
    def __init__(self, id=None, item_id=None, month=None,
                 actual_amount=0, reason=None, risk_level=None):
        self.id = id
        self.item_id = item_id
        self.month = month
        self.actual_amount = actual_amount
        self.reason = reason
        self.risk_level = risk_level

    def to_dict(self):
        return {
            'id': self.id,
            'item_id': self.item_id,
            'month': self.month,
            'actual_amount': self.actual_amount,
            'reason': self.reason,
            'risk_level': self.risk_level
        }


class BudgetChangeLog:
    def __init__(self, id=None, item_id=None, changed_at=None,
                 old_budget=0, new_budget=0, diff=0, changed_by=None):
        self.id = id
        self.item_id = item_id
        self.changed_at = changed_at
        self.old_budget = old_budget
        self.new_budget = new_budget
        self.diff = diff
        self.changed_by = changed_by

    def to_dict(self):
        return {
            'id': self.id,
            'item_id': self.item_id,
            'changed_at': self.changed_at,
            'old_budget': self.old_budget,
            'new_budget': self.new_budget,
            'diff': self.diff,
            'changed_by': self.changed_by
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
            'is_active': self.is_active
        }


class Permission:
    def __init__(self, id=None, user_id=None, feishu_group=None,
                 owner_id=None, role='viewer'):
        self.id = id
        self.user_id = user_id
        self.feishu_group = feishu_group
        self.owner_id = owner_id
        self.role = role

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'feishu_group': self.feishu_group,
            'owner_id': self.owner_id,
            'role': self.role
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

        # 负责人表
        cursor.execute(translate_create_table('''
            CREATE TABLE IF NOT EXISTS budget_owners (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                feishu_group TEXT,
                sort_order INTEGER DEFAULT 0
            )
        '''))

        # 预算板块表
        cursor.execute(translate_create_table('''
            CREATE TABLE IF NOT EXISTS budget_categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                sort_order INTEGER DEFAULT 0,
                UNIQUE(owner_id, name),
                FOREIGN KEY (owner_id) REFERENCES budget_owners(id)
            )
        '''))

        # 预算明细表
        cursor.execute(translate_create_table('''
            CREATE TABLE IF NOT EXISTS budget_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id INTEGER NOT NULL,
                item_name TEXT NOT NULL,
                original_budget REAL DEFAULT 0,
                current_budget REAL DEFAULT 0,
                sort_order INTEGER DEFAULT 0,
                UNIQUE(category_id, item_name),
                FOREIGN KEY (category_id) REFERENCES budget_categories(id)
            )
        '''))

        # 实际数表
        cursor.execute(translate_create_table('''
            CREATE TABLE IF NOT EXISTS budget_actuals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER NOT NULL,
                month TEXT NOT NULL,
                actual_amount REAL DEFAULT 0,
                reason TEXT,
                risk_level TEXT,
                UNIQUE(item_id, month),
                FOREIGN KEY (item_id) REFERENCES budget_items(id)
            )
        '''))

        # 变更记录表
        cursor.execute(translate_create_table('''
            CREATE TABLE IF NOT EXISTS budget_change_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER NOT NULL,
                changed_at TEXT,
                old_budget REAL,
                new_budget REAL,
                diff REAL,
                changed_by TEXT,
                FOREIGN KEY (item_id) REFERENCES budget_items(id)
            )
        '''))

        # 风险规则表
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

        # 权限表
        cursor.execute(translate_create_table('''
            CREATE TABLE IF NOT EXISTS permissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                feishu_group TEXT,
                owner_id INTEGER,
                role TEXT DEFAULT 'viewer',
                UNIQUE(user_id, owner_id)
            )
        '''))

        conn.commit()
        conn.close()

    def _init_risk_rules(self):
        """初始化默认风险规则"""
        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM risk_rules")
        count = cursor.fetchone()[0]

        if count == 0:
            rules = [
                ('P0', '超支5%以上', 'over_budget', 0.05),
                ('P1', '未使用满10%以上', 'under_used', 0.90),
                ('P2', '当期未使用预算', 'no_usage', 0),
                ('P3', '预算内', 'within_budget', 0)
            ]
            for level, label, cond_type, threshold in rules:
                cursor.execute(
                    "INSERT INTO risk_rules (level, label, condition_type, threshold) VALUES (?, ?, ?, ?)",
                    (level, label, cond_type, threshold)
                )
            conn.commit()

        conn.close()

    # ===== Owner CRUD =====
    def save_owner(self, owner):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO budget_owners (id, name, feishu_group, sort_order) VALUES (?, ?, ?, ?)",
            (owner.id, owner.name, owner.feishu_group, owner.sort_order)
        )
        owner.id = cursor.lastrowid
        conn.commit()
        conn.close()
        return owner

    def get_all_owners(self):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM budget_owners ORDER BY sort_order, name")
        rows = cursor.fetchall()
        conn.close()
        return [BudgetOwner(id=r[0], name=r[1], feishu_group=r[2], sort_order=r[3]) for r in rows]

    def delete_owner(self, owner_id):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM budget_owners WHERE id = ?", (owner_id,))
        conn.commit()
        conn.close()

    # ===== Category CRUD =====
    def save_category(self, category):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO budget_categories (id, owner_id, name, sort_order) VALUES (?, ?, ?, ?)",
            (category.id, category.owner_id, category.name, category.sort_order)
        )
        category.id = cursor.lastrowid
        conn.commit()
        conn.close()
        return category

    def get_categories_by_owner(self, owner_id):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM budget_categories WHERE owner_id = ? ORDER BY sort_order, name", (owner_id,))
        rows = cursor.fetchall()
        conn.close()
        return [BudgetCategory(id=r[0], owner_id=r[1], name=r[2], sort_order=r[3]) for r in rows]

    def delete_category(self, category_id):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM budget_categories WHERE id = ?", (category_id,))
        conn.commit()
        conn.close()

    # ===== Item CRUD =====
    def save_item(self, item):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO budget_items (id, category_id, item_name, original_budget, current_budget, sort_order) VALUES (?, ?, ?, ?, ?, ?)",
            (item.id, item.category_id, item.item_name, item.original_budget, item.current_budget, item.sort_order)
        )
        item.id = cursor.lastrowid
        conn.commit()
        conn.close()
        return item

    def get_items_by_category(self, category_id):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM budget_items WHERE category_id = ? ORDER BY sort_order, item_name", (category_id,))
        rows = cursor.fetchall()
        conn.close()
        return [BudgetItem(id=r[0], category_id=r[1], item_name=r[2],
                           original_budget=r[3], current_budget=r[4], sort_order=r[5]) for r in rows]

    def get_item_by_id(self, item_id):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM budget_items WHERE id = ?", (item_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return BudgetItem(id=row[0], category_id=row[1], item_name=row[2],
                              original_budget=row[3], current_budget=row[4], sort_order=row[5])
        return None

    def update_item_budget(self, item_id, new_budget, changed_by=None):
        """更新预算并记录变更"""
        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute("SELECT current_budget FROM budget_items WHERE id = ?", (item_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return None

        old_budget = row[0]
        diff = new_budget - old_budget

        cursor.execute("UPDATE budget_items SET current_budget = ? WHERE id = ?", (new_budget, item_id))

        cursor.execute(
            "INSERT INTO budget_change_log (item_id, changed_at, old_budget, new_budget, diff, changed_by) VALUES (?, ?, ?, ?, ?, ?)",
            (item_id, datetime.now().isoformat(), old_budget, new_budget, diff, changed_by)
        )

        conn.commit()
        conn.close()
        return {'old_budget': old_budget, 'new_budget': new_budget, 'diff': diff}

    def delete_item(self, item_id):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM budget_items WHERE id = ?", (item_id,))
        conn.commit()
        conn.close()

    # ===== Actuals CRUD =====
    def save_actual(self, actual):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO budget_actuals (id, item_id, month, actual_amount, reason, risk_level) VALUES (?, ?, ?, ?, ?, ?)",
            (actual.id, actual.item_id, actual.month, actual.actual_amount, actual.reason, actual.risk_level)
        )
        actual.id = cursor.lastrowid
        conn.commit()
        conn.close()
        return actual

    def get_actuals_by_item(self, item_id):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM budget_actuals WHERE item_id = ? ORDER BY month", (item_id,))
        rows = cursor.fetchall()
        conn.close()
        return [BudgetActual(id=r[0], item_id=r[1], month=r[2],
                             actual_amount=r[3], reason=r[4], risk_level=r[5]) for r in rows]

    def update_actual_reason(self, item_id, month, reason):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE budget_actuals SET reason = ? WHERE item_id = ? AND month = ?",
            (reason, item_id, month)
        )
        conn.commit()
        conn.close()

    # ===== Change Log =====
    def get_change_log(self, item_id=None):
        conn = self._get_conn()
        cursor = conn.cursor()
        if item_id:
            cursor.execute("SELECT * FROM budget_change_log WHERE item_id = ? ORDER BY changed_at DESC", (item_id,))
        else:
            cursor.execute("SELECT * FROM budget_change_log ORDER BY changed_at DESC")
        rows = cursor.fetchall()
        conn.close()
        return [BudgetChangeLog(id=r[0], item_id=r[1], changed_at=r[2],
                                old_budget=r[3], new_budget=r[4], diff=r[5], changed_by=r[6]) for r in rows]

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
                "UPDATE risk_rules SET label = ?, condition_type = ?, threshold = ?, is_active = ? WHERE level = ?",
                (rule['label'], rule['condition_type'], rule['threshold'], rule['is_active'], rule['level'])
            )
        conn.commit()
        conn.close()

    # ===== Permissions =====
    def save_permission(self, permission):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO permissions (id, user_id, feishu_group, owner_id, role) VALUES (?, ?, ?, ?, ?)",
            (permission.id, permission.user_id, permission.feishu_group, permission.owner_id, permission.role)
        )
        permission.id = cursor.lastrowid
        conn.commit()
        conn.close()
        return permission

    def get_permissions(self):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM permissions ORDER BY user_id")
        rows = cursor.fetchall()
        conn.close()
        return [Permission(id=r[0], user_id=r[1], feishu_group=r[2],
                           owner_id=r[3], role=r[4]) for r in rows]

    # ===== Tree Query =====
    def get_full_tree(self):
        """获取完整三层树结构"""
        owners = self.get_all_owners()
        tree = []

        for owner in owners:
            categories = self.get_categories_by_owner(owner.id)
            owner_dict = owner.to_dict()
            owner_dict['categories'] = []

            for cat in categories:
                items = self.get_items_by_category(cat.id)
                cat_dict = cat.to_dict()
                cat_dict['items'] = [item.to_dict() for item in items]
                owner_dict['categories'].append(cat_dict)

            tree.append(owner_dict)

        return tree
