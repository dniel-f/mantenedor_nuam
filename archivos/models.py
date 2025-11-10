# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class Archivo(models.Model):
    id_archivo = models.AutoField(primary_key=True)
    nombre_archivo = models.CharField(max_length=255)
    fecha_carga = models.DateTimeField(blank=True, null=True)
    estado_validacion = models.CharField(max_length=9, blank=True, null=True)
    ruta = models.CharField(max_length=255, blank=True, null=True)
    id_usuario = models.ForeignKey('usuarios.Usuario', models.DO_NOTHING, db_column='id_usuario', blank=True, null=True)
    id_estado = models.ForeignKey('usuarios.Estado', models.DO_NOTHING, db_column='id_estado')

    class Meta:
        managed = False
        db_table = 'archivo'

    def __str__(self):
        return self.nombre_archivo