import di4.settings.Constants as const
from jinja2 import Template


def spaces_removal(text: str):
    res = map(str.strip, text.strip().split('\n'))
    return ' '.join(res)


class TwoDatesInterval:
    def __init__(self, date_start, date_end):
        self.date_start = date_start
        self.date_end = date_end

    def get_date_start(self):
        return self.date_start

    def get_date_end(self):
        return self.date_end


class QueryMaker:
    def __init__(self, table_name: str, head: str = ''):
        self.table_name = table_name
        self.order_by = []
        self.order_direction = ''
        self.where_fields = {}
        self._set_head_query(head)

    def set_WHERE_fields(self, fields: dict):
        if isinstance(fields, dict):
            self.where_fields.update(fields)
        else:
            raise TypeError('fields must be a dict')

    def set_name_like_filter(self, name: str):
        self.where_fields['name'] = name

    def set_date_between_filter(self, date_start, date_end):
        self.where_fields['date'] = ''
        self.where_fields['date_between'] = TwoDatesInterval(date_start, date_end)

    def set_date_like_filter(self, date: str):
        self.where_fields['date_between'] = ''
        self.where_fields['date'] = date

    def _get_name_like_filter(self):
        name = self.where_fields.get('name')
        return f'name LIKE "%{name}%"' if name else ''

    def _get_date_like_filter(self):
        date = self.where_fields.get('date')
        return f'date LIKE "%{date}%"' if date else ''

    def _get_date_between_filter(self):
        date_interval = self.where_fields.get('date_between')
        if date_interval:
            return f'date BETWEEN date("{date_interval.get_date_start()}") ' \
                   f'AND date("{date_interval.get_date_end()}")'
        return ''

    def _get_filters(self, *filters_names):
        if not filters_names:
            return ''

        filters_to_chose = {
            'name': self._get_name_like_filter(),
            'date': self._get_date_like_filter() + self._get_date_between_filter(),
        }

        applied_filters = []
        for f_name in filters_names:
            query_filter = filters_to_chose.get(f_name)
            if query_filter:
                applied_filters.append(query_filter)
            else:
                if query_filter is None:
                    raise NameError(f'There is no such filter as "{f_name}". Use valid filter')

        return ' AND '.join(applied_filters)

    def get_sqlRelationModel_filter(self, *filters_names):
        return self._get_filters(*filters_names)

    def get_WHERE_filter(self, *filters_names):
        """ Creates 'WHERE' part of query string based on parameters having in 'filters' collection """
        where_filter_body = self._get_filters(*filters_names) if filters_names else ''
        where_filter = "WHERE " + where_filter_body if where_filter_body else ''
        return where_filter

    def set_ORDER_BY_fields(self, *fields: str, ascending=True):
        self.order_by = list(fields)
        self.order_direction = 'ASC' if ascending else 'DESC'

    def _get_ORDER_BY_fields(self):
        order_str = ', '.join(self.order_by)
        return f'ORDER BY {order_str} {self.order_direction}'

    def _set_head_query(self, query):
        self.head_query = spaces_removal(query)


class QueryMakerGroupBy(QueryMaker):
    def __init__(self, table_name: str, group_by: str, head: str = ''):
        super().__init__(table_name, head)
        self.group_by = group_by

    def get_full_query_grouped(self, *where_args, limit=0, ordered=True):
        where_filter = self.get_WHERE_filter(*where_args)
        group_filter = f'GROUP BY {self.group_by}'
        order_filter = self._get_ORDER_BY_fields() if ordered else ''
        limit_filter = f'LIMIT {limit}' if limit else ''
        return f'{self.head_query} {where_filter} {group_filter} {order_filter} {limit_filter}'


class QueryMakerTemplate(QueryMaker):
    def __init__(self, template_query):
        self.base_query = template_query
        self.where_fields = {}

    def get_full_query(self, *where):
        where_filter = self.get_WHERE_filter(*where)
        query = Template(self.base_query).render(WHERE_STATEMENT=where_filter)
        return query


def testQueryOrders():
    # ordersQueryMaker = QueryMaker('orders')
    # ordersQueryMaker.set_name_like_filter('')
    # ordersQueryMaker.set_date_like_filter('')
    # filter_query = ordersQueryMaker.get_WHERE_filter()
    #
    # print(filter_query)
    test_qr = QueryMakerTemplate(const.AVG_PROFIT_STAT_TEMPLATE)
    print(test_qr.get_full_query())




if __name__ == '__main__':
    testQueryOrders()
    # purchase_query_stat = QueryMakerGroup('purchase', 'goods.id', const.BASE_TOTAL_PURCHASES)
    # purchase_query_stat.set_WHERE_fields({'purchase.date': '2023-03', 'name': ''})
    # purchase_query_stat.set_ORDER_BY_fields('name')
    # print(purchase_query_stat.get_full_query_grouped('purchase.date'))
    # temp_query = const.AVG_PROFIT_STAT_TEMPLATE
    # q_m_templ = QueryMakerTemplate(temp_query)
    # q_m_templ.set_WHERE_fields({'name':'e60', 'date':'2023-04'})
    # print(q_m_templ.get_full_query('name', 'date'))
