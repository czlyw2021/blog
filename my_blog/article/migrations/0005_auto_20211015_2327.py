# Generated by Django 2.2 on 2021-10-15 15:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('article', '0004_articlepost_avatar'),
    ]

    operations = [
        migrations.AlterField(
            model_name='articlepost',
            name='avatar',
            field=models.ImageField(blank=True, upload_to='my_blog/media/article/%Y%m%d/'),
        ),
    ]