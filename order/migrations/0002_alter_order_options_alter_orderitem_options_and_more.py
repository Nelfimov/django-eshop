# Generated by Django 4.0.5 on 2022-06-30 12:35

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='order',
            options={'ordering': ('-start_date',), 'verbose_name': 'Bestellung', 'verbose_name_plural': 'Bestellungen'},
        ),
        migrations.AlterModelOptions(
            name='orderitem',
            options={'verbose_name': 'Warenkorb Artikel', 'verbose_name_plural': 'Warenkorb Artikeln'},
        ),
        migrations.AlterModelOptions(
            name='trackingcompany',
            options={'verbose_name': 'Tracking company', 'verbose_name_plural': 'Tracking companies'},
        ),
        migrations.AlterField(
            model_name='address',
            name='apartment_address',
            field=models.CharField(max_length=100, verbose_name='Wohnung'),
        ),
        migrations.AlterField(
            model_name='address',
            name='street_address',
            field=models.CharField(max_length=100, verbose_name='Strasse'),
        ),
        migrations.AlterField(
            model_name='order',
            name='refund_granted',
            field=models.BooleanField(default=False, verbose_name='Refundgewährt'),
        ),
        migrations.AlterField(
            model_name='order',
            name='refund_requested',
            field=models.BooleanField(default=False, verbose_name='Refund angefordert'),
        ),
        migrations.AlterField(
            model_name='order',
            name='tracking_company',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='order.trackingcompany', verbose_name='Tracking company'),
        ),
    ]
