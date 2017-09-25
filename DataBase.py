from GameModel import BaseCharacterParm, BaseCharacterInfluence
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey

__DBNAME__ = 'sqlite:///pnp_gm_bot.sqlite'
Base = declarative_base() #this binds metadata, fuck you.

# GAME MODEL
class Setting(Base):
    __tablename__ = 'setting'

    setting_id = Column(String, primary_key=True)
    setting_name = Column(String)
    flavourtext = Column(String)
    owner = Column(String)  # Game Master

    def __repr__(self):
        return "<Setting(setting_id='%s, setting_name='%s, flavourtext='%s, owner='%s)>" % (
            self.setting_id, self.setting_name, self.flavourtext, self.owner
        )

class Module(Base):
    __tablename__ = 'module'

    module_id = Column(String, primary_key=True)
    setting_id = Column(String, ForeignKey('setting.setting_id'))
    module_name = Column(String)
    flavourtext = Column(String)  #flavour that descripts and starts the module

    def __repr__(self):
        return "<Module(module_id='%s', setting_id='%s', module_name='%s', flavourtext='%s')>" % (
            self.module_id, self.setting_id, self.module_name, self.flavourtext
        )

class ModulePlayer(Base):
    __tablename__ = 'moduleplayer'

    game_id = Column(String, ForeignKey('module.module_id'), primary_key=True)
    username = Column(String, primary_key=True)
    char_id = Column(String)
    in_game = Column(Boolean)

    def __repr__(self):
        return "<ModulePlayer(game_id='%s', username='%s')>" % (
            self.game_id, self.username
        )

1
class Character(Base):
    __tablename__ = 'character'

    char_id = Column(String, primary_key=True)
    owner = Column(String)
    reference = Column(String)
    flavourtext = Column(String)

    def __repr__(self):
        return  "<Character(char_id='%s', username='%s', reference='%s', flavourtext='%s')>" % (
            self.char_id, self.username, self.reference, self.flavourtext
        )

    def populate(self, session):
        self.actions = dict()
        self.stats = session.query(Stats).filter(Stats.char_id == self.char_id).all()
        self.actions['Stats'] = []
        for i in self.stats:
            self.action['Stats'].append(i.parm_name)

        return True

    def roll(self):

class CoreParms(Base, BaseCharacterParm):
    __basedice__ = 100
    __parmlist__ = 'Здоровье,Инициатива'
    __cost__ = 1
    __referencename__ = 'Core'

    def calculate_bonus(self, influence):
        return self.parm_value*10 + influence


class Stats(Base, BaseCharacterParm):
    __basedice__ = 10
    __parmlist__ = 'Сила,Выносливость,Ловкость,Скорость,Интеллект,Внимание,Мудрость,Харизма'
    __cost__ = 10  # each point costs 10
    __referencename__ = 'Stats'


    def calculate_bonus(self, influence):
        new_parm_value = self.parm_value + influence
        if new_parm_value == 0:
            return -200
        elif new_parm_value == 1:
            return -100
        elif new_parm_value == 2:
            return -50
        elif new_parm_value == 3:
            return -25
        elif new_parm_value == 4:
            return -10
        elif new_parm_value == 5:
            return 0
        elif new_parm_value == 6 or new_parm_value == 7:
            return 5
        elif new_parm_value == 8 or new_parm_value == 9:
            return 10
        elif new_parm_value >= 10:
            return 15+5*(new_parm_value-10)


class Scene(Base):
    __tablename__ = 'scene'

    scene_id = Column(String, primary_key=True)
    flavourtext = Column(String)

    def __repr__(self):
        return "<Scene(scene_id='%s', flavourtext='%s')>" % (
            self.scene_id, self.flavourtext
        )

class ScenePlayer(Base):
    __tablename__ = 'sceneplayer'

    char_id = Column(String, primary_key=True)  #one character to one scene at all times.
    scene_id = Column(String, ForeignKey('scene.scene_id'))

    def __repr__(self):
        return "<ScenePlayer(char_id='%s', scene_id='%s')>" % (
            self.char_id, self.scene_id
        )


# class ModuleCharacters(Base):
# class Character(Base):

# GAME ENGINE CLASSES
class GameContext(Base):
    __tablename__ = 'gcontext'

    username = Column(String, primary_key=True)
    context_function = Column(String)
    context_marker = Column(String)
    on_finish = Column(String)
    finish_marker = Column(String)

    def __repr__(self):
        return "<GameContext(username='%s', context_function='%s', on_finish='%s')>" % (
            self.username, self.context_function, self.on_finish
        )

# INTERFACE CLASSES
class InterfaceContext(Base):
    __tablename__ = 'icontext'

    username = Column(String, primary_key=True)
    context_function = Column(String)  # function to handle request
    return_payload = Column(String)  # current json
    request_payload = Column(String)  # parameters, taken from original payload
    flavourtext = Column(String)
    on_finish = Column(String)  # game engine function to call on finish
    marker = Column(String) #marker for on_finish function

    def __repr__(self):
        return "<InterfaceContext(username='%s', context_type='%s', context_function='%s')>" % (
            self.username, self.context_type, self.context_function
        )

class UserId(Base):
    __tablename__ = 'userid'

    username = Column(String, primary_key=True)
    chat_id = Column(String)

if __name__ == '__main__':
    engine = create_engine(__DBNAME__, echo=True)
    Base.metadata.create_all(engine)
