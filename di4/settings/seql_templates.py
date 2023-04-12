from jinja2 import Template
import sqlite3 as sq

sel_fields_templ='''
SELECT {{fields[0]}}{% for f in fields[1:] %},{{f}}{% endfor %}
FROM {{table}} 
'''

sel_where_templ = '''WHERE {{field}} = "{{value}}" '''


class Integer:
    pass


class SqlExecutor:
    def __init__(self, db_name):
        self.db_name = db_name

    def execute_query(self, query):
        with sq.connect(self.db_name) as connection:
            try:
                cursor = connection.cursor()
                cursor.execute(query)
                return cursor.fetchall()
            except Exception as ex:
                print(f'[ERROR] database problem: {ex}')
                return False, ex


class Goods:
    table = 'goods'
    session = SqlExecutor('bampera_test.db')
    fields = ['id', 'name', 'amount']

    def __init__(self, field=None, value=None):
        if field and value:
            self._load_attributes(field, value)

    @classmethod
    def _create_mapping_list(cls):
        query = Template(sel_fields_templ).render(fields=cls.fields, table=cls.table)
        res = cls.session.execute_query(query)
        return res

    @classmethod
    def mapp_database(cls):
        for el in cls._create_mapping_list():
            pass

    @staticmethod
    def create_object(field, value):
        return Goods(field, value)

    def _load_attributes(self, name, value):
        query_head = Template(sel_fields_templ).render(fields=self.fields, table=self.table)
        query_tail = Template(sel_where_templ).render(field=name, value=value)
        res = self.session.execute_query(query_head+query_tail)
        if isinstance(res, list) and res:
            for i,el in enumerate(res[0]):
                setattr(self, self.fields[i], el)





if __name__ == '__main__':
    g = Goods('id', 5)

    print(g.name)
