from django.db import models
from django.contrib.auth.models import User
from game.models import Game
# Create your models here.

class Chat(models.Model):
    added = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User)
    game = models.ForeignKey(Game)
    msg = models.CharField(max_length=255)

    @property
    def as_dict(self):
        return dict(added=self.added, user=self.user.username, game=self.game.name, msg=self.msg)
