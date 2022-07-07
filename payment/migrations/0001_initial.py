# Generated by Django 4.0.6 on 2022-07-07 13:33

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('order', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('paypal_id', models.CharField(blank=True, max_length=100, null=True)),
                ('amount', models.FloatField(verbose_name='Summe')),
                ('timestamp', models.DateTimeField(auto_now_add=True, verbose_name='Zeitstempel')),
                ('order', models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, to='order.order')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Zahlung',
                'verbose_name_plural': 'Zahlungen',
            },
        ),
    ]
