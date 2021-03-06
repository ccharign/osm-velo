# Generated by Django 4.0.2 on 2022-04-08 07:11

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dijk', '0005_cachenomrue_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='chemin_d',
            options={'ordering': ['-dernier_p_modif', 'date']},
        ),
        migrations.RemoveConstraint(
            model_name='cachenomrue',
            name='Une seule entrée pour chaque (nom, zone).',
        ),
        migrations.RemoveField(
            model_name='cache_adresse',
            name='zone',
        ),
        migrations.RemoveField(
            model_name='cachenomrue',
            name='zone',
        ),
        migrations.AddField(
            model_name='cache_adresse',
            name='ville',
            field=models.ForeignKey(default=25309, on_delete=django.db.models.deletion.CASCADE, to='dijk.ville'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='cachenomrue',
            name='ville',
            field=models.ForeignKey(default=25309, on_delete=django.db.models.deletion.CASCADE, to='dijk.ville'),
            preserve_default=False,
        ),
        migrations.AddConstraint(
            model_name='cachenomrue',
            constraint=models.UniqueConstraint(fields=('nom', 'ville'), name='Une seule entrée pour chaque (nom, ville).'),
        ),
    ]
