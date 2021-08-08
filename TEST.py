from core.models import Order

order = Order.objects.filter(user__email='admin@admin.ru', ordered=False)
order_items = order[0].items.all()

listofitems = []
for i in order_items:
    # listofitems = {
    #     'name': str(i.item.title),
    #     'price': float(i.item.price),
    #     'unit_amount': {
    #         'currency_code': 'EUR',
    #         'value': float(i.item.price)
    #     }
    # }

    listofitems.append(
        {
            'name': str(i.item.title),
            'price': float(i.item.price),
            'unit_amount': {
                'currency_code': 'EUR',
                'value': round(float(i.item.price)/1.19, 2)
            },
            'quantity': i.quantity,
        }
        )

print(listofitems)
