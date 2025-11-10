from django.db import models

# --- NUEVO MANAGER ---
# Este Manager se asegura de que Calificacion.objects.all()
# SÓLO devuelva las calificaciones activas (borrado lógico)
class CalificacionActivaManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(activo=True)


class Calificacion(models.Model):
    id_calificacion = models.AutoField(primary_key=True)
    monto = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    factor = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True)
    fecha_emision = models.DateField(blank=True, null=True)
    fecha_pago = models.DateField(blank=True, null=True)
    id_usuario = models.ForeignKey('usuarios.Usuario', models.DO_NOTHING, db_column='id_usuario', blank=True, null=True)
    id_instrumento = models.ForeignKey('instrumentos.Instrumento', models.DO_NOTHING, db_column='id_instrumento', blank=True, null=True)
    id_mercado = models.ForeignKey('instrumentos.Mercado', models.DO_NOTHING, db_column='id_mercado', blank=True, null=True)
    id_archivo = models.ForeignKey('archivos.Archivo', models.DO_NOTHING, db_column='id_archivo', blank=True, null=True)
    id_estado = models.ForeignKey('usuarios.Estado', models.DO_NOTHING, db_column='id_estado', blank=True, null=True)
    fecha_registro = models.DateTimeField(blank=True, null=True) # El default CURRENT_TIMESTAMP de la BBDD se encarga
    
    # --- CAMPO NUEVO ---
    activo = models.BooleanField(default=True)

    # --- MANAGERS NUEVOS ---
    objects = CalificacionActivaManager() # Manager por defecto (solo activos)
    objects_all = models.Manager()        # Manager que ve TODO (activos e inactivos)

    class Meta:
        managed = False
        db_table = 'calificacion'

    def __str__(self):
        return f"Calificación {self.id_calificacion}"


class Calificaciontributaria(models.Model):
    id_calificacion_tributaria = models.AutoField(primary_key=True)
    id_calificacion = models.ForeignKey(Calificacion, models.DO_NOTHING, db_column='id_calificacion')
    secuencia_evento = models.CharField(max_length=50, blank=True, null=True)
    evento_capital = models.CharField(max_length=100, blank=True, null=True)
    anio = models.TextField(blank=True, null=True)  # This field type is a guess.
    valor_historico = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    descripcion = models.TextField(blank=True, null=True)
    ingreso_por_montos = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'calificaciontributaria'


class Factortributario(models.Model):
    id_factor = models.AutoField(primary_key=True)
    id_calificacion_tributaria = models.ForeignKey(Calificaciontributaria, models.DO_NOTHING, db_column='id_calificacion_tributaria')
    codigo_factor = models.CharField(max_length=10, blank=True, null=True)
    descripcion_factor = models.CharField(max_length=255, blank=True, null=True)
    valor_factor = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'factortributario'