# -*- coding: utf-8 -*-
"""
Database abstraction layer - SQLite (local) / PostgreSQL (Render)
Reads DATABASE_URL env var. If absent, falls back to SQLite.
"""
import os
import re
import sqlite3

_pg_conn = None

SERIAL_COLUMNS = {
    'budget_owners': 'id',
    'budget_categories': 'id',
    'budget_items': 'id',
    'budget_actuals': 'id',
    'budget_change_log': 'id',
    'risk_rules': 'id',
    'permissions': 'id',
    'reports': 'id',
    'report_data': 'id',
    'report_kpis': 'id',
    'filter_rules': 'id',
}


def get_db_type():
    return 'postgresql' if os.environ.get('DATABASE_URL') else 'sqlite'


def get_connection():
    if get_db_type() == 'postgresql':
        return _get_pg_connection()
    return _get_sqlite_connection()


def _get_sqlite_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn


def _get_pg_connection():
    global _pg_conn
    if _pg_conn is not None:
        try:
            _pg_conn.cursor().execute("SELECT 1")
            return PgConnection(_pg_conn)
        except Exception:
            _pg_conn = None

    url = os.environ['DATABASE_URL']
    if url.startswith('postgres://'):
        url = url.replace('postgres://', 'postgresql://', 1)

    import psycopg
    conn = psycopg.connect(conninfo=url)
    conn.autocommit = False
    _pg_conn = conn
    return PgConnection(conn)


def _parse_pg_url(url):
    from urllib.parse import urlparse
    parsed = urlparse(url)
    return {
        'host': parsed.hostname or 'localhost',
        'port': parsed.port or 5432,
        'user': parsed.username,
        'password': parsed.password,
        'dbname': parsed.path.lstrip('/'),
    }


def translate_create_table(sql):
    if get_db_type() != 'postgresql':
        return sql
    sql = re.sub(
        r'\bINTEGER\s+PRIMARY\s+KEY\s+AUTOINCREMENT\b',
        'BIGSERIAL PRIMARY KEY', sql, flags=re.IGNORECASE)
    sql = re.sub(
        r'\bINTEGER\s+PRIMARY\s+KEY\b',
        'BIGSERIAL PRIMARY KEY', sql, flags=re.IGNORECASE)
    return sql


class Row:
    __slots__ = ('_data', '_columns')

    def __init__(self, data, columns):
        self._data = data
        self._columns = columns

    def __getitem__(self, key):
        if isinstance(key, int):
            return self._data[key]
        return self._data[self._columns.index(key)]

    def __iter__(self):
        return iter(self._data)

    def keys(self):
        return list(self._columns)


