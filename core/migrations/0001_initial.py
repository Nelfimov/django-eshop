# Generated by Django 4.0.4 on 2022-06-03 14:20

import autoslug.fields
import core.models
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Carousel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('img', models.ImageField(upload_to='carousel/images/')),
                ('title', models.CharField(max_length=120, verbose_name='Name')),
                ('body', models.TextField(verbose_name='Hauptteil')),
                ('alt', models.TextField(verbose_name='Alt text')),
                ('index', models.IntegerField(unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='CategoryItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=20)),
                ('slug', autoslug.fields.AutoSlugField(editable=False, populate_from='name', unique_with=('id',))),
            ],
        ),
        migrations.CreateModel(
            name='Item',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100, verbose_name='Name')),
                ('price', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Preis')),
                ('delivery_price', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Lieferpreis')),
                ('discount', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Rabatt')),
                ('label', models.CharField(blank=True, choices=[('n', 'NEW'), ('h', 'HOT')], max_length=1, null=True)),
                ('stock', models.PositiveIntegerField(default='1', verbose_name='Lager')),
                ('slug', autoslug.fields.AutoSlugField(editable=False, populate_from='title', unique_with=('id',))),
                ('title_image', models.ImageField(upload_to=core.models.item_image_path, verbose_name='Titelbild')),
                ('description', models.TextField(verbose_name='Beschreibung')),
                ('additional_information', models.TextField(blank=True, null=True, verbose_name='Zusätzliche Information')),
                ('additional_information_image1', models.ImageField(blank=True, null=True, upload_to=core.models.item_image_path)),
                ('additional_information_image2', models.ImageField(blank=True, null=True, upload_to=core.models.item_image_path)),
                ('additional_information_image3', models.ImageField(blank=True, null=True, upload_to=core.models.item_image_path)),
                ('created_date', models.DateTimeField(auto_now_add=True, verbose_name='Erstellungsdatum')),
                ('ordered_counter', models.PositiveIntegerField(default='0', verbose_name='Bestellt Zähler')),
                ('category', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='core.categoryitem', verbose_name='Kategorie')),
            ],
            options={
                'verbose_name': 'Artikel',
                'verbose_name_plural': 'Artikeln',
            },
        ),
    ]