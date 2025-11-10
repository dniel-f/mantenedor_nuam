from django.db import models

class Rol(models.Model):
    id_rol = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=50)
    descripcion = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'rol'

    def __str__(self):
        # Le dice a Django que use el nombre
        return self.nombre


class Estado(models.Model):
    id_estado = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=50)
    descripcion = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'estado'

    def __str__(self):
        # Le dice a Django que use el nombre
        return self.nombre


class Usuario(models.Model):
    id_usuario = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    correo = models.CharField(unique=True, max_length=100)
    contrasena_hash = models.CharField(max_length=255)
    fecha_creacion = models.DateTimeField(blank=True, null=True)
    id_rol = models.ForeignKey(Rol, models.DO_NOTHING, db_column='id_rol')
    id_estado = models.ForeignKey(Estado, models.DO_NOTHING, db_column='id_estado', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'usuario'

    def __str__(self):
        # Mostramos el correo, que es único
        return self.correo
    
    @property
    def is_authenticated(self):
        """
        Propiedad para que Django/DRF sepa que este objeto
        representa un usuario logueado.
        """
        return True

    @property
    def is_active(self):
        """
        Propiedad que mapea nuestro campo 'id_estado'
        al 'is_active' que Django espera.
        """
        # Asume que el estado "Activo" se llama 'Activo'
        return self.id_estado and self.id_estado.nombre == 'Activo'

    @property
    def is_staff(self):
        """
        Propiedad que mapea nuestro campo 'id_rol'
        al 'is_staff' que Django espera (para el admin).
        """
        # Asume que el rol de Admin se llama 'Administrador'
        return self.id_rol and self.id_rol.nombre == 'Administrador'

    @property
    def is_superuser(self):
        """
        Para este proyecto, 'is_staff' y 'is_superuser' son lo mismo.
        """
        return self.id_rol and self.id_rol.nombre == 'Administrador'