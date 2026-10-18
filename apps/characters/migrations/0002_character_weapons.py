# Add the items relation after Weapon exists to keep initial migrations acyclic.
# ruff: noqa: RUF012

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('characters', '0001_initial'),
        ('items', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='character',
            name='weapons',
            field=models.ManyToManyField(blank=True, related_name='wielded_by', to='items.weapon'),
        ),
    ]
