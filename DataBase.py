from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, ForeignKey

__DBNAME__ = 'sqlite:///pnp_gm_bot.sqlite'
Base = declarative_base() #this binds metadata, fuck you.

# GAME MODEL
class Setting(Base):
    __tablename__ = 'setting'

    setting_id = Column(String, primary_key=True)
    setting_name = Column(String)
    flavourtext = Column(String)
    owner = Column(String)

    def __repr__(self):
        return "<Setting(setting_id='%s, setting_name='%s, flavourtext='%s, owner='%s)>" % (
            self.setting_id, self.setting_name, self.flavourtext, self.owner
        )

class Module(Base):
    __tablename__ = 'module'

    module_id = Column(String, primary_key=True)
    setting_id = Column(String, ForeignKey('setting.setting_id'))
    module_name = Column(String)
    flavourtext = Column(String)

class ModulePlayers(Base):
    __tablename__ = 'gamelist'

    game_id = Column(String, primary_key=True)
    username = Column(String)

    def __repr__(self):
        return "<ModulePlayers(game_id='%s', username='%s')>" % (
            self.game_id, self.username
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

class UserIds(Base):
    __tablename__ = 'userids'

    username = Column(String, primary_key=True)
    chat_id = Column(String)

if __name__ == '__main__':
    engine = create_engine(__DBNAME__, echo=True)
    Base.metadata.create_all(engine)
