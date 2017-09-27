import time
from DataBase import __DBNAME__
from DataBase import *
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

__EMPTY_PAYLOAD__ = dict()
__EMPTY_PAYLOAD__['marker'] = ''


# INTERFACE CONTRACTS FUNCTION
# always returns next action
# empty action is a payload {'type': 'none'}
def request_choose(choose_list, max_num, return_function, return_marker, flavourtext):
    request_payload = dict()
    request_payload['type'] = 'choose'
    request_payload['marker'] = return_marker
    request_payload['callback'] = return_function
    request_payload['flavourtext'] = flavourtext
    request_payload['payload'] = {
        'choose_list': choose_list,
        'max_num': max_num
    }
    return request_payload


def request_gather(max_num, return_function, return_marker, flavourtext):
    request_payload = dict()
    request_payload['type'] = 'gather'
    request_payload['marker'] = return_marker
    request_payload['callback'] = return_function
    request_payload['flavourtext'] = flavourtext
    request_payload['payload'] = {
        'max_num': max_num  # -1 is infinite, 1-n is finite
    }
    return request_payload
    # GAME PROCESS


def request_send(userlist, return_function, return_marker, flavourtext):
    request_payload = dict()
    request_payload['type'] = 'send'
    request_payload['marker'] = return_marker
    request_payload['callback'] = return_function
    request_payload['flavourtext'] = flavourtext
    request_payload['payload'] = dict()
    request_payload['payload']['userlist'] = userlist
    return request_payload


