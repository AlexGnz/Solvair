from django.db import models


class User(models.Model):
    username = models.CharField(max_length=30, blank=True, null=True)
    password = models.CharField(max_length=30, blank=True, null=True)
    TYPE_CHOICES = (('C', 'Client'), ('E', 'Employee'))
    type = models.CharField(max_length=1, choices=TYPE_CHOICES, default='C')

    def __str__(self):
        return "%s" % (self.username)


class Ville(models.Model):
    nom = models.CharField(max_length=50, blank=True, null=True)
    prefixe = models.CharField(max_length=3, blank=True, null=True)

    def __str__(self):
        return "%s - %s" % (self.nom, self.prefixe)


class Avion(models.Model):
    capacite = models.IntegerField(blank=True, null=True)
    nom = models.CharField(max_length=20, blank=True, null=True)
    compagnie = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return "%s de %s places appartenant à %s" % (self.nom, self.capacite, self.compagnie)


class Trajet(models.Model):
    ville_init = models.ForeignKey(Ville, related_name='ville_init', blank=True, null=True, on_delete=models.CASCADE)
    ville_finale = models.ForeignKey(Ville, related_name='ville_finale', blank=True, null=True,
                                     on_delete=models.CASCADE)

    def __str__(self):
        return "%s a %s" % (self.ville_init, self.ville_finale)


class Vol(models.Model):
    trajet = models.ForeignKey(Trajet, on_delete=models.CASCADE, blank=True, null=True)
    avion = models.ForeignKey(Avion, on_delete=models.CASCADE, blank=True, null=True)
    datetime_depart = models.DateTimeField(auto_now=False, blank=True, null=True)
    datetime_arrivee = models.DateTimeField(auto_now=False, blank=True, null=True)
    prix = models.FloatField(blank=True, null=True)
    reference = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return "Vol [%s] decolle le %s de %s et atterit a %s, le %s" % (
        self.reference, self.datetime_depart, self.trajet.ville_init, self.trajet.ville_finale, self.datetime_arrivee)


class Reservation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    vol = models.ForeignKey(Vol, on_delete=models.CASCADE, blank=True, null=True)
    prix = models.FloatField(blank=True, null=True)
    nombre_places = models.IntegerField(blank=True, null=True)
    first_class = models.BooleanField(default=False)

    def __str__(self):
        return "%s a reserve un vol pour %s personnes au prix de %s" % (
        self.user.username, self.nombre_places, self.prix)


class Place(models.Model):
    reservation = models.ForeignKey(Reservation, null=True, on_delete=models.CASCADE)
    emplacement = models.CharField(max_length=3)

    def __str__(self):
        return "%s reserved by %s" % (self.emplacement, self.reservation.user.username)



