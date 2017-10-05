from django.apps import AppConfig
from django.db.models.signals import post_save

class MainConfig(AppConfig):
    name = 'main'

class ToolsConfig(AppConfig):
    name = 'tools'

class GameConfig(AppConfig):
    name = 'game'