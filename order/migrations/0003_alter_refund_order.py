# Generated by Django 4.0.4 on 2022-06-17 14:42

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0002_alter_refund_order'),
    ]

    operations = [
        migrations.AlterField(
            model_name='refund',
            name='order',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='order.order', verbose_name='Bestellung'),
        ),
    ]