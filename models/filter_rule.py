import sqlite3
import json

class FilterRule:
    def __init__(self, db_path):
        self.db_path = db_path

    def create_table(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS filter_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                conditions TEXT NOT NULL,
                logic_operator TEXT DEFAULT 'AND',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()

    def save(self, name, conditions, logic_operator='AND', description=''):
        conn = sqlite3.connect(self.db_path)
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
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM filter_rules ORDER BY created_at DESC')
        rules = [dict(row) for row in cursor.fetchall()]
        conn.close()
        for rule in rules:
            rule['conditions'] = json.loads(rule['conditions'])
        return rules

    def get_by_id(self, rule_id):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM filter_rules WHERE id = ?', (rule_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            rule = dict(row)
            rule['conditions'] = json.loads(rule['conditions'])
            return rule
        return None

    def update(self, rule_id, name, conditions, logic_operator='AND', description=''):
        conn = sqlite3.connect(self.db_path)
        conn.execute('''
            UPDATE filter_rules
            SET name = ?, description = ?, conditions = ?, logic_operator = ?
            WHERE id = ?
        ''', (name, description, json.dumps(conditions, ensure_ascii=False), logic_operator, rule_id))
        conn.commit()
        conn.close()

    def delete(self, rule_id):
        conn = sqlite3.connect(self.db_path)
        conn.execute('DELETE FROM filter_rules WHERE id = ?', (rule_id,))
        conn.commit()
        conn.close()
