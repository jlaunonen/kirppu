# Generated by Django 2.0.7 on 2018-07-03 13:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('kirppuauth', '0003_auto_20170629_1208'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='last_name',
            field=models.CharField(blank=True, max_length=150, verbose_name='last name'),
        ),
    ]
