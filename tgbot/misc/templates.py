"""
Темплейты для джинджи
"""
hotel_card: str = """
    <b>{{title|e}}</b>
    {{address|e}}
    Расстояние от центра: {{distance}} км
    Общая стоимость: <b>{{total_cost}}</b>
    Цена за ночь: {{price}}
    """

query_card: str = """
    Поиск в <b>{{city_text|e}}</b>
    Период с <b>{{date_from}}</b> по <b>{{date_to}}</b>
    Порядок сортировки: <b>{{sort_comment}}</b>
    {% if price_max %}Цены от {{cur_sym}}{{price_min}} до {{cur_sym}}{{price_max}} {% endif %} 
    """

history_card: str = """
    <b>{{ts(timestamp)}}</b>
    Поиск в <b>{{city_text|e}}</b>
    Период с <b>{{date_from}}</b> по <b>{{date_to}}</b>
    Порядок сортировки: <b>{{sort_comment}}</b>
    {% if price_max %}Цены от {{cur_sym}}{{price_min}} до {{cur_sym}}{{price_max}} {% endif %}
    Просмотрены отели:
    {% for hotel in hotels %}
    <b>{{hotel[0]|e}}</b>
    {% endfor %}
    """