class PgCursorWrapper:
    def __init__(self, conn):
        self._conn = conn
        self._cursor = conn.cursor()
        self._lastrowid = None
        self._description = None
        self._rows = None

    def execute(self, sql, params=None):
        params = params or ()
        params = tuple(params)

        if get_db_type() == 'postgresql':
            sql, params = self._convert_none_to_default(sql, params)

            if sql.strip().upper().startswith('INSERT OR REPLACE'):
                return self._execute_upsert(sql, params)

        translated = sql.replace('?', '%s') if get_db_type() == 'postgresql' else sql

        if translated.strip().upper().startswith('INSERT') and 'RETURNING' not in translated.upper():
            translated = translated.rstrip().rstrip(';') + ' RETURNING id'

        self._cursor.execute(translated, params)

        self._description = self._cursor.description
        if self._cursor.description and self._cursor.rowcount >= 0:
            try:
                self._rows = self._cursor.fetchall()
            except Exception:
                self._rows = None
        else:
            self._rows = None

        if translated.strip().upper().startswith('INSERT') and 'RETURNING' in translated.upper():
            try:
                row = self._cursor.fetchone()
                if row:
                    self._lastrowid = row[0]
            except Exception:
                pass

        return self

    def _execute_upsert(self, sql, params):
        """Execute INSERT OR REPLACE as DELETE + INSERT for PostgreSQL"""
        params = tuple(params)
        sql_work = sql.replace('?', '%s')

        table_match = re.search(r'INTO\s+(\w+)', sql_work, re.IGNORECASE)
        if not table_match:
            translated = sql_work.replace('INSERT OR REPLACE', 'INSERT', flags=re.IGNORECASE)
            self._cursor.execute(translated, params)
            return self

        table = table_match.group(1)

        cols_match = re.search(r'\(([^)]+)\)\s*VALUES', sql_work, re.IGNORECASE)
        if not cols_match:
            translated = sql_work.replace('INSERT OR REPLACE', 'INSERT', flags=re.IGNORECASE)
            self._cursor.execute(translated, params)
            return self

        cols_str = cols_match.group(1)
        cols = [c.strip().strip('"') for c in cols_str.split(',')]

        pk_cols = self._get_pk_columns(table)
        unique_constraints = self._get_unique_constraints(table)

        if pk_cols and all(col in cols for col in pk_cols):
            pk_ph = []
            for col in pk_cols:
                idx = cols.index(col)
                if idx < len(params) and params[idx] is not None:
                    pk_ph.append('%s')
                else:
                    pk_ph.append('NULL')
            if 'NULL' not in pk_ph:
                where = ' AND '.join(f'{c} = {p}' for c, p in zip(pk_cols, pk_ph))
                delete_sql = f'DELETE FROM {table} WHERE {where}'
                delete_params = tuple(params[cols.index(col)] for col in pk_cols)
                self._cursor.execute(delete_sql, delete_params)

        secondary = [
            c for name, c in unique_constraints
            if name != 'pk' and all(col in cols for col in c)
        ]
        for constraint in secondary:
            phs = []
            constraint_params = []
            all_none = True
            for col in constraint:
                idx = cols.index(col)
                if idx < len(params):
                    if params[idx] is not None:
                        phs.append('%s')
                        constraint_params.append(params[idx])
                        all_none = False
                    else:
                        phs.append('NULL')
            if not all_none:
                where = ' AND '.join(f'{c} = {p}' for c, p in zip(constraint, phs))
                delete_sql = f'DELETE FROM {table} WHERE {where}'
                self._cursor.execute(delete_sql, tuple(constraint_params))

        insert_sql = re.sub(r'INSERT\s+OR\s+REPLACE', 'INSERT', sql_work, flags=re.IGNORECASE)
        if 'RETURNING' not in insert_sql.upper():
            insert_sql = insert_sql.rstrip().rstrip(';') + ' RETURNING id'

        self._cursor.execute(insert_sql, params)

        self._description = self._cursor.description
        if self._cursor.description and self._cursor.rowcount >= 0:
            try:
                self._rows = self._cursor.fetchall()
            except Exception:
                self._rows = None
        else:
            self._rows = None

        if 'RETURNING' in insert_sql.upper():
            try:
                row = self._cursor.fetchone()
                if row:
                    self._lastrowid = row[0]
            except Exception:
                pass

        return self

    def _translate(self, sql, params):
        if get_db_type() != 'postgresql':
            return sql
        upper = sql.strip().upper()
        if upper.startswith('INSERT OR REPLACE'):
            return self._translate_upsert(sql, params)
        return sql.replace('?', '%s')

    def _translate_upsert(self, sql, params):
        params = tuple(params)
        sql = sql.replace('?', '%s')

        table_match = re.search(r'INTO\s+(\w+)', sql, re.IGNORECASE)
        if not table_match:
            return sql
        table = table_match.group(1)

        cols_match = re.search(r'\(([^)]+)\)\s*VALUES', sql, re.IGNORECASE)
        if not cols_match:
            return sql
        cols_str = cols_match.group(1)
        cols = [c.strip().strip('"') for c in cols_str.split(',')]

        unique_constraints = self._get_unique_constraints(table)
        pk_cols = self._get_pk_columns(table)

        parts = ['BEGIN']

        if pk_cols and all(col in cols for col in pk_cols):
            pk_ph = []
            for col in pk_cols:
                idx = cols.index(col)
                if idx < len(params) and params[idx] is not None:
                    pk_ph.append('%s')
                else:
                    pk_ph.append('NULL')
            if 'NULL' not in pk_ph:
                where = ' AND '.join(f'{c} = {p}' for c, p in zip(pk_cols, pk_ph))
                parts.append(f'DELETE FROM {table} WHERE {where}')

        secondary = [
            c for name, c in unique_constraints
            if name != 'pk' and all(col in cols for col in c)
        ]
        for constraint in secondary:
            phs = []
            all_none = True
            for col in constraint:
                idx = cols.index(col)
                if idx < len(params):
                    if params[idx] is not None:
                        phs.append('%s')
                        all_none = False
                    else:
                        phs.append('NULL')
            if not all_none:
                where = ' AND '.join(f'{c} = {p}' for c, p in zip(constraint, phs))
                parts.append(f'DELETE FROM {table} WHERE {where}')

        insert_sql = re.sub(r'INSERT\s+OR\s+REPLACE', 'INSERT', sql, flags=re.IGNORECASE)
        parts.append(insert_sql)
        parts.append('COMMIT')

        return '; '.join(parts)

    def _get_unique_constraints(self, table):
        if get_db_type() != 'postgresql':
            return []
        try:
            cursor = self._conn.cursor()
            cursor.execute("""
                SELECT conname, array_agg(attname ORDER BY array_position(conkey, attnum))
                FROM pg_constraint
                JOIN pg_attribute ON attnum = ANY(conkey) AND attrelid = conrelid
                WHERE conrelid = %s::regclass AND contype = 'u'
                GROUP BY conname
            """, (table,))
            return [(row[0], row[1]) for row in cursor.fetchall()]
        except Exception:
            return []

    def _get_pk_columns(self, table):
        if get_db_type() != 'postgresql':
            return ['id']
        try:
            cursor = self._conn.cursor()
            cursor.execute("""
                SELECT attname
                FROM pg_constraint
                JOIN pg_attribute ON attnum = ANY(conkey) AND attrelid = conrelid
                WHERE conrelid = %s::regclass AND contype = 'p'
                ORDER BY array_position(conkey, attnum)
            """, (table,))
            return [row[0] for row in cursor.fetchall()]
        except Exception:
            return ['id']

    def _convert_none_to_default(self, sql, params):
        if get_db_type() != 'postgresql':
            return sql, params

        upper = sql.strip().upper()
        if not upper.startswith('INSERT'):
            return sql, params

        cols_match = re.search(
            r'INSERT\s+(?:OR\s+REPLACE\s+)?INTO\s+\w+\s*\(([^)]+)\)',
            sql, re.IGNORECASE)
        if not cols_match:
            return sql, params

        table_match = re.search(r'INTO\s+(\w+)', sql, re.IGNORECASE)
        if not table_match:
            return sql, params
        table = table_match.group(1).lower()

        cols_str = cols_match.group(1)
        cols = [c.strip().strip('"').lower() for c in cols_str.split(',')]

        id_col = SERIAL_COLUMNS.get(table, 'id')

        none_indices = []
        for i, col in enumerate(cols):
            if col == id_col and i < len(params) and params[i] is None:
                none_indices.append(i)

        if not none_indices:
            return sql, params

        remaining_cols = [c for i, c in enumerate(cols) if i not in none_indices]
        if not remaining_cols:
            return sql, params

        vals_match = re.search(
            r'VALUES\s*\((.+)\)\s*;?\s*$', sql,
            re.IGNORECASE | re.DOTALL)
        if not vals_match:
            return sql, params

        vals_str = vals_match.group(1)
        vals = [v.strip() for v in vals_str.split(',')]

        new_vals = [v for i, v in enumerate(vals) if i not in none_indices]
        new_params = tuple(p for i, p in enumerate(params) if i not in none_indices)

        cols_clause = ', '.join(remaining_cols)
        vals_clause = ', '.join(new_vals)

        new_sql = re.sub(
            r'(INSERT\s+(?:OR\s+REPLACE\s+)?INTO\s+\w+\s*)\([^)]+\)(\s*VALUES\s*)\(.+\)\s*;?\s*$',
            r'\1(' + cols_clause + r')\2(' + vals_clause + r')',
            sql, count=1, flags=re.IGNORECASE | re.DOTALL)

        return new_sql, new_params

    def fetchone(self):
        if self._rows and len(self._rows) > 0:
            row = self._rows.pop(0)
            if hasattr(row, 'keys'):
                return row
            cols = [desc[0] for desc in self._description]
            return Row(row, cols)
        return None

    def fetchall(self):
        if self._rows is not None:
            rows = self._rows
            self._rows = []
            result = []
            cols = [desc[0] for desc in self._description] if self._description else []
            for row in rows:
                if hasattr(row, 'keys'):
                    result.append(row)
                else:
                    result.append(Row(row, cols))
            return result
        return self._cursor.fetchall()

    def fetchmany(self, size=None):
        if self._rows is not None:
            size = size or 1
            rows = self._rows[:size]
            self._rows = self._rows[size:]
            return rows
        return self._cursor.fetchmany(size)

    @property
    def lastrowid(self):
        return self._lastrowid

    @property
    def description(self):
        return self._description or self._cursor.description

    @property
    def rowcount(self):
        return self._cursor.rowcount

    def close(self):
        self._cursor.close()

    def __iter__(self):
        return iter(self.fetchall())


class PgConnection:
    def __init__(self, raw_conn):
        self._conn = raw_conn

    def cursor(self):
        return PgCursorWrapper(self._conn)

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    @property
    def row_factory(self):
        return None

    @row_factory.setter
    def row_factory(self, value):
        pass

    def sync_sequences(self, table_names=None):
        if get_db_type() != 'postgresql':
            return
        cursor = self._conn.cursor()
        tables = table_names or list(SERIAL_COLUMNS.keys())
        for table in tables:
            col = SERIAL_COLUMNS.get(table)
            if not col:
                continue
            try:
                cursor.execute(f"""
                    SELECT setval(pg_get_serial_sequence(%s, %s),
                                  COALESCE((SELECT MAX({col}) FROM {table}), 1))
                """, (table, col))
            except Exception:
                pass
        self._conn.commit()


def init_db():
    from models.budget import BudgetRepository
    from models.report import ReportRepository
    from models.filter_rule import FilterRule

    BudgetRepository()
    ReportRepository()
    FilterRule().create_table()

    if get_db_type() == 'postgresql':
        conn = get_connection()
        if isinstance(conn, PgConnection):
            conn.sync_sequences()
