# Add the items relation after Weapon exists to keep initial migrations acyclic.
# ruff: noqa: RUF012

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('divinities', '0002_god_children_demigods'),
        ('items', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='god',
            name='weapons',
            field=models.ManyToManyField(
                blank=True, related_name='associated_gods', to='items.weapon'
            ),
        ),
    ]
