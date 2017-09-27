from telepot import flavor, glance
from telepot import Bot
from telepot.loop import MessageLoop
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton, \
    InputTextMessageContent, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telepot.exception import TelegramError
from GameEngine import GameEngine
from DataBase import InterfaceContext, UserId
import datetime
import time
import json
import sys
from local import lang
locale = lang['ru']
"""
    RULES:
        
"""


class GMBot:
    def __init__(self, token, game):
        self.game_engine = game
        self.token = token
        self.core = Bot(self.token)
        MessageLoop(self.core, self.handler).run_as_thread()

    @staticmethod
    def log(text):
        print(str(datetime.datetime.now()) + ': ' + text)

    def handler(self, msg):
        # only private chat, mainly text
        # IF NOT PRIVATE AND NOT TEXT PASS
        # pass handling to EVAL of context
        # limit inbound communications
        message_flavor = flavor(msg)
        if message_flavor not in ('chat', 'callback_query'):
            return True

        # check if we're in the interface process
        username = msg['from']['username']
        context = self.get_context(username)
        if message_flavor == 'chat' and msg['text'] == '/clear':  # FIX THIS
            if context is not None:
                self.game_engine.session.delete(context)
            gcontext = self.game_engine.get_context(username)
            if gcontext is not None:
                self.game_engine.session.delete(gcontext)
            self.game_engine.session.commit()
            return True
        if context is not None:
            eval('self.' + context.context_function)(msg, context)
            return True

        # only pass text to the GameEngine
        if message_flavor == 'chat':
            chat_id = self.get_chat_id(username)
            if chat_id is None:
                self.game_engine.session.add(UserId(username=username, chat_id=msg['from']['id']))
                self.game_engine.session.commit()
            content_type, chat_type, chat_id = glance(msg, message_flavor)
            if content_type != 'text' or chat_type != 'private':
                return True
            next_action = self.game_engine.handle(username, msg['text'])
            if next_action == False:
                self.log('GameEngine handle() returned false!!')
                return True
            self.register_action(username, next_action)
        else:
            return True

    def get_context(self, username):
        return self.game_engine.session.query(InterfaceContext).filter(InterfaceContext.username == username).first()


    def register_action(self, username, action):
        # POSSIBLE CHOICE:
        # send
        # gather
        # spread
        # choose
        # structure: type, callback(optional), marker(optional), flavourtext, payload:
        type = action['type']
        if type == 'send':
            empty_return_payload = dict()
            empty_return_payload['sent'] = []
            context = InterfaceContext(username=username, context_function='send',
                                       return_payload=json.dumps(empty_return_payload),
                                       request_payload=json.dumps(action['payload']),
                                       flavourtext=action['flavourtext'],
                                       on_finish=action['callback'], marker=action['marker'])
            self.game_engine.session.add(context)
            self.game_engine.session.commit()
            self.send(None, context)
            return True
        elif type == 'gather':
            empty_return_payload = dict()
            empty_return_payload['chosen'] = []
            context = InterfaceContext(username=username, context_function='gather',
                                       return_payload=json.dumps(empty_return_payload),
                                       request_payload=json.dumps(action['payload']),
                                       flavourtext=action['flavourtext'],
                                       on_finish=action['callback'], marker=action['marker']
                                       )
            self.game_engine.session.add(context)
            self.game_engine.session.commit()
            self.gather(None, context)
            return True
        elif type == 'spread':
            return True
        elif type == 'choose':
            empty_return_payload = dict()
            empty_return_payload['msg_id'] = ''
            empty_return_payload['chosen'] = []
            context = InterfaceContext(username=username, context_function='choose',
                                       return_payload=json.dumps(empty_return_payload),
                                       request_payload=json.dumps(action['payload']), flavourtext=action['flavourtext'],
                                       on_finish=action['callback'], marker=action['marker']
                                       )
            self.game_engine.session.add(context)
            self.game_engine.session.commit()
            self.choose(None, context)
            return True
        else:
            self.log('GameEngine sent unexpected type!')
        return True

    def send(self, msg, context):
        request_payload = json.loads(context.request_payload)
        return_payload = json.loads(context.return_payload)
        finish_up = False
        if msg is None:
            for i in request_payload['userlist']:
                chat_id = self.get_chat_id(i)
                try:
                    self.core.sendMessage(chat_id, context.flavourtext)
                    return_payload['sent'].append(i)
                except TelegramError:
                    pass
            finish_up = True

        context.request_payload = json.dumps(request_payload)
        context.return_payload = json.dumps(return_payload)
        self.game_engine.session.commit()

        if finish_up:
            finish = context.on_finish
            username = context.username
            finish_payload = dict()
            finish_payload['marker'] = context.marker
            finish_payload['payload'] = return_payload
            self.game_engine.session.delete(context)
            self.game_engine.session.commit()
            if finish != '':
                next_action = eval('self.game_engine.' + finish)(username, finish_payload)
                return self.register_action(username, next_action)
            else:
                return True

    def gather(self, msg, context):
        request_payload = json.loads(context.request_payload)
        return_payload = json.loads(context.return_payload)
        finish_up = False
        markup = None
        chat_id = self.get_chat_id(context.username)
        username = context.username
        if msg is None:
            if request_payload['max_num'] == 0:
                markup = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=locale['interface']['done'], callback_data='finish')]])
            return_payload['msg_id'] = self.core.sendMessage(chat_id=chat_id, text=context.flavourtext, reply_markup=markup)['message_id']
        else:
            message_flavor = flavor(msg)
            if message_flavor == 'callback_query': #finish
                finish_up = True
            else:
                return_payload['chosen'].append(msg['text'])
                if request_payload['max_num']>0 and return_payload['chosen'].__len__()>=request_payload['max_num']:
                    finish_up = True
        #update payloads
        context.request_payload = json.dumps(request_payload)
        context.return_payload = json.dumps(return_payload)
        self.game_engine.session.commit()

        if finish_up:
            finish = context.on_finish
            finish_payload = dict()
            finish_payload['marker'] = context.marker
            finish_payload['payload'] = return_payload
            try:
                self.core.editMessageReplyMarkup((chat_id, return_payload['msg_id']), markup)
            except TelegramError:
                pass
            self.game_engine.session.delete(context)
            self.game_engine.session.commit()
            next_action = eval('self.game_engine.'+finish)(username, finish_payload)
            return self.register_action(username, next_action)


    def choose(self, msg, context):
        # request payload is       'choose_list', 'max_num'
        # restore payload
        request_payload = json.loads(context.request_payload)
        return_payload = json.loads(context.return_payload)
        finish_up = False

        button_list = [a for a in request_payload['choose_list']]
        markup = InlineKeyboardMarkup(inline_keyboard=[[]])
        if request_payload['max_num'] == 1:  # only one choice. it's on or not, easy
            # if msg is not None check against existing and finish up.
            if msg is not None:
                if msg['data'] in request_payload['choose_list']:
                    return_payload['chosen'].append(msg['data'])
                    finish_up = True
                else:
                    return True
            else:
                keyrow = 0
                for a, cnt in zip(button_list, range(1, button_list.__len__() + 1)):
                    if cnt % 5 == 0:
                        keyrow += 1
                        markup.inline_keyboard.append([])
                    markup.inline_keyboard[keyrow].append(InlineKeyboardButton(text=a, callback_data=a))
        else:
            # many buttons! MANY MANY BUTTONS!
            # check if we've got new buttons!
            if msg is not None:
                if msg['data'] in return_payload['chosen']:
                    return_payload['chosen'].pop(return_payload['chosen'].index(msg['data']))
                elif msg['data'] in request_payload['choose_list']:
                    return_payload['chosen'].append(msg['data'])
                elif msg['data'] == 'finish':
                    finish_up = True
                else:
                    return True  # not possible
            if not finish_up:
                keyrow = 0
                for a, cnt in zip(button_list, range(1, button_list.__len__() + 1)):
                    if cnt % 5 == 0:
                        keyrow += 1
                        markup.inline_keyboard.append([])
                    markup.inline_keyboard[keyrow].append(InlineKeyboardButton(
                        text=a if a not in return_payload['chosen'] else '[' + a + ']',
                        callback_data=a)
                    )
                markup.inline_keyboard.append([InlineKeyboardButton(text=locale['interface']['done'], callback_data='finish')])
        # get chat id
        chat_id = self.get_chat_id(context.username)
        # manupulate messages
        if return_payload['msg_id'] == '':
            return_payload['msg_id'] = \
            self.core.sendMessage(chat_id=chat_id, text=context.flavourtext, reply_markup=markup)['message_id']
        else:
            pretty_string = ''  # ...groan
            for ch in return_payload['chosen']:
                pretty_string += ch + ', '
            pretty_string = pretty_string[:-2]
            try:
                self.core.editMessageText((chat_id, return_payload['msg_id']),
                                          text=context.flavourtext + '\n' + locale['interface']['chosen'] + pretty_string)
                self.core.editMessageReplyMarkup((chat_id, return_payload['msg_id']), reply_markup=markup)
            except TelegramError:
                pass

        # finish up?
        if finish_up:
            payload = dict()
            payload['marker'] = context.marker
            payload['payload'] = return_payload
            username = context.username
            finish = context.on_finish
            self.game_engine.session.delete(context)
            self.game_engine.session.commit()
            # remove process context!
            next_action = eval('self.game_engine.' + finish)(username, payload)
            self.register_action(username, next_action)
        else:
            # update payloads in context
            context.return_payload = json.dumps(return_payload)
            self.game_engine.session.commit()  # TEST OUT
            return True
        return True

    def get_chat_id(self, username):
        chat_id = self.game_engine.session.query(UserId.chat_id).filter(UserId.username == username).first()
        if chat_id is not None:
            return chat_id[0]
        else:
            return None


key = sys.argv[1]
bot = GMBot(key, GameEngine())

while (True):
    time.sleep(10)
