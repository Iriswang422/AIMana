from db import get_connection, translate_create_table
import json


class FilterRule:
    def __init__(self, db_path=None):
        pass

    def create_table(self):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(translate_create_table('''
            CREATE TABLE IF NOT EXISTS filter_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                conditions TEXT NOT NULL,
                logic_operator TEXT DEFAULT 'AND',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        '''))
        conn.commit()
        conn.close()

    def save(self, name, conditions, logic_operator='AND', description=''):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO filter_rules (name, description, conditions, logic_operator)
            VALUES (?, ?, ?, ?)
        ''', (name, description, json.dumps(conditions, ensure_ascii=False), logic_operator))
        conn.commit()
        rule_id = cursor.lastrowid
        conn.close()
        return rule_id

    def get_all(self):
        conn = get_connection()
        conn.row_factory = True
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM filter_rules ORDER BY created_at DESC')
        rows = cursor.fetchall()
        conn.close()
        rules = []
        for row in rows:
            r = dict(row) if not isinstance(row, dict) else row
            r['conditions'] = json.loads(r['conditions'])
            rules.append(r)
        return rules

    def get_by_id(self, rule_id):
        conn = get_connection()
        conn.row_factory = True
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM filter_rules WHERE id = ?', (rule_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            rule = dict(row) if not isinstance(row, dict) else row
            rule['conditions'] = json.loads(rule['conditions'])
            return rule
        return None

    def update(self, rule_id, name, conditions, logic_operator='AND', description=''):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE filter_rules
            SET name = ?, description = ?, conditions = ?, logic_operator = ?
            WHERE id = ?
        ''', (name, description, json.dumps(conditions, ensure_ascii=False), logic_operator, rule_id))
        conn.commit()
        conn.close()

    def delete(self, rule_id):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM filter_rules WHERE id = ?', (rule_id,))
        conn.commit()
        conn.close()
