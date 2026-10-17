# This relationship is added after Character's table exists to avoid a
# circular dependency between the characters and divinities initial migrations.
# ruff: noqa: RUF012

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('characters', '0001_initial'),
        ('divinities', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='god',
            name='children_demigods',
            field=models.ManyToManyField(
                blank=True,
                help_text='Named demigod children.',
                related_name='divine_parent_god',
                to='characters.character',
            ),
        ),
    ]
