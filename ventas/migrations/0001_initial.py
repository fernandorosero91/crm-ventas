# Generated manually for ventas app

from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('clientes', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Opportunity',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(default=True)),
                ('title', models.CharField(max_length=150, validators=[django.core.validators.MinLengthValidator(3)], verbose_name='Título')),
                ('estimated_value', models.DecimalField(decimal_places=2, help_text='Valor estimado de la oportunidad (debe ser mayor a 0)', max_digits=12, validators=[django.core.validators.MinValueValidator(0.01)], verbose_name='Valor estimado')),
                ('probability', models.IntegerField(help_text='Probabilidad de cierre entre 0 y 100', validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)], verbose_name='Probabilidad (%)')),
                ('expected_close_date', models.DateField(verbose_name='Fecha esperada de cierre')),
                ('stage', models.CharField(choices=[('prospeccion', 'Prospección'), ('calificacion', 'Calificación'), ('propuesta', 'Propuesta'), ('negociacion', 'Negociación'), ('cierre_ganado', 'Cierre Ganado'), ('cierre_perdido', 'Cierre Perdido')], default='prospeccion', max_length=20, verbose_name='Etapa')),
                ('actual_close_date', models.DateField(blank=True, help_text='Fecha en que se cerró la oportunidad (ganada o perdida)', null=True, verbose_name='Fecha real de cierre')),
                ('loss_reason', models.TextField(blank=True, help_text='Razón por la cual se perdió la oportunidad', verbose_name='Motivo de pérdida')),
                ('weighted_value', models.DecimalField(decimal_places=2, default=0.0, editable=False, help_text='Calculado automáticamente: estimated_value * probability / 100', max_digits=12, verbose_name='Valor ponderado')),
                ('assigned_vendedor', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assigned_opportunities', to=settings.AUTH_USER_MODEL, verbose_name='Vendedor asignado')),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='opportunities', to='clientes.client', verbose_name='Cliente')),
            ],
            options={
                'verbose_name': 'Oportunidad',
                'verbose_name_plural': 'Oportunidades',
                'ordering': ['expected_close_date'],
            },
        ),
        migrations.CreateModel(
            name='FollowUp',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(default=True)),
                ('follow_up_type', models.CharField(choices=[('call', 'Llamada'), ('email', 'Email'), ('meeting', 'Reunión'), ('other', 'Otro')], max_length=20, verbose_name='Tipo de seguimiento')),
                ('date', models.DateTimeField(verbose_name='Fecha')),
                ('notes', models.TextField(help_text='Mínimo 10 caracteres', validators=[django.core.validators.MinLengthValidator(10)], verbose_name='Notas')),
                ('next_action_date', models.DateField(blank=True, null=True, verbose_name='Fecha de próxima acción')),
                ('client', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='follow_ups', to='clientes.client', verbose_name='Cliente')),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_follow_ups', to=settings.AUTH_USER_MODEL, verbose_name='Creado por')),
                ('opportunity', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='follow_ups', to='ventas.opportunity', verbose_name='Oportunidad')),
            ],
            options={
                'verbose_name': 'Seguimiento',
                'verbose_name_plural': 'Seguimientos',
                'ordering': ['-date'],
            },
        ),
        migrations.CreateModel(
            name='StageChange',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('from_stage', models.CharField(max_length=20, verbose_name='Etapa Anterior')),
                ('to_stage', models.CharField(max_length=20, verbose_name='Nueva Etapa')),
                ('changed_at', models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Cambio')),
                ('changed_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='stage_changes_made', to=settings.AUTH_USER_MODEL, verbose_name='Cambiado Por')),
                ('opportunity', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='stage_changes', to='ventas.opportunity', verbose_name='Oportunidad')),
            ],
            options={
                'verbose_name': 'Cambio de Etapa',
                'verbose_name_plural': 'Cambios de Etapa',
                'ordering': ['-changed_at'],
            },
        ),
        migrations.AddIndex(
            model_name='opportunity',
            index=models.Index(fields=['assigned_vendedor', 'stage', 'is_active'], name='ventas_oppo_assigne_8e5c8a_idx'),
        ),
        migrations.AddIndex(
            model_name='opportunity',
            index=models.Index(fields=['client', 'is_active'], name='ventas_oppo_client__c8e9e5_idx'),
        ),
        migrations.AddIndex(
            model_name='opportunity',
            index=models.Index(fields=['expected_close_date'], name='ventas_oppo_expecte_f8a9c3_idx'),
        ),
        migrations.AddIndex(
            model_name='followup',
            index=models.Index(fields=['opportunity', 'date'], name='ventas_foll_opportu_a1b2c3_idx'),
        ),
        migrations.AddIndex(
            model_name='followup',
            index=models.Index(fields=['next_action_date', 'is_active'], name='ventas_foll_next_ac_d4e5f6_idx'),
        ),
        migrations.AddIndex(
            model_name='stagechange',
            index=models.Index(fields=['opportunity', '-changed_at'], name='ventas_stag_opportu_g7h8i9_idx'),
        ),
        migrations.AddIndex(
            model_name='stagechange',
            index=models.Index(fields=['changed_by', '-changed_at'], name='ventas_stag_changed_j0k1l2_idx'),
        ),
    ]
