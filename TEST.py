from core.models import Order

order = Order.objects.filter(user__email='admin@admin.ru', ordered=False)
order_items = order[0].items.all()

listofitems = []
for i in order_items:
    currency = 'EUR'
    listofitems.append(
                {
                    'name': str(i.item.title),
                    'description': str(i.item.description),
                    'unit_amount': {
                        'currency_code': currency,
                        'value': round(float(i.get_final_price_wo_delivery())/1.19, 2)
                    },
                    'tax': {
                        'currency_code': currency,
                        'value': round((-1)*(float(i.get_final_price_wo_delivery())/1.19-float(i.get_final_price_wo_delivery())), 2),
                    },
                    'quantity': i.quantity,
                    'category': 'PHYSICAL_GOODS'
                }
        )

print(listofitems)
