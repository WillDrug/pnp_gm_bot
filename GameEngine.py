import time
from DataBase import __DBNAME__
from DataBase import *
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from local import lang
import sys
locale = lang['ru']
__EMPTY_PAYLOAD__ = dict()
__EMPTY_PAYLOAD__['marker'] = ''


# INTERFACE CONTRACTS FUNCTION
# always returns next action
# empty action is a payload {'type': 'none'}
def request_choose(choose_list, max_num, return_function, return_marker, flavourtext, additional = None):
    request_payload = dict()
    request_payload['type'] = 'choose'
    request_payload['marker'] = return_marker
    request_payload['callback'] = return_function
    request_payload['flavourtext'] = flavourtext
    request_payload['payload'] = {
        'choose_list': choose_list,
        'max_num': max_num,
        'additional': additional
    }
    return request_payload


def request_gather(max_num, return_function, return_marker, flavourtext, additional = None):
    request_payload = dict()
    request_payload['type'] = 'gather'
    request_payload['marker'] = return_marker
    request_payload['callback'] = return_function
    request_payload['flavourtext'] = flavourtext
    request_payload['payload'] = {
        'max_num': max_num,  # -1 is infinite, 1-n is finite
        'additional': additional
    }
    return request_payload
    # GAME PROCESS


def request_send(userlist, return_function, return_marker, flavourtext, additional = None):
    request_payload = dict()
    request_payload['type'] = 'send'
    request_payload['marker'] = return_marker
    request_payload['callback'] = return_function
    request_payload['flavourtext'] = flavourtext
    request_payload['payload'] = dict()
    request_payload['payload'] = {'userlist': userlist,
                                  'additional': additional
                                  }
    return request_payload

def request_spread(spread_list, start_value, points_available, cost, return_function, return_marker, flavourtext, additional = None):
    request_payload = dict()
    request_payload['type'] = 'spread'
    request_payload['marker'] = return_marker
    request_payload['callback'] = return_function
    request_payload['flavourtext'] = flavourtext
    request_payload['payload'] = dict()
    request_payload['payload'] = {
        'spread_list': spread_list,
        'start_value': start_value,
        'points': points_available,
        'cost': cost,
        'additional': additional
    }
    return request_payload

