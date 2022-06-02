import datetime

from cart.models import Cart, CartItem
from core.models import Address, Item, Order
from django.conf import settings
from django.core import mail
from django.template.loader import render_to_string
from django.test import TestCase
from django.utils.html import strip_tags


class EmailSend(TestCase):

    def setUp(self):
        self.item = Item.objects.create(
            title='Test', price=100,
            delivery_price=10, discount=5,
            stock=10, title_image='',
        )
        cart_item = CartItem.objects.create(
            item=self.item, quantity=2
        )
        self.session = self.client.session
        self.session['key'] = 'value'
        self.session.save()
        self.cart = Cart.objects.create(
            user=None, creation_date=datetime.datetime.now(),
            session_key=self.session.session_key,
        )
        self.cart.items.add(cart_item)
        self.cart.save()
        shipping_address = Address.objects.create(
            user=None, email='nelfimov@mail.ru',
            name_for_delivery='Nikita Elfimov',
            street_address='test',
            apartment_address='test',
            country='DE', zip='012345',
            address_type='S', default=True,
        )
        billing_address = shipping_address
        billing_address.address_type = 'B'
        self.order = Order.objects.create(
            cart=self.cart, user=None,
            billing_address=billing_address,
            shipping_address=shipping_address,
        )
        self.order.items.add(cart_item)

    def tearDown(self):
        self.item.delete()
        self.cart.delete()
        self.order.delete()

    def testOrder(self):
        self.assertFalse(self.order.ordered)

    def testSession(self):
        self.assertEqual(self.session.session_key, self.cart.session_key)

    def testMailSend(self):
        order = Order.objects.get(id=1)
        subject = 'Your order'
        from_mail = settings.DEFAULT_FROM_EMAIL
        html_message = render_to_string(
            'emails/order_confirmation_email.html',
            {'objects': order}
        )
        plain_message = strip_tags(html_message)
        to = order.shipping_address.email
        mail.send_mail(
            subject, plain_message, from_mail, [to],
            html_message=html_message,
            fail_silently=False
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, subject)
