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
    setting_id = Column(String)
    module_name = Column(String)
    flavourtext = Column(String)  #flavour that descripts and starts the module
    finished = Column(Boolean)

    def __repr__(self):
        return "<Module(module_id='%s', setting_id='%s', module_name='%s', flavourtext='%s')>" % (
            self.module_id, self.setting_id, self.module_name, self.flavourtext
        )

class ModulePlayer(Base):
    __tablename__ = 'moduleplayer'

    module_id = Column(String, primary_key=True)
    username = Column(String, primary_key=True)
    char_id = Column(String)
    in_game = Column(Boolean)

    def __repr__(self):
        return "<ModulePlayer(game_id='%s', username='%s')>" % (
            self.game_id, self.username
        )


class Character(Base):
    __tablename__ = 'character'

    setting_id = Column(String, primary_key=True)
    owner = Column(String, primary_key=True)
    name = Column(String, primary_key=True)
    display_name = Column(String)
    known = Column(Boolean)
    reference = Column(String)
    flavourtext = Column(String)
    maneuver_list = Column(String)
    experience = Column(Integer)

    def __repr__(self):
        return "<Character(char_id='%s', username='%s', reference='%s', flavourtext='%s')>" % (
            self.char_id, self.username, self.reference, self.flavourtext
        )

    def populate(self, session):
        self.actions = dict()
        self.parms = dict()
        self.plugins = [CoreParms, Stats, Combat, Magic, Secondary, Tertiary]
        for q in plugins:
            self.parms[q.__referencename__] = self.load_parm(q, session)
            self.actions[q.__referencename__] = []
            self.append_parm(self.parms[q.__referencename__], q.__referencename__)

        self.influences = dict()
        self.influence_actions = dict()
        self.influence_list = [Feats, Items]
        for q in self.influences:
            self.influences[q.__referencename__] = self.load_parm(q, session)
            self.influences[q.__referencename__] = []
            self.append_influence(self.influence_actions[q.__referencename__], q.__referencename__)

        return True

    def load_parm(self, parm, session):
        return session.query(parm).filter(parm.char_id == self.char_id).all()

    def append_parm(self, parm, declared_name):
        self.actions[declared_name] = []
        for i in parm:
            self.actions[declared_name].append(parm.parm_name)

    def append_influence(self, parm, declared_name):
        self.influences[declared_name] = []
        for q in parm:
            self.influences[declared_name].append(parm)

class CharacterExtraDetails(Base):
    __tablename__ = 'extradetails'


class CoreParms(Base, BaseCharacterParm):
    __tablename__ = 'coreparms'

    __basedice__ = 100
    __parmlist__ = 'Здоровье,Инициатива'
    __cost__ = 99999 #lol kek
    __referencename__ = 'Core'

    def calculate_bonus(self, influence):
        return (self.parm_value+influence)*10


class Stats(Base, BaseCharacterParm):
    __tablename__ = 'stats'

    __basedice__ = 10
    __parmlist__ = 'Сила,Выносливость,Ловкость,Скорость,Интеллект,Внимание,Мудрость,Харизма'
    __cost__ = 25  # each point costs 10
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

class Combat(Base, BaseCharacterParm):
    __tablename__ = 'combat'

    __basedice__ = 100
    __parmlist__ = 'Атака,Блок,Уворот,Стойкость'
    __cost__ = 5
    __referencename__ = 'Combat'


class Magic(Base, BaseCharacterParm):
    __tablename__ = 'magic'

    __basedice__ = 100
    __parmlist__ = 'Атака,Защита,Аккумуляция'
    __cost__ = 5
    __referencename__ = 'Magic'

class Secondary(Base, BaseCharacterParm):
    __tablename__ = 'secondary'

    __basedice__ = 100
    __parmlist__ = 'Акробатика,Атлетика,Оккультизм,Внимание,Социал,Стиль'
    __cost__ = 1
    __referencename__ = 'Secondary'


class Tertiary(Base, BaseCharacterParm):
    __tablename__ = 'tertiary'

    __basedice__ = 100
    __parmlist__ = 'dynamic'
    __cost__ = 0.1
    __referencename__ = 'Tertiary'

class Feats(Base, BaseCharacterInfluence):
    __tablename__ = 'feats'
    __referencename__ = 'Feats'

class Items(Base, BaseCharacterInfluence):
    __tablename__ = 'items'
    def populate(self):
        super()
        self.__referencename__ = 'Items'

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
    scene_id = Column(String)

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
    stored_id = Column(String)

    def __repr__(self):
        return "<GameContext(username='%s', context_function='%s', context_marker='%s', on_finish='%s', finish_marker='%s', stored_id='%s')>" % (
            self.username, self.context_function, self.context_marker, self.on_finish, self.finish_marker, self.stored_id
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