class GameEngine:
    def __init__(self):
        engine = create_engine(__DBNAME__)
        self.session = sessionmaker(bind=engine)()

    def finish_up(self, on_finish, username, payload):
        return eval('self.' + on_finish)(username, payload)

    def get_context(self, username, fname):
        return self.session.query(GameContext).filter(GameContext.username == username).filter(GameContext.context_function == fname).first()

    def edit_context(self, username, context_function, on_finish, finish_marker, stored_id):
        context = self.get_context(username, context_function)
        if context is None:
            self.session.add(GameContext(username=username,
                                     context_function=context_function,
                                     on_finish=on_finish,
                                     finish_marker=finish_marker,
                                     stored_id=stored_id
                                     )
                             )
        else:
            context.on_finish = on_finish if on_finish is not None else context.on_finish
            context.finish_marker = finish_marker if finish_marker is not None else context.finish_marker
            context.stored_id = stored_id if stored_id is not None else context.stored_id
        self.session.commit()

    def delete_context(self, username, fname):
        context = self.session.query(GameContext).filter(GameContext.username == username).filter(GameContext.context_function == fname).first()
        if context is not None:
            self.session.delete(context)
            self.session.commit()
        return True

    def handle(self, username, text):
        context = self.get_context(username, 'handle')
        if context is None:
            self.create_context(username, 'handle', 'main_menu', '', '')
            context = self.get_context(username, 'handle')
            payload = __EMPTY_PAYLOAD__
            payload['marker'] = context.finish_marker
        return self.finish_up(context.on_finish, username, payload)

    # MENU STRUCTURE
    def main_menu(self, username, payload):
        if payload['marker'] == '':  # no requests were made prior to this
            chooselist = []
            gming, playing = self.list_games(username)
            for q in gming:
                chooselist.append(locale['game']['master'] + q.module_name)
            for q in playing:
                chooselist.append(locale['game']['play'] + q.module_name)
            chooselist.append(locale['game']['create_game'])
            return request_choose(chooselist, 1, 'main_menu', 'first_chosen',
                                  locale['game']['main_menu'])
        if payload['marker'] == 'first_chosen':
            # payload will be from CHOOSE here.
            chosen = payload['payload']['chosen'][0]
            if chosen == locale['game']['create_game']:
                newgame = dict()
                newgame['marker'] = 'main'
                newgame['payload'] = dict()
                return self.create_game(username, newgame)  # create game
            else:
                module = self.session.query(Module).filter(Module.module_name == chosen[8:]).first()
                if chosen.startswith(locale['game']['play']):
                    marker = 'player'
                elif chosen.startswith(locale['game']['master']):
                    marker = 'gm'
                self.edit_context(username, 'handle', 'game', marker, module.module_id)
                self.session.commit()
                return request_send([username], 'game', 'first_entrance', 'Вы в игре.')
        return {'type': 'none'}

    def create_game(self, username, payload):
        if payload['marker'] == 'main':  # create game process starts
            settings = self.session.query(Setting).filter(Setting.owner == username).all()
            if settings.__len__() > 0:
                chooselist = []
                for i in settings:
                    chooselist.append(i.setting_name)
                chooselist.append('Создать')
                return request_choose(chooselist, 1, 'create_game', 'setting_chosen',
                                      locale['game']['choose_setting'])
            else:
                payload['marker'] = 'setting_chosen'
                payload['payload']['chosen'] = [locale['game']['create']]
        if payload['marker'] == 'setting_chosen':
            if payload['payload']['chosen'][0] == locale['game']['create']:
                self.edit_context(username, 'create_setting', 'create_game', 'setting_created', '')
                return self.create_setting(username, __EMPTY_PAYLOAD__)
            else:
                setting_chosen = self.session.query(Setting).filter(Setting.owner == username). \
                    filter(Setting.setting_name == payload['payload']['chosen'][0]).first()
                self.edit_context(username, 'create_game', None, None, setting_chosen.setting_id)
                payload['marker'] = 'create_module'
        if payload['marker'] == 'setting_created':
            self.edit_context(username, 'create_game', None, None, payload['payload']['create_setting'])
            payload['marker'] = 'create_module'
        if payload['marker'] == 'create_module':
            context = self.get_context(username, 'create_game')
            new_module = Module(module_id=username + str(int(time.time())), setting_id=context.stored_id,
                                module_name='', flavourtext='', finished=False)
            self.edit_context(username, 'create_game', None, None, new_module.module_id)
            self.session.add(new_module)
            self.session.commit()
            return request_gather(1, 'create_game', 'module_name', locale['game']['type_module_name'])
        if payload['marker'] == 'module_name':
            context = self.get_context(username, 'create_game')
            module = self.session.query(Module).filter(Module.module_id == context.stored_id).first()
            module.module_name = payload['payload']['chosen'][0]
            self.session.commit()
            return request_gather(1, 'create_game', 'module_flavour', locale['game']['type_module_flavour'])
        if payload['marker'] == 'module_flavour':
            context = self.get_context(username, 'create_game')
            module = self.session.query(Module).filter(Module.module_id == context.stored_id).first()
            module.flavourtext = payload['payload']['chosen'][0]
            self.edit_context(username, 'handle', 'game', 'dm', '')
            self.edit_context(username, 'game', '', '', module.module_id)
            return request_send([username], 'game', 'dm', locale['game']['in_game'])

    def create_setting(self, username, payload):
        if payload['marker'] == '':
            return request_gather(1, 'create_setting', 'name_chosen', locale['game']['type_setting_name'])
        if payload['marker'] == 'name_chosen':
            setting = Setting(setting_id=username + str(int(time.time())), setting_name=payload['payload']['chosen'][0],
                              flavourtext='', owner=username)
            self.edit_context(username, 'create_setting', None, None, setting.setting_id)
            return request_gather(1, 'create_setting', 'flavour_chosen', locale['game']['type_setting_flavour'])
        if payload['marker'] == 'flavour_chosen':
            context = self.get_context(username, 'create_setting')
            setting = self.session.query(Setting).filter(Setting.setting_id == context.stored_id).first()
            setting.flavourtext = payload['payload']['chosen'][0]
            self.session.commit()
            new_payload = __EMPTY_PAYLOAD__
            new_payload['marker'] = context.finish_marker
            new_payload['payload']['create_setting'] = setting.setting_id
            return self.finish_up(context.on_finish, context.username, new_payload)

    def game(self, username, payload):
        # context.stored_id holds module id
        # generic commands:
        # split
        if payload['marker'] == 'player':
            char = self.get_character(username, None)
            if char is None:
                self.edit_context(username, 'create_character', 'game', 'player', '')
                self.session.commit()
                return self.create_character(username, __EMPTY_PAYLOAD__)
            if 'chosen' not in payload['payload'].keys():
                return request_gather(1, 'game', 'player', locale['game']['player_commands'])
            else:
                comm = payload['payload']['chosen'][0]

        if payload['marker'] == 'dm':
            # this is a player action or DM flavourtext
            if 'chosen' not in payload['payload'].keys():
                return request_gather(1, 'game', 'player', locale['game']['gm_commands'])
            else:
                comm = payload['payload']['chosen'][0]

    def get_current_setting(self, username):
        return self.session.query(Setting).join(Module, Module.setting_id == Setting.setting_id).filter(
            Module.module_id == self.get_context(username, 'game').stored_id)

    def get_character(self, username, name):
        if name == None:
            return self.session.query(Character).filter(Character.owner == username).filter(
                Character.setting_id == self.get_current_setting(username).setting_id).first()
        else:
            return self.session.query(Character).filter(Character.owner == username).filter(
                Character.setting_id == self.get_current_setting(username).setting_id).\
                filter(Character.name == name).first()

    def create_character(self, username, payload):
        if payload['marker'] == '':  # start creation
            return request_gather(1, 'create_character', 'name', locale['game']['type_character_name'])
        if payload['marker'] == 'name':
            char = Character(char_id=username + str(int(time.time())),
                             setting_id=self.get_current_setting(username).setting_id, owner=username,
                             name=payload['payload']['chosen'][0], display_name='', known=False,
                             reference='', flavourtext='', experience=600)
            self.edit_context(username, 'create_character', None, None, char.name)
            self.session.add(char)
            self.session.commit()
            return request_gather(1, 'create_character', 'display_name', locale['game']['type_character_d_name'])
        context = self.get_context(username, 'create_character')
        char = self.get_character(username, context.stored_id)
        if payload['marker'] == 'display_name':
            char.display_name = payload['payload']['chosen'][0]
            self.session.commit()
            return request_gather(1, 'create_character', 'reference', locale['game']['type_character_reference'])
        if payload['marker'] == 'reference':
            char.reference = payload['payload']['chosen'][0]
            self.session.commit()
            return request_gather(1, 'create_character', 'flavour', locale['game']['type_character_flavour'])
        if payload['marker'] == 'flavour':
            char.flavourtext = payload['payload']['chosen'][0]
            self.session.commit()
            payload['marker'] = 'parms'
            # from this point on SHIT HITS THE FAN.
            # for all those we need 1) init. 2) request shit 3) fucking inform
            # 1) parms
            char.populate()  # hope this works
            parms = char.parm_list
            parms = [q.__name__ for q in parms]
            self.edit_context(username, 'manage_parm', 'create_character', 'parms', char.name)
            payload = __EMPTY_PAYLOAD__
            payload['marker'] = 'create'
            payload['payload']['parm'] = parms[0]
            payload['payload']['parm_list'] = parms[1:]
            return
        if payload['marker'] == 'parms':
            return

            # 2) influence
            # 3) lists
            # 4)


    def manage_parm(self, username, payload): #CRUD
        context = self.get_context(username, 'manage_parm')
        char = self.get_character(username, context.stored_id)
        if payload['marker'] == 'create':
            parmclass = eval(payload['payload']['parm'])
            if parmclass.__parmlist__ == 'dynamic':
                return request_gather(0, 'manage_parm', 'gather_create', parmclass.__flavourtext__,payload['payload'])
            else:
                parmlist = parmclass.__parmlist__.split(',')
                for i in parmlist:
                    parm = parmclass(char_id=char.char_id, parm_name=i, parm_value=parmclass.__startvalue__,
                                     bonus_sources='', penalty_sources='')
                    self.session.add(parm)
                self.session.commit()
                return request_spread(parmlist, parmclass.__startvalue__, char.experience, parmclass.__cost__,
                                      'manage_parm', 'created', parmclass.__flavourtext__, payload['payload'])
        if payload['marker'] == 'gather_create':
            parmclass = eval(payload['payload']['original']['additional']['parm'])
            for q in payload['payload']['chosen']:
                parm = parmclass(char_id=context.stored_id,parm_name=q,parm_value=parmclass.__startvalue__,
                                 bonus_sources='', penalty_sources='')
                self.session.add(parm)
            self.session.commit()
            return request_spread(payload['payload']['chosen'], parmclass.__startvalue__, char.experience,
                                  parmclass.__cost__, 'manage_parm', 'created', parmclass.__flavourtext__,
                                  payload['payload'])
        if payload['marker'] == 'created':
            parmclass = eval(payload['payload']['original']['additional']['parm'])
            for q in payload['payload']['spread']:
                parm = self.session.query(parmclass).filter(parmclass.char_id==char.char_id).filter(parmclass.parm_name == q).first()
                parm.parm_value = payload['payload']['spread'][q]




        return __EMPTY_PAYLOAD__

    def manage_influence(self, username, payload): #CRUD
        return True

    def manage_resource(self, username, payload): #CRUD
        return True

    def manage_list(self, username, payload): #CRUD
        return True
    # INTERFACE FUNCTIONS
    def list_games(self, username):
        dming = self.session.query(Module).join(Setting, Setting.setting_id == Module.setting_id).filter(
            Setting.owner == username).filter(~Module.finished).all()
        playing = self.session.query(Module).join(ModulePlayer,
                                                  ModulePlayer.module_id == Module.module_id).filter(
            ModulePlayer.username == username).filter(~Module.finished).all()

        return dming, playing
