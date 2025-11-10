# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class Auditoria(models.Model):
    id_auditoria = models.AutoField(primary_key=True)
    fecha = models.DateTimeField(blank=True, null=True)
    tipo = models.CharField(max_length=50, blank=True, null=True)
    resultado = models.CharField(max_length=100, blank=True, null=True)
    observaciones = models.TextField(blank=True, null=True)
    id_usuario = models.ForeignKey('usuarios.Usuario', models.DO_NOTHING, db_column='id_usuario', blank=True, null=True)
    id_calificacion = models.ForeignKey('calificaciones.Calificacion', models.DO_NOTHING, db_column='id_calificacion', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'auditoria'


class Log(models.Model):
    id_log = models.AutoField(primary_key=True)
    fecha = models.DateTimeField(blank=True, null=True)
    accion = models.CharField(max_length=6)
    detalle = models.TextField(blank=True, null=True)
    id_usuario = models.ForeignKey('usuarios.Usuario', models.DO_NOTHING, db_column='id_usuario', blank=True, null=True)
    id_calificacion = models.ForeignKey('calificaciones.Calificacion', models.DO_NOTHING, db_column='id_calificacion', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'log'
