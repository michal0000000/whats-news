# Generated by Django 4.1.4 on 2023-01-28 12:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('newsapp', '0024_remove_tag_display_title_category_display_title_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='active',
            field=models.BooleanField(default=False),
        ),
    ]
