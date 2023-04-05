import di4.settings.Constants as const
from jinja2 import Template


def spaces_removal(text: str):
    res = map(str.strip, text.strip().split('\n'))
    return ' '.join(res)


class QueryMaker:
    def __init__(self, table_name: str, head: str = ''):
        self.table_name = table_name
        self.order_by = []
        self.order_direction = ''
        self.where_fields = {}
        self.set_head_query(head)

    def set_WHERE_fields(self, fields: dict):
        if isinstance(fields, dict):
            self.where_fields.update(fields)
        else:
            raise TypeError('fields must be a dict')

    def get_WHERE_filter(self, *fields) -> str:
        if fields:
            filters = [f'{key} LIKE "%{self.where_fields[key]}%"' for key in fields]
        else:
            filters = [f'{key} LIKE "%{self.where_fields[key]}%"' for key in self.where_fields.keys()]

        if len(filters) == 1:
            return ''.join(filters)
        return ' AND '.join(filters)

    def set_ORDER_BY_fields(self, *fields: str, ascending=True):
        self.order_by = list(fields)
        self.order_direction = 'ASC' if ascending else 'DESC'

    def get_ORDER_BY_fields(self):
        order_str = ', '.join(self.order_by)
        return f'ORDER BY {order_str} {self.order_direction}'

    def get_full_query(self, *where, limit=0, ordered=True):
        where_filter = f"WHERE {self.get_WHERE_filter(*where)}" if where else ''
        order_filter = self.get_ORDER_BY_fields() if ordered else ''
        limit_filter = f'LIMIT {limit}' if limit else ''
        return f'{self.head_query} {where_filter} {order_filter} {limit_filter};'

    def set_head_query(self, query):
        self.head_query = spaces_removal(query)


class QueryMakerGroup(QueryMaker):
    def __init__(self, table_name:str, group_by:str,head:str=''):
        super().__init__(table_name, head)
        self.group_by = group_by

    def get_full_query_grouped(self, *where, limit=0, ordered=True):
        where_filter = f"WHERE {self.get_WHERE_filter(*where)}" if where else ''
        group_filter = f'GROUP BY {self.group_by}'
        order_filter = self.get_ORDER_BY_fields() if ordered else ''
        limit_filter = f'LIMIT {limit}' if limit else ''
        return f'{self.head_query} {where_filter} {group_filter} {order_filter} {limit_filter};'


class QueryMakerTemplate:
    def __init__(self, template_query):
        self.base_query = template_query
        self.where_fields = {}

    def set_WHERE_fields(self, fields: dict):
        if isinstance(fields, dict):
            self.where_fields.update(fields)
        else:
            raise TypeError('fields must be a dict')

    def get_WHERE_fields(self, *fields) -> str:
        if fields:
            filters = [f'{key} LIKE "%{self.where_fields[key]}%"' for key in fields]
        else:
            filters = [f'{key} LIKE "%{self.where_fields[key]}%"' for key in self.where_fields.keys()]

        if len(filters) == 1:
            return ''.join(filters)
        return ' AND '.join(filters)

    def get_full_query(self, *where):
        where_filter = f"WHERE {self.get_WHERE_fields(*where)}" if where else ''
        query = Template(self.base_query).render(WHERE_STATEMENT=where_filter)
        return query







if __name__ == '__main__':
    # purchase_query_stat = QueryMakerGroup('purchase', 'goods.id', const.BASE_TOTAL_PURCHASES)
    # purchase_query_stat.set_WHERE_fields({'purchase.date': '2023-03', 'name': ''})
    # purchase_query_stat.set_ORDER_BY_fields('name')
    # print(purchase_query_stat.get_full_query_grouped('purchase.date'))
    temp_query = '''
                SELECT purchase_avg.name, 
                price_buy_avg,
                price_sell_avg,
                (price_sell_avg - price_buy_avg) as avg_profit,
                (price_sell_avg - price_buy_avg)*orders_avg.amount as total_profit
                FROM (SELECT name,
                      ROUND(AVG(buy_price), 2) as price_buy_avg
                      FROM purchase 
                      JOIN goods ON purchase.goods_id = goods.id
                      {{ WHERE_STATEMENT }}
                      GROUP BY purchase.goods_id) purchase_avg
                JOIN goods ON goods.name = purchase_avg.name
                JOIN (SELECT name,
                      ROUND(AVG(sell_price), 2) as price_sell_avg,
                      COUNT(name) as amount
                      FROM orders
                      JOIN goods ON orders.goods_id = goods.id
                      {{ WHERE_STATEMENT }}
                      GROUP BY orders.goods_id) orders_avg ON orders_avg.name = goods.name
             '''
    q_m_templ = QueryMakerTemplate(temp_query)
    q_m_templ.set_WHERE_fields({'name':'e60', 'date':'2023-04'})
    print(q_m_templ.get_full_query('name', 'date'))


