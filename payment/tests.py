import datetime

from order.models import Order, OrderItem
from core.models import Item
from checkout.models import Address
from django.conf import settings
from django.core import mail
from django.template.loader import render_to_string
from django.test import TestCase
from django.utils.html import strip_tags


class EmailSend(TestCase):
    def setUp(self):
        self.item = Item.objects.create(
            title="Test",
            price=100,
            delivery_price=10,
            discount=5,
            stock=10,
            title_image="",
        )
        self.session = self.client.session
        self.session["key"] = "value"
        self.session.save()
        self.order = Order.objects.create(
            user=None,
            start_date=datetime.datetime.now(),
            session_key=self.session.session_key,
        )
        order_item = OrderItem.objects.create(
            order=self.order, item=self.item, quantity=2
        )
        self.address = Address.objects.create(
            user=None,
            email="nelfimov@mail.ru",
            shipping_name="Nikita Elfimov",
            shipping_street_address="test",
            shipping_apartment_address="123",
            shipping_city="Voronezh",
            shipping_zip="12345",
            shipping_country="DE",
            billing_street_address="test",
            billing_apartment_address="123",
            billing_city="Voronezh",
            billing_zip="12345",
            billing_country="DE",
        )
        self.order.address = self.address
        self.order.save()

    def tearDown(self):
        self.item.delete()
        self.order.delete()
        self.address.delete()

    def testOrder(self):
        self.assertFalse(self.order.ordered)

    def testSession(self):
        self.assertEqual(self.session.session_key, self.order.session_key)

    def testMailSend(self):
        order = Order.objects.get(id=1)
        subject = "Your order"
        from_mail = settings.DEFAULT_FROM_EMAIL
        html_message = render_to_string(
            "emails/order_confirmation_email.html", {"objects": order}
        )
        plain_message = strip_tags(html_message)
        to = order.address.email
        mail.send_mail(
            subject,
            plain_message,
            from_mail,
            [to],
            html_message=html_message,
            fail_silently=False,
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, subject)
