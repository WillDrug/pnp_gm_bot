from django.db import models
from django.contrib.auth.models import User
from game.models import Game
import time
from datetime import datetime
# Create your models here.

class Chat(models.Model):
    added = models.FloatField(default=0)
    user = models.ForeignKey(User)
    game = models.ForeignKey(Game)
    msg = models.CharField(max_length=255)

    @property
    def as_dict(self):
        return dict(readable_date=datetime.fromtimestamp(self.added).strftime('%Y-%m-%dT%H:%M:%S'), added=self.added, user=self.user.username, game=self.game.name, msg=self.msg)

    def save(self, *ar, **kw):
        self.added = time.time()
        super(Chat, self).save(*ar, **kw)