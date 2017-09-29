from django.db import models

class Game(models.Model):
    id = models.CharField('lolz', max_length=8, primary_key=True)
    owner = models.CharField(max_length=200)
    name = models.CharField(max_length=200)

class Module(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    flavour = models.CharField(max_length=200)
    players = models.IntegerField(default=0)