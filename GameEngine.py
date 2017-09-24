from DataBase import GameContext, GameList, __DBNAME__
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

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
        'max_num': max_num # -1 is infinite, 1-n is finite
    }
    return request_payload
    # GAME PROCESS


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
        return eval('self.' + context.context_function)(username, context, {'marker': '', 'payload': text})
        return False

    # MENU STRUCTURE

    def main_menu(self, username, context, payload):
        if payload['marker'] == '':  # no requests were made prior to this
            text = payload['payload']  # we don't need this in the main menu, but still
            gameslist = self.list_games(username)
            chooselist = []
            for game in gameslist:
                chooselist.append('Войти в ' + game.game_name)
            chooselist.append('Создать Игру')
            return request_choose(chooselist, 1, 'main_menu', 'first_chosen', 'Вы в главном меню:')
        if payload['marker'] == 'first_chosen':
            # payload will be from CHOOSE here.
            chosen = payload['payload']['chosen'][0]
            if chosen.startswith('Войти в '):
                return {'type': 'none'} #use this to join game {'marker': '', payload: {'join_game': chosen[8:]}}
            else:
                newgame = dict()
                newgame['marker'] = 'main'
                newgame['payload'] = dict()
                return self.create_game(username, None, newgame) # create game
        return {'type': 'none'}

    def create_game(self, username, context, payload):
        if payload['marker'] == 'main': #create game process starts
            return request_gather(1, 'create_game', 'done', 'Пришлите мне название игры:')
        if payload['marker'] == 'done':
            print(payload)
            return {'type': 'none'}


    # INTERFACE FUNCTIONS
    def list_games(self, username):
        return self.session.query(GameList).filter(GameList.username == username).all()
