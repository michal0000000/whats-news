# Generated by Django 4.1.4 on 2023-01-28 11:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('newsapp', '0022_alter_article_published'),
    ]

    operations = [
        migrations.AddField(
            model_name='tag',
            name='display_title',
            field=models.CharField(default='N/A', max_length=50),
        ),
        migrations.AlterField(
            model_name='tag',
            name='title',
            field=models.CharField(default='N/A', max_length=50),
        ),
    ]
