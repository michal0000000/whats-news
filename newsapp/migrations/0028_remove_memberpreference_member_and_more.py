# Generated by Django 4.1.4 on 2023-01-31 20:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('newsapp', '0027_memberpreference'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='memberpreference',
            name='member',
        ),
        migrations.AlterField(
            model_name='memberpreference',
            name='sources',
            field=models.ManyToManyField(to='newsapp.source'),
        ),
        migrations.AddField(
            model_name='memberpreference',
            name='member',
            field=models.ManyToManyField(to='newsapp.membershiptoken'),
        ),
    ]
