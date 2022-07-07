# Generated by Django 4.0.6 on 2022-07-07 13:33

import checkout.models
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django_countries.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Address',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(max_length=254)),
                ('shipping_name', models.CharField(max_length=120, verbose_name='Shipping full name')),
                ('shipping_street_address', models.CharField(max_length=100, verbose_name='Shipping street address')),
                ('shipping_apartment_address', models.CharField(max_length=100, verbose_name='Shipping apartment address')),
                ('shipping_city', models.CharField(max_length=100, verbose_name='Shipping city')),
                ('shipping_country', django_countries.fields.CountryField(countries=checkout.models.EUCountries, max_length=2, verbose_name='Shipping country')),
                ('shipping_zip', models.CharField(max_length=10)),
                ('billing_name', models.CharField(max_length=120, verbose_name='Billing full name')),
                ('billing_street_address', models.CharField(max_length=100, verbose_name='Billing street address')),
                ('billing_apartment_address', models.CharField(max_length=100, verbose_name='Billing apartment address')),
                ('billing_city', models.CharField(max_length=100, verbose_name='Billing city')),
                ('billing_country', django_countries.fields.CountryField(countries=checkout.models.EUCountries, max_length=2, verbose_name='Billing country')),
                ('billing_zip', models.CharField(max_length=10)),
                ('default', models.BooleanField(blank=True, default=False, verbose_name='Save for future usage')),
                ('user', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name_plural': 'Adressen',
            },
        ),
    ]