class GameEngine:
    def __init__(self):
        engine = create_engine(__DBNAME__)
        self.session = sessionmaker(bind=engine)()

    def get_context(self, username):
        return self.session.query(GameContext).filter(GameContext.username == username).first()

    def handle(self, username, text):
        context = self.get_context(username)
        if context is None:
            self.session.add(GameContext(username=username, context_function='main_menu', context_marker='',
                                         finish_marker='', on_finish=''
                                         )
                             )
            self.session.commit()
            context = self.get_context(username)
        return eval('self.' + context.context_function)(username, {'marker': '', 'payload': text})

    # MENU STRUCTURE

    def main_menu(self, username, payload):
        if payload['marker'] == '':  # no requests were made prior to this
            text = payload['payload']  # we don't need this in the main menu, but still
            chooselist = []
            gming, playing = self.list_games(username)
            for q in gming:
                chooselist.append('Мастер: ' + q.module_name)
            for q in playing:
                chooselist.append('Играть: ' + q.module_name)
            chooselist.append('Создать Игру')
            return request_choose(chooselist, 1, 'main_menu', 'first_chosen',
                                  'Вы в главном меню.\nВыберите игру для входа или создайте новую.')
        if payload['marker'] == 'first_chosen':
            # payload will be from CHOOSE here.
            chosen = payload['payload']['chosen'][0]
            if chosen == 'Создать Игру':
                newgame = dict()
                newgame['marker'] = 'main'
                newgame['payload'] = dict()
                return self.create_game(username, newgame)  # create game
            else:
                context = self.get_context(username)
                module = self.session.query(Module).filter(Module.module_name == chosen[8:]).first()
                context.stored_id = module.module_id
                context.context_function = 'game'
                context.finish_marker = ''
                context.on_finish = ''
                if chosen.startswith('Играть: '):
                    context.context_marker = 'player'
                elif chosen.startswith('Мастер: '):
                    context.context_marker = 'gm'
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
                                      'Выберите сеттинг (или создайте новый)')
            else:
                payload['marker'] = 'setting_chosen'
                payload['payload']['chosen'] = ['Создать']
        if payload['marker'] == 'setting_chosen':
            if payload['payload']['chosen'][0] == 'Создать':
                payload['marker'] = 'new_setting'
            else:
                setting_chosen = self.session.query(Setting).filter(Setting.owner == username). \
                    filter(Setting.setting_name == payload['payload']['chosen'][0]).first()
                context = self.get_context(username)
                context.stored_id = setting_chosen.setting_id
                self.session.commit()
                payload['marker'] = 'create_module'
        if payload['marker'] == 'new_setting':
            context = self.get_context(username)
            context.context_function = 'create_game'
            context.context_marker = 'setting_created'
            context.on_finish = 'create_game'
            context.finish_marker = 'create_module'
            self.session.commit()
            return self.create_setting(username, __EMPTY_PAYLOAD__)
        if payload['marker'] == 'create_module':
            context = self.get_context(username)
            new_module = Module(module_id=username + str(int(time.time())), setting_id=context.stored_id,
                                module_name='', flavourtext='', finished=False)
            context.stored_id = new_module.module_id
            self.session.add(new_module)
            self.session.commit()
            return request_gather(1, 'create_game', 'module_name', 'Введите название модуля:')
        if payload['marker'] == 'module_name':
            context = self.get_context(username)
            module = self.session.query(Module).filter(Module.module_id == context.stored_id).first()
            module.module_name = payload['payload']['chosen'][0]
            self.session.commit()
            return request_gather(1, 'create_game', 'module_flavour', 'Введите описание модуля:')
        if payload['marker'] == 'module_flavour':
            context = self.get_context(username)
            module = self.session.query(Module).filter(Module.module_id == context.stored_id).first()
            module.flavourtext = payload['payload']['chosen'][0]
            context.context_function = 'game'
            context.context_marker = ''
            context.on_finish = ''
            context.finish_marker = ''
            context.stored_id = module.module_id  # active game stored here
            self.session.commit()
            return request_send([username], 'game', 'first_entrance', 'Вы в игре.')

    def create_setting(self, username, payload):
        if payload['marker'] == '':
            return request_gather(1, 'create_setting', 'name_chosen', 'Выберите имя для сеттинга')
        if payload['marker'] == 'name_chosen':
            context = self.get_context(username)
            setting = Setting(setting_id=username + str(int(time.time())), setting_name=payload['payload']['chosen'][0],
                              flavourtext='', owner=username)
            context.stored_id = setting.setting_id
            self.session.add(setting)
            self.session.commit()
            return request_gather(1, 'create_setting', 'flavour_chosen', 'Пришлите описание сеттинга:')
        if payload['marker'] == 'flavour_chosen':
            context = self.get_context(username)
            setting = self.session.query(Setting).filter(Setting.setting_id == context.stored_id).first()
            setting.flavourtext = payload['payload']['chosen'][0]
            self.session.commit()
            new_payload = __EMPTY_PAYLOAD__
            new_payload['marker'] = context.finish_marker
            return eval('self.' + context.on_finish)(username, new_payload)

    def game(self, username, payload):
        # context.stored_id holds module id
        # generic commands:
        # split
        if payload['marker'] == 'player':
            char = self.get_character(username)
            if char is None:
                context = self.get_context(username)
                context.finish_marker = 'player'
                context.on_finish = 'game'
                self.session.commit()
                return self.create_character(username, __EMPTY_PAYLOAD__)
            if 'chosen' not in payload['payload']:
                return request_gather(1, 'game', 'player',
                                      'Все что вы напишете будет действием персонажа. '
                                      'Если вам надо написать другим игрокам в общий чат используйте команду /chat '
                                      '(можно сразу "/chat текст сообщения".\nВыйти из игры можно по команде /leave\n'
                                      'Команды игрока:\n/me - Показывает вашего персонажа\n'
                                      '/chars - показывает список персонажей в сцене с вами\n'
                                      '/remind - Показывает описание сцены и последние три действия')
        if payload['marker'] == 'dm':
            # this is a player action or DM flavourtext
            return request_gather(1, 'game', 'player',
                                  'Все что вы напишете будет описанием сцены. '
                                  'Если вам надо написать другим игрокам в общий чат используйте команду /chat '
                                  '(можно сразу "/chat текст сообщения".\nВыйти из игры можно по команде /leave\n'
                                  'Команды мастера игры включают:\n/scene - Управление сценами\n'
                                  '/chars - Управление персонажами (PC и NPC)\n'
                                  '/request - запрашивает бросок навыка\n'
                                  '/pause - Ставит отображение лога действий на паузу и возвращает наза\n'
                                  '/turns - Включает пораундовый режим')

    def get_current_setting(self, username):
        return self.session.query(Setting).join(Module, Module.setting_id == Setting.setting_id).filter(
            Module.module_id == self.get_context(username).stored_id)

    def get_character(self, username):
        return self.session.query(Character).filter(Character.owner == username).filter(
            Character.setting_id == self.get_current_setting(username).setting_id).first()

    def create_character(self, username, payload):
        if payload['marker'] == '':  # start creation
            return request_gather(1, 'create_character', 'name', 'Введите имя персонажа (как оно будет отображаться):')
        if payload['marker'] == 'name':
            char = Character(setting_id=self.get_current_setting(username).setting_id, owner=username,
                             name=payload['payload']['chosen'][0], display_name='', known=False,
                             reference='', flavourtext='', maneuver_list='', experience=600)
            context = self.get_context(username)
            context.stored_id = char.name
            self.session.add(char)
            self.session.commit()
            return request_gather(1, 'create_character', 'display_name',
                                  'Введите имя, которое будет отображаться пока персонажа не знают '
                                  '(например, "Человек в Шляпе"):')
        if payload['marker'] == 'display_name'
            char = self.get_character(username)
            char.display_name = payload['payload']['chosen'][0]
            return request_gather(1, 'create_character', 'reference',
                                  'Пришлите ссылки на референсы персонажа (или на рисунок)\n'
                                  'Использование файлов будет сделано позже')
        if payload['marker'] == 'reference':
            char = self.get_character(username)
            char.reference = payload['payload']['chosen'][0]
            return request_gather(1, 'create_character', 'flavour',
                                  'Введите описание персонажа:')
        # add something like Character Extra Details for spellbook \ maneuver book

    # INTERFACE FUNCTIONS
    def list_games(self, username):
        dming = self.session.query(Module).join(Setting, Setting.setting_id == Module.setting_id).filter(
            Setting.owner == username).filter(~Module.finished).all()
        playing = self.session.query(Module).join(ModulePlayer,
                                                  ModulePlayer.module_id == Module.module_id).filter(
            ModulePlayer.username == username).filter(~Module.finished).all()

        return dming, playing
