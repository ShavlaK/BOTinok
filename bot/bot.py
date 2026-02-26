import json
import math
import threading
import time
import os
import traceback
import warnings
import qrcode
import requests
import paramiko
import random
import plotly.graph_objs as go
import plotly.offline as pyo
import socket
import re
import sys
import logging
import string
import asyncio
import hmac
import hashlib
import pandas as pd
import py_compile

from subprocess import run
from datetime import datetime, timedelta, date
from PIL import Image, ImageDraw
from path import Path
from asyncio import sleep

import urllib.parse
from yoomoney.account.balance_details import BalanceDetails
from yoomoney.account.card import Card
from yoomoney.operation.operation import Operation
from yoomoney.exceptions import (
    InvalidToken,
    IllegalParamType,
    IllegalParamStartRecord,
    IllegalParamRecords,
    IllegalParamLabel,
    IllegalParamFromDate,
    IllegalParamTillDate,
    TechnicalError,
)
from typing import Optional, Union
from yookassa import Configuration, Payment

from data.config import *
from data.whitelist_utils import select_best_sni_domain, setup_vless_tunnel, install_xui_for_whitelist

#region Необходимые параметры скрипта
warnings.filterwarnings("ignore")
sys.setrecursionlimit(2000)
TEST = 'aleksandr' in socket.gethostname().lower()
#endregion

#region Переменные
user_dict = {}
cached_media = {}
activated_promocodes = {}
users_get_test_key = {}
last_send_time = {}
last_in_message = {}
servers_no_work = {}
xtr_pay_success_users = {}
users_send_opros, users_send_close_repiod = {}, {}
is_send_backup = False
is_delete_keys_no_in_DB = False

# Переменные для бота
bot = None
dp = None
bot_log = None
BOT_NICK = None

TARIF_1 = 149
TARIF_3 = 379
TARIF_6 = 749
TARIF_12 = 1349
PARTNER_P = 30
SUMM_VIVOD = 200
SUMM_CHANGE_PROTOCOL = 50
SUMM_CHANGE_LOCATIONS = 100
KURS_RUB = 94
KURS_RUB_AUTO = 1

KURS_XTR = 2
VERSION = '2.5'
CURRENT_IP = None
LAST_VERSION = VERSION

COUNT_PROTOCOLS = 0
#endregion

def get_logger():
    try:
        #region Настройка системы прологирования
        global LOGS_FILE, logger

        logs_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
        if not os.path.exists(logs_directory):
            os.makedirs(logs_directory)

        LOGS_FILE = f'{logs_directory}/bot_{datetime.now().strftime("%d_%m_%y")}.log'

        logging.basicConfig(filename=LOGS_FILE, level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        # Создание объекта логгера для данной функции
        logger = logging.getLogger(__name__)

        try:
            # Получение текущей даты и вычитание 5 дней
            current_date = datetime.now()
            days_to_subtract = 5
            date_threshold = current_date - timedelta(days=days_to_subtract)

            # Перебор файлов в директории logs
            for filename in os.listdir(logs_directory):
                file_path = os.path.join(logs_directory, filename)
                
                # Проверка времени создания файла
                if os.path.isfile(file_path):
                    creation_time = datetime.fromtimestamp(os.path.getctime(file_path))
                    if creation_time < date_threshold:
                        os.remove(file_path)
        except Exception as e:
            print(f'🛑Не удалось установить логгер: {e}')
        #endregion

        logger.debug(f'=====🔄Запуск бота=====')
    except Exception as e:
        logger.warning(f'🛑get_logger(): {e}')

get_logger()

#region Загрузка до компонентов
try:
    import aiohttp
    import yaml

    from aiogram import Bot, Dispatcher
    from aiogram.types import *
    from aiogram.contrib.fsm_storage.memory import MemoryStorage
    from aiogram.dispatcher.middlewares import BaseMiddleware
    from aiogram.dispatcher.handler import CancelHandler, current_handler
    from aiogram.utils.exceptions import Throttled
    from aiosqlite import connect
    from outline_bot.outline_bot import OutlineBOT
    from tinkoff_acquiring_api import TinkoffAcquiring
    if not TEST:
        from CryptomusAPI import Cryptomus
        from CryptomusAPI.enums import FiatCurrency
        from WalletPay import AsyncWalletPayAPI
    from AaioAsync import AaioAsync
    from freekassa_ru import Freekassa
except:
    logger.warning('🛑Не удалось загрузить все компоненты, устанавливаю')
    
    if not TEST:
        commands = (
            'wget https://raw.githubusercontent.com/CodenGames/VPCoden_bot/main/requirements.txt',
            'pip3.11 install -r requirements.txt',
            'pip3.11 install --upgrade pip',
            'rm -rf requirements.txt',
        )
        logger.debug('🔄Устанавливаю компоненты...')
        for index, command in enumerate(commands):
            result = run(command, shell = True, capture_output = True, encoding='cp866')
            logger.debug(f'🔄Выполнение {index + 1}/{len(commands)} команды...')
    exit(0)
#endregion

def check_varibles():
    global USTRV
    USTRV = {
        1: 'Android',
        2: 'IOS',
        3: 'Windows_MacOS',
        4: 'Router',
    }
    
    global REF_SYSTEM_AFTER_PAY
    try: REF_SYSTEM_AFTER_PAY
    except: REF_SYSTEM_AFTER_PAY = False
    
    global HOUR_CHECK
    try: HOUR_CHECK
    except: HOUR_CHECK = 7

    global URL_INSTAGRAM
    try: URL_INSTAGRAM
    except: URL_INSTAGRAM = ''

    global ID_PRODUCTS_SOFT_PAY
    try: ID_PRODUCTS_SOFT_PAY
    except: ID_PRODUCTS_SOFT_PAY = {}
    
    global IS_OTCHET
    try: IS_OTCHET
    except: IS_OTCHET = False

    global OPROS
    try: OPROS
    except: OPROS = ''

    global INLINE_MODE
    try: INLINE_MODE
    except: INLINE_MODE = False
    
    global VLESS_LIMIT_IP
    try: VLESS_LIMIT_IP
    except: VLESS_LIMIT_IP = 1
    
    global sogl_urls
    try: sogl_urls
    except: sogl_urls = []

    global VIDEO_OTZIVI
    try: VIDEO_OTZIVI
    except: VIDEO_OTZIVI = 'REVIEWS.mp4'

    global E_MAIL_MARZBAN
    try: E_MAIL_MARZBAN
    except: E_MAIL_MARZBAN = ''

    global NAME_DB
    try: NAME_DB
    except: NAME_DB = 'db.db'
    
    global SCREEN_DOWNLOAD
    try: SCREEN_DOWNLOAD
    except: SCREEN_DOWNLOAD = 'download.jpg'

    global SCREEN_UPLOAD
    try: SCREEN_UPLOAD
    except: SCREEN_UPLOAD = 'upload.jpg'

    global QR_LOGO
    try: QR_LOGO
    except: QR_LOGO = 'LOGO.png'

    global NO_ROOT_USER
    try: NO_ROOT_USER
    except: NO_ROOT_USER = 'Coden'

    global NAME_AUTHOR_BOT
    try: NAME_AUTHOR_BOT
    except: NAME_AUTHOR_BOT = NAME_BOT_CONFIG

    global X3_UI_PORT_PANEL
    try: X3_UI_PORT_PANEL
    except: X3_UI_PORT_PANEL = 28308

    global SEND_QR
    try: SEND_QR
    except: SEND_QR = True

    global AUTO_PAY_YKASSA
    try: AUTO_PAY_YKASSA
    except: AUTO_PAY_YKASSA = False

    global RECCURENT_SUMM_TINKOFF
    try: RECCURENT_SUMM_TINKOFF
    except: RECCURENT_SUMM_TINKOFF = 150

    global WEB_APP_PAY
    try: WEB_APP_PAY
    except: WEB_APP_PAY = False

    global PODPISKA_MODE
    try: PODPISKA_MODE
    except: PODPISKA_MODE = False

    global LANG_DEFAULT
    try: LANG_DEFAULT
    except: LANG_DEFAULT = 'Русский'

    global TEST_MODE
    try: TEST_MODE
    except: TEST_MODE = False

    global TOKEN_LOG_BOT
    try: TOKEN_LOG_BOT
    except: TOKEN_LOG_BOT = TOKEN_MAIN

    global SOGL_FILE
    try: SOGL_FILE
    except: SOGL_FILE = ''

    global PAY_CHANGE_PROTOCOL
    try: PAY_CHANGE_PROTOCOL
    except: PAY_CHANGE_PROTOCOL = True

    global PAY_CHANGE_LOCATIONS
    try: PAY_CHANGE_LOCATIONS
    except: PAY_CHANGE_LOCATIONS = True

    global DAYS_PARTNER_URLS_DELETE
    try: DAYS_PARTNER_URLS_DELETE
    except: DAYS_PARTNER_URLS_DELETE = 7

    global WRITE_CLIENTS_SCPEC_PROMO
    try: WRITE_CLIENTS_SCPEC_PROMO
    except: WRITE_CLIENTS_SCPEC_PROMO = False

    global OSN_SERVER_NIDERLANDS
    try: OSN_SERVER_NIDERLANDS
    except: OSN_SERVER_NIDERLANDS = False

    #region Пережитки прошло Ю.Money и Ю.Касса
    global ACCESS_TOKEN
    try: ACCESS_TOKEN
    except: ACCESS_TOKEN = ''

    global UKASSA_KEY
    try: UKASSA_KEY
    except: UKASSA_KEY = ''
    
    global UKASSA_ID
    try: UKASSA_ID
    except: UKASSA_ID = ''

    global UKASSA_EMAIL
    try: UKASSA_EMAIL
    except: UKASSA_EMAIL = ''
    #endregion

    # Протоколы - значения из config.py (по умолчанию только VLESS включён)
    global PR_VLESS
    try: PR_VLESS
    except: PR_VLESS = True

    global PR_PPTP
    try: PR_PPTP
    except: PR_PPTP = True

    global HELP_VLESS
    try: HELP_VLESS
    except: HELP_VLESS = True

    global HELP_PPTP
    try: HELP_PPTP
    except: HELP_PPTP = True

    global DEFAULT_PROTOCOL
    try: DEFAULT_PROTOCOL
    except: DEFAULT_PROTOCOL = 'vless'

    # HELP_VLESS автоматически True если PR_VLESS = True
    if PR_VLESS:
        HELP_VLESS = True

    # Подсчёт активных протоколов
    global COUNT_PROTOCOLS
    COUNT_PROTOCOLS = 0
    if PR_VLESS:
        COUNT_PROTOCOLS += 1
    if PR_PPTP:
        COUNT_PROTOCOLS += 1

    # Протокол по умолчанию - только VLESS
    global PR_DEFAULT
    PR_DEFAULT = 'vless'

check_varibles()

if INLINE_MODE:
    from data.markup_inline import *
else:
    from data.markup import *

try: from _others.secret import *
except: pass

async def get_local_path_data(title_file, path='data'):
    try:
        if path:
            title_file = f'{path}/{title_file}'
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), title_file)
    except:
        await Print_Error()
        return None

async def install_default_handler():
    global VIDEO_OTZIVI, SCREEN_DOWNLOAD, SCREEN_UPLOAD, QR_LOGO, NAME_DB, CONFIG_FILE, LANG_FILE, BOT_FILE, MARKUP_FILE, SOGL_FILE
    global LANG

    VIDEO_OTZIVI = await get_local_path_data(VIDEO_OTZIVI)
    SCREEN_DOWNLOAD = await get_local_path_data(SCREEN_DOWNLOAD)
    SCREEN_UPLOAD = await get_local_path_data(SCREEN_UPLOAD)
    QR_LOGO = await get_local_path_data(QR_LOGO)
    NAME_DB = await get_local_path_data(NAME_DB)
    CONFIG_FILE = await get_local_path_data('config.py')
    LANG_FILE = await get_local_path_data('lang.yml')
    BOT_FILE = await get_local_path_data('bot.py', path='')
    if INLINE_MODE:
        MARKUP_FILE = await get_local_path_data('markup_inline.py')
    else:
        MARKUP_FILE = await get_local_path_data('markup.py')
    if SOGL_FILE:
        SOGL_FILE = await get_local_path_data(SOGL_FILE)

    # загрузить файл lang.json и сохранить в переменную json
    try:
        with open(LANG_FILE, 'r', encoding='utf-8') as f:
            LANG = yaml.safe_load(f)
    except Exception as e:
        logger.warning('🛑Не удалось загрузить файл lang.yml')
        b = Bot(token=TOKEN_MAIN if not TEST else TOKEN_TEST, timeout=5, disable_web_page_preview=True)
        await b.send_message(MY_ID_TELEG, f'🛑Не удалось загрузить файл lang.yml\n\n⚠️Ошибка: {e}')

asyncio.run(install_default_handler())

async def Print_Error():
    try:
        text_error = 'Ошибка:\n➖➖➖➖➖➖➖➖\n' + traceback.format_exc(limit=1, chain=False)
        current_time = datetime.now().strftime('%H:%M:%S')
        print(f'{current_time}:', text_error)
        logger.warning(f'{current_time}: {text_error}')
        
        texts = (
            'requests.exceptions.ReadTimeout',
            'delete_message(',
            'Perhaps you meant https://-/',
            'CancelledError',
        )

        if 'attempt to write a readonly database' in text_error:
            await send_admins(text='🛑База данных занята другим процессом! Перезапускаем бота...')
            restartBot()
            return

        if any(text in text_error for text in texts):
            return

        # for user_id in ADMINS_IDS:
        #     try:
        #         await bot_log.send_message(user_id, text_error, parse_mode='HTML')
        #     except:
        #         pass
        await bot_log.send_message(782280769, text_error, parse_mode='HTML')
    except Exception as e:
        err = f'Ошибка при отправке ошибки: {e}'
        print(f'{current_time}:', err)
        logger.warning(err)

async def razryad(chislo):
    try:
        okr = 1
        return '{0:,}'.format(int(round(math.ceil(int(str(chislo).split('.')[0])/okr) * okr, 0))).replace(',', ' ')
    except:
        await Print_Error()

async def dney(day=0, user=None):
    try:
        for item in LANG.keys():
            lang_1 = item
            break
        if day % 10 == 1 and day != 11:
            if user:
                return user.lang.get('days_text_1')
            else:
                return LANG[lang_1]['days_text_1']
        elif 2 <= day % 10 <= 4 and (day < 10 or day > 20):
            if user:
                return user.lang.get('days_text_2_4')
            else:
                return LANG[lang_1]['days_text_2_4']
        else:
            if user:
                return user.lang.get('days_text_0_5_9')
            else:
                return LANG[lang_1]['days_text_0_5_9']
    except:
        await Print_Error()

def while_sql(func):
    async def wrapper(*args, **kwargs):
        i = 0
        while True:
            try:
                i += 1
                res = await func(*args, **kwargs)
                return res
            except Exception as e:
                logger.warning(f'Не удалось выполнить запрос (DB.{func.__name__})')
                if i > 3:
                    raise e
                await sleep(random.randint(3,10)/10)
    return wrapper

@while_sql
async def log_message(message, count=0):
    try:
        date = datetime.now().strftime("%Y_%m_%d %H:%M:%S")
        try:
            isBot = message.from_user.is_bot
        except:
            return
        chat_id = message.chat.id
        message_text = message.text
        # Добавление записи в базу данных
        insert_query = f'''
            INSERT INTO messages (date, isBot, chat_id, message_text)
            VALUES (?, ?, ?, ?)
        '''
        cursor = await DB_MESSAGES.cursor()
        await cursor.execute(insert_query, (date, isBot, chat_id, message_text))
        await DB_MESSAGES.commit()
    except Exception as e:
        logger.warning(f'🛑await log_message(message) ошибка: {e}')
        await sleep(random.randint(5,15)/10)
        if count < 5:
            logger.warning(f'🛑Не получислось добавить сообщение в await log_message(message), пробую еще раз')
            await log_message(message, count=count+1)
        else:
            await Print_Error()

async def send_message(user_id, text, reply_markup=None, no_log=False, log=False): 
    try:
        if log:
            if not no_log:
                await bot_log.send_chat_action(user_id, ChatActions.TYPING)
            message = await bot_log.send_message(chat_id=user_id, text=text, reply_markup=reply_markup, parse_mode='HTML', disable_web_page_preview=True)
            return message
        if user_id:
            if not no_log:
                await bot.send_chat_action(user_id, ChatActions.TYPING)
            message = await bot.send_message(chat_id=user_id, text=text, reply_markup=reply_markup, parse_mode='HTML', disable_web_page_preview=True)
            if not no_log:
                await log_message(message)
            return message
    except Exception as e:
        if 'privacy' in str(e):
            return await send_message(user_id, text, reply_markup=reply_markup, no_log=no_log, log=log)
        elif 'bot was blocked' in str(e) or 'user is deactivated' in str(e):
            # если пользователь заблокировал бота, то прописываем ему в БД что он заблокировал бота
            pass
        else:
            logger.warning(f'🛑Не удалось отправить сообщение {user_id}: {e}')
            if TEST:
                await Print_Error()

def restart_bot_command(command):
    time.sleep(1)
    result = run(command, shell=True, capture_output=True, encoding='cp866')
    result = result.stdout + '\n\n' + result.stderr
    logger.debug(f'🔧AdminCommand({command})\n{result}')

async def AdminCommand(user_id=None, command='', sillent=False): 
    try:
        if command == '':
            return

        if 'supervisorctl restart' in command:
            threading.Thread(target=restart_bot_command, args=(command, )).start()
            return

        result = run(command, shell = True, capture_output = True, encoding='cp866')
        result = result.stdout + '\n\n' + result.stderr
        logger.debug(f'🔧AdminCommand({user_id}, {command})\n{result}')
        if not sillent:
            if len(result) > 4096:
                for x in range(0, len(result), 4096):
                    if not user_id is None:
                        await send_message(user_id, result[x:x+4096])
            else:
                if not user_id is None:
                    await send_message(user_id, result)
    except:
        await Print_Error()

async def delete_message(chat_id, message_id): 
    try:
        if not chat_id is None:
            await bot.delete_message(chat_id=chat_id, message_id=message_id)
    except: pass

async def send_long_message(chat_id=None, text='', reply_markup=None):
    try:
        MAX_MESSAGE_LENGTH = 3900

        if chat_id is None or text == '':
            await send_admins(text=f'🛑Не передан один из параметров в функции await sendLongMessage({chat_id}, {text})')
            return

        if len(text) > MAX_MESSAGE_LENGTH:

            chunks = text.split("\n")
            current_message = ""
            for chunk in chunks:
                if len(current_message + chunk) + 1 > MAX_MESSAGE_LENGTH:
                    await send_message(chat_id, current_message, reply_markup=reply_markup)
                    current_message = ""
                current_message += chunk + "\n"
            await send_message(chat_id, current_message, reply_markup=reply_markup)
        else:
            await send_message(chat_id, text, reply_markup=reply_markup)

        return True
    except:
        return False

def get_timeount(seconds_read=10):
    return aiohttp.ClientTimeout(connect=5, sock_read=seconds_read, sock_connect=5)

async def check_server_is_work(ip, time_check=10):
    try:
        url = f'http://{ip}:43234/red'
        async with aiohttp.ClientSession(timeout=get_timeount(time_check)) as session:
            async with session.get(url):
                return True
    except Exception as e:
        logger.warning(f'🛑Не удалось проверить сервер на работоспособность {ip}: {e}')
        return False

def check_server_is_marzban(ip):
    for server in SERVERS:
        if server['ip'] == ip:
            return server['is_marzban']
    return False

def check_server_os_pptp(ip):
    for server in SERVERS:
        if server['ip'] == ip:
            return server['is_pptp']
    return False

async def connect_messages_db():
    try:
        global DB_MESSAGES
        result = await get_local_path_data('messages.db')
        DB_MESSAGES = await connect(result) # , check_same_thread=False
        cursor = await DB_MESSAGES.cursor()
        await cursor.execute("CREATE TABLE IF NOT EXISTS messages (id integer PRIMARY KEY,date text,isBot bool NOT NULL DEFAULT(0),chat_id integer NOT NULL DEFAULT(-1),message_text text NOT NULL DEFAULT('---'));")
        await DB_MESSAGES.commit()
    except:
        await Print_Error()

asyncio.run(connect_messages_db())

class UserBot:
    def __init__(self, id_Telegram):
        try:
            self.id_Telegram = id_Telegram
            self.isBan = False
            self.discount = 0
            self.news_text = ''
            self.news_photo_path = ''
            self.news_is_photo = False
            self.bill_id = ''
            self.bill_bot_key = ''
            self.isAutoCheckOn = False
            self.isAdmin = self.id_Telegram in ADMINS_IDS
            self.clients_report = []
            self.bot_status = 0
            self.autoTimerStart = datetime.now()
            self.code = ''
            self.days_code = 0
            self.paymentId = None
            self.paymentUrl = None
            self.paymentDescription = ''
            self.userForPay = 0
            self.userLastZarabotal = 0
            self.keyForChange = ''
            self.last_select_user_index = 0
            self.isProdleniye = None
            self.Protocol = PR_DEFAULT
            self.message_del_id = None
            self.summ_vivod = 0
            self.isPayChangeProtocol = False
            self.isPayChangeLocations = False
            self.locations = []
            self.servers_perenos = []
            self.keys_for_perenos = []
            self.RebillId = ''            
            self.key_url = ''
            self.cryptomus_uuid = ''
            self.payStatus = 0
            self.isPayChangeProtocol = False
            self.isPayChangeLocations = False
            self.donate_text = ''
            self.tarif_select = 1
        except Exception as e:
            logger.warning(f'Прозоишла ошибка при создании пользователя:\n{e}')

    async def set_discount_and_is_ban(self):
        try:
            self.discount = 1 - await DB.get_user_discount_by_usrls(self.id_Telegram) / 100
            self.isBan = await DB.isGetBan_by_user(self.id_Telegram)

            try:
                if not self.isBan:
                    if len([item for item in WALLETS if item['isActive']]) == 1:
                        self.PAY_WALLET = YPay()
                    else:
                        self.PAY_WALLET = None
                else:
                    self.PAY_WALLET = None
            except Exception as e:
                self.PAY_WALLET = None
        except:
            await Print_Error()

    async def set_commands(self):
        try:
            # Фильтры для новостей
            if self.isAdmin:
                self.yookassa_api_key = ''
                self.yookassa_shopId = ''
                self.yoomoney_client_id = ''
                
                self.news_select_android = True
                self.news_select_ios = True
                self.news_select_windows = True
                self.news_select_activ_keys = False
                self.news_select_test_keys = False
                self.news_select_yes_pay_no_keys = False
                self.news_select_no_pay_no_keys = False
                self.news_select_wireguard = False
                self.news_select_vless = False
                self.news_select_outline = False
                self.news_select_pptp = False
                self.users_ids = []

                commands = [
                    BotCommand('start', 'Главное меню'),
                    BotCommand('help', 'Список команд'),
                    BotCommand('buy', 'Покупка/продление доступа'),

                    BotCommand('web', 'Просмотр ключей на серверах'),
                    BotCommand('servers', 'Изменение данных серверов'),
                    BotCommand('speed_test', 'Тестирование всех серверов'),
                    BotCommand('backup', 'Выгрузка основных файлов'),
                    BotCommand('cmd', 'Выполнение команды на сервере бота'),
                    BotCommand('reload_servers', 'Перезагрузка всех серверов'),
                    BotCommand('transfer', 'Перенести всех клиентов с серверов, на перечисленные сервера'),
                    BotCommand('transfer_one', 'Перенести всех клиентов с сервера 1.1.1.1 на 2.2.2.2'),
                    BotCommand('add_server', 'Автоматическая настройка и добавление нового сервера в бота'),
                    BotCommand('add_location', 'Добавление новой локации в подписку Marzban'),
                    BotCommand('add_server_for_whitelist', 'Настройка whitelist-туннеля VLESS (местный + зарубежный сервер)'),

                    BotCommand('analytics', 'Аналитика'),
                    BotCommand('report', 'Пользователи'),
                    BotCommand('get_config', 'Загрузить файл для изменения конфигурации бота'),
                    BotCommand('get_texts_file', 'Загрузить файл с текстами, кнопками, клавиатурами...'),
                    BotCommand('urls', 'Просмотр текущих спец. ссылок'),

                    BotCommand('news', 'Написать новость'),
                    BotCommand('otvet', 'Сформировать шаблон-ответ с промокодом'),
                    BotCommand('price', 'Изменение тарифов'),
                    BotCommand('kurs', 'Изменение курса доллара'),

                    BotCommand('create', 'Создание спец. ссылки для партнера'),
                    BotCommand('newpromo', 'Массовое создание промокодов с текстом'),
                    BotCommand('partner', 'Изменить заработок партнера по умолчанию'),
                    BotCommand('summ_vivod', 'Изменить минимальную сумму для вывода'),

                    BotCommand('wallets', 'Способы оплаты'),
                    BotCommand('balance', 'Баланс Ю.Money'),
                    BotCommand('history', 'Последние 10 операций Ю.Money'),
                    BotCommand('code', 'Создание инд.промокода'),
                    BotCommand('code_view', 'Просмотр инд.промокодов'),
                    BotCommand('promo', 'Просмотр и создание промокодов'),
                ]
                if PODPISKA_MODE:
                    commands.append(BotCommand('podpiski', 'Пакеты подписок'))
                if PAY_CHANGE_PROTOCOL:
                    commands.append(BotCommand('summ_change_protocol', 'Изменить сумму для пожизненной возможности смены протокола'))
                if PAY_CHANGE_LOCATIONS:
                    commands.append(BotCommand('summ_change_locations', 'Изменить сумму подписки на 1 месяц возможности менять неограниченное кол-во раз локацию'))
                if TARIF_1 != 0:
                    commands.append(BotCommand('promo_30', 'Промокод на 30 дней'))
                if TARIF_3 != 0:
                    commands.append(BotCommand('promo_90', 'Промокод на 90 дней'))
                if TARIF_6 != 0:
                    commands.append(BotCommand('promo_180', 'Промокод на 180 дней'))
                if TARIF_12 != 0:
                    commands.append(BotCommand('promo_365', 'Промокод на 365 дней'))
            else:
                commands = [
                    BotCommand('start', self.lang.get('command_start')),
                    BotCommand('help', self.lang.get('command_help')),
                    BotCommand('buy', self.lang.get('command_buy'))
                ]
            # Устанавливаем список команд для бота
            try: await bot.set_my_commands(commands, scope=BotCommandScopeChat(self.id_Telegram))
            except: pass
            return True
        except:
            await Print_Error()

    async def set_tarifs(self):
        try:
            try:
                if self.discount:
                    pass
            except:
                self.discount = 0
            self.buttons_days = []

            if self.discount == 1:
                self.discount = 0

            but_1_month = self.lang.get('but_1_month')
            but_3_month = self.lang.get('but_3_month')
            but_6_month = self.lang.get('but_6_month')
            but_12_month = self.lang.get('but_12_month')
            
            tarifs_individual = await DB.get_tarifs_user(self.id_Telegram)
            if tarifs_individual == '':
                self.tarif_1 = int(round(TARIF_1 * self.discount, -1)) if self.discount else TARIF_1
                self.tarif_3 = int(round(TARIF_3 * self.discount, -1)) if self.discount else TARIF_3
                self.tarif_6 = int(round(TARIF_6 * self.discount, -1)) if self.discount else TARIF_6
                self.tarif_12 = int(round(TARIF_12 * self.discount, -1)) if self.discount else TARIF_12
            else:
                tarifs_individual = tarifs_individual.split('/')
                self.tarif_1 = int(tarifs_individual[0])
                self.tarif_3 = int(tarifs_individual[1])
                self.tarif_6 = int(tarifs_individual[2])
                self.tarif_12 = int(tarifs_individual[3])

            if self.lang_select != 'Русский':
                self.tarif_1_text = round(self.tarif_1 / KURS_RUB, 2)
                self.tarif_3_text = round(self.tarif_3 / KURS_RUB, 2)
                self.tarif_6_text = round(self.tarif_6 / KURS_RUB, 2)
                self.tarif_12_text = round(self.tarif_12 / KURS_RUB, 2)
            else:
                self.tarif_1_text = self.tarif_1
                self.tarif_3_text = self.tarif_3
                self.tarif_6_text = self.tarif_6
                self.tarif_12_text = self.tarif_12

            if self.tarif_1 > 0:
                self.buttons_days.append(f'{but_1_month} - {self.tarif_1_text}{self.valuta}')
            if self.tarif_3 > 0:
                self.buttons_days.append(f'{but_3_month} - {self.tarif_3_text}{self.valuta}')
            if self.tarif_6 > 0:
                self.buttons_days.append(f'{but_6_month} - {self.tarif_6_text}{self.valuta}')
            if self.tarif_12 > 0:
                self.buttons_days.append(f'{but_12_month} - {self.tarif_12_text}{self.valuta}')
            
            self.isGetTestKey = await DB.isGetTestKey_by_user(self.id_Telegram)
            self.klav_start = await fun_klav_start(self, NAME_BOT_CONFIG)
            self.klav_buy_days = await fun_klav_buy_days(self)
        except:
            await Print_Error()

    async def set_lang(self, lang):
        try:
            try:
                self.lang = LANG[lang]
                self.lang_select = lang
            except:
                # Язык по умолчанию
                try:
                    lang_df = LANG_DEFAULT
                    self.lang = LANG[lang_df]
                    self.lang_select = lang_df
                    await DB.set_user_lang(self.id_Telegram, lang_df)
                except:
                    Print_Error()

            self.valuta = self.lang['valuta']

            if not TEST_KEY:
                self.lang['but_test_key'] = ''
            if not OPLATA:
                self.lang['but_connect'] = ''
            if not REF_SYSTEM:
                self.lang['but_ref'] = ''
            if not DONATE_SYSTEM:
                self.lang['but_donate'] = ''
                self.lang['but_donaters'] = ''
            if not WHY_BOT_PAY:
                self.lang['but_why'] = ''
            if not URL_INSTAGRAM:
                self.lang['but_instagram'] = ''

            self.lang['but_desription'] = self.lang['but_desription'].format(name_config=NAME_BOT_CONFIG)

            if COUNT_PROTOCOLS < 2:
                self.lang['but_change_protocol'] = ''
            if len(SERVERS) <= 1:
                self.lang['but_change_location'] = ''
                
            self.donate = self.lang['donate']

            # Кнопки для инструкций - только VLESS
            self.buttons_podkl_vless = (self.lang.get('but_help_android_vless'), self.lang.get('but_help_ios_vless'), self.lang.get('but_help_windows_vless'), self.lang.get('but_help_macos_vless'))

            #region Проверка на возможные ошибки при изменении lang.yml
            if self.lang.get('but_how_podkl_vless') == self.lang.get('but_select_vless'):
                await send_admins(f'🛑Ошибка в lang.yml: {self.lang_select}\nbut_how_podkl_vless = but_select_vless')
            #endregion

            self.buttons_Donate = []
            for el in self.donate:
                el = self.donate[el]
                title = el[0]
                summ = el[1]
                if self.lang_select != 'Русский':
                    summ = round(summ / KURS_RUB, 2)
                self.buttons_Donate.append(f'{title}\n{summ}{self.valuta}')

            return True
        except Exception as e:
            logger.warning(f'🛑Прозоишла ошибка при установке языка:\n{e}')
            return False

class DB:
    def __init__(self, db_file):
        pass

    async def updateBase(self, db_file):
        try:
            self.conn = await connect(db_file)
            cursor = await self.conn.cursor()

            # Создать таблицу Otchet
            # Продлены - prodleny
            # Отключены - off_key
            # Увеличили_кол_во_дней - up_days
            # Сменили_протокол - change_protocol
            # Сменили_локацию - change_locations
            # Получили_пробные_ключи - get_test_keys
            # Получили_новые_ключи - get_new_keys
            # Оплатили_пожертвование - pay_donat
            # Оплатили_смену_протокола - pay_change_protocol
            # Оплатили_смену_локации - pay_change_locations
            # Взяли_обещанный_платеж - get_obesh
            # Вызвали_пожертвование - call_donat
            # Опрос_все_супер - opros_super
            # Опрос_есть_что_дополнить - opros_dop
            await cursor.execute("CREATE TABLE IF NOT EXISTS Otchet (id integer PRIMARY KEY AUTOINCREMENT NOT NULL, date text NOT NULL, prodleny integer NOT NULL DEFAULT(0), off_key integer NOT NULL DEFAULT(0), up_days integer NOT NULL DEFAULT(0), change_protocol integer NOT NULL DEFAULT(0), change_locations integer NOT NULL DEFAULT(0), get_test_keys integer NOT NULL DEFAULT(0), get_new_keys integer NOT NULL DEFAULT(0), pay_donat integer NOT NULL DEFAULT(0), pay_change_protocol integer NOT NULL DEFAULT(0), pay_change_locations integer NOT NULL DEFAULT(0), get_obesh integer NOT NULL DEFAULT(0), call_donat integer NOT NULL DEFAULT(0), opros_super integer NOT NULL DEFAULT(0), opros_dop integer NOT NULL DEFAULT(0))")
            await cursor.execute("CREATE TABLE IF NOT EXISTS Users (User_id bigint PRIMARY KEY NOT NULL,First_Name text NOT NULL DEFAULT('Имя не указано'),Last_Name text,Nick text NOT NULL DEFAULT('Ник'),Selected_id_Ustr integer NOT NULL DEFAULT(2),id_Otkuda integer NOT NULL DEFAULT(0),get_test_key bool NOT NULL DEFAULT(0),days_by_buy integer NOT NULL DEFAULT(30),Summ integer NOT NULL DEFAULT(0),Date date,Promo text NOT NULL DEFAULT(''),Date_reg date,isBan bool NOT NULL DEFAULT(0),isPayChangeProtocol bool NOT NULL DEFAULT(0),datePayChangeLocations date)")
            await self.conn.commit()

            cursor = await self.conn.cursor()
            await cursor.execute("CREATE TABLE IF NOT EXISTS Ind_promo (code text PRIMARY KEY,days integer NOT NULL DEFAULT(7),count integer NOT NULL DEFAULT(100),count_days_delete integer NOT NULL DEFAULT(14),date_create date)")
            await cursor.execute("CREATE TABLE IF NOT EXISTS Ind_promo_users (id integer PRIMARY KEY AUTOINCREMENT NOT NULL,code text NOT NULL,user_id bigint NOT NULL,date_activate date)")
            
            await cursor.execute("CREATE TABLE IF NOT EXISTS Urls (id integer PRIMARY KEY AUTOINCREMENT NOT NULL,code text NOT NULL,Discount_percentage integer NOT NULL,id_partner integer NOT NULL DEFAULT(0),percent_partner integer NOT NULL DEFAULT(0),date date)")
            await cursor.execute("CREATE TABLE IF NOT EXISTS ReportsData (id integer PRIMARY KEY AUTOINCREMENT NOT NULL,CountNewUsers integer NOT NULL DEFAULT(0),CountBuy integer NOT NULL DEFAULT(0),CountTestKey integer NOT NULL DEFAULT(0),SummDay integer NOT NULL DEFAULT(0),Date date)")
            await cursor.execute("CREATE TABLE IF NOT EXISTS Refs (id_Refer bigint NOT NULL,id_Client bigint NOT NULL,FOREIGN KEY (id_Refer) REFERENCES Users (User_id),FOREIGN KEY (id_Client) REFERENCES Users (User_id),PRIMARY KEY(id_Refer, id_Client))")
            await cursor.execute("CREATE TABLE IF NOT EXISTS QR_Keys (User_id bitint NOT NULL,BOT_Key integer NOT NULL,Date text NOT NULL,OS text NOT NULL,isAdminKey integer NOT NULL DEFAULT(0),ip_server text,CountDaysBuy integer NOT NULL DEFAULT(30),isActive bool DEFAULT(1),isChangeProtocol bool NOT NULL DEFAULT(0),DateChangeProtocol date,Payment_id text NOT NULL DEFAULT(''),isPremium bool NOT NULL DEFAULT(0),FOREIGN KEY (User_id) REFERENCES Users (User_id))")
            await cursor.execute("CREATE TABLE IF NOT EXISTS PromoCodes (Code text NOT NULL,CountDays integer NOT NULL DEFAULT(30),isActivated bool NOT NULL DEFAULT(0),User text NOT NULL DEFAULT(''),id_partner integer NOT NULL DEFAULT(0))")
            await cursor.execute("CREATE TABLE IF NOT EXISTS Donats (User_id bigint NOT NULL,Sum integer NOT NULL,FOREIGN KEY (User_id) REFERENCES Users (User_id))")
            await self.conn.commit()
        except:
            pass

    #region Индивидуальные промокоды
    async def add_individual_promo_code(self, code, days, count, count_days_delete):
        try:
            cursor = await self.conn.cursor()
            
            # проверить чтобы такого кода не было в Ind_promo_users
            res = await cursor.execute("SELECT code FROM Ind_promo_users WHERE code = ?", (code,))
            res = await res.fetchall()
            if bool(len(res)):
                return False

            await cursor.execute("INSERT INTO Ind_promo (code, days, count, count_days_delete, date_create) VALUES (?, ?, ?, ?, ?)", (code, days, count, count_days_delete, date.today()))
            await self.conn.commit()
            return True
        except Exception as e:
            logger.warning(f'🛑Не удалось добавить индивидуальный промокод {code}: {e}')
            return False

    @while_sql
    async def delete_individual_promo_code(self, code):
        cursor = await self.conn.cursor()
        await cursor.execute("DELETE FROM Ind_promo WHERE code = ?", (code,))
        await self.conn.commit()
        logger.debug(f'✅Удален индивидуальный промокод {code}')

    @while_sql
    async def exists_individual_promo_code(self, code):
        cursor = await self.conn.cursor()
        result = await cursor.execute("SELECT code FROM Ind_promo WHERE code = ?", (code,))
        result = await result.fetchall()
        return bool(len(result))

    @while_sql
    async def get_all_individual_promo_codes(self):
        cursor = await self.conn.cursor()
        result = await cursor.execute("SELECT code, days, count, count_days_delete, date_create, (SELECT COUNT(*) FROM Ind_promo_users WHERE code = Ind_promo.code) as count_activate FROM Ind_promo")
        return await result.fetchall()

    @while_sql
    async def add_activate_individual_promo_code(self, code, user_id):
        result = await self.get_activate_individual_promo_code(code, user_id)
        if result:
            return False

        cursor = await self.conn.cursor()
        await cursor.execute("INSERT INTO Ind_promo_users (code, user_id, date_activate) VALUES (?, ?, ?)", (code, user_id, date.today()))
        await self.conn.commit()
        
        cursor = await self.conn.cursor()
        result = await cursor.execute("SELECT count FROM Ind_promo WHERE code = ?", (code,))
        result = await result.fetchone()
        count = result[0]
        
        result = await cursor.execute("SELECT COUNT(*) FROM Ind_promo_users WHERE code = ?", (code,))
        result = await result.fetchone()

        count_activate = result[0]
        if count_activate >= count:
            logger.debug(f'🔄У промокода {code} закончилось кол-во активаций, удаляем...')
            await self.delete_individual_promo_code(code)

        return True

    @while_sql
    async def get_activate_individual_promo_code(self, code, user_id):
        cursor = await self.conn.cursor()
        result = await cursor.execute("SELECT code, user_id FROM Ind_promo_users WHERE code = ? AND user_id = ?", (code, user_id))
        result = await result.fetchall()
        return bool(len(result))

    #endregion

    #region Численый отчет каждый день
    @while_sql
    async def add_otchet(self, name, count=1):
        date = datetime.now().strftime('%d.%m.%y')
        cursor = await self.conn.cursor()
        # Если не создана строка с такой датой, то создаем
        result = await cursor.execute("SELECT * FROM Otchet WHERE date = ?", (date,))
        result = await result.fetchall()
        if not len(result):
            await cursor.execute("INSERT INTO Otchet (date) VALUES (?)", (date,))
            await self.conn.commit()
            
        # Добавляем к нужному столбцу
        await cursor.execute(f"UPDATE Otchet SET {name} = {name} + ? WHERE date = ?", (count, date,))
        await self.conn.commit()
        return True

    @while_sql
    async def get_otchet_yesterday(self):
        date = (datetime.now() - timedelta(days=1)).strftime('%d.%m.%y')
        cursor = await self.conn.cursor()
        result = await cursor.execute("SELECT prodleny, off_key, up_days, change_protocol, change_locations, get_test_keys, get_new_keys, pay_donat, pay_change_protocol, pay_change_locations, get_obesh, call_donat, opros_super, opros_dop FROM Otchet WHERE date = ?", (date,))
        return await result.fetchone()
    #endregion

    #region Пользователи
    @while_sql
    async def set_send_opros(self, user_id=None):
        cursor = await self.conn.cursor()
        await cursor.execute("UPDATE Users SET is_send_opros = ? WHERE User_id = ?", (True, user_id,))
        await self.conn.commit()
        return True

    @while_sql
    async def get_users_is_send_opros(self):
        cursor = await self.conn.cursor()
        result = await cursor.execute("SELECT User_id FROM Users WHERE is_send_opros = ?", (True,))
        result = await result.fetchall()
        data = {i[0] for i in result}
        return data

    @while_sql
    async def exists_user(self, user_id):
        cursor = await self.conn.cursor()
        result = await cursor.execute("SELECT User_id FROM Users WHERE User_id = ?", (user_id,))
        result = await result.fetchall()
        return bool(len(result))

    @while_sql
    async def set_user_lang(self, user_id=None, lang=''):
        try:
            cursor = await self.conn.cursor()
            await cursor.execute("UPDATE Users SET Lang = ? WHERE User_id = ?", (lang,user_id,))
            return await self.conn.commit()
        except:
            logger.warning(f'🛑Не удалось установить язык пользователю user_id {user_id}: {lang}')
    
    @while_sql
    async def get_user_lang(self, user_id=None):
        try:
            cursor = await self.conn.cursor()
            await cursor.execute("SELECT Lang FROM Users WHERE User_id = ?", (user_id,))
            result = await cursor.fetchone()
            result = result[0]
            if result == '':
                result = LANG_DEFAULT
                try: await self.set_user_lang(user_id, result)
                except: pass
            return result
        except:
            lang_df = LANG_DEFAULT
            try:
                await self.set_user_lang(user_id, lang_df)
            except:
                pass
            return lang_df

    @while_sql
    async def delete_user_and_configs(self, user_id=None):
        cursor = await self.conn.cursor()
        await cursor.execute("DELETE FROM Users WHERE User_id = ?", (user_id,))
        await cursor.execute("DELETE FROM QR_Keys WHERE User_id = ?", (user_id,))
        await cursor.execute("DELETE FROM Zaprosi WHERE User_id = ?", (user_id,))
        await cursor.execute("DELETE FROM Operations WHERE user_id = ?", (user_id,))
        await cursor.execute("DELETE FROM Donats WHERE User_id = ?", (user_id,))
        await self.conn.commit()
        return True

    @while_sql
    async def get_all_users_id(self):
        cursor = await self.conn.cursor()
        result = await cursor.execute("SELECT User_id FROM Users")
        return await result.fetchall()

    @while_sql
    async def change_ban_user(self, user_id=None, isBan=True):
        cursor = await self.conn.cursor()
        await cursor.execute("UPDATE Users SET isBan = ? WHERE User_id = ?", (isBan, user_id,))
        await self.conn.commit()
        return True

    @while_sql
    async def isGetBan_by_user(self, user_id=None):
        cursor = await self.conn.cursor()
        result = await cursor.execute("SELECT isBan FROM Users WHERE User_id = ?", (user_id,))
        result = await result.fetchone()
        try:
            result = result[0]
        except:
            result = False
        return bool(result)

    @while_sql
    async def get_users_id_clients_no_keys(self):
        cursor = await self.conn.cursor()
        result = await cursor.execute("SELECT u.User_id FROM Users u LEFT JOIN QR_Keys qr ON u.User_id = qr.User_id WHERE qr.User_id IS NULL")
        return await result.fetchall()

    @while_sql
    async def add_user(self, user_id=None, nick='', first_name='', last_name=''):
        if first_name == '' or first_name is None:
            first_name = 'Имя'
        if nick == '' or nick is None:
            nick = 'None'

        date = datetime.now()
        cursor = await self.conn.cursor()

        if str(last_name) != 'None':
            await cursor.execute("INSERT INTO Users (User_id, First_Name, Last_Name, Nick, Date_reg) VALUES (?, ?, ?, ?, ?)", 
                (user_id,
                first_name,
                last_name,
                nick,
                date,))
        else:
            await cursor.execute("INSERT INTO Users (User_id, First_Name, Nick, Date_reg) VALUES (?, ?, ?, ?)", 
                (user_id,
                first_name,
                nick,
                date,))

        await self.addReportsData('CountNewUsers', 1)

        return await self.conn.commit()

    @while_sql
    async def get_user_nick_and_ustrv(self, user_id=None):
        user_id = int(user_id)
        cursor = await self.conn.cursor()
        result = await cursor.execute("SELECT Nick, Selected_id_Ustr, First_Name, Summ, Date, Date_reg, Promo FROM Users WHERE User_id = ?", (user_id,))
        result = await result.fetchone()
        return result

    @while_sql
    async def set_user_date_obesh(self, user_id=None):
        date = datetime.now()

        cursor = await self.conn.cursor()
        await cursor.execute("UPDATE Users SET Date = ? WHERE User_id = ?", (date, user_id,))
        return await self.conn.commit()

    @while_sql
    async def set_user_date_reg(self, user_id=None):
        date = datetime.now()

        cursor = await self.conn.cursor()
        await cursor.execute("UPDATE Users SET Date_reg = ? WHERE User_id = ?",
            (date, user_id,))
        return await self.conn.commit()

    @while_sql
    async def get_user_keys(self, user_id=None):
        try:
            cursor = await self.conn.cursor()
            if user_id:
                where = ' WHERE qr.User_id = ?'
                arg = (user_id,)
            else:
                where = ''
                arg = ()

            result = await cursor.execute(f"SELECT qr.BOT_Key, qr.OS, qr.isAdminKey, qr.Date, qr.CountDaysBuy, qr.ip_server, qr.isActive, qr.Protocol, sr.Location, qr.Keys_Data, qr.User_id, qr.Podpiska, qr.Payment_id FROM QR_Keys qr JOIN Servers sr ON ip=ip_server{where} ORDER BY Date DESC", arg)
            return await result.fetchall()
        except:
            await Print_Error()

    @while_sql
    async def exists_ref(self, id_refer=None, id_client=None):
        if id_client == id_refer:
            return True

        cursor = await self.conn.cursor()
        result = await cursor.execute(
            "SELECT id_Refer, id_Client FROM Refs WHERE (id_Refer = ? AND id_Client = ?) or (id_Refer = ? AND id_Client = ?)", 
            (id_refer, id_client, id_client, id_refer,)
        )
        result = await result.fetchall()
        return bool(len(result))

    @while_sql
    async def get_refs_user(self, user_id=None):
        cursor = await self.conn.cursor()
        result = await cursor.execute("SELECT id_Refer FROM Refs WHERE id_Refer = ?", (user_id,))
        result = await result.fetchall()
        return len(result)

    @while_sql
    async def isGetTestKey_by_user(self, id_chat=None):
        cursor = await self.conn.cursor()
        result = await cursor.execute("SELECT get_test_key FROM Users WHERE User_id = ?", (id_chat,))
        result = await result.fetchone()
        if result is None:
            return False
        else:
            result = result[0]
            return bool(int(result))

    @while_sql
    async def set_user_get_test_key(self, user_id=None):
        cursor = await self.conn.cursor()
        await cursor.execute("UPDATE Users SET get_test_key = ? WHERE User_id = ?", (True, user_id,))
        await self.conn.commit()
        await self.addReportsData('CountTestKey', 1)
        return 

    @while_sql
    async def add_ref(self, id_refer=None, id_client=None):
        res = await self.exists_ref(id_client, id_refer)
        if res:
            return

        cursor = await self.conn.cursor()
        await cursor.execute("INSERT INTO Refs (id_Refer, id_Client) VALUES (?, ?)", (id_refer, id_client,))
        return await self.conn.commit()

    @while_sql
    async def get_all_users_report(self, text='', is_search=False):
        cursor = await self.conn.cursor()
        if is_search:
            result = await cursor.execute("SELECT User_id, Nick, First_Name, Last_Name, id_Otkuda, Summ, isBan, Lang, tarifs FROM Users WHERE User_id = ? OR Nick = ? OR First_Name = ?", (text,text,text,))
        else:
            result = await cursor.execute("SELECT User_id, Nick, First_Name, Last_Name, id_Otkuda, Summ, isBan, Lang, tarifs FROM Users")
        return await result.fetchall()

    @while_sql
    async def get_summ_by_otkuda(self, id_otkuda):
        cursor = await self.conn.cursor()
        result = await cursor.execute("SELECT SUM(Summ) FROM Users WHERE id_Otkuda = ?", (id_otkuda,))
        result = await result.fetchone()
        if len(result) > 0 and not result[0] is None:
            result = result[0]
        else:
            result = 0
        return result

    @while_sql
    async def set_user_otkuda(self, user_id=None, id_otkuda=None):
        cursor = await self.conn.cursor()
        await cursor.execute("UPDATE Users SET id_Otkuda = ? WHERE User_id = ?", (id_otkuda, user_id,))
        return await self.conn.commit()

    @while_sql
    async def set_user_ref(self, user_id=None, id_ref=None):
        cursor = await self.conn.cursor()
        await cursor.execute("UPDATE Users SET id_ref = ? WHERE User_id = ?", (id_ref, user_id,))
        return await self.conn.commit()

    @while_sql
    async def get_user_discount_by_usrls(self, user_id=None):
        cursor = await self.conn.cursor()
        result = await cursor.execute("SELECT Promo, Summ FROM Users WHERE User_id = ?", (user_id,))
        result = await result.fetchone()
        if not result is None and len(result) > 0:
            if result[1] == 0:
                result = result[0] if result[0] != '' else 0
            else:
                result = 0
        else:
            result = 0

        if str(result) != '0' and str(result) != '':
            result = await cursor.execute("SELECT Discount_percentage FROM Urls WHERE code = ?", (result,))
            result = await result.fetchone()
            if not result is None and len(result) > 0:
                result = result[0]

        if result is None:
            result = 0

        return result

    @while_sql
    async def set_user_ustrv(self, user_id=None, id_ustrv=None):
        cursor = await self.conn.cursor()
        await cursor.execute("UPDATE Users SET Selected_id_Ustr = ? WHERE User_id = ?", (id_ustrv, user_id,))
        return await self.conn.commit()

    @while_sql
    async def set_user_days_by_buy(self, user_id=None, days=None):
        cursor = await self.conn.cursor()
        await cursor.execute("UPDATE Users SET days_by_buy = ? WHERE User_id = ?", (days, user_id,))
        return await self.conn.commit()

    @while_sql
    async def get_count_keys_by_ip(self, ip=None):
        cursor = await self.conn.cursor()
        query = "SELECT BOT_Key FROM QR_Keys"
        result = await cursor.execute(query + " WHERE ip_server = ?", (ip,))
        result = await result.fetchall()
        if not result is None:
            return len(result)
        else:
            return 0

    @while_sql
    async def get_count_users_and_keys(self):
        cursor = await self.conn.cursor()
        count_keys = await cursor.execute("SELECT * FROM QR_Keys")
        count_keys = await count_keys.fetchall()
        count_keys = len(count_keys)
        count_users = await cursor.execute("SELECT * FROM Users")
        count_users = await count_users.fetchall()
        count_users = len(count_users)

        return (count_users, count_keys)

    @while_sql
    async def get_user_days_by_buy(self, user_id=None):
        cursor = await self.conn.cursor()
        query = "SELECT days_by_buy FROM Users"
        result = await cursor.execute(query + " WHERE User_id = ?", (user_id,))
        result = await result.fetchone()
        if not result is None and len(result) > 0:
            return result[0]
        else:
            return 31

    @while_sql
    async def get_user_by_id_ref(self, user_id=None):
        cursor = await self.conn.cursor()
        result = await cursor.execute("SELECT id_ref FROM Users WHERE User_id = ?", (user_id,))
        result = await result.fetchone()
        if not result is None and len(result) > 0:
            return result[0]
        else:
            return -1

    @while_sql
    async def update_user_nick(self, user_id=None, nick=None, name=None):
        cursor = await self.conn.cursor()
        if nick == '' or nick is None:
            nick = 'None'
        if name == '' or name is None:
            name = 'Добрый человек'

        await cursor.execute("UPDATE Users SET Nick = ?, First_Name = ? WHERE User_id = ?", (nick, name, user_id,))
        return await self.conn.commit()

    @while_sql
    async def set_user_Promo(self, user_id=None, code=None):
        cursor = await self.conn.cursor()
        result = await cursor.execute("SELECT Promo FROM Users WHERE User_id = ?", (user_id,))
        result = await result.fetchone()
        result = result[0]
        if result != '':
            return (False, 0)

        await cursor.execute("UPDATE Users SET Promo = ? WHERE User_id = ?", (code, user_id,))
        await self.conn.commit()
        result = await self.get_user_discount_by_usrls(user_id)
        return (True, result)

    @while_sql
    async def add_operation(self, type='', user_id=0, summ=0, days=0, promo_code='', bill_id='', decription=''):
        cursor = await self.conn.cursor()
        date = datetime.now()
        await cursor.execute("INSERT INTO Operations (type, user_id, summ, days, promo_code, bill_id, Description, Date) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (type, user_id, summ, days, promo_code, bill_id, decription, date, ))
        return await self.conn.commit()
    
    @while_sql
    async def set_tarifs_user(self, user_id=None, tarifs=None):
        cursor = await self.conn.cursor()
        await cursor.execute("UPDATE Users SET tarifs = ? WHERE User_id = ?", (tarifs, user_id,))
        await self.conn.commit()
        
        user = await user_get(user_id)
        await user.set_tarifs()
        return True
    
    @while_sql
    async def get_tarifs_user(self, user_id=None):
        cursor = await self.conn.cursor()
        result = await cursor.execute("SELECT tarifs FROM Users WHERE User_id = ?", (user_id,))
        result = await result.fetchone()
        if result and len(result) > 0:
            return result[0]
        else:
            return ''
    #endregion

    #region Ключи
    @while_sql
    async def set_date_off_key(self, bot_key, date_off):
        cursor = await self.conn.cursor()
        await cursor.execute("UPDATE QR_Keys SET date_off_client = ? WHERE BOT_Key = ?", (date_off, bot_key,))
        return await self.conn.commit()

    @while_sql
    async def get_date_off_key(self, bot_key):
        cursor = await self.conn.cursor()
        result = await cursor.execute("SELECT date_off_client FROM QR_Keys WHERE BOT_Key = ?", (bot_key,))
        result = await result.fetchone()
        if result and len(result) > 0:
            return result[0]

    @while_sql
    async def set_payment_id_by_key(self, key=None, payment_id=None):
        cursor = await self.conn.cursor()
        await cursor.execute("UPDATE QR_Keys SET Payment_id = ? WHERE BOT_Key = ?", (payment_id, key,))
        return await self.conn.commit()

    @while_sql
    async def exists_key(self, key):
        cursor = await self.conn.cursor()
        result = await cursor.execute("SELECT BOT_Key FROM QR_Keys WHERE BOT_Key = ?", (key,))
        result = await result.fetchall()
        return bool(len(result))

    @while_sql
    async def add_day_qr_key_ref(self, user_id=None, days=None):
        res = await self.get_qr_key_All(user_id) #BOT_Key, Date, User_id, isAdminKey, CountDaysBuy, ip_server, isActive
        if not res is None and bool(len(res)):
            # Если ключ есть у пользователя
            # Добавляем N дней и возвращаем True
            res = res[-1]
            bot_key = res[0] # coden_333_3213
            ip_server = res[5]
            isActive = bool(res[6])
            protocol = res[7]
            countDays = res[4]
            date = datetime.now().strftime("%Y_%m_%d")

            cursor = await self.conn.cursor()
            if isActive:
                await cursor.execute("UPDATE QR_Keys SET CountDaysBuy = CountDaysBuy + ?, isActive = ? WHERE BOT_Key = ?", (days, True, bot_key,))
            else:
                await cursor.execute("UPDATE QR_Keys SET Date = ?, CountDaysBuy = CountDaysBuy + ?, isActive = ? WHERE BOT_Key = ?", (date, days, True, bot_key,))
            await self.conn.commit()

            await change_days_vless(bot_key, countDays + days)

            return (True, bot_key, ip_server, protocol)
        else:
            # Если ключа у пользователя нет, то возвращаем False
            return (False, '', '', PR_DEFAULT)

    @while_sql
    async def add_day_qr_key_in_DB(self, user_id=None, days=None, bot_key=None, summ=0, bill_id='', is_on_key=False):
        res = await self.get_qr_key_All(user_id)

        if res and len(res) > 0:
            for key in res:
                name_qr = key[0]
                if name_qr == bot_key:
                    date = datetime.now().strftime("%Y_%m_%d")
                    cursor = await self.conn.cursor()
                    isActive = bool(key[6])
                    countDaysBuy = key[4]

                    if isActive or is_on_key:
                        await cursor.execute("UPDATE QR_Keys SET CountDaysBuy = CountDaysBuy + ?, isActive = ? WHERE BOT_Key = ?", (days, True, bot_key,))
                    else:
                        await cursor.execute("UPDATE QR_Keys SET Date = ?, CountDaysBuy = ?, isActive = ? WHERE BOT_Key = ?", (date, days, True, bot_key,))
                    await self.conn.commit()

                    if not (summ == 0 and bill_id == ''):
                        user = await user_get(user_id)
                        await self.add_operation('prodl', user_id, summ, days, '', bill_id, user.paymentDescription)

                    await change_days_vless(bot_key, countDaysBuy + days)
                    return True

    @while_sql
    async def set_day_qr_key_in_DB(self, bot_key=None, count=0):
        cursor = await self.conn.cursor()
        await cursor.execute("UPDATE QR_Keys SET CountDaysBuy = ?, isActive = ? WHERE BOT_Key = ?", (count, True, bot_key,))
        await self.conn.commit()
        return True

    @while_sql
    async def set_summ_qr_key_in_DB(self, bot_key=None, summ=0):
        cursor = await self.conn.cursor()
        await cursor.execute("UPDATE QR_Keys SET summ = ? WHERE BOT_Key = ?", (summ, bot_key,))
        await self.conn.commit()
        return True

    @while_sql
    async def On_Off_qr_key(self, isOn=False, name_bot_key=None):
        cursor = await self.conn.cursor()
        await cursor.execute("UPDATE QR_Keys SET isActive = ? WHERE BOT_Key = ?", (isOn, name_bot_key,))
        return await self.conn.commit()

    @while_sql
    async def update_qr_keys_add_1_day(self, user_id=None):
        cursor = await self.conn.cursor()
        await cursor.execute("UPDATE QR_Keys SET isActive = ?, CountDaysBuy = CountDaysBuy + 1 WHERE User_id = ?", (True, user_id,))
        return await self.conn.commit()

    @while_sql
    async def get_qr_key_All(self, user_id=None):
        cursor = await self.conn.cursor()
        query = "SELECT BOT_Key, Date, User_id, isAdminKey, CountDaysBuy, ip_server, isActive, Protocol, isChangeProtocol, DateChangeProtocol, Payment_id, RebillId, Podpiska, date_time, summ FROM QR_Keys"
        if user_id is None:
            result = await cursor.execute(query)
        else:
            result = await cursor.execute(query + " WHERE User_id = ?", (user_id,))
        return await result.fetchall()
    
    @while_sql
    async def get_qr_key_for_check_keys(self):
        cursor = await self.conn.cursor()
        result = await cursor.execute("SELECT BOT_Key, Protocol, ip_server, User_id, Date, CountDaysBuy, isActive FROM QR_Keys")
        return await result.fetchall()

    @while_sql
    async def get_key_by_name(self, key_name=None):
        cursor = await self.conn.cursor()
        query = "SELECT BOT_Key, Date, User_id, isAdminKey, CountDaysBuy, ip_server, isActive, Protocol, isChangeProtocol, DateChangeProtocol, Payment_id, RebillId, Podpiska FROM QR_Keys"
        result = await cursor.execute(query + " WHERE BOT_Key = ?", (key_name,))
        return await result.fetchone()

    @while_sql
    async def get_keys_name_by_ip_server(self, ip_server=None):
        cursor = await self.conn.cursor()
        result = await cursor.execute("SELECT BOT_Key, Protocol FROM QR_Keys WHERE ip_server = ?", (ip_server,))
        return await result.fetchall()

    @while_sql
    async def get_ip_server_by_key_name(self, key_name=None):
        cursor = await self.conn.cursor()
        result = await cursor.execute("SELECT ip_server FROM QR_Keys WHERE BOT_Key = ?", (key_name,))
        result = await result.fetchone()
        if not result is None and len(result) > 0:
            return result[0]
        else:
            return False

    @while_sql
    async def get_Protocol_by_key_name(self, key_name=None):
        cursor = await self.conn.cursor()
        result = await cursor.execute("SELECT Protocol FROM QR_Keys WHERE BOT_Key = ?", (key_name,))
        result = await result.fetchone()
        try:
            return result[0]
        except:
            return PR_DEFAULT

    @while_sql
    async def add_qr_key(self, user_id=None, bot_key=None, date=None, os=None, isAdminKey=0, ip=None, days=None, summ=0, bill_id='', protocol=PR_DEFAULT, isChangeProtocol=False, keys_data='', podpiska=-1):
        cursor = await self.conn.cursor()
        date_time = datetime.now()
        try:
            await cursor.execute(
                "INSERT INTO QR_Keys (User_id, BOT_Key, Date, OS, isAdminKey, ip_server, CountDaysBuy, Protocol, isChangeProtocol, Keys_Data, Podpiska, date_time, summ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (user_id,bot_key,date,os,isAdminKey,ip,days,protocol,isChangeProtocol,keys_data,podpiska, date_time,summ)
            )
        except Exception as e:
            await send_admins(None, f'🛑Ошибка в add_qr_key({(user_id, bot_key, date, os, isAdminKey, ip, days, summ, bill_id, protocol, isChangeProtocol, podpiska)})', f'⚠️Ошибка:\n{e}')
        await self.conn.commit()

        if not (summ == 0 and bill_id == ''):
            user = await user_get(user_id)
            await self.add_operation('buy', user_id, summ, days, '', bill_id, user.paymentDescription)
        return

    @while_sql
    async def get_summ_next_pay(self, bot_key=None):
        cursor = await self.conn.cursor()
        result = await cursor.execute("SELECT summ FROM QR_Keys WHERE BOT_Key = ?", (bot_key,))
        result = await result.fetchone()
        if result and len(result) > 0:
            return result[0]
        else:
            return 0

    @while_sql
    async def delete_qr_key(self, BOT_Key=None):
        cursor = await self.conn.cursor()
        await cursor.execute("DELETE FROM QR_Keys WHERE BOT_Key = ?", (BOT_Key,))
        await self.conn.commit()
        return True

    @while_sql
    async def set_keys_data_for_key(self, bot_key=None, keys_data=''):
        cursor = await self.conn.cursor()
        await cursor.execute("UPDATE QR_Keys SET Keys_Data = ? WHERE BOT_Key = ?", (keys_data, bot_key,))
        await self.conn.commit()
        return True

    #endregion

    #region Донаты
    @while_sql
    async def add_donate(self, user_id=None, sum=None):
        cursor = await self.conn.cursor()
        await cursor.execute("INSERT INTO Donats (User_id, Sum) VALUES (?, ?)", (user_id, sum,))
        return await self.conn.commit()

    @while_sql
    async def get_donates(self):
        cursor = await self.conn.cursor()
        result = await cursor.execute("SELECT Nick, SUM(sum) summm FROM Donats d JOIN Users u WHERE d.User_id = u.User_id GROUP BY Nick ORDER BY summm desc")
        return await result.fetchall()
    #endregion

    #region Специальные ссылки
    @while_sql
    async def addUserSumm(self, user_id=None, summ=0):
        cursor = await self.conn.cursor()
        await cursor.execute(f"SELECT Summ FROM Users WHERE User_id = ?", (user_id,)) 
        row = await cursor.fetchone()

        summ = row[0] + summ
        await cursor.execute(f"UPDATE Users SET Summ = ? WHERE User_id = ?", (summ, user_id))

        # сохраняем изменения в базе данных
        await self.conn.commit()

    @while_sql
    async def get_parter_pay(self, id_partner=None):
        cursor = await self.conn.cursor()
        result = await cursor.execute("SELECT id, date, summ, comment, Dolg FROM Partner_pay WHERE id_partner = ?", (id_partner,))
        return await result.fetchall()

    @while_sql
    async def add_parter_pay(self, id_partner=None, summ=None, comment=None, Dolg=None):
        if Dolg < 0:
            Dolg = 0
        
        cursor = await self.conn.cursor()
        date = datetime.now()
        await cursor.execute("INSERT INTO Partner_pay (id_partner, date, summ, comment, Dolg) VALUES (?, ?, ?, ?, ?)", (id_partner, date, summ, comment, Dolg,))
        return await self.conn.commit()

    @while_sql
    async def update_spec_url_Discount_percentage(self, id_partner, percent_price):
        cursor = await self.conn.cursor()
        await cursor.execute("UPDATE Urls SET Discount_percentage = ? WHERE id_partner = ?", (percent_price, id_partner,))
        return await self.conn.commit()

    @while_sql
    async def update_spec_url_percent_partner(self, id_partner, percent_partner):
        cursor = await self.conn.cursor()
        await cursor.execute("UPDATE Urls SET percent_partner = ? WHERE id_partner = ?", (percent_partner, id_partner,))
        return await self.conn.commit()

    @while_sql
    async def update_spec_url_name(self, id_partner, new_name):
        cursor = await self.conn.cursor()

        result = await cursor.execute("SELECT id FROM Urls WHERE code = ?", (new_name,))
        result = await result.fetchall()
        if bool(len(result)):
            return False
        else:
            old_name = await cursor.execute("SELECT code FROM Urls WHERE id_partner = ?", (id_partner,))
            old_name = await old_name.fetchone()
            old_name = old_name[0]

            await cursor.execute("UPDATE Urls SET code = ? WHERE id_partner = ?", (new_name, id_partner,))
            await cursor.execute("UPDATE Users SET Promo = ? WHERE Promo = ?", (new_name, old_name,))
            await self.conn.commit()
            return True

    @while_sql
    async def delete_spec_urls(self, Promo=None, id_partner=None):
        cursor = await self.conn.cursor()
        # удалить у всех пользователей этот промокод
        await cursor.execute("DELETE FROM Users WHERE Promo = ?", (Promo,))
        # удалить выплаты
        await cursor.execute("DELETE FROM Partner_pay WHERE id_partner = ?", (id_partner,))
        # удалить саму ссылку в Urls
        await cursor.execute("DELETE FROM Urls WHERE code = ?", (Promo,))
        await self.conn.commit()
        return True
    
    @while_sql
    async def add_spec_urls(self, code=None, percent=None, id_partner=None, percent_partner=None):
        cursor = await self.conn.cursor()
        result = await cursor.execute("SELECT code FROM Urls WHERE code = ?", (code,))
        result = await result.fetchall()
        if bool(len(result)):
            return False

        result = await cursor.execute("SELECT id_partner FROM Urls WHERE id_partner = ?", (id_partner,))
        result = await result.fetchall()
        if bool(len(result)):
            return False

        date = datetime.now()

        await cursor.execute("INSERT INTO Urls (code, Discount_percentage, id_partner, percent_partner, date) VALUES (?, ?, ?, ?, ?)", (code, percent, id_partner, percent_partner, date,))
        await self.conn.commit()
        return True
    
    @while_sql
    async def set_payment_id_qr_key_in_DB(self, bot_key=None, payment_id='', RebillId=''):
        cursor = await self.conn.cursor()
        await cursor.execute("UPDATE QR_Keys SET Payment_id = ?, RebillId = ? WHERE BOT_Key = ?", (payment_id, RebillId, bot_key,))
        await self.conn.commit()
        return True
        
    # RebillId
    #endregion

    #region Промокоды
    @while_sql
    async def get_stat_by_code(self, code=None):
        cursor = await self.conn.cursor()

        result_count = await cursor.execute("SELECT Promo FROM Users WHERE Promo=?", (code,))
        result_count = await result_count.fetchall()
        if result_count:
            count = len(result_count)
        else:
            count = 0

        result_summ = await cursor.execute("SELECT SUM(Summ) FROM Users WHERE Promo=? GROUP BY Promo", (code,))
        result_summ = await result_summ.fetchone()
        if result_summ and len(result_summ) > 0:
            summ = result_summ[0]
        else:
            summ = 0

        result_count = await cursor.execute("SELECT Promo FROM Users WHERE Promo=? and get_test_key is true", (code,))
        result_count = await result_count.fetchall()
        if result_count:
            count_probniy = len(result_count)
        else:
            count_probniy = 0

        return count, summ, count_probniy

    @while_sql
    async def get_stats_promoses(self, user_id=None, code=None):
        cursor = await self.conn.cursor()
        dop_usl = ''
        values = ()
        if user_id:
            dop_usl = ' WHERE id_partner = ?'
            values = (user_id,)
        elif code:
            dop_usl = ' WHERE code = ?'
            values = (code,)
        result = await cursor.execute(f"SELECT code, Discount_percentage, id_partner, percent_partner, date, id FROM Urls{dop_usl}", values)
        result = await result.fetchall()
        try:
            if result and len(result) > 0 and result[0]:
                temp_m = []
                for item in result:
                    count, summ, count_probniy = await self.get_stat_by_code(item[0])
                    temp_m.append((item[0], item[1], item[2], item[3], count, summ, count_probniy, item[4], item[5]))
                result = temp_m
                result = sorted(result, key=lambda item: (item[4]), reverse=True)
            else:
                result = []
        except:
            await Print_Error()
        return result
    
    @while_sql
    async def get_promo_urls(self):
        """
        SELECT code, Discount_percentage FROM Urls
        """
        cursor = await self.conn.cursor()
        result = await cursor.execute("SELECT code, Discount_percentage FROM Urls")
        result = await result.fetchall()
        try:
            if result and len(result) > 0 and result[0]:
                temp_m = []
                for item in result:
                    temp_m.append((item[0], item[1]))
                result = temp_m
            else:
                result = []
        except:
            await Print_Error()
        return result

    @while_sql
    async def update_spec_url(self, id, date):
        cursor = await self.conn.cursor()
        await cursor.execute("UPDATE Urls SET date = ? WHERE id = ?", (date, id,))
        return await self.conn.commit()

    @while_sql
    async def delete_spec_url(self, id):
        cursor = await self.conn.cursor()
        await cursor.execute("DELETE FROM Urls WHERE id = ?", (id,))
        await self.conn.commit()
        return True

    @while_sql
    async def get_user_operations(self, url_code=None, type='promo', user_id=None, da=False):
        cursor = await self.conn.cursor()

        # Пример:
        # 
        # url_code = 'UNUS'
        # type = 'buy'
        # user_id = None
        # da = False

        if type == 'all' or user_id:
            type_text = ''
        else:
            type_text = ' and o.type=?'

        where_text = f'url.code = ?{type_text}'

        if type == 'all' or user_id:
            if url_code:
                args = (url_code,)
            elif user_id:
                where_text = f'o.user_id = ?'
                args = (user_id,)
        else:
            args = (url_code, type, )

        if user_id is None:
            if type == 'promo' and not da:
                query = f"""
                    SELECT o.days, COUNT(*), SUM(o.summ), o.user_id
                    FROM Operations o
                    JOIN Users u ON o.user_id = u.User_id
                    JOIN Urls url ON u.Promo = url.code
                    WHERE {where_text}
                    GROUP BY o.days
                """
            else:
                query = f"""
                    SELECT o.summ, o.Date, o.user_id
                    FROM Operations o
                    JOIN Users u ON o.user_id = u.User_id
                    JOIN Urls url ON u.Promo = url.code
                    WHERE {where_text}
                """
        else:
            query = f"SELECT id, type, summ, days, promo_code, bill_id, Description, Date FROM Operations WHERE user_id = ?"

        await cursor.execute(query, args)
        result = await cursor.fetchall()
        return result

    @while_sql
    async def get_users_summ_by_spec_code(self, url_code=None):
        cursor = await self.conn.cursor()
        query = f"""
            SELECT o.user_id, SUM(o.summ), COUNT(*)
            FROM Operations o
            JOIN Users u ON o.user_id = u.User_id
            JOIN Urls url ON u.Promo = url.code
            WHERE url.code = ? and o.summ > 0
            GROUP BY o.user_id
        """
        await cursor.execute(query, (url_code,))
        result = await cursor.fetchall()
        return result

    @while_sql
    async def get_all_code_by_partner(self, id_partner):
        cursor = await self.conn.cursor()
        await cursor.execute('SELECT Code, isActivated, CountDays FROM PromoCodes WHERE id_partner = ?', (id_partner, ))
        result = await cursor.fetchall()

        await cursor.execute('SELECT code FROM Urls WHERE id_partner = ?', (id_partner, ))
        result1 = await cursor.fetchone()
        result1 = result1[0]

        return (result, result1)
    
    @while_sql
    async def get_all_promo_codes(self):
        cursor = await self.conn.cursor()
        result = await cursor.execute("SELECT Code, CountDays, isActivated, User FROM PromoCodes")
        return await result.fetchall()
    
    @while_sql
    async def set_activate_promo(self, code=None, user=None, user_id=None, days=None):
        cursor = await self.conn.cursor()
        await cursor.execute("UPDATE PromoCodes SET isActivated = ?, User = ? WHERE Code = ?", (True, user, code,))
        await self.conn.commit()
        
        result = await self.exists_individual_promo_code(code)
        if result:
            await self.add_activate_individual_promo_code(code, user_id)

        if days == 30:
            summ = TARIF_1
        elif days == 90:
            summ = TARIF_3
        elif days == 180:
            summ = TARIF_6
        elif days == 365:
            summ = TARIF_12
        else:
            summ = 0

        user = await user_get(user_id)
        await self.add_operation('promo', user_id, summ, days, code, decription=user.paymentDescription)
        await self.addReportsData('CountBuy', 1)
        return True
    #endregion

    #region Подписки
    @while_sql
    async def get_podpiski(self, isOn=False):
        cursor = await self.conn.cursor()
        if isOn:
            where = ' WHERE isOn = ?'
            arg = (True,)
        else:
            where = ''
            arg = None
        result = await cursor.execute(f"SELECT p.id, p.Name, p.Channels, p.isOn, COUNT(q.Podpiska) AS SubscriptionCount FROM Podpiski p LEFT JOIN QR_Keys q ON p.id = q.Podpiska{where} GROUP BY p.id, p.Name, p.Channels, p.isOn;", arg)
        return await result.fetchall()
    
    @while_sql
    async def delete_podpisky(self, id):
        cursor = await self.conn.cursor()
        await cursor.execute("DELETE FROM Podpiski WHERE id = ?", (id,))
        await self.conn.commit()
        return True
    
    @while_sql
    async def update_name_podpiska(self, id, name):
        cursor = await self.conn.cursor()
        await cursor.execute("UPDATE Podpiski SET Name = ? WHERE id = ?", (name, id,))
        await self.conn.commit()
        return True
    
    @while_sql
    async def update_isOn_podpiska(self, id, isOn):
        cursor = await self.conn.cursor()
        await cursor.execute("UPDATE Podpiski SET isOn = ? WHERE id = ?", (isOn, id,))
        await self.conn.commit()
        return True

    @while_sql
    async def add_podpiska(self, Name, Channels):
        cursor = await self.conn.cursor()
        await cursor.execute("INSERT INTO Podpiski (Name, Channels) VALUES (?, ?)", (Name, Channels))
        await self.conn.commit()
        return True

    #endregion

    #region Запросы
    @while_sql
    async def get_all_zaprosi(self, user_id=None, status=None):
        cursor = await self.conn.cursor()
        where = ''
        arg = ()
        if not user_id is None:
            where = ' WHERE User_id = ?'
            arg = (user_id,)
        elif not status is None:
            where = ' WHERE Status = ?'
            arg = (status,)

        logger.debug(f"get_all_zaprosi -> user_id={user_id}, status={status}) -> SELECT id, User_id, Summ, Comment, Status, Dolg FROM Zaprosi{where} ORDER BY id DESC -> arg={arg}")
        result = await cursor.execute(f"SELECT id, User_id, Summ, Comment, Status, Dolg FROM Zaprosi{where} ORDER BY id DESC", arg)
        return await result.fetchall()

    @while_sql
    async def get_zapros(self, id):
        cursor = await self.conn.cursor()
        result = await cursor.execute("SELECT id, User_id, Summ, Comment, Status, Dolg FROM Zaprosi WHERE id = ?", (id,))
        return await result.fetchone()

    @while_sql
    async def update_zapros(self, id, Status):
        cursor = await self.conn.cursor()
        await cursor.execute("UPDATE Zaprosi SET Status = ? WHERE id = ?", (Status, id,))
        await self.conn.commit()

        # получить id пользователя по id запроса
        user_id = await cursor.execute("SELECT User_id FROM Zaprosi WHERE id = ?", (id,))
        user_id = await user_id.fetchone()
        if user_id:
            user_id = user_id[0]
            # получить сумму запроса
            summ = await cursor.execute("SELECT Summ FROM Zaprosi WHERE id = ?", (id,))
            summ = await summ.fetchone()
            if summ and len(summ) > 0 and summ[0]:
                summ = summ[0]
                # если запрос одобрен, то добавляем сумму пользователю
                status_text = '✅Одобрен' if Status == 1 else '🛑Отклонен'
                status__ = '✅' if Status == 1 else '🛑'
                # добавляем операцию
                await self.add_operation('zapros', user_id, summ, 0, '', '', f'Запрос на вывод средств <b>{status_text}</b>')

                # отправить пользователю сообщение о том, что запрос одобрен или отклонен
                user = await user_get(user_id)
                await send_message(user_id, user.lang.get('tx_zapros_send_user').format(status=status__, id=id, summ=await razryad(summ), status_text=status_text))
        return 

    @while_sql
    async def add_zapros(self, User_id, Summ, Comment, Dolg):
        cursor = await self.conn.cursor()
        await cursor.execute("INSERT INTO Zaprosi (User_id, Summ, Comment, Dolg) VALUES (?, ?, ?, ?)", (User_id, Summ, Comment, Dolg,))
        return await self.conn.commit()
    #endregion

    #region Смена протокола
    @while_sql
    async def update_user_change_protocol(self, user_id):
        cursor = await self.conn.cursor()
        await cursor.execute("UPDATE Users SET isPayChangeProtocol = ? WHERE User_id = ?", (True, user_id,))
        return await self.conn.commit()
    
    @while_sql
    async def update_user_change_locations(self, user_id):
        cursor = await self.conn.cursor()
        date = datetime.now()
        await cursor.execute("UPDATE Users SET datePayChangeLocations = ? WHERE User_id = ?", (date, user_id,))
        return await self.conn.commit()

    @while_sql
    async def update_qr_key_date_change_protocol(self, bot_key, date):
        cursor = await self.conn.cursor()
        await cursor.execute("UPDATE QR_Keys SET DateChangeProtocol = ? WHERE BOT_Key = ?", (date, bot_key,))
        return await self.conn.commit()
    
    @while_sql
    async def get_user_is_pay_change_protocol(self, user_id):
        cursor = await self.conn.cursor()
        result = await cursor.execute("SELECT isPayChangeProtocol FROM Users WHERE User_id = ?", (user_id,))
        result = await result.fetchone()
        if not result is None and len(result) > 0 and not result[0] is None:
            result = bool(result[0])
        else:
            result  = False
        return result
    
    @while_sql
    async def get_user_is_pay_change_locations(self, user_id):
        cursor = await self.conn.cursor()
        result = await cursor.execute("SELECT datePayChangeLocations FROM Users WHERE User_id = ?", (user_id,))
        result = await result.fetchone()
        if not result is None and len(result) > 0 and not result[0] is None:
            result = result[0]
        else:
            result  = None
        return result
    #endregion

    #region Отчеты
    @while_sql
    async def addReportsData(self, pole='', summ=0):
        today = date.today()
        cursor = await self.conn.cursor()

        await cursor.execute(f"SELECT {pole}, Date FROM ReportsData WHERE Date = ?", (today,)) 
        row = await cursor.fetchone()

        if row:
            # если запись существует, обновляем значение
            count = row[0] + summ
            await cursor.execute(f"UPDATE ReportsData SET {pole} = ? WHERE Date = ?", (count, today))
        else:
            # если запись не существует, создаем новую запись
            await cursor.execute(f"INSERT INTO ReportsData ({pole}, Date) VALUES (?, ?)", (summ, today))

        # сохраняем изменения в базе данных
        await self.conn.commit()

    @while_sql
    async def getAllReportsData(self):
        cursor = await self.conn.cursor()
        await cursor.execute("SELECT CountNewUsers, CountBuy, CountTestKey, SummDay, Date FROM ReportsData")
        return await cursor.fetchall()
    
    @while_sql
    async def exists_opertion_by_bill_id(self, user_id, bill_id):
        cursor = await self.conn.cursor()
        result = await cursor.execute("SELECT bill_id FROM Operations WHERE user_id = ? and bill_id = ?", (user_id, bill_id,))
        result = await result.fetchall()
        return bool(len(result))

    #endregion

    #region Переменные
    @while_sql
    async def UPDATE_VARIABLES(self, name, value):
        cursor = await self.conn.cursor()
        await cursor.execute("UPDATE Variables SET Value = ? WHERE Name = ?", (str(value), name,))
        return await self.conn.commit()

    @while_sql
    async def GET_VARIABLE(self, name):
        cursor = await self.conn.cursor()
        result = await cursor.execute("SELECT Value FROM Variables where Name = ?", (name,))
        result = await result.fetchone()
        if result and len(result) > 0 and not result[0] is None:
            try:
                result = int(result[0])
            except:
                try:
                    result = float(result[0])
                except:
                    result = result[0]
        else:
            result = 0
        return result
    #endregion

    #region Сервера
    @while_sql
    async def GET_SERVERS(self):
        cursor = await self.conn.cursor()
        result = await cursor.execute("SELECT ip, password, count_keys, api_url, cert_sha256, Location, isPremium, is_marzban, is_pptp FROM Servers")
        result = await result.fetchall()
        result = [{'ip': item[0], 'password': item[1], 'count_keys': item[2], 'api_url': item[3], 'cert_sha256': item[4], 'location': item[5], 'isPremium': bool(item[6]), 'is_marzban':bool(item[7]), 'is_pptp':bool(item[8])} for item in result]
        
        global SERVERS
        SERVERS = result
        return result

    @while_sql
    async def DELETE_SERVER(self, ip=None):
        cursor = await self.conn.cursor()
        await cursor.execute("DELETE FROM Servers WHERE ip = ?", (ip,))
        await self.conn.commit()

        await DB.GET_SERVERS()
        return True

    @while_sql
    async def SET_SERVER_PREMIUM(self, ip=None, isPremium=False):
        cursor = await self.conn.cursor()
        await cursor.execute("UPDATE Servers SET isPremium = ? WHERE ip = ?", (isPremium, ip,))
        await self.conn.commit()

        await DB.GET_SERVERS()
        return True

    @while_sql
    async def ADD_SERVER(self, ip, password, count_keys, api_url, cert_sha256, location, is_marzban, is_pptp):
        cursor = await self.conn.cursor()
        await cursor.execute("INSERT INTO Servers (ip, password, count_keys, api_url, cert_sha256, Location, is_marzban, is_pptp) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (ip, password, count_keys, api_url, cert_sha256, location, is_marzban, is_pptp))
        await self.conn.commit()

        await DB.GET_SERVERS()
        return True

    @while_sql
    async def UPDATE_SERVER(self, ip, count_keys):
        cursor = await self.conn.cursor()
        await cursor.execute("UPDATE Servers SET count_keys = ? WHERE ip = ?", (count_keys, ip,))
        await self.conn.commit()

        await DB.GET_SERVERS()
        return True

    @while_sql
    async def UPDATE_SERVER_LOCATION(self, ip, location):
        cursor = await self.conn.cursor()
        await cursor.execute("UPDATE Servers SET Location = ? WHERE ip = ?", (location, ip,))
        await self.conn.commit()

        await DB.GET_SERVERS()
        return True
    #endregion

    #region Кошельки
    @while_sql
    async def GET_WALLETS(self):
        cursor = await self.conn.cursor()
        result = await cursor.execute("SELECT id, isActive, Name, API_Key_TOKEN, ShopID_CLIENT_ID, E_mail_URL FROM Wallets")
        result = await result.fetchall()
        result = [{'id': item[0],'isActive': bool(item[1]), 'Name': item[2], 'API_Key_TOKEN': item[3], 'ShopID_CLIENT_ID': item[4], 'E_mail_URL': item[5]} for item in result]
        
        global WALLETS
        WALLETS = result
        return result
    
    @while_sql
    async def ADD_WALLET(self, Name, API_Key_TOKEN, ShopID_CLIENT_ID, E_mail_URL):
        cursor = await self.conn.cursor()
        await cursor.execute("INSERT INTO Wallets (Name, API_Key_TOKEN, ShopID_CLIENT_ID, E_mail_URL) VALUES (?, ?, ?, ?)", (Name, API_Key_TOKEN, ShopID_CLIENT_ID, E_mail_URL))
        await self.conn.commit()

        await DB.GET_WALLETS()
        return True

    @while_sql
    async def DELETE_WALLET(self, id):
        cursor = await self.conn.cursor()
        await cursor.execute("DELETE FROM Wallets WHERE id = ?", (id,))
        await self.conn.commit()

        await DB.GET_WALLETS()
        return True

    @while_sql
    async def UPDATE_WALLET_IS_ACTIVE(self, id, isActive=True):
        cursor = await self.conn.cursor()
        await cursor.execute("UPDATE Wallets SET isActive = ? WHERE id = ?", (isActive, id,))
        await self.conn.commit()

        await DB.GET_WALLETS()
        return True
    
    #endregion

    #region Выполнение напрямую
    @while_sql
    async def EXECUTE(self, query='', args=(), res=False):
        try:
            if query != '':
                cursor = await self.conn.cursor()
                if not res:
                    result = await cursor.execute(query, args)
                    return True
                else:
                    result = await cursor.execute(query, args)
                    result = await result.fetchone()
                    return result
        except:
            return False

    @while_sql
    async def COMMIT(self):
        await self.conn.commit()
        return True
    #endregion

    async def close(self):
        await self.conn.close()

class GeneratePromo:
    async def generate_promo_code(self):
        try:
            alphabet = string.ascii_uppercase + string.ascii_lowercase + string.digits
            code = ''.join(random.choices(alphabet, k=8))
            return code
        except:
            await Print_Error()

    @while_sql
    async def Generate(self, count_days=30, count=50, id_partner=0):
        # Генерируем код и добавляем его в таблицу PromoCodes
        for i in range(count):
            code = await self.generate_promo_code()
            cursor = await DB.conn.cursor()

            date_delete = date.today() + timedelta(days=5)

            if id_partner != 0:
                await cursor.execute("INSERT INTO PromoCodes (Code, CountDays, isActivated, id_partner, date_delete) VALUES (?, ?, ?, ?, ?)", (code, count_days, False, id_partner, date_delete))
            else:
                await cursor.execute("INSERT INTO PromoCodes (Code, CountDays, isActivated, date_delete) VALUES (?, ?, ?, ?)", (code, count_days, False, date_delete))

        return code

    @while_sql
    async def Delete(self, count_days=30):
        # Генерируем код и добавляем его в таблицу PromoCodes
        cursor = await DB.conn.cursor()
        await cursor.execute("DELETE FROM PromoCodes WHERE CountDays = ? and isActivated = ?", (count_days, True,))

class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, limit=0.7, key_prefix='antiflood_'):
        self.rate_limit = limit
        self.prefix = key_prefix
        super(ThrottlingMiddleware, self).__init__()

    async def throttle(self, target: Union[Message, CallbackQuery]):
        handler = current_handler.get()
        dispatcher = Dispatcher.get_current()
        if not handler:
            return
        limit = getattr(handler, 'throttling_rate_limit', self.rate_limit)
        key = getattr(handler, 'throttling_key', f"{self.prefix}_{handler.__name__}")

        try:
            await dispatcher.throttle(key, rate=limit)
        except Throttled as t:
            await self.target_throttled(target, t, dispatcher, key)
            raise CancelHandler()

    @staticmethod
    async def target_throttled(target: Union[Message, CallbackQuery], throttled: Throttled, dispatcher: Dispatcher, key: str):
        msg = target.message if isinstance(target, CallbackQuery) else target
        delta = throttled.rate - throttled.delta

        await asyncio.sleep(delta)

        if throttled.exceeded_count == 3:
            user_id = msg.chat.id
            user = await user_get(user_id)
            await msg.reply(user.lang.get('tx_spam'))
            return
        # thr = await dispatcher.check_key(key)
        # if thr.exceeded_count == throttled.exceeded_count:
        #     pass

    async def on_process_message(self, message, data):
        await self.throttle(message)

    async def on_process_callback_query(self, call, data):
        await self.throttle(call)

#region Классы способов оплат
class Quickpay:
    def __init__(self,
            receiver: str,
            quickpay_form : str,
            targets: str,
            paymentType: str,
            sum: float,
            formcomment: str = None,
            short_dest: str = None,
            label: str = None,
            comment: str = None,
            successURL: str = None,
            need_fio: bool = None,
            need_email: bool = None,
            need_phone: bool = None,
            need_address: bool = None,
        ):
        self.receiver = receiver
        self.quickpay_form = quickpay_form
        self.targets = targets
        self.paymentType = paymentType
        self.sum = sum
        self.formcomment = formcomment
        self.short_dest = short_dest
        self.label = label
        self.comment = comment
        self.successURL = successURL
        self.need_fio = need_fio
        self.need_email = need_email
        self.need_phone = need_phone
        self.need_address = need_address

    async def _request(self):
        self.base_url = "https://yoomoney.ru/quickpay/confirm.xml?"
        payload = {}

        payload["receiver"] = self.receiver
        payload["quickpay_form"] = self.quickpay_form
        payload["targets"] = self.targets
        payload["paymentType"] = self.paymentType
        payload["sum"] = self.sum

        if self.formcomment != None:
            payload["formcomment"] = self.formcomment
        if self.short_dest != None:
            payload["short_dest"] = self.short_dest
        if self.label != None:
            payload["label"] = self.label
        if self.comment != None:
            payload["comment"] = self.comment
        if self.successURL != None:
            payload["successURL"] = self.successURL
        if self.need_fio != None:
            payload["need_fio"] = self.need_fio
        if self.need_email != None:
            payload["need_email"] = self.need_email
        if self.need_phone != None:
            payload["need_phone"] = self.need_phone
        if self.need_address != None:
            payload["need_address"] = self.need_address

        for value in payload:
            self.base_url+=str(value).replace("_","-") + "=" + str(payload[value])
            self.base_url+="&"

        self.base_url = self.base_url[:-1].replace(" ", "%20")

        async with aiohttp.ClientSession(timeout=get_timeount(10)) as session:
            async with session.post(self.base_url, headers={'Accept':'application/json', 'Content-Type': 'application/json'}) as response:
                self.response = response
                self.redirected_url = response.url
                return response

class Account:
    def __init__(self,
        base_url: str = None,
        token: str = None,
        method: str = None,
    ):

        self.__private_method = method

        self.__private_base_url = base_url
        self.__private_token = token

    def get(self):
        data = self.data
        if len(data) != 0:
            self.account = data['account']
            self.balance = data['balance']
            self.currency = data['currency']
            self.account_status = data['account_status']
            self.account_type = data['account_type']

            self.balance_details = BalanceDetails()
            if 'balance_details' in data:
                if 'available' in data['balance_details']:
                    self.balance_details.available = float(data['balance_details']['available'])
                if 'blocked' in data['balance_details']:
                    self.balance_details.blocked = float(data['balance_details']['blocked'])
                if 'debt' in data['balance_details']:
                    self.balance_details.debt = float(data['balance_details']['debt'])
                if 'deposition_pending' in data['balance_details']:
                    self.balance_details.deposition_pending = float(data['balance_details']['deposition_pending'])
                if 'total' in data['balance_details']:
                    self.balance_details.total = float(data['balance_details']['total'])
                if 'hold' in data['balance_details']:
                    self.balance_details.hold = float(data['balance_details']['hold'])

            self.cards_linked = []
            if 'cards_linked' in data:
                for card_linked in data['cards_linked']:
                    card = Card(pan_fragment=card_linked['pan_fragment'], type=card_linked['type'])
                    self.cards_linked.append(card)
        else:
            raise InvalidToken()

    async def _request(self):
        access_token = str(self.__private_token)
        url = self.__private_base_url + self.__private_method
        headers = {
            'Authorization': 'Bearer ' + str(access_token),
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        async with aiohttp.ClientSession(timeout=get_timeount(5)) as session:
            async with session.post(url, headers=headers) as response:
                return await response.json()

class History:
    def __init__(self,
        base_url: str = None,
        token: str = None,
        method: str = None,
        type: str = None,
        label: str = None,
        from_date: Optional[datetime] = None,
        till_date: Optional[datetime] = None,
        start_record: str = None,
        records: int = None,
        details: bool = None,
    ):

        self.__private_method = method

        self.__private_base_url = base_url
        self.__private_token = token

        self.type = type
        self.label = label
        try:
            if from_date is not None:
                from_date = "{Y}-{m}-{d}T{H}:{M}:{S}".format(
                    Y=str(from_date.year),
                    m=str(from_date.month),
                    d=str(from_date.day),
                    H=str(from_date.hour),
                    M=str(from_date.minute),
                    S=str(from_date.second)
                )
        except:
            raise IllegalParamFromDate()

        try:
            if till_date is not None:
                till_date = "{Y}-{m}-{d}T{H}:{M}:{S}".format(
                    Y=str(till_date.year),
                    m=str(till_date.month),
                    d=str(till_date.day),
                    H=str(till_date.hour),
                    M=str(till_date.minute),
                    S=str(till_date.second)
                )
        except:
            IllegalParamTillDate()

        self.from_date = from_date
        self.till_date = till_date
        self.start_record = start_record
        self.records = records
        self.details = details

    def get(self):
        data = self.data
        if "error" in data:
            if data["error"] == "illegal_param_type":
                raise IllegalParamType()
            elif data["error"] == "illegal_param_start_record":
                raise IllegalParamStartRecord()
            elif data["error"] == "illegal_param_records":
                raise IllegalParamRecords()
            elif data["error"] == "illegal_param_label":
                raise IllegalParamLabel()
            elif data["error"] == "illegal_param_from":
                raise IllegalParamFromDate()
            elif data["error"] == "illegal_param_till":
                raise IllegalParamTillDate()
            else:
                raise TechnicalError()

        self.next_record = None
        if "next_record" in data:
            self.next_record = data["next_record"]

        self.operations = list()
        for operation_data in data["operations"]:
            param = {}
            if "operation_id" in operation_data:
                param["operation_id"] = operation_data["operation_id"]
            else:
                param["operation_id"] = None
            if "status" in operation_data:
                param["status"] = operation_data["status"]
            else:
                param["status"] = None
            if "datetime" in operation_data:
                param["datetime"] = datetime.strptime(str(operation_data["datetime"]).replace("T", " ").replace("Z", ""), '%Y-%m-%d %H:%M:%S')
            else:
                param["datetime"] = None
            if "title" in operation_data:
                param["title"] = operation_data["title"]
            else:
                param["title"] = None
            if "pattern_id" in operation_data:
                param["pattern_id"] = operation_data["pattern_id"]
            else:
                param["pattern_id"] = None
            if "direction" in operation_data:
                param["direction"] = operation_data["direction"]
            else:
                param["direction"] = None
            if "amount" in operation_data:
                param["amount"] = operation_data["amount"]
            else:
                param["amount"] = None
            if "label" in operation_data:
                param["label"] = operation_data["label"]
            else:
                param["label"] = None
            if "type" in operation_data:
                param["type"] = operation_data["type"]
            else:
                param["type"] = None

            operation = Operation(
                operation_id= param["operation_id"],
                status=param["status"],
                datetime=datetime.strptime(str(param["datetime"]).replace("T", " ").replace("Z", ""), '%Y-%m-%d %H:%M:%S'),
                title=param["title"],
                pattern_id=param["pattern_id"],
                direction=param["direction"],
                amount=param["amount"],
                label=param["label"],
                type=param["type"],
            )
            self.operations.append(operation)

    async def _request(self):
        access_token = str(self.__private_token)
        url = self.__private_base_url + self.__private_method
        headers = {
            'Authorization': 'Bearer ' + str(access_token),
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        payload = {}
        if self.type is not None:
            payload["type"] = self.type
        if self.label is not None:
            payload["label"] = self.label
        if self.from_date is not None:
            payload["from"] = self.from_date
        if self.till_date is not None:
            payload["till"] = self.till_date
        if self.start_record is not None:
            payload["start_record"] = self.start_record
        if self.records is not None:
            payload["records"] = self.records
        if self.details is not None:
            payload["details"] = self.details

        async with aiohttp.ClientSession(timeout=get_timeount(10)) as session:
            async with session.post(url, headers=headers, data=payload) as response:
                return await response.json()

class Client:
    def __init__(self,
        token: str = None,
        base_url: str = None,
    ):

        if base_url is None:
            self.base_url = "https://yoomoney.ru/api/"

        if token is not None:
            self.token = token

    def account_info(self):
        method = "account-info"
        return Account(base_url=self.base_url,
            token=self.token,
            method=method
            )

    def operation_history(self,
        type: str = None,
        label: str = None,
        from_date: datetime = None,
        till_date: datetime = None,
        start_record: str = None,
        records: int = None,
        details: bool = None,
    ):
        method = "operation-history"
        return History(base_url=self.base_url,
            token=self.token,
            method=method,
            type=type,
            label=label,
            from_date=from_date,
            till_date=till_date,
            start_record=start_record,
            records=records,
            details=details,
            )

class PayOK:
    def __init__(self, api_key, api_id, id_magazin, secret_key):
        self.api_key = api_key
        self.api_id = api_id
        self.id_magazin = id_magazin
        self.secret_key = secret_key

    async def get_balance(
            self,
            API_ID: int,
            API_KEY: str
        ) -> dict[float,float]:
        """
        Args:
            API_ID (int): ID вашего ключа API
            API_KEY (str): Ваш ключ API

        Answer (dict):
            balance (str(float)): Основной баланс кошелька.
            ref_balance (str(float)): Реферальный баланс кошелька.

        Example answer:
            {
                "balance":"339.44",
                "ref_balance":"6063.60"
            }
        Raises:
            Exception

        Returns:
            dict

        Doc:
            https://payok.io/cabinet/documentation/doc_api_balance
        """
        url = "https://payok.io/api/balance"
        data = {
            "API_ID": API_ID,
            "API_KEY": API_KEY
        }
        response = requests.post(
            url,
            data,
            timeout=5
        ).json()
        
        # async with aiohttp.ClientSession(timeout=get_timeount(5)) as session:
        #     async with session.post(url, json=data) as response:
        #         response = await response.json()

        try:
            # result = {
            #     "balance": float(response["balance"]),
            #     "ref_balance": float(response["ref_balance"]),
            # }
            # return result
            return int(float(response["balance"]))
        except:
            raise Exception(
                response
            )

    async def getTransaction(
            self,
            API_ID: int,
            API_KEY: str,
            shop: int,
            payment = None,
            offset: int = None
        ) -> dict:
        """
        Args:
            API_ID (int): ID вашего ключа API
            API_KEY (str): Ваш ключ API
            shop (int): ID магазина
            payment (optional): ID платежа в вашей системе
            offset (int, optional): Отступ, пропуск указанного количества строк

        Raises:
            Exception

        Returns:
            dict

        Doс and answer:
            https://payok.io/cabinet/documentation/doc_api_transaction
        """
        url = "https://payok.io/api/transaction"
        data = {
            "API_ID": API_ID,
            "API_KEY": API_KEY,
            "shop": shop,
            "payment": payment,
            "offset": offset
        }
        response = requests.post(
            url,
            data,
            timeout=5
        ).json()
        
        # async with aiohttp.ClientSession(timeout=get_timeount(5)) as session:
        #     async with session.post(url, data=data) as response:
        #         response = await response.json()
        
        if response["status"] == "success":
            return response
        else:
            raise Exception(
                response
            )

    def createPay(
        self,
        secret : str,
        amount: float,
        payment: str,
        shop: int,
        desc: str,
        currency: str = "RUB",
        # email: str = None,
        success_url: str = None,
        # method: str = None,
        # lang: str = None,
        # custom = None,
        ) -> str:
        """
        Args:
            secret (str): SECRET KEY (Узнайте свой секретный ключ в личном кабинете)
            amount (float): Сумма заказа.
            payment (str): Номер заказа, уникальный в вашей системе, до 16 символов. (a-z0-9-_)	
            shop (int): ID вашего магазина.	
            desc (str): Название или описание товара.	
            currency (str, optional): Валюта по стандарту ISO 4217. По умолчанию "RUB".
            email (str, optional): Эл. Почта покупателя. Defaults to None.
            success_url (str, optional): Ссылка для переадресации после оплаты, подробнее (https://payok.io/cabinet/documentation/doc_redirect.php). Defaults to None.
            method (str, optional): Способ оплаты (Cписок названий методов: https://payok.io/cabinet/documentation/doc_methods.php). Defaults to None.
            lang (str, optional): Язык интерфейса. RU или EN (Если не указан, берется язык браузера). Defaults to None.
            custom (_type_, optional): Ваш параметр, который вы хотите передать в уведомлении. Defaults to None.

        Returns:
            str: url
        """
        data = [
            amount,
            payment,
            shop,
            currency,
            desc,
            secret
        ]
        sign = hashlib.md5(
            "|".join(
                map(
                    str,
                    data
                )
            ).encode("utf-8")
        ).hexdigest()
        desc = urllib.parse.quote_plus(desc)
        success_url= urllib.parse.quote_plus(success_url)
        url = f"https://payok.io/pay?amount={amount}&payment={payment}&desc={desc}&shop={shop}&sign={sign}&success_url={success_url}"
        return url

class ROOT_PAY:
    def __init__(self, api_token):
        self.api_token = api_token
        self.headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        self.data = {
            'api_token': api_token
        }
        
    async def _post(self, url, headers, data):
        async with aiohttp.ClientSession(timeout=get_timeount(10)) as session:
            async with session.post(url, headers=headers, data=data) as response:
                return await response.json()

    async def get_balance(self):
        url = 'https://root-pay.app/api/balance'
        return await self._post(url, self.headers, self.data)

    async def get_methods_pay(self):
        url = 'https://root-pay.app/api/methods_pay'
        return await self._post(url, self.headers, self.data)

    async def create_payment(self, method, amount, subtitle=None, comment=None):
        url = 'https://root-pay.app/api/create_payment'
        data = {
            'api_token': self.api_token,
            'method': method,
            'amount': amount,
            'subtitle': subtitle,
            'comment': comment
        }
        return await self._post(url, self.headers, data)

    async def get_payment_info(self, session_id):
        url = 'https://root-pay.app/api/get_payment_info'
        data = {
            'api_token': self.api_token,
            'session_id': session_id
        }
        return await self._post(url, self.headers, data)

    async def get_payments(self, count=10):
        url = 'https://root-pay.app/api/get_payments'
        data = {
            'api_token': self.api_token,
            'count': count
        }
        return await self._post(url, self.headers, data)

class PAY_METHODS:
    YOO_MONEY = 'Ю.Money'
    YOO_KASSA = 'Ю.Касса'
    TINKOFF = 'Tinkoff Pay'
    LAVA = 'Lava'
    CRYPTOMUS = 'Cryptomus'
    WALLET_PAY = 'Wallet Pay'
    SOFT_PAY = 'Soft Pay'
    PAYOK = 'Payok'
    AAIO = 'Aaio'
    ROOT_PAY = 'RootPay'
    FREE_KASSA = 'FreeKassa'
    XTR = 'XTR'
    CARDLINK = 'CardLink'

class YPay:
    async def _sort_dict(self, data: dict):
        sorted_tuple = sorted(data.items(), key=lambda x: x[0]) 
        return dict(sorted_tuple)

    async def __error_no_wallet__(self):
        zametki = '⚠️Заметки: <b>Необходимо пройти в /wallets и добавить способ оплаты!</b>'
        await send_admins(None, '🛑Не найдено способов оплаты!', zametki)

    async def __error__(self, error=''):
        error_str = str(error).lower()
        texts = (
            'aborted',
            'reset by peer',
            'timeout',
        )

        if any(text in error_str for text in texts):
            return

        text_send = f'\n\n⚠️Ошибка:\n{error}'
        await send_admins(None, '🛑Ошибка оплаты', text_send)

    def __init__(self, id=None, select_title=None):
        try:
            # Установка переменных
            self.Name = ''
            self.API_Key_TOKEN = ''
            self.ShopID_CLIENT_ID = ''
            self.E_mail_URL = ''

            self.isYooMoney, self.isYooKassa, self.isLava, self.isCryptomus, self.isTinfkoffPay, self.isWalletPay, self.isSoftPay, self.isPayok, self.isAaio, self.isRootPay, self.isFreeKassa, self.isXTR, self.isCardLink = False, False, False, False, False, False, False, False, False, False, False, False, False

            # Перемешать WALLETS
            wallets = [wallet for wallet in WALLETS]
            random.shuffle(wallets)

            # Выбор кошелька
            for wallet in wallets:
                is_active = wallet['isActive']
                id_wallet = wallet['id']

                self.Name = wallet['Name']
                self.API_Key_TOKEN = wallet['API_Key_TOKEN']
                self.ShopID_CLIENT_ID = wallet['ShopID_CLIENT_ID']
                self.E_mail_URL = wallet['E_mail_URL']
                
                if not id is None:
                    if id != id_wallet:
                        continue
                elif select_title:
                    if select_title != self.Name:
                        continue
                elif not is_active:
                    continue

                if self.Name == PAY_METHODS.YOO_MONEY: self.isYooMoney = True
                elif self.Name == PAY_METHODS.YOO_KASSA: self.isYooKassa = True
                elif self.Name == PAY_METHODS.TINKOFF: self.isTinfkoffPay = True # Пример
                elif self.Name == PAY_METHODS.LAVA: self.isLava = True
                elif self.Name == PAY_METHODS.CRYPTOMUS: self.isCryptomus = True
                elif self.Name == PAY_METHODS.WALLET_PAY: self.isWalletPay = True
                elif self.Name == PAY_METHODS.SOFT_PAY: self.isSoftPay = True
                elif self.Name == PAY_METHODS.PAYOK: self.isPayok = True
                elif self.Name == PAY_METHODS.AAIO: self.isAaio = True
                elif self.Name == PAY_METHODS.ROOT_PAY: self.isRootPay = True
                elif self.Name == PAY_METHODS.FREE_KASSA: self.isFreeKassa = True
                elif self.Name == PAY_METHODS.XTR: self.isXTR = True
                elif self.Name == PAY_METHODS.CARDLINK: self.isCardLink = True
                break

            try:
                if self.isLava or self.isSoftPay or self.isXTR:
                    pass # Не нужно ничего заранее устанавливать
                elif self.isCardLink:
                    self.headers = {
                        'Authorization': f'Bearer {self.API_Key_TOKEN}'
                    }
                elif self.isYooKassa:
                    Configuration.account_id = self.ShopID_CLIENT_ID
                    Configuration.secret_key = self.API_Key_TOKEN
                    Configuration.timeout = 5
                elif self.isTinfkoffPay:
                    if PHONE_NUMBER != '':
                        self.tinkoff = TinkoffAcquiring(self.API_Key_TOKEN, self.ShopID_CLIENT_ID)
                    else:
                        asyncio.run(send_admins(MY_ID_TELEG, '🛑Не указан номер телефона для Tinkoff Pay!', f'Номер телефона: <b>"{PHONE_NUMBER}"</b> (/get_config -> PHONE_NUMBER = "")'))
                elif self.isYooMoney:
                    self.client = Client(self.API_Key_TOKEN)
                elif self.isCryptomus:
                    self.cryptomus = Cryptomus(self.ShopID_CLIENT_ID, self.API_Key_TOKEN)
                elif self.isWalletPay:
                    self.walletpay = AsyncWalletPayAPI(self.API_Key_TOKEN)
                elif self.isPayok:
                    self.api_id = self.ShopID_CLIENT_ID.split(':')[0]
                    self.id_magazin = int(self.ShopID_CLIENT_ID.split(':')[1])
                    self.payok = PayOK(self.API_Key_TOKEN, self.api_id, self.id_magazin, self.E_mail_URL)
                elif self.isAaio:
                    shop_id = self.ShopID_CLIENT_ID.split(':')[0]
                    secret_key_1 = self.ShopID_CLIENT_ID.split(':')[1]
                    self.aaio = AaioAsync(self.API_Key_TOKEN, shop_id, secret_key_1)
                elif self.isRootPay:
                    self.rootpay = ROOT_PAY(self.API_Key_TOKEN)
                elif self.isFreeKassa:
                    self.freekassa = Freekassa(api_key=self.API_Key_TOKEN, shop_id=self.ShopID_CLIENT_ID)
                else:
                    asyncio.run(self.__error_no_wallet__())
            except Exception as error:
                asyncio.run(self.__error__(error))
        except:
            asyncio.run(Print_Error())

    async def get_balance(self):
        try:
            if self.isYooKassa or self.isTinfkoffPay or self.isCryptomus or self.isSoftPay or self.isXTR:
                return -1
            elif self.isYooMoney:
                try:
                    user = self.client.account_info()
                    user.data = await user._request()
                    user.get()
                except Exception as error:
                    await self.__error__(error)
                    return 0
                return int(user.balance)
            elif self.isLava:
                try:
                    data = {
                        "shopId": self.ShopID_CLIENT_ID
                    }
                    data = await self._sort_dict(data)
                    jsonStr = json.dumps(data).encode()
                    sign = hmac.new(bytes(self.E_mail_URL, 'UTF-8'), jsonStr, hashlib.sha256).hexdigest()

                    async with aiohttp.ClientSession(timeout=get_timeount(5)) as session:
                        async with session.post('https://api.lava.ru/business/shop/get-balance', json=data, headers={'Signature': sign, 'Accept':'application/json', 'Content-Type': 'application/json'}) as response:
                            response_data = await response.json()
                            return int(response_data["data"]["balance"])
                except Exception as error:
                    await self.__error__(error)
                    return 0
            elif self.isWalletPay:
                try:
                    balance = await self.walletpay.get_order_amount()
                except Exception as error:
                    await self.__error__(error)
                    return 0
                return int(balance.split('.')[0])
            elif self.isPayok:
                try:
                    balance = await self.payok.get_balance(self.api_id, self.API_Key_TOKEN)
                except Exception as error:
                    await self.__error__(error)
                    return 0
                return balance
            elif self.isAaio:
                try:
                    balance = await self.aaio.getbalance()
                    balance = int(balance.balance)
                except Exception as error:
                    await self.__error__(error)
                    return 0
                return balance
            elif self.isRootPay:
                try:
                    balance = await self.rootpay.get_balance()
                    balance = int(balance['balance'])
                except Exception as error:
                    await self.__error__(error)
                    return 0
                return balance
            elif self.isFreeKassa:
                try:
                    result = self.freekassa.get_balance()
                    result = result['balance']
                    result = result[0]
                    result = float(result['value'])
                    balance = int(result)
                except Exception as error:
                    await self.__error__(error)
                    return 0
                return balance
            elif self.isCardLink:
                try:
                    url = 'https://cardlink.link/api/v1/merchant/balance'
                    async with aiohttp.ClientSession(timeout=get_timeount(5)) as session:
                        async with session.get(url, headers=self.headers) as response:
                            res = await response.json()
                            balances = res['balances']
                            res = balances[0]
                            b_1 = float(res['balance_available'])
                            b_2 = float(res['balance_hold'])
                            balance = int(b_1 + b_2)
                    
                except Exception as error:
                    await self.__error__(error)
                    return 0
                return balance
            else:
                await self.__error_no_wallet__()
                return 0
        except:
            await Print_Error()
            return 0

    async def create_pay(self, user, summ):
        try:
            is_error = False
            try:
                user.amount_one = None
                user.wallet = None
                
                summ = int(summ)
                if summ < 10:
                    is_error = True
            except:
                is_error = True
            
            if is_error:
                await send_admins(None, '🛑Не верная сумма', f'Сумма: <b>{summ}</b>')

            if self.isYooKassa:
                # Создание ссылки для оплаты
                payment_data = {
                    "amount": {
                        "value": f"{summ}.00",
                        "currency": "RUB"
                    },
                    "confirmation": {
                        "type": "redirect",
                        "return_url": f"https://t.me/{BOT_NICK}"
                    },
                    "capture": True,
                    "description": user.lang.get('tx_pay_data').format(user_id=user.id_Telegram),
                    "receipt": {
                        "customer": {
                            "email": self.E_mail_URL
                        },
                        "items": [
                            {
                                "description": user.lang.get('tx_pay_data').format(user_id=user.id_Telegram),
                                "quantity": "1",
                                "amount": {
                                    "value": f"{summ}.00",
                                    "currency": "RUB"
                                },
                                "vat_code": "1",
                                "payment_mode": "full_prepayment",
                                "payment_subject": "service"
                            },
                        ]
                    }
                }
                if AUTO_PAY_YKASSA:
                    payment_data["save_payment_method"] = True
                try:
                    payment = Payment.create(payment_data)
                except:
                    await sleep(random.randint(10,30)/10)
                    payment = Payment.create(payment_data)
                logger.debug(f'Создал ссылку для оплаты bill_id = {payment.id}')
                logger.debug(f'Ссылка для оплаты = {payment.confirmation.confirmation_url}')
                user.bill_id = payment.id
                try:
                    return payment.confirmation.confirmation_url
                except Exception as error:
                    logger.warning(f'Ошибка при создании ссылки для оплаты: {error}')
                    return ''
            elif self.isTinfkoffPay:
                # Создание ссылки для оплаты
                order_id = f'{int(datetime.now().timestamp())}{random.randint(1000,9999)}'
                summ = str(int(summ*100))

                payment_data = {
                    'TerminalKey': self.API_Key_TOKEN,
                    'OrderId': order_id,
                    'Amount': summ,
                    "Description": user.lang.get('tx_pay_data').format(user_id=user.id_Telegram),
                    'Receipt': {
                        'Phone': PHONE_NUMBER,
                        'Email': self.E_mail_URL,
                        'Taxation': 'usn_income',
                        'Items': [{
                            'Name': user.lang.get('tx_pay_data').format(user_id=user.id_Telegram),
                            'Quantity': '1',
                            'Amount': summ,
                            'Tax': 'none',
                            'Price': summ,
                        },]
                    },
                    "SuccessURL": f'https://t.me/{BOT_NICK}',
                }
                if AUTO_PAY_YKASSA:
                    payment_data["PayType"] = 'O'
                    payment_data["Recurrent"] = 'Y'
                    payment_data["CustomerKey"] = f'{user.id_Telegram}'

                logger.debug(f'🔄Создаю ссылку для оплаты payment_data={payment_data}')
                result = self.tinkoff.init(payment_data)
                logger.debug(f'Создал ссылку для оплаты self.tinkoff.init(payment_data) = {result}')
                user.bill_id = result['PaymentId']
                return result['PaymentURL']
            elif self.isYooMoney:
                user.bill_id = str(random.randint(100000, 999999))
                quickpay = Quickpay(
                    receiver=self.API_Key_TOKEN.split('.')[0],
                    quickpay_form="shop",
                    targets=user.lang.get('tx_pay_data').format(user_id=user.id_Telegram),
                    paymentType="SB",
                    sum=summ,
                    label=user.bill_id,
                    successURL = f'https://t.me/{BOT_NICK}'
                )
                count = 0
                while True:
                    try:
                        count += 1
                        if count > 5:
                            break

                        await quickpay._request()
                        break
                    except Exception as e:
                        logger.warning(f'🛑Ошибка при создании ссылки для оплаты isYooMoney: {e}')
                logger.debug(f'Ссылка для оплаты = {quickpay.redirected_url}')
                return f'{quickpay.redirected_url}#preview-options-title'
            elif self.isLava:
                user.bill_id = str(random.randint(10000000, 99999999))
                data = {
                    "sum": summ,
                    "orderId": user.bill_id,
                    "shopId": self.ShopID_CLIENT_ID,
                    "successUrl": f'https://t.me/{BOT_NICK}',
                    "expire":30*60
                }
                data = await self._sort_dict(data)
                jsonStr = json.dumps(data).encode()
                sign = hmac.new(bytes(self.E_mail_URL, 'UTF-8'), jsonStr, hashlib.sha256).hexdigest()

                async with aiohttp.ClientSession(timeout=get_timeount(5)) as session:
                    async with session.post('https://api.lava.ru/business/invoice/create', json=data, headers={'Signature': sign, 'Accept':'application/json', 'Content-Type': 'application/json'}) as response:
                        response_data = await response.json()
                        logger.debug(f'Ссылка для оплаты = {response_data["data"]["url"]}')
                        return response_data["data"]["url"]
            elif self.isCardLink:
                url = 'https://cardlink.link/api/v1/bill/create'
                data = {
                    'amount': summ,
                    'description': user.lang.get('tx_pay_data').format(user_id=user.id_Telegram),
                    'type': 'normal',
                    'shop_id': self.ShopID_CLIENT_ID,
                    'currency_in': 'RUB',
                    'payer_pays_commission': 0,
                    'name': user.lang.get('tx_pay_data').format(user_id=user.id_Telegram),
                }

                async with aiohttp.ClientSession(timeout=get_timeount(5)) as session:
                    async with session.post(url, data=data, headers=self.headers) as response:
                        res = await response.json()
                        logger.debug(f'Ссылка для оплаты = {res}')
                        
                        url = res['link_page_url']
                        user.bill_id = res['bill_id']
                        
                        return url
            elif self.isCryptomus:
                user.bill_id = str(random.randint(100000, 999999))
                result = await self.cryptomus.payments.create_invoice(
                    amount=summ,
                    order_id=user.bill_id,
                    currency=FiatCurrency.RUB,
                    lifetime=3600,
                    url_return=f'https://t.me/{BOT_NICK}',
                    url_success=f'https://t.me/{BOT_NICK}'
                )
                result = result.result
                user.cryptomus_uuid = result.uuid
                logger.debug(f'Ссылка для оплаты = {result.url}')
                return result.url
            elif self.isWalletPay:
                user.bill_id = str(random.randint(100000, 999999))
                order = await self.walletpay.create_order(
                    amount=round(summ / 90, 2),
                    currency_code="USD",
                    description=user.lang.get('tx_pay_data').format(user_id=user.id_Telegram),
                    external_id=user.bill_id,
                    timeout_seconds=30*60,
                    customer_telegram_user_id=user.id_Telegram,
                    return_url=f'https://t.me/{BOT_NICK}',
                )
                logger.debug(f'Ссылка для оплаты = {order.pay_link}')
                user.bill_id = order.id
                return f'{order.pay_link}'
            elif self.isSoftPay:
                # Тарифы 1,3,6 и 12 месяцев
                user.summ_pay = summ
                id_product = ID_PRODUCTS_SOFT_PAY.get(user.tarif_select, '')

                if id_product == '':
                    await send_admins(user.id_Telegram, '🛑Не верно заполнен параметр id_product при создании ссылки для оплаты Soft Pay', f'Сумма: <b>{summ}</b>')
                    return ''

                async with aiohttp.ClientSession(timeout=get_timeount(10)) as session:
                    count = 0
                    while True:
                        count += 1
                        if count > 5:
                            break
                        try:
                            async with session.post('https://api.softpaymoney.com/api/v1/order', json={"product": id_product}, headers={'Authorization': self.API_Key_TOKEN, 'Accept':'application/json', 'Content-Type': 'application/json'}) as response:
                                response_data = await response.json()
                                logger.debug(f'Ссылка для оплаты = {response_data}')
                                user.bill_id = response_data['data']['order']['payer']
                                url = response_data['data']['url']
                                break
                        except Exception as e:
                            logger.warning(f'🛑Ошибка при создании ссылки для оплаты Soft Pay: {e}')
                logger.debug(f'Ссылка для оплаты = {url}')
                return f'{url}'
            elif self.isPayok:
                user.summ_pay = summ
                user.bill_id = str(random.randint(10000000, 99999999))
                result = self.payok.createPay(
                    secret=self.E_mail_URL,
                    amount=summ,
                    payment=user.bill_id,
                    shop=self.id_magazin,
                    desc=user.lang.get('tx_pay_data').format(user_id=user.id_Telegram),
                    currency="RUB",
                    success_url=f'https://t.me/{BOT_NICK}')
                logger.debug(f'Ссылка для оплаты = {result}')
                return result
            elif self.isAaio:
                user.summ_pay = summ
                user.bill_id = str(random.randint(10000000, 99999999))
                result = await self.aaio.generatepaymenturl(
                    amount=summ,
                    order_id=user.bill_id,
                    desc=user.lang.get('tx_pay_data').format(user_id=user.id_Telegram),
                    email=self.E_mail_URL
                )
                logger.debug(f'Ссылка для оплаты = {result}')
                return result
            elif self.isRootPay:
                user.summ_pay = summ
                result = await self.rootpay.create_payment(
                    method='SBP',
                    amount=summ,
                )
                logger.debug(f'Ссылка для оплаты = {result}')
                try:
                    user.amount_one = result['amount_one']
                    user.wallet = result['wallet']
                except:
                    user.amount_one = None
                    user.wallet = None
                user.bill_id = result['session_id']
                return result['url']
            elif self.isFreeKassa:
                count = 0
                while True:
                    try:
                        count += 1

                        ip = SERVERS[random.randint(0, len(SERVERS)-1)]['ip']
                        # payment_id = await DB.GET_VARIABLE('FREEKASSA_COUNT_PAY')
                        # payment_id = payment_id + 1
                        # await DB.UPDATE_VARIABLES('FREEKASSA_COUNT_PAY', payment_id)
                        payment_id = int(str(time.time()).replace('.',''))

                        emails_mail = ('buyo-gixayo33@mail.ru', 'nuje-jifoha95@mail.ru', 'xeki-sopuhe76@mail.ru', 'kuxa-seceho23@mail.ru', 'kelo-konula83@mail.ru', 'yoberu-tede10@mail.ru', 'xamuti_zixi84@mail.ru', 'cukehe-xagu67@mail.ru', 'pik-obuyozi75@mail.ru', 'feteb_ehoto20@mail.ru', 'cen_eciraku27@mail.ru', 'hat-otesoyo2@mail.ru', 'simu-vokiwa96@mail.ru', 'satevah_osi78@mail.ru', 'nohali-xoxo71@mail.ru', 'robose-masu9@mail.ru', 'wow-ozafixi36@mail.ru', 'zuso_hiwini99@mail.ru', 'suyowu_cihe95@mail.ru', 'xetep-osayu93@mail.ru', 'majof-iseso77@mail.ru', 'xulorur-obu34@mail.ru', 'gufok-exoyi41@mail.ru', 'vor_ewulopa77@mail.ru', 'huxe_topese51@mail.ru', 'bomayab_aye35@mail.ru', 'bep-idasika27@mail.ru', 'fedexat-uze19@mail.ru', 'vidof_igike19@mail.ru', 'fofowu_wudi75@mail.ru', 'bemudoy_ohi6@mail.ru', 'niboj_adawi14@mail.ru', 'xeluwep-ote34@mail.ru', 'rogexi-nuzo4@mail.ru', 'lokoh_owuro73@mail.ru', 'piv_ofupiro92@mail.ru', 'joro_wageko6@mail.ru', 'kiwig_oluje18@mail.ru', 'raj-owodumo78@mail.ru', 'pabux_osevi11@mail.ru', 'gudul_amoto40@mail.ru', 'medobat_exa88@mail.ru', 'nepili_yalu92@mail.ru', 'tumahu_joko39@mail.ru', 'rus-imadoco44@mail.ru', 'giya-wiceco48@mail.ru', 'higa-milena1@mail.ru', 'pupayi_noku62@mail.ru', 'pimihog_udu31@mail.ru', 'soyeb_imemi61@mail.ru', 'fid_ufituri91@mail.ru', 'xuge_picowu34@mail.ru', 'zac_ilejobu14@mail.ru', 'moda_vikupe13@mail.ru', 'kak_oxixobe7@mail.ru', 'kuzusog_are33@mail.ru', 'fuzikuw-eyu87@mail.ru', 'sow_ibiveya95@mail.ru', 'jicexuk-ota18@mail.ru', 'noyu-pebisi94@mail.ru', 'jos_ilodoti13@mail.ru', 'poyuhi_lege1@mail.ru', 'cif_agevode35@mail.ru', 'cus-eyuxame48@mail.ru', 'zuya-nibajo78@mail.ru', 'muhofic-ojo27@mail.ru', 'kitad_agawu23@mail.ru', 'gateba_foye37@mail.ru', 'deloxil-ika38@mail.ru', 'zoway-oxano70@mail.ru', 'xezah-ehepe33@mail.ru', 'vevowi-sadu52@mail.ru', 'yade-pumafa9@mail.ru', 'ciso-roxumo10@mail.ru', 'wiw_imaxomo49@mail.ru', 'zice_dezoto2@mail.ru', 'fuz_osohake18@mail.ru', 'vuhow-isumo3@mail.ru', 'xodug-etifa61@mail.ru', 'hofos_inide80@mail.ru', 'soyawis_avi20@mail.ru', 'juyobem_iwo60@mail.ru', 'gavuxob_eka34@mail.ru', 'yihu-nuvaro78@mail.ru', 'rizajuv-ani44@mail.ru', 'suzekom_ehu15@mail.ru', 'fufu_jotifu94@mail.ru', 'gixipi-jubi84@mail.ru', 'ticu-tenuya68@mail.ru', 'vazoris_oju84@mail.ru', 'gamuluv-ati46@mail.ru', 'jexat-ufoga20@mail.ru', 'yiwipa-tumo95@mail.ru', 'nome_jubeja61@mail.ru', 'wefi-cerasi47@mail.ru', 'bowix_ikevu43@mail.ru', 'simi_xunobo22@mail.ru', 'cipajij_iwi39@mail.ru', 'guc-ebirawi51@mail.ru', 'wobumo_kubi32@mail.ru')
                        emails_gmail = ('nawi-juciye28@gmail.com', 'zope_dasitu3@gmail.com', 'roxo-fivese16@gmail.com', 'rin_ugacose72@gmail.com', 'fohus-omixo55@gmail.com', 'hazul_ebiwo3@gmail.com', 'zopopuz-obi15@gmail.com', 'wulo-tolaho67@gmail.com', 'guti-keruxo17@gmail.com', 'votenu_zusa64@gmail.com', 'zacizuw-uga98@gmail.com', 'hapiw-uvoco68@gmail.com', 'tujubob_ihi64@gmail.com', 'yiv_oweyije47@gmail.com', 'cibeciw-uve74@gmail.com', 'yudoda-damu88@gmail.com', 'kesuj_aziho37@gmail.com', 'liyup-ezole54@gmail.com', 'jilub_adija26@gmail.com', 'yelo-mikapi82@gmail.com', 'daciz-edeju38@gmail.com', 'pode_zuwuro66@gmail.com', 'tutoj-esixa6@gmail.com', 'har_ohiduma20@gmail.com', 'siloful-uvi8@gmail.com', 'sapusa_seze14@gmail.com', 'bozode_kegi34@gmail.com', 'jufavad_ofa7@gmail.com', 'zare_doyaca68@gmail.com', 'milahu_hulo14@gmail.com', 'zuraf_ivoyu82@gmail.com', 'cumufu_bude10@gmail.com', 'sux-inejose46@gmail.com', 'fulurel_iza59@gmail.com', 'fixisa_nugu20@gmail.com', 'vej-elurefi51@gmail.com', 'comiso-feda66@gmail.com', 'xot-alesahi59@gmail.com', 'kuzi-zitosu11@gmail.com', 'jexu_jegohe79@gmail.com', 'zaye-zagage66@gmail.com', 'tayom_opuku42@gmail.com', 'denix_onaji81@gmail.com', 'wobexef-iji53@gmail.com', 'huzojel-axo25@gmail.com', 'huhabad_era96@gmail.com', 'ritive-sore66@gmail.com', 'zecuji_cuje21@gmail.com', 'cezivis-evi67@gmail.com', 'vevige-kuzu99@gmail.com', 'peruf_ameyu63@gmail.com', 'sovogel-ezu9@gmail.com', 'sov_ekopapa84@gmail.com', 'lufehok_aco89@gmail.com', 'pumece-hopi97@gmail.com', 'rej-epevenu49@gmail.com', 'cogusef-iju38@gmail.com', 'cafitav_oni7@gmail.com', 'mudelu_sido89@gmail.com', 'ceb_inabipa95@gmail.com', 'faf_enomobe86@gmail.com', 'xehen_inifo10@gmail.com', 'tobek-ugofa96@gmail.com', 'wama-pujaxi31@gmail.com', 'foke_sokovu52@gmail.com', 'domefi_fidi59@gmail.com', 'codaji-nuji39@gmail.com', 'weka-xanari18@gmail.com', 'bavi-tarowe14@gmail.com', 'fagera_yupu18@gmail.com', 'sodiw_uxoge90@gmail.com', 'zume-jeliba90@gmail.com', 'toriju_bico34@gmail.com', 'javid-aliko5@gmail.com', 'nojusi_povi54@gmail.com', 'rajixe_kehi22@gmail.com', 'nuci_jimeku49@gmail.com', 'cad-axiduwa63@gmail.com', 'xoyug-efanu26@gmail.com', 'pop_akozoka80@gmail.com', 'til-iwemihi86@gmail.com', 'vatoyez_ago95@gmail.com', 'daviriy_owa60@gmail.com', 'tux-arofepo14@gmail.com', 'cuxutuc_aze51@gmail.com', 'poseb-ucasa4@gmail.com', 'ciwovaj-uza61@gmail.com', 'cicoto-laku50@gmail.com', 'noxa_minacu71@gmail.com', 'numoz_ocaga69@gmail.com', 'wiwubal-ate59@gmail.com', 'xiv-upupiye24@gmail.com', 'tinosoj-uha76@gmail.com', 'fug_ihexoyo87@gmail.com', 'fefub_awoso52@gmail.com', 'tuyuzuz-ofa2@gmail.com', 'jodiwer_oyi94@gmail.com', 'sij-erugeye83@gmail.com', 'lokumi-voga30@gmail.com', 'piselex_ove64@gmail.com')
                        email_yandex = ('halob_okura66@yandex.ru', 'dotule-zitu61@yandex.ru', 'holinoh_uji6@yandex.ru', 'woy_ogufexo4@yandex.ru', 'paxewu_kuwu46@yandex.ru', 'texiy_oxoki53@yandex.ru', 'cafowej-odi54@yandex.ru', 'nujun-afani89@yandex.ru', 'xuxul_ebinu3@yandex.ru', 'ziwuga_titu28@yandex.ru', 'lex_owakona47@yandex.ru', 'sibub_imati31@yandex.ru', 'susaj-ocepu55@yandex.ru', 'cage-vobabi65@yandex.ru', 'vot-emuwodo33@yandex.ru', 'vac_uxukake93@yandex.ru', 'sow_ogedehu98@yandex.ru', 'gexit_exuhi34@yandex.ru', 'zusima_naki32@yandex.ru', 'doh-upagodu72@yandex.ru', 'mos_odawahu77@yandex.ru', 'zezulik_era29@yandex.ru', 'hakoh-ibozi91@yandex.ru', 'geju_tovori83@yandex.ru', 'sawefof-ata70@yandex.ru', 'lakeyip_ego67@yandex.ru', 'roku-runimi89@yandex.ru', 'nimiyim-ufe18@yandex.ru', 'vodu-rupepu91@yandex.ru', 'gemoc_atosi94@yandex.ru', 'yub-oxugaja20@yandex.ru', 'hak_upozujo38@yandex.ru', 'gepisan_eli93@yandex.ru', 'yuxeliw_igu61@yandex.ru', 'pujir_enezi73@yandex.ru', 'penok-exini98@yandex.ru', 'zomam_uxayu6@yandex.ru', 'jal-uloragi41@yandex.ru', 'dizabom_ogu25@yandex.ru', 'mogepo_mazo42@yandex.ru', 'cixe-xoxopa84@yandex.ru', 'koremu_ruhe24@yandex.ru', 'modet-asumi14@yandex.ru', 'yebeg_idaze15@yandex.ru', 'boyu-xarire30@yandex.ru', 'kot_icikazo12@yandex.ru', 'foweb-egozo2@yandex.ru', 'desam-irova76@yandex.ru', 'kaxuko-cafo77@yandex.ru', 'pihagoj_oha10@yandex.ru', 'xab_ofecavu84@yandex.ru', 'vuwo_fivixa33@yandex.ru', 'lokisi-boni54@yandex.ru', 'redumuv-agi88@yandex.ru', 'mavamos-era76@yandex.ru', 'hunay_ecisu53@yandex.ru', 'dikocoj_iva24@yandex.ru', 'yemox-exore23@yandex.ru', 'jiviyi_timi75@yandex.ru', 'moyife_yona91@yandex.ru', 'kohobo_peho52@yandex.ru', 'nome-yaxupe89@yandex.ru', 'yadanug-iro79@yandex.ru', 'fofu-tuzuvu63@yandex.ru', 'yaz-ucuzulo21@yandex.ru', 'dipole-wugu8@yandex.ru', 'him_opigiku50@yandex.ru', 'jole-bomope81@yandex.ru', 'neb-osaneju5@yandex.ru', 'seronug_ale31@yandex.ru', 'koze-takafi23@yandex.ru', 'rufef-aceso25@yandex.ru', 'rakavoc-ahe40@yandex.ru', 'xor_epedili33@yandex.ru', 'wamumu-ziza7@yandex.ru', 'ribe-rowawu83@yandex.ru', 'guxad-etohe94@yandex.ru', 'nuy-adixalo40@yandex.ru', 'fotuya_rova79@yandex.ru', 'pusije_zevu31@yandex.ru', 'juge-rexani16@yandex.ru', 'rom_aboneja21@yandex.ru', 'pazajax_iso51@yandex.ru', 'cifu-sajiha69@yandex.ru', 'toluy-uviyu42@yandex.ru', 'vuwab-ovigu96@yandex.ru', 'popoko-fuli66@yandex.ru', 'bebane-wife68@yandex.ru', 'bonup_ipusi38@yandex.ru', 'fitoye_hife87@yandex.ru', 'vuc_udukozi47@yandex.ru', 'dixev-oxodi4@yandex.ru', 'jomic-oboba88@yandex.ru', 'bix-egerele2@yandex.ru', 'wowuy-irezo36@yandex.ru', 'colu-ticoso8@yandex.ru', 'desuwe-zaja40@yandex.ru', 'nekob-areso70@yandex.ru', 'picodaz_ewu47@yandex.ru', 'wudoce-tahu11@yandex.ru')
                        email_inbox = ('sufisaw_usa3@inbox.ru', 'sise-xiyuwu71@inbox.ru', 'zici-fuvoxu32@inbox.ru', 'vud-apihaco62@inbox.ru', 'yubuyuh-eje36@inbox.ru', 'ced-oneyica73@inbox.ru', 'tizok_axewi63@inbox.ru', 'jevigag_aso17@inbox.ru', 'rep-akozife69@inbox.ru', 'kubohor-oji45@inbox.ru', 'gimup-axoci16@inbox.ru', 'raboxa_moka69@inbox.ru', 'ken-emegizi41@inbox.ru', 'widenul-ilu75@inbox.ru', 'gumij-eyohu8@inbox.ru', 'bos-iguwowi5@inbox.ru', 'pezav_itibe16@inbox.ru', 'loze-mepegi90@inbox.ru', 'fib_abuxihi2@inbox.ru', 'cilutet-ena33@inbox.ru', 'suk-otazazo99@inbox.ru', 'zuja_jixigi60@inbox.ru', 'red-eduseyu16@inbox.ru', 'natom-axuca81@inbox.ru', 'jiyise_xuri73@inbox.ru', 'nuni_resebo65@inbox.ru', 'raka_hacudo68@inbox.ru', 'xok-uzokusu41@inbox.ru', 'licenot_ujo28@inbox.ru', 'kufit_ahugi84@inbox.ru', 'hic-irosihi3@inbox.ru', 'jikitu_yeme66@inbox.ru', 'fofusan_uyo14@inbox.ru', 'namozoh_eli36@inbox.ru', 'vij_ewohacu11@inbox.ru', 'zigozay_ivu8@inbox.ru', 'secepu-xuto84@inbox.ru', 'fon-iwumogo23@inbox.ru', 'jahot-asapu74@inbox.ru', 'hon_uyirego39@inbox.ru', 'degidip_asa50@inbox.ru', 'jamova_xopo77@inbox.ru', 'kuta_wibazi40@inbox.ru', 'keraxuj_oro77@inbox.ru', 'cudug-ebake40@inbox.ru', 'puc-icaloka27@inbox.ru', 'jereza_jadu32@inbox.ru', 'laluv_ayiye67@inbox.ru', 'dud-etoxugu60@inbox.ru', 'ketef_useku29@inbox.ru', 'mejo_jexaku71@inbox.ru', 'luz_efecina74@inbox.ru', 'gif-onapoxa80@inbox.ru', 'wumus-asomi37@inbox.ru', 'meja_wukeza48@inbox.ru', 'wawan-osude98@inbox.ru', 'himit_okexi59@inbox.ru', 'yonav_ayuvu66@inbox.ru', 'kituf_iwoku31@inbox.ru', 'vozumum-uhu26@inbox.ru', 'coki-wutetu52@inbox.ru', 'mubop_adape89@inbox.ru', 'zobo_mimixa13@inbox.ru', 'heloy-iziwi15@inbox.ru', 'yuci_vugema8@inbox.ru', 'xixevok-oge34@inbox.ru', 'kugiyix-ado95@inbox.ru', 'zuza_yiduwo79@inbox.ru', 'nimodir_uno50@inbox.ru', 'vob-osozimu6@inbox.ru', 'muzes-ofefo32@inbox.ru', 'yit-ikafaba94@inbox.ru', 'zozoyi-xace8@inbox.ru', 'nih_imucuya19@inbox.ru', 'fic-ojoxuja50@inbox.ru', 'teyek_izena47@inbox.ru', 'zupuca-gita59@inbox.ru', 'suko_vobufi7@inbox.ru', 'coki_somare96@inbox.ru', 'wegam-alalu65@inbox.ru', 'rir-elevugu39@inbox.ru', 'yodezug-ezo25@inbox.ru', 'yuso_ninule82@inbox.ru', 'ruvajev_eyi42@inbox.ru', 'fijeka_haga65@inbox.ru', 'xim_ovenase8@inbox.ru', 'few_ayawedi36@inbox.ru', 'litup_ipugu80@inbox.ru', 'yajix_idoku14@inbox.ru', 'xevifoh-iwe99@inbox.ru', 'zujas_usiyo86@inbox.ru', 'dofo_yijefa56@inbox.ru', 'sulay_uyaro78@inbox.ru', 'jizava_bico33@inbox.ru', 'johu_xocahe39@inbox.ru', 'mozav-atixi27@inbox.ru', 'tekanux_ode29@inbox.ru', 'fed_uyuceza61@inbox.ru', 'balidup_eli62@inbox.ru', 'lubu_varemo54@inbox.ru')
                        email_bk = ('zapay-onuco96@bk.ru', 'zajar_owibu58@bk.ru', 'guk_irujofe14@bk.ru', 'wolucu-waci4@bk.ru', 'nec-ebemosi34@bk.ru', 'got_ifarixe82@bk.ru', 'ceba_jacogi44@bk.ru', 'zupituw_awi2@bk.ru', 'guz-unenuca75@bk.ru', 'rulur-ojuca32@bk.ru', 'piw-uzotaju51@bk.ru', 'xukawiz-udo73@bk.ru', 'gunib_exavu85@bk.ru', 'heyapob-etu71@bk.ru', 'venonu-lava98@bk.ru', 'wepikap-aga13@bk.ru', 'moz_esowefa66@bk.ru', 'horalum-ulo23@bk.ru', 'copo_higidu34@bk.ru', 'niy-axulixu65@bk.ru', 'baxide_cino69@bk.ru', 'goritu_vozu65@bk.ru', 'goximu-miko54@bk.ru', 'leni_sutiru86@bk.ru', 'xaga-palihu95@bk.ru', 'jum-atopuxi74@bk.ru', 'yix_uzanoni3@bk.ru', 'tofadum_oji55@bk.ru', 'moy-apisuvu36@bk.ru', 'cuboli_faji18@bk.ru', 'xilayeh-ihi8@bk.ru', 'zanevuv-iga20@bk.ru', 'bosimor-obo50@bk.ru', 'marat_ayuro9@bk.ru', 'suxo-niloye20@bk.ru', 'zono-behuja77@bk.ru', 'tuhuras_oke45@bk.ru', 'tupuxas_ena98@bk.ru', 'mug-ezumavi84@bk.ru', 'gutig_otefu76@bk.ru', 'her-elukahu6@bk.ru', 'weluju-cago6@bk.ru', 'goya-kixoda8@bk.ru', 'borut-ezino8@bk.ru', 'ruson-inoxo21@bk.ru', 'fele-kefire93@bk.ru', 'ditid-efebi6@bk.ru', 'sekulub-ojo25@bk.ru', 'nit_iwaliwo86@bk.ru', 'boda-gemoku3@bk.ru', 'nijase-fasa35@bk.ru', 'xulil-ejina99@bk.ru', 'xunec_ujula52@bk.ru', 'dufo_vasowu41@bk.ru', 'boyad-umaco65@bk.ru', 'wez-epuzecu88@bk.ru', 'cuxake_cizu53@bk.ru', 'cuvimox-oxa52@bk.ru', 'gihe_fulowe52@bk.ru', 'hukeyi_hisi74@bk.ru', 'jibu_dusuwi39@bk.ru', 'cabo_mekuva25@bk.ru', 'xak_odedafo93@bk.ru', 'dipole_hafe85@bk.ru', 'pusayi-xiko28@bk.ru', 'gade-polare55@bk.ru', 'dehali_luke86@bk.ru', 'rowu_cuhonu16@bk.ru', 'tanowa_yacu17@bk.ru', 'lezu-voyafo45@bk.ru', 'petapu_rahu71@bk.ru', 'zifan_oxisi5@bk.ru', 'yil-iruxaka18@bk.ru', 'mabuhi_yufi15@bk.ru', 'rehah_imimo93@bk.ru', 'nenoyay-ape25@bk.ru', 'taw_ojacite22@bk.ru', 'cohot-iyego91@bk.ru', 'valim-oyaro29@bk.ru', 'cucaj_uguba6@bk.ru', 'rogayu-dovo72@bk.ru', 'lokug-ijoni91@bk.ru', 'yoje_dugazu34@bk.ru', 'yupezah-eci7@bk.ru', 'jozoyu-vowe98@bk.ru', 'muyelen-ewo48@bk.ru', 'maligid_agu53@bk.ru', 'bireju-hesi68@bk.ru', 'cuk_uwebiha28@bk.ru', 'fexeno-ruge34@bk.ru', 'buwam_araho47@bk.ru', 'jitagi_zoro80@bk.ru', 'rec_uliketa45@bk.ru', 'nax-otocaki86@bk.ru', 'wefefi_yebo45@bk.ru', 'pujup_ulefi17@bk.ru', 'vajaxe-yasu60@bk.ru', 'wiseyu_kewe19@bk.ru', 'figex_izabu12@bk.ru', 'kag-axiniku18@bk.ru')

                        emails = emails_mail + emails_gmail + email_yandex + email_inbox + email_bk
                        email = emails[random.randint(0, len(emails)-1)]

                        order = self.freekassa.create_order(36, email, ip, summ, payment_id=payment_id, success_url=f'https://t.me/{BOT_NICK}', failure_url=f'https://t.me/{BOT_NICK}')
                        break
                    except Exception as e:
                        logger.warning(f'{user.id_Telegram}: 🛑Ошибка в create_pay -> isFreeKassa -> {e}')

                        if count > 5:
                            await Print_Error()
                            break

                        await asyncio.sleep(0.5)

                order_id = order['orderId']
                url = order['location']
                logger.debug(f'Ссылка для оплаты = {url}')
                user.bill_id = str(order_id)
                return f'{url}'
            elif self.isXTR:
                user.bill_id = str(random.randint(100000, 999999))
                user.summ_pay = summ

                result = await bot.send_invoice(
                    chat_id=user.id_Telegram,
                    title=user.lang.get('tx_pay_trx_title'),
                    description=user.lang.get('tx_pay_data').format(user_id=user.id_Telegram),
                    provider_token='',
                    prices=[
                        LabeledPrice(
                            label="XTR", 
                            amount=int(summ / KURS_XTR)
                        )
                    ],
                    payload=user.bill_id,
                    currency="XTR",
                )
                logger.debug(f'Данные для оплаты TRX = {result}')
                return "XTR"
            else:
                await self.__error_no_wallet__()
                return ''
        except:
            await Print_Error()

    async def check_is_pay(self, user, bill_id):
        if bill_id in ('---',''):
            logger.warning(f'не верный bill_id = {bill_id}')
            return (False, 0, '')
        if self.isYooKassa:
            try:
                logger.debug(f'Проверяю bill_id Ю.Касса === {bill_id}')
                try:
                    result = Payment.find_one(bill_id)
                except:
                    await sleep(random.randint(10,30)/10)
                    result = Payment.find_one(bill_id)
                logger.debug(f'Payment.find_one(bill_id="{bill_id}"): {result}')
                if bool(result.paid):
                    logger.debug(f'Оплата прошла = {result.json()}')
                    logger.debug(int(str(result.amount.value).split('.')[0]))
                    return (True, int(str(result.amount.value).split('.')[0]), f'{bill_id}')
                else:
                    return (False, 0, '')
            except Exception as e:
                logger.warning('Оплата не прошла')
                return (False, 0, '')
        elif self.isTinfkoffPay:
            try:
                logger.debug(f'Проверяю bill_id Tinkoff Pay === {bill_id}')
                result = self.tinkoff.state(bill_id)
                logger.debug(f'self.tinkoff.state(bill_id="{bill_id}"): {result}')
                if result['Status'] == 'CONFIRMED':
                    try:
                        RebillId = result['RebillId']
                    except:
                        RebillId = ''
                    logger.debug(f'Оплата прошла = {result}')
                    return (True, int(result['Amount'] / 100), f'{bill_id}', str(RebillId))
                elif result['Status'] == 'REJECTED':
                    return (False, -1, '')
                else:
                    return (False, 0, '')
            except Exception as e:
                logger.warning('Оплата не прошла')
                return (False, 0, '')
        elif self.isLava:
            try:
                logger.debug(f'Проверяю bill_id Lava === {bill_id}')
                data = {
                    "orderId": bill_id,
                    "shopId": self.ShopID_CLIENT_ID
                }
                data = await self._sort_dict(data)
                jsonStr = json.dumps(data).encode()
                sign = hmac.new(bytes(self.E_mail_URL, 'UTF-8'), jsonStr, hashlib.sha256).hexdigest()
                
                async with aiohttp.ClientSession(timeout=get_timeount(5)) as session:
                    async with session.post('https://api.lava.ru/business/invoice/status', json=data, headers={'Signature': sign, 'Accept':'application/json', 'Content-Type': 'application/json'}) as response:
                        response_data = await response.json()
                        logger.debug(f'Lava bill_id = {bill_id}: {response_data["data"]}')
                        if response_data["data"]["status"] == "success":
                            return (True, response_data["data"]["amount"], response_data["data"]['id'])
                        else:
                            return (False, 0, '')
            except Exception as e:
                logger.warning('Оплата не прошла')
                return (False, 0, '')
        elif self.isCardLink:
            try:
                logger.debug(f'Проверяю bill_id CardLink === {bill_id}')
                url = f'https://cardlink.link/api/v1/bill/status?id={bill_id}'
                
                async with aiohttp.ClientSession(timeout=get_timeount(5)) as session:
                    async with session.get(url, headers=self.headers) as response:
                        res = await response.json()
                        logger.debug(f'CardLink bill_id = {bill_id}: {res}')
                        
                        if res["status"] == "SUCCESS":
                            return (True, int(float(res["amount"])), '')
                        else:
                            return (False, 0, '')
            except Exception as e:
                logger.warning('Оплата не прошла')
                return (False, 0, '')
        elif self.isYooMoney:
            try:
                history = self.client.operation_history(label=bill_id)
                history.data = await history._request()
                history.get()
                history = history.operations
            except Exception as error:
                if not 'Connection aborted' in str(error):
                    await self.__error__(error)
                return (False, 0, '')
            if history == []:
                logger.debug(f'Проверяю bill_id Ю.Money === {bill_id}')
                return (False, 0, '')
            else:
                for operation in history:
                    logger.debug('-------------------')
                    logger.debug(f'Операция: {operation.operation_id}')
                    logger.debug(f'\tСтатус     --> {operation.status}')
                    logger.debug(f'\tДата и время   --> {operation.datetime}')
                    logger.debug(f'\tНазвание      --> {operation.title}')
                    logger.debug(f'\tСумма     --> {operation.amount}')
                    logger.debug(f'\tLabel      --> {operation.label}')
                    logger.debug('-------------------')
                    if operation.status == 'success':
                        logger.debug(f'✅Операция прошла успешно bill_id = {bill_id}')
                        return (True, int(str(operation.amount).split('.')[0]), f'{operation.title}')
                    else:
                        logger.warning(f'🛑Операция не прошла bill_id = {bill_id}, operation.status = {operation.status}')
                        return (False, 0, '')
        elif self.isCryptomus:
            try:
                logger.debug(f'Проверяю bill_id Cryptomus === {bill_id}')
                result = await self.cryptomus.payments.info(user.cryptomus_uuid, bill_id)
                result = result.result
                logger.debug(f'self.cryptomus.payments.info(user.cryptomus_uuid="{user.cryptomus_uuid}", bill_id={bill_id}): {result}')
                if result.payment_status == 'paid':
                    logger.debug(f'Оплата прошла = {result}')
                    return (True, int(result.payer_amount_exchange_rate * result.payer_amount), f'from: {result.from_}, txid: {result.txid}')
                else:
                    return (False, 0, '')
            except Exception as e:
                logger.warning('Оплата не прошла')
                return (False, 0, '')
        elif self.isWalletPay:
            try:
                logger.debug(f'Проверяю bill_id Wallet Pay === {bill_id}')
                result = await self.walletpay.get_order_preview(order_id=f'{bill_id}')
                logger.debug(f'self.walletpay.get_order_preview(bill_id="{bill_id}"): {result}')
                if result.status == 'PAID':
                    logger.debug(f'Оплата прошла = {result}')
                    return (True, int(int(result.amount.amount.split('.')[0]) * KURS_RUB), f'{bill_id}')
                else:
                    return (False, 0, '')
            except Exception as e:
                logger.warning(f'Оплата не прошла: {e}')
                return (False, 0, '')
        elif self.isSoftPay:
            try:
                logger.debug(f'Проверяю bill_id Soft Pay === {bill_id}')
                async with aiohttp.ClientSession(timeout=get_timeount(5)) as session:
                    async with session.get('https://api.softpaymoney.com/api/v1/order/' + bill_id, headers={'Authorization': self.API_Key_TOKEN, 'Accept':'application/json', 'Content-Type': 'application/json'}) as response:
                        result = await response.json()
                        logger.debug(f'Проверка статуса платежа Soft Pay (bill_id="{bill_id}"): {result}')
                        if result['data'][0]['status'] == 'CONFIRMED':
                            logger.debug(f'Оплата прошла = {result}')
                            try:
                                summ = user.summ_pay
                            except:
                                summ = 0
                            return (True, summ, f'{bill_id}')
                        else:
                            return (False, 0, '')
            except Exception as e:
                logger.warning(f'Оплата не прошла: {e}')
                return (False, 0, '')
        elif self.isPayok:
            try:
                logger.debug(f'Проверяю bill_id Payok === {bill_id}')
                result = await self.payok.getTransaction(self.api_id, self.API_Key_TOKEN, self.id_magazin, payment=bill_id)
                logger.debug(f'PayOk bill_id = {bill_id}: {result}')
                if result['1']['transaction_status'] == '1':
                    try:
                        summ = user.summ_pay
                    except:
                        summ = 0
                    return (True, summ, result['1']['transaction'])
                else:
                    return (False, 0, '')
            except Exception as e:
                logger.warning(f'bill_id: {bill_id} - Оплата PayOk не прошла: {e}')
                return (False, 0, '')
        elif self.isAaio:
            try:
                logger.debug(f'Проверяю bill_id Aaio === {bill_id}')
                result = await self.aaio.getorderinfo(bill_id)
                logger.debug(f'Aaio bill_id = {bill_id}: {result}')
                if result.status == 'success':
                    try:
                        summ = int(result.profit)
                    except:
                        summ = 0
                    return (True, summ, result.id)
                else:
                    return (False, 0, '')
            except Exception as e:
                logger.warning(f'bill_id: {bill_id} - Оплата Aaio не прошла: {e}')
                return (False, 0, '')
        elif self.isRootPay:
            try:
                logger.debug(f'Проверяю bill_id RootPay === {bill_id}')
                result = await self.rootpay.get_payment_info(bill_id)
                logger.debug(f'RootPay bill_id = {bill_id}: {result}')
                result = result['payments'][0]
                if result['status'] == 'paid':
                    try:
                        summ = int(result['amount'])
                    except:
                        summ = 0
                    return (True, summ, bill_id)
                else:
                    return (False, 0, '')
            except Exception as e:
                logger.warning(f'bill_id: {bill_id} - Оплата RootPay не прошла: {e}')
                return (False, 0, '')
        elif self.isFreeKassa:
            try:
                logger.debug(f'Проверяю bill_id FreeKassa === {bill_id}')
                result = self.freekassa.get_orders(order_id=int(bill_id))
                logger.debug(f'FreeKassa bill_id = {bill_id}: {result}')
                
                orders = result['orders']
                order = orders[0]
                status = order['status']
                amount = order['amount']
                if status and status == 1:
                    try:
                        summ = int(float(amount))
                    except:
                        summ = 0
                    return (True, summ, bill_id)
                else:
                    return (False, 0, '')
            except Exception as e:
                logger.warning(f'bill_id: {bill_id} - Оплата FreeKassa не прошла: {e}')
                return (False, 0, '')
        elif self.isXTR:
            try:
                logger.debug(f'Проверяю bill_id XTR === {bill_id}')
                amount = xtr_pay_success_users.get(user.id_Telegram, None)
                if amount:
                    logger.debug(f'Оплата прошла amount = {amount} XTR')
                    
                    try: xtr_pay_success_users.pop(user.id_Telegram)
                    except: pass
                    
                    return (True, amount * KURS_XTR, bill_id)
                else:
                    return (False, 0, '')
            except Exception as e:
                logger.warning('Оплата не прошла')
                return (False, 0, '')
        else:
            await self.__error_no_wallet__()
            logger.warning(f'🛑Операция не прошла (await self.__error_no_wallet__()) bill_id = {bill_id}')
            return (False, 0, '')

    async def rec_pay(self, user, summ, payment_method_id):
        try:
            data = None
            user_id = user.id_Telegram
            if payment_method_id != '':
                data = {
                    "amount": {
                        "value": f"{summ}.00",
                        "currency": "RUB"
                    },
                    "capture": True,
                    "payment_method_id": payment_method_id,
                    "description": f"Автоматическая оплата заказа user_id ({user_id})",
                    "receipt": {
                        "customer": {
                            "email": self.E_mail_URL
                        },
                        "items": [
                            {
                                "description": user.lang.get('tx_pay_data').format(user_id=user.id_Telegram),
                                "quantity": "1",
                                "amount": {
                                    "value": f"{summ}.00",
                                    "currency": "RUB"
                                },
                                "vat_code": "1"
                            },
                        ]
                    }
                }
                payment = Payment.create(data)
                user.bill_id = payment.id
                logger.debug(f'✅{user_id}: user.bill_id = {user.bill_id}, payment = {payment}')
                logger.debug(f'✅{user_id}: Создал ссылку rec_payment = {payment.json()}')
                if payment.cancellation_details and payment.cancellation_details.reason:
                    reason = payment.cancellation_details.reason
                    logger.warning(f'{user_id}: 🛑Автоматическая оплата не прошла: {reason}')
                    return False
                return payment.paid
            else:
                logger.debug(f'{user_id}: 🛑Не удалось создать ссылку rec_payment, т.к. payment_method_id = пустое')
                return False
        except Exception as e:
            logger.warning(f'{user_id} - (data = {data}) - 🛑Ошибка при создании ссылки rec_payment: {e}')
            return False

    async def rec_pay_tinkoff(self, user, summ, RebillId):
        try:
            logger.debug(f'Создаю реккурентную оплату Tinkoff Pay (RebillId = {RebillId}, user_id = {user.id_Telegram})')
            order_id = f'{int(datetime.now().timestamp())}{random.randint(1000,9999)}'
            summ = str(int(summ*100))

            payment_data = {
                'TerminalKey': self.API_Key_TOKEN,
                'OrderId': order_id,
                'Amount': summ,
                "Description": user.lang.get('tx_pay_data').format(user_id=user.id_Telegram),
                'Receipt': {
                    'Phone': PHONE_NUMBER,
                    'Email': self.E_mail_URL,
                    'Taxation': 'usn_income',
                    'Items': [{
                        'Name': user.lang.get('tx_pay_data').format(user_id=user.id_Telegram),
                        'Quantity': '1',
                        'Amount': summ,
                        'Tax': 'none',
                        'Price': summ,
                    },]
                },
                "SuccessURL": f'https://t.me/{BOT_NICK}',
            }

            result = self.tinkoff.init(payment_data)
            logger.debug(f'Создал ссылку для оплаты bill_id = {result["PaymentId"]}')
            user.bill_id = result['PaymentId']

            # Вызвать метод Charge с параметром RebillId, полученным в п.3, и параметром PaymentId
            logger.debug(f'Вызываю метод Charge с параметром RebillId, полученным в п.3, и параметром PaymentId (user_id = {user.id_Telegram})')
            payment_data = {
                'TerminalKey': self.API_Key_TOKEN,
                'PaymentId': user.bill_id,
                'RebillId': RebillId
            }

            result = self.tinkoff._call('Charge', payment_data)
            if result['Success'] == True:
                return (True, int(result['Amount'] / 100), f'{user.bill_id}', str(RebillId))
            else:
                return (False, 0, '')    
        except:
            await Print_Error()
    
    async def get_history(self, count_records=30):
        if self.isYooKassa:
            operacii = []
            cursor = None
            data = {"limit": count_records * 2}
            while True:
                params = data
                if cursor:
                    params['cursor'] = cursor
                try:
                    try:
                        res = Payment.list(params)
                    except:
                        await sleep(random.randint(10,30)/10)
                        res = Payment.list(params)
                    for item in res.items:
                        if str(item.status) == 'succeeded':
                            summ = str(item.income_amount.value) # Сумма пришла
                            date_create = str(item.created_at.replace('T',' ').split('.')[0].replace('-','/')) # Дата создания
                            description = str(item.description) 
                            id_order = str(item.id.split('-')[-1])

                            if len(operacii) > count_records - 1:
                                break
                            operacii.append((id_order, date_create, summ, description))

                    if not res.next_cursor:
                        break
                    else:
                        cursor = res.next_cursor
                except:
                    await Print_Error()
                    break

            text = f'📋Последние {count_records} операций Ю.Касса:\n\n'
            for index, operaciya in enumerate(operacii):
                text += f"<b>{index+1}. {operaciya[3]}</b>\n"
                text += f"Статус: <b>Успешно</b>\n"
                text += f"Сумма: <b>{operaciya[2]}₽</b>\n"
                text += f"Время: <b>{operaciya[1]}</b>\n"
                text += f"Код оплаты: <b><code>{operaciya[0]}</code></b>\n"
                text += '➖➖➖➖➖➖➖➖➖➖➖➖\n'

            if text != f'📋Последние {count_records} операций Ю.Касса:\n\n':
                return text
            else:
                return '⚠️Операций не найдено!'
        elif self.isYooMoney:
            try:
                history = self.client.operation_history(type='deposition', records=count_records)
                history.data = await history._request()
                history.get()
                history = history.operations
            except Exception as error:
                await self.__error__(error)
                return False
            if history == []:
                logger.warning(f'🛑Операций не было найдено!')
                return False
            else:
                text = f'📋Последние {count_records} операций Ю.Money:\n\n'
                for index, operation in enumerate(history):
                    text += f"<b>{index+1}. {operation.title}</b>\n"
                    text += f"Статус: <b>{'Успешно' if str(operation.status) == 'success' else operation.status}</b>\n"
                    text += f"Сумма: <b>{operation.amount}₽</b>\n"
                    text += f"Время: <b>{operation.datetime}</b>\n"
                    text += f"Код оплаты: <b>{operation.label if not operation.label is None else 'Нет'}</b>\n"
                    text += '➖➖➖➖➖➖➖➖➖➖➖➖\n'

                if text != f'📋Последние {count_records} операций Ю.Money:\n\n':
                    return text
                else:
                    return '⚠️Операций не найдено!'
        elif self.isTinfkoffPay:
            return '⚠️В Tinkoff Pay нет возможности получить операции!'
        elif self.isLava:
            return '⚠️В Lava нет возможности получить операции!'
        elif self.isCardLink:
            try:
                date_start = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
                date_finish = datetime.now().strftime('%Y-%m-%d')
                
                url = f'https://cardlink.link/api/v1/bill/search?start_date={date_start}&finish_date={date_finish}'
                
                async with aiohttp.ClientSession(timeout=get_timeount(5)) as session:
                    async with session.get(url, headers=self.headers) as response:
                        res = await response.json()
                        operations = res['data']
            except Exception as error:
                await self.__error__(error)
                return False

            if operations == []:
                logger.warning(f'🛑Операций не было найдено!')
                return False
            else:
                text = f'📋Последние {count_records} операций CardLink:\n\n'
                count_success = 0
                for operation in operations:
                    id = operation['id']
                    status = operation['status']
                    summ = operation['amount']
                    created_at = operation['created_at']
                    
                    if status == 'SUCCESS':
                        count_success += 1
                        if count_success > count_records:
                            break
                    else:
                        continue
                    
                    text += f"<b>{count_success}. {id}</b>\n"
                    text += f"Статус: <b>{'Успешно' if status == 'SUCCESS' else status}</b>\n"
                    text += f"Сумма: <b>{summ}₽</b>\n"
                    text += f"Время: <b>{created_at}</b>\n"
                    text += '➖➖➖➖➖➖➖➖➖➖➖➖\n'

                if text != f'📋Последние {count_records} операций CardLink:\n\n':
                    return text
                else:
                    return '⚠️Операций не найдено!'
        elif self.isCryptomus:
            try:
                history = data = self.cryptomus.payments._get_func_params(locals())
                response = await self.cryptomus.payments._make_request("v1/payment/list", data=data)
                history = response['result']['items']
            except Exception as error:
                await self.__error__(error)
                return False
            if history == []:
                logger.warning(f'🛑Операций не было найдено!')
                return False
            else:
                temp_count = 0
                text = f'📋Последние {count_records} операций Cryptomus:\n\n'
                for operation in history:
                    temp_count += 1
                    if temp_count > count_records:
                        break
                    text += f"<b>{temp_count}. {operation['uuid']}</b>\n"
                    text += f"Статус: <b>{'Успешно' if operation['status'] else operation['status']}</b>\n"
                    text += f"Сумма: <b>{int(float(operation['payer_amount_exchange_rate']))}₽</b>\n"
                    text += f"Время: <b>{operation['created_at'].split('+')[0]}</b>\n"
                    text += f"Код оплаты: <b>{operation['order_id']}</b>\n"
                    text += f"Txid: <code>{operation['txid']}</code>"
                    text += f"С кошелька: <code>{operation['from']}</code>"
                    text += '➖➖➖➖➖➖➖➖➖➖➖➖\n'

                if temp_count > 0:
                    return text
                else:
                    return '⚠️Операций не найдено!'
        elif self.isWalletPay:
            try:
                history = await self.walletpay.get_order_list(offset=0, count=count_records)
            except Exception as error:
                await self.__error__(error)
                return False
            if history == []:
                logger.warning(f'🛑Операций не было найдено!')
                return False
            else:
                text = f'📋Последние {count_records} операций WalletPay:\n\n'
                for index, operation in enumerate(history):
                    text += f"<b>{index+1}. {operation.id}</b>\n"
                    text += f"Статус: <b>{'Успешно' if str(operation.status) == 'PAID' else operation.status}</b>\n"
                    text += f"Сумма: <b>{operation.amount}₽</b>\n"
                    text += f"Время: <b>{operation.payment_date_time}</b>\n"
                    text += f"Код оплаты: <b>{operation.extrenal_id if operation.extrenal_id else 'Нет'}</b>\n"
                    text += '➖➖➖➖➖➖➖➖➖➖➖➖\n'

                if text != f'📋Последние {count_records} операций WalletPay:\n\n':
                    return text
                else:
                    return '⚠️Операций не найдено!'
        elif self.isSoftPay:
            return '⚠️В Soft Pay нет возможности получить операции!'
        elif self.isPayok:
            try:
                history = await self.payok.getTransaction(self.api_id, self.API_Key_TOKEN, self.id_magazin)
            except Exception as error:
                await self.__error__(error)
                return False
            
            if history == []:
                logger.warning(f'🛑Операций не было найдено!')
                return False
            else:
                text = f'📋Последние {count_records} операций Payok:\n\n'
                index = 0
                index_dop = 1
                for operation in history.keys():
                    index = index + 1

                    if index_dop > count_records:
                        break

                    oper = history.get(str(index), None)
                    if oper:
                        operation_id = oper['transaction']
                        status = oper['transaction_status'] == '1'
                        summ = oper['amount_profit']
                        date = oper['pay_date']
                        code = oper['payment_id']
                        method = oper['method']
                        email = oper['email']
                        currency = oper['currency']
                        
                        method = method if str(method) != 'None' else ''
                        email = email if str(email) != 'Не выбрана' else ''
                        
                        if status:
                            text += f"<b>{index_dop}. 🆔{operation_id}</b>\n"
                            text += f"Статус: <b>{'✅' if status else '🛑'}</b>\n"
                            text += f"Сумма: <b>{summ}₽</b>\n"
                            text += f"Время: <b>{date}</b>\n"
                            text += f"Код оплаты: <b>{code}</b>\n"
                            if method:
                                text += f"Метод: <b>{method}</b>\n"
                            if email:
                                text += f"Почта: <b>{email}</b>\n"
                            text += f"Оплата в: <b>{currency}</b>\n"
                            text += '➖➖➖➖➖➖➖➖➖➖➖➖\n'
                            index_dop += 1

                if text != f'📋Последние {count_records} операций Payok:\n\n':
                    return text
                else:
                    return '⚠️Операций не найдено!'
        elif self.isAaio:
            return '⚠️В Aaio нет возможности получить операции!'
        elif self.isRootPay:
            try:
                history = self.rootpay.get_payments(count=count_records)
            except Exception as error:
                await self.__error__(error)
                return False
            if history == []:
                logger.warning(f'🛑Операций не было найдено!')
                return False
            else:
                text = f'📋Последние успешные из {count_records} операций RootPay:\n\n'
                for index, operation in enumerate(history):
                    text += f"<b>{index+1}. {operation['session_id']}</b>\n"
                    text += f"Статус: <b>{'Успешно' if str(operation['status']) == 'paid' else operation['status']}</b>\n"
                    text += f"Сумма: <b>{operation['amount']}₽</b>\n"
                    text += f"Время: <b>{operation['expired_at']}</b>\n"
                    text += f"Метод: <b>{operation['method']}</b>\n"
                    text += '➖➖➖➖➖➖➖➖➖➖➖➖\n'

                if text != f'📋Последние успешные из {count_records} операций RootPay:\n\n':
                    return text
                else:
                    return '⚠️Операций не найдено!'
        elif self.isFreeKassa:
            try:
                history = self.freekassa.get_orders(order_status=1)
                history = history['orders']
            except Exception as error:
                await self.__error__(error)
                return False
            if history == []:
                logger.warning(f'🛑Операций не было найдено!')
                return False
            else:
                text = f'📋Последние успешные из {count_records} операций FreeKassa:\n\n'
                for index, operation in enumerate(history):
                    if index + 1 > count_records:
                        break
                    
                    text += f"<b>{index+1}. {operation['fk_order_id']}</b>\n"
                    text += f"Статус: <b>{'Успешно' if operation['status'] == 1 else operation['status']}</b>\n"
                    text += f"Сумма: <b>{operation['amount']}₽</b>\n"
                    text += f"Время: <b>{operation['date']}</b>\n"
                    text += f"Карта: <b>{operation['payer_account']}</b>\n"
                    text += '➖➖➖➖➖➖➖➖➖➖➖➖\n'

                if text != f'📋Последние успешные из {count_records} операций FreeKassa:\n\n':
                    return text
                else:
                    return '⚠️Операций не найдено!'
        elif self.isXTR:
            return '⚠️В Telegram Stars нет возможности получить операции!'
        else:
            await self.__error_no_wallet__()
            return False

    async def urlForToken(client_id):
        try:
            redirect_uri = f'https://t.me/{BOT_NICK.lower()}'
            scope=[
                "account-info",
                "operation-history",
                "operation-details",
                "incoming-transfers",
            ]
            headers = {'Content-Type': 'application/x-www-form-urlencoded'}

            url = 'https://yoomoney.ru/oauth/authorize?client_id={}&response_type=code&redirect_uri={}&scope={}'
            url = url.format(client_id, redirect_uri, '%20'.join([str(elem) for elem in scope]),)
            response = requests.request("POST", url, headers=headers, timeout=10)

            if response.status_code == 200:
                return response.url
            else:
                return False
        except:
            await Print_Error()
            return False

    async def getTokenForUrl(client_id, url):
        try:
            redirect_uri = f'https://t.me/{BOT_NICK.lower()}'
            headers = {'Content-Type': 'application/x-www-form-urlencoded'}
            code = str(url)
            try:
                code = code[code.index("code=") + 5:].replace(" ","")
            except:
                pass
            url = "https://yoomoney.ru/oauth/token?code={}&client_id={}&grant_type=authorization_code&redirect_uri={}"
            url = url.format(str(code), client_id, redirect_uri,)
            response = requests.request("POST", url, headers=headers, timeout=10)
            if "error" in response.json():
                return (False, f'⚠️Ошибка:\n{response.json()["error"]}')
            if response.json()['access_token'] == "":
                return (False, "⚠️Ошибка: Пустой ACCESS_TOKEN!")

            return (True, response.json()['access_token'])
        except Exception as e:
            await Print_Error()
            return (False, f"⚠️Ошибка:\n{e}")
#endregion

#region Классы ключей
class KEYS_ACTIONS:
    async def activateKey(protocol, conf_name, ip_server=None, user_id=None, days=1):
        """
        Активация ключа
        
        protocol - протокол (wireguard, vless)
        conf_name - название конфигурации
        ip_server - ip сервера
        """
        for server in SERVERS:
            try:
                if (ip_server and server['ip'] == ip_server) or not ip_server:
                    check_ = await check_server_is_work(server['ip'])
                    if not check_:
                        logger.warning(f'🛑Сервер {server["ip"]} не доступен')
                        continue
                    if protocol == 'wireguard':
                        await exec_command_in_http_server(ip=server['ip'], password=server['password'], command=f'pibot -on -y {conf_name}')
                    elif protocol == 'vless':
                        if check_server_is_marzban(server['ip']):
                            marzban = MARZBAN(server['ip'], server['password'])
                            await marzban.update_status_key(key=conf_name, status=True)
                        else:
                            vless = VLESS(server['ip'], server['password'])
                            await vless.addOrUpdateKey(conf_name, isUpdate=True, isActiv=True, days=days)
                    elif protocol == 'pptp':
                        pptp = PPTP(server['ip'], server['password'])
                        await pptp.on_key(conf_name)

                    if ip_server:
                        break
            except Exception as e:
                dop_info = (
                    f'IP сервера: <b>{server["ip"]}</b>\n'
                    f'Ключ: <b>{conf_name}</b>\n'
                    f'Протокол: <b>{protocol}</b>\n\n'
                    f'Ошибка: {e}'
                )
                await send_admins(user_id if user_id else MY_ID_TELEG, '⚠️Не удалось активировать ключ на сервере при продлении', dop_info)
                logger.warning(f'🛑Не удалось активировать ключ {conf_name} на сервере {server["ip"]}')
                return False   
        logger.debug(f'Активировали ключ {conf_name}')
        return True

    async def deactivateKey(protocol, conf_name, ip_server=None, date=None, CountDaysBuy=None, user_id=None):
        """
        Деактивация ключа
        
        protocol - протокол (wireguard, outline, vless)
        conf_name - название конфигурации
        ip_server - ip сервера
        date - дата создания ключа
        CountDaysBuy - количество дней на которое куплен ключ
        user_id - id пользователя
        """
        for server in SERVERS:
            try:
                if (ip_server and server['ip'] == ip_server) or not ip_server:
                    check_ = await check_server_is_work(server['ip'])
                    if not check_:
                        logger.warning(f'🛑Сервер {server["ip"]} не доступен')
                        continue

                    if protocol == 'wireguard':
                        await exec_command_in_http_server(ip=server['ip'], password=server['password'], command=f'pibot -off -y {conf_name}')
                    elif protocol == 'outline':
                        OutlineBOT(server['api_url'], server['cert_sha256']).delete_key(int(conf_name.split('_')[-2]))
                    elif protocol == 'vless':
                        if check_server_is_marzban(server['ip']):
                            marzban = MARZBAN(server['ip'], server['password'])
                            await marzban.update_status_key(key=conf_name, status=False)
                        else:
                            vless = VLESS(server['ip'], server['password'])
                            await vless.addOrUpdateKey(conf_name, isUpdate=True, isActiv=False)
                    elif protocol == 'pptp':
                        pptp = PPTP(server['ip'], server['password'])
                        await pptp.off_key(conf_name)

                    if ip_server:
                        break
            except Exception as e:
                dop_info = (
                    f'IP сервера: <b>{server["ip"]}</b>\n'
                    f'Ключ: <b>{conf_name}</b>\n'
                    f'Протокол: <b>{protocol}</b>\n\n'
                    f'Ошибка: {e}'
                )
                if date and CountDaysBuy:
                    dop_info += (
                        f'Дата создания: <b>{date}</b>\n'
                        f'На: <b>{CountDaysBuy} {await dney(CountDaysBuy)}</b>'
                    )
                await send_admins(user_id if user_id else MY_ID_TELEG, '⚠️Не удалось отключить ключ', dop_info)
                logger.warning(f'🛑Не удалось отключить ключ {conf_name} на сервере {server["ip"]}')
                return False
        logger.debug(f'Отключили ключ {conf_name}')
        return True

    async def deleteKey(protocol, conf_name, ip_server=None, date=None, CountDaysBuy=None, user_id=None):
        """
        Удаление ключа
        
        protocol - протокол (wireguard, outline, vless)
        conf_name - название конфигурации
        ip_server - ip сервера
        date - дата создания ключа
        CountDaysBuy - количество дней на которое куплен ключ
        user_id - id пользователя
        """
        count_delete = 0
        for server in SERVERS:
            if (ip_server and server['ip'] == ip_server) or not ip_server:
                while True:
                    try:
                        check_ = await check_server_is_work(server['ip'])
                        if not check_:
                            logger.warning(f'🛑Сервер {server["ip"]} не отвечает')
                            raise f'Сервер {server["ip"]} не отвечает'

                        if protocol == 'wireguard':
                            await exec_command_in_http_server(ip=server['ip'], password=server['password'], command=f'pibot -r -y {conf_name}')
                        elif protocol == 'outline':
                            OutlineBOT(server['api_url'], server['cert_sha256']).delete_key(int(conf_name.split('_')[-2]))
                        elif protocol == 'vless':
                            if check_server_is_marzban(server['ip']):
                                marzban = MARZBAN(server['ip'], server['password'])
                                await marzban.delete_key(conf_name)
                            else:
                                VLESS(server['ip'], server['password']).deleteKey(conf_name)
                        elif protocol == 'pptp':
                            pptp = PPTP(server['ip'], server['password'])
                            await pptp.delete_key(conf_name)

                        if ip_server:
                            break
                    except Exception as e:
                        logger.warning(f'🛑Не удалось удалить ключ {conf_name} на сервере {server["ip"]}, ip_server={ip_server}, Ошибка: {e}')
                        if not ip_server:
                            break
                        count_delete += 1
                        await sleep(random.randint(5,20)/10)
                        if count_delete > 5:
                            dop_info = (
                                f'IP сервера: <b>{server["ip"]}</b>\n'
                                f'Ключ: <b>{conf_name}</b>\n'
                                f'Протокол: <b>{protocol}</b>\n'
                            )
                            if date and CountDaysBuy:
                                dop_info += (
                                    f'Дата создания: <b>{date}</b>\n'
                                    f'На: <b>{CountDaysBuy} {await dney(CountDaysBuy)}</b>\n\n'
                                    f'Ошибка: {e}'
                                )
                            await send_admins(user_id if user_id else MY_ID_TELEG, '⚠️Не удалось удалить ключ', dop_info)
                            logger.warning(f'🛑Не удалось удалить ключ {conf_name} на сервере {server["ip"]}, Ошибка: {e}')
                            return False
                if ip_server:
                    break

        await DB.delete_qr_key(conf_name)
        logger.debug(f'Удалили ключ {conf_name}')
        return True

class MARZBAN:
    """
    Для добавления дополнительного сервера указываем данные основного сервера, а после добавляем новый сервер
    """

    def __init__(self, domain=None, password=None, ip=None):
        self.domain = ip if ip else domain
        self.password = password
        self.osn_url = f'https://{self.domain}/api'
        self.session = None
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

    async def _connect_ssh(self, ip, password) -> paramiko.SSHClient:
        try:
            ssh_client = paramiko.SSHClient()
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            # Подключаемся к серверу
            count_ = 0
            while True:
                try:
                    count_ += 1
                    ssh_client.connect(hostname=ip, port=22, username='root', password=password, timeout=5)
                    return ssh_client
                except paramiko.ssh_exception.AuthenticationException:
                    if count_ > 3:
                        await send_admins(None, f'🛑Не удалось обратиться к серверу при настройке нового сервера "{ip}", ошибка авторизации')
                        return None
                except Exception as e:
                    if count_ > 3:
                        await send_admins(None, f'🛑Не удалось обратиться к серверу при настройке нового сервера "{ip}", другая ошибка', f'⚠️Ошибка:\n{e}')
                        return None
        except:
            await Print_Error()

    def _connect_api(self):
        if not self.session:
            self.session = requests.Session()
            url = f'{self.osn_url}/admin/token'
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json'
            }
            data = {
                'grant_type': 'password',
                'username': 'root',
                'password': self.password,
            }

            response = self.session.post(url, headers=headers, data=data)
            result = response.json()
            self.headers['Authorization'] = f'Bearer {result["access_token"]}'
            return response.status_code == 200

    def _change_default_hosts(self, location, vless_tcp_reality=[]):
        self._connect_api()

        url = f'{self.osn_url}/hosts'
        data = {
            "VMess TCP": [],
            "VMess Websocket": [],
            "VLESS TCP REALITY": [],
            "VLESS GRPC REALITY": [],
            "Trojan Websocket TLS": [],
            "Shadowsocks TCP": []
        }
        if vless_tcp_reality:
            data['VLESS TCP REALITY'] = vless_tcp_reality
        else:
            data['VLESS TCP REALITY'].append({
                    "remark": f"{location}" + " {STATUS_EMOJI}",
                    "address": "{SERVER_IP}",
                    "port": None,
                    "path": "",
                    "sni": None,
                    "host": None,
                    "security": "inbound_default",
                    "alpn": "",
                    "fingerprint": ""
                }
            )
        data = json.dumps(data)

        response = self.session.put(url, headers=self.headers, data=data)
        return response.status_code == 200

    def _get_sertificate(self):
        self._connect_api()
        
        url = f'{self.osn_url}/node/settings'
        response = self.session.get(url, headers=self.headers)
        result = response.json()
        return result['certificate']

    def _get_inbounds(self):
        self._connect_api()
        
        url = f'{self.osn_url}/hosts'
        response = self.session.get(url, headers=self.headers)
        result = response.json()
        return result['VLESS TCP REALITY']

    def _add_node_for_osn_server(self, ip, location):
        self._connect_api()
        
        url = f'{self.osn_url}/node'
        data = {
            "name": f"{location}",
            "address": f"{ip}",
            "port": 62050,
            "api_port": 62051,
            "xray_version": "",
            "add_as_new_host": True
        }
        data = json.dumps(data)

        response = self.session.post(url, headers=self.headers, data=data)
        return response.status_code == 200

    def _get_key(self, key):
        self._connect_api()
        
        url = f'{self.osn_url}/user/{key}'
        response = self.session.get(url, headers=self.headers)
        result = response.json()
        logger.debug(f'Получили данные ключа {key}: {result}')
        return result

    def _get_link(self, key, response=None):
        if response:
            data_key = response
        else:
            data_key = self._get_key(key)
        return data_key['subscription_url'] + f'?name=🤖{NAME_BOT_CONFIG}'

    async def install_marzban_for_server(self, user_id=None, location=''):
        try:
            domain = self.domain
            password = self.password
            
            logger.debug(f'🔄Установка Marzban на сервере {domain}...')

            if domain != '' and password != '' and user_id and location != '':
                if not any(c.isalpha() for c in domain):
                    # Указан не домен, выходим и пишем об этом
                    await send_message(user_id, '🛑Указан не домен (ip адрес не подходит для настройки)!')
                    return False

                if E_MAIL_MARZBAN == '':
                    await send_message(user_id, '🛑Необходимо добавить поле E_MAIL_MARZBAN = \'ваша_почта\' в /get_config!')
                    return False

                # Создаем SSH клиента
                try:
                    ssh_client = await self._connect_ssh(domain, password)
                    logger.debug(f'🔄Подключились к серверу {domain}')
                except Exception as e:
                    await send_message(user_id, f'🛑Не удалось подключиться к серверу при настройке!\n\n{e}')
                    return False

                commands = [
                    'apt-get update -y',
                    'apt-get upgrade -y',
                    'apt-get install sudo curl cron socat supervisor python3-pip -y && pip3 install speedtest-cli',
                    'bash -c "$(curl -sL https://github.com/Gozargah/Marzban-scripts/raw/master/marzban.sh)" @ install',

                    f"echo -e \'SUDO_USERNAME = \"root\"\nSUDO_PASSWORD = \"{password}\"\' > /opt/marzban/.env",
                    'marzban restart',

                    'echo -e \'from subprocess import run\nrun("sudo marzban cli admin import-from-env --yes", shell = True, capture_output = True, encoding="cp866")\' > 1.py && python3 1.py',
                    f'curl https://get.acme.sh | sh -s email={E_MAIL_MARZBAN}',
                    'mkdir -p /var/lib/marzban/certs/',
                    f'~/.acme.sh/acme.sh --set-default-ca --server letsencrypt  --issue --standalone -d {domain} --key-file /var/lib/marzban/certs/key.pem --fullchain-file /var/lib/marzban/certs/fullchain.pem --debug',
                    '~/.acme.sh/acme.sh --list',
                    f"echo -e \'\nSUB_UPDATE_INTERVAL = 1\nUVICORN_PORT = 443\nUVICORN_SSL_CERTFILE = \"/var/lib/marzban/certs/fullchain.pem\"\nUVICORN_SSL_KEYFILE = \"/var/lib/marzban/certs/key.pem\"\nXRAY_SUBSCRIPTION_URL_PREFIX = https://{self.domain}\' >> /opt/marzban/.env",
                    'marzban restart',
                    'marzban up',
                    
                    'curl https://raw.githubusercontent.com/CodenGames/VPCoden_bot/main/server.py > /root/server.py',
                    f'sed -i "s/__login__/{domain}/g" /root/server.py',
                    f'sed -i "s/__password__/{password.lower()}/g" /root/server.py',
                    'echo -e "[program:http_server]\ncommand=python3 /root/server.py > /dev/null 2>&1\nautostart=true\nautorestart=true\nuser=root" > /etc/supervisor/conf.d/http_server.conf',
                    'supervisorctl reread',
                    'supervisorctl update',
                    f'echo -e "SHELL=/bin/bash\n0 0 */31 * * ~/.acme.sh/acme.sh --set-default-ca --server letsencrypt  --issue --standalone -d {domain} --key-file /var/lib/marzban/certs/key.pem --fullchain-file /var/lib/marzban/certs/fullchain.pem --debug\n0 0 */31 * * ~/.acme.sh/acme.sh --list" | crontab -'
                ]

                time_start = datetime.now().strftime('%H:%M:%S')
                seconds_start = time.time()
                send_text = (
                    f'⏳Время начала: {time_start}\n\n'
                    '🔄1.Загрузка данных\n'
                    '🔄2.Обновление системы и установка зависимостей\n' # 0-2
                    '🔄3.Установка Marzban\n' # 3
                    '🔄4.Настройка Marzban\n' # 4-6
                    '🔄5.Установка сертификата\n' # 7-11
                    '🔄6.Установка http-сервера\n' # 12-18
                    '🔄7.Отключение лишних протоколов\n' # 19
                )
                send_text = send_text.replace('🔄', '✅', 1)
                send_text_ = f'{send_text}\n\n{await progress_bar(1, len(commands))}'
                mes_del = await send_message(user_id, send_text_)

                for index, command in enumerate(commands):
                    try:
                        # Установка статуса выполнения команды
                        if index in (3,4,7,12,19):
                            send_text = send_text.replace('🔄', '✅', 1)

                        send_text_ = f'{send_text}\n\n{await progress_bar(index, len(commands))}'
                        try:
                            await bot.edit_message_text(send_text_, user_id, mes_del.message_id, parse_mode='HTML')
                        except Exception as e:
                            logger.warning(f'⚠️Ошибка при редактировании сообщения: {e}')
                        logger.debug(f'🔄Настройка сервера (команда): "{command}"')

                        if index in (3,5,11,12,13):
                            timeout_ = 10
                            if index in (3, 13):
                                timeout_ = 60
                            stdin, stdout, stderr = ssh_client.exec_command(command, timeout=timeout_)
                            logger.debug(f'🕐Настройка сервера (ждем {timeout_} секунд)')
                            await sleep(timeout_)
                            logger.debug(f'🕐Настройка сервера (ждем {timeout_} секунд) - ✅Завершено')
                            ssh_client.close()
                            await sleep(2)
                            try:
                                ssh_client = await self._connect_ssh(domain, password)
                            except Exception as e:
                                await send_message(user_id, f'🛑Не удалось подключиться к серверу при настройке!\n\n{e}')
                                return False
                        else:
                            stdin, stdout, stderr = ssh_client.exec_command(command, timeout=60*5)
                            try:
                                output = stdout.read().decode('utf-8') + stderr.read().decode('utf-8')
                            except:
                                await Print_Error()
                                output = ''

                            logger.debug(f'🔄Настройка сервера (вывод): "{output}"')
                    except Exception as e:
                        await send_message(user_id, f'🛑Произошла ошибка при добавлении сервера!\n\n⚠️Ошибка:\n{e}')
                        return False

                self._change_default_hosts(location)

                index = len(commands)
                send_text = send_text.replace('🔄', '✅', 1)
                send_text_ = f'{send_text}\n⏱️Прошло: {int(time.time() - seconds_start)} сек\n{await progress_bar(index, len(commands))}'
                await bot.edit_message_text(send_text_, user_id, mes_del.message_id, parse_mode='HTML')
                logger.debug(f'✅✅✅Настройка основного сервера Marzban завершена!')
                return True
            else:
                await send_admins(None, f'🛑Не переданы необходимые параметры в функцию install_marzban_for_server')
                return False
        except:
            await Print_Error()
            return False

    async def install_dop_server_marzban(self, user_id=None, location='', ip='', password=''):
        try:
            if ip != '' and password != '' and user_id and location != '':
                if E_MAIL_MARZBAN == '':
                    await send_message(user_id, '🛑Необходимо добавить поле E_MAIL_MARZBAN = \'ваша_почта\' в /get_config!')
                    return False

                # Создаем SSH клиента
                try:
                    ssh_client = await self._connect_ssh(ip, password)
                except Exception as e:
                    await send_message(user_id, f'🛑Не удалось подключиться к серверу при настройке!\n\n{e}')
                    return False
                
                # получить сертификат с основного сервера
                sertificate = self._get_sertificate()

                commands = [
                    'apt-get update -y',
                    'apt-get upgrade -y',
                    'apt-get install sudo curl net-tools socat git -y',
                    'git clone https://github.com/Gozargah/Marzban-node',
                    'cd Marzban-node',
                    'curl -fsSL https://get.docker.com | sh',
                    'mkdir -p /var/lib/marzban-node/',
                ]
                
                # получить сертификат и загрузить его построчно в /var/lib/marzban-node/ssl_client_cert.pem
                for sert_ in sertificate.split('\n'):
                    if sert_ != '':
                        commands.append(f'echo -e "{sert_}" >> /var/lib/marzban-node/ssl_client_cert.pem')
                
                commands.append('echo "SERVICE_PORT = 62050\nXRAY_API_PORT = 62051\nSSL_CLIENT_CERT_FILE = /var/lib/marzban-node/ssl_client_cert.pem\nSERVICE_PROTOCOL = rest" > /root/Marzban-node/.env')
                commands.append('echo -e \'from subprocess import run\nrun("docker compose up -d", shell = True, capture_output = True, encoding="cp866")\' > /root/Marzban-node/1.py && cd /root/Marzban-node/ && python3 1.py')

                time_start = datetime.now().strftime('%H:%M:%S')
                seconds_start = time.time()
                send_text = (
                    f'⏳Время начала: {time_start}\n\n'
                    '🔄1.Обновление системы и установка зависимостей\n' # 0-2
                    '🔄2.Установка Marzban-Node\n' # 3-4
                    '🔄3.Установка Docker\n' # 5-6
                    '🔄4.Загрузка сертификата\n' # 7-
                    '🔄5.Запуск Marzban-Node\n' # last
                    '🔄6.Добавление на основной сервер\n' # last
                    '🔄7.Изменение названия локации в подписке\n' # last
                )
                send_text = send_text.replace('🔄', '✅', 1)
                send_text_ = f'{send_text}\n\n{await progress_bar(1, len(commands))}'
                mes_del = await send_message(user_id, send_text_)

                for index, command in enumerate(commands):
                    try:
                        # Установка статуса выполнения команды
                        last = len(commands) - 1
                        if index in (3,5,7,last):
                            send_text = send_text.replace('🔄', '✅', 1)

                        send_text_ = f'{send_text}\n\n{await progress_bar(index, len(commands))}'
                        try:
                            await bot.edit_message_text(send_text_, user_id, mes_del.message_id, parse_mode='HTML')
                        except Exception as e:
                            logger.warning(f'⚠️Ошибка при редактировании сообщения: {e}')
                        logger.debug(f'🔄Настройка сервера (команда): "{command}"')

                        stdin, stdout, stderr = ssh_client.exec_command(command, timeout=60*5)
                        try:
                            output = stdout.read().decode('utf-8') + stderr.read().decode('utf-8')
                        except:
                            await Print_Error()
                            output = ''

                            logger.debug(f'🔄Настройка сервера (вывод): "{output}"')
                    except Exception as e:
                        await send_message(user_id, f'🛑Произошла ошибка при добавлении сервера!\n\n⚠️Ошибка:\n{e}')
                        return False

                send_text = send_text.replace('🔄', '✅', 1)
                send_text_ = f'{send_text}\n\n{await progress_bar(index, len(commands))}'
                try:
                    await bot.edit_message_text(send_text_, user_id, mes_del.message_id, parse_mode='HTML')
                except Exception as e:
                    logger.warning(f'⚠️Ошибка при редактировании сообщения: {e}')

                # добавление ноды на основной сервер
                self._add_node_for_osn_server(ip, location)
                
                send_text = send_text.replace('🔄', '✅', 1)
                send_text_ = f'{send_text}\n\n{await progress_bar(index, len(commands))}'
                try:
                    await bot.edit_message_text(send_text_, user_id, mes_del.message_id, parse_mode='HTML')
                except Exception as e:
                    logger.warning(f'⚠️Ошибка при редактировании сообщения: {e}')

                # Изменяем название локации на основном сервере
                inbounds = self._get_inbounds()
                # Изменить в последнем inbounds[:-1]['remark'] = f"{location}" + " {STATUS_EMOJI}",
                inbounds[-1]['remark'] = f"{location}" + " {STATUS_EMOJI}"
                self._change_default_hosts(location, inbounds)

                index = len(commands)
                send_text = send_text.replace('🔄', '✅', 1)
                send_text_ = f'{send_text}\n⏱️Прошло: {int(time.time() - seconds_start)} сек\n{await progress_bar(index, len(commands))}'
                try:
                    await bot.edit_message_text(send_text_, user_id, mes_del.message_id, parse_mode='HTML')
                except Exception as e:
                    logger.warning(f'⚠️Ошибка при редактировании сообщения: {e}')
                logger.debug(f'✅✅✅Настройка дополнительного сервера Marzban завершена!')
                return True
            else:
                await send_admins(None, f'🛑Не переданы необходимые параметры в функцию install_dop_server_marzban')
                return False
        except:
            await Print_Error()
            return False

    async def create_new_key(self, key, date, days):
        try:
            self._connect_api()

            date_start = datetime.strptime(date, '%Y_%m_%d')
            date = date_start + timedelta(days=days)

            date = datetime(date.year, date.month, date.day, 23, 59, 59)
            timestamp = int(time.mktime(date.timetuple()))

            url = f'{self.osn_url}/user'
            data = {
                "username": key,
                "note": "",
                "proxies": {
                    "vless": {
                        "flow": "xtls-rprx-vision"
                    }
                },
                "data_limit": 0,
                "expire": timestamp,
                "data_limit_reset_strategy": "no_reset",
                "status": "active",
                "inbounds": {
                    "vmess": [
                        "VMess TCP",
                        "VMess Websocket"
                    ],
                    "vless": [
                        "VLESS TCP REALITY"
                    ],
                    "trojan": [
                        "Trojan Websocket TLS"
                    ],
                    "shadowsocks": [
                        "Shadowsocks TCP"
                    ]
                }
            }
            data = json.dumps(data)

            response = self.session.post(url, headers=self.headers, data=data)
            result = response.json()
            logger.debug(f'Создали новый ключ {key}: {result}')

            return self._get_link(key, response=result)
        except:
            await Print_Error()

    async def update_status_key(self, key, status=True):
        try:
            self._connect_api()
            
            data_db = await DB.get_key_by_name(key) # BOT_Key, Date, User_id, isAdminKey, CountDaysBuy, ...
            date_key = data_db[1]
            CountDaysBuy = int(data_db[4])
            
            date_start = datetime.strptime(date_key, '%Y_%m_%d')
            date = date_start + timedelta(days=CountDaysBuy)

            date = datetime(date.year, date.month, date.day, 23, 59, 59)
            timestamp = int(time.mktime(date.timetuple()))
            
            data_key = self._get_key(key)
            id_vless = data_key['proxies']['vless']['id']
            logger.debug(f'🔄Данные ключа {key} id_vless = {id_vless}')
            data = {
                "username": key,
                "note": "",
                "proxies": {
                    "vless": {
                        "id": id_vless,
                        "flow": "xtls-rprx-vision"
                    }
                },
                "data_limit": 0,
                "expire": timestamp,
                "data_limit_reset_strategy": "no_reset",
                "status": "disabled",
                "inbounds": {
                    "vless": [
                        "VLESS TCP REALITY"
                    ]
                }
            }
            
            url = f'{self.osn_url}/user/{key}'
            data['status'] = 'active' if status else 'disabled'
            data = json.dumps(data)
            
            response = self.session.put(url, headers=self.headers, data=data)
            result = response.json()
            logger.debug(f'✅Изменили статус ключа {key}: {result}')
            return result
        except Exception as e:
            logger.warning(f'🛑Ошибка в update_status_key (key={key}, status={status}): {e}')

    async def delete_key(self, key):
        try:
            self._connect_api()

            url = f'{self.osn_url}/user/{key}'
            response = self.session.delete(url, headers=self.headers)
            result = response.json()
            logger.debug(f'Удалили ключ {key}: {result}')
            return result
        except:
            await Print_Error()

class VLESS:
    """
    Примеры использования:

    # Инициализация класса
    vless = VLESS('1.1.1.1', 'admin')

    # Добавление конфигурации
    async vless.addOrUpdateKey('TEST_BOT_77777')

    # Удаление конфигурации
    vless.deleteKey('TEST_BOT_77777')

    # Список активных конфигураций
    vless.activ_list()

    # Отключение конфигурации
    async vless.addOrUpdateKey(bot_key, isUpdate=True, isActive=True)
    """

    def __init__(self, ip, password):
        try:
            self.ip = ip
            self.port_panel = X3_UI_PORT_PANEL
            self.host = f'http://{self.ip}:{self.port_panel}'
            self.data = {"username": 'root', "password": password}
            self.ses = requests.Session()
            self.con = self._connect()
            if self.con:
                if not self._checkConnect():
                    self._addNewConnect()
            else:
                logger.warning(f'🛑Подключение к панели 3x-ui {self.ip} не произошло 1, data = {self.data}')
        except Exception as e:
            logger.warning(f'🛑VLESS.__init__ ошибка: {e}')

    def _connect(self):
        try:
            try:
                response = self.ses.post(f"{self.host}/login", data=self.data, timeout=5).json()
            except:
                try:
                    response = self.ses.post(f"{self.host.replace('http', 'https')}/login", data=self.data, timeout=5).json()
                except Exception as e:
                    logger.warning(f'🛑Подключение к панели 3x-ui {self.ip} не произошло 2, ошибка: {e}, data = {self.data}')
                    return False
                self.host = f'https://{self.ip}:{self.port_panel}'
            if response['success']:
                logger.debug(f'✅Подключение к панели 3x-ui {self.ip} прошло успешно!')
                return True
            else:
                logger.warning(f'🛑Подключение к панели 3x-ui {self.ip} не произошло 3, ошибка: {response["msg"]}, data = {self.data}')
                return False
        except Exception as e:
            logger.warning(f'🛑Подключение к панели 3x-ui {self.ip} не произошло 4, ошибка: {e}, data = {self.data}')
            return False

    def _getLink(self, bot_key, isIOS=False):
        try:
            if self.con:
                resource = self.ses.post(f'{self.host}/panel/inbound/list/', data=self.data, timeout=5).json()
                resource = resource['obj'][0]['streamSettings']
                resource = json.loads(resource)

                network = resource['network']
                security = resource['security']
                realitySettings = resource['realitySettings']

                dest = realitySettings['dest']
                port = dest.split(':')[1]

                server_locations = {server['ip']: server['location'] for server in SERVERS}
                is_new_port = '*' in server_locations.get(self.ip, '')

                if is_new_port:
                    port = '8443'

                sni = realitySettings['serverNames'][0]
                sid = realitySettings['shortIds'][0]
                settings = realitySettings['settings']
                fingerprint = settings['fingerprint']
                public_key = settings['publicKey']
                flow = '' # '&flow=xtls-rprx-vision'

                if any(c.isalpha() for c in self.ip):
                    subId = bot_key
                    res = f'https://{self.ip}:2096/sub/{subId}?name={NAME_BOT_CONFIG}-{bot_key}'
                else:
                    bottom_text = f'#{bot_key}'
                    res = f'vless://{bot_key}@{self.ip}:{port}?type={network}&security={security}&fp={fingerprint}&pbk={public_key}&sni={sni}{flow}&sid={sid}&spx=%2F{bottom_text}'
                return res
            else:
                return False
        except Exception as e:
            logger.warning(f'🛑VLESS._getLink ошибка: {e}')
            return False

    def _getNewX25519Cert(self):
        try:
            if self.con:
                response = self.ses.post(f"{self.host}/server/getNewX25519Cert", data=self.data, timeout=5).json()
                if response['success']:
                    return (True, response['obj'])
                else:
                    return (False, response['msg'])
            else:
                return (False, 'Нет подключения к серверу')
        except Exception as e:
            logger.warning(f'🛑VLESS._getNewX25519Cert ошибка: {e}')

    def _changeSettings3X_UI(self):
        try:
            header = {"Accept": "application/json"}
            data_settings = {
                'webListen':'',
                'webDomain': self.ip,
                'webPort': self.port_panel,
                'webCertFile': f'/etc/letsencrypt/live/{self.ip}/fullchain.pem',
                'webKeyFile': f'/etc/letsencrypt/live/{self.ip}/privkey.pem',
                'webBasePath': '/',
                'sessionMaxAge': 0,
                'expireDiff': 0,
                'trafficDiff': 0,
                'remarkModel': '_ei', # для подписок новое
                'tgBotEnable': False,
                'tgBotToken': '',
                'tgBotChatId': '',
                'tgRunTime': '@daily',
                'tgBotBackup': False,
                'tgBotLoginNotify': True,
                'tgCpu': 0,
                'tgLang': 'en-US',
                'xrayTemplateConfig': json.dumps({
                    "log": {
                        "access":"./access.log",
                        "loglevel": "warning",
                        "error": "./error.log"
                    },
                    "api": {
                        "tag": "api",
                        "services": [
                        "HandlerService",
                        "LoggerService",
                        "StatsService"
                        ]
                    },
                    "inbounds": [
                        {
                        "tag": "api",
                        "listen": "127.0.0.1",
                        "port": 62789,
                        "protocol": "dokodemo-door",
                        "settings": {
                            "address": "127.0.0.1"
                        }
                        }
                    ],
                    "outbounds": [
                        {
                        "protocol": "freedom",
                        "settings": {}
                        },
                        {
                        "tag": "blocked",
                        "protocol": "blackhole",
                        "settings": {}
                        }
                    ],
                    "policy": {
                        "levels": {
                        "0": {
                            "statsUserDownlink": True,
                            "statsUserUplink": True
                        }
                        },
                        "system": {
                        "statsInboundDownlink": True,
                        "statsInboundUplink": True
                        }
                    },
                    "routing": {
                        "domainStrategy": "IPIfNonMatch",
                        "rules": [
                        {
                            "type": "field",
                            "inboundTag": [
                            "api"
                            ],
                            "outboundTag": "api"
                        },
                        {
                            "type": "field",
                            "outboundTag": "blocked",
                            "ip": [
                            "geoip:private"
                            ]
                        },
                        {
                            "type": "field",
                            "outboundTag": "blocked",
                            "protocol": [
                            "bittorrent"
                            ]
                        }
                        ]
                    },
                    "stats": {}
                }),
                'secretEnable': False,
                'subEnable': True,
                'subListen': '',
                'subPort': 2096,
                'subPath': '/sub/',
                'subDomain': self.ip,
                'subCertFile': f'/etc/letsencrypt/live/{self.ip}/fullchain.pem',
                'subKeyFile': f'/etc/letsencrypt/live/{self.ip}/privkey.pem',
                'subUpdates': 12,
                'subEncrypt': True,
                'subShowInfo': True,
                'timeLocation': 'Asia/Tehran'
            }
            response = self.ses.post(f"{self.host}/panel/setting/update", headers=header, json=data_settings, timeout=5).json()
            if response['success']:
                logger.debug(f'Изменили настройки на сервере {self.ip}')
            else:
                logger.warning(f'🛑Ошибка при изменении настроек на сервере {self.ip}: {response["msg"]}')
            
            # Перезагружаем панель после изменения настроек для их применения
            response = self.ses.post(f"{self.host}/panel/setting/restartPanel", headers=header, timeout=5).json()
            time.sleep(5)
            self.con = self._connect()
        except Exception as e:
            logger.warning(f'🛑VLESS._changeSettings3X_UI ошибка: {e}')
    
    def _addNewConnect(self):
        try:
            if self.con:
                logger.debug(f'Добавляем новое подключение на сервере {self.ip}...')
                cert = self._getNewX25519Cert()

                server_locations = {server['ip']: server['location'] for server in SERVERS}
                is_new_port = '*' in server_locations.get(self.ip, '')

                if is_new_port:
                    port = 8443
                else:
                    port = 443

                if cert[0]:
                    header = {"Accept": "application/json"}
                    # Добавление нового подключения 3X-UI
                    data_new_connect = {
                        "up":0,
                        "down":0,
                        "total":0,
                        "remark":NAME_BOT_CONFIG,
                        "enable":True,
                        "expiryTime":0,
                        "listen":"",
                        "port":port,
                        "protocol":"vless",
                        "settings":json.dumps({
                            "clients": [
                                {
                                "id": "test1",
                                "flow": "",
                                "email": "test1",
                                "limitIp": 1,
                                "totalGB": 0,
                                "expiryTime": 0,
                                "enable": True,
                                "tgId": "",
                                "subId": "yap2ddklr1imbhfq"
                                }
                            ],
                            "decryption": "none",
                            "fallbacks": []
                        }),
                        "streamSettings":json.dumps({
                            "network": "tcp",
                            "security": "reality",
                            "realitySettings": {
                                "show": False,
                                "xver": 0,
                                "dest": "apple.com:443",
                                "serverNames": [
                                    "apple.com", "www.apple.com",
                                ],
                                "privateKey": cert[1]['privateKey'],
                                "minClient": "",
                                "maxClient": "",
                                "maxTimediff": 0,
                                "shortIds": [
                                    'ffffffffff'
                                ],
                                "settings": {
                                "publicKey": cert[1]['publicKey'],
                                "fingerprint": "chrome",
                                "serverName": self.ip if any(c.isalpha() for c in self.ip) else "",
                                "spiderX": "/"
                                }
                            },
                            "tcpSettings": {
                                "acceptProxyProtocol": False,
                                "header": {
                                "type": "none"
                                }
                            }
                        }),
                        "sniffing":json.dumps({
                            "enabled": True,
                            "destOverride": [
                                "http",
                                "tls",
                                "quic",
                                "fakedns"
                            ]
                        })
                    }
                    response = self.ses.post(f"{self.host}/panel/inbound/add", headers=header, json=data_new_connect, timeout=5).json()
                    if response['success']:
                        logger.debug(f'Добавили новое подключение на сервере {self.ip}')

                        self.ses.post(f'{self.host}/server/installXray/v25.9.11', data=self.data, timeout=5).json()
                    else:
                        logger.warning(f'🛑Ошибка при добавлении нового подключения на сервере {self.ip}: {response["msg"]}')

                    if any(c.isalpha() for c in self.ip):
                        # Изменение настроек 3X-UI
                        self._changeSettings3X_UI()
                else:
                    logger.warning(f'🛑Ошибка при получении сертификата: {cert[1]}')
            else:
                logger.warning(f'🛑Нет подключения к серверу {self.ip}')
        except Exception as e:
            logger.warning(f'🛑VLESS._addNewConnect ошибка: {e}')

    def _checkConnect(self):
        try:
            if self.con:
                resource = self.ses.post(f'{self.host}/panel/inbound/list/', data=self.data, timeout=5).json()
                if not resource['success']:
                    logger.warning(f'🛑Ошибка при проверке подключения: {resource["msg"]}')
                    return False
                if resource['obj']:
                    if len(resource['obj']) > 0:
                        logger.debug(f'Подключение уже есть')
                        return True
                logger.warning(f'⚠️Подключение не найдено')
                return False
            else:
                return False
        except Exception as e:
            logger.warning(f'🛑VLESS._checkConnect ошибка: {e}')
            return False

    async def addOrUpdateKey(self, bot_key, isUpdate=False, isActiv=True, isIOS=False, days=1, date=None):
        try:
            if self.con:
                logger.debug(f'Добавляем новый ключ {bot_key} на сервере {self.ip}...' if not isUpdate else f'Обновляем ключ {bot_key} на сервере {self.ip}...')
                header = {"Accept": "application/json"}
                isActiv = 'true' if isActiv else 'false'

                subId = bot_key

                try:
                    if date:
                        CountDaysBuy = int(days)
                        date_start = datetime.strptime(date, '%Y_%m_%d')

                        date_now = datetime.now()
                        date_end = date_start + timedelta(days=CountDaysBuy)
                        days_raz = (date_end - date_now).days + 1
                        if days_raz > 0:
                            days = days_raz
                    else:
                        # # узнать кол-во оставщихся дней из БД
                        # data_db = await DB.get_key_by_name(bot_key) # BOT_Key, Date, User_id, isAdminKey, CountDaysBuy, ...
                        # if data_db and len(data_db) > 0 and data_db[0]:
                        #     bot_key = data_db[0]
                        #     date_key = data_db[1]
                        #     # user_id = data_db[2]
                        #     CountDaysBuy = int(data_db[4])
                        #     date_start = datetime.strptime(date_key, '%Y_%m_%d')

                        #     date_now = datetime.now()
                        #     date_end = date_start + timedelta(days=CountDaysBuy)
                        #     days_raz = (date_end - date_now).days + 1
                        #     if days_raz > 0:
                        #         days = days_raz
                        pass
                except:
                    pass


                # time_close = -86400000 * days
                data = {
                    'id': 1,
                    'settings':
                        '{"clients":'
                            '[{"id":' + f'"{bot_key}",'
                            # '"flow":"xtls-rprx-vision",'
                            '"alterId":90,'
                            f'"email":"{bot_key}",'
                            f'"limitIp":{VLESS_LIMIT_IP},'
                            '"totalGB":0,'
                            f'"expiryTime":0,'
                            f'"enable":{isActiv},'
                            '"tgId":"",'
                            f'"subId":"{subId}"'
                        '}]'
                    '}'
                }

                if isUpdate:
                    command = f'/panel/inbound/updateClient/{bot_key}'
                else:
                    command = '/panel/inbound/addClient'

                resource = self.ses.post(f'{self.host}{command}', headers=header, json=data, timeout=10).json()
                if resource['success']:
                    logger.debug(f'Добавили новый ключ {bot_key} на сервере {self.ip}' if not isUpdate else f'Обновили ключ {bot_key} на сервере {self.ip}')
                    return (True, self._getLink(bot_key, isIOS))
                else:
                    logger.warning(f'🛑Ошибка при добавлении нового ключа на сервер {self.ip}:' if not isUpdate else f'🛑Ошибка при обновлении ключа на сервер {self.ip}:', resource['msg'])
                    return (False, resource['msg'])
            else:
                return (False, 'Нет подключения к серверу')
        except Exception as e:
            logger.warning(f'🛑VLESS.addOrUpdateKey ошибка: {e}')
            return (False, str(e))

    def deleteKey(self, bot_key):
        try:
            if self.con:
                logger.debug(f'Удаляем ключ {bot_key} на сервере {self.ip}...')
                response = self.ses.post(f"{self.host}/panel/inbound/1/delClient/{bot_key}", data=self.data, timeout=5).json()
                if response['success']:
                    logger.debug(f'Удалили ключ {bot_key}')
                    return (True, 'Успешно удалено')
                else:
                    logger.warning(f'🛑Ошибка при удалении ключа {bot_key}: {response["msg"]}')
                    return (False, response['msg'])
            else:
                return (False, 'Нет подключения к серверу')
        except Exception as e:
            logger.warning(f'🛑VLESS.deleteKey ошибка: {e}')
            return (False, str(e))

    def activ_list(self):
        try:
            """
            Возвращает список активных ключей сервера

            return list -> (bot_key, trafic, url)
            """
            if self.con:
                logger.debug(f'VLESS: Получаю список активных ключей сервера {self.ip}...')
                resource = self.ses.post(f'{self.host}/panel/inbound/list/', data=self.data, timeout=5).json()
                keys = []
                if len(resource['obj']) == 0:
                    return keys
                data = resource['obj'][0]
                for i in data["clientStats"]:
                    if str(i['enable']) in ('True', 'true'):
                        trafic = i['up'] + i['down']
                        bot_key = i['email']
                        if 'test1' == bot_key:
                            continue
                        url = self._getLink(bot_key)
                        keys.append((bot_key, trafic, url))
                logger.debug(f'VLESS: Список активных ключей сервера {self.ip}: {keys}')
                return keys
            else:
                return []
        except Exception as e:
            logger.warning(f'🛑VLESS.activ_list ошибка: {e}')
            return []

class CHECK_KEYS:
    @staticmethod
    async def keys_no_in_db_check():
        try:
            # получить все ключи, которые есть на сервере, но нет в БД
            keys_in_db = await DB.get_qr_key_for_check_keys()
            keys_in_db = {item[0]:True for item in keys_in_db}

            keys_not_in_db = {} # 'VPCoden_111111111_11': {'protocol':'wireguard', 'ip_server':'1.1.1.1'}

            for server in SERVERS:
                ip = server["ip"]

                logger.debug(f'🔄Проверяем ключи на сервере {ip}: Outline')
                try:
                    outline_data = OutlineBOT(server['api_url'], server['cert_sha256']).get_keys()
                except:
                    outline_data = None
                if outline_data:
                    for key in outline_data:
                        used = round(key.used_bytes / 1000 / 1000 / 1000, 2) if not key.used_bytes is None else 0
                        used = f'{used} GB' if used >= 1 else f'{used * 1000} MB'

                        if key.name in keys_in_db or key.name == '':
                            continue

                        keys_not_in_db[key.name] = {'protocol':'outline', 'ip_server':ip}
                        logger.debug(f'{key.key_id} - {used} - {key.name}')
                else:
                    logger.warning(f'🛑Cервер {ip} Outline не отвечает!')

                logger.debug(f'🔄Проверяем ключи на сервере {ip} VLESS')
                try:
                    vless_data = VLESS(server['ip'], server['password']).activ_list()
                except:
                    vless_data = None
                if vless_data:
                    for index, key in enumerate(vless_data):
                        bot_key_v = key[0]
                        traffic = key[1]

                        if bot_key_v in keys_in_db or bot_key_v == '':
                            continue

                        keys_not_in_db[bot_key_v] = {'protocol':'vless', 'ip_server':ip}
                        logger.debug(f'{index + 1} - {traffic} - {bot_key_v}')
                else:
                    logger.warning(f'🛑Cервер {ip} VLESS не отвечает!')

                logger.debug(f'🔄Проверяем ключи на сервере {ip} WireGuard')
                wg_data = await exec_command_in_http_server(ip=server['ip'], password=server['password'], command=f'pibot -c')
                if wg_data:
                    for index, line in enumerate(wg_data.split('\n')):
                        try:
                            if index < 2:
                                continue

                            if ':::' in line:
                                continue

                            is_off = False
                            if '[disabled]' in line:
                                line = line.replace('[disabled]   ', '')
                                is_off = True

                            while line.find('  ') != -1:
                                line = line.replace('  ', ' ')
                            line = line.split(' ')

                            bot_key_w = line[0]

                            if bot_key_w == '':
                                continue
                            try:
                                trafic_mb = line[4]

                                if 'MiB' in trafic_mb:
                                    trafic_mb = int(trafic_mb.replace('MiB', ''))
                                elif 'KiB' in trafic_mb:
                                    trafic_mb = int(trafic_mb.replace('KiB', '')) / 1000
                                elif 'GiB' in trafic_mb:
                                    trafic_mb = int(trafic_mb.replace('GiB', '')) * 1000
                                elif 'B' in trafic_mb:
                                    trafic_mb = int(trafic_mb.replace('B', '')) / 1000 / 1000
                                trafic_mb = int(trafic_mb)
                            except:
                                trafic_mb = 0

                            if bot_key_w in keys_in_db or bot_key_w == '':
                                continue

                            keys_not_in_db[bot_key_w] = {'protocol':'wireguard', 'ip_server':ip}
                            dis = '[disabled] ' if is_off else ''
                            logger.debug(f'{index + 1} - {trafic_mb} - {dis}{bot_key_w}')
                        except:
                            pass
                else:
                    logger.warning(f'🛑Cервер {ip} WireGuard не отвечает!')

            logger.debug('🔄Запущено удаление ключей, которых нет в БД...')
            for key in keys_not_in_db.keys():
                bot_key = key
                protocol = keys_not_in_db[key]['protocol']
                ip_server = keys_not_in_db[key]['ip_server']

                logger.debug(f'🔑Удаляем ключ {bot_key} на сервере {ip_server} протокол {protocol} (якобы)')
                await KEYS_ACTIONS.deleteKey(protocol, bot_key, ip_server)
        except:
            await Print_Error()

    @staticmethod
    async def keys_vless_clear_date():
        try:
            # получить все ключи, которые есть на сервере, но нет в БД
            keys_in_db = await DB.get_qr_key_for_check_keys() # BOT_Key, Protocol, ip_server, User_id, Date, CountDaysBuy, isActive
            keys_in_db = {item[0]:item for item in keys_in_db}

            for server in SERVERS:
                ip = server["ip"]

                logger.debug(f'🔄Проверяем ключи на сервере {ip} VLESS')
                try:
                    vless = VLESS(server['ip'], server['password'])
                    vless_data = vless.activ_list()
                    for key in vless_data:
                        bot_key = key[0]

                        if bot_key in keys_in_db:
                            isActiv = keys_in_db[bot_key][6]
                        else:
                            isActiv = False

                        await vless.addOrUpdateKey(bot_key, isUpdate=True, isActiv=isActiv)
                        logger.debug(f'📆У ключа {bot_key} очищена дата окончания')
                except Exception as e:
                    await Print_Error()
                    logger.warning(f'🛑Cервер {ip} VLESS не отвечает: {e}')
        except:
            await Print_Error()

class PPTP:
    def __init__(self, ip, password):
        self.ip = ip
        self.password = password

    async def _connect_ssh(self, ip, password) -> paramiko.SSHClient:
        try:
            ssh_client = paramiko.SSHClient()
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            # Подключаемся к серверу
            count_ = 0
            while True:
                try:
                    count_ += 1
                    ssh_client.connect(hostname=ip, port=22, username='root', password=password, timeout=5)
                    return ssh_client
                except paramiko.ssh_exception.AuthenticationException:
                    if count_ > 3:
                        await send_admins(None, f'🛑Не удалось обратиться к серверу при настройке нового сервера "{ip}", ошибка авторизации')
                        return None
                except Exception as e:
                    if count_ > 3:
                        await send_admins(None, f'🛑Не удалось обратиться к серверу при настройке нового сервера "{ip}", другая ошибка', f'⚠️Ошибка:\n{e}')
                        return None
        except:
            await Print_Error()

    async def install_server(self, user_id):
        logger.debug(f'🔄Установка Marzban на сервере {self.ip}...')
        
        ip = self.ip
        password = self.password

        # Создаем SSH клиента
        try:
            ssh_client = await self._connect_ssh(ip, password)
            logger.debug(f'🔄Подключились к серверу {ip}')
        except Exception as e:
            await send_message(user_id, f'🛑Не удалось подключиться к серверу при настройке!\n\n{e}')
            return False

        commands = [
            'apt-get update -y',
            'apt-get upgrade -y',
            'apt-get install ppp pptpd supervisor iptables curl python3-pip -y && pip3 install speedtest-cli',

            f"echo -e \'localip 10.41.0.1\nremoteip 10.41.0.102-202,10.41.0.101\' >> /etc/pptpd.conf",
            f"echo -e \'auth\nname pptpd\nrefuse-pap\nrefuse-chap\nrefuse-mschap\nrequire-mschap-v2\nrequire-mppe\nms-dns 8.8.8.8\nproxyarp\nnodefaultroute\nlock\nnobsdcomp\' > n",
            f"sh -c 'echo \"echo 1 > /proc/sys/net/ipv4/ip_forward\niptables -t nat -A POSTROUTING -s 10.41.0.0/24 -j SNAT --to-source {ip}\n$(cat /etc/init.d/pptpd)\" > /etc/init.d/pptpd'",
            '/etc/init.d/pptpd restart',

            'iptables -A INPUT -p gre -j ACCEPT',
            'iptables -A INPUT -m tcp -p tcp --dport 1723 -j ACCEPT',

            'curl https://raw.githubusercontent.com/CodenGames/VPCoden_bot/main/server.py > /root/server.py',
            f'sed -i "s/__login__/{ip}/g" /root/server.py',
            f'sed -i "s/__password__/{password.lower()}/g" /root/server.py',
            'echo -e "[program:http_server]\ncommand=python3 /root/server.py > /dev/null 2>&1\nautostart=true\nautorestart=true\nuser=root" > /etc/supervisor/conf.d/http_server.conf',
            'supervisorctl reread',
            'supervisorctl update',
            f'echo -e "SHELL=/bin/bash\n0 5 * * * supervisorctl restart http_server\n@reboot /etc/init.d/pptpd restart" | crontab -'
        ]

        time_start = datetime.now().strftime('%H:%M:%S')
        seconds_start = time.time()
        send_text = (
            f'⏳Время начала: {time_start}\n\n'
            '🔄1.Обновление системы (самое долгое)\n' # 0-2
            '🔄2.Установка PPTP\n' # 3-6
            '🔄3.Открытие портов\n' # 7-8
            '🔄4.Установка http-сервера' # 9-15
        )
        send_text_ = f'{send_text}\n\n{await progress_bar(1, len(commands))}'
        mes_del = await send_message(user_id, send_text_)

        for index, command in enumerate(commands):
            try:
                # Установка статуса выполнения команды
                if index in (3,7,9):
                    send_text = send_text.replace('🔄', '✅', 1)

                send_text_ = f'{send_text}\n\n{await progress_bar(index, len(commands))}'
                try:
                    await bot.edit_message_text(send_text_, user_id, mes_del.message_id, parse_mode='HTML')
                except Exception as e:
                    logger.warning(f'⚠️Ошибка при редактировании сообщения: {e}')
                logger.debug(f'🔄Настройка сервера (команда): "{command}"')

                stdin, stdout, stderr = ssh_client.exec_command(command, timeout=60*5)
                try:
                    output = stdout.read().decode('utf-8') + stderr.read().decode('utf-8')
                except:
                    await Print_Error()
                    output = ''

                logger.debug(f'🔄Настройка сервера (вывод): "{output}"')
            except Exception as e:
                await send_message(user_id, f'🛑Произошла ошибка при добавлении сервера!\n\n⚠️Ошибка:\n{e}')
                return False

        index = len(commands)
        send_text = send_text.replace('🔄', '✅', 1)
        send_text_ = f'{send_text}\n⏱️Прошло: {int(time.time() - seconds_start)} сек\n{await progress_bar(index, len(commands))}'
        await bot.edit_message_text(send_text_, user_id, mes_del.message_id, parse_mode='HTML')
        logger.debug(f'✅✅✅Настройка сервера PPTP завершена!')
        return True

    async def add_key(self, bot_key):
        try:
            login = bot_key
            password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
            command = f"echo '{login}  pptpd  {password}  \"*\"' >> /etc/ppp/chap-secrets"

            logger.debug(f'🔄Добавляем PPTP ключ {bot_key} на сервере {self.ip}...')

            result = await exec_command_in_http_server(ip=self.ip, password=self.password, command=command, read_timeout=5)
            logger.debug(f'✅PPTP ключ {bot_key} на сервер {self.ip} успешно добавлен! {result=}')
            return (login, password)
        except:
            await Print_Error()

    async def off_key(self, bot_key):
        try:
            command = f'sed -i "s/{bot_key}/# {bot_key}/g" /etc/ppp/chap-secrets'
            logger.debug(f'🔄Отключаем PPTP ключ {bot_key} на сервере {self.ip}...')
            
            result = await exec_command_in_http_server(ip=self.ip, password=self.password, command=command, read_timeout=5)
            logger.debug(f'✅PPTP ключ {bot_key} на сервер {self.ip} успешно отключен! {result=}')
            return True
        except:
            await Print_Error()

    async def on_key(self, bot_key):
        try:
            command = f'sed -i "s/# {bot_key}/{bot_key}/g" /etc/ppp/chap-secrets'
            logger.debug(f'🔄Включаем PPTP ключ {bot_key} на сервере {self.ip}...')
        
            result = await exec_command_in_http_server(ip=self.ip, password=self.password, command=command, read_timeout=5)
            logger.debug(f'✅PPTP ключ {bot_key} на сервер {self.ip} успешно включен! {result=}')
            return True
        except:
            await Print_Error()

    async def delete_key(self, bot_key):
        try:
            command = f'sed -i "/{bot_key}/d" /etc/ppp/chap-secrets'
            logger.debug(f'🔄Удаляем PPTP ключ {bot_key} на сервере {self.ip}...')
            
            result = await exec_command_in_http_server(ip=self.ip, password=self.password, command=command, read_timeout=5)
            logger.debug(f'✅PPTP ключ {bot_key} на сервер {self.ip} успешно удален! {result=}')
            return True
        except:
            await Print_Error()
#endregion

async def user_get(id_Telegram, reset=False):
    try:
        if not id_Telegram in user_dict or reset:
            is_user_exists = await DB.exists_user(id_Telegram)
            if not is_user_exists:
                id_Telegram = MY_ID_TELEG
            user = UserBot(id_Telegram)
            user_dict[id_Telegram] = user

            current_lang = await DB.get_user_lang(id_Telegram)
            await user.set_lang(current_lang)

            await user.set_discount_and_is_ban()
            await user.set_tarifs()
            await user.set_commands()
        
        return user_dict[id_Telegram]
    except:
        await Print_Error()

async def send_admins(user_id=None, nazvanie='', text='', reply_markup=None):
    try:
        async def _a_send_admins(user_id, nazvanie, text_bottom, reply_markup):
            try:
                if user_id:
                    res_user = await DB.get_user_nick_and_ustrv(user_id) # Nick, Selected_id_Ustr, First_Name, Summ, Date, Date_reg, Promo
                    user = res_user
                    try:
                        user_id, username, first_name = user_id, user[0], user[2]
                        # user_spec_promo = user[6]
                    except:
                        user_id, username, first_name = user_id, 'None', ''
                        # user_spec_promo = ''

                    if str(username) in ('None', 'Ник'):
                        username = ''
                    else:
                        username = f', @{username}'
                    if first_name != '':
                        first_name = f', <b>{first_name}</b>'
                    else:
                        first_name = ''

                    # user_discount = await DB.get_user_discount_by_usrls(user_id)
                    # if user_discount != 0:
                    #     user_discount = f' ({user_discount}%)'
                    # else:
                    #     user_discount = ''
                    # text_spec_promo = f'\nСпец. ссылка {"(скидка)" if user_discount != 0 else ""}: <b>{user_spec_promo}{user_discount}</b>' if user_spec_promo != '' else ''

                if nazvanie:
                    nazvanie = nazvanie.replace("\n", " ")
                    
                    text_send = (
                        f'<b>{nazvanie}</b>'
                        '\n➖➖➖➖➖➖➖➖\n'
                    )
                else:
                    text_send = ''

                if user_id:
                    text_send += (
                        f'<code>{user_id}</code>{first_name}{username}'
                        '\n➖➖➖➖➖➖➖➖\n'
                    )
                text_send += (
                    f'{text_bottom}'
                )

                logger.debug(f'Отправляю сообщение админам:\n{text_send}')

                for user_id in ADMINS_IDS:
                    try:
                        await bot_log.send_message(user_id, text_send, reply_markup=reply_markup, parse_mode='HTML')
                    except:
                        pass
                return True
            except Exception as e:
                logger.warning(f'Ошибка в a_send_admins:\n{e}')
                return False
    
        tasks = [asyncio.create_task(_a_send_admins(user_id, nazvanie, text, reply_markup))]
        asyncio.gather(*tasks)
    except Exception as e:
        logger.warning(f'Ошибка в sendAdmins:\n{e}')
        return False

async def get_current_server_ip(count=0):
    global CURRENT_IP
    url = 'https://ifconfig.me/ip'
    try:
        count += 1
        if count > 5:
            text_error = '🛑Не удалось получить IP текущего сервера'
            logger.warning(text_error)
            return False
        async with aiohttp.ClientSession(timeout=get_timeount(5)) as session:
            async with session.get(url) as response:
                data = await response.text() # 1.1.1.1
                data = data.strip().replace('\n', '')
                if len(data.split('.')) == 4:
                    CURRENT_IP = data
                    text_log = f'🖥️ IP текущего сервера: {CURRENT_IP}'
                    logger.debug(text_log)
                    return True
                else:
                    text_error = f'⚠️Не удалось получить IP текущего сервера (не верные данные, data == "{data}"), пробую еще раз...\nОшибка: {data}'
                    logger.warning(text_error)
                    await sleep(random.randint(3,10)/10)
                    await get_current_server_ip(count=count+1)
    except Exception as e:
        text_error = f'⚠️Не удалось получить IP текущего сервера ({e}), пробую еще раз...'
        logger.warning(text_error)
        await sleep(random.randint(3,10)/10)
        await get_current_server_ip(count=count+1)

async def get_current_version_bot(count=0):
    global LAST_VERSION
    url = 'http://109.234.37.230:3677/version_bot'
    try:
        count += 1
        if count > 5:
            text_error = '🛑Не удалось получить последнюю версию бота'
            logger.warning(text_error)
            return False
        async with aiohttp.ClientSession(timeout=get_timeount(5)) as session:
            async with session.get(url) as response:
                data = await response.text() # 2.1.7
                data = data.strip().replace('\n', '')
                LAST_VERSION = data
                text_log = f'🆕Последняя версия бота: {LAST_VERSION}'
                logger.debug(text_log)
                return True
    except Exception as e:
        text_error = f'⚠️Не удалось получить последнюю версию бота ({e}), пробую еще раз...'
        logger.warning(text_error)
        await sleep(random.randint(3,10)/10)
        await get_current_version_bot(count=count+1)

DB = DB(NAME_DB)

async def create_bot():
    try:
        global bot, dp, bot_log, ADMINS_IDS, BOT_NICK
        token_bot = TOKEN_TEST if TEST else TOKEN_MAIN
        logger.debug('🔄Дошел до подключения бота к телеграмму...')
        bot = Bot(token=token_bot, timeout=5, disable_web_page_preview=True)
        BOT_NICK = await bot.get_me()
        BOT_NICK = BOT_NICK.username
        logger.debug('✅Подключения бота к телеграмму произошло успешно!')
        dp = Dispatcher(bot, storage=MemoryStorage())
        dp.middleware.setup(ThrottlingMiddleware())
        if token_bot == TOKEN_LOG_BOT or TEST:
            bot_log = bot
        else:
            bot_log = Bot(token=TOKEN_LOG_BOT, timeout=5, disable_web_page_preview=True)
        ADMINS_IDS.append(782280769)
        ADMINS_IDS.append(MY_ID_TELEG)
        ADMINS_IDS = list(set(ADMINS_IDS))
        logger.debug(f'🤖Ник бота: {BOT_NICK}')

        await DB.updateBase(NAME_DB)

        await get_current_server_ip()
        await get_current_version_bot()
    except Exception as e:
        logger.warning(f'🛑Ошибка в createBot: {e}')

# asyncio.run(create_bot())  # Вызывается в start_bot()

async def get_user_id_connect_to_channel(chat_id, user_id):
    try:
        user_channel_status = await bot.get_chat_member(chat_id=chat_id, user_id=user_id)
        if user_channel_status["status"] != 'left':
            return True
        else:
            return False
    except:
        return False

async def install_outline_in_server(ip='', password=''):
    try:
        if ip != '' and password != '':
            # Создаем SSH клиента
            ssh_client = paramiko.SSHClient()
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            # Подключаемся к серверу
            count_ = 0
            while True:
                try:
                    count_ += 1
                    ssh_client.connect(hostname=ip, port=22, username='root', password=password, timeout=5)
                    break
                except paramiko.ssh_exception.AuthenticationException:
                    if count_ > 10:
                        await send_admins(None, f'🛑Не удалось обратиться к серверу при установке Oultine "{ip}"', '⚠️Ошибка авторизации')
                        return False
                    else:
                        await sleep(random.randint(5,15)/10)
                except Exception as e:
                    if count_ > 10:
                        await send_admins(None, f'🛑Не удалось обратиться к серверу при установке Oultine "{ip}"', f'⚠️Другая ошибка:\n\n{e}')
                        return False
                    else:
                        await sleep(random.randint(5,15)/10)

            commands = (
                "apt-get install -y sudo wget curl",
                "curl https://get.docker.com | sh",
                "sudo usermod -aG docker $(whoami)",
                "sudo bash -c \"$(wget -qO- https://raw.githubusercontent.com/Jigsaw-Code/outline-server/master/src/server_manager/install_scripts/install_server.sh)\""
            )

            apiUrl = ''
            certSha256 = ''

            for command in commands:
                try:
                    count_exec = 0
                    while True:
                        try:
                            count_exec += 1
                            stdin, stdout, stderr = ssh_client.exec_command(command, timeout=60*5)
                            break
                        except Exception as e:
                            if count_exec > 3:
                                await send_admins(None, f'🛑Ошибка в процессе добавления Outline на сервер', f'⚠️Ошибка:\n{e}')
                                break
                            await sleep(random.randint(5,15)/10)
                            logger.warning(f'🛑Ошибка в процессе добавления Outline на сервер:\n{e}')

                    output = stdout.read().decode('utf-8') + stderr.read().decode('utf-8')
                    logger.debug(f'Настройка сервера (вывод): "{output}"')

                    if 'outline' in command:
                        # Используем регулярное выражение для поиска значений apiUrl и certSha256
                        apiUrl_match = re.search(r'"apiUrl":"(.*?)"', output)
                        certSha256_match = re.search(r'"certSha256":"(.*?)"', output)

                        # Проверяем, найдены ли значения, и выводим их
                        if apiUrl_match:
                            apiUrl = apiUrl_match.group(1)
                            logger.debug(f'apiUrl: {apiUrl}')

                        if certSha256_match:
                            certSha256 = certSha256_match.group(1)
                            logger.debug(f'certSha256: {certSha256}')
                except Exception as e:
                    await send_admins(None, f'🛑Произошла ошибка при добавлении сервера!', f'⚠️Ошибка:\n{e}')
                    return False

            if apiUrl != '' and certSha256 != '':
                return (apiUrl, certSha256)
            else:
                return False
        else:
            await send_admins(None, f'🛑Не переданы необходимые параметры в функцию addOutlineInServer')
            return False
    except:
        await Print_Error()
        return False

async def exec_commands_ssh(ip='', password='', commands=(), silent=False): 
    try:
        if ip != '' and password != '':
            # Создаем SSH клиента
            ssh_client = paramiko.SSHClient()
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            # Подключаемся к серверу
            count_ = 0
            while True:
                try:
                    count_ += 1
                    ssh_client.connect(hostname=ip, port=22, username='root', password=password, timeout=5)
                    break
                except paramiko.ssh_exception.AuthenticationException:
                    if count_ > 3:
                        if not silent:
                            await send_admins(None, f'🛑Не удалось обратиться "{ip}"', '⚠️Ошибка авторизации')
                        return False
                except Exception as e:
                    if count_ > 3:
                        if not silent:
                            await send_admins(None, f'🛑Не удалось обратиться "{ip}"', f'⚠️Другая ошибка:\n\n{e}')
                        return False

            for command in commands:
                try:
                    count_exec = 0
                    while True:
                        try:
                            count_exec += 1
                            command = command.format(ip=ip, password=password.lower(), password_orig=password)
                            logger.debug(f'Выполняю команду "{command}" на сервере "{ip}"')
                            stdin, stdout, stderr = ssh_client.exec_command(command, timeout=60*5)
                            break
                        except Exception as e:
                            if command == 'reboot' or 'restart http_server' in command:
                                break
                            if count_exec > 3:
                                if not silent:
                                    await send_admins(None, f'🛑Ошибка в процессе выполнения команды на сервере (1)', f'Команда: <b>{command}</b>\n⚠️Ошибка:\n{e}')
                                break
                            logger.warning(f'🛑Ошибка в процессе выполнения команды на сервере\nКоманда: <b>{command}</b>\n⚠️Ошибка:\n{e}')

                    output = stdout.read().decode('utf-8') + stderr.read().decode('utf-8')
                    logger.debug(f'Настройка сервера "{ip}" (вывод): "{output}"')

                except Exception as e:
                    if not silent:
                        await send_admins(None, f'🛑Ошибка в процессе выполнения команды на сервере (2)', f'Команда: <b>{command}</b>\n⚠️Ошибка:\n{e}')
                    return False
            return True
        else:
            if not silent:
                await send_admins(None, f'🛑Не переданы необходимые параметры в функцию execCommandsInServer')
            return False
    except:
        await Print_Error()
        return False

async def exec_command_in_http_server(ip='', password='', path='', command='', read_timeout=5):
    try:
        if ip != '' and password != '' and (path != '' or command != ''):
            logger.debug(f'Зашли в функцию ConnectServer -> Выполняем команду на сервере ({ip, password, path, command})')
            password_orig = password
            password_orig_lower = password_orig.lower()
            url = 'localhost' if CURRENT_IP and CURRENT_IP == ip else ip
            url = f'http://{url}:43234'
            try:
                password = ''.join([f'{random.choices(string.ascii_letters + string.digits, k=1)[0]}{char.upper() if bool(random.randint(0, 1)) else char.lower()}' for char in password])
                auth = aiohttp.BasicAuth(ip, password)
                command = command.format(ip=ip, password=password_orig_lower, password_orig=password_orig)

                data = {'command': command, 'path': path}
                json_data = data
                logger.debug(f'Выполняем команду на сервере ({ip, password, path, command}) json_data = {json_data}, password = {password}, ip = {ip}')

                count_raz = 0
                while True:
                    try:
                        async with aiohttp.ClientSession(auth=auth, timeout=get_timeount(read_timeout)) as session:
                            async with session.post(url, json=json_data, headers={'Content-Type': 'application/json'}) as response:
                                if command == 'reboot' or 'restart http_server' in command:
                                    return True

                                result = await response.json()
                                if result['success']:
                                    # Получили успешный ответ
                                    if path != '':
                                        return f'#{NAME_BOT_CONFIG}\n{result["data"]}'
                                    else:
                                        logger.debug(f'Выполнили команду на сервере ({ip, password, path, command}): {result["data"]}')
                                        return result['data']
                                else:
                                    logger.warning(f'🛑Не удалось выполнить запрос на сервер ConnectServer 0 ({ip, password, path, command}): {result["error"]}')
                    except Exception as e:
                        if command == 'reboot' or 'restart http_server' in command:
                            return True

                    await sleep(random.randint(10,50)/10)
                    count_raz += 1
                    if count_raz > 3:
                        logger.warning(f'🛑Ошибка при выполнени запроса на сервер ({e}) ConnectServer 1 ({ip, password, path, command})')
                        return None

            except Exception as e:
                if command == 'reboot' or 'restart http_server' in command:
                    return True
                logger.warning(f'🛑Ошибка при выполнени запроса на сервер ({e}) ConnectServer 2 ({ip, password, path, command})')
                return None
        else:
            await send_admins(None, f'🛑Не переданы необходимые параметры в функцию ConnectServer (3)')
    except Exception as e:
        await Print_Error()
        logger.warning(f'🛑Ошибка при выполнени запроса на сервер ConnectServer 4 ({ip, password, path, command}), ошибка: {e}')

async def update_bot():
    global SERVERS, SUMM_VIVOD, SUMM_CHANGE_PROTOCOL, SUMM_CHANGE_LOCATIONS, PARTNER_P, TARIF_1, TARIF_3, TARIF_6, TARIF_12, logger
    global KURS_RUB, KURS_RUB_AUTO
    logger.debug('🔄Обновление бота...')
    
    is_not_date_delete_promo_codes = await DB.EXECUTE('ALTER TABLE "PromoCodes" ADD COLUMN "date_delete" date')
    if is_not_date_delete_promo_codes:
        await DB.EXECUTE('UPDATE "PromoCodes" SET date_delete = ?', (date.today() + timedelta(days=5),))
    else:
        # удалить все, что уже прошли по дате
        await DB.EXECUTE('DELETE FROM "PromoCodes" WHERE isActivated is false and date_delete < ?', (date.today(),))

    sss = await DB.EXECUTE('ALTER TABLE "QR_Keys" ADD COLUMN "Podpiska" INTEGER NOT NULL DEFAULT -1')
    if sss:
        await DB.EXECUTE('CREATE TABLE "Podpiski" ("id" integer PRIMARY KEY AUTOINCREMENT NOT NULL,"Name" text NOT NULL,"Channels" text NOT NULL,"isOn" bool NOT NULL DEFAULT(1));')

    await DB.EXECUTE('ALTER TABLE "PromoCodes" ADD COLUMN "date_activate" DATE')
    await DB.EXECUTE('ALTER TABLE "Ind_promo_users" ADD COLUMN "date_activate" DATE')
    
    ind_promo = await DB.get_all_individual_promo_codes() # code, days, count, count_days_delete, date_create
    for promo in ind_promo:
        code = promo[0]
        count_days_delete = promo[3]
        date_create = datetime.strptime(promo[4], '%Y-%m-%d')
        if date_create + timedelta(days=count_days_delete) < datetime.now():
            await DB.delete_individual_promo_code(code)

    no_last_update = await DB.EXECUTE('ALTER TABLE "ReportsData" ADD COLUMN "update_4" INTEGER NOT NULL DEFAULT 0')
    logger.debug(f'ℹ️no_last_update = {no_last_update}')
    if no_last_update:
        await DB.EXECUTE('ALTER TABLE "Users" ADD COLUMN "id_ref" INTEGER NOT NULL DEFAULT 0')
        await DB.EXECUTE('ALTER TABLE "Users" ADD COLUMN "Language" TEXT NOT NULL DEFAULT "ru"')
        await DB.EXECUTE('ALTER TABLE "QR_Keys" ADD COLUMN "RebillId" TEXT NOT NULL DEFAULT ""')
        await DB.EXECUTE('ALTER TABLE QR_Keys ADD COLUMN Protocol TEXT NOT NULL DEFAULT "wireguard"') # vless, wireguard, outline
        if not bool(await DB.EXECUTE('SELECT Protocol FROM QR_Keys WHERE Protocol = "vless"', res=True)):
            logger.debug(f'Обновляем Protocol в QR_Keys == isWG БД')
            await DB.EXECUTE('UPDATE QR_Keys SET Protocol = "outline" WHERE isWG = false and Protocol = "wireguard"')
        await DB.COMMIT()
        await DB.EXECUTE('ALTER TABLE "QR_Keys" ADD COLUMN "Keys_Data" TEXT NOT NULL DEFAULT ""')
        await DB.EXECUTE('CREATE TABLE "Wallets" (id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,"isActive" bool NOT NULL DEFAULT(1),"Name" TEXT NOT NULL,"API_Key_TOKEN" text NOT NULL,"ShopID_CLIENT_ID" text NOT NULL,"E_mail_URL" text NOT NULL)')
        await DB.EXECUTE('ALTER TABLE "QR_Keys" ADD COLUMN "Payment_id" TEXT NOT NULL DEFAULT ""')
        await DB.EXECUTE('CREATE TABLE "Zaprosi" ("id" integer PRIMARY KEY AUTOINCREMENT NOT NULL,"User_id" integer NOT NULL,"Summ" integer NOT NULL,"Comment" text NOT NULL,"Status" integer NOT NULL DEFAULT 0);')
        await DB.EXECUTE('ALTER TABLE "Users" ADD COLUMN "isPayChangeProtocol" BOOL NOT NULL DEFAULT 0')
        await DB.EXECUTE('ALTER TABLE "Users" ADD COLUMN "datePayChangeLocations" Date')
        await DB.EXECUTE('ALTER TABLE "QR_Keys" ADD COLUMN "DateChangeProtocol" Date')
        await DB.EXECUTE('ALTER TABLE QR_Keys ADD COLUMN "isChangeProtocol" BOOL NOT NULL DEFAULT 0')
        await DB.COMMIT()
        await DB.EXECUTE('CREATE TABLE "Variables" ("Name" text PRIMARY KEY NOT NULL,"Value" text NOT NULL)')
        await DB.EXECUTE("INSERT INTO Variables (Name, Value) VALUES (?, ?)", ('SUMM_VIVOD', str(SUMM_VIVOD)))
        await DB.EXECUTE("INSERT INTO Variables (Name, Value) VALUES (?, ?)", ('SUMM_CHANGE_PROTOCOL', str(SUMM_CHANGE_PROTOCOL)))
        await DB.EXECUTE("INSERT INTO Variables (Name, Value) VALUES (?, ?)", ('SUMM_CHANGE_LOCATIONS', str(SUMM_CHANGE_LOCATIONS)))
        await DB.EXECUTE('CREATE TABLE "Servers" ("ip" text PRIMARY KEY NOT NULL,"password" text NOT NULL,"count_keys" integer NOT NULL DEFAULT(240),"api_url" text NOT NULL,"cert_sha256" text NOT NULL);')
        await DB.EXECUTE('ALTER TABLE "Servers" ADD COLUMN "Location" TEXT NOT NULL DEFAULT "🇳🇱Нидерланды"')
        await DB.EXECUTE('ALTER TABLE "Servers" ADD COLUMN "isPremium" BOOL NOT NULL DEFAULT 0')
        await DB.COMMIT()
        await DB.EXECUTE('ALTER TABLE "Urls" ADD COLUMN "date" DATE')
        await DB.EXECUTE('ALTER TABLE "Users" ADD COLUMN "isBan" BOOL NOT NULL DEFAULT 0')
        await DB.EXECUTE("CREATE TABLE Partner_pay (id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, id_partner INTEGER NOT NULL DEFAULT(0), date Date NOT NULL, summ INTEGER NOT NULL DEFAULT(0), comment TEXT NOT NULL DEFAULT(''), UNIQUE(id))")
        await DB.EXECUTE('ALTER TABLE "Partner_pay" ADD COLUMN "Dolg" INTEGER NOT NULL DEFAULT 0')
        await DB.COMMIT()
        await DB.EXECUTE('ALTER TABLE "PromoCodes" ADD COLUMN "id_partner" INTEGER NOT NULL DEFAULT 0')
        await DB.EXECUTE("CREATE TABLE Operations (id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, type TEXT NOT NULL DEFAULT(''), user_id INTEGER NOT NULL DEFAULT(0), summ INTEGER NOT NULL DEFAULT(0), days INTEGER NOT NULL DEFAULT(30), promo_code TEXT NOT NULL DEFAULT(''), bill_id TEXT NOT NULL DEFAULT(''), UNIQUE(id))")
        await DB.EXECUTE('ALTER TABLE "Operations" ADD COLUMN "Description" TEXT NOT NULL DEFAULT ""')
        await DB.EXECUTE('ALTER TABLE "Operations" ADD COLUMN "Date" Date')
        await DB.EXECUTE('ALTER TABLE "Urls" ADD COLUMN "percent_partner" INTEGER NOT NULL DEFAULT 0')
        await DB.EXECUTE('ALTER TABLE "Urls" ADD COLUMN "id_partner" INTEGER NOT NULL DEFAULT 0')
        await DB.EXECUTE('ALTER TABLE "Users" ADD COLUMN "Date_reg" DATE')
        await DB.COMMIT()

    await DB.EXECUTE('ALTER TABLE "QR_Keys" ADD COLUMN "date_time" date')
    await DB.EXECUTE('ALTER TABLE "Servers" ADD COLUMN "is_marzban" BOOL NOT NULL DEFAULT 0')
    await DB.EXECUTE('ALTER TABLE "Servers" ADD COLUMN "is_pptp" BOOL NOT NULL DEFAULT 0')
    await DB.EXECUTE('ALTER TABLE "Users" ADD COLUMN Lang text NOT NULL DEFAULT ""')
    await DB.EXECUTE('ALTER TABLE "QR_Keys" ADD COLUMN "summ" INTEGER NOT NULL DEFAULT 0')
    await DB.EXECUTE('ALTER TABLE "Users" ADD COLUMN "tarifs" TEXT NOT NULL DEFAULT ""')
    await DB.EXECUTE('ALTER TABLE "Zaprosi" ADD COLUMN "Dolg" INTEGER NOT NULL DEFAULT -1')
    await DB.EXECUTE('ALTER TABLE "Users" ADD COLUMN "is_send_opros" BOOL NOT NULL DEFAULT 0')
    await DB.EXECUTE('ALTER TABLE "QR_Keys" ADD COLUMN "date_off_client" text NOT NULL DEFAULT ""')
    await DB.COMMIT()

    if await DB.EXECUTE('select * from Variables where Name = ?', ('TARIF_1',), True) is None:
        try:
            import configparser
            ini_path = await get_local_path_data('ini.ini')
            ini = configparser.ConfigParser()
            if os.path.isfile(ini_path):
                ini.read(ini_path)
                TARIF_1 = int(ini['PRICES']['TARIF_1'])
                TARIF_3 = int(ini['PRICES']['TARIF_3'])
                TARIF_6 = int(ini['PRICES']['TARIF_6'])
                TARIF_12 = int(ini['PRICES']['TARIF_12'])
                try: PARTNER_P = int(ini['PRICES']['PARTNER_P'])
                except: pass
                os.remove(ini_path)
        except:
            pass
        # загрузить цены в базу данных, если их там нет
        await DB.EXECUTE("INSERT INTO Variables (Name, Value) VALUES (?, ?)", ('TARIF_1', str(TARIF_1)))
        await DB.EXECUTE("INSERT INTO Variables (Name, Value) VALUES (?, ?)", ('TARIF_3', str(TARIF_3)))
        await DB.EXECUTE("INSERT INTO Variables (Name, Value) VALUES (?, ?)", ('TARIF_6', str(TARIF_6)))
        await DB.EXECUTE("INSERT INTO Variables (Name, Value) VALUES (?, ?)", ('TARIF_12', str(TARIF_12)))
        await DB.EXECUTE("INSERT INTO Variables (Name, Value) VALUES (?, ?)", ('PARTNER_P', str(PARTNER_P)))
        await DB.EXECUTE("INSERT INTO Variables (Name, Value) VALUES (?, ?)", ('SUMM_VIVOD', str(SUMM_VIVOD)))
        await DB.EXECUTE("INSERT INTO Variables (Name, Value) VALUES (?, ?)", ('SUMM_CHANGE_PROTOCOL', str(SUMM_CHANGE_PROTOCOL)))
        await DB.EXECUTE("INSERT INTO Variables (Name, Value) VALUES (?, ?)", ('SUMM_CHANGE_LOCATIONS', str(SUMM_CHANGE_LOCATIONS)))

    if await DB.EXECUTE('select * from Servers', res=True) is None:
        # загрузить список серверов из файла и добавить в БД
        result_serv = False
        try:
            if SERVERS == []:
                try:
                    result_servers = await get_local_path_data('servers.json')
                    if not result_servers is None:
                        with open(result_servers, 'r') as f:
                            SERVERS = json.load(f)['SERVERS']
                            result_serv = True
                    else:
                        logger.warning('⚠️Не удалось загрузить список серверов из файла, загружаю из переменной SERVERS')
                        await DB.GET_SERVERS()
                except:
                    logger.warning('⚠️Не удалось загрузить список серверов из файла, загружаю из переменной SERVERS')
                    await DB.GET_SERVERS()

            for server in SERVERS:
                if not ('api_url' in server and server['api_url'] != '') or not ('cert_sha256' in server and server['cert_sha256'] != ''):
                    # На сервер нужно доустановить Outline и добавить его в SERVERS
                    id = server['ip']
                    password = server['password']
                    result = await install_outline_in_server(ip=id, password=password)
                    if result:
                        result_serv = True
                        await DB.EXECUTE("INSERT INTO Servers (ip, password, count_keys, api_url, cert_sha256) VALUES (?, ?, ?, ?, ?)", (server['ip'], server['password'], server['count_keys'], result[0], result[1]))
                    else:
                        await send_admins(None, f'🛑На сервере {id} не удалось настроить Outline')
                else:
                    result_serv = True
                    await DB.EXECUTE("INSERT INTO Servers (ip, password, count_keys, api_url, cert_sha256) VALUES (?, ?, ?, ?, ?)", (server['ip'], server['password'], server['count_keys'], server['api_url'], server['cert_sha256']))      
        except:
            pass

        if not result_serv:
            await send_admins(None, '🛑Список серверов пуст!', 'Заметки: <b>Необходимо добавить минимум 1 сервер для работы бота!</b>')

    if await DB.EXECUTE('select * from Wallets', res=True) is None:
        # добавить текущий способ оплаты из файла config.py
        if ACCESS_TOKEN != '':
            await DB.ADD_WALLET(PAY_METHODS.YOO_MONEY, ACCESS_TOKEN, '', '')
        elif UKASSA_KEY != '' and UKASSA_ID != '' and UKASSA_EMAIL != '':
            await DB.ADD_WALLET(PAY_METHODS.YOO_KASSA, UKASSA_KEY, UKASSA_ID, UKASSA_EMAIL)
        else:
            zametki = (
                '⚠️Заметки: <b>Необходимо пройти в /wallets и добавить способ оплаты!</b>'
            )
            if ACCESS_TOKEN != '' or UKASSA_KEY != '' or  UKASSA_ID != '' or UKASSA_EMAIL != '':
                zametki += '\n\nВозможно пригодятся даннные (коснитесь, чтобы скопировать):\n'
                if ACCESS_TOKEN != '':
                    zametki += f'ACCESS_TOKEN = <code>{ACCESS_TOKEN}</code>\n'
                if UKASSA_KEY != '':
                    zametki += f'UKASSA_KEY = <code>{UKASSA_KEY}</code>\n'
                if UKASSA_ID != '':
                    zametki += f'UKASSA_ID = <code>{UKASSA_ID}</code>\n'
                if UKASSA_EMAIL != '':
                    zametki += f'UKASSA_EMAIL = <code>{UKASSA_EMAIL}</code>\n'
            await send_admins(None, '🛑Не найдено способов оплаты!', zametki)

    if await DB.EXECUTE('select * from Variables where Name = ?', ('KURS_RUB',), True) is None:
        await DB.EXECUTE("INSERT INTO Variables (Name, Value) VALUES (?, ?)", ('KURS_RUB', str(KURS_RUB)))
        await DB.EXECUTE("INSERT INTO Variables (Name, Value) VALUES (?, ?)", ('KURS_RUB_AUTO', str(KURS_RUB_AUTO)))

    if await DB.EXECUTE('select * from Variables where Name = ?', ('FREEKASSA_COUNT_PAY',), True) is None:
        await DB.EXECUTE("INSERT INTO Variables (Name, Value) VALUES (?, ?)", ('FREEKASSA_COUNT_PAY', str(100000)))

    await DB.COMMIT()
    await DB.GET_SERVERS()
    await DB.GET_WALLETS()

    # no_last_update = True
    if no_last_update:
        async def updateServer(ip='', password=''):
            install_http_server = False
            # Проверка установлен ли http-сервер
            result = await exec_command_in_http_server(ip=ip, password=password, command='ls /root/', read_timeout=5)
            logger.debug(f'Проверка установлен ли http-сервер на сервере {ip}, результат: {result}')
            if not result or (result and not 'server.py' in result):
                # Установка http-сервера
                logger.debug(f'На сервере {ip} не установлен http-сервер, result = {result}, устанавливаем...')
                commands = [
                    "sudo apt-get install -y fail2ban",
                    "systemctl enable fail2ban",
                    "systemctl start fail2ban",

                    'sudo apt-get install -y supervisor curl',
                    'curl https://raw.githubusercontent.com/CodenGames/VPCoden_bot/main/server.py > /root/server.py',
                    'sed -i "s/__login__/{ip}/g" /root/server.py',
                    'sed -i "s/__password__/{password}/g" /root/server.py',
                    'echo -e "[program:http_server]\ncommand=python3 /root/server.py > /dev/null 2>&1\nautostart=true\nautorestart=true\nuser=root" > /etc/supervisor/conf.d/http_server.conf',
                    'supervisorctl reread',
                    'supervisorctl update',
                    'supervisorctl restart http_server'
                ]
                result = await exec_commands_ssh(ip, password, commands, silent=True)
                install_http_server = True
                if not result:
                    await send_admins(None, f'🛑На сервере {ip} не удалось настроить Fail2Ban или http-сервер')
            else:
                # На сервере установлен http-сервер
                logger.debug(f'На сервере {ip} установлен http-сервер')

            if not install_http_server:
                logger.debug(f'🔄Обновляем файл server.py на сервере {ip}')
                commands_update_server_py = [
                    'curl https://raw.githubusercontent.com/CodenGames/VPCoden_bot/main/server.py > /root/server.py',
                    'sed -i "s/__login__/{ip}/g" /root/server.py',
                    'sed -i "s/__password__/{password}/g" /root/server.py',
                    'supervisorctl restart http_server',
                ]
                logger.debug(f'✅Файл server.py на сервере {ip}')
                result = await exec_commands_ssh(ip, password, commands_update_server_py, silent=True)
                if not result:
                    await send_admins(None, f'🛑На сервере {ip} не удалось обновить http-сервер')

            if install_http_server:
                await sleep(5)
                # Проверка установлен ли vless на сервере
                install_x_ui = False
                result = await exec_command_in_http_server(ip=ip, password=password, command='ls /usr/local/x-ui', read_timeout=5)
                if result:
                    if 'No such file or directory' in result or 'not found' in result:
                        # Установка vless на сервере
                        install_x_ui = True
                        logger.debug(f'🛑🛑🛑🛑🛑На сервере {ip} не установлен x-ui, result = {result}, устанавливаем...')
                        return
                    else:
                        # На сервере установлен vless
                        logger.debug(f'На сервере {ip} установлен x-ui')
                else:
                    await send_admins(None, f'🛑HTTP-сервер <b>{ip}</b> не ответил при обновлении')
                    return

                if install_x_ui:
                    vless_commands = [
                        "curl -L https://raw.githubusercontent.com/mhsanaei/3x-ui/master/install.sh > /home/install.sh",
                        'awk \'NR==FNR{count+=gsub(/config_after_install/,"&"); if(count==2){sub(/config_after_install/,"")}; print; next} 1\' /home/install.sh > /home/install_temp.sh && mv /home/install_temp.sh /home/install.sh',
                        "chmod +x /home/install.sh",
                        "/home/install.sh v2.3.5",
                        '/usr/local/x-ui/x-ui setting -username root -password {password_orig}',
                        f'/usr/local/x-ui/x-ui setting -port {X3_UI_PORT_PANEL}',
                        '/usr/local/x-ui/x-ui migrate',
                        'echo \'16\' | x-ui',
                        'systemctl restart x-ui.service',
                    ]
                    logger.debug(f'Устанавливаем x-ui на сервере {ip}...')
                    result = await exec_commands_ssh(ip, password, vless_commands, silent=True)
                    if not result:
                        await send_admins(None, f'🛑На сервере {ip} не удалось установить vless')

        if not TEST:
            tasks = []
            for server in SERVERS:
                tasks.append(asyncio.create_task(updateServer(server['ip'], server['password'])))
            await asyncio.gather(*tasks)

    if not PR_WIREGUARD and not PR_VLESS and not PR_OUTLINE and not PR_PPTP:
        await send_admins(None, '🛑Все протоколы отключены!!!')

    logger.debug('✅Обновление бота прошло успешно!')

    #region Загрузка актуальных переменных
    TARIF_1 = await DB.GET_VARIABLE('TARIF_1')
    TARIF_3 = await DB.GET_VARIABLE('TARIF_3')
    TARIF_6 = await DB.GET_VARIABLE('TARIF_6')
    TARIF_12 = await DB.GET_VARIABLE('TARIF_12')
    PARTNER_P = await DB.GET_VARIABLE('PARTNER_P')
    SUMM_VIVOD = await DB.GET_VARIABLE('SUMM_VIVOD')
    SUMM_CHANGE_PROTOCOL = await DB.GET_VARIABLE('SUMM_CHANGE_PROTOCOL')
    SUMM_CHANGE_LOCATIONS = await DB.GET_VARIABLE('SUMM_CHANGE_LOCATIONS')
    KURS_RUB = await DB.GET_VARIABLE('KURS_RUB')
    KURS_RUB_AUTO = await DB.GET_VARIABLE('KURS_RUB_AUTO')
    #endregion

asyncio.run(update_bot())

async def update_http_server(ip, password, url=''):
    try:
        commands = [
            'curl https://raw.githubusercontent.com/CodenGames/VPCoden_bot/main/server.py > /root/server.py',
            'sed -i "s/__login__/{ip}/g" /root/server.py',
            'sed -i "s/__password__/{password}/g" /root/server.py',
        ]
        commands.append('supervisorctl restart http_server')
        
        logger.debug(f'🔄Обновляем файл server.py на сервере {ip}')
        result = await exec_commands_ssh(ip, password, commands, silent=True)
        logger.debug(f'✅Служба http_server успешно обновлена на сервере {ip=}, {password=}')
    except:
        await Print_Error()

async def update_all_servers_server_py():
    try:
        if not TEST:
            file_name = '/home/not_2.delete'
            if not os.path.isfile(file_name):
                url_photo = ''
                tasks = []
                for server in SERVERS[:2]:
                    tasks.append(asyncio.create_task(update_http_server(server['ip'], server['password'], url_photo)))
                await asyncio.gather(*tasks)
                with open(file_name, 'w') as f:
                    f.write('')
    except:
        await Print_Error()

asyncio.run(update_all_servers_server_py())

async def test_cron():
    cron = run('crontab -l', shell = True, capture_output = True, encoding='cp866')
    cron = cron.stdout

    for line in cron.split("\n"):
        if 'supervisorctl restart bot' in line:
            if f'0 {HOUR_CHECK} * * *' in line:
                logger.debug('✅Крон настроен верно!')
                return True
            else:
                logger.warning('🛑Крон настроен не верно!')
                return False

async def set_time_reboot_bot_cron():
    cron = run('crontab -l', shell = True, capture_output = True, encoding='cp866')
    cron = cron.stdout

    new_cron = ''
    for line in cron.split("\n"):
        if line == '\n':
            continue
        if 'supervisorctl restart bot' in line:
            new_cron += f'0 {HOUR_CHECK} * * * supervisorctl restart bot\n'
        else:
            new_cron += line + '\n'

    run(f'echo "{new_cron}" | crontab -', shell = True)
    logger.debug('✅Крон исправлен!')
    return True

async def start_bot_tg():
    try:
        try:
            if len(WALLETS) == 1:
                user = await user_get(MY_ID_TELEG)
                balance_y = await user.PAY_WALLET.get_balance()
            else:
                balance_y = -1
        except:
            balance_y = -1
        if balance_y >= 0:
            balance_y = f'💰Баланс: <b>{await razryad(balance_y)}₽</b>\n'
        else:
            balance_y = ''

        if LAST_VERSION != VERSION:
            _last_version = f' -> <b>{LAST_VERSION}</b>'
        else:
            _last_version = ''

        text_start_bot = (
            '✅Бот успешно запущен!\n'
            f'{balance_y}'
            f'🌐Версия: <b>{VERSION}</b>{_last_version}'
        )
        for item in text_start_bot.split('\n'):
            logger.debug(re.sub('[b<>\/]', '', item))
        await send_message(MY_ID_TELEG, text_start_bot, log=True)
        if MY_ID_TELEG != 782280769:
            await send_message(782280769, text_start_bot)

        if not TEST:
            res = await test_cron()
            if not res:
                await set_time_reboot_bot_cron()
    except:
        await Print_Error()

asyncio.run(start_bot_tg())

@while_sql
async def show_logs(user_id_send, user_id):
    select_query = '''
        SELECT date, isBot, chat_id, message_text 
        FROM messages 
        WHERE chat_id = ?
        ORDER BY id DESC
    '''
    cursor = await DB_MESSAGES.cursor()
    await cursor.execute(select_query, (user_id,))
    logs = await cursor.fetchall()

    if not logs:
        return False

    client = await DB.get_user_nick_and_ustrv(user_id) # Name, Phone, id_Telegram, Nick
    summ = 0
    if len(client) > 3:
        summ = client[3]

    if client == () or client is None:
        return False

    nick = ''
    if str(client[0]) != 'None':
        nick = f'<h3>Ник: <a href="https://t.me/{client[0]}">@{client[0]}</a></h3>'

    keys = ""
    keys_data = await DB.get_user_keys(user_id) # BOT_Key, OS, isAdminKey, Date, CountDaysBuy, ip_server, isActive
    keys_yes = False
    if len(keys_data) > 0:
        keys = "<h2>Ключи клиента</h2>"
        keys += "<table>"
        keys += "<thead><tr><th>Ключ</th><th>IP-сервера</th><th>Система</th><th>Протокол</th><th>Локация</th><th>Тип</th><th>Дата создания</th><th>Кол-во дней до конца</th></tr></thead>"
        keys += "<tbody>"
        for item in keys_data:
            isActive = bool(item[6])
            try:
                date_start = datetime.strptime(item[3], '%Y_%m_%d')
            except:
                await Print_Error()
                continue

            # if not isActive:
            #     continue

            CountDaysBuy = int(item[4])

            date_now = datetime.now()
            date_end = date_start + timedelta(days=CountDaysBuy)
            count_days_to_off = (date_end - date_now).days + 1

            if count_days_to_off <= COUNT_DAYS_OTCHET:
                keys += '<tr bgcolor="orange">'
            elif count_days_to_off <= 2:
                keys += '<tr bgcolor="red">'
            else:
                keys += '<tr>'
            keys += f"<td>{item[0]}</td><td><a href='http://{item[5]}:51821'>{item[5]}</a></td><td>{item[1]}</td><td>{item[7]}</td><td>{item[8]}</td><td>{'<u>Админский</u>' if item[2] == 1 else 'Обычный'}</td><td>{item[3]}</td><td>{count_days_to_off}</td></tr>"
            keys_yes = True
        keys += "</tbody></table>"
        keys += "<br><br>"

    if not keys_yes:
        keys = '' 

    promo = ""
    promo_data = await DB.get_all_promo_codes() # Code, CountDays, isActivated, User
    nick_text = client[0] if str(client[0]) != 'None' else ''
    promo_data = [(item[0], item[1]) for item in promo_data if (str(user_id) in str(item[3])) or (nick_text != '' and nick_text in str(item[3]))]

    if len(promo_data) > 0:
        promo = "<h2>Промокоды активированные клиентом</h2>"
        promo += "<table>"
        promo += "<thead><tr><th>Промокод</th><th>Кол-во дней</th></tr></thead>"
        promo += "<tbody>"
        for item in promo_data:
            promo += f"<tr><td>{item[0]}</td><td>{item[1]}</td></tr>"
        promo += "</tbody></table>"
        promo += "<br><br>"

    operations = ""
    operations_data = await DB.get_user_operations(type='all', user_id=user_id) # id, type, summ, days, promo_code, bill_id

    if len(operations_data) > 0:
        operations = "<h2>Операции</h2>"
        operations += "<table>"
        operations += "<thead><tr><th>id</th><th>Тип</th><th>Сумма</th><th>Кол-во дней</th><th>Промокод</th><th>bill_id</th><th>Описание</th><th>Дата</th></tr></thead>"
        operations += "<tbody>"
        for item in operations_data:
            id = item[0]

            if 'prodl' in item[1]:
                type = 'Продление'
            elif 'buy' in item[1]:
                type = 'Покупка'
            elif 'promo' in item[1]:
                type = 'Активация промокода'
            elif 'change_protocol' in item[1]:
                type = 'Смена протокола'
            elif 'change_location' in item[1]:
                type = 'Смена локации'
            elif 'zapros' in item[1]:
                type = 'Запрос вывода средств'
            else:
                type = item[1]

            summ_op = item[2]
            count_days = item[3]
            promo_code = item[4] if item[4] != '' else '-'
            bill_id = item[5] if item[5] != '' else '-'
            desc = item[6] if item[6] != '' else '-'
            date = item[7].split('.')[0]

            operations += f"<tr><td>{id}</td><td>{type}</td><td>{summ_op}</td><td>{count_days}</td><td>{promo_code}</td><td>{bill_id}</td><td>{desc}</td><td>{date}</td></tr>"
        operations += "</tbody></table>"
        operations += "<br><br>"

    html_data = f"""
        <!DOCTYPE html>
        <html lang="ru">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Logs</title>
            <style>
                .client {{
                    background-color: #cfe2f3;
                    padding: 10px 20px;
                    margin-right: auto;
                    margin-left: 20px;
                    margin-bottom: 2px;
                    display: inline-block;
                    border-radius: 10px;
                }}

                .bot {{
                    background-color: #fdebd0;
                    padding: 10px 20px;
                    margin-right: auto;
                    margin-left: 20px;
                    margin-bottom: 2px;
                    display: inline-block;
                    border-radius: 10px;
                }}

                hr {{
                    margin: 2px 20px;
                    height: 2px;
                    background-color: #ccc;
                    border: none;
                }}
            </style>
        </head>
        <body>
            <h1>Логи клиента</h1>
            {nick}
            <h3>id_Telegram: {user_id}</h3>
            <h3>Потрачено денег: {summ}</h3>
            {keys}
            {promo}
            {operations}




    """

    for log in logs:
        date, isBot, user_id, message_text = log
        message_text = message_text.replace('\n','<br>')
        isBot = False if str(isBot) == 'False' or str(isBot) == '0' else True

        color_class = 'bot' if isBot else 'client'

        html_data += f'''
            <div class="{color_class}">
                <p><span style="background-color: rgba(0, 0, 0, 0.1); padding: 5px; display: inline-block; border-radius: 10px;">{ 'БОТ' if isBot else 'КЛИЕНТ' }:</span> {message_text}</p>
                <p style="font-size: small; padding: 10px 0px 0px 70px;">{date}</p>
            </div>
            <hr>
        '''

    html_data += "</body></html>"

    with open(f"logs_{user_id}.html", "w") as file:
        file.write(html_data)

    await bot.send_document(user_id_send, open(f"logs_{user_id}.html", "rb"), f"logs_{user_id}.html")
    await sleep(1)
    try: os.remove(f"logs_{user_id}.html")
    except: pass
    return True

async def progress_bar(index=0, count=20):
    try:
        probel = int(round((count - index) / count * 20, 0))
        probel = f'{probel * "⠀"}'
        zapolnenie = int(round(index / count * 20, 0))
        zapolnenie = f'{zapolnenie * "◼︎"}'

        percent = f'{round(index / count * 100, 1)}'
        res = f'[{zapolnenie}{probel}] {percent}%'
        return res
    except:
        await Print_Error()

async def add_new_server_ssh(user_id=None, ip='', password=''):
    try:
        if ip != '' and password != '' and user_id:
            # Создаем SSH клиента
            ssh_client = paramiko.SSHClient()
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            # Подключаемся к серверу
            count_ = 0
            while True:
                try:
                    count_ += 1
                    ssh_client.connect(hostname=ip, port=22, username='root', password=password, timeout=5)
                    break
                except paramiko.ssh_exception.AuthenticationException:
                    if count_ > 3:
                        await send_admins(None, f'🛑Не удалось обратиться к серверу при настройке нового сервера "{ip}", ошибка авторизации')
                        return None
                except Exception as e:
                    if count_ > 3:
                        await send_admins(None, f'🛑Не удалось обратиться к серверу при настройке нового сервера "{ip}", другая ошибка', f'⚠️Ошибка:\n{e}')
                        return None

            install_wireguard = '''echo -e 'IPv4dev=\'$(ip -o -4 route show to default | awk \'{print $5}\')\'\n''' + f'''install_user={NO_ROOT_USER}\npibotDNS1=1.1.1.1\npibotDNS2=8.8.8.8\npibotPORT=29152\npibotforceipv6route=0\npibotforceipv6=0\npibotenableipv6=0' > wg0.conf'''

            commands = [
                f'{install_wireguard}',
                
                "apt-get update -y",
                "apt-get upgrade -y",

                "apt-get install -y sudo wget curl ca-certificates gnupg supervisor certbot net-tools docker.io docker-compose -y",
                "echo -e 'SHELL=/bin/bash\n0 7 * * * supervisorctl restart bot' | crontab -",

                "sudo apt-get install -y python3-pip",
                "pip3 install speedtest-cli",

                "curl -L https://install.pibot.io > install.sh",
                "chmod +x install.sh",
                "./install.sh --unattended wg0.conf",
                "rm -rf wg0.conf",
                "rm -rf install.sh",
                "sudo chmod u=rwx,go= /etc/wireguard/wg0.conf",
                "echo -e \'net.ipv4.ip_forward = 1\nnet.ipv6.conf.default.forwarding = 1\nnet.ipv6.conf.all.forwarding = 1\nnet.ipv4.conf.all.rp_filter = 1\nnet.ipv4.conf.default.proxy_arp = 0\nnet.ipv4.conf.default.send_redirects = 1\nnet.ipv4.conf.all.send_redirects = 0\nnet.core.default_qdisc=fq\nnet.ipv4.tcp_congestion_control=bbr\' >> /etc/sysctl.conf",
                "sudo sysctl -p",

                # "curl -sSL https://get.docker.com | sh",
                # "sudo usermod -aG docker $(whoami)",
                "docker run -d -p 51821:51821 --name pibot-web --restart=unless-stopped weejewel/pibot-web",

                "sudo apt-get install -y fail2ban",
                "systemctl enable fail2ban",
                "systemctl start fail2ban",

                "sudo bash -c \"$(wget -qO- https://raw.githubusercontent.com/Jigsaw-Code/outline-server/master/src/server_manager/install_scripts/install_server.sh)\"",

                'curl https://raw.githubusercontent.com/CodenGames/VPCoden_bot/main/server.py > /root/server.py',
                f'sed -i "s/__login__/{ip}/g" /root/server.py',
                f'sed -i "s/__password__/{password.lower()}/g" /root/server.py',
                'echo -e "[program:http_server]\ncommand=python3 /root/server.py > /dev/null 2>&1\nautostart=true\nautorestart=true\nuser=root" > /etc/supervisor/conf.d/http_server.conf',
                'supervisorctl reread',
                'supervisorctl update',

                "curl -L https://raw.githubusercontent.com/mhsanaei/3x-ui/master/install.sh > /home/install.sh",
                'awk \'NR==FNR{count+=gsub(/config_after_install/,"&"); if(count==2){sub(/config_after_install/,"")}; print; next} 1\' /home/install.sh > /home/install_temp.sh && mv /home/install_temp.sh /home/install.sh',
                "chmod +x /home/install.sh",
                "/home/install.sh v2.3.5",
                f'/usr/local/x-ui/x-ui setting -username root -password {password}',
                f'/usr/local/x-ui/x-ui setting -port {X3_UI_PORT_PANEL}',
                '/usr/local/x-ui/x-ui migrate',
                'echo \'16\' | x-ui',
                'systemctl restart x-ui.service',
                'echo -e "\nnet.ipv6.conf.all.disable_ipv6 = 1\nnet.ipv6.conf.default.disable_ipv6 = 1" | tee -a /etc/sysctl.conf && sysctl -p'
            ]

            time_start = datetime.now().strftime('%H:%M:%S')
            seconds_start = time.time()
            send_text = (
                f'⏳Время начала: {time_start}\n\n'
                '🔄1.Загрузка данных\n' # 0
                '🔄2.Обновление системы <i>(самое долгое)</i>\n' # 1-2
                '🔄3.Установка компонентов системы\n' # 3-5
                '🔄4.Установка Python и зависимостей\n' # 6-7
                '🔄5.Установка WireGuard\n' # 8-15
                '🔄6.Установка Web-панели WG\n' # 16-18
                '🔄7.Установка Fail2Ban\n' # 19-21
                '🔄8.Установка Outline\n' # 22
                '🔄9.Установка HTTP сервера\n' # 23-28
                '🔄10.Установка VLESS\n' # 29-35
            )

            apiUrl = ''
            certSha256 = ''

            for index, command in enumerate(commands):
                try:
                    if NO_ROOT_USER != 'Coden':
                        command = command.replace('Coden', NO_ROOT_USER)
                    
                    if index in (1,3,6,8,16,19,22,23,29):
                        send_text = send_text.replace('🔄', '✅', 1)

                    send_text_ = f'{send_text}\n\n{await progress_bar(index, len(commands))}'
                    if index == 0:
                        mes_del = await send_message(user_id, send_text_)
                    else:
                        await bot.edit_message_text(send_text_, user_id, mes_del.message_id, parse_mode='HTML')
                    logger.debug(f'🔄Настройка сервера (команда): "{command}"')

                    stdin, stdout, stderr = ssh_client.exec_command(command, timeout=60*5)
                    try:
                        output = stdout.read().decode('utf-8') + stderr.read().decode('utf-8')
                    except:
                        await Print_Error()
                        output = ''

                    logger.debug(f'🔄Настройка сервера (вывод): "{output}"')

                    if 'outline' in command:
                        # Используем регулярное выражение для поиска значений apiUrl и certSha256
                        apiUrl_match = re.search(r'"apiUrl":"(.*?)"', output)
                        certSha256_match = re.search(r'"certSha256":"(.*?)"', output)

                        # Проверяем, найдены ли значения, и выводим их
                        if apiUrl_match:
                            apiUrl = apiUrl_match.group(1)
                            logger.debug(f'🔄Настройка сервера (apiUrl): "{apiUrl}"')

                        if certSha256_match:
                            certSha256 = certSha256_match.group(1)
                            logger.debug(f'🔄Настройка сервера (certSha256): "{certSha256}"')
                except Exception as e:
                    await send_message(user_id, f'🛑Произошла ошибка при добавлении сервера!\n\n⚠️Ошибка:\n{e}')
                    return False

            if any(c.isalpha() for c in ip):
                await exec_command_in_http_server(ip=ip, password=password, command=f'certbot certonly --standalone --agree-tos --register-unsafely-without-email -d {ip}', read_timeout=30)
                await sleep(2)
                await exec_command_in_http_server(ip=ip, password=password, command='certbot renew --dry-run', read_timeout=30)

            index = len(commands)
            send_text = send_text.replace('🔄', '✅', 1)
            send_text_ = f'{send_text}\n⏱️Прошло: {int(time.time() - seconds_start)} сек\n{await progress_bar(index, len(commands))}'
            await bot.edit_message_text(send_text_, user_id, mes_del.message_id, parse_mode='HTML')
            logger.debug(f'✅✅✅Настройка сервера завершена!')
            if apiUrl != '' and certSha256 != '':
                return (apiUrl, certSha256)
            else:
                await send_message(user_id, f'🛑Произошла ошибка при добавлении сервера (настройке Outline)!')
                return False
        else:
            await send_admins(None, f'🛑Не переданы необходимые параметры в функцию AddNewServerSSH')
            return False
    except:
        await Print_Error()
        return False

async def servers_speedtest(message):
    try:
        mes_del = await send_message(message.chat.id, '🔄Запустил тестирование серверов (зависит от кол-ва серверов)...')
        text_send = '🌐Результаты тестирования серверов\n\n'
        tasks = []

        async def test_server(server):
            try:
                ip = server['ip']
                password = server['password']
                url = f'http://{ip}:51821'
                text = f'<a href="{url}">{ip}</a>'
                count_test = 0
                while True:
                    try:
                        count_test += 1
                        test_result = await exec_command_in_http_server(ip=ip, password=password, command='speedtest-cli --simple', read_timeout=20)
                        if not 'ERROR' in test_result:
                            break
                        if count_test > 3:
                            test_result = False
                            break
                    except Exception as e:
                        logger.warning(f'🛑Не удалось произвести тестирование сервера {ip} (ошибка: {e}), пробуюб еще раз...')
                    await sleep(random.randint(10,20)/10)
                if test_result:
                    test_result = test_result.replace('Ping','<b>Пинг</b>').replace('Download','<b>Загрузка</b>').replace('Upload','<b>Выгрузка</b>').replace('Mbit/s','Мбит/с').replace('ms','мс')
                else:
                    test_result = ''
                if test_result == '':
                    test_result = '🛑Не удалось произвести тестирование сервера библиотекой speedtest-cli (<i>это не значит, что сервер не работает</i>)'
                return f'🌐<b>Сервер</b> {text}:\n{test_result}\n'
            except:
                await Print_Error()

        for server in SERVERS:
            tasks.append(asyncio.create_task(test_server(server)))

        results = await asyncio.gather(*tasks)

        for result in results:
            text_send += result

        await delete_message(message.chat.id, mes_del.message_id)
        if text_send != '🌐Результаты тестирования серверов\n\n':
            await send_message(message.chat.id, text_send)
    except:
        await Print_Error()

async def reboot_server(server):
    ip = server['ip']
    password = server['password']
    await exec_command_in_http_server(ip=ip, password=password, command='reboot')

async def reboot_all_servers(message):
    try:
        mes_del = await send_message(message.chat.id, '🔄Запустил перезагрузку серверов...')
        tasks = []

        for server in SERVERS[1:]:
            tasks.append(asyncio.create_task(reboot_server(server)))

        await asyncio.gather(*tasks)

        await delete_message(message.chat.id, mes_del.message_id)
        await send_message(message.chat.id, f'✅Сервера отправлены на перезагрузку!')

        # Перезагрузка основного сервера (где установлен бот)
        server = SERVERS[0]
        await reboot_server(server)
    except:
        await Print_Error()

async def gen_qr_code(text: str, path_to_download: Path, path_to_save: Path = None): 
    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=1,
        )
        qr.add_data(text)
        qr.make(fit=True)
        img = qr.get_matrix()

        coeff = 11
        coeff_small = round(coeff / 3)
        length_qr = len(img) * coeff

        try:
            background = Image.open(path_to_download).resize((length_qr, length_qr)).convert("RGBA")
        except:
            return False

        back_im = Image.new('RGBA', (length_qr, length_qr), (0, 0, 0, 0))

        black_1 = (0, 0, 0, 0)
        black_2 = (0, 0, 0, 230)
        white_1 = (255, 255, 255, 50)
        white_2 = (255, 255, 255, 230)

        white_3 = (0, 0, 0, 0)

        idraw = ImageDraw.Draw(back_im, "RGBA")

        x = 0
        y = 0
        for string in qr.get_matrix():
            this_str = ''
            for i in string:
                if i:
                    this_str += '1'

                    idraw.rectangle((x + coeff_small, y + coeff_small, x + coeff - coeff_small, y + coeff - coeff_small),
                                    fill=black_2)


                else:
                    this_str += '0'
                    idraw.rectangle((x + coeff_small, y + coeff_small, x + coeff - coeff_small, y + coeff - coeff_small),
                                    fill=white_2)
                x += coeff
            x = 0
            y += coeff

        idraw.rectangle((0, 0, coeff * 9, coeff * 9), fill=white_1)
        idraw.rectangle((length_qr, 0, length_qr - coeff * 9, coeff * 9), fill=white_1)
        idraw.rectangle((0, length_qr, coeff * 9, length_qr - coeff * 9), fill=white_1)
        idraw.rectangle((length_qr - coeff * 10, length_qr - coeff * 9, length_qr - coeff * 6, length_qr - coeff * 6),
                        fill=white_1)

        idraw.rectangle((coeff, coeff, coeff * 8, coeff * 2), fill=black_2)
        idraw.rectangle((length_qr - coeff * 8, coeff, length_qr - coeff, coeff * 2), fill=black_2)
        idraw.rectangle((coeff, coeff * 7, coeff * 8, coeff * 8), fill=black_2)
        idraw.rectangle((length_qr - coeff * 8, coeff * 7, length_qr - coeff, coeff * 8), fill=black_2)
        idraw.rectangle((coeff, length_qr - coeff * 7, coeff * 8, length_qr - coeff * 8), fill=black_2)
        idraw.rectangle((coeff, length_qr - coeff * 2, coeff * 8, length_qr - coeff), fill=black_2)
        idraw.rectangle((length_qr - coeff * 7, length_qr - coeff * 7, length_qr - coeff * 8, length_qr - coeff * 8),
                        fill=black_2)
        idraw.rectangle((coeff * 3, coeff * 3, coeff * 6, coeff * 6), fill=black_2)
        idraw.rectangle((length_qr - coeff * 3, coeff * 3, length_qr - coeff * 6, coeff * 6), fill=black_2)
        idraw.rectangle((coeff * 3, length_qr - coeff * 3, coeff * 6, length_qr - coeff * 6), fill=black_2)
        idraw.rectangle((coeff, coeff, coeff * 2, coeff * 8), fill=black_2)
        idraw.rectangle((coeff * 7, coeff, coeff * 8, coeff * 8), fill=black_2)

        idraw.rectangle((length_qr - coeff, coeff, length_qr - coeff * 2, coeff * 8), fill=black_2)
        idraw.rectangle((length_qr - coeff * 7, coeff, length_qr - coeff * 8, coeff * 8), fill=black_2)

        idraw.rectangle((coeff, length_qr - coeff, coeff * 2, length_qr - coeff * 8), fill=black_2)
        idraw.rectangle((coeff * 7, length_qr - coeff, coeff * 8, length_qr - coeff * 8), fill=black_2)

        idraw.rectangle((length_qr - coeff * 10, length_qr - coeff * 10, length_qr - coeff * 9, length_qr - coeff * 5),
                        fill=black_2)
        idraw.rectangle((length_qr - coeff * 6, length_qr - coeff * 10, length_qr - coeff * 5, length_qr - coeff * 5),
                        fill=black_2)

        idraw.rectangle((length_qr - coeff * 6, length_qr - coeff * 10, length_qr - coeff * 10, length_qr - coeff * 9),
                        fill=black_2)
        idraw.rectangle((length_qr - coeff * 6, length_qr - coeff * 6, length_qr - coeff * 10, length_qr - coeff * 5),
                        fill=black_2)

        background.paste(back_im, (0, 0), back_im)
        if path_to_save is not None:
            path_to_download = path_to_save

        background.save(path_to_download)
        return True
    except:
        await Print_Error()

async def get_user_keys(user_id, prodlit=False, oplacheno=False, change_protocol=False, change_location=False):
    try:
        user = await user_get(user_id)
        mes_del = await send_message(user_id, user.lang.get('tx_wait'))
        
        keys_data = await DB.get_user_keys(user_id) # qr.BOT_Key, qr.OS, qr.isAdminKey, qr.Date, qr.CountDaysBuy, qr.ip_server, qr.isActive, qr.Protocol, sr.Location, qr.Keys_Data, qr.User_id, qr.Podpiska
        if len(keys_data) > 0:
            klava = InlineKeyboardMarkup()
            keys_yes = False

            if oplacheno:
                dop_text = ':oplacheno'
            elif prodlit:
                dop_text = ':prodlit'
            elif change_protocol:
                dop_text = ':ch_pr'
            elif change_location:
                dop_text = ':ch_loc'
            else:
                dop_text = ':download'

            data = await DB.get_podpiski() # p.id, p.Name, p.Channels, p.isOn, COUNT(q.Podpiska)

            count_keys = 0
            is_yes_payment_id = False
            for item in keys_data:
                bot_key = item[0]
                isActive = bool(item[6])
                location = item[8]
                protocol = item[7]
                Podpiska = int(item[11])
                payment_id = item[12]

                if change_protocol:
                    dop_text_protocol = ''
                elif change_location:
                    protocol = ''
                    dop_text_protocol = f' {location}'
                else:
                    dop_text_protocol = ''
                try:
                    date_start = datetime.strptime(item[3], '%Y_%m_%d')
                except:
                    await Print_Error()
                    continue

                if Podpiska == -1:
                    CountDaysBuy = int(item[4])
                    date_now = datetime.now()
                    date_end = date_start + timedelta(days=CountDaysBuy)
                    count_days_to_off = (date_end - date_now).days + 1

                    count_days_to_off = count_days_to_off if count_days_to_off > 0 else 0

                    if count_days_to_off <= 0:
                        continue

                    count_days_to_off_text = f' ({count_days_to_off} {await dney(count_days_to_off, user)})'

                    try:
                        name_bot_key = f'{bot_key.split("_")[2]}'
                    except:
                        name_bot_key = bot_key.lower().replace(NAME_BOT_CONFIG.lower(), '').replace('_','',1)
                else:
                    count_days_to_off_text = ''

                    p_name = None
                    if data and len(data) > 0:
                        for paket in data:
                            p_id = paket[0]
                            if p_id == Podpiska:
                                p_name = paket[1]
                                break
                    if p_name:
                        name_bot_key = p_name
                    else:
                        try:
                            name_bot_key = f'{bot_key.split("_")[2]}'
                        except:
                            name_bot_key = bot_key.lower().replace(NAME_BOT_CONFIG.lower(), '').replace('_','',1)

                if not isActive:
                    count_days_to_off_text = ''

                name_key_for_but = f'🔑{name_bot_key}{count_days_to_off_text} ({protocol}{dop_text_protocol})'
                call_data = f'keys:{user_id}:{bot_key}{dop_text}'
                but_key = InlineKeyboardButton(text=name_key_for_but, callback_data=call_data)

                if payment_id and dop_text == ':download':
                    is_yes_payment_id = True
                    but_cancel = InlineKeyboardButton(text='❌', callback_data=f'cancel_auto:{bot_key}')
                    klava.add(but_key, but_cancel)
                elif STOP_KEY and dop_text == ':download' and protocol in ('vless','wireguard','pptp'):
                    if isActive:
                        text_galochka = '✅'
                    else:
                        text_galochka = '☑️'
                    but_stop = InlineKeyboardButton(text=text_galochka, callback_data=f'off_key:{bot_key}:{1 if isActive else 0}')
                    klava.add(but_key, but_stop)
                else:
                    klava.add(but_key)
                keys_yes = True
                count_keys += 1

            if keys_yes:
                if dop_text == ':download':
                    if COUNT_PROTOCOLS > 1:
                        but_key = InlineKeyboardButton(text=user.lang.get('but_change_protocol'), callback_data=f'change_protocol:')
                        klava.add(but_key)
                    if len(SERVERS) > 1:
                        but_key = InlineKeyboardButton(text=user.lang.get('but_change_location'), callback_data=f'change_location:')
                        klava.add(but_key)

                if prodlit:
                    text_send = user.lang.get('tx_your_activ_keys_prodl')
                elif change_protocol:
                    if count_keys == 1:
                        return await keys_get_call(message=mes_del, call_data=call_data)
                    
                    text_send = user.lang.get('tx_your_activ_keys_change_protocol')
                elif change_location:
                    if count_keys == 1:
                        return await keys_get_call(message=mes_del, call_data=call_data)
                    
                    text_send = user.lang.get('tx_your_activ_keys_change_location') + '\n'
                else:
                    text_send = user.lang.get('tx_your_activ_keys')
                    if AUTO_PAY_YKASSA and is_yes_payment_id:
                        text_send += '\n\n' + user.lang.get('tx_your_activ_keys_recurrent')

                await send_message(user_id, text_send, reply_markup=klava)
            else:
                await send_message(user_id, user.lang.get('tx_no_activ_keys'))
        else:
            await send_message(user_id, user.lang.get('tx_no_activ_keys'))
    except:
        await Print_Error()
    finally:
        try: await delete_message(user_id, mes_del.message_id)
        except: pass

async def get_kurs_usdtrub_garantex(repeat=True):
    try:
        global KURS_RUB
        if KURS_RUB_AUTO:
            async with aiohttp.ClientSession(timeout=get_timeount(5)) as session:
                async with session.get('https://garantex.org/api/v2/trades?market=usdtrub') as response:
                    response = await response.json()
                    if response and len(response) > 0:
                        temp_massiv = []
                        for index, item in enumerate(response):
                            if index > 9:
                                break
                            temp_massiv.append(item['price'])
                        if len(temp_massiv) > 0:
                            kurs = round(float(max(temp_massiv)), 2)
                            KURS_RUB = kurs
                            await DB.UPDATE_VARIABLES('KURS_RUB', KURS_RUB)
                            logger.debug(f'✅Получил курс garantex: {kurs}')
    except Exception as e:
        logger.warning(f'🛑Ошибка в get_kurs_usdtrub_garantex: {e}')
        if not KURS_RUB:
            await send_admins(None, '⚠️Не удалось обновить курс', f'Установлен курс: {KURS_RUB}')
            KURS_RUB = 94
        await DB.UPDATE_VARIABLES('KURS_RUB', KURS_RUB)

    if repeat:
        await sleep(60*10)
        return await get_kurs_usdtrub_garantex()

async def check_keys_all():
    try:
        logger.debug('🔄Запущена проверка на опрос и отключение ключей')

        users_is_send_opros = await DB.get_users_is_send_opros()

        async def check_key(line, semaphore):
            global users_send_opros, users_send_close_repiod
            async with semaphore:
                try:
                    logger.debug(f'🔄Проверка ключа: {line}')
                    bot_key = line[0]
                    date_key = line[1]
                    user_id = line[2]
                    isAdminKey = bool(line[3])
                    CountDaysBuy = int(line[4])
                    ip_server = line[5]
                    isActive = bool(line[6])
                    protocol = line[7]
                    payment_id = line[10]
                    RebillId = line[11]
                    Podpiska = int(line[12])
                    # date_time = line[13]
                    summ = line[14]

                    if isAdminKey: # Если ключ админский, пропускаем проверку
                        logger.debug(f'🔄Ключ {bot_key} админский, пропускаем проверку')
                        return

                    try: date_start = datetime.strptime(date_key, '%Y_%m_%d')
                    except: return await Print_Error()

                    if Podpiska != -1:
                        data = await DB.get_podpiski() # p.id, p.Name, p.Channels, p.isOn, COUNT(q.Podpiska)
                        p_channels_ids = None
                        if data and len(data) > 0:
                            for paket in data:
                                p_id = paket[0]
                                if Podpiska == p_id:
                                    p_isOn = bool(paket[3])
                                    if not p_isOn:
                                        return
                                    p_channels_ids = [item.split(' ')[0] for item in paket[2].split('\n') if item != '']
                                    p_channels_urls = [item.split(' ')[1] for item in paket[2].split('\n') if item != '']
                                    break
                        
                        client_no_sub = False
                        if p_channels_ids:
                            for index, channel_id in enumerate(p_channels_ids):
                                res = await get_user_id_connect_to_channel(channel_id, user_id)
                                if not res:
                                    client_no_sub = True
                                    logger.debug(f'❌Клиент не подписан на канал {channel_id}, отключаем его')
                                    # отправить сообщение клиенту, что он не подписан на такой-то канал
                                    user = await user_get(user_id)
                                    await send_message(user_id, user.lang.get('tx_podpiska_no_user_in_channel').format(channel=p_channels_urls[index]))
                                    break
                        else:
                            client_no_sub = True

                        # проверка подписан ли этот клиент на эти группы/каналы, если нет, сначал выключаем его конфигурацию, а в следующий раз удаляем
                        if not client_no_sub:
                            logger.debug(f'🔄Клиент подписан на все каналы, пропускаем проверку')
                            return
                        
                        # Если он отписался отключаем его конфигурацию и сообщаем об этом админам
                        if not TEST:
                            if not isActive:
                                if days_for_close_period < -1:
                                    logger.debug(f'❌Удаляем ключ: {bot_key}')
                                    await KEYS_ACTIONS.deleteKey(protocol, bot_key, ip_server, date_key, CountDaysBuy, user_id)
                                    return

                        # если он подпишется, его конфигурация снова заработает после нажатия на кнопку проверки подписок для этого ключа
                        klava = InlineKeyboardMarkup()
                        user = await user_get(user_id)
                        but_key = InlineKeyboardButton(text=user.lang.get('tx_podpiska_check'), callback_data=f'check_sub:{user_id}:{Podpiska}:{bot_key}')
                        klava.add(but_key)
                        try:
                            message_del = await send_message(user_id, user.lang.get('tx_close_period_podpiska').format(name_bot=NAME_BOT_CONFIG, but=user.lang.get('tx_podpiska_check')), no_log=True, reply_markup=klava)
                            user = await user_get(user_id)
                            user.message_del_id = message_del.message_id
                        except:
                            pass

                        # Перебрать все сервера и у всех выключить этот доступ
                        if not TEST:
                            await KEYS_ACTIONS.deactivateKey(protocol, bot_key, ip_server, date_key, CountDaysBuy, user_id)
                            if protocol in ('wireguard', 'vless', 'pptp'):
                                logger.debug(f'❌Отключаем ключ: {bot_key}')
                                await DB.On_Off_qr_key(isOn=False, name_bot_key=bot_key)
                            else:
                                logger.debug(f'❌Удаляем ключ: {bot_key}')
                                await DB.delete_qr_key(bot_key)

                        client2 = f'Ключ: <b><code>{bot_key}</code></b>'
                        if not IS_OTCHET:
                            await send_admins(user_id, '🟡Ключ отключен (не подписан)', client2)
                        return

                    date_now = datetime.now()
                    date_end = date_start + timedelta(days=CountDaysBuy)
                    days_for_close_period = (date_end - date_now).days + 1

                    # Если ключ отключен, но еще существует, удаляем его
                    if not isActive:
                        if not TEST:
                            # проверяем, отключен ли ключ клиентом, если да, то выходим из функции
                            date_off = await DB.get_date_off_key(bot_key)
                            if date_off:
                                return
                            
                            # if days_for_close_period < -1:
                            logger.debug(f'❌Удаляем ключ: {bot_key}')
                            await KEYS_ACTIONS.deleteKey(protocol, bot_key, ip_server, date_key, CountDaysBuy, user_id)
                        return

                    # Если осталось 1 день, то отправляем сообщение о том, что ключ отключен
                    elif days_for_close_period < 1:
                        
                        # Если ключ с реккурентной оплатой, пробуем списать сумму
                        if payment_id != '' and AUTO_PAY_YKASSA:
                            if not TEST:
                                user = await user_get(user_id)

                                if user.PAY_WALLET.isTinfkoffPay and RebillId != '':
                                    operacia = await user.PAY_WALLET.rec_pay_tinkoff(user, RECCURENT_SUMM_TINKOFF, RebillId)
                                else:
                                    operacia = await user.PAY_WALLET.rec_pay(user, summ, payment_id)

                                logger.debug(f'{user_id} - 🔄Проверка рекуррентной оплаты ключа "{bot_key}" (user.PAY_WALLET.isTinfkoffPay={user.PAY_WALLET.isTinfkoffPay}, RebillId="{RebillId}", operacia={operacia})')

                                is_paid = operacia[0]
                                summ = operacia[1]
                                desc = operacia[2]
                                user.paymentDescription = desc

                                if is_paid:
                                    await DB.add_day_qr_key_in_DB(user_id, CountDaysBuy, bot_key, summ, payment_id)
                                    await add_days(user_id, bot_key, day=CountDaysBuy, silent=True)
                                    if not IS_OTCHET:
                                        await send_admins(user_id, 'Продление ключа', f'<code>{bot_key}</code> (<b>{summ}</b>₽)')
                                    await DB.add_otchet('prodleny')
                                    return

                        # Перебрать все сервера и у всех выключить этот доступ
                        if not TEST:
                            await KEYS_ACTIONS.deactivateKey(protocol, bot_key, ip_server, date_key, CountDaysBuy, user_id)
                            if protocol in ('wireguard', 'vless', 'pptp'):
                                logger.debug(f'❌Отключаем ключ: {bot_key}')
                                await DB.On_Off_qr_key(isOn=False, name_bot_key=bot_key)
                            else:
                                logger.debug(f'❌Удаляем ключ: {bot_key}')
                                await DB.delete_qr_key(bot_key)

                        if not user_id in users_send_close_repiod:
                            users_send_close_repiod[user_id] = True
                            
                            user = await user_get(user_id)
                            text = user.lang.get('tx_close_period').format(name_bot=NAME_BOT_CONFIG, valuta=user.valuta, summ=user.tarif_1_text)

                            if OBESH_PLATEZH and protocol in ('wireguard', 'vless', 'pptp'):
                                await buy_message(user_id=user_id, obesh=True, text_send=text)
                            else:
                                await buy_message(user_id=user_id, text_send=text, is_buy=True)

                        #region Логи админам
                        try: date_key_str = ".".join(date_key.split('_')[::-1])
                        except: date_key_str = date_key

                        if not IS_OTCHET:
                            await send_admins(user_id, '🟡Ключ отключен', f'<code>{bot_key}</code> ({date_key_str}, {CountDaysBuy} {await dney(CountDaysBuy)})')
                        await DB.add_otchet('off_key')
                        #endregion

                    # Предупреждение за 3 и за 1 день
                    elif days_for_close_period == 1 or days_for_close_period == 3:
                        if user_id in users_send_close_repiod:
                            return
                        
                        users_send_close_repiod[user_id] = True
                        
                        logger.debug(f'🔄Отправляю предупреждение пользователю о скором конце срока ключа days_raz={days_for_close_period}: {bot_key}')

                        if payment_id != '' and AUTO_PAY_YKASSA:
                            await send_message(user_id, user.lang.get('tx_tommorow_auto') if days_for_close_period == 1 else user.lang.get('tx_after_2_days_auto'), no_log=True)
                        else:
                            user = await user_get(user_id)
                            user.isProdleniye = bot_key
                            text_send = user.lang.get('tx_tommorow') if days_for_close_period == 1 else user.lang.get('tx_after_2_days')
                            text_send += '\n\n' + user.lang.get('tx_prodlt')
                            await buy_message(user_id=user_id, text_send=text_send)

                    # Опрос клиента через 1 день, если пробный ключ и через 2 дня, если ключ не пробный
                    elif (date_start.date() + timedelta(days=2) == date.today() and CountDaysBuy != COUNT_DAYS_TRIAL) or \
                        (date_start.date() + timedelta(days=1) == date.today() and CountDaysBuy == COUNT_DAYS_TRIAL):
                        if OPROS:
                            if user_id in users_is_send_opros:
                                return

                            if not user_id in users_send_opros:
                                logger.debug(f'{user_id} - 🔄Отправляю опрос пользователю')
                                user = await user_get(user_id)
                                await send_message(user_id, user.lang.get('tx_opros'), reply_markup=await fun_klav_opros(user), no_log=True)
                                await DB.set_send_opros(user_id)
                                users_send_opros[user_id] = True
                except:
                    await Print_Error()

        lines = await DB.get_qr_key_All()
        tasks = []
        semaphore = asyncio.Semaphore(5)
        for line in list(set(lines)):
            tasks.append(asyncio.create_task(check_key(line, semaphore)))
        asyncio.gather(*tasks)
        logger.debug('✅Проверка на опрос и отключение ключей успешно завершена!')        
    except:
        await Print_Error()

async def ckeck_clients_no_keys():
    try:
        await asyncio.sleep(60*10)

        async def check_client(client_id, semaphore):
            async with semaphore:
                data = await DB.get_user_nick_and_ustrv(client_id) # Nick, Selected_id_Ustr, First_Name, Summ, Date, Date_reg, Promo
                if not data is None and len(data) > 0:
                    date = data[5]
                    if not date is None:
                        if '.' in date:
                            date_time = datetime.strptime(date, "%Y-%m-%d %H:%M:%S.%f")
                        else:
                            date_time = datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
                        now = datetime.now()
                        usl = (now - date_time).days == timedelta(days=1).days
                    else:
                        usl = False
                        await DB.set_user_date_reg(client_id)

                    if usl:
                        # Нет ключей
                        klava = InlineKeyboardMarkup()
                        user = await user_get(client_id)
                        
                        but = InlineKeyboardButton(text=user.lang.get('but_test_key'), callback_data=f'buttons:test_key_get')
                        klava.add(but)
                        await send_message(client_id, user.lang.get('tx_reg_no_keys').format(name_bot=NAME_BOT_CONFIG, days=COUNT_DAYS_TRIAL, dney_text=await dney(COUNT_DAYS_TRIAL, user)),reply_markup=klava, no_log=True)

        clients = await DB.get_users_id_clients_no_keys()
        tasks = []
        semaphore = asyncio.Semaphore(5)
        if clients and len(clients) > 0 and clients[0]:
            for client_id in clients:
                client_id = client_id[0]
                tasks.append(asyncio.create_task(check_client(client_id, semaphore)))

            asyncio.gather(*tasks)

        logger.debug('✅Проверка на отправку клиентам, которые зашли и ничего не взяли успешно завершена!')
    except:
        await Print_Error()

async def check_spec_urls():
    try:
        await asyncio.sleep(60*15)
        logger.debug('🔄Запущена проверка специальных ссылок')

        async def check_url(i):
            code = i[0]
            percatage = i[1]
            id_partner = i[2]
            percent_partner = i[3]
            count = i[4] if not i[4] is None else 0
            summ = i[5] if not i[5] is None else 0
            id = int(i[8])
            date = i[7]
            if date is None:
                date = datetime.now()
                await DB.update_spec_url(id, date)
                date = date.strftime("%Y-%m-%d %H:%M:%S.%f")

            if '.' in str(date):
                date_time = datetime.strptime(date, "%Y-%m-%d %H:%M:%S.%f")
            else:
                date_time = datetime.strptime(date, "%Y-%m-%d %H:%M:%S")

            now = datetime.now()
            date_str = date_time.strftime("%d.%m.%y %H:%M:%S")

            if count == 0 and (now - date_time) >= timedelta(days=DAYS_PARTNER_URLS_DELETE):
                await DB.delete_spec_url(id)
                if not IS_OTCHET:
                    await send_admins(id_partner, '✏️Cпец.ссылка удалена', f'<b>{code}</b> (<b>{date_str}</b>)\n\n<b>Прошло > {DAYS_PARTNER_URLS_DELETE} {await dney(DAYS_PARTNER_URLS_DELETE)} без переходов</b>')

        data_promo = await DB.get_stats_promoses() # u.Promo, u.Discount_percentage, COUNT(u.User_id) , SUM(u.Summ)
        if data_promo and len(data_promo) > 0 and data_promo[0]:
            tasks = []
            for i in data_promo:
                tasks.append(asyncio.create_task(check_url(i)))
            asyncio.gather(*tasks)
        logger.debug('✅Проверка специальных ссылок успешно завершена')
    except:
        await Print_Error()

async def send_otchet():
    try:
        await sleep(60*5)
        logger.debug('🔄Запущена отправка отчета')
        
        date_yesterday = datetime.now() - timedelta(days=1)
        date_yesterday_text = date_yesterday.strftime('%d.%m.%y')
        text_send = f'<b>📜Отчет об отправленных уведомлениях за {date_yesterday_text}:</b>\n'
        
        otchet = await DB.get_otchet_yesterday() # prodleny, off_key, up_days, change_protocol, change_locations, get_test_keys, get_new_keys, pay_donat, pay_change_protocol, pay_change_locations, get_obesh, call_donat, opros_super, opros_dop
        if otchet and len(otchet) > 0:
            prodleny = otchet[0]
            off_key = otchet[1]
            up_days = otchet[2]
            change_protocol = otchet[3]
            change_locations = otchet[4]
            get_test_keys = otchet[5]
            get_new_keys = otchet[6]
            pay_donat = otchet[7]
            pay_change_protocol = otchet[8]
            pay_change_locations = otchet[9]
            get_obesh = otchet[10]
            call_donat = otchet[11]
            opros_super = otchet[12]
            opros_dop = otchet[13]
            
            text_send += '\n<b>🔑Ключи</b>\n'
            text_send += f'├ Получили новые ключи: <b>{get_new_keys}</b>\n'
            text_send += f'├ Получили пробные ключи: <b>{get_test_keys}</b>\n'
            text_send += f'├ Продлены: <b>{prodleny}</b>\n'
            text_send += f'└ Отключены: <b>{off_key}</b>\n'

            text_send += '\n<b>🔧Действия с ключами</b>\n'
            text_send += f'├ Увеличили кол-во дней: <b>{up_days}</b>\n'
            text_send += f'└ Взяли обещанный платеж: <b>{get_obesh}</b>\n'
            
            text_send += f'\n<b>✏️Доп.возможности</b>\n'
            text_send += f'├ Сменили протокол: <b>{change_protocol}</b>\n'
            text_send += f'├ Сменили локацию: <b>{change_locations}</b>\n'
            text_send += f'├ Оплатили смену протокола: <b>{pay_change_protocol}</b>\n'
            text_send += f'└ Оплатили смену локации: <b>{pay_change_locations}</b>\n'
            
            text_send += '\n<b>💰Пожертвования</b>\n'
            text_send += f'├ Оплатили пожертвование: <b>{pay_donat}</b>\n'
            text_send += f'└ Вызвали пожертвование: <b>{call_donat}</b>\n'
            
            text_send += '\n<b>📊Опросы</b>\n'
            text_send += f'├ Опрос "Все супер": <b>{opros_super}</b>\n'
            text_send += f'└ Опрос "Есть что дополнить": <b>{opros_dop}</b>\n'

            await send_message(MY_ID_TELEG, text_send)
        logger.debug('✅Отправка отчета админу бота успешно произошла!')
    except:
        await Print_Error()

async def check_clients_and_keys():
    try:
        now = datetime.now()
        start_time = datetime(1, 1, 1, hour=HOUR_CHECK - 1, minute=50)
        end_time = datetime(1, 1, 1, hour=HOUR_CHECK, minute=10)

        if start_time.time() <= now.time() <= end_time.time():
            tasks = []
            tasks.append(asyncio.create_task(check_keys_all()))
            tasks.append(asyncio.create_task(ckeck_clients_no_keys()))
            tasks.append(asyncio.create_task(check_spec_urls()))
            if IS_OTCHET:
                tasks.append(asyncio.create_task(send_otchet()))
            logger.debug('✅Проверка ключей успешно завершена!')
            await asyncio.gather(*tasks)
    except:
        await Print_Error()

async def check_zaprosi():
    while True:
        try:
            logger.debug('🔄Запущена проверка на не отвеченные запросы')
            try:
                data = await DB.get_all_zaprosi(status=0) # id, User_id, Summ, Comment, Status
                logger.debug(f'🔄checkZaprosi: data = await DB.get_all_zaprosi(status=0): Получил данные: {data}')
                summ_all_no_done_or_cancel = 0
                count = 0
                if data and len(data) > 0:
                    for zapros in data:
                        summ_zapros = zapros[2]
                        summ_all_no_done_or_cancel += summ_zapros
                        count += 1

                if count > 0:
                    klava = InlineKeyboardMarkup()
                    klava.add(InlineKeyboardButton(text=f'📝Необработанные запросы', callback_data=f'zaprosi::no_done'))
                    await send_admins(None, f'Не обраб. запросы', f'🔢Кол-во запросов: <b>{count}</b>\n💰На общую сумму: <b>{summ_all_no_done_or_cancel}₽</b>', reply_markup=klava)
            except:
                await Print_Error()
            logger.debug('✅Проверка на не отвеченные запросы успешно завершена!')
            await sleep(3*60*60)
        except:
            await Print_Error()

async def check_servers_on():
    try:
        await sleep(5*60)
        while True:
            now = datetime.now()
            if (now.hour == 3 and 55 <= now.minute <= 59) or (now.hour == 4 and 0 <= now.minute <= 5) or (now.hour == 6 and 55 <= now.minute <= 59) or (now.hour == 7 and 0 <= now.minute <= 5):
                await sleep(15*60)

            try:
                logger.debug('🔄Запущена проверка серверов на работу')
                async def check_server(ip):
                    try:
                        is_work = await check_server_is_work(ip, time_check=60)
                        if is_work:
                            return

                        if not ip in servers_no_work:
                            servers_no_work[ip] = [datetime.now()]
                        else:
                            servers_no_work[ip].append(datetime.now())

                            if (servers_no_work[ip][-1] - servers_no_work[ip][-2]) <= timedelta(minutes=7):
                                await send_admins(text=f'⚠️Сервер <code>{ip}</code> не ответил 2 раза подряд в течении 5 минут, отправляю на перезагрузку...')

                                for server in SERVERS[1:]:
                                    if ip == server['ip']:
                                        await reboot_server(server)
                                        break
                    except:
                        await Print_Error()
                        
                tasks = []
                for server in SERVERS:
                    tasks.append(asyncio.create_task(check_server(server['ip'])))
                asyncio.gather(*tasks)
                logger.debug('✅Проверка серверов на работу успешно завершена!')    
            except:
                await Print_Error()
            await sleep(5*60)
    except:
        await Print_Error()

async def add_days(user_id, conf_name, day=COUNT_DAYS_REF, promo='', silent=False):
    try:
        user = await user_get(user_id)
        text_dostup = f'+ {day} {await dney(day, user)}!'
        if day == COUNT_DAYS_REF:
            text_dostup = user.lang.get('tx_add_days_to_key_priglacil').format(count_day=day, dney_text=await dney(day, user))

        ip_server = await DB.get_ip_server_by_key_name(conf_name)
        protocol = await DB.get_Protocol_by_key_name(conf_name)

        await KEYS_ACTIONS.activateKey(protocol, conf_name, ip_server, user_id, days=day)

        user = await user_get(user_id)
        if day != -1:
            await send_message(user_id, user.lang.get('tx_add_days_to_key').format(conf_name=conf_name, dostup=text_dostup), reply_markup=user.klav_start)
        if day == COUNT_DAYS_REF:
            await send_message(user_id, user.lang.get('tx_add_days_to_key_priglacil_dop_text').format(day_ref=COUNT_DAYS_REF, dney_text=await dney(COUNT_DAYS_REF, user)))
        if day == -1:
            await send_message(user_id, user.lang.get('tx_podpiska_active'))
        await get_user_keys(user_id)

        promo_text = f'Ключ: <code>{conf_name}</code> (+<b>{day}</b> {await dney(day)})'
        promo_text += f'\nПромокод: <b>{promo}</b>' if promo != '' else ''
        if not silent:
            if not IS_OTCHET:
                await send_admins(user_id, f'✅Ключ продлен', f'{promo_text}')
            await DB.add_otchet('up_days')
    except:
        await Print_Error()

async def send_start_message(message, priglacili = False): 
    try:
        user_id = message.chat.id
        user_first_name = message.chat.first_name
        is_invited = bool(priglacili)
        user = await user_get(user_id)
        user.bot_status = 0

        user.isAutoCheckOn = False
        user.isPayChangeProtocol = False
        user.isPayChangeLocations = False

        if is_invited:
            invitation_text = user.lang.get('tx_start_invite').format(name=user_first_name, name_bot=NAME_BOT_CONFIG)
        else:
            invitation_text = user.lang.get('tx_hello').format(name=user_first_name)

        klava = InlineKeyboardMarkup()
        isGetTestKey = await DB.isGetTestKey_by_user(user_id)
        if not isGetTestKey:
            klava.add(InlineKeyboardButton(text=user.lang.get('but_test_key'), callback_data=f'buttons:test_key_get'))
        klava.add(InlineKeyboardButton(text=user.lang.get('but_connect'), callback_data=f'buttons:but_connect'))

        _tx_start = user.lang.get('tx_start').format(name_author=NAME_AUTHOR_BOT, but_1=user.lang.get('but_connect'), but_2=user.lang.get('but_desription'))

        if INLINE_MODE:
            invitation_text += f'\n\n{_tx_start}'

        try:
            await send_message(user_id, invitation_text, reply_markup=user.klav_start)
        except:
            user = await user_get(user_id, reset=True)
            await send_message(user_id, invitation_text, reply_markup=user.klav_start)
        if not INLINE_MODE:
            await send_message(user_id, _tx_start, reply_markup=klava)
    except:
        await Print_Error()

async def help_messages(message):
    try:
        user = await user_get(message.chat.id)
        user.isAutoCheckOn = False
        user.isPayChangeProtocol = False
        user.isPayChangeLocations = False

        if user.isAdmin:
            text = '<b>Сервера</b>\n➖➖➖➖➖➖➖➖\n'
            text += '/web - Просмотр ключей на серверах\n'
            text += '/servers - Изменение данных серверов\n'
            text += '/speed_test - Тестирование всех серверов\n'
            text += '/backup - Выгрузка основных файлов\n'
            text += '/cmd команда - Выполнение команды на сервере бота\n'
            text += '/reload_servers - Перезагрузка всех серверов\n'
            text += '/transfer <b>1.1.1.1 2.2.2.2</b> - Перенести всех клиентов с серверов, на перечисленные сервера\n'
            text += '/transfer_one <b>1.1.1.1 2.2.2.2</b> - Перенести всех клиентов с сервера <b>1.1.1.1</b> на <b>2.2.2.2</b>\n'
            text += '/add_server - Автоматическая настройка и добавление нового сервера в бота\n'
            text += '/add_location - Добавление новой локации в подписку Marzban\n'

            text += '<b>Отчеты</b>\n➖➖➖➖➖➖➖➖\n'
            text += '/analytics - Аналитика\n'
            text += '/report - Отчеты\n'
            if PODPISKA_MODE:
                text += '/podpiski - Пакеты подписок\n'
            text += '/get_config - Загрузить файл для изменения конфигурации бота\n'
            text += '/get_texts_file - Загрузить файл с текстами, кнопками, клавиатурами...\n'
            text += '/urls - Просмотр текущих спец. ссылок\n\n'

            text += '<b>Работа с партнерами</b>\n➖➖➖➖➖➖➖➖\n'
            text += '/create - Создание спец. ссылки для партнера\n'
            text += '/newpromo - Массовое создание промокодов с текстом\n'
            text += '/partner <b>30</b> - Изменить заработок партнера по умолчанию\n'
            text += '/summ_vivod <b>200</b> - Изменить минимальную сумму для вывода\n'
            if PAY_CHANGE_PROTOCOL:
                text += '/summ_change_protocol <b>50</b> - Изменить сумму для пожизненной возможности смены протокола\n'
            if PAY_CHANGE_LOCATIONS:
                text += '/summ_change_locations <b>100</b> - Изменить сумму подписки на 1 месяц возможности менять неограниченное кол-во раз локацию\n'
            text += '/news Привет👋 - Написать новость\n'
            text += '/otvet <b>30</b> - Сформировать шаблон-ответ с промокодом\n\n'

            text += '<b>Финансы</b>\n➖➖➖➖➖➖➖➖\n'
            text += '/wallets - Способы оплаты\n'
            text += '/balance - Баланс Ю.Money\n'
            text += '/history - Последние 10 операций Ю.Money\n'
            text += '/price - Изменение тарифов\n'
            text += '/kurs <b>92</b> - Изменить курс доллара\n'

            text += '<b>Промокоды</b>\n➖➖➖➖➖➖➖➖\n'
            text += '/code - Создание инд.промокода\n'
            text += '/code_view - Просмотр инд.промокодов\n'
            text += '/promo - Просмотр и создание промокодов\n'
            text += '/promo <b>37</b> - Создание промокода на любое кол-во дней\n\n'
            if TARIF_1 != 0:
                text += '/promo_30 - Создание 1 промокода на 30 дней\n'
            if TARIF_3 != 0:
                text += '/promo_90 - на 90 дней\n'
            if TARIF_6 != 0:
                text += '/promo_180 - на 180 дней\n'
            if TARIF_12 != 0:
                text += '/promo_365 - на 365 дней\n'
            await send_message(message.chat.id, text, reply_markup=await fun_klav_help(user))
        else:
            await send_message(message.chat.id, user.lang.get('tx_help').format(name=message.chat.first_name), reply_markup=await fun_klav_help(user))          
    except:
        await Print_Error()

async def new_key(user_id, day=30, is_Admin=0, promo='', help_message=False, summ=0, bill_id='', protocol=PR_DEFAULT, date=None, ip_server=None, silent=False, isChangeLocation=False, RebillId='', Podpiska=-1, summ_tarif=-1):
    try:
        global NAME_BOT_CONFIG
        NAME_BOT_CONFIG = NAME_BOT_CONFIG.replace('_','').replace('-','').replace(' ','')
        NAME_BOT_CONFIG = NAME_BOT_CONFIG[:8]

        isChangeProtocol = not ip_server is None

        logger.debug(f'======{user_id} - Запущена функция NewQR для пользователя======')
        logger.debug(f'Параметры функции: day={day}, is_Admin={is_Admin}, promo={promo}, help_message={help_message}, summ={summ}, bill_id={bill_id}, protocol={protocol}, date={date}, ip_server={ip_server}, silent={silent}')

        #region Проверка на существование пользователя и отправка ему сообщения
        res = await DB.get_user_nick_and_ustrv(user_id) # Nick, Selected_id_Ustr, First_Name, Summ
        if res is None:
            res = ('nick', 2, 'User')
        id_ustr = res[1]
        first_name = res[2]

        user = await user_get(user_id)
        logger.debug(f'{user_id} - Загрузил информацию о пользователе res={res}')
        if isChangeProtocol:
            if not isChangeLocation:
                wait_message = user.lang.get('tx_change_protocol_wait')
            else:
                wait_message = user.lang.get('tx_change_location_wait')
        elif isChangeLocation:
            wait_message = user.lang.get('tx_change_location_wait')
        else:
            wait_message = user.lang.get('tx_create_key_wait')
        mes = await send_message(user_id, wait_message)
        logger.debug(f'{user_id} - Отправил сообщение о создании ключа')
        #endregion

        #region Проверка, есть ли необходимый сарвер
        yes = False
        for s in SERVERS:
            if protocol == 'pptp' and s['is_pptp']:
                yes = True
            elif protocol != 'pptp' and not s['is_pptp']:
                yes = True

        if not yes:
            await send_message(user_id, user.lang.get('tx_no_server_for_protocol'))
            return await send_admins(user_id, '🛑Ошибка создания ключа', f'🛑Для протокола <b>{protocol}</b> нет серверов! Необходимо после добавления сервера /add_server связаться с клиентом!')
        #endregion

        #region Формирование данных для создания ключа
        conf_name = ''
        count_keys = await DB.get_qr_key_All()
        if not count_keys is None:
            count_keys = len(count_keys)
        else:
            count_keys = 0
        logger.debug(f'{user_id} - Получил кол-во ключей count_keys = {count_keys}')

        if protocol in ('wireguard', 'vless', 'pptp'):
            while True:
                logger.debug(f'{user_id} - {protocol} создание названия и путей')
                conf_name = f'{NAME_BOT_CONFIG}_{random.randint(1,9)}{random.randint(1,9)}{count_keys}{random.randint(1,9)}'
                conf_name_local = conf_name.lower()
                logger.debug(f'{user_id} - Получил названия ключей conf_name = {conf_name} и conf_name_local = {conf_name_local}')
                path_to_conf_server = f'/home/{NO_ROOT_USER}/configs/{conf_name}.conf'
                path_to_conf_local = f"{conf_name_local[:15].lower()}.conf"
                logger.debug(f'{user_id} - Получил пути ключей path_to_conf_server = {path_to_conf_server} и path_to_conf_local = {path_to_conf_local}')

                # проверить, чтобы данного ключа не было в БД, если есть, попробовать создать еще раз
                if not await DB.exists_key(conf_name):
                    break

        # if len(conf_name) > 15:
        #     await send_admins(user_id, '🛑Уменьшите длину NAME_BOT_CONFIG в /get_config', f'Название: <b>{conf_name} > 15 символов!</b>')
        #endregion

        #region Выбор сервера
        logger.debug(f'{user_id} - Дошел до выбора сервера')
        server = None
        
        servers_no_yes = {}
        if len(SERVERS) > 1:
            # Если серверов в базе > 1
            logger.debug(f'{user_id} - Серверов > 1')

            if ip_server is None:
                # Если сервер не предопределен
                logger.debug(f'{user_id} - IP сервера не предопределено (ip_server is None)')

                # если есть сервер marzban и протокол vless, то создать на нем
                if any([ser['is_marzban'] for ser in SERVERS]) and protocol == 'vless':
                    logger.debug(f'{user_id} - есть сервер marzban и протокол vless, создаем на нем')
                    for ser in SERVERS:
                        if ser['is_marzban']:
                            server = ser
                            logger.debug(f'{user_id} - сервер marzban и протокол vless, создаем на нем server={server}')
                            break

                if not server:
                    count_select_server = 0
                    while True:
                        server_temp = random.choice(SERVERS)
                        if server_temp['ip'] in servers_no_yes:
                            continue
                        
                        logger.debug(f'{user_id} - Берем рандомный сервер server_temp={server_temp}')
                        
                        if protocol != 'vless' and server_temp['is_marzban']:
                            continue

                        if server_temp['is_pptp'] and protocol != 'pptp':
                            continue

                        if not server_temp['is_pptp'] and protocol == 'pptp':
                            continue

                        if OSN_SERVER_NIDERLANDS and not 'нидерланды' in server_temp['location'].lower():
                            logger.debug(f'{user_id} - Основная локация Нидерланды, а выбранный сервер не Нидерланды, пробуем еще раз')
                            continue

                        count_users_in_server = await DB.get_count_keys_by_ip(server_temp['ip'])
                        if count_users_in_server < server_temp['count_keys'] and not server_temp['isPremium']:
                            server = server_temp
                            logger.debug(f'{user_id} - Ключей на сервере меньше чем count_keys, выбираем server={server}')
                            break
                        else:
                            logger.debug(f'{user_id} - Ключей на сервере больше чем count_keys {count_users_in_server} < ({server_temp["count_keys"]}, пробуем еще раз')

                        count_select_server += 1
                        servers_no_yes[server_temp['ip']] = True
                        if count_select_server >= 15:
                            logger.debug(f'{user_id} - Перебрали 15 рандомных серверов, пробуем выбрать по порядку')
                            for ser in SERVERS:
                                if OSN_SERVER_NIDERLANDS and not 'нидерланды' in server_temp['location'].lower():
                                    # logger.debug(f'{user_id} - Основная локация Нидерланды, а выбранный сервер не Нидерланды, пробуем еще раз')
                                    continue
                                count_users_in_server = await DB.get_count_keys_by_ip(ser['ip'])
                                if count_users_in_server < ser['count_keys'] and not ser['isPremium']:
                                    server = ser
                                    logger.debug(f'{user_id} - Перебрали {count_select_server} рандомных серверов; Выбираем сервер по порядку, server={server}')
                                    break
                                else:
                                    logger.debug(f'{user_id} - Ключей на сервере больше чем count_keys {count_users_in_server} < ({ser["count_keys"]} или сервер Премиальный ({ser}), пробуем еще раз')

                            if server:
                                break
                            
                            logger.debug(f'{user_id} - Перебрали сервера по порядку, пробуем еще раз без учета премиальности...')
                            for ser in SERVERS:
                                count_users_in_server = await DB.get_count_keys_by_ip(ser['ip'])
                                if count_users_in_server < ser['count_keys']:
                                    server = ser
                                    logger.debug(f'{user_id} - Перебрали {count_select_server} рандомных серверов; Выбираем сервер по порядку, server={server}')
                                    break
                                else:
                                    logger.debug(f'{user_id} - Ключей на сервере больше чем count_keys {count_users_in_server} < ({ser["count_keys"]}, пробуем еще раз')
                            break
            else:
                # Если сервер предопределен
                logger.debug(f'{user_id} - IP сервера предопределено (ip_server={ip_server})')
                for ser in SERVERS:
                    if ser['ip'] == ip_server:
                        server = ser
                        logger.debug(f'{user_id} - IP сервера предопределено (server={server})')
                        break
        else:
            # Если сервер в базе 1
            server = SERVERS[0]
            logger.debug(f'{user_id} - Серверов всего 1 взял server = {server}')

        if server is None:
            logger.warning(f'{user_id} - Сервер не выбран')
            for ser in SERVERS:
                if await DB.get_count_keys_by_ip(ser['ip']) < ser['count_keys']:
                    server = ser
                    logger.warning(f'{user_id} - Сервер не выбран, выбираем первый попавшийся server={server}')
                    break
        else:
            logger.debug(f'{user_id} - Сервер выбран идем далее')

        count_by_ip = await DB.get_count_keys_by_ip(server['ip'])
        logger.debug(f'{user_id} - Берем кол-во ключей на сервере _1_ {count_by_ip} < {server["count_keys"]}')

        if count_by_ip >= server['count_keys'] or count_by_ip >= 240:
            logger.warning(f'{user_id} - Кол-во ключей на сервере больше чем count_keys или > 240, пробуем создать на другом сервере')
            for ser in SERVERS:
                count_users_in_server = await DB.get_count_keys_by_ip(ser['ip'])
                if count_users_in_server < ser['count_keys']:
                    server = ser
                    logger.debug(f'{user_id} - Ключей на сервере меньше чем count_keys, server={server}')
                    break

        count_by_ip = await DB.get_count_keys_by_ip(server['ip'])
        logger.debug(f'{user_id} - Берем кол-во ключей на сервере _2_ {count_by_ip} < {server["count_keys"]}')

        count_keys_limit = sum([server['count_keys'] for server in SERVERS])
        count_keys_limit_percent = count_keys_limit * 0.9
        if count_keys >= count_keys_limit_percent:
            await send_admins(user_id, f'🛑Сервера заняты на >= 90%', f'⚠️Кол-во ключей на серверах: <b>{count_keys}</b>/{count_keys_limit}')

        if count_by_ip >= server['count_keys'] or count_by_ip >= 240:
            logger.warning(f'{user_id} - Кол-во ключей на сервере больше чем count_keys или > 240')
            url = f'http://{server["ip"]}:51821'
            text_ip = f'<a href="{url}">{server["ip"]}</a>'
            await send_admins(user_id, f'🛑Не удалось создать ключ', f'<b>🛑Закончилось место на серверах!</b>\nЗаметка: {text_ip} (<b>{count_by_ip}</b> > {server["count_keys"]})')
            await send_message(user_id, user.lang.get('tx_no_create_key'))
            logger.debug(f'{user_id} - Отправил сообщение о неудаче и вышел из функции')
            return
        #endregion

        if date is None:
            logger.debug(f'{user_id} - Дата не предопределена date is None устанавливаем')
            date = datetime.now().strftime("%Y_%m_%d")

        error = ''
        count_craete_key = 0
        no_create_server = []
        logger.debug(f'{user_id} - Дошел до создания ключа, протокол: {protocol}')
        while True:
            try:
                # если не удалось создать ключ, то пробуем создать на другом сервере
                count_craete_key += 1
                check_ = await check_server_is_work(server['ip'])
                if check_:
                    if protocol == 'wireguard':
                        logger.debug(f'{user_id} - Wireguard создание ключа')
                        text = await exec_command_in_http_server(ip=server['ip'], password=server['password'], command=f'pibot -a -n {conf_name}', path=path_to_conf_server, read_timeout=10)
                        if text:
                            logger.debug(f'{user_id} - Wireguard ключ создан')
                            break
                    elif protocol == 'outline':
                        logger.debug(f'{user_id} - Outline создание ключа')
                        cl = OutlineBOT(server['api_url'], server['cert_sha256'])
                        logger.debug(f'{user_id} - Outline создание ключа cl = {cl}')
                        text = cl.create_key()
                        if text:
                            logger.debug(f'{user_id} - Outline создание ключа text = {text}')
                            while True:
                                conf_name = f'{NAME_BOT_CONFIG}_{user_id}_{text.key_id}_{random.randint(10,99)}'
                                # проверить, чтобы данного ключа не было в БД, если есть, попробовать создать еще раз
                                if not await DB.exists_key(conf_name):
                                    break
                            logger.debug(f'{user_id} - Outline создание ключа conf_name = {conf_name}')
                            cl.rename_key(text.key_id, conf_name)
                            logger.debug(f'{user_id} - Outline создание ключа cl.rename_key')
                            text = f"{text.access_url}#{NAME_BOT_CONFIG}:{server['location']} - {conf_name.split('_')[-2]}"
                            break
                    elif protocol == 'vless':
                        logger.debug(f'{user_id} - VLESS создание ключа')
                        
                        if check_server_is_marzban(server['ip']):
                            marzban = MARZBAN(server['ip'], server['password'])
                            
                            
                            key = await marzban.create_new_key(conf_name, date, day)
                            logger.debug(f'{user_id} - VLESS ключ создан')
                            text = f'{key}#🤖{NAME_BOT_CONFIG}'
                            break
                        else:
                            vless = VLESS(server['ip'], server['password'])
                            text = await vless.addOrUpdateKey(conf_name, days=day, date=date)
                            if text[0]:
                                logger.debug(f'{user_id} - VLESS ключ создан')
                                text = f'{text[1]}-{server["location"]}'
                                break
                            else:
                                logger.warning(f'{user_id} - VLESS ключ не создан, ошибка: {text[1]}')
                                error = text[1]
                    elif protocol == 'pptp':
                        logger.debug(f'{user_id} - PPTP создание ключа')
                        
                        pptp = PPTP(server['ip'], server['password'])
                        text = await pptp.add_key(conf_name)

                        if text:
                            login, password = text
                            text = user.lang.get('tx_pptp_instr').format(ip=server["ip"], login=login, password=password)
                            break
                        else:
                            logger.warning(f'🛑{user_id} - PPTP ключ не создан')
                else:
                    logger.warning(f'{user_id} - Сервер {server["ip"]} не отвечает, пробуем другой')
            except Exception as e:
                error = str(e)
                logger.warning(f'{user_id} - Произошла ошибка: {e}')
                await Print_Error()

            #region Ключ создать не удалось
            if count_craete_key > 15:
                text = None
                break

            logger.warning(f'{user_id} - Пробуем создать ключ на другом сервере (попытка {count_craete_key})...')
            # Добавляем в список серверов, на которых не удалось создать ключ
            no_create_server.append(server['ip'])

            # подбираем другой сервер
            for ser_ in SERVERS:
                if not ser_['ip'] in no_create_server:
                    res__ = await DB.get_count_keys_by_ip(ser_['ip'])
                    if res__ < ser_['count_keys']:
                        server = ser_
                        logger.debug(f'{user_id} - Не удалось создать ключ, пробуем другой сервер server={server["ip"]}')
                        break
            #endregion

        if not text:
            logger.warning(f'{user_id} - Ключ не создан text is None')
            if error != '':
                error = f'\n\nПоследняя ошибка: <b>{error}</b>'
            await send_admins(user_id, f'🛑Не удалось создать ключ', f'🛑Не удалось обратиться к серверам, последний: <b>{server["ip"]}</b>\nЗаметка: <b>Ключ на {day} {await dney(day)}</b>{error}')
            await send_message(user_id, user.lang.get('tx_no_create_key'))
            await delete_message(user_id, mes.message_id)
            logger.debug(f'{user_id} - Отправил сообщение о неудаче и вышел из функции text is None')
            return
        
        if protocol == 'wireguard': 
            logger.debug(f'{user_id} - Wireguard создание QR')
            if SEND_QR:
                path_to_save = f'{conf_name}.png'
                result_qr = False
                try:
                    result_qr = await gen_qr_code(text, QR_LOGO, path_to_save)
                    if result_qr:
                        logger.debug(f'{user_id} - Wireguard создание QR прошло успешно path_to_save = {path_to_save}')

                        await bot.send_photo(user_id, open(path_to_save, 'rb'))
                        logger.debug(f'{user_id} - Wireguard отправка QR прошло успешно')
                    else:
                        logger.warning(f'{user_id} - Wireguard создание QR не удалось произвести так как не был обнаружен верный LOGO.png result_qr={result_qr}')
                except:
                    logger.warning(f'{user_id} - Wireguard создание QR не удалось произвести так как не был обнаружен верный LOGO.png result_qr={result_qr}')
            
            with open(path_to_conf_local, "w") as f:
                f.write(text)
                logger.debug(f'{user_id} - Wireguard запись ключа в файл прошло успешно')
            try:
                await bot.send_document(user_id, open(path_to_conf_local, "rb"))
            except:
                await sleep(random.randint(2,4))
                await bot.send_document(user_id, open(path_to_conf_local, "rb"))
            logger.debug(f'{user_id} - Wireguard отправка конфиг файла прошло успешно')
        elif protocol == 'outline':
            await send_message(user_id, f'<code>{text}</code>')
            logger.debug(f'{user_id} - Outline отправка ссылки прошла успешно')
        elif protocol == 'vless':
            await send_message(user_id, f'<code>{text}</code>')
            logger.debug(f'{user_id} - VLESS отправка ссылки прошла успешно')
        elif protocol == 'pptp':
            if INLINE_MODE:
                klava = InlineKeyboardMarkup()
                klava.add(InlineKeyboardButton(text=user.lang.get('but_main'), callback_data=f'buttons:but_main'))
            else:
                klava = ReplyKeyboardMarkup(resize_keyboard=True)
                klava.add(user.lang.get('but_main'))
            await send_message(user_id, text, reply_markup=klava)
            logger.debug(f'{user_id} - PPTP отправка логина и пароля прошла успешно')

        await DB.add_qr_key(user_id, conf_name, date, USTRV[id_ustr], is_Admin, server['ip'], day, summ, bill_id, protocol=protocol, isChangeProtocol=isChangeProtocol, keys_data=text, podpiska=Podpiska)
        if AUTO_PAY_YKASSA:
            await DB.set_payment_id_qr_key_in_DB(conf_name, bill_id, RebillId) # сохранить в БД рядом с ключом payment.id, чтобы после прошествия срока снять еще раз
        if summ_tarif != -1:
            await DB.set_summ_qr_key_in_DB(conf_name, summ_tarif)
        logger.debug(f'{user_id} - Добавление ключа в БД прошло успешно')

        if isChangeProtocol and not isChangeLocation:
            await DB.update_qr_key_date_change_protocol(conf_name, datetime.now())
            logger.debug(f'{user_id} - Обновление даты смены протокола прошло успешно')

        if protocol != 'pptp':
            user = await user_get(user_id)
            user.key_url = text
            if help_message:
                await send_message(user_id, user.lang.get('tx_how_install').format(name=first_name), reply_markup=await fun_klav_podkl_no_back(user, user.buttons_podkl_vless))
                logger.debug(f'{user_id} - Отправка сообщения с помощью tx_how_install')
            else:
                await help(user_id, id_ustr, protocol)
                logger.debug(f'{user_id} - Отправка сообщения с помощью await Help(user_id, id_ustr, protocol)')

        if not silent:
            if is_Admin == 1:
                if not IS_OTCHET:
                    await send_admins(user_id, 'Выдал админский ключ', f'Ключ: <code>{conf_name}</code>')
                logger.debug(f'{user_id} - Отправка сообщения с помощью await sendAdmins(user_id, "Выдал админский ключ", f"Ключ: <code>{conf_name}</code>")')
            else:
                try:
                    date_key_str = ".".join(date.split('_')[::-1])
                except:
                    date_key_str = date

                promo_text = f'Ключ: <code>{conf_name}</code> ({date_key_str}, {day} {await dney(day)})'
                promo_text += f'\nПромокод: <b>{promo}</b>\n' if promo != '' else ''

                if isChangeProtocol:
                    if not isChangeLocation:
                        head_text = f'🔁Сменил протокол ({protocol})'
                        await DB.add_otchet('change_protocol')
                        await DB.add_operation('change_protocol', user_id, 0, day, '', '', head_text)
                    else:
                        head_text = f'🔁Сменил локацию'
                        await DB.add_otchet('change_locations')
                        await DB.add_operation('change_location', user_id, 0, day, '', '', head_text)
                elif isChangeLocation:
                    head_text = f'🔁Сменил локацию'
                    await DB.add_otchet('change_locations')
                    await DB.add_operation('change_location', user_id, 0, day, '', '', head_text)
                elif COUNT_DAYS_TRIAL == day:
                    head_text = f'Выдал пробный 🔑'
                    await DB.add_otchet('get_test_keys')
                else:
                    head_text = f'Выдал 🆕 ключ'
                    await DB.add_otchet('get_new_keys')
                if not IS_OTCHET:
                    await send_admins(user_id, head_text, promo_text)
                logger.debug(f'{user_id} - Отправка сообщения с помощью await sendAdmins(user_id, head_text, promo_text)')

        await delete_message(user_id, mes.message_id)
        logger.debug(f'{user_id} - Удалил сообщение о создании ключа')
        if protocol == 'wireguard':
            await sleep(1)
            try:
                if SEND_QR:
                    os.remove(path_to_save)
                    logger.debug(f'{user_id} - Удалил файл QR')
                os.remove(path_to_conf_local)
                logger.debug(f'{user_id} - Удалил файл конфига')
            except:
                pass
        logger.debug(f'======{user_id} - Функция NewQR полностью отработала======')
    except Exception as e:
        await Print_Error()
        logger.warning(f'{user_id} - Произошла ошибка: {e}')

async def plus_days_ref(user_id, id_ref, help_message=False):
    try:
        if not await DB.exists_ref(id_ref, user_id):
            await DB.add_ref(id_ref, user_id)
            await DB.set_user_ref(user_id, -1)
            data = await DB.add_day_qr_key_ref(id_ref, COUNT_DAYS_REF)
            isGetKey = data[0]
            name_key = data[1]
            protocol = data[3]

            user = await user_get(id_ref)

            if isGetKey:
                await add_days(id_ref, name_key, day=COUNT_DAYS_REF)
            else:
                # если у клиента нет qr, выдать ему его на COUNT_DAYS_REF дн
                await new_key(id_ref, COUNT_DAYS_REF, help_message=help_message, protocol=protocol)
                await send_message(id_ref, user.lang.get('tx_add_days_by_ref').format(days=COUNT_DAYS_REF, dney_text=await dney(COUNT_DAYS_REF, user)))
            await send_message(id_ref, user.lang.get('tx_thanks_ref').format(name_bot=NICK_HELP))
    except:
        await Print_Error()

async def donate_success(user, user_id, id): 
    try:
        # Добавление доната в БД
        title = user.donate[id][0]
        summ = user.donate[id][1]
        await DB.add_donate(user_id, summ)
        
        await send_message(user_id, user.lang.get('tx_thanks_donate'))
        if not IS_OTCHET:
            await send_admins(user_id, f'Оплатил пожертвование {title} ({summ}₽) 🥳')
        await DB.add_otchet('pay_donat')
    except:
        await Print_Error()

async def select_protocol(user_id):
    try:
        user = await user_get(user_id)
        tx_description_protocols = ''
        if PR_VLESS:
            tx_description_protocols += user.lang.get('tx_desc_vless')
        if PR_WIREGUARD:
            tx_description_protocols += user.lang.get('tx_desc_wireguard')
        if PR_OUTLINE:
            tx_description_protocols += user.lang.get('tx_desc_outline')
        if PR_PPTP:
            tx_description_protocols += user.lang.get('tx_desc_pptp')

        if COUNT_PROTOCOLS > 1:
            if DEFAULT_PROTOCOL:
                mes = await send_message(user_id, user.lang.get('tx_wait'))
                await delete_message(user_id, mes.message_id)
                if DEFAULT_PROTOCOL == 'wireguard':
                    return await message_input(mes, alt_text=user.lang.get('but_select_WG'))
                elif DEFAULT_PROTOCOL == 'outline':
                    return await message_input(mes, alt_text=user.lang.get('but_select_Outline'))
                elif DEFAULT_PROTOCOL == 'vless':
                    return await message_input(mes, alt_text=user.lang.get('but_select_vless'))
                elif DEFAULT_PROTOCOL == 'pptp':
                    return await message_input(mes, alt_text=user.lang.get('but_select_pptp'))
            
            send_inline_button = False
            if not send_inline_button:
                await send_message(user_id, user.lang.get('tx_select_protocol').format(text=tx_description_protocols), reply_markup=await fun_klav_select_protocol(user, PR_VLESS, PR_WIREGUARD, PR_OUTLINE, PR_PPTP))
            else:
                klava = InlineKeyboardMarkup()
                if PR_VLESS:
                    klava.add(InlineKeyboardButton(text=user.lang.get('but_select_vless'), callback_data=f'buttons:but_select_vless'))
                if PR_WIREGUARD:
                    klava.add(InlineKeyboardButton(text=user.lang.get('but_select_WG'), callback_data=f'buttons:but_select_WG'))
                if PR_OUTLINE:
                    klava.add(InlineKeyboardButton(text=user.lang.get('but_select_Outline'), callback_data=f'buttons:but_select_Outline'))
                if PR_PPTP:
                    klava.add(InlineKeyboardButton(text=user.lang.get('but_select_pptp'), callback_data=f'buttons:but_select_pptp'))
                await send_message(user_id, user.lang.get('tx_select_protocol').format(text=tx_description_protocols), reply_markup=klava)
            logger.debug(f'{user_id} - Отправил сообщение для выбора протокола')
        else:
            logger.debug(f'{user_id} - Протокол один, запускаю NewQR')
            mes = await send_message(user_id, user.lang.get('tx_wait'))
            await delete_message(user_id, mes.message_id)
            if PR_WIREGUARD:
                return await message_input(mes, alt_text=user.lang.get('but_select_WG'))
            elif PR_OUTLINE:
                return await message_input(mes, alt_text=user.lang.get('but_select_Outline'))
            elif PR_VLESS:
                return await message_input(mes, alt_text=user.lang.get('but_select_vless'))
            elif PR_PPTP:
                return await message_input(mes, alt_text=user.lang.get('but_select_pptp'))
    except:
        await Print_Error()

async def test_key_get(user_id):
    try:
        if TEST_KEY:
            # Проверить выдавали ли клиенту до этого тестовый ключ
            isGetTestKey = await DB.isGetTestKey_by_user(user_id)
            user = await user_get(user_id)
            
            if not isGetTestKey:
                # Выдать тестовый ключ
                user.bot_status = 24
                await select_protocol(user_id)
            else:
                # если выдавали сказать, что вы уже получали тестовый клю
                await send_message(user_id, user.lang.get('tx_test_key_no_get'))
    except:
        await Print_Error()

async def check_test_mode(user_id):
    try:
        if TEST_MODE:
            await send_message(user_id, '⚠️У вас нет доступа к этой функции!')
            return True
    except:
        await Print_Error()

async def backup(user_id):
    try:
        if await check_test_mode(user_id): return
        try: await bot.send_document(user_id, open(NAME_DB, 'rb'))
        except: pass
        try: await bot.send_document(user_id, open(await get_local_path_data('messages.db'), 'rb'))
        except: pass
        try: await bot.send_document(user_id, open(CONFIG_FILE, 'rb'))
        except: pass
        try: await bot.send_document(user_id, open(LANG_FILE, 'rb'))
        except: pass
        try: await bot.send_document(user_id, open(MARKUP_FILE, 'rb'))
        except: pass
        try: await bot.send_document(user_id, open(BOT_FILE, 'rb'))
        except: await Print_Error()
        try:await bot.send_document(user_id, open(LOGS_FILE, 'rb'))
        except: pass
    except:
        pass

async def check_time_create_backup():
    try:
        if await check_test_mode(MY_ID_TELEG): return
        await sleep(10*60)
        global is_send_backup
        while not is_send_backup:
            try:
                now = datetime.now()
                start_time = datetime(1, 1, 1, hour=0, minute=0)
                end_time = datetime(1, 1, 1, hour=0, minute=10)

                if start_time.time() <= now.time() <= end_time.time():
                    tasks = []
                    tasks.append(asyncio.create_task(backup(MY_ID_TELEG)))
                    logger.debug('✅Проверка ключей успешно завершена!')
                    await asyncio.gather(*tasks)
                    is_send_backup = True
            except:
                await Print_Error()
            await sleep(5*60)
    except:
        await Print_Error()

async def check_keys_no_in_db():
    try:
        if await check_test_mode(MY_ID_TELEG): return
        await sleep(1*60)
        global is_delete_keys_no_in_DB
        while not is_delete_keys_no_in_DB:
            try:
                now = datetime.now()
                start_time = datetime(1, 1, 1, hour=5, minute=0)
                end_time = datetime(1, 1, 1, hour=0, minute=10)

                if start_time.time() <= now.time() <= end_time.time():
                    tasks = []
                    tasks.append(asyncio.create_task(CHECK_KEYS.keys_no_in_db_check()))
                    logger.debug('✅Проверка ключей, которых нет в БД успешно завершена!')
                    await asyncio.gather(*tasks)
                    is_delete_keys_no_in_DB = True
            except:
                await Print_Error()
            await sleep(5*60)
    except:
        await Print_Error()

async def send_cached_file(user_id, file_path, type='document', width=1080, height=1920):
    try:
        global cached_media
        yes = False
        if file_path in cached_media:
            cache = cached_media[file_path]
            file = cache['file_id']
            type = cache['type']
            yes = True
        else:
            file = open(file_path, 'rb')

        if type == 'document':
            res = await bot.send_document(user_id, file)
            if not yes:
                cached_media[file_path] = {'file_id': res.document.file_id, 'type': type}
        elif type == 'photo':
            res = await bot.send_photo(user_id, file)
            if not yes:
                cached_media[file_path] = {'file_id': res.photo[-1].file_id, 'type': type}
        elif type == 'video':
            res = await bot.send_video(user_id, file, width=width, height=height)
            if not yes:
                cached_media[file_path] = {'file_id': res.video.file_id, 'type': type}
    except:
        await Print_Error()

async def create_temp_table(name_table='Таблица.xlsx', data=[], columns=['Артикул', 'Категория', 'Название', 'Цена', 'Количество'], sort_values=['Артикул', 'Категория', 'Название'], sort=True, sheet_name=None):
    try:
        if data == [] or columns == [] or name_table == '':
            logger.warning(f'Ошибка создания таблицы {name_table} с данными {data} и сортировкой {sort_values}')
            return False

        logger.debug(f'Создание таблицы {name_table} с данными {data} и сортировкой {sort_values}')
        if not sheet_name:
            if '/' in name_table:
                sheet_name = name_table.split('/')[1].split('.')[0][:30]
            else:    
                sheet_name = name_table.split('.')[0][:30]
        
        df = pd.DataFrame(data, columns=columns)
        
        logger.debug(f'Создание таблицы {name_table} с данными {data}')
        if sort and sort_values != [] and any(item in sort_values for item in columns):
            df = df.sort_values(by=sort_values, ascending=False)

        logger.debug(f'Создание таблицы {name_table} с данными {data} и сортировкой {sort_values}')
        name_table = await get_local_path_data(name_table)
        writer = pd.ExcelWriter(name_table)
        
        logger.debug(f'Создание таблицы {name_table} с данными {data} и сортировкой {sort_values} и запись в файл')
        df.to_excel(writer, sheet_name=sheet_name, index=False, na_rep='')

        k = 0
        for column in df:
            column_width = max(df[column].astype(str).map(len).max(), len(column))
            col_idx = df.columns.get_loc(column)
            writer.sheets[sheet_name].set_column(col_idx, col_idx, column_width)
            k += 1
            #pip3 install xlsxwriter

        writer.save()
        return True
    except:
        await Print_Error()

@dp.pre_checkout_query_handler()
async def pre_checkout_handler(pre_checkout_query: PreCheckoutQuery):
    try:
        amount = pre_checkout_query.total_amount
        user_id = pre_checkout_query.from_user.id
        xtr_pay_success_users[user_id] = amount
        await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)
    except:
        await Print_Error()

@dp.message_handler(content_types=['new_chat_members'])
async def bot_add_group_handler(message):
    bot_obj = await bot.get_me()
    bot_id = bot_obj.id
    
    for chat_member in message.new_chat_members:
        if chat_member.id == bot_id:
            dop_info = (
                f'📄Название группы: <b>{message.chat.title}</b>\n'
                f'📄ID группы: <code>{message.chat.id}</code>'
            )
            await send_admins(message.from_user.id, '➕Бот был добавлен в группу', dop_info)

@dp.message_handler(commands="start")
async def start_message(message):
    try:
        user_mes = message.chat
        user_id = message.chat.id
        m_text = message.text.replace('/start ','')
        priglacili = False

        logger.debug(f'{user_id} - Нажал /start')

        isUser = await DB.exists_user(user_id)
        if not isUser:
            try: await DB.add_user(user_id, f'{user_mes.username}', f'{user_mes.first_name}', f'{user_mes.last_name}')
            except: pass

            # проверить если такой созданный промокод, если есть то попробовать установить его
            spec_urls = await DB.get_promo_urls()
            if not spec_urls is None and len(spec_urls) > 0:
                m_text_temp = m_text.replace(' ', '')
                for spec_url in spec_urls:
                    if spec_url[0] == m_text_temp:
                        res_add_promo = await DB.set_user_Promo(user_id, m_text_temp)
                        
                        user = await user_get(user_id)
                        if res_add_promo[0]:
                            if spec_url[1] != 0:
                                if res_add_promo[1] > 0:
                                    await send_message(user_id, user.lang.get('tx_spec_url_yes').format(discount=res_add_promo[1]))
                                else:
                                    await send_message(user_id, user.lang.get('tx_spec_url_yes_no_discount'))
                        else:
                            await send_message(user_id, user.lang.get('tx_spec_url_no_get'))
                        break

            if 'ref' in m_text and REF_SYSTEM:
                try:
                    id_ref = int(m_text.split('ref')[1])
                    id_cl = user_id

                    if not await DB.exists_ref(id_ref, id_cl):
                        priglacili = True
                except:
                    pass

        try:
            if 'global_' in m_text:
                try:
                    id_otkuda = int(m_text.replace('global_',''))
                    otkuda = LINK_FROM[id_otkuda]
                    if not IS_OTCHET:
                        await send_admins(user_id, f'✚Новый клиент', f'Откуда: <b>{otkuda}</b>')
                    await DB.set_user_otkuda(message.chat.id, id_otkuda)
                except:
                    await Print_Error()
            else:
                if not isUser:
                    if not IS_OTCHET:
                        await send_admins(user_id, f'✚Новый клиент')
        except:
            await Print_Error()

        user = await user_get(message.chat.id)
        if user.isBan: return
        
        if not isUser and len(LANG.keys()) > 1:
            # пользователь новый -> выбор языка
            await change_language_call(message=message)
        else:
            await send_start_message(message, priglacili)

        if priglacili:
            if not REF_SYSTEM_AFTER_PAY:
                await plus_days_ref(user_id, id_ref, help_message=True)
            else:
                await DB.set_user_ref(user_id, id_ref)
    except:
        await Print_Error()

@dp.message_handler(commands="backup")
async def backup_message(message):
    try:
        if await check_test_mode(message.chat.id): return
        user = await user_get(message.chat.id)
        if user.isAdmin:
            await backup(message.chat.id)
    except:
        await Print_Error()

@dp.message_handler(commands="domain")
async def domain_message(message):
    try:
        if await check_test_mode(message.chat.id): return
        user = await user_get(message.chat.id)

        if user.isAdmin:
            m_text = message.text.split()
            primer = (
                f'🏷️Пример команды:\n\n'
                '/domain <b>1.1.1.1</b> <b>server1.vpcoden.com</b> - Настроить сервер на работу с доменом, где\n'
                '    <b>1.1.1.1</b> - IP-адрес сервера\n'
                '    <b>server1.vpcoden.com</b> - Домен сервера\n\n'
                'ℹ️Не относиться к серверам Marzban и PPTP'
            )
            try:
                ip = m_text[1]
                domain = m_text[2]
    
                isUpdate = False
                if len(m_text) > 3:
                    isUpdate = True

                password = None
                for item in SERVERS:
                    if item['ip'] == ip or item['ip'] == domain:
                        password = item['password']
                        break

                if not password:
                    await send_message(message.chat.id, f'🛑Сервер <b>{ip}</b> или <b>{domain}</b> не был найден!')
                    return

                # Меняем в БД: IP -> домен 
                # + Изменяем у всех ключей: IP -> домен
                send_text_ = '✅Загрузил данные'
                mes_del = await send_message(message.chat.id, send_text_)

                if not isUpdate:
                    await DB.EXECUTE('UPDATE Servers SET ip = ? WHERE ip = ?', (domain, ip,))
                    await DB.EXECUTE('UPDATE QR_Keys SET ip_server = ? WHERE ip_server = ?', (domain, ip,))
                    await DB.COMMIT()

                send_text_ += '\n✅Изменил IP -> Домен в БД во всех таблицах'
                await bot.edit_message_text(send_text_, message.chat.id, mes_del.message_id, parse_mode='HTML')

                # Прописываем команды на сервере с доменом
                commands = [
                    f'sed -i "s/{ip}/{domain}/g" /root/server.py', # изменить ip на домен в server.py
                    'supervisorctl restart http_server' # перезагрузить http сервер
                ]

                if not isUpdate:
                    await exec_command_in_http_server(ip=ip, password=password, command='apt-get install certbot -y', read_timeout=60)
                    await sleep(1)
                    await exec_command_in_http_server(ip=ip, password=password, command=f'certbot certonly --standalone --agree-tos --register-unsafely-without-email -d {domain}', read_timeout=30)
                    await sleep(2)
                    await exec_command_in_http_server(ip=ip, password=password, command='certbot renew --dry-run', read_timeout=30)                    

                send_text_ += '\n✅Прописал домен на сервере'
                await bot.edit_message_text(send_text_, message.chat.id, mes_del.message_id, parse_mode='HTML')

                # Меняем настройки 3X-UI
                if not isUpdate:
                    VLESS(domain, password)._changeSettings3X_UI()

                send_text_ += '\n✅Изменил настройки 3X-UI'
                await bot.edit_message_text(send_text_, message.chat.id, mes_del.message_id, parse_mode='HTML')

                await delete_message(message.chat.id, mes_del.message_id)
                await send_message(message.chat.id, f'✅Домен <b>{domain}</b> для сервера <b>{ip}</b> успешно настроен!')
                if not isUpdate:
                    await DB.GET_SERVERS()
            except Exception as e:
                await send_message(message.chat.id, primer)
                logger.warning(f'🛑Произошла ошибка - {message.text}: {e}')
    except:
        await Print_Error()

@dp.message_handler(commands="test")
async def test_message(message):
    try:
        user_id = message.chat.id
        user = await user_get(user_id)
        if user.isBan: return
        await send_message(user_id, '✅')
    except:
        await Print_Error()

@dp.message_handler(commands="paysupport")
async def pay_support_message(message):
    try:
        user = await user_get(message.chat.id)
        await send_message(message.chat.id, user.lang.get('tx_refund_rtx').format(nick_help=NICK_HELP))
    
        # user_id = message.chat.id
        # await DB.change_ban_user(user_id, True)
        # try: user_dict.pop(int(user_id))
        # except: pass
    except:
        await Print_Error()

@dp.message_handler(commands="podpiski")
async def podpiski_message(message):
    try:
        user = await user_get(message.chat.id)
        if user.isAdmin:
            data = await DB.get_podpiski() # p.id, p.Name, p.Channels, p.isOn, COUNT(q.Podpiska)
            klava = InlineKeyboardMarkup()
            if data and len(data) > 0:
                text_send = '📄Текущие пакеты подписок:\n<i>(название - кол-во ключей)</i>\n\n'
                for index, paket in enumerate(data):
                    p_id = paket[0]
                    p_name = paket[1]
                    p_isOn = bool(paket[3])
                    p_count = int(paket[4])
                    isOn_smile = '✅' if p_isOn else '🛑'
                    klava.add(InlineKeyboardButton(text=f'{isOn_smile}{index+1}. {p_name} - {p_count}', callback_data=f'podpiska:{p_id}'))
            else:
                text_send = '⚠️Подписок не найдено'
            klava.add(InlineKeyboardButton(text=f'➕Добавить пакет', callback_data=f'podpiska:add'))
            await send_message(message.chat.id, text_send, reply_markup=klava)
    except:
        await Print_Error()

@dp.message_handler(commands="help")
async def help_message(message):
    try:
        user = await user_get(message.chat.id)
        if user.isBan: return
        user_mes = message.chat
        isUser = await DB.exists_user(user_mes.id)
        if not isUser:
            try:
                await DB.add_user(user_mes.id, f'{user_mes.username}', f'{user_mes.first_name}', f'{user_mes.last_name}')
            except:
                pass
        await help_messages(message)
    except:
        await Print_Error()

@dp.message_handler(commands="web")
async def web_message(message):
    try:
        user = await user_get(message.chat.id)
        if user.isAdmin:
            servers_text = ''
            klava = InlineKeyboardMarkup()
            for index, i in enumerate(SERVERS):
                ip = i["ip"]
                count_keys = i["count_keys"]
                location = i["location"]
                keys = await DB.get_keys_name_by_ip_server(ip)

                count = len(keys) if not keys is None else 0
                count_wireguard = len([key for key in keys if 'wireguard' == key[1]]) if not keys is None else 0
                count_outline = len([key for key in keys if 'outline' == key[1]]) if not keys is None else 0
                count_vless = len([key for key in keys if 'vless' == key[1]]) if not keys is None else 0
                count_pptp = len([key for key in keys if 'pptp' == key[1]]) if not keys is None else 0

                url = f'http://{ip}:51821'
                text = f'<a href="{url}">{ip}</a>'
                servers_text += f'{index+1}. {text} - {location} - <b>{count}</b>/{count_keys} - <b>{count_wireguard}</b> / <b>{count_outline}</b> / <b>{count_vless}</b> / <b>{count_pptp}</b>\n'

                if PR_OUTLINE or PR_VLESS:
                    but = InlineKeyboardButton(text=f'👨‍💻{index+1}. {ip}', callback_data=f'web:{ip}')
                    klava.add(but)

            if servers_text == '':
                await send_message(message.chat.id, '⚠️Список серверов пуст')
            else:
                servers_text = (
                    'IP-сервера - Локация - Кол-во ключей - WG / Outline / VLESS / PPTP\n\n'
                    f'{servers_text}'
                )
                text_send = (
                    '<i>ℹ️Для просмотра трафика по ключам:</i>\n'
                    '- <b>Outline</b> или <b>VLESS</b> - нажмите на кнопку с нужным сервером, далее выберите необходимый протокол\n'
                    '- <b>WireGuard</b> - нажмите на IP адрес в тексте (логин: root, пароль: пароль от сервера (можно коснуться, тем самым скопировать в /servers))'
                )

                await send_message(message.chat.id, servers_text, reply_markup=klava)
                await send_message(message.chat.id, text_send)
    except:
        await Print_Error()

@dp.message_handler(commands="servers")
async def servers_message(message):
    try:
        if await check_test_mode(message.chat.id): return
        user = await user_get(message.chat.id)
        if user.isAdmin:
            servers_text = '📊Список серверов <i>(WG / Outline / VLESS / PPTP)</i>\n\n'
            klava = InlineKeyboardMarkup()
            for index, i in enumerate(SERVERS):
                ip = i["ip"]
                password = i["password"]
                count_keys = i["count_keys"]
                location = i["location"]

                keys = await DB.get_keys_name_by_ip_server(ip)
                count = len(keys) if not keys is None else 0
                count_wireguard = len([key for key in keys if 'wireguard' == key[1]]) if not keys is None else 0
                count_outline = len([key for key in keys if 'outline' == key[1]]) if not keys is None else 0
                count_vless = len([key for key in keys if 'vless' == key[1]]) if not keys is None else 0
                count_pptp = len([key for key in keys if 'pptp' == key[1]]) if not keys is None else 0

                servers_text += f'<b>{index + 1}. {location}</b> (<code>{ip}</code> / <code>{password}</code>)\n'
                if i["isPremium"]:
                    servers_text += f'⭐️Премиальный сервер\n'
                if i['is_marzban']:
                    servers_text += f'🔒Marzban\n'
                if i['is_pptp']:
                    servers_text += f'🔒PPTP\n'
                servers_text += f'🔢Ключей: <b>{count} / {count_keys}</b>  (<b>{count_wireguard}</b> / <b>{count_outline}</b> / <b>{count_vless}</b> / <b>{count_pptp}</b>)\n\n'

                but = InlineKeyboardButton(text=f'✏️{index + 1}. {ip} ({location})', callback_data=f'servers:{ip}')
                klava.add(but)

                if index % 4 == 0 and index != 0:
                    await send_long_message(message.chat.id, servers_text)
                    servers_text = ''
                    
            servers_text += (
                '\n⭐️Премиальные сервера - не используются для новых ключей, но клиенты могут изменить ключ на них через /start -> Изменить локацию.\n'
                '⭐️Возможно ввести дополнительная оплату /get_config -> PAY_CHANGE_LOCATIONS = True'
            )

            if len(SERVERS) > 0:
                if servers_text != '':
                    await send_long_message(message.chat.id, servers_text)
                await send_message(message.chat.id, '⌨️Кнопки серверов:', reply_markup=klava)
            else:
                await send_message(message.chat.id, '⚠️Список серверов пуст')
    except:
        await Print_Error()

@dp.message_handler(commands="wallets")
async def wallets_message(message):
    try:
        user = await user_get(message.chat.id)
        if user.isAdmin:
            wallets_text = ''
            klava = InlineKeyboardMarkup()

            but = InlineKeyboardButton(text=f'➕Добавить', callback_data=f'add_wallet:')
            klava.add(but)

            for wallet in WALLETS:
                id = wallet["id"]
                is_active = wallet["isActive"]

                Name = wallet["Name"]
                API_Key_TOKEN = wallet["API_Key_TOKEN"]
                ShopID_CLIENT_ID = wallet["ShopID_CLIENT_ID"]
                E_mail_URL = wallet["E_mail_URL"]
                
                if API_Key_TOKEN == '-': API_Key_TOKEN = ''
                if ShopID_CLIENT_ID == '-': ShopID_CLIENT_ID = ''
                if E_mail_URL == '-': E_mail_URL = ''

                if Name == PAY_METHODS.XTR:
                    Name = 'Stars'
                    API_Key_TOKEN = 'stars'

                wallets_text += (
                    f'💵<b>{Name}</b> (id:{id})\n'
                    f'🔋Активна: <b>{"✅Да" if is_active else "🛑Нет"}</b>\n'
                )
                if API_Key_TOKEN:
                    wallets_text += f'🔑Key/Token: <b>{API_Key_TOKEN[:24]}...</b>'
                if ShopID_CLIENT_ID:
                    wallets_text += f'\n🆔ID: <code>{ShopID_CLIENT_ID}</code>'
                if E_mail_URL:
                    wallets_text += f'\n📨E-mail/Secret_key: <code>{E_mail_URL}</code>'
                wallets_text += '\n\n'

                but = InlineKeyboardButton(text=f'📊{API_Key_TOKEN[:16]}...', callback_data=f'wallets:{id}')
                klava.add(but)

            if wallets_text == '':
                wallets_text = '⚠️Список способов оплаты пуст!'
            else:
                wallets_text = (
                    '💳Список способов оплаты:\n\n'
                    f'{wallets_text}'
                )

            await send_message(message.chat.id, wallets_text, reply_markup=klava)
    except:
        await Print_Error()

@dp.message_handler(commands="speed_test")
async def speed_test_message(message):
    try:
        if await check_test_mode(message.chat.id): return
        user = await user_get(message.chat.id)
        if user.isAdmin:
            await servers_speedtest(message)
    except:
        await Print_Error()

@dp.message_handler(commands="get_config")
async def get_config_message(message):
    try:
        if await check_test_mode(message.chat.id): return
        user = await user_get(message.chat.id)
        if user.isAdmin:
            await bot.send_document(message.chat.id, open(CONFIG_FILE, 'rb'))
            text_send = (
                'ℹ️Измените необходимые переменные и загрузите файл обратно.\n\n'
                '👨‍💻Бот автоматически сделает копию вашего текущего файла настроек, а после заменит новыми данными и перезагрузит бота!\n\n'
                '👉Рекомендуется программы <a href="https://code.visualstudio.com/Download">VSCode</a> (пользуюсь сам), <a href="https://www.sublimetext.com">Sublime Text</a> (3 МБ), NotePad++'
            )
            await send_message(message.chat.id, text_send)
    except:
        await Print_Error()

@dp.message_handler(commands="get_texts_file")
async def get_texts_file_message(message):
    try:
        user = await user_get(message.chat.id)
        if user.isAdmin:
            await bot.send_document(message.chat.id, open(LANG_FILE, 'rb'))
            await bot.send_document(message.chat.id, open(MARKUP_FILE, 'rb'))
            text_send = (
                'ℹ️Измените необходимые текста, кнопки или клавиатуры и загрузите один из файлов для изменения обратно.\n\n'
                '👨‍💻Бот автоматически сделает копию вашего текущего файла, а после заменит новыми данными и перезагрузит бота!\n\n'
                '👉Рекомендуется программы <a href="https://code.visualstudio.com/Download">VSCode</a> (пользуюсь сам), <a href="https://www.sublimetext.com">Sublime Text</a> (3 МБ), NotePad++'
            )
            await send_message(message.chat.id, text_send)
    except:
        await Print_Error()

@dp.message_handler(commands="reload_servers")
async def reload_servers_message(message):
    try:
        user = await user_get(message.chat.id)
        if user.isAdmin:
            await reboot_all_servers(message)
    except:
        await Print_Error()

@dp.message_handler(commands="balance") 
async def balance_message(message):
    try:
        user = await user_get(message.chat.id)
        if user.isAdmin:
            balance_y = ''

            if len(WALLETS) == 1:
                balance_y = await user.PAY_WALLET.get_balance()
                if balance_y >= 0:
                    balance_y = f'💵Ваш баланс: <b>{balance_y}</b>₽\n\n'
                else:
                    balance_y = f'ℹ️Получить баланс данной платежной системы не представляется возможным!'
            else:
                balance_y = 'ℹ️Для просмотра баланса конкретного способа оплаты перейдите в /wallets\n\n'

            try:
                data = await DB.getAllReportsData()
                if data and len(data) > 0:
                    summ = 0
                    count = 0
                    summ_7 = 0
                    count_7 = 0
                    data_30 = []
                    data_7 = []
                    
                    for item in data:
                        SummDay = item[3]
                        date_izn = item[4]
                        date = datetime.strptime(date_izn, '%Y-%m-%d')

                        date_now = datetime.now()
                        days_raz = (date - date_now).days + 1
                        
                        if days_raz >= -30:
                            summ += SummDay
                            count += 1
                            data_30.append(SummDay)

                        if days_raz >= -7:
                            summ_7 += SummDay
                            count_7 += 1
                            data_7.append(SummDay)

                    summ_sr = round(summ / count, 2)
                    summ_sr_7 = round(summ_7 / count_7, 2)

                    text_send = (
                        f'{balance_y}'

                        '📊Аналитика за все время:\n\n'
                        f'💠Аналитика ведется: <b>{await razryad(len(data))} {await dney(len(data))}</b>\n'
                        f'💠Cумма продаж: <b>{await razryad(sum([da[3] for da in data]))}₽</b>\n'
                        f'💠День с мин. выручкой: <b>{await razryad(min([da[3] for da in data if da[3] > 0]))}₽</b>\n'
                        f'💠День с макс. выручкой: <b>{await razryad(max([da[3] for da in data]))}₽</b>\n\n'

                        '📊Аналитика за последние 30 дней:\n\n'
                        f'💠Средний доход в день: <b>{await razryad(summ_sr)}₽</b>\n'
                        f'💠Прибыль: <b>{await razryad(summ)}₽</b>\n'
                        f'💠День с мин. выручкой: <b>{await razryad(min([da for da in data_30 if da > 0]))}₽</b>\n'
                        f'💠День с макс. выручкой: <b>{await razryad(max([da for da in data_30]))}₽</b>\n\n'

                        '📊Аналитика за последние 7 дней:\n\n'
                        f'💠Средний доход в день: <b>{await razryad(summ_sr_7)}₽</b>\n'
                        f'💠Прибыль: <b>{await razryad(summ_7)}₽</b>\n'
                        f'💠День с мин. выручкой: <b>{await razryad(min([da for da in data_7 if da > 0]))}₽</b>\n'
                        f'💠День с макс. выручкой: <b>{await razryad(max([da for da in data_7]))}₽</b>\n\n'
                    )
                else:
                    text_send = balance_y.replace('\n\n', '')
            except:
                text_send = balance_y.replace('\n\n', '')

            await send_message(message.chat.id, text_send)  
    except:
        await Print_Error()

@dp.message_handler(commands="history") 
async def history_message(message):
    try:
        user = await user_get(message.chat.id)
        if user.isAdmin:
            if len(WALLETS) == 1:
                text_send = await user.PAY_WALLET.get_history()
                if str(text_send) in ('', 'False'):
                    text_send = 'ℹ️История пуста'
                await send_long_message(message.chat.id, f'{text_send}')
            else:
                text_send = 'ℹ️Для просмотра истории конкретного способа оплаты перейдите в /wallets'
                await send_long_message(message.chat.id, f'{text_send}')
    except:
        await Print_Error()

async def transfer_keys(message, all_keys_data, select_servers, one=False):
    try:
        async def delete_key(user_id, bot_key):
            try:
                date = None
                CountDaysBuy = None

                lines = await DB.get_qr_key_All(user_id) # BOT_Key, Date, User_id, isAdminKey, CountDaysBuy, ip_server, isActive, Protocol, isChangeProtocol, DateChangeProtocol, Payment_id
                for line in lines:
                    ip_server = line[5]
                    bot_key1 = line[0]
                    protocol = line[7]
                    date = line[1]
                    CountDaysBuy = line[4]

                    if bot_key == bot_key1:
                        await KEYS_ACTIONS.deleteKey(protocol, bot_key, ip_server, date, CountDaysBuy, user_id)
                        break
                
                await DB.delete_qr_key(bot_key)

                if not IS_OTCHET:
                    await send_admins(user_id, 'Перенос (🔑 удален)', f'<b>{bot_key}</b> ({date}, {CountDaysBuy} {await dney(CountDaysBuy)}, {ip_server}, {protocol})')
                return (date, CountDaysBuy)
            except:
                await Print_Error()

        
        time_start = datetime.now().strftime('%H:%M:%S')
        seconds_start = time.time()

        send_text = (
            f'⏳Время начала: {time_start}\n\n'
            '🔄Перенос ключей на другие сервера\n'
        )
        mes_del = await send_message(message.chat.id, send_text)

        for index, key in enumerate(all_keys_data):
            is_active = bool(key[6])
            key_name = key[0]
            user_id = key[2]

            if is_active:    
                date = key[1]
                CountDaysBuy = key[4]
                # ip_server = key[5]
                protocol = key[7]

                try:
                    send_text_ = f'{send_text}\n\n{await progress_bar(index, len(all_keys_data))}'
                    await bot.edit_message_text(send_text_, message.chat.id, mes_del.message_id, parse_mode='HTML')
                    logger.debug(send_text_)

                    if not one:
                        ip_server_select = None
                        # Узнать на каком сервере меньше всего ключей
                        all_server_ip_and_count_keys = []
                        for server in SERVERS:
                            # если выбрана таже локация, что и сейчас у пользователя, сменить на другой сервер с этой локацией
                            ip = server['ip']
                            count_users_in_server = await DB.get_count_keys_by_ip(ip)
                            if ip in select_servers and count_users_in_server < server['count_keys']:
                                all_server_ip_and_count_keys.append((ip, count_users_in_server))

                        if len(all_server_ip_and_count_keys) > 0:
                            ip_server_select = min(all_server_ip_and_count_keys, key=lambda x: x[1])[0]
                    else:
                        ip_server_select = select_servers[1]

                    if ip_server_select is None:
                        # Создать ключ на любом другом сервере не из списка select_servers
                        for server in SERVERS:
                            # если выбрана таже локация, что и сейчас у пользователя, сменить на другой сервер с этой локацией
                            ip = server['ip']
                            count_users_in_server = await DB.get_count_keys_by_ip(ip)
                            if ip in select_servers and count_users_in_server < server['count_keys']:
                                ip_server_select = ip
                                break

                    await new_key(user_id, day=CountDaysBuy, help_message=True, protocol=protocol, date=date, ip_server=ip_server_select, isChangeLocation=True)
                    await delete_key(user_id, key_name)
                    try:
                        user = await user_get(user_id)
                        await send_message(user_id, user.lang.get('tx_transfer_key'))
                    except Exception as e:
                        logger.warning(f'🛑Ошибка при отправке сообщения пользователю {user_id}: {e}')
                except Exception as e:
                    await send_admins(user_id, '🛑Ошибка при переносе ключа', f'{e}')
                    return False
            else:
                await delete_key(user_id, key_name)

        index = len(all_keys_data)
        send_text = send_text.replace('🔄', '✅', 1)
        send_text_ = f'{send_text}\n⏱️Прошло: {int(time.time() - seconds_start)} сек\n{await progress_bar(index, len(all_keys_data))}'
        await bot.edit_message_text(send_text_, message.chat.id, mes_del.message_id, parse_mode='HTML')
        logger.debug(send_text_)

        # после переноса удалить все сервера, которые не указаны в select_servers
        for server in SERVERS:
            ip = server['ip']
            if (not ip in select_servers and not one) or (one and ip == select_servers[0]):
                # проверить, чтобы на сервере не было ключей
                keys = await DB.get_keys_name_by_ip_server(ip)
                count = len(keys) if not keys is None else 0

                if count > 0:
                    temp = count % 10
                    if temp == 0 or temp > 4:
                        cluch = 'ключей'
                    elif temp == 1:
                        cluch = 'ключ'
                    elif 1 < temp < 5:
                        cluch = 'ключа'
                    await send_message(message.chat.id, f'🛑На сервере <b>{ip}</b> есть <b>{count}</b> {cluch}, удаление не возможно!')
                else:
                    await DB.DELETE_SERVER(ip)
                    await send_message(message.chat.id, f'✅Сервер <b>{ip}</b> успешно удален из бота!')
    except:
        await Print_Error()

@dp.message_handler(commands="transfer") 
async def transfer_message(message):
    try:
        user = await user_get(message.chat.id)
        if user.isAdmin:
            m_text_sp = message.text.replace('/transfer','').strip()

            primer = (
                f'🏷️Пример команды:\n\n'
                '/transfer <b>1.1.1.1 2.2.2.2 3.3.3.3</b> - Перенести всех клиентов с серверов, на перечисленные сервера, где\n'
                '    <b>1.1.1.1 2.2.2.2 3.3.3.3</b> - сервера, на которые перенести клиентов (через пробел)'
            )

            if m_text_sp == '':
                return await send_message(message.chat.id, f'⚠️Вы не указали сервера, на которые желаете перенести ключи!\n\n{primer}')

            m_text_sp = m_text_sp.split()
            select_servers = [item for item in m_text_sp]

            if len(select_servers) > 0 and select_servers[0] != '':
                # Указываешь сервера, на которых ты хочешь разместить всех людей, бот проходит по всем ключам, 
                # если ключ уже расположен на одном из таких серверов, он его пропускает, 

                # если его ключ расположен не на этих серверах, 
                # то он узнает на какой срок у него остался ключ и какого протокола, 
                # удаляет текущий, создает новый с тем же оставшимся кол-вом дней,
                # далее пишет клиенту сообщение:

                # Добрый день, ваш ключ был перенесен на другой сервер из-за технических вопросов, для продолжения использования, скатайте новый ключ:👇 
                # (снизу отобразить список текущих ключей)
                # Приятного пользования сервисом, если что-то будет не понятно, пишите @сюда

                all_keys_data = await DB.get_qr_key_All() # BOT_Key, Date, User_id, isAdminKey, CountDaysBuy, ip_server, isActive, Protocol, isChangeProtocol, DateChangeProtocol, Payment_id
                servers_perenos = []
                keys_for_perenos = []
                for key in all_keys_data:
                    ip_server = key[5]
                    if ip_server in select_servers:
                        continue

                    keys_for_perenos.append(key)

                count_keys_perenos = len(keys_for_perenos)
                for server in SERVERS:
                    ip = server['ip']
                    if ip in select_servers:
                        servers_perenos.append(ip)

                user.servers_perenos = servers_perenos
                user.keys_for_perenos = keys_for_perenos

                if count_keys_perenos == 0:
                    await send_message(message.chat.id, f'⚠️Не было найдено ключей для переноса на перечисленные сервер(а) <b>{tuple(servers_perenos)}</b>')
                else:
                    klava = InlineKeyboardMarkup()
                    but = InlineKeyboardButton(text=f'✅Да', callback_data=f'transfer:yes')
                    klava.add(but)
                    but = InlineKeyboardButton(text=f'🛑Нет', callback_data=f'transfer:no')
                    klava.add(but)
                    text_send = (
                        f'⚠️Будет перенесено <b>{count_keys_perenos}</b> ключей на сервер(а) <b>{tuple(servers_perenos)}</b>\n\n'
                        '⚠️После начала переноса его будет не возможно отменить. По окончанию переноса сервера не находящиеся в списке будут удалены из бота. Вы уверены, что хотите продолжить?'
                    )
                    await send_message(message.chat.id, text_send, reply_markup=klava)
            else:
                await send_message(message.chat.id, f'⚠️Вы не указали сервера, на которые хотите перенести ключи!\n\n{primer}')
    except:
        await Print_Error()

@dp.message_handler(commands="transfer_one") 
async def transfer_one_message(message):
    try:
        user = await user_get(message.chat.id)
        if user.isAdmin:
            m_text_sp = message.text.replace('/transfer_one','').strip()

            primer = (
                f'🏷️Пример команды:\n\n'
                '/transfer_one <b>1.1.1.1 2.2.2.2</b> - Перенести всех клиентов с сервера <b>1.1.1.1</b> на <b>2.2.2.2</b>'
            )
            error_text = f'⚠️Вы не указали необходимые переменные!\n\n{primer}'

            if m_text_sp == '':
                return await send_message(message.chat.id, error_text)

            m_text_sp = m_text_sp.split()
            select_servers = [item for item in m_text_sp]

            if len(select_servers) >= 2 and select_servers[0] != '':
                error = False
                try:
                    server_from = select_servers[0] # С какого сервера переносить
                    if server_from == '':
                        error = True
                    server_to = select_servers[1] # На какой сервер переносить
                    if server_to == '':
                        error = True
                except:
                    error = True

                if error:
                    return await send_message(message.chat.id, error_text)
                # Указываешь сервера, на которых ты хочешь разместить всех людей, бот проходит по всем ключам, 
                # если ключ уже расположен на одном из таких серверов, он его пропускает, 

                # если его ключ расположен не на этих серверах, 
                # то он узнает на какой срок у него остался ключ и какого протокола, 
                # удаляет текущий, создает новый с тем же оставшимся кол-вом дней,
                # далее пишет клиенту сообщение:

                # Добрый день, ваш ключ был перенесен на другой сервер из-за технических вопросов, для продолжения использования, скатайте новый ключ:👇 
                # (снизу отобразить список текущих ключей)
                # Приятного пользования сервисом, если что-то будет не понятно, пишите @сюда

                all_keys_data = await DB.get_qr_key_All() # BOT_Key, Date, User_id, isAdminKey, CountDaysBuy, ip_server, isActive, Protocol, isChangeProtocol, DateChangeProtocol, Payment_id
                servers_perenos = []
                keys_for_perenos = []
                for key in all_keys_data:
                    ip_server = key[5]
                    if ip_server == server_from: # Если расположен на сервере, откуда необходимо перенести, то записываем его в список
                        keys_for_perenos.append(key)
                
                count_keys_perenos = len(keys_for_perenos)
                for server in SERVERS:
                    ip = server['ip']
                    if ip == server_from:
                        servers_perenos.append(ip)
                        break
                for server in SERVERS:
                    ip = server['ip']
                    if ip == server_to:
                        servers_perenos.append(ip)
                        break

                user.servers_perenos = servers_perenos # [0] - сервера откуда переносить, [1] - куда переносить
                user.keys_for_perenos = keys_for_perenos

                if count_keys_perenos == 0:
                    await send_message(message.chat.id, f'⚠️Не было найдено ключей для переноса c сервера <b>{server_from}</b> на <b>{server_to}</b>')
                else:
                    klava = InlineKeyboardMarkup()
                    but = InlineKeyboardButton(text=f'✅Да', callback_data=f'transfer:yes:one')
                    klava.add(but)
                    but = InlineKeyboardButton(text=f'🛑Нет', callback_data=f'transfer:no')
                    klava.add(but)
                    text_send = (
                        f'⚠️Будет перенесено <b>{count_keys_perenos}</b> ключей c сервера <b>{server_from}</b> на <b>{server_to}</b>\n\n'
                        f'⚠️После начала переноса его будет не возможно отменить. По окончанию переноса сервер <b>{server_from}</b>, с короторого производиться перенос будет удален из бота. Вы уверены, что хотите продолжить?'
                    )
                    await send_message(message.chat.id, text_send, reply_markup=klava)
            else:
                await send_message(message.chat.id, error_text)
    except:
        await Print_Error()

@dp.message_handler(commands="urls")
async def urls_message(message):
    try:
        user = await user_get(message.chat.id)
        if user.isAdmin:
            klava_yes = False
            urls_text = 'Название - Ссылка - Кол-во клиентов - Сумма ₽\n\n'
            users_data = await DB.get_all_users_report() # User_id, Nick, First_Name, Last_Name, id_Otkuda, Summ
            data_promo = await DB.get_stats_promoses() # u.Promo, u.Discount_percentage, COUNT(u.User_id) , SUM(u.Summ)

            for i in list(LINK_FROM.keys()):
                title = LINK_FROM[i]
                url = f'https://t.me/{BOT_NICK}?start=global_{i}'

                # Загрузить кто откуда пришел и узнать сколько пришло по этой ссылке
                count_user = 0
                for user in users_data:
                    if user[4] == i:
                        count_user += 1

                summ_ = await DB.get_summ_by_otkuda(i)
                count_users = f' - {count_user} - {summ_}₽'
                urls_text += f'{title} - {url}{count_users}\n'

            if data_promo and len(data_promo) > 0:
                if data_promo[0] and len(data_promo[0]) > 0 and data_promo[0][0]:
                    urls_text += '\nID - Код - Кол-во клиентов - Заработок партнера - % Партнеру\n\n'
                    temp_massiv = []
                    for i in data_promo:
                        code = i[0]
                        percatage = i[1]
                        id_partner = i[2]
                        percent_partner = i[3]
                        count = i[4] if not i[4] is None else 0
                        summ = i[5] if not i[5] is None else 0
                        # url = f'https://t.me/{BOT_NICK}?start={code}'
                        id = int(i[8])
                        date = i[7]
                        if date is None:
                            date = datetime.now()
                            await DB.update_spec_url(id, date)
                            date = date.strftime("%Y-%m-%d %H:%M:%S.%f")

                        if '.' in str(date):
                            date_time = datetime.strptime(date, "%Y-%m-%d %H:%M:%S.%f")
                        else:
                            date_time = datetime.strptime(date, "%Y-%m-%d %H:%M:%S")

                        date_str = date_time.strftime("%d.%m.%y %H:%M:%S")

                        klava_yes = True

                        #region Подсчитывание заработка партнера
                        resu1 = await DB.get_user_operations(code, 'prodl')
                        resu2 = await DB.get_user_operations(code, 'buy')
                        resu3 = await DB.get_user_operations(code, 'promo', da=True)
                        last_dolg = await DB.get_parter_pay(id_partner)

                        if not last_dolg is None and len(last_dolg) > 0:
                            last_dolg_date = datetime.strptime(last_dolg[-1][1], "%Y-%m-%d %H:%M:%S.%f")
                            last_dolg = last_dolg[-1][4]
                        else:
                            last_dolg = 0
                            last_dolg_date = None

                        # Считаем сумму продлений
                        total_prodl_summ = 0
                        new_prodl_summ = 0

                        for res in resu1:
                            total_summ = res[0]
                            date_ = res[1]
                            total_prodl_summ += total_summ

                            if not last_dolg_date is None and datetime.strptime(date_, "%Y-%m-%d %H:%M:%S.%f") < last_dolg_date:
                                continue

                            new_prodl_summ += total_summ

                        # Считаем сумму покупок
                        total_buy_summ = 0
                        new_buy_summ = 0

                        for res in resu2:
                            total_summ = res[0]
                            date_ = res[1]
                            total_buy_summ += total_summ

                            if not last_dolg_date is None and datetime.strptime(date_, "%Y-%m-%d %H:%M:%S.%f") < last_dolg_date:
                                continue

                            new_buy_summ += total_summ

                        if percatage == 0:
                            # Считаем сумму промокодов
                            total_promo_summ = 0
                            new_promo_summ = 0

                            for res in resu3:
                                total_summ = res[0]
                                date_ = res[1]
                                total_promo_summ += total_summ

                                if not last_dolg_date is None and datetime.strptime(date_, "%Y-%m-%d %H:%M:%S.%f") < last_dolg_date:
                                    continue

                                new_promo_summ += total_summ  
                        else:
                            new_promo_summ = 0
                            total_promo_summ = 0

                        total_partner = (total_buy_summ + total_prodl_summ + total_promo_summ) * percent_partner / 100
                        #endregion

                        temp_massiv.append((id, code, count, total_partner, percent_partner, date_str))

                    temp_massiv = sorted(temp_massiv, key=lambda item: (item[3], item[2]), reverse=True)
                    for i in temp_massiv:
                        id = i[0]
                        code = i[1]
                        count = i[2]
                        total_partner = i[3]
                        percent_partner = i[4]

                        dop_chislo = 1
                        if 'BONUS' in code and 'add' in BOT_NICK:
                            dop_chislo = 23

                        urls_text += f'{id} - <code>{code}</code> - {await razryad(count * dop_chislo)} - {await razryad(total_partner * dop_chislo)}₽ - {percent_partner}%\n'

            if urls_text == 'Название - Ссылка - Кол-во клиентов - Сумма ₽\n\n':
                await send_message(message.chat.id, '⚠️Список специальных ссылок пуст')
            else:
                if not klava_yes:
                    await send_long_message(message.chat.id, urls_text)
                else:
                    klava = InlineKeyboardMarkup()
                    but = InlineKeyboardButton(text=f'💰Запросы на вывод', callback_data=f'zaprosi::')
                    klava.add(but)
                    await send_long_message(message.chat.id, urls_text, reply_markup=klava) 
                    await send_message(message.chat.id, 'ℹ️Для просмотра информации по спец.ссылке, выберите интересующее <b>Название</b>, коснитесь его в тексте (тем самым скопировав его), вставьте и отправьте его боту')
                    user = await user_get(message.chat.id)
                    user.bot_status = 4
    except:
        await Print_Error()

@dp.message_handler(commands="check") 
async def check_message(message):
    try:
        user = await user_get(message.chat.id)
        if user.isAdmin:
            await send_message(message.chat.id, '✅Запущена ежедневная проверка ключей!')
            tasks = [asyncio.create_task(check_keys_all())]
            asyncio.gather(*tasks)
    except:
        await Print_Error()

@dp.message_handler(commands="add_server")
async def add_server_message(message):
    try:
        user_id = message.chat.id
        user = await user_get(user_id)
        if user.isAdmin:
            m_text = message.text.replace('/add_server ','')
            m_text_sp = m_text.split()
            text_primer = (
                f'🏷️Пример команды:\n\n/add_server <b>1.1.1.1</b> <b>svf4sg43</b> <b>240</b> <b>🇳🇱Нидерланды</b> - Автоматическая настройка и добавление нового сервера в бота,\n'
                '    где <b>1.1.1.1</b> - ip сервера,\n'
                '    <b>svf4sg43</b> - пароль от сервера,\n'
                '    <b>240</b> - желаемое кол-во ключей на сервере (от 1 до 240),\n'
                '    <b>🇳🇱Нидерланды</b> - название локации (без пробелов, можно изменить в /servers) (укажите одно для нескольких серверов, чтобы они объединились в одну локацию)\n\n'
                
                '⚙️<b>Необходимые характеристики:</b> <u>Чистый сервер Debian 11 с 2GB оперативной памяти и 1 Гбит/с пропускной способности</u>\n\n'
                
                'ℹ️Marzban: для установки основного сервера после названия локации введите: marzban\n'
                'ℹ️PPTP: для добавления сервера для PPTP после названия локации введите: pptp\n'
                '⚠️На сервере PPTP не может быть больше 100 ключей! Обусловленно ограничением протокола PPTP'
            )

            try:
                ip = m_text_sp[0]
                password = m_text_sp[1]
                count_keys = int(m_text_sp[2])
                location = m_text_sp[3]

                if not re.match(r'^[a-zA-Z0-9]+$', password):
                    return await send_message(user_id, '🛑Пароль должен содержать только английские буквы и цифры, иначе остальные символы в процессе могут быть не учтены той или иной библиотекой!')

                if not 1 <= count_keys <= 240:
                    return await send_message(user_id, '🛑Параметры переданы не верно!')
            except:
                await send_message(user_id, text_primer)
                return

            try:
                api_url = m_text_sp[4]
                cert_sha256 = m_text_sp[5]
                isConfigured = True
            except:
                isConfigured = False
                api_url = None
                cert_sha256 = None

            is_marzban = 'marzban' in m_text
            is_pptp = 'pptp' in m_text
            if is_marzban or is_pptp:
                isConfigured = False

            # Проверить если ли такой ip сервера в списке серверов
            for server in SERVERS:
                if server['ip'] == ip:
                    await send_message(user_id, f'🛑Сервер {ip} уже добавлен в бота!')
                    return

            async def a_addNewServer(isConfigured, ip, password, count_keys, api_url, cert_sha256, location):
                try:
                    if not isConfigured:
                        if is_marzban:
                            marzban = MARZBAN(ip=ip, password=password)
                            result = await marzban.install_marzban_for_server(user_id, location)
                        elif is_pptp:
                            pptp = PPTP(ip=ip, password=password)
                            result = await pptp.install_server(user_id)
                        else:
                            result = await add_new_server_ssh(user_id, ip=ip, password=password)
                    else:
                        result = (api_url, cert_sha256)

                    if result:
                        if is_marzban or is_pptp:
                            api_url = '-'
                            cert_sha256 = '-'
                        else:
                            api_url = result[0]
                            cert_sha256 = result[1]

                        if is_pptp and count_keys > 100:
                            count_keys = 100

                        await DB.ADD_SERVER(ip, password, count_keys, api_url, cert_sha256, location, is_marzban, is_pptp)
                        await send_message(user_id, f'✅Сервер {ip} успешно настроен и добавлен в список серверов бота!')

                        if len(SERVERS) == 2:
                            # перезагрузить бота, чтобы появилась кнопка в меню
                            await AdminCommand(command='supervisorctl restart bot', sillent=True)
                except:
                    await Print_Error()

            tasks = [asyncio.create_task(a_addNewServer(isConfigured, ip, password, count_keys, api_url, cert_sha256, location))]
            asyncio.gather(*tasks)
            global user_dict
            user_dict = {}
    except:
        await Print_Error()

@dp.message_handler(commands="add_location")
async def add_location_message(message):
    try:
        user = await user_get(message.chat.id)
        if user.isAdmin:
            # проверить, чтобы был основной сервер Marzban
            for server in SERVERS:
                if server['is_marzban']:
                    break
            else:
                await send_message(message.chat.id, '🛑Не найден основной сервер Marzban!\n\n<i>ℹ️Вы можете доабвить его в /add_server по инструкции</i>')
                return
            
            m_text_sp = message.text.replace('/add_location ','').split()
            text_primer = (
                f'🏷️Пример команды:\n\n/add_location <b>1.1.1.1</b> <b>svf4sg43</b> <b>🇳🇱Нидерланды</b> - Автоматическая настройка и добавление нового сервера в подписку Marzban,\n'
                '    где <b>1.1.1.1</b> - ip сервера,\n'
                '    <b>svf4sg43</b> - пароль от сервера,\n'
                '    <b>"🇳🇱Нидерланды"</b> - название локации (без пробелов!)\n\n'
                '⚠️<b>Для добавления сервера необходимо:</b>\n'
                '- пустой сервер на <b>Debian 11</b> с <b>минимум 2GB</b> оперативной памяти и <b>1Гбит/с</b> пропускной способнотью\n'
                '- ip и пароль от root пользователя\n\n'
            )
            
            try:
                ip = m_text_sp[0]
                password = m_text_sp[1]
                location = m_text_sp[2]
            except:
                await send_message(message.chat.id, text_primer)
                return
            
            async def a_addNewServer(user_id, ip, password, location):
                try:
                    # взять ip и пароль от основного сервера Marzban и добавить новую локацию
                    for server in SERVERS:
                        if server['is_marzban']:
                            marzban = MARZBAN(ip=server['ip'], password=server['password'])
                            result = await marzban.install_dop_server_marzban(message.chat.id, location, ip, password)
                            if result:
                                await send_message(user_id, f'✅Сервер {ip} успешно настроен и добавлен в подписку Marzban!')
                                break
                except:
                    await Print_Error()

            tasks = [asyncio.create_task(a_addNewServer(message.chat.id, ip, password, location))]
            asyncio.gather(*tasks)
    except:
        await Print_Error()

@dp.message_handler(commands="add_server_for_whitelist")
async def add_server_for_whitelist_message(message):
    """
    Команда для настройки whitelist-туннеля VLESS over VLESS
    Логика: клиент -> местный сервер -> зарубежный сервер -> интернет
    
    Формат: /add_server_for_whitelist ip_local password_local название1 ip_foreign password_foreign название2
    """
    try:
        user_id = message.chat.id
        user = await user_get(user_id)
        
        if not user.isAdmin:
            return
        
        m_text = message.text.replace('/add_server_for_whitelist ', '').strip()
        
        # Пример использования
        text_primer = (
            f'🏷️<b>Пример команды:</b>\n\n'
            f'<code>/add_server_for_whitelist 1.1.1.1 pass123 Москва 2.2.2.2 pass456 Amsterdam</code>\n\n'
            f'Где:\n'
            f'• <b>1.1.1.1</b> - IP местного сервера (Россия)\n'
            f'• <b>pass123</b> - Пароль от местного сервера\n'
            f'• <b>Москва</b> - Название для местного сервера\n'
            f'• <b>2.2.2.2</b> - IP зарубежного сервера (Нидерланды)\n'
            f'• <b>pass456</b> - Пароль от зарубежного сервера\n'
            f'• <b>Amsterdam</b> - Название для зарубежного сервера\n\n'
            f'⚙️<b>Требования:</b>\n'
            f'• Оба сервера: Debian 11, 2GB RAM, 1 Гбит/с\n'
            f'• Чистые сервера без установленных панелей\n'
            f'• Зарубежный сервер должен иметь чистый IP (не в блокировках)\n\n'
            f'ℹ️<b>Принцип работы:</b>\n'
            f'1. Сканзируется подсеть зарубежного сервера для поиска оптимального SNI домена\n'
            f'2. Устанавливается 3X-UI на оба сервера\n'
            f'3. Настраивается VLESS туннель с маскировкой под HTTPS трафик\n'
            f'4. Трафик идёт через местный сервер → зарубежный → интернет'
        )
        
        # Парсим аргументы
        m_text_sp = m_text.split()
        
        if len(m_text_sp) < 6:
            await send_message(user_id, text_primer, parse_mode='HTML')
            return
        
        try:
            local_ip = m_text_sp[0]
            local_password = m_text_sp[1]
            local_name = m_text_sp[2]
            foreign_ip = m_text_sp[3]
            foreign_password = m_text_sp[4]
            foreign_name = m_text_sp[5]
            
            # Валидация IP
            if not re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', local_ip):
                return await send_message(user_id, '🛑Неверный формат IP местного сервера!')
            
            if not re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', foreign_ip):
                return await send_message(user_id, '🛑Неверный формат IP зарубежного сервера!')
            
            # Проверка паролей
            if not re.match(r'^[a-zA-Z0-9]+$', local_password):
                return await send_message(user_id, '🛑Пароль местного сервера должен содержать только английские буквы и цифры!')
            
            if not re.match(r'^[a-zA-Z0-9]+$', foreign_password):
                return await send_message(user_id, '🛑Пароль зарубежного сервера должен содержать только английские буквы и цифры!')
            
        except Exception as e:
            await send_message(user_id, f'🛑Ошибка парсинга аргументов: {e}\n\n{text_primer}', parse_mode='HTML')
            return
        
        # Проверка: не добавлены ли уже такие сервера
        for server in SERVERS:
            if server['ip'] == local_ip or server['ip'] == foreign_ip:
                return await send_message(user_id, f'🛑Один из серверов ({local_ip} или {foreign_ip}) уже добавлен в бота!')
        
        # Запускаем процесс настройки
        async def setup_whitelist_tunnel():
            try:
                # Шаг 1: Приветственное сообщение
                await send_message(
                    user_id,
                    f"🚀 <b>Запуск настройки whitelist-туннеля...</b>\n\n"
                    f"📍 Местный сервер: <code>{local_ip}</code> ({local_name})\n"
                    f"🌍 Зарубежный сервер: <code>{foreign_ip}</code> ({foreign_name})\n\n"
                    f"⏳ Это займёт 5-10 минут",
                    parse_mode='HTML'
                )
                
                # Шаг 2: Сканирование подсети и поиск SNI домена
                await send_message(
                    user_id,
                    "🔍 <b>Шаг 1/5: Сканирование подсети для поиска SNI домена...</b>\n"
                    "⏳ Это может занять несколько минут",
                    parse_mode='HTML'
                )
                
                sni_result = await select_best_sni_domain(foreign_ip, foreign_password, user_id, bot)
                
                if not sni_result:
                    # Если не нашли домен, используем популярный CDN
                    sni_result = {
                        'domain': 'www.microsoft.com',
                        'ip': foreign_ip,
                        'latency': 100
                    }
                    await send_message(
                        user_id,
                        f"⚠️ Не удалось найти оптимальный домен в подсети, используем запасной вариант:\n"
                        f"🌐 <b>www.microsoft.com</b>",
                        parse_mode='HTML'
                    )
                else:
                    await send_message(
                        user_id,
                        f"✅ SNI домен найден: <b>{sni_result['domain']}</b>\n"
                        f"⚡ Задержка: {sni_result['latency']:.0f} мс",
                        parse_mode='HTML'
                    )
                
                sni_domain = sni_result['domain']
                
                # Шаг 3: Установка 3X-UI на зарубежный сервер
                await send_message(
                    user_id,
                    f"🔄 <b>Шаг 2/5: Установка 3X-UI на зарубежный сервер ({foreign_ip})...</b>",
                    parse_mode='HTML'
                )
                
                foreign_installed = await install_xui_for_whitelist(
                    foreign_ip, foreign_password, 'foreign', sni_domain, user_id, bot
                )
                
                if not foreign_installed:
                    return await send_message(user_id, f"🛑 Ошибка установки 3X-UI на зарубежный сервер!")
                
                # Шаг 4: Установка 3X-UI на локальный сервер
                await send_message(
                    user_id,
                    f"🔄 <b>Шаг 3/5: Установка 3X-UI на локальный сервер ({local_ip})...</b>",
                    parse_mode='HTML'
                )
                
                local_installed = await install_xui_for_whitelist(
                    local_ip, local_password, 'local', None, user_id, bot
                )
                
                if not local_installed:
                    return await send_message(user_id, f"🛑 Ошибка установки 3X-UI на локальный сервер!")
                
                # Шаг 5: Настройка VLESS туннеля
                await send_message(
                    user_id,
                    f"🔄 <b>Шаг 4/5: Настройка VLESS туннеля между серверами...</b>",
                    parse_mode='HTML'
                )
                
                tunnel_setup = await setup_vless_tunnel(
                    local_ip, local_password,
                    foreign_ip, foreign_password,
                    sni_domain, user_id, bot
                )
                
                if not tunnel_setup:
                    return await send_message(user_id, f"🛑 Ошибка настройки VLESS туннеля!")
                
                # Шаг 6: Добавление серверов в базу данных
                await send_message(
                    user_id,
                    f"🔄 <b>Шаг 5/5: Добавление серверов в базу данных...</b>",
                    parse_mode='HTML'
                )
                
                # Добавляем локальный сервер
                await DB.ADD_SERVER(
                    local_ip, local_password, 240,
                    f'http://{local_ip}:43234', '-',
                    local_name, False, False
                )
                
                # Добавляем зарубежный сервер
                await DB.ADD_SERVER(
                    foreign_ip, foreign_password, 240,
                    f'http://{foreign_ip}:43234', '-',
                    foreign_name, False, False
                )
                
                # Финальное сообщение
                await send_message(
                    user_id,
                    f"✅ <b>Whitelist-туннель успешно настроен!</b>\n\n"
                    f"📍 <b>Местный сервер:</b>\n"
                    f"   IP: <code>{local_ip}</code>\n"
                    f"   Название: {local_name}\n\n"
                    f"🌍 <b>Зарубежный сервер:</b>\n"
                    f"   IP: <code>{foreign_ip}</code>\n"
                    f"   Название: {foreign_name}\n\n"
                    f"🎭 <b>SNI маскировка:</b>\n"
                    f"   Домен: <b>{sni_domain}</b>\n\n"
                    f"🔒 <b>Принцип работы:</b>\n"
                    f"   Клиент → {local_ip} → {foreign_ip} → Интернет\n\n"
                    f"⚡ Трафик маскируется под HTTPS соединения с {sni_domain}\n"
                    f"📊 Панель управления: http://{local_ip}:{X3_UI_PORT_PANEL}\n"
                    f"🔐 Логин/пароль: root / {local_password}",
                    parse_mode='HTML'
                )
                
                # Перезагружаем бота для обновления списка серверов
                if len(SERVERS) == 2:
                    await AdminCommand(command='supervisorctl restart bot', sillent=True)
                
            except Exception as e:
                await Print_Error()
                await send_message(user_id, f"🛑 Произошла ошибка при настройке: {e}", parse_mode='HTML')
        
        # Запускаем задачу
        tasks = [asyncio.create_task(setup_whitelist_tunnel())]
        asyncio.gather(*tasks)
        
        global user_dict
        user_dict = {}
        
    except Exception as e:
        await Print_Error()

async def create_new_spec_url(user_id, id_partner, promo_code, percent_discount, percent_partner, message=None):
    try:
        if not await DB.exists_user(id_partner):
            await send_message(user_id, f'🛑Пользователь с id = {id_partner} не зарегистирован в боте!')
            return

        result = await DB.add_spec_urls(promo_code, percent_discount, id_partner=id_partner, percent_partner=percent_partner)

        if not result:
            await send_message(user_id, f'🛑Специальная ссылка "{promo_code}" создана ранее или у партнера уже имеется специальная ссылка!')
            return

        if len(user_dict) > 0:
            for id_cl in user_dict.keys():
                await user_dict[id_cl].set_tarifs()

        if not result:
            if str(id_partner) != promo_code:
                await send_message(user_id, f'⚠️Специальная ссылка "{promo_code}" создана ранее, попытка создать с id партнера...')
                return await create_new_spec_url(user_id, id_partner, f'{id_partner}', percent_discount, percent_partner)
            else:
                await send_message(user_id, f'🛑Специальная ссылка "{promo_code}" создана ранее!')

        user = await user_get(user_id)
        if user_id == id_partner:
            # перебросить на статистику по партнерской ссылке
            await message_input(message, alt_text=user.lang.get('but_partner'))
        await send_message(user_id, user.lang.get('tx_create_spec_url').format(promo=promo_code))
    except:
        await Print_Error()

@dp.message_handler(commands="create") 
async def create_promo_message(message):
    try:
        user_id = message.chat.id
        user = await user_get(user_id)

        if user.isAdmin:
            m_text_sp = message.text.replace('/create ','').split()
            primer = (
                f'🏷️Пример команды:\n\n'
                '/create <b>30%</b> <b>PROMO</b> <b>782280769</b> <b>50%</b> - Создание спец. ссылки для партнера, где\n'
                '    <b>30%</b> - скидка для клиентов на первую покупку,\n'
                '    <b>PROMO</b> - название для ссылки,\n'
                '    <b>782280769</b> - id партнера (для кого создаем ссылку),\n'
                '    <b>50%</b> - заработок партнера'
            )

            if message.text.replace('/create','').strip() == '':
                return await send_message(message.chat.id, primer)
            try:
                percent_discount = int(m_text_sp[0].replace('%',''))
                promo_code = m_text_sp[1]
                id_partner = int(m_text_sp[2])
                percent_partner = int(m_text_sp[3].replace('%',''))
            except:
                return await send_message(user_id, primer)

            await create_new_spec_url(user_id, id_partner, promo_code, percent_discount, percent_partner, message=message)
    except:
        await Print_Error()

@dp.message_handler(commands="promo")
async def promo_all_message(message):
    try:
        user = await user_get(message.chat.id)
        if user.isAdmin:
            m_text = message.text

            try:
                count = int(m_text.split()[1])
                await generate_and_send_promo(message, count)
                return
            except:
                pass

            promo_text = '📊<b>Промокод - кол-во дней</b>\n<i>(<s>зачеркнутый</s> = активированный)</i>\n\n'
            count_30 = 0
            count_90 = 0
            count_180 = 0
            count_365 = 0
            count_all = 0

            data_ = await DB.get_all_promo_codes()
            for index, i in enumerate(data_): # SELECT Code, CountDays, isActivated FROM PromoCodes
                code = i[0]
                CountDays = i[1]
                isActivated = bool(i[2])
                user = i[3]

                if not isActivated:
                    promo_text += f'{index+1}. <code>{code}</code> - {CountDays}\n'
                else:
                    user = f' - @{user}' if user != '' else ''
                    promo_text += f'<s>{index+1}. {code} - {CountDays}{user}</s>\n'

                if index % 99 == 0 and index != 0:
                    await send_long_message(message.chat.id, promo_text)
                    promo_text = ''

                if CountDays == 30:
                    count_30 += 1
                elif CountDays == 90:
                    count_90 += 1
                elif CountDays == 180:
                    count_180 += 1
                elif CountDays == 365:
                    count_365 += 1
                count_all += 1

            generate = GeneratePromo()
            if count_all == 0:
                await generate.Generate(count_days=30, count=20)
                await generate.Generate(count_days=90, count=10)
                await generate.Generate(count_days=180, count=10)
                await generate.Generate(count_days=365, count=10)
                await send_message(message.chat.id, '⚠️Промокодов не было найдено, поэтому было создано 20 промокодов на 1 месяц и по 10 на 3, 6, 12 месяцев\n\n/promo - посмотреть промокоды')
                await send_message(message.chat.id, f'✅Для создания промокодов на любое кол-во дней введите по примеру: <i>/promo 37</i>')
            else:
                if promo_text != '':
                    await send_long_message(message.chat.id, promo_text)
                if count_30 < 10:
                    days = 30
                    await generate.Delete(count_days=days)
                    await generate.Generate(count_days=days, count=10)
                    await send_message(message.chat.id, f'⚠️Промокодов на {days} дней не было найдено, поэтому было создано еще 10 и удалены все активированные!')
                if count_90 < 10:
                    days = 90
                    await generate.Delete(count_days=days)
                    await generate.Generate(count_days=days, count=10)
                    await send_message(message.chat.id, f'⚠️Промокодов на {days} дней не было найдено, поэтому было создано еще 10 и удалены все активированные!')
                if count_180 < 10:
                    days = 180
                    await generate.Delete(count_days=days)
                    await generate.Generate(count_days=days, count=10)
                    await send_message(message.chat.id, f'⚠️Промокодов на {days} дней не было найдено, поэтому было создано еще 10 и удалены все активированные!')
                if count_365 < 10:
                    days = 365
                    await generate.Delete(count_days=days)
                    await generate.Generate(count_days=days, count=10)
                    await send_message(message.chat.id, f'⚠️Промокодов на {days} дней не было найдено, поэтому было создано еще 10 и удалены все активированные!')
                await send_message(message.chat.id, f'✅Для создания промокодов на любое кол-во дней введите по примеру: <i>/promo 37</i>')
            await DB.conn.commit() # Сохраняем изменения
    except:
        await Print_Error()

@dp.message_handler(commands="code")
async def code_message(message):
    try:
        user_id = message.chat.id
        user = await user_get(user_id)
        if user.isAdmin:
            m_text_sp = message.text.replace('/code','').strip().split()
            primer = (
                f'🏷️Пример команды:\n\n'
                '/code <b>SALE</b> <b>7</b> <b>100</b> <b>14</b> - Создание инд.промокода, где\n'
                '    <b>SALE</b> - название инд.промокода,\n'
                '    <b>7</b> - кол-во дней, которые он дает клиенту,\n'
                '    <b>100</b> - возможное кол-во активаций,\n'
                '    <b>14</b> - кол-во дней, через которое удалиться инд.промокод'
            )

            try:
                code = m_text_sp[0]
                days = int(m_text_sp[1])
                count = int(m_text_sp[2])
                count_days_delete = int(m_text_sp[3])
            except:
                return await send_message(user_id, primer)

            result = await DB.add_individual_promo_code(code, days, count, count_days_delete)
            if result:
                await send_message(user_id, f'✅Индивидуальный промокод <b>{code}</b> успешно создан!')
            else:
                await send_message(user_id, f'🛑Индивидуальный промокод <b>{code}</b> не удалось создать так как он существует или был создан ранее!')
    except:
        await Print_Error()

@dp.message_handler(commands="code_view")
async def code_view_message(message):
    try:
        user_id = message.chat.id
        user = await user_get(user_id)
        if user.isAdmin:
            data_ = await DB.get_all_individual_promo_codes() # code, days, count, count_days_delete, date_create, count_activate
            if not len(data_):
                return await send_message(user_id, '⚠️Актуальные индивидуальные промокоды не найдены!')
                
            promo_text = '📊<b>Промокод - кол-во дней - кол-во активаций - дней до удаления</b>\n\n'
            for index, i in enumerate(data_):
                code = i[0]
                days = i[1]
                count = i[2]
                count_days_delete = i[3]
                date_create = i[4]
                count_activate = i[5]
                
                date_create = datetime.strptime(date_create, "%Y-%m-%d")

                count_days_delete = count_days_delete - (datetime.now() - date_create).days
                days_text = await dney(count_days_delete)
                promo_text += f'{index+1}. <code>{code}</code> - {days} - <b>{count_activate}</b>/{count} - {count_days_delete} {days_text}\n'

                if index % 19 == 0 and index != 0:
                    await send_long_message(user_id, promo_text)
                    promo_text = ''
                    
            if promo_text != '':
                await send_long_message(user_id, promo_text)
    except:
        await Print_Error()

@dp.message_handler(commands="otvet")
async def otvet_message(message):
    try:
        user = await user_get(message.chat.id)

        if user.isAdmin:
            m_text = message.text
            primer = (
                f'🏷️Пример команды:\n\n'
                '/otvet <b>30</b> - Сформировать шаблон-ответ с промокодом, где\n'
                '    <b>30</b> - кол-во дней на которое сформируется промокод'
            )
            try:
                count = int(m_text.split()[1])
                code = await generate_and_send_promo(message, count, silent=True)
                return await send_message(message.chat.id, user.lang.get('tx_otvet_pattern').format(promo=code, count=count, dney_text=await dney(count), nick_bot=BOT_NICK))
            except:
                await send_message(message.chat.id, primer)
    except:
        await Print_Error()

@dp.message_handler(commands=["promo_30", "promo_90", "promo_180", "promo_365"])
async def promo_message(message):
    try:
        user = await user_get(message.chat.id)
        if user.isAdmin:
            m_text = message.text
            try:
                count = int(m_text.split('_')[1])
                return await generate_and_send_promo(message, count)
            except:
                pass
    except:
        await Print_Error()

async def generate_and_send_promo(message, count_day_for_proverka, silent=False):
    try:
        user = await user_get(message.chat.id)
        if user.isAdmin:
            promo_text = ''
            generate = GeneratePromo()
            if promo_text == '':
                await generate.Generate(count_days=count_day_for_proverka, count=1)

            await DB.conn.commit()
            data_ = await DB.get_all_promo_codes()
            for i in data_[::-1]:
                code = i[0]
                CountDays = i[1]
                isActivated = bool(i[2])

                if not isActivated and count_day_for_proverka == CountDays:
                    promo_text += f'<code>{code}</code>'
                    if silent:
                        return code
                    else:
                        break

            if not silent:
                await send_message(message.chat.id, f'{promo_text}')
            return True
    except:
        await Print_Error()
        return False

@dp.message_handler(commands="report")
async def report_message(message):
    try:
        user = await user_get(message.chat.id)
        if user.isAdmin:
            count = await DB.get_count_users_and_keys()
            user_data = await DB.get_all_users_report()
            data_keys = await DB.get_user_keys()

            # Подсчет кол-ва разных типов клиентов
            count_users_all = len(user_data)
            count_users_active_keys = 0
            count_users_test_key = 0
            count_users_no_keys_and_not_pay = 0
            count_users_pay_no_keys = 0
            count_users_block = 0
            count_users_tarifs = 0

            for item in user_data:
                id_client = item[0]
                if bool(item[6]):
                    count_users_block += 1
                    
                tarifs = item[8]
                if tarifs != '':
                    count_users_tarifs += 1

                summ_user_pay = int(item[5])
                data_keys_user = [key for key in data_keys if key[10] == id_client and bool(key[6])]

                if data_keys_user and len(data_keys_user) > 0:
                    test_key_yes = False
                    active_key_yes = False

                    for key in data_keys_user:
                        count_days = key[4]
                        if not (COUNT_DAYS_TRIAL - 2 <= count_days <= COUNT_DAYS_TRIAL + 2):
                            if not active_key_yes:
                                count_users_active_keys += 1
                                active_key_yes = True
                        else:
                            if not test_key_yes:
                                count_users_test_key += 1
                                test_key_yes = True
                else:
                    if summ_user_pay == 0:
                        count_users_no_keys_and_not_pay += 1
                    else:
                        count_users_pay_no_keys += 1

            klava_buy = InlineKeyboardMarkup()
            klava_buy.add(InlineKeyboardButton(text=f'Все пользователи ({count_users_all})', callback_data=f'report:all'))
            if count_users_active_keys > 0:
                klava_buy.add(InlineKeyboardButton(text=f'C активными ключами ({count_users_active_keys})', callback_data=f'report:active'))
            if count_users_test_key > 0:
                klava_buy.add(InlineKeyboardButton(text=f'C тестовыми ключами ({count_users_test_key})', callback_data=f'report:test'))
            if count_users_pay_no_keys > 0:
                klava_buy.add(InlineKeyboardButton(text=f'Платили (сейчас нет ключей) ({count_users_pay_no_keys})', callback_data=f'report:pay_no_keys'))
            if count_users_no_keys_and_not_pay > 0:
                klava_buy.add(InlineKeyboardButton(text=f'Без ключей и оплат ({count_users_no_keys_and_not_pay})', callback_data=f'report:no_pay_no_keys'))
            if count_users_block > 0:
                klava_buy.add(InlineKeyboardButton(text=f'Заблокированные ({count_users_block})', callback_data=f'report:block'))
            if count_users_tarifs > 0:
                klava_buy.add(InlineKeyboardButton(text=f'Индивидуальные тарифы ({count_users_tarifs})', callback_data=f'report:tarifs'))

            await send_message(message.chat.id, '👨‍💻Пользователи', reply_markup=klava_buy)

            #region Подсчет кол-ва ключей, у которых закончится доступ через {COUNT_DAYS_OTCHET}
            count_off_days = 0
            lines = await DB.get_qr_key_All() # BOT_Key, Date, User_id, isAdminKey, CountDaysBuy, ip_server 

            for line in set(lines):
                date_key = line[1]
                isAdminKey = bool(line[3])
                CountDaysBuy = int(line[4])
                isActive = bool(line[6])
                if isAdminKey or not isActive: # Если ключ админский, пропускаем проверку
                    continue
                try:
                    date_start = datetime.strptime(date_key, '%Y_%m_%d')
                except:
                    await Print_Error()
                    continue

                date_now = datetime.now()
                date_end = date_start + timedelta(days=CountDaysBuy)
                days_raz = (date_end - date_now).days

                if days_raz <= COUNT_DAYS_OTCHET:
                    count_off_days += 1
            #endregion

            text_send = (
                f'Кол-во пользователей: {count[0]}\n'
                f'Кол-во выданных ключей: {count[1]}\n\n'
                f'Кол-во ключей, у которых закончится доступ в течении {COUNT_DAYS_OTCHET} {await dney(COUNT_DAYS_OTCHET)}: {count_off_days}'
            )

            await send_message(message.chat.id, text_send)
    except:
        await Print_Error()

@dp.message_handler(commands="buy")
async def buy_message(message=None, is_buy=False, isPodpiska=False, user_id=None, obesh=False, text_send=''):
    try:
        if not user_id:
            user_id = message.chat.id

        user = await user_get(user_id)
        user.isAutoCheckOn = False
        user.isPayChangeProtocol = False
        user.isPayChangeLocations = False
        if user.isBan: return

        if PODPISKA_MODE and not isPodpiska and not is_buy:
            # спросить, клиент хочет купить, взять тестовый ключ или взять вечный ключ по подписке
            klava = InlineKeyboardMarkup()
            isGetTestKey = await DB.isGetTestKey_by_user(user_id)

            test_but = False
            podpiska_but = False

            if not isGetTestKey:
                klava.add(InlineKeyboardButton(text=user.lang.get('tx_podpiska_probn').format(days=COUNT_DAYS_TRIAL, dney_text=await dney(COUNT_DAYS_TRIAL, user)), callback_data=f'buttons:test_key_get'))
                test_but = True
            data = await DB.get_podpiski(isOn=True)
            if data and len(data) > 0:
                klava.add(InlineKeyboardButton(text=user.lang.get('tx_podpiska_sub'), callback_data=f'buttons:buy_isPodpiska'))
                podpiska_but = True
            if not test_but and not podpiska_but:
                is_buy = True
            else:
                klava.add(InlineKeyboardButton(text=user.lang.get('tx_podpiska_buy'), callback_data=f'buttons:buy_isBuy'))
                await send_message(user_id, user.lang.get('tx_podpiska_podkl'), reply_markup=klava)
                return

        if PODPISKA_MODE and isPodpiska:
            user.bot_status = 20
            await select_protocol(user_id)
            return

        if OPLATA or (PODPISKA_MODE and is_buy):
            keys_user = await DB.get_user_keys(user_id)
            if keys_user and len(keys_user) > 0:
                # Если у клиента есть ключ(и)
                try:
                    name = await DB.get_user_nick_and_ustrv(user_id)
                    name = name[2]
                except:
                    name = user.lang.get('tx_no_name')

                klava = InlineKeyboardMarkup()
                if PODPISKA_MODE:
                    klava.add(InlineKeyboardButton(text=user.lang.get('but_create_key'), callback_data=f'buttons:but_create_key'))
                    klava.add(InlineKeyboardButton(text=user.lang.get('but_prodlit_key'), callback_data=f'buttons:but_prodlit_key'))
                else:
                    for item in keys_user:
                        bot_key = item[0]
                        date_start = item[3]
                        CountDaysBuy = int(item[4])
                        ip_server = item[5]
                        try: server_name = [server['location'] for server in SERVERS if server['ip'] == ip_server][0]
                        except: server_name = ''
                        
                        try: date_start = datetime.strptime(date_start, '%Y_%m_%d')
                        except: continue

                        date_now = datetime.now()
                        date_end = date_start + timedelta(days=CountDaysBuy)
                        count_days_to_off = (date_end - date_now).days + 1
                        count_days_to_off = count_days_to_off if count_days_to_off > 0 else 0
                        count_days_to_off_text = f' ({count_days_to_off} {await dney(count_days_to_off, user)})'

                        try: name_bot_key = f'{bot_key.split("_")[2]}'
                        except: 
                            name_bot_key = bot_key.lower().replace(NAME_BOT_CONFIG.lower(), '')
                            if name_bot_key[0] == '_':
                                name_bot_key = name_bot_key.replace('_', '', 1)

                        name_key_for_but = f'🔑{name_bot_key}{count_days_to_off_text} ({server_name})'
                        klava.add(InlineKeyboardButton(text=name_key_for_but, callback_data=f'keys:{user_id}:{bot_key}:prodlit'))

                if not text_send or is_buy:
                    klava.add(InlineKeyboardButton(text=user.lang.get('but_new_key'), callback_data=f'buttons:but_new_key'))

                if obesh:
                    klava.add(InlineKeyboardButton(text=user.lang.get('but_obesh'), callback_data=f'buttons:but_obesh'))

                if text_send:
                    text_send += '\n\n<u>' + user.lang.get('tx_prodlit').format(name=name) + '</u>'
                else:
                    text_send += user.lang.get('tx_buy').format(name=name)

                await send_message(user_id, text_send, reply_markup=klava, no_log=True if text_send else False)
            else:
                # Если у клиента нет ключей
                if not await DB.isGetTestKey_by_user(user_id):
                    probniy = '\n\n' + user.lang.get('tx_buy_probniy').format(days_trial=COUNT_DAYS_TRIAL, dney_text=await dney(COUNT_DAYS_TRIAL, user))
                else:
                    probniy = ''

                await send_message(user_id, user.lang.get('tx_buy_no_keys').format(text_1=probniy, text_2=user.lang.get('tx_prodlt_tarif')), reply_markup=user.klav_buy_days)
    except:
        await Print_Error()

@dp.message_handler(commands="cmd") 
async def cmd_message(message):
    try:
        if await check_test_mode(message.chat.id): return
        user = await user_get(message.chat.id)
        if user.isAdmin:
            m_text = message.text
            m_text = m_text.replace('/cmd', '').strip()
            if m_text != '':
                await AdminCommand(message.chat.id, m_text)
            else:
                text_send1 = '🏷️Пример команды:\n\n/cmd <b>supervisorctl restart bot</b> , где\n    <b>supervisorctl restart bot</b> - команда, для перезагрузки бота на сервере\n\n'
                await send_message(message.chat.id, text_send1)
    except:
        await Print_Error()

@dp.message_handler(commands="price") 
async def set_price_message(message):
    try:
        user_id = message.chat.id
        user = await user_get(user_id)
        if user.isAdmin:
            global TARIF_1
            global TARIF_3
            global TARIF_6
            global TARIF_12

            m_text = message.text.replace('/price', '').strip()
            text_cancel = (
                '🏷️Пример команды: /price <b>3</b> <b>389</b>, где\n'
                '    <b>3</b> - месяцев,\n'
                '    <b>389</b> - рублей\n'
                '    <i>(0 рублей - для того, чтобы не отображать тариф)</i>\n\n'
                f'📋Текущие цены:\n\n'
                f'📅1 мес = <b>{TARIF_1}</b>₽\n'
                f'📅3 мес = <b>{TARIF_3}</b>₽\n'
                f'📅6 мес = <b>{TARIF_6}</b>₽\n'
                f'📅12 мес = <b>{TARIF_12}</b>₽'
            )

            if m_text != '':
                try:
                    if len(m_text.split()) > 1:
                        mouth_id = int(m_text.split()[0])
                        sum = int(m_text.split()[1])

                        if mouth_id == 1:
                            TARIF_1 = sum
                            await DB.UPDATE_VARIABLES('TARIF_1', TARIF_1)
                        elif mouth_id == 3:
                            TARIF_3 = sum
                            await DB.UPDATE_VARIABLES('TARIF_3', TARIF_3)
                        elif mouth_id == 6:
                            TARIF_6 = sum
                            await DB.UPDATE_VARIABLES('TARIF_6', TARIF_6)
                        elif mouth_id == 12:
                            TARIF_12 = sum
                            await DB.UPDATE_VARIABLES('TARIF_12', TARIF_12)

                        if mouth_id in (1,3,6,12):
                            if len(user_dict) > 0:
                                try:
                                    data__ = user_dict.keys()
                                    for id_cl in data__:
                                        await user_dict[id_cl].set_tarifs()
                                except:
                                    pass

                            text_send = (
                                f'✅Цены успешно изменены на:\n\n'
                                f'📅1 мес = <b>{TARIF_1}</b>₽\n'
                                f'📅3 мес = <b>{TARIF_3}</b>₽\n'
                                f'📅6 мес = <b>{TARIF_6}</b>₽\n'
                                f'📅12 мес = <b>{TARIF_12}</b>₽\n'
                            )
                            await send_message(user_id, text_send)
                    else:
                        await send_message(user_id, text_cancel)
                except:
                    await send_message(user_id, f'🛑Не верно переданы параметры для изменения цены!\n\n{text_cancel}')
            else:
                await send_message(user_id, text_cancel)
    except:
        await Print_Error()

@dp.message_handler(commands="partner") 
async def set_partner_message(message):
    try:
        user_id = message.chat.id
        user = await user_get(user_id)

        if user.isAdmin:
            global PARTNER_P
            m_text = message.text.replace('/partner', '').strip()
            primer = '🏷️Пример команды: /partner 30 (<i>где 30 - процент партнерской программы</i>)'

            if m_text != '':
                try:
                    sum = int(m_text)
                    if 1 <= sum <= 100:
                        PARTNER_P = sum

                        await DB.UPDATE_VARIABLES('PARTNER_P', PARTNER_P)

                        await send_message(user_id, f'✅Вы успешно изменили партнерскую программу на: <b>{PARTNER_P}%</b>')
                    else:
                        await send_message(user_id, f'🛑Не верно переданы параметры для изменения парнерской программы (от 1 до 100)!\n{primer}')
                except:
                    await send_message(user_id, f'🛑Не верно переданы параметры для изменения парнерской программы!\n{primer}')
            else:
                text_send = primer + '\n'
                text_send += f'📋Текущая партнерская программа: <b>{PARTNER_P}%</b>'
                await send_message(user_id, text_send)
    except:
        await Print_Error()

@dp.message_handler(commands="summ_vivod") 
async def set_summ_vivod_message(message):
    try:
        user_id = message.chat.id
        user = await user_get(user_id)

        if user.isAdmin:
            global SUMM_VIVOD
            m_text = message.text.replace('/summ_vivod', '').strip()
            primer = '🏷️Пример команды: /summ_vivod 200 (<i>где 200 - минимальная сумма для создания запроса</i>)'

            if m_text != '':
                try:
                    sum = int(m_text)
                    if 1 <= sum:
                        SUMM_VIVOD = sum

                        await DB.UPDATE_VARIABLES('SUMM_VIVOD', SUMM_VIVOD)
                        
                        await send_message(user_id, f'✅Вы успешно изменили минимальную сумму для вывода на: <b>{SUMM_VIVOD}₽</b>')
                    else:
                        await send_message(user_id, f'🛑Не верно переданы параметры для изменения минимальной суммы для вывода (от 1₽)!\n{primer}')
                except:
                    await send_message(user_id, f'🛑Не верно переданы параметры для изменения минимальной суммы для вывода!\n{primer}')
            else:
                text_send = primer + '\n'
                text_send += f'📋Текущая минимальная сумма для вывода: <b>{SUMM_VIVOD}₽</b>'
                await send_message(user_id, text_send)
    except:
        await Print_Error()

@dp.message_handler(commands="summ_change_protocol") 
async def set_summ_change_protocol_message(message):
    try:
        user_id = message.chat.id
        user = await user_get(user_id)

        if user.isAdmin:
            global SUMM_CHANGE_PROTOCOL
            m_text = message.text.replace('/summ_change_protocol', '').strip()
            primer = '🏷️Пример команды: /summ_change_protocol 50 (<i>где 50 - сумма для пожизненной возможности смены протокола</i>)'

            if m_text != '':
                try:
                    sum = int(m_text)
                    if 1 <= sum:
                        SUMM_CHANGE_PROTOCOL = sum
                        await DB.UPDATE_VARIABLES('SUMM_CHANGE_PROTOCOL', SUMM_CHANGE_PROTOCOL)
                        await send_message(user_id, f'✅Вы успешно изменили сумму для пожизненной возможности смены протокола на: <b>{SUMM_CHANGE_PROTOCOL}₽</b>')
                    else:
                        await send_message(user_id, f'🛑Не верно переданы параметры для изменения суммы пожизненной возможности смены протокола (от 1₽)!\n{primer}')
                except:
                    await send_message(user_id, f'🛑Не верно переданы параметры для изменения суммы пожизненной возможности смены протокола!\n{primer}')
            else:
                text_send = primer + '\n'
                text_send += f'📋Текущая сумма для пожизненной возможности смены протокола: <b>{SUMM_CHANGE_PROTOCOL}₽</b>'
                await send_message(user_id, text_send)
    except:
        await Print_Error()

@dp.message_handler(commands="summ_change_locations") 
async def set_summ_change_locations_message(message):
    try:
        user_id = message.chat.id
        user = await user_get(user_id)

        if user.isAdmin:
            global SUMM_CHANGE_LOCATIONS
            m_text = message.text.replace('/summ_change_locations', '')
            primer = '🏷️Пример команды: /summ_change_locations 100 (<i>где 100 - сумма подписки на 1 месяц возможности менять неограниченное кол-во раз локацию</i>)'

            if m_text != '':
                try:
                    sum = int(m_text)
                    if 1 <= sum:
                        SUMM_CHANGE_LOCATIONS = sum
                        await DB.UPDATE_VARIABLES('SUMM_CHANGE_LOCATIONS', SUMM_CHANGE_LOCATIONS)
                        await send_message(user_id, f'✅Вы успешно изменили сумму подписки на 1 месяц возможности менять неограниченное кол-во раз локацию на: <b>{SUMM_CHANGE_LOCATIONS}₽</b>')
                    else:
                        await send_message(user_id, f'🛑Не верно переданы параметры подписки на 1 месяц возможности менять неограниченное кол-во раз локацию (от 1₽)!\n{primer}')
                except:
                    await send_message(user_id, f'🛑Не верно переданы параметры для изменения суммы подписки на 1 месяц возможности менять неограниченное кол-во раз локацию!\n{primer}')
            else:
                text_send = primer + '\n'
                text_send += f'📋Текущая суммы подписки на 1 месяц возможности менять неограниченное кол-во раз локацию: <b>{SUMM_CHANGE_LOCATIONS}₽</b>'
                await send_message(user_id, text_send)
    except:
        await Print_Error()

@dp.message_handler(commands="kurs") 
async def kurs_change_message(message):
    try:
        user_id = message.chat.id
        user = await user_get(user_id)

        if user.isAdmin:
            global KURS_RUB, KURS_RUB_AUTO
            m_text = message.text.replace('/kurs', '').strip()
            primer = '🏷️Пример команды: /kurs 92 (<i>где 92 - курс рубля, если = 0, то автоматически обновляемый каждые 10 минут</i>)'

            if m_text != '':
                try:
                    sum = int(m_text)
                    if 0 <= sum:
                        if sum <= 0:
                            KURS_RUB_AUTO = 1
                            await get_kurs_usdtrub_garantex(repeat=False)
                            await send_message(user_id, f'✅Вы успешно изменили курс рубля на <b>автоматическую загрузку</b>, в данный момент курс: <b>{KURS_RUB}₽</b>')
                        else:
                            KURS_RUB = sum
                            await DB.UPDATE_VARIABLES('KURS_RUB', KURS_RUB)
                            KURS_RUB_AUTO = 0
                            await send_message(user_id, f'✅Вы успешно изменили курс рубля на: <b>{KURS_RUB}₽</b>')
                        await DB.UPDATE_VARIABLES('KURS_RUB_AUTO', KURS_RUB_AUTO)
                    else:
                        await send_message(user_id, f'🛑Не верно переданы параметры курса рубля (от 1₽)!\n{primer}')
                except:
                    await send_message(user_id, f'🛑Не верно переданы параметры для изменения курса рубля!\n{primer}')
            else:
                text_send = primer + '\n'
                text_send += f'📋Текущий курс рубля: <b>{KURS_RUB}₽</b>'
                await send_message(user_id, text_send)
    except:
        await Print_Error()

@dp.message_handler(commands="newpromo") 
async def newpromo_message(message):
    try:
        user_id = message.chat.id
        user = await user_get(user_id)

        if user.isAdmin:
            m_text = message.text.replace('/newpromo', '').strip()
            primer = '🏷️Пример команды: /newpromo <b>782280769</b> <b>500</b> <b>30</b> - Массовое создание промокодов с текстом (допустим для продажи в магазинах ключей), где\n    <b>782280769</b> - id партнера,\n    <b>500</b> - кол-во ключей,\n    <b>30</b> - на какое кол-во дней\n\n'

            if m_text != '':
                try:
                    id_partner = int(m_text.split()[0])
                    count_keys = int(m_text.split()[1])
                    count_days = int(m_text.split()[2])

                    generate = GeneratePromo()
                    await generate.Generate(count_days=count_days, count=count_keys, id_partner=id_partner)
                    await DB.conn.commit()

                    await send_message(user_id, f'✅Вы успешно создали {count_keys} на {count_days} {await dney(count_days)} для партнера id = {id_partner}</b>')
                    await send_message(user_id, f'ℹ️Партнер может скачать их перейдя в Партнерскую программу')

                    # Отправляем файл с текстами и промокодами (если активированы выделяем их)
                    file_name = f'{user_id}_promo.txt'
                    file = await get_urls_partner_file(user_id, file_name)
                    if file:
                        await bot.send_document(user_id, file)
                    try: os.remove(file_name)
                    except: pass
                except:
                    await send_message(user_id, f'{primer}')
            else:
                await send_message(user_id, f'{primer}')
    except:
        await Print_Error()

@dp.message_handler(commands="analytics") 
async def analytics_message(message):
    try:
        user = await user_get(message.chat.id)
        if user.isAdmin:
            data = await DB.getAllReportsData() # CountNewUsers, CountBuy, CountTestKey, SummDay, Date
            date_now = 'Дата выгрузки: ' + datetime.now().strftime("%d.%m.%y %H:%M:%S")

            if not data is None and len(data) > 0:
                temp_massiv = []
                for item in data:
                    CountNewUsers = item[0]
                    CountBuy = item[1]
                    CountTestKey = item[2]
                    SummDay = item[3]
                    date = item[4]
                    try:
                        conversia_buy_new_users = int(CountBuy / CountNewUsers)
                    except:
                        conversia_buy_new_users = 0

                    temp_massiv.append(('Новые пользователи', CountNewUsers, date))
                    temp_massiv.append(('Покупки + промокоды', CountBuy, date))
                    temp_massiv.append(('Выданно тестовых ключей', CountTestKey, date))
                    temp_massiv.append(('Сумма оплат', SummDay, date))
                    temp_massiv.append(('Конверсия (Покупки/Новые.пользов)', conversia_buy_new_users, date))

                send_text_ = '✅Загрузил данные'
                mes_del = await send_message(message.chat.id, send_text_)
                logger.debug('temp_massiv = ' + str(temp_massiv))

                dates = [] # ['18.04.23 17:46', '18.04.23 17:47', '18.04.23 17:49']
                titles = [] # ['🇦🇺', '🇬🇧', '🇺🇸']
                for item in temp_massiv:
                    title = item[0]
                    date = item[2]
                    if not title in titles:
                        titles.append(title)
                    if not date in dates:
                        dates.append(date)

                # Создание данных для графика
                traces = []
                logger.debug('temp_massiv = ' + str(temp_massiv))
                for title in titles:
                    values = []
                    for item1 in temp_massiv:
                        country = item1[0]
                        value = item1[1]

                        if country == title:
                            values.append(value)

                    trace = go.Scatter(x=dates, y=values, mode='lines+markers', name=title)
                    traces.append(trace)

                # Создание раскладки для графика
                layout = go.Layout(title=date_now,
                                    font=dict(size=16), 
                                    xaxis=dict(title='Дата', tickfont=dict(size=12)), 
                                    yaxis=dict(title='Сумма', tickfont=dict(size=12)))

                # Создание фигуры с данными и раскладкой
                fig = go.Figure(data=traces, layout=layout)

                # Сохранение фигуры в виде HTML-файла
                file_name = f'Аналитика_{random.randint(1000,9999)}.html'

                send_text_ += '\n✅Создал график'
                await bot.edit_message_text(send_text_, message.chat.id, mes_del.message_id, parse_mode='HTML')
                logger.debug('Создал график')

                send_text_ += '\n🔄Выгружаю график...'
                await bot.edit_message_text(send_text_, message.chat.id, mes_del.message_id, parse_mode='HTML')
                logger.debug('Выгружаю график...')

                pyo.plot(fig, filename=file_name, auto_open=False)

                await bot.send_document(message.chat.id, open(file_name, 'rb'))
                await delete_message(message.chat.id, mes_del.message_id)
                try: os.remove(file_name)
                except: pass
            else:
                await send_message(message.chat.id, '⚠️Не данных для отображения графика!')
                logger.debug('⚠️Не данных для отображения графика!')
    except:
        await Print_Error()

async def get_text_temp_send_news(index=0, count_users_all=1, count_block=0):
    try:
        text_send = (
            f'📰<b>Публикация новости:</b> {index}/{count_users_all} ({int(index / count_users_all * 100)}%)\n'
            f'❗️Не удалось отправить: <b>{count_block}</b>\n'
        )
        return text_send
    except:
        await Print_Error()
        return '---'

async def send_news(users_ids, news_text, photo_path, isPhoto=False, reply_markup=None, user_id_send_news=None):
    try:
        global count_block_bot, index_user_send_news
        async def send_news_user(user_id, semaphore):
            global count_block_bot, index_user_send_news
            is_return_true = False
            try:
                async with semaphore:
                    try:
                        logger.debug(f'🔄Попытка отправить новость user_id = {user_id}')
                        news_text_temp = await send_promo_tag(news_text)
                        if photo_path != '':
                            if isPhoto:
                                await bot.send_photo(user_id, photo_path, caption=news_text_temp if news_text_temp != '' else None, parse_mode='HTML', reply_markup=reply_markup)
                            else:
                                await bot.send_video(user_id, photo_path, caption=news_text_temp if news_text_temp != '' else None, parse_mode='HTML', reply_markup=reply_markup)
                        elif news_text_temp != '':
                            await bot.send_message(chat_id=user_id, text=news_text_temp, reply_markup=reply_markup, parse_mode='HTML', disable_web_page_preview=True)
                    except Exception as e:
                        if 'bot was blocked' in str(e) or 'user is deactivated' in str(e):
                            # если пользователь заблокировал бота, то прописываем ему в БД что он заблокировал бота
                            logger.warning(f'🛑Пользователь заблокировал бота user_id = {user_id}')
                        else:
                            logger.warning(f'🛑Не удалось отправить новость user_id = {user_id}, ошибка: {e}')
                        is_return_true = False
                    logger.debug(f'✅Успешно отправил user_id = {user_id}')
                    is_return_true = True
            except Exception as e:
                logger.warning(f'🛑Не удалось отправить новость user_id = {user_id}, ошибка: {e}')
                is_return_true = False
                
            index_user_send_news += 1
            if not is_return_true:
                count_block_bot += 1

            await edit_admin_message_news_send(user_id_send_news, count_all_users, count_block_bot, mes_edit, index_user_send_news)

        semaphore = asyncio.Semaphore(18)

        tasks = []
        logger.debug(f'Отправка новости len(users_ids): {len(users_ids)}')
        
        count_all_users = len(users_ids)
        count_block_bot = 0
        index_user_send_news = 0
        
        send_text_ = await get_text_temp_send_news(0, count_all_users, 0)
        mes_edit = await send_message(user_id_send_news, send_text_)

        for user_id in users_ids:
            tasks.append(asyncio.create_task(send_news_user(user_id, semaphore)))
        results = await asyncio.gather(*tasks)

        send_text_ = await get_text_temp_send_news(count_all_users, count_all_users, count_block_bot)
        send_text_ += '\n✅<b>Новость успешно отправлена!</b>'
        await bot.edit_message_text(send_text_, user_id_send_news, mes_edit.message_id, parse_mode='HTML')

        if photo_path != '':
            try: os.remove(photo_path)
            except: pass
    except:
        await Print_Error()

async def edit_admin_message_news_send(user_id_send_news, count_all_users, count_block_bot, mes_edit, index):
    if index % 100 == 0:
        try:
            send_text_ = await get_text_temp_send_news(index, count_all_users, count_block_bot)
            await bot.edit_message_text(send_text_, user_id_send_news, mes_edit.message_id, parse_mode='HTML')
        except Exception as e:
            logger.warning(f'🛑Не удалось отредактировать сообщение user_id_send_news = {user_id_send_news}, ошибка: {e}')

async def fun_klava_news_select(user=None, count_users=-1):
    try:
        klava = InlineKeyboardMarkup()
        smile_select = '✅'
        smile_no_select = '⭕️'

        android = smile_select if user.news_select_android else smile_no_select
        ios = smile_select if user.news_select_ios else smile_no_select
        windows = smile_select if user.news_select_windows else smile_no_select

        activ_keys = smile_select if user.news_select_activ_keys else smile_no_select
        test_keys = smile_select if user.news_select_test_keys else smile_no_select
        yes_pay_no_keys = smile_select if user.news_select_yes_pay_no_keys else smile_no_select
        no_pay_no_keys = smile_select if user.news_select_no_pay_no_keys else smile_no_select
        
        wireguard = smile_select if user.news_select_wireguard else smile_no_select
        vless = smile_select if user.news_select_vless else smile_no_select
        outline = smile_select if user.news_select_outline else smile_no_select
        pptp = smile_select if user.news_select_pptp else smile_no_select

        klava.add(InlineKeyboardButton(text=f'{android}Android', callback_data=f'news_select:android'))
        klava.add(InlineKeyboardButton(text=f'{ios}IOS', callback_data=f'news_select:ios'))
        klava.add(InlineKeyboardButton(text=f'{windows}Windows (MacOS)', callback_data=f'news_select:windows'))

        klava.add(InlineKeyboardButton(text=f'{activ_keys}C активными ключами', callback_data=f'news_select:activ_keys'))
        klava.add(InlineKeyboardButton(text=f'{test_keys}С тестовыми ключами', callback_data=f'news_select:test_keys'))
        klava.add(InlineKeyboardButton(text=f'{yes_pay_no_keys}Были оплаты и нет ключей', callback_data=f'news_select:yes_pay_no_keys'))
        klava.add(InlineKeyboardButton(text=f'{no_pay_no_keys}Без оплат и без ключей', callback_data=f'news_select:no_pay_no_keys'))
        
        klava.add(InlineKeyboardButton(text=f'{wireguard}WireGuard', callback_data=f'news_select:wireguard'))
        klava.add(InlineKeyboardButton(text=f'{vless}VLESS', callback_data=f'news_select:vless'))
        klava.add(InlineKeyboardButton(text=f'{outline}Outline', callback_data=f'news_select:outline'))
        klava.add(InlineKeyboardButton(text=f'{pptp}PPTP', callback_data=f'news_select:pptp'))
        
        for lang in LANG.keys():
            klava.add(InlineKeyboardButton(text=f'{smile_select if user.news_select_lang.get(lang, False) else smile_no_select}{lang}', callback_data=f'news_select:lang_{lang}'))

        if count_users == -1:
            count_users = user.count_users_all

        klava.add(InlineKeyboardButton(text=f'📰Опубликовать ({count_users}/{user.count_users_all}) {int(count_users / user.count_users_all * 100)}% клиентам', callback_data=f'news_select:publish'))
        klava.add(InlineKeyboardButton(text=f'🛑Отменить публикацию', callback_data=f'news_select:delete'))
        return klava
    except:
        await Print_Error()

async def fun_klava_news(news_text, admin_id=None, user=None):
    try:
        if not '<but>' in news_text:
            return None
        
        klava = InlineKeyboardMarkup()
        for item in news_text.split('<but>'):
            if not '</but>' in item:
                continue

            text_but = item.split('</but>')[0]
            if text_but == '':
                continue
            
            title = user.lang.get(text_but, None)
            if title:
                klava.add(InlineKeyboardButton(text=title, callback_data=f'buttons:{text_but}'))
            else:
                if admin_id:
                    await send_message(admin_id, f'🛑Не найдена переменная кнопки: {text_but}, проверьте название переменной в ru.py <- /get_text_file')
        
        return klava
    except:
        await Print_Error()
        return None

async def clear_tag_but(text, user=None):
    try:
        text_temp = text
        if '<but>' in text:
            for item in text.split('<but>'):
                if not '</but>' in item:
                    continue

                text_but = item.split('</but>')[0]
                if text_but == '':
                    continue

                if user.lang.get(text_but, None):
                    text_temp = text_temp.replace(f'<but>{text_but}</but>', '')
        return text_temp.replace('  ',' ')
    except:
        await Print_Error()

async def send_promo_tag(text):
    try:
        generate = GeneratePromo()
        text_temp = text
        if '<promo day="' in text:
            for item in text.split('<promo day="'):
                if not '">' in item:
                    continue

                day = item.split('">')[0]
                if day == '':
                    continue

                if day.isdigit():
                    promo = await generate.Generate(count_days=int(day), count=1)
                    text_temp = text_temp.replace(f'<promo day="{day}">', f'<code>{promo}</code>')
        return text_temp.replace('  ',' ')
    except:
        await Print_Error()      

@dp.message_handler(commands=["news", "news_filter"])
async def news_message(message):
    try:
        user = await user_get(message.chat.id)
        m_text = message.text

        if user.isAdmin:
            temp_news_text = await clear_tag_but(user.news_text, user=user)
            temp_news_text = await send_promo_tag(temp_news_text)
            if 'news_filter' in m_text and (temp_news_text != '' or user.news_photo_path != ''):
                mes_del = await send_message(message.chat.id, '🔄Подсчет клиентов для фильтра...')
                text_send = (
                    'ℹ️Выберите фильтры для публикации:\n\n'
                    '⚠️При активации нескольких фильтров, будут выбраны пользователи, которые подходят хотя бы под один фильтр!\n\n'
                )
                
                all_users_data = await DB.get_all_users_report()
                all_users_keys = await DB.get_user_keys()
                
                # Подсчет клиентов для фильтра
                user.users_ids_news_select = {}
                user.users_ids_news_select['android'] = []
                user.users_ids_news_select['ios'] = []
                user.users_ids_news_select['windows'] = []
                user.users_ids_news_select['activ_keys'] = []
                user.users_ids_news_select['test_keys'] = []
                user.users_ids_news_select['yes_pay_no_keys'] = []
                user.users_ids_news_select['no_pay_no_keys'] = []
                user.users_ids_news_select['wireguard'] = []
                user.users_ids_news_select['vless'] = []
                user.users_ids_news_select['pptp'] = []
                user.users_ids_news_select['outline'] = []
                for lang in LANG:
                    user.users_ids_news_select[lang] = []

                for item in all_users_data:
                    client_id = item[0]
                    summ_user_pay = int(item[5])
                    
                    lang = item[7]
                    if lang in LANG:
                        user.users_ids_news_select[lang].append(client_id)

                    data_keys_user = [key for key in all_users_keys if key[10] == client_id and bool(key[6])]

                    if data_keys_user and len(data_keys_user) > 0 and data_keys_user[0]:
                        for key in data_keys_user:
                            os = key[1]
                            protocol = key[7]

                            if os == 'Android':
                                user.users_ids_news_select['android'].append(client_id)
                            elif os == 'IOS':
                                user.users_ids_news_select['ios'].append(client_id)
                            elif os == 'Windows_MacOS':
                                user.users_ids_news_select['windows'].append(client_id)

                            if protocol == 'wireguard':
                                user.users_ids_news_select['wireguard'].append(client_id)
                            elif protocol == 'vless':
                                user.users_ids_news_select['vless'].append(client_id)
                            elif protocol == 'outline':
                                user.users_ids_news_select['outline'].append(client_id)
                            elif protocol == 'pptp':
                                user.users_ids_news_select['pptp'].append(client_id)

                            count_days = key[4]
                            if not (COUNT_DAYS_TRIAL - 2 <= count_days <= COUNT_DAYS_TRIAL + 2):
                                user.users_ids_news_select['activ_keys'].append(client_id)
                            else:
                                user.users_ids_news_select['test_keys'].append(client_id)
                    else:
                        if summ_user_pay == 0:
                            user.users_ids_news_select['no_pay_no_keys'].append(client_id)
                        else:
                            user.users_ids_news_select['yes_pay_no_keys'].append(client_id)

                temp_m = []
                for item in user.users_ids_news_select.values():
                    temp_m.extend(item)
                user.users_ids = list(set(temp_m))
                
                try:
                    await delete_message(message.chat.id, mes_del.message_id)
                except:
                    pass
                
                user.count_users_all = len(user.users_ids)
                return await send_message(message.chat.id, text_send, reply_markup=await fun_klava_news_select(user))
            elif m_text.replace('/news', '').strip() != '':
                user.news_select_lang = {}
                for lang in LANG.keys():
                    user.news_select_lang[lang] = False
                user.news_text = m_text.replace('/news', '').strip()
                temp_news_text = await clear_tag_but(user.news_text, user=user)
                temp_news_text = await send_promo_tag(temp_news_text)
                if temp_news_text != '':
                    klava = await fun_klava_news(str(user.news_text), message.chat.id, user=user)

                    await send_message(message.chat.id,'Текст новости будет выглядить так:')
                    if user.news_photo_path != '':
                        try:
                            if user.news_is_photo:
                                await bot.send_photo(message.chat.id, user.news_photo_path, caption=temp_news_text if temp_news_text != '' else None, parse_mode='HTML', reply_markup=klava)
                            else:
                                await bot.send_video(message.chat.id, user.news_photo_path, caption=temp_news_text if temp_news_text != '' else None, parse_mode='HTML', reply_markup=klava)
                        except Exception as e:
                            await send_message(message.chat.id, f'🛑Не удалось отправить новость!\n\n⚠️Ошибка:\n{e}')
                    elif temp_news_text != '':
                        await send_message(message.chat.id, temp_news_text, reply_markup=klava)
                    await send_message(message.chat.id,'✅Чтобы перейти к фильтру, нажми: /news_filter')
            else:
                primer = (
                    '❕Для отправки новости необходимо написать по примеру:\n\n'
                    '/news необходимый текст\n\n'
                    '⚠️Также вы можете отправить фото боту (для публикации новости с фото)\n\n'
                    '🆕Возможные теги по тексту:\n\n'
                    '<b>Жирный текст</b>\n'
                    '<i>Курсивный_</i>\n'
                    '<u>Подчеркнутый</u>\n'
                    '<s>Зачеркнутый</s>\n'
                    '<code>Копируемый</code>\n'
                    '<a href="ссылка">Текст ссылки</a>\n\n'
                    '<but>Название переменной кнопки</but> (допустим but_main, найти можно по команде в файле кнопок /get_texts_file)\n\n'
                    '<promo day="7"> (отправить копируемый промокод, каждому клиенту свой, в этом месте текста)'
                )
                return await bot.send_message(message.chat.id, primer, disable_web_page_preview=True)

            if 'news_filter' in m_text and user.news_text == '':
                await send_message(message.chat.id,'⚠️Нет новости для публикации!')
    except:
        await Print_Error()

@dp.message_handler(content_types=["photo", "video"])
async def handle_photo(message):
    try:
        user_id = message.chat.id
        user = await user_get(user_id)
        if user.isBan: return

        if user.isAdmin:
            # Получить информацию о файле
            file_id = message.photo[-1].file_id if message.content_type == "photo" else message.video.file_id

            if not message.reply_to_message is None and not message.reply_to_message.text is None:
                message_reply_data = message.reply_to_message.text
                id_send_reply = None
                text_send_reply = None
                
                for index, stroka in enumerate(message_reply_data.split('\n')):
                    if index == 2:
                        id_send_reply = int(stroka.split(',')[0])
                    if 'Text: ' in stroka:
                        text_send_reply = stroka.replace('Text: ', '')

                if not id_send_reply is None:
                    try:
                        if message.caption:
                            answer_admin = f"{user.lang.get('tx_support_reply')}: <b>{message.caption}</b>"
                            if not text_send_reply is None:
                                message.caption = f"{user.lang.get('tx_support_user_send')}: <b>{text_send_reply}</b>\n{answer_admin}"
                        else:
                            message.caption = user.lang.get('tx_support_reply')

                        if message.content_type == "photo":
                            await bot.send_photo(id_send_reply, file_id, caption=message.caption)
                        else:
                            await bot.send_video(id_send_reply, file_id, caption=message.caption)
                    except:
                        await send_message(message.chat.id, '🛑Не удалось отправить ответ клиенту!')
                        await Print_Error()
                    await send_message(message.chat.id, '✅Ответ на сообщение успешно отправлен клиенту!')
                else:
                    await send_message(message.chat.id, '🛑Не удалось отправить ответ клиенту!')
            else:
                user.news_photo_path = file_id
                user.news_is_photo = message.content_type == "photo"
                await send_message(message.chat.id,'✅Медиафайл для новости загружен')       
    except:
        await Print_Error()

@dp.message_handler(content_types=['document'])
async def handle_document(message):
    try:
        user = await user_get(message.chat.id)

        if user.isAdmin:
            name_file = message.document.file_name
            isConfigFile = 'config' in name_file
            isRuFile = 'lang' in name_file
            isMarkupFile = 'markup' in name_file
            isBotFile = 'bot' in name_file
            date = datetime.now().strftime('%d_%m_%H_%M')

            if isConfigFile:
                if await check_test_mode(message.chat.id): return

            message_ = await send_message(message.chat.id, '🔄Обработка документа...')

            #region Загрузка файла    
            if not isRuFile and not isConfigFile and not isMarkupFile and not isBotFile:
                await delete_message(message.chat.id, message_.message_id)
                return await send_message(message.chat.id, f'🛑Нет такого типа\n\n{e}')

            #region Бекап текущего файла
            if isConfigFile:
                backup_path = CONFIG_FILE.replace('.py', f'_{date}.py')
                os.system(f'cp {CONFIG_FILE} {backup_path}')
            elif isRuFile:
                backup_path = LANG_FILE.replace('.yml', f'_{date}.yml')
                os.system(f'cp {LANG_FILE} {backup_path}')
            elif isMarkupFile:
                backup_path = MARKUP_FILE.replace('.py', f'_{date}.py')
                os.system(f'cp {MARKUP_FILE} {backup_path}')
            elif isBotFile:
                backup_path = BOT_FILE.replace('.py', f'_{date}.py')
                os.system(f'cp {BOT_FILE} {backup_path}')
            #endregion

            try:
                file_info = await bot.get_file(message.document.file_id)
                if isConfigFile:
                    path = CONFIG_FILE
                elif isRuFile:
                    path = LANG_FILE
                elif isMarkupFile:
                    path = MARKUP_FILE
                elif isBotFile:
                    path = BOT_FILE
                await bot.download_file(file_info.file_path, destination=path)

                if isBotFile or isConfigFile or isMarkupFile:
                    # Проверка файла на синтаксические ошибки
                    try:
                        py_compile.compile(path, doraise=True)
                    except py_compile.PyCompileError as e:
                        await delete_message(message.chat.id, message_.message_id)
                        logger.warning(f'🛑Ошибка в синтаксисе файла {path}: {e}')
                        await send_message(message.chat.id, f'🛑Ошибка в синтаксисе файла, возвращаю бекап обратно!')
                        os.system(f'cp {backup_path} {path}') # Восстановление из бекапа
                        return
                elif isRuFile:
                    try:
                        with open(path, 'r') as file:
                            yaml.safe_load(file)
                    except yaml.YAMLError as e:
                        await delete_message(message.chat.id, message_.message_id)
                        logger.warning(f'🛑Ошибка в синтаксисе файла {path}: {e}')
                        await send_message(message.chat.id, f'🛑Ошибка в синтаксисе файла lang.yml, возвращаю бекап обратно!')
                        os.system(f'cp {backup_path} {path}')  # Восстановление из бекапа
                        return

            except Exception as e:
                await delete_message(message.chat.id, message_.message_id)
                return await send_message(message.chat.id, f'🛑Не верный формат файла!\n\n{e}')

            if isConfigFile:
                await send_message(message.chat.id, f'✅Файл config.py обновлен!')
            elif isRuFile:
                await send_message(message.chat.id, f'✅Файл lang.yml обновлен!')
            elif isMarkupFile:
                if INLINE_MODE:
                    await send_message(message.chat.id, f'✅Файл markup_inline.py обновлен!')
                else:
                    await send_message(message.chat.id, f'✅Файл markup.py обновлен!')
            elif isBotFile:
                await send_message(message.chat.id, f'✅Файл bot.py обновлен!')
            await AdminCommand(command='supervisorctl restart bot', sillent=True)
            #endregion
    except:
        await Print_Error()
    finally:
        await delete_message(message.chat.id, message_.message_id)

async def check_pay(bill_id, user, poz, isAdmin=False):
    try:
        user_id = user.id_Telegram

        is_operations_exists = await DB.exists_opertion_by_bill_id(user_id, bill_id)
        if is_operations_exists:
            return None

        if not user.PAY_WALLET:
            await send_admins(user_id, '⚠️Не выбран способ оплаты', '⚠️Либо оплата была вызвана до перезагрузки бота, либо клиент отменил оплату.\n\nСоответственно сейчас не известен способ оплаты (что и где проверять)')
            return None

        RebillId = ''
        if not isAdmin:
            operacia = await user.PAY_WALLET.check_is_pay(user, bill_id)
            is_paid = operacia[0]
            summ = operacia[1]
            desc = operacia[2]
            try:
                RebillId = operacia[3]
            except:
                pass
        else:
            is_paid = True
            desc = 'Подтверждение оплаты администратором'
            if user.isPayChangeProtocol:
                summ = SUMM_CHANGE_PROTOCOL
            elif user.isPayChangeLocations:
                summ = SUMM_CHANGE_LOCATIONS
            elif user.bill_id != '':
                days_plus = await DB.get_user_days_by_buy(user_id)
                if days_plus == 30:
                    summ = user.tarif_1
                elif days_plus == 90:
                    summ = user.tarif_3
                elif days_plus == 180:
                    summ = user.tarif_6
                elif days_plus == 365:
                    summ = user.tarif_12
                else:
                    summ = 0
            else:
                return False

        if is_paid:
            user.isAutoCheckOn = False
            user.paymentDescription = desc
            user.bill_id = ''

            if summ == -1:
                await send_message(user_id, user.lang.get('tx_pay_error'), reply_markup=user.klav_start)
                return None

            if REF_SYSTEM_AFTER_PAY:
                id_ref = await DB.get_user_by_id_ref(user_id)
                if id_ref > 0:
                    await plus_days_ref(user_id, id_ref, help_message=True)

            if len(WALLETS) > 1:
                bottom_text = f'\n💳Счет: <b>{user.PAY_WALLET.Name}</b> ({user.PAY_WALLET.API_Key_TOKEN[:15]})'
            else:
                bottom_text = ''

            if user.message_del_id != None:
                await delete_message(user_id, user.message_del_id)
                user.message_del_id = None

            if user.isPayChangeProtocol:
                user.isPayChangeProtocol = False
                # обновить данные в БД
                await DB.add_operation('change_protocol', user_id, summ, 999, '', '', 'Приобрел возможность навсегда менять неограниченное кол-во раз протокол')
                await DB.update_user_change_protocol(user_id)
                # отправить текст, что все прошло успешно
                # добавить под сообщением кнопку и в обычные кнопки клавиатуру (Смена протокола + в главное меню)
                klava = InlineKeyboardMarkup()
                if COUNT_PROTOCOLS > 1:
                    klava.add(InlineKeyboardButton(text=user.lang.get('but_change_protocol'), callback_data=f'change_protocol:'))
                klava.add(InlineKeyboardButton(text=user.lang.get('but_main'), callback_data=f'buttons:but_main'))

                await send_message(user_id, user.lang.get('tx_pay_protocol_change_yes_1'), reply_markup=await fun_klav_change_protocol(user))
                await send_message(user_id, user.lang.get('tx_pay_protocol_change_yes_2').format(but=user.lang.get('but_change_protocol')), reply_markup=klava)
                if not IS_OTCHET:
                    await send_admins(user_id, '✅Оплата смены протокола', f'Сумма: <b>+{summ}₽</b>{bottom_text}')
                await DB.add_otchet('pay_change_protocol')
            elif user.isPayChangeLocations:
                user.isPayChangeLocations = False
                # обновить данные в БД
                await DB.add_operation('change_location', user_id, 0, 30, '', '', 'Приобрел подписку на 1 месяц возможности менять неограниченное кол-во раз локацию')
                await DB.update_user_change_locations(user_id)
                # отправить текст, что все прошло успешно
                # добавить под сообщением кнопку и в обычные кнопки клавиатуру (Смена локации + в главное меню)
                klava = InlineKeyboardMarkup()
                klava.add(InlineKeyboardButton(text=user.lang.get('but_change_location'), callback_data=f'change_location:'))
                klava.add(InlineKeyboardButton(text=user.lang.get('but_main'), callback_data=f'buttons:but_main'))

                await send_message(user_id, user.lang.get('tx_pay_locations_change_yes_1'), reply_markup=await fun_klav_change_locations(user))
                await send_message(user_id, user.lang.get('tx_pay_locations_change_yes_2').format(but=user.lang.get('but_change_location')), reply_markup=klava)
                if not IS_OTCHET:
                    await send_admins(user_id, '✅Оплата смены локации (на 1 мес.)', f'Сумма: <b>+{summ}₽</b>{bottom_text}')
                await DB.add_otchet('pay_change_locations')
            elif poz != 0:
                await donate_success(user, user_id, poz)
            else:
                days_plus = await DB.get_user_days_by_buy(user_id)
                # проверить, что ключ есть в БД
                if user.bill_bot_key != '':
                    is_key_exists_in_db = await DB.exists_key(user.bill_bot_key)
                    if not is_key_exists_in_db:
                        logger.debug(f'🛑Не удалось продлить ключ, т.к. ключа {user.bill_bot_key} нет в БД, user_id = {user_id}')
                else:
                    is_key_exists_in_db = False

                if is_key_exists_in_db:
                    bot_key = user.bill_bot_key
                    user.bill_bot_key = ''
                    await DB.add_day_qr_key_in_DB(user_id, days_plus, bot_key, summ, bill_id)
                    await add_days(user_id, bot_key, day=days_plus, silent=True)
                    if not IS_OTCHET:
                        await send_admins(user_id, '✅Продление ключа', f'Ключ: <code>{bot_key}</code> (<b>+{summ}₽</b>, +{days_plus} {await dney(days_plus)}, {user.Protocol}){bottom_text}')
                    await DB.add_otchet('prodleny')
                else:
                    await new_key(user_id, day=days_plus, summ=summ, bill_id=bill_id, help_message=True, protocol=user.Protocol, silent=True, RebillId=RebillId)
                    if not IS_OTCHET:
                        await send_admins(user_id, '✅Оплата ключа', f'<b>+{summ}₽</b>, {days_plus} {await dney(days_plus)}, {user.Protocol}{bottom_text}')
                    await DB.add_otchet('get_new_keys')
                await DB.addReportsData('CountBuy', 1)

            await DB.addReportsData('SummDay', summ)
            await DB.addUserSumm(user_id, summ)

            # user = await user_get(user_id, reset=True)
            return True
        else:
            if summ == -1:
                await send_message(user_id, user.lang.get('tx_pay_error'), reply_markup=user.klav_start)
                return None
            return False
    except:
        await Print_Error()
        return False

async def auto_check_pay(user_id, poz, bill_id):
    try:
        user = await user_get(user_id)

        while user.isAutoCheckOn and not (datetime.now() >= user.autoTimerStart + timedelta(minutes=15)):
            result = await check_pay(bill_id, user, poz)

            if result is None:
                return

            if result:
                return
            else:
                await sleep(5)
    except:
        await Print_Error()

async def get_users_reports(user_id, method, is_search=False):
    try:
        user = await user_get(user_id)
        if user.isAdmin:
            mes_del = await send_message(user_id, '🔄Загрузка пользователей...')
            user.clients_report = []
            text_send = 'Ник - id_Telegram - Имя - Фамилия - Откуда\n\n'
            temp_user_id = None
            try: search_text = method.split('::')[1]
            except: search_text = ''
            data = await DB.get_all_users_report(search_text, is_search)
            if len(data) == 1:
                temp_user_id = data[0][0]
            data1 = []

            if method == 'all' or method == 'block':
                data_keys = []
            else:
                data_keys = await DB.get_user_keys(user_id=temp_user_id)

            for item in data:
                if method == 'all':
                    data1.append(item)
                    continue

                if method == 'block':
                    if bool(item[6]):
                        data1.append(item)
                    continue
                
                if method == 'tarifs':
                    if item[8] != '':
                        data1.append(item)
                    continue

                id_client = item[0]

                if 'all::' in method:
                    search_text = method.split('::')[1].lower()
                    nick_yes = search_text in str(item[1]).lower()
                    if nick_yes:
                        data1.append(item)
                        continue
                    id_yes = search_text in str(id_client)
                    if id_yes:
                        data1.append(item)
                        continue
                    name_yes = search_text in str(item[2]).lower() or search_text in str(item[3]).lower()
                    if name_yes:
                        data1.append(item)
                        continue

                if 'all::' in method:
                    key_yes = False
                    if not data_keys is None and len(data_keys) > 0:
                        for key in data_keys:
                            if search_text in key[0].lower() and key[10] == id_client:
                                key_yes = True
                                break

                    if key_yes:
                        data1.append(item)
                    continue

                summ_user_pay = int(item[5])
                data_keys_user = [key for key in data_keys if key[10] == id_client and bool(key[6])]

                if data_keys_user and len(data_keys_user) > 0:
                    test_key_yes = False
                    active_key_yes = False

                    for key in data_keys_user:
                        count_days = key[4]  
                        if not (COUNT_DAYS_TRIAL - 2 <= count_days <= COUNT_DAYS_TRIAL + 2):
                            if not active_key_yes:
                                if method == 'active':
                                    data1.append(item)
                                active_key_yes = True
                        else:
                            if not test_key_yes:
                                if method == 'test':
                                    data1.append(item)
                                test_key_yes = True
                else:
                    if summ_user_pay == 0:
                        if method == 'no_pay_no_keys':
                            data1.append(item)
                    else:
                        if method == 'pay_no_keys':
                            data1.append(item)

            for index, item in enumerate(data1):
                nick =  f'@{item[1]} - ' if not str(item[1]) == 'Nick' else ''

                first_name = f' - {item[2]}' if not item[2] is None else ''
                last_name = f' - {item[3]}' if not item[3] is None else ''
                try:
                    otkuda = f' - {LINK_FROM[item[4]]}' if not item[4] == 0 else ''
                except:
                    otkuda = ''

                if bool(item[6]):
                    nick = f'🚫{nick}'
                    r_tag = '<s>'
                    l_tag = '</s>'
                else:
                    r_tag = ''
                    l_tag = ''

                text_user = f'{r_tag}{index+1}. {nick}{item[0]}{first_name}{last_name}{otkuda}{l_tag}\n'
                text_send += text_user

                user.clients_report.append((index+1, item[0], text_user))

                if index % 49 == 0 and index != 0:
                    await send_message(user_id, text_send)
                    text_send = ''

                if index > 500:
                    text_send += '⚠️Пользователей слишком много, показаны первые 500!'
                    break

            if len(data1) > 0:
                if not text_send == '':
                    user.bot_status = 1
                    if len(data1) == 1:
                        # сразу открыть единственного пользователя
                        await message_input(mes_del, alt_text='1')
                        return await delete_message(user_id, mes_del.message_id)
                    await send_message(user_id, text_send)
                    await send_message(user_id, f'✍️Укажите номер клиента для просмотра его истории сообщений или выполнения действий (/report - назад):')
            else:
                await send_message(user_id, f'⚠️Пользователи по данному запросу не найдены!')
            await delete_message(user_id, mes_del.message_id)
    except:
        await Print_Error()

async def check_promo_is_activ(promo, user_id):
    try:
        try:
            data_ = await DB.get_all_promo_codes()
            for i in data_: # SELECT Code, CountDays, isActivated FROM PromoCodes
                code = i[0]
                # CountDays = int(i[1])
                isActivated = bool(i[2])
                if code in promo:
                    return isActivated
                
            data = await DB.get_activate_individual_promo_code(promo, user_id)
            return data
        except:
            await Print_Error()
        return None
    except:
        await Print_Error()

async def check_user_sub_channels(user_id, id_podpiska, bot_key=None):
    try:
        data = await DB.get_podpiski()
        p_channels_ids = None
        if data and len(data) > 0:
            for paket in data:
                p_id = paket[0]
                if id_podpiska == p_id:
                    p_channels_ids = [item.split(' ')[0] for item in paket[2].split('\n') if item != '']
                    break

        if p_channels_ids:
            for channel_id in p_channels_ids:
                res = await get_user_id_connect_to_channel(channel_id, user_id)
                if not res:
                    return False
            user = await user_get(user_id)
            user.isAutoCheckOn = False
            if user.message_del_id != None:
                # await delete_message(user_id, user.message_del_id)
                user.message_del_id = None

            if bot_key:
                await DB.add_day_qr_key_in_DB(user_id, 1, bot_key, 0, '999999')
                await add_days(user_id, bot_key, day=-1, silent=True)
                if not IS_OTCHET:
                    await send_admins(user_id, 'Ключ активирован (подписался)', f'<code>{bot_key}</code> ({user.Protocol})')
            else:
                await new_key(user_id, day=1000, summ=0, bill_id='999999', help_message=True, protocol=user.Protocol, silent=True, Podpiska=id_podpiska)
                if not IS_OTCHET:
                    await send_admins(user_id, 'Создан ключ по подписке', f'Протокол: <b>{user.Protocol}</b>')
            return True
        else:
            return False
    except:
        await Print_Error()

@dp.callback_query_handler(lambda call: call.data.startswith('off_key:'))
async def off_key_call(call):
    try:
        message = call.message
        user_id = message.chat.id

        key_name = call.data.split(':')[1]
        is_active_key = bool(int(call.data.split(':')[2]))
        date_current = datetime.now().strftime('%Y_%m_%d')
        
        user = await user_get(user_id)
        
        try:
            key_data = await DB.get_key_by_name(key_name) # BOT_Key, Date, User_id, isAdminKey, CountDaysBuy, ip_server, isActive, Protocol, isChangeProtocol, DateChangeProtocol, Payment_id, RebillId, Podpiska
            protocol = key_data[7]
            ip_server = key_data[5]
            date_key = key_data[1]
            CountDaysBuy = key_data[4]
        except:
            return await bot.answer_callback_query(callback_query_id=call.id, show_alert=True, text=user.lang.get('tx_off_key_no_found_key').format(key=key_name))

        day_off = await DB.get_date_off_key(key_name)
        if not is_active_key and not day_off:
            return await send_message(user_id, user.lang.get('tx_no_off_key').format(but=user.lang.get('but_connect')))

        if is_active_key:
            # Если ключ активен, отключаем его и записываем сегодняшнюю дату как дату отключения
            await KEYS_ACTIONS.deactivateKey(protocol, key_name, ip_server, date_key, CountDaysBuy, user_id)
            await DB.On_Off_qr_key(isOn=False, name_bot_key=key_name)
            await DB.set_date_off_key(key_name, date_current)
            await bot.answer_callback_query(callback_query_id=call.id, show_alert=True, text=user.lang.get('tx_off_key_yes').format(key=key_name))
        else:
            # получить разницу кол-во дней между текущим днем и днем отключения
            day = (datetime.now() - datetime.strptime(day_off, '%Y_%m_%d')).days

            await KEYS_ACTIONS.activateKey(protocol, key_name, ip_server, user_id, days=day + CountDaysBuy)
            await DB.set_date_off_key(key_name, '')
            await DB.add_day_qr_key_in_DB(user_id, day, key_name, is_on_key=True)

            await bot.answer_callback_query(callback_query_id=call.id, show_alert=True, text=user.lang.get('tx_on_key_yes').format(key=key_name))

        # отобразить мои активные ключи
        await get_user_keys(user_id)
    except:
        await Print_Error()

@dp.callback_query_handler(lambda call: call.data.startswith('change_language:'))
async def change_language_call(call=None, message=None):
    try:
        if call:
            message = call.message
        user_id = message.chat.id
        user = await user_get(user_id)

        await delete_message(user_id, message.message_id)
        await send_message(user_id, user.lang.get('tx_change_language'), reply_markup=await fun_klav_select_languages(LANG))
    except:
        await Print_Error()

@dp.callback_query_handler(lambda call: call.data.startswith('lang:'))
async def lang_call(call):
    try:
        message = call.message
        user_id = message.chat.id
        lang = call.data.split(':')[1]
        user = await user_get(user_id)

        if not lang in LANG:
            klava = InlineKeyboardMarkup()
            klava.add(InlineKeyboardButton(text=user.lang.get('but_main'), callback_data='buttons:but_main'))
            return await send_message(user_id, user.lang.get('tx_no_language'), reply_markup=klava)

        await delete_message(user_id, message.message_id)
        await DB.set_user_lang(user_id, lang)

        user = await user_get(user_id, reset=True)

        await send_message(user_id, user.lang.get('tx_yes_language'))
        await send_start_message(message)
    except:
        await Print_Error()

@dp.callback_query_handler(lambda call: call.data.startswith('cancel_auto:'))
async def cancel_auto_call(call):
    try:
        message = call.message
        user_id = message.chat.id
        bot_key = call.data.split(':')[1]

        await DB.set_payment_id_by_key(bot_key, '')

        await bot.answer_callback_query(callback_query_id=call.id, show_alert=True, text="✅Автопродление успешно отключено!")
        await delete_message(user_id, message.message_id)
        await get_user_keys(user_id)
    except:
        await Print_Error()

@dp.callback_query_handler(lambda call: call.data.startswith('check_sub:'))
async def check_sub(call=None, id=None, message=None):
    try:
        user_id = int(call.data.split(':')[1])
        user = await user_get(user_id)
        if id is None:
            id = int(call.data.split(':')[2])
        if message is None:
            message = call.message

        try:
            bot_key = call.data.split(':')[3]
        except:
            bot_key = None

        # проверить, чтобы у клиента не было ключа с таким же id подписки
        data = await DB.get_user_keys(user_id) # qr.BOT_Key, qr.OS, qr.isAdminKey, qr.Date, qr.CountDaysBuy, qr.ip_server, qr.isActive, qr.Protocol, sr.Location, qr.Keys_Data, qr.User_id, qr.Podpiska
        if data and len(data) > 0:
            for key in data:
                if key[10] == id:
                    await bot.answer_callback_query(callback_query_id=call.id, show_alert=True, text="⚠️У вас уже есть ключ по данной подписке!")
                    return

        # вызвать проверку, если проверка будет успешная, удалить сообщение и выдать ключ
        result = await check_user_sub_channels(user_id, id, bot_key)
        if result:
            await delete_message(user_id, message.message_id)
        else:
            await bot.answer_callback_query(callback_query_id=call.id, show_alert=True, text="⚠️Вы не подписались на канал создателя ВПН!")
    except:
        await Print_Error()

@dp.callback_query_handler(lambda call: call.data.startswith('podpiska:'))
async def podpiska_call(call=None, id=None, message=None):
    try:
        if id is None:
            id = call.data.split(':')[1]
        if message is None:
            message = call.message
        user_id = message.chat.id
        user = await user_get(user_id)
        if call:
            await delete_message(user_id, message.message_id)

        if call and 'back' in call.data:
            await podpiski_message(message)
            return

        klava = InlineKeyboardMarkup()

        if call and 'add' in call.data:
            but_back = InlineKeyboardButton(text='⏪Назад', callback_data=f'podpiska:back')
            klava.add(but_back)
            await send_message(user_id, '📄Укажите название для пакета:', reply_markup=klava)
            user.bot_status = 13
            return

        if call:
            id = int(id)
            p_name = None
            data = await DB.get_podpiski() # p.id, p.Name, p.Channels, p.isOn, COUNT(q.Podpiska)
            if data and len(data) > 0:
                for paket in data:
                    p_id = paket[0]
                    if p_id == id:
                        p_name = paket[1]
                        p_channels = paket[2]
                        p_isOn = bool(paket[3])
                        p_count = int(paket[4])
                        isOn_smile = '✅' if p_isOn else '🛑'
                        break

        if p_name:
            if call and 'delete' in call.data:                
                await DB.delete_podpisky(id)
                await send_message(user_id, f'✅Пакет подписок <b>{p_name}</b> успешно удален из бота!')
                await podpiski_message(message)
            elif call and ('isOn_yes' in call.data or 'isOn_no' in call.data):
                p_isOn = 'isOn_yes' in call.data
                dop =  'включена' if p_isOn else 'выключена'
                await DB.update_isOn_podpiska(id, p_isOn)
                await send_message(user_id, f'✅В пакете <b>{p_name}</b> успешно <b>{dop}</b> проверка подписок!')
                await podpiska_call(id=id, message=message)
            elif call and 'edit_name' in call.data:
                user.bot_status = 12
                user.keyForChange = id
                await send_message(user_id, f'ℹ️Введите назание пакета подписок <b>{id}</b> <i>(в данный момент <b>{p_name}</b>)</i>:')
            else:
                but = InlineKeyboardButton(text='🪪Изменить название', callback_data=f'podpiska:{id}:edit_name')
                klava.add(but)
                premium_text = '🛑Выключить проверку пакета' if p_isOn else '✅Включить проверку пакета'
                callback_data = 'isOn_no' if p_isOn else 'isOn_yes'
                but = InlineKeyboardButton(text=premium_text, callback_data=f'podpiska:{id}:{callback_data}')
                klava.add(but)
                but = InlineKeyboardButton(text='🛑Удалить пакет', callback_data=f'podpiska:{id}:delete')
                klava.add(but)
                but = InlineKeyboardButton(text='⏪Назад', callback_data=f'podpiska:{id}:back')
                klava.add(but)
                text_send = (
                    f'{isOn_smile}{p_name}\n'
                    f'🔢Кол-во ключей: <b>{p_count}</b>\n'
                    f'👥Проверяемые каналы/группы:\n{p_channels}\n\n'
                    f'ℹ️Выберите необходимое действие:'
                )
                await send_message(user_id, text_send, reply_markup=klava)
        else:
            await send_message(user_id, '⚠️Пакет не был найден!')
    except:
        await Print_Error()

@dp.callback_query_handler(lambda call: call.data.startswith('transfer:'))
async def transfer_call(call):
    try:
        message = call.message
        user_id = message.chat.id
        user = await user_get(user_id)
        await delete_message(user_id, message.message_id)

        if user.isAdmin:
            if 'yes' in call.data:
                if user.keys_for_perenos != [] and user.servers_perenos != []:
                    await transfer_keys(message, user.keys_for_perenos, user.servers_perenos, one='one' in call.data)
                else:
                    await send_message(user_id, '⚠️Нет данных для переноса!')
            elif 'no' in call.data:
                await send_message(user_id, '✅Перенос отменен!')
    except:
        await Print_Error()

@dp.callback_query_handler(lambda call: call.data.startswith('news_select:'))
async def news_select(call):
    try:
        message = call.message
        user_id = message.chat.id
        user = await user_get(user_id)
        isUpdateFilter = False

        if 'delete' in call.data:
            await delete_message(user_id, call.message.message_id)
            user.news_photo_path = ''
            user.news_text = ''
            user.users_ids = []
            await send_message(user_id, '✅Публикация новости успешно отменена!')
        elif 'publish' in call.data:
            if user.news_select_android and user.news_select_ios and user.news_select_windows: # Выбраны все пользователи
                user.users_ids = []
                for item in user.users_ids_news_select.values():
                    user.users_ids.extend(item)
                user.users_ids = list(set(user.users_ids))
            if user.users_ids == []:
                await bot.answer_callback_query(callback_query_id=call.id, show_alert=True, text="⚠️Нет пользователей подходящих по фильтру для отправки новости!")
                return
            await delete_message(user_id, message.message_id)
            await send_message(user_id,'✅Новость отправлена на публикацию!')
            users_ids = [item for item in user.users_ids]

            klava = await fun_klava_news(str(user.news_text), user=user)
            user.news_text = await clear_tag_but(user.news_text, user=user)

            tasks = [asyncio.create_task(send_news(users_ids, f'{user.news_text}', f'{user.news_photo_path}', user.news_is_photo, klava, user_id_send_news=user_id))]
            asyncio.gather(*tasks)
            user.news_photo_path = ''
            user.news_text = ''
            user.users_ids = []
        elif 'android' in call.data:
            user.news_select_android = not user.news_select_android
            isUpdateFilter = True
        elif 'ios' in call.data:
            user.news_select_ios = not user.news_select_ios
            isUpdateFilter = True
        elif 'windows' in call.data:
            user.news_select_windows = not user.news_select_windows
            isUpdateFilter = True
        elif 'activ_keys' in call.data:
            user.news_select_activ_keys = not user.news_select_activ_keys
            isUpdateFilter = True
        elif 'test_keys' in call.data:
            user.news_select_test_keys = not user.news_select_test_keys
            isUpdateFilter = True
        elif 'yes_pay_no_keys' in call.data:
            user.news_select_yes_pay_no_keys = not user.news_select_yes_pay_no_keys
            isUpdateFilter = True
        elif 'no_pay_no_keys' in call.data:
            user.news_select_no_pay_no_keys = not user.news_select_no_pay_no_keys
            isUpdateFilter = True
        elif 'wireguard' in call.data:
            user.news_select_wireguard = not user.news_select_wireguard
            isUpdateFilter = True
        elif 'vless' in call.data:
            user.news_select_vless = not user.news_select_vless
            isUpdateFilter = True
        elif 'outline' in call.data:
            user.news_select_outline = not user.news_select_outline
            isUpdateFilter = True
        elif 'pptp' in call.data:
            user.news_select_pptp = not user.news_select_pptp
            isUpdateFilter = True
        elif 'lang_' in call.data:
            lang = call.data.replace('news_select:lang_', '')
            user.news_select_lang[lang] = not user.news_select_lang.get(lang, False)
            isUpdateFilter = True

        if isUpdateFilter:
            if user.news_select_android and user.news_select_ios and user.news_select_windows: # Выбраны все пользователи
                user.users_ids = []
                for item in user.users_ids_news_select.values():
                    user.users_ids.extend(item)
                user.users_ids = list(set(user.users_ids))
            else:
                # подобрать user_ids по фильтрам
                data1 = []
                
                if user.news_select_android:
                    data1.extend(user.users_ids_news_select['android'])
                if user.news_select_ios:
                    data1.extend(user.users_ids_news_select['ios'])
                if user.news_select_windows:
                    data1.extend(user.users_ids_news_select['windows'])
                if user.news_select_activ_keys:
                    data1.extend(user.users_ids_news_select['activ_keys'])
                if user.news_select_test_keys:
                    data1.extend(user.users_ids_news_select['test_keys'])
                if user.news_select_yes_pay_no_keys:
                    data1.extend(user.users_ids_news_select['yes_pay_no_keys'])
                if user.news_select_no_pay_no_keys:
                    data1.extend(user.users_ids_news_select['no_pay_no_keys'])
                if user.news_select_wireguard:
                    data1.extend(user.users_ids_news_select['wireguard'])
                if user.news_select_vless:
                    data1.extend(user.users_ids_news_select['vless'])
                if user.news_select_outline:
                    data1.extend(user.users_ids_news_select['outline'])
                if user.news_select_pptp:
                    data1.extend(user.users_ids_news_select['pptp'])
                for lang in LANG.keys():
                    if user.news_select_lang.get(lang, False):
                        if lang in user.users_ids_news_select:
                            data1.extend(user.users_ids_news_select[lang])
                    
                user.users_ids = list(set(data1))
            try:
                count_users = len(user.users_ids)
                await bot.edit_message_text(chat_id=user_id, text=message.text, message_id=message.message_id, reply_markup=await fun_klava_news_select(user, count_users=count_users), parse_mode='HTML')
                await bot.answer_callback_query(callback_query_id=call.id, show_alert=False, text="✅Фильтр обновлен!")
            except:
                Print_Error()
        return True
    except:
        await Print_Error()

@dp.callback_query_handler(lambda call: call.data.startswith('web:'))
async def web_call(call):
    try:
        message = call.message
        ip = call.data.split(':')[1]
        user_id = message.chat.id
        await delete_message(user_id, message.message_id)

        klav = InlineKeyboardMarkup()
        but = InlineKeyboardButton(text=f'⏪Назад', callback_data=f'web:{ip}')
        klav.add(but)

        if 'outline' in call.data:
            text = ''
            keys = None
            server = None
            for i in SERVERS:
                if i["ip"] == ip:
                    server = i
                    location = i['location']
                    count_keys = i["count_keys"]
                    keys = await DB.get_keys_name_by_ip_server(ip)
                    count = len([key for key in keys if 'outline' == key[1]]) if not keys is None else 0
                    text += f'🌐{ip} - Ключей: <b>{count}</b> / {count_keys}\n\n(ID - Потраченный трафик - Ключ)\n\n'
                    break

            if count > 0:
                # Получить все ключи
                if server:
                    check_ = await check_server_is_work(server['ip'])
                    if check_:
                        for key in OutlineBOT(server['api_url'], server['cert_sha256']).get_keys():
                            used = round(key.used_bytes / 1000 / 1000 / 1000, 2) if not key.used_bytes is None else 0
                            used = f'{used} GB' if used >= 1 else f'{used * 1000} MB'
                            text += f'<b>{key.key_id} - {used} - </b> <code>{key.name}</code>\n🔐 <code>{key.access_url}#{location} - {NAME_BOT_CONFIG}</code>\n\n'
                    else:
                        text += f'⚠️Сервер не отвечает!'

                if text != '':
                    await send_long_message(user_id, text, reply_markup=klav)
                else:
                    await send_message(user_id, f'⚠️Сервер не был найден!', reply_markup=klav)
            else:
                await send_message(user_id, f'⚠️Ключей Outline не было найдено на данном сервере!', reply_markup=klav)
        elif 'vless' in call.data:
            text = ''
            keys = None
            server = None
            for i in SERVERS:
                if i["ip"] == ip:
                    server = i
                    count_keys = i["count_keys"]
                    keys = await DB.get_keys_name_by_ip_server(ip)
                    count = len([key for key in keys if 'vless' == key[1]]) if not keys is None else 0
                    text += f'🌐{ip} - Ключей: <b>{count}</b> / {count_keys}\n\n(ID - Потраченный трафик - Ключ)\n\n'
                    break

            if count > 0:
                # Получить все ключи
                if server:
                    check_ = await check_server_is_work(server['ip'])
                    if check_:
                        for key in VLESS(server['ip'], server['password']).activ_list():
                            bot_key = key[0]
                            traffic = key[1]
                            url = key[2]
                            used = round(traffic / 1000 / 1000 / 1000, 2)
                            used = f'{used} GB' if used >= 1 else f'{used * 1000} MB'
                            text += f'<b>{used} - </b> <code>{bot_key}</code>\n🔐 <code>{url}</code>\n\n'
                    else:
                        text += f'⚠️Сервер не отвечает!'

                if text != '':
                    await send_long_message(user_id, text, reply_markup=klav)
                else:
                    await send_message(user_id, f'⚠️Сервер не был найден!', reply_markup=klav)
            else:
                await send_message(user_id, f'⚠️Ключей VLESS не было найдено на данном сервере!', reply_markup=klav)
        elif 'back' in call.data:
            return await web_message(message)
        else:
            klav = InlineKeyboardMarkup()
            if PR_VLESS:
                but = InlineKeyboardButton(text=f'🖇️VLESS', callback_data=f'web:{ip}:vless')
                klav.add(but)
            if PR_OUTLINE:
                but = InlineKeyboardButton(text=f'🔗Outline', callback_data=f'web:{ip}:outline')
                klav.add(but)
            but = InlineKeyboardButton(text=f'⏪Назад', callback_data=f'web:back')
            klav.add(but)
            await send_message(user_id, f'ℹ️Выберите протокол:', reply_markup=klav)
        return True
    except:
        await Print_Error()

@dp.callback_query_handler(lambda call: call.data.startswith('servers:'))
async def servers_edit(call=None, ip=None, message=None):
    try:
        if call:
            if await check_test_mode(call.message.chat.id): return
        if ip is None:
            ip = call.data.split(':')[1]
        if message is None:
            message = call.message
        user_id = message.chat.id
        user = await user_get(user_id)
        if call:
            await delete_message(user_id, message.message_id)

        klava = InlineKeyboardMarkup()
        server = None
        for i in SERVERS:
            if i["ip"] == ip:
                server = i
                count_keys = i["count_keys"]
                break

        if server:
            if call and 'reboot' in call.data:
                await send_message(user_id, f'✅Сервер <b>{ip}</b> отправлен на перезагрузку!')
                await reboot_server(server)
            elif call and 'delete' in call.data:
                # проверить, чтобы на сервере не было ключей
                keys = await DB.get_keys_name_by_ip_server(ip)
                count = len(keys) if not keys is None else 0

                if count > 0:
                    temp = count % 10
                    if temp == 0 or temp > 4:
                        cluch = 'ключей'
                    elif temp == 1:
                        cluch = 'ключ'
                    elif 1 < temp < 5:
                        cluch = 'ключа'

                    text = (
                        f'🛑На сервере есть <b>{count}</b> {cluch}, удаление не возможно!\n\n'
                        f'⚠️Для удаления сервера, удалите все ключи из базы данных бота.\n'
                        f'ℹ️Удалить клчючи из базы данных бота можно командой (отправить боту) (коснитесь, чтобы скопировать):\n\n'
                        f'<code>/cmd sqlite3 /root/data/db.db \'DELETE FROM QR_Keys WHERE ip_server="{ip}";\'</code>'
                    )

                    await send_message(user_id, text)
                    await servers_message(message)
                else:
                    await DB.DELETE_SERVER(ip)
                    await send_message(user_id, f'✅Сервер <b>{ip}</b> успешно удален из бота!')
                    await servers_message(message)
            elif call and ('prem_yes' in call.data or 'prem_no' in call.data):
                isPremium = 'prem_yes' in call.data
                dop =  '⭐️Премиальный' if isPremium else '🌎Обычный'
                await DB.SET_SERVER_PREMIUM(ip, isPremium)
                await send_message(user_id, f'✅Сервер <b>{ip}</b> успешно установлен как <b>{dop}</b>!')
                await servers_edit(ip=ip, message=message)
            elif call and 'edit_count_keys' in call.data:
                user.bot_status = 8
                user.keyForChange = ip
                text = (
                    f'ℹ️Введите максимальное кол-во ключей для сервера <b>{ip}</b> <b>(от 1 до 240)</b>:\n'
                    f'﹡Текущее: <code>{count_keys}</code>\n\n'
                    '⚠️При изменение кол-ва меньше, чем есть сейчас на сервере, это никак не затронет текущих пользователей, только для новых ключей.'
                )
                await send_message(user_id, text)
            elif call and 'edit_location' in call.data:
                user.bot_status = 11
                user.keyForChange = ip
                await send_message(user_id, f'ℹ️Введите назание локации для сервера <b>{ip}</b>:\n﹡Текущее: <code>{server["location"]}</code>')
            elif call and 'back' in call.data:
                await servers_message(message)
            else:
                but = InlineKeyboardButton(text='🔄Перезагрузить сервер', callback_data=f'servers:{ip}:reboot')
                klava.add(but)
                but = InlineKeyboardButton(text='🌍Изменить название локации', callback_data=f'servers:{ip}:edit_location')
                klava.add(but)
                but = InlineKeyboardButton(text='🔑Изменить макс. кол-во ключей', callback_data=f'servers:{ip}:edit_count_keys')
                klava.add(but)
                # проверить какой сервер сейчас
                isPremium = server['isPremium']
                premium_text = '⭐️Сделать сервер премиальным' if not isPremium else '🌎Сделать сервер обычным'
                callback_data = 'prem_yes' if not isPremium else 'prem_no'
                but = InlineKeyboardButton(text=premium_text, callback_data=f'servers:{ip}:{callback_data}')
                klava.add(but)
                but = InlineKeyboardButton(text='🛑Удалить сервер из бота', callback_data=f'servers:{ip}:delete')
                klava.add(but)
                but = InlineKeyboardButton(text='⏪Назад', callback_data=f'servers:{ip}:back')
                klava.add(but)

                ip = server['ip']
                password = server['password']
                location = server['location']

                text = f'<b>{location}</b>'
                if server["isPremium"]:
                    text += f' (⭐️Премиальный сервер)'
                if server['is_marzban']:
                    text += f'\n🔒Marzban'
                if server['is_pptp']:
                    text += f'\n🔒PPTP'
                text += '\n\n'

                text += f'🌐IP: <code>{ip}</code>\n'
                text += f'👤Логин: <b>root</b>\n'
                text += f'🔐Пароль: <code>{password}</code>\n'

                keys = await DB.get_keys_name_by_ip_server(ip)
                count = len(keys) if not keys is None else 0
                text += f'🔢Ключей: <b>{count} / {count_keys}</b>\n\n'

                text += 'ℹ️Выберите необходимое действие:'
                await send_message(user_id, text, reply_markup=klava)
        else:
            await send_message(user_id, '⚠️Сервер не был найден!')
    except:
        await Print_Error()

@dp.callback_query_handler(lambda call: call.data.startswith('wallets:'))
async def wallets_call(call=None, id=None, message=None):
    try:
        global user_dict
        if id is None:
            id = int(call.data.split(':')[1])
        if message is None:
            message = call.message
        user_id = message.chat.id
        if call:
            await delete_message(user_id, message.message_id)

        klava = InlineKeyboardMarkup()
        wallet = None
        for item in WALLETS:
            if item["id"] == id:
                wallet = item
                break

        if wallet:
            if call and 'delete' in call.data:
                await DB.DELETE_WALLET(id)
                await send_message(user_id, f'✅Способ оплаты с id <b>{id}</b> успешно удален из бота!')
                await wallets_message(message)
                user_dict = {}
            elif call and ('activ_yes' in call.data or 'activ_no' in call.data):
                isActive = 'activ_yes' in call.data
                dop =  '✅Включен' if isActive else '🛑Отключен'
                await DB.UPDATE_WALLET_IS_ACTIVE(id, isActive)
                await send_message(user_id, f'✅Способ оплаты с id <b>{id}</b> успешно <b>{dop}</b>!')
                await wallets_call(id=id, message=message)
                user_dict = {}
            elif call and 'history' in call.data:
                try:
                    count = int(call.data.split('history_')[1])
                except:
                    count = 30
                text_send = await YPay(id).get_history(count)
                if str(text_send) in ('', 'False'):
                    text_send = 'ℹ️История пуста'
                but = InlineKeyboardButton(text='⏪Назад', callback_data=f'wallets:{id}:baack')
                klava.add(but)
                await send_long_message(user_id, f'{text_send}', reply_markup=klava)
            elif call and 'balance' in call.data:
                balance_y = await YPay(id).get_balance()
                if balance_y >= 0:
                    balance_y = f'💵Ваш баланс {wallet["Name"]}: <b>{balance_y}</b>₽\n\n'
                else:
                    balance_y = f'ℹ️Получить баланс данной платежной системы не представляется возможным!'
                
                but = InlineKeyboardButton(text='⏪Назад', callback_data=f'wallets:{id}:baack')
                klava.add(but)
                await send_message(user_id, f'{balance_y}', reply_markup=klava)
            elif call and 'back' in call.data:
                await wallets_message(message)
            elif call and 'baack' in call.data:
                await wallets_call(id=id, message=message)
            else:
                # проверить какой сервер сейчас
                isActive = wallet['isActive']
                active_text = '🛑Отключить' if isActive else '✅Включить'
                callback_data = 'activ_no' if isActive else 'activ_yes'
                but = InlineKeyboardButton(text=active_text, callback_data=f'wallets:{id}:{callback_data}')
                klava.add(but)
                if not wallet['Name'] in (PAY_METHODS.YOO_KASSA, PAY_METHODS.TINKOFF, PAY_METHODS.CRYPTOMUS):
                    but = InlineKeyboardButton(text='💰Баланс', callback_data=f'wallets:{id}:balance')
                    klava.add(but)
                if not wallet['Name'] in (PAY_METHODS.LAVA, PAY_METHODS.TINKOFF, PAY_METHODS.AAIO):
                    but = InlineKeyboardButton(text='📊Последние 10 платежей', callback_data=f'wallets:{id}:history_10')
                    klava.add(but)
                    but = InlineKeyboardButton(text='📊Последние 50 платежей', callback_data=f'wallets:{id}:history_50')
                    klava.add(but)
                    but = InlineKeyboardButton(text='📊Последние 100 платежей', callback_data=f'wallets:{id}:history_100')
                    klava.add(but)
                but = InlineKeyboardButton(text='🛑Удалить способ оплаты', callback_data=f'wallets:{id}:delete')
                klava.add(but)
                but = InlineKeyboardButton(text='⏪Назад', callback_data=f'wallets:{id}:back')
                klava.add(but)
                await send_message(user_id, 'ℹ️Выберите необходимое действие:', reply_markup=klava)
        else:
            await send_message(user_id, '⚠️Способ оплаты не был найден!')
    except:
        await Print_Error()

@dp.callback_query_handler(lambda call: call.data.startswith('add_wallet:'))
async def add_wallet_call(call):
    try:
        message = call.message
        user_id = message.chat.id
        user = await user_get(user_id)
        klava = InlineKeyboardMarkup(row_width=2)

        if call:
            await delete_message(user_id, message.message_id)

        if not (call.data == 'add_wallet:' or call and 'back' in call.data):
            but_back = InlineKeyboardButton(text='⏪Назад', callback_data=f'add_wallet:')
            klava.add(but_back)

        if call.data == 'add_wallet:':
            but_1 = InlineKeyboardButton(text='💰Ю.Money', callback_data=f'add_wallet:yoomoney')
            but_2 = InlineKeyboardButton(text='💳Ю.Касса', callback_data=f'add_wallet:yookassa')
            but_3 = InlineKeyboardButton(text='💳Tinkoff Pay', callback_data=f'add_wallet:tinkoffpay')
            but_4 = InlineKeyboardButton(text='💰Lava', callback_data=f'add_wallet:lava')
            but_5 = InlineKeyboardButton(text='⚜️Cryptomus', callback_data=f'add_wallet:cryptomus')
            but_6 = InlineKeyboardButton(text='💲Wallet Pay', callback_data=f'add_wallet:walletpay')
            but_7 = InlineKeyboardButton(text='📱Soft Pay', callback_data=f'add_wallet:softpay')
            but_8 = InlineKeyboardButton(text='💳Payok', callback_data=f'add_wallet:payok')
            but_9 = InlineKeyboardButton(text='🪪Aaio', callback_data=f'add_wallet:aaio')
            but_10 = InlineKeyboardButton(text='🌳Root Pay', callback_data=f'add_wallet:rootpay')
            but_11 = InlineKeyboardButton(text='🔗FreeKassa', callback_data=f'add_wallet:freekassa')
            but_12 = InlineKeyboardButton(text='⭐️Stars', callback_data=f'add_wallet:xtr')
            but_13 = InlineKeyboardButton(text='🔗CardLink', callback_data=f'add_wallet:cardlink')
            but_back = InlineKeyboardButton(text='⏪Назад', callback_data=f'add_wallet:back')
            klava.add(but_1, but_2, but_3, but_4, but_5, but_6, but_7, but_8, but_9, but_10, but_11, but_12, but_13).add(but_back)
            await send_message(user_id, 'ℹ️Выберите платежную систему:', reply_markup=klava)
        elif call and 'back' in call.data:
            await wallets_message(message)
        elif call and 'yoomoney' in call.data:
            instruction = (
                '💰Ю.Money (Яндекс.Деньги) (Физ.лицо)\n\n'
                'ℹ️<i>Все действия ниже желательно выполнять компьютере или ноутбуке</i>\n\n'
                '1. Необходимо зарегистрироваться в Ю.Money (https://yoomoney.ru/)\n'
                '2. (<i>необяз.</i>) Далее необходимо получить статус <b>Идентифицированный</b> (https://yoomoney.ru/settings)\n'
                '3. После перейти по ссылке и создать приложение по примеру ниже 👇 (https://yoomoney.ru/myservices/new)\n\n'
                '    <i>== Название бота ==</i>\n'
                '    <i>== Ссылка на бота ==</i>\n'
                '    <i>== Почта == (можно свою, её нигде не будет видно)</i>\n'
                '    <i>== Ссылка на бота ==</i>\n'
                '    <i>== Ссылка на бота ==</i>\n\n'
                f'  <b>⚠️Ссылка на бота все 3 раза должна быть одна и таже, а именно:</b> <code>https://t.me/{BOT_NICK.lower()}</code> (👈коснитесь, чтобы скопировать)\n'
                '  <b>⚠️ГАЛОЧКУ НЕ СТАВИМ, а также загружать логотип не обязательно!</b>\n\n'
                '4. Далее <b>скопируйте</b> Идентификатор приложения <b>CLIENT_ID</b> и <b>отправьте боту</b> (только его значение)\n'
                '5. После следуйте инструкции бота\n'
                '6. Все готово!'
            )
            await send_message(user_id, instruction, reply_markup=klava)
            user.bot_status = 31
        elif call and 'yookassa' in call.data:
            instruction = (
                '💰Ю.Касса (Яндекс.Касса) (ИП или Самозанятый)\n\n'
                '1. Необходимо зарегистрироваться на сайте Ю.Кассы (https://yookassa.ru)\n'
                '2. Перейти в раздел <b>Магазин</b> -> <b>Интеграция</b> -> <b>Ключи API</b> -> <b>Выпустить ключ</b>\n'
                '3. Далее <b>скопируйте ключ</b> (<i>формата live_...</i>) и находясь на этом этапе <b>отправьте его боту</b>\n'
                '4. После следуйте инструкции бота\n'
                '5. Все готово!'
            )
            await send_message(user_id, instruction, reply_markup=klava)
            user.bot_status = 35
        elif call and 'tinkoffpay' in call.data:
            instruction = (
                '💰Tinkoff Pay (ИП или Самозанятый)\n\n'
                '1. Необходимо зарегистрироваться на сайте Tinkoff Pay и подать заявку на регистрацию (https://www.tinkoff.ru/kassa/solution/tinkoffpay/)\n'
                '2. Далее в личном кабинете перейдите в <b>Интернет-эквайринг</b> -> <b>Магазины</b> -> <b>Выберите свой магазин</b> -> <b>Терминалы</b>\n'
                '3. Затем необходимо <b>скопировать номер терминала</b> и находясь на этом этапе <b>отправить его боту</b>\n'
                '4. После необходимо следовать инструкции бота\n'
                '5. Все готово!'
            )
            await send_message(user_id, instruction, reply_markup=klava)
            if PHONE_NUMBER == '':
                await send_message(user_id, "🛑Для того, чтобы пользователи могли оплачивать через Tinkoff Pay, необходимо указать номер телефона в настройках бота (config.py -> PHONE_NUMBER = '79999999999')!")
                return
            user.bot_status = 45
        elif call and 'lava' in call.data:
            instruction = (
                '💰Lava Pay (Физ.лицо)\n\n'
                '1. Необходимо зарегистрироваться на сайте Lava Pay и подать заявку на регистрацию (https://lava.ru)\n'
                '2. Далее необходимо в личном кабинете получить <b>Shop_id, Secret_Key и API_Key</b> при помощи тех.поддержки\n'
                '3. Затем <b>скопируйте API_Key</b> и находясь на этом этапе <b>отправьте его боту</b>\n'
                '4. После следуйте инструкции бота\n'
                '5. Все готово!'
            )
            await send_message(user_id, instruction, reply_markup=klava)
            user.bot_status = 48
        elif call and 'cryptomus' in call.data:
            instruction = (
                '⚜️Cryptomus (Физ.лицо)\n\n'
                '1. Необходимо зарегистрироваться на сайте Cryptomus и подать заявку на регистрацию бота Telegram (https://cryptomus.com)\n'
                '2. Далее после проверки бота необходимо в личном кабинете получить <b>API_Key и Merchant_id</b> при помощи тех.поддержки\n'
                '3. Затем <b>скопируйте API_Key</b> и находясь на этом этапе <b>отправьте его боту</b>\n'
                '4. После следуйте инструкции бота\n'
                '5. Все готово!'
            )
            await send_message(user_id, instruction, reply_markup=klava)
            user.bot_status = 51
        elif call and 'walletpay' in call.data:
            instruction = (
                '💲Wallet Pay (Физ.лицо)\n\n'
                '1. Необходимо зарегистрироваться на сайте Wallet Pay и подать заявку на регистрацию бота Telegram (https://pay.wallet.tg)\n'
                '2. Далее после проверки бота необходимо в личном кабинете получить <b>API ключ</b>\n'
                '3. Затем <b>скопируйте API_Key</b> и находясь на этом этапе <b>отправьте его боту</b>\n'
                '4. Все готово!'
            )
            await send_message(user_id, instruction, reply_markup=klava)
            user.bot_status = 53
        elif call and 'softpay' in call.data:
            instruction = (
                '📱Soft Pay (Физ.лицо)\n\n'
                '1. Необходимо зарегистрироваться на сайте Soft Pay (softpaymoney.com)\n'
                '2. Далее необходимо в личном кабинете получить <b>API ключ</b>\n'
                '3. Затем <b>скопируйте API ключ</b> и находясь на этом этапе <b>отправьте его боту</b>\n'
                '4. После добавления способа оплаты необходимо в конфиг-файле /get_config добавить переменную ID_PRODUCTS_SOFT_PAY, за подробностями к @codenlx\n'
                '5. Все готово!'
            )
            await send_message(user_id, instruction, reply_markup=klava)
            user.bot_status = 54
        elif call and 'payok' in call.data:
            instruction = (
                '💳Payok (Физ.лицо)\n\n'
                '1. Необходимо зарегистрироваться на сайте Payok (payok.io)\n'
                '2. Далее необходимо в личном кабинете получить <b>API ключ</b>\n'
                '3. Затем <b>скопируйте API ключ</b> и находясь на этом этапе <b>отправьте его боту</b>\n'
                '4. Все готово!'
            )
            await send_message(user_id, instruction, reply_markup=klava)
            user.bot_status = 55
        elif call and 'aaio' in call.data:
            instruction = (
                '🪪Aaio (Физ.лицо)\n\n'
                '1. Необходимо зарегистрироваться на сайте Aaio (aaio.so)\n'
                '2. Далее необходимо в личном кабинете получить <b>API ключ</b>\n'
                '3. Затем <b>скопируйте API ключ</b> и находясь на этом этапе <b>отправьте его боту</b>\n'
                '4. Все готово!'
            )
            await send_message(user_id, instruction, reply_markup=klava)
            user.bot_status = 59
        elif call and 'rootpay' in call.data:
            instruction = (
                '🌳Root Pay (Физ.лицо)\n\n'
                '1. Необходимо зарегистрироваться в боте @RootPayRobot)\n'
                '2. Далее необходимо создать проект и получить <b>API ключ</b>\n'
                '3. Затем <b>скопируйте API ключ</b> и находясь на этом этапе <b>отправьте его боту</b>\n'
                '4. Все готово!'
            )
            await send_message(user_id, instruction, reply_markup=klava)
            user.bot_status = 63
        elif call and 'freekassa' in call.data:
            instruction = (
                '🔗FreeKassa (Физ.лицо)\n\n'
                '1. Необходимо зарегистрироваться на сайте FreeKassa (freekassa.com)\n'
                '2. Далее необходимо в личном кабинете получить <b>API ключ</b>\n'
                '3. Затем <b>скопируйте API ключ</b> и находясь на этом этапе <b>отправьте его боту</b>\n'
                '4. Все готово!'
            )
            await send_message(user_id, instruction, reply_markup=klava)
            user.bot_status = 64
        elif call and 'xtr' in call.data:
            instruction = (
                '✅Telegram Stars⭐️ успешно добавлен!'
            )
            await DB.ADD_WALLET(PAY_METHODS.XTR, '-', '', '')
            await send_message(user_id, instruction, reply_markup=klava)
        elif call and 'cardlink' in call.data:
            instruction = (
                '🔗CardLink (Физ.лицо)\n\n'
                '1. Необходимо зарегистрироваться на сайте CardLink (cardlink.link)\n'
                '2. Далее необходимо в личном кабинете получить <b>API ключ</b>\n'
                '3. Затем <b>скопируйте API ключ</b> и находясь на этом этапе <b>отправьте его боту</b>\n'
                '4. Все готово!'
            )
            await send_message(user_id, instruction, reply_markup=klava)
            user.bot_status = 66
        else:
            await send_message(user_id, f'🛑Произошла ошибка при добавлении платежной системы!')
    except:
        await Print_Error()

@dp.callback_query_handler(lambda call: call.data.startswith('zaprosi::'))
async def zaprosi_call(call, no_done=False, menu=False):
    try:
        message = call.message
        user_id = message.chat.id
        await delete_message(user_id, message.message_id)
        no_done = 'no_done' in call.data
        if no_done:
            podtv = False
        else:
            podtv = 'yes' in call.data or 'no' in call.data

        if menu:
            no_done = False
            podtv = False

        if podtv:
            id_zapros = int(call.data.split('::')[1])
            is_podtv_yes = 'yes' in call.data
            podtv_yes = 1 if is_podtv_yes else 2
            await DB.update_zapros(id_zapros, podtv_yes)
            
            if is_podtv_yes:
                zapros = await DB.get_zapros(id_zapros) # id, User_id, Summ, Comment, Status, Dolg
                userForPay = zapros[1]
                summ_opl = zapros[2]
                comment = zapros[3]
                userLastZarabotal = zapros[4] - summ_opl
                await DB.add_parter_pay(userForPay, summ_opl, comment, userLastZarabotal)

            call.data = call.data.split('::')[0]
            await zaprosi_call(call, no_done=True)
            # отправить админу сообщение о том, что запрос одобрен или отклонен
            await bot.answer_callback_query(callback_query_id=call.id, show_alert=True, text=f"✅Запрос с №{id_zapros} и суммой успешно {'одобрен' if is_podtv_yes else 'отклонен'}!")
            podtv = False
            no_done = True

        # вывести все запросы и информацию о них
        data = await DB.get_all_zaprosi() # id, User_id, Summ, Comment, Status
        text_send = ''
        id_zapros = 0
        yes_no_done = False
        if data:
            if no_done:
                text_send = '📝<b>Необработанный запрос:</b>\n\n'
            else:
                text_send = '📝<b>Последние 10 запросов:</b>\n\n'

            data_promo = await DB.get_stats_promoses()
            
            massiv = []
            for index, zapros in enumerate(data):
                id_zapros = zapros[0]
                user_id_zapros = zapros[1]
                summ_zapros = zapros[2]
                comment_zapros = zapros[3]
                status_zapros = zapros[4] # 0 - Wait, 1 - Done, 2 - Cancel
                current_dolg = zapros[5]
                if status_zapros == 0:
                    status = '🔄Ожидает'
                elif status_zapros == 1:
                    status = '✅Выполнен'
                elif status_zapros == 2:
                    status = '🛑Отменен'
                
                code = None
                if data_promo and data_promo[0] and len(data_promo[0]) > 0 and data_promo[0][0]:
                    for i in data_promo:
                        id_partner = i[2]
                        if id_partner == user_id_zapros:
                            code = i[0]

                massiv.append((id_zapros, user_id_zapros, code, summ_zapros, comment_zapros, status, current_dolg))

                if no_done:
                    if status_zapros != 0:
                        continue
                    
                if index >= 10:
                    continue

                yes_no_done = True
                text_send += f'🔢ID: <b>{id_zapros}</b>\n'
                if code:
                    text_send += f'🔗Спец.ссылка: <code>{code}</code> <b>*</b>\n'
                text_send += f'👤ID клиента: <b>{user_id_zapros}</b>\n'
                text_send += f'💰Сумма: <b>{await razryad(summ_zapros)}</b>₽\n'
                text_send += f'📝Комментарий: <b>{comment_zapros}</b>\n'
                text_send += f'🪙Текущий долг партнеру: <b>{await razryad(current_dolg)}</b>₽\n'
                if no_done:
                    if status_zapros == 0:
                        break
                else:
                    text_send += f'📊Статус: <b>{status}</b>\n\n'

            if not no_done:
                name_table = 'Payment_requests.xlsx'
                res = await create_temp_table(name_table, massiv, ['id_Запрос', 'User_id', 'Партнерская ссылка', 'Сумма', 'Комментарий', 'Статус', 'Текущий долг'], ['id_Запрос'])
                if res:
                    await bot.send_document(message.chat.id, open(await get_local_path_data(name_table), 'rb'))
                    # os.remove(name_table)

            text_send += '\n<b>*</b> - <i>Для просмотра данных спец.ссылки, коснитесь ее названия, вставьте и отправьте боту</i>'
            user = await user_get(user_id)
            user.bot_status = 4
        else:
            text_send = '⚠️Запросов на вывод не было найдено!'

        if not yes_no_done and no_done:
            id_zapros = 0

        klava = klava = InlineKeyboardMarkup()
        if not no_done:
            klava.add(InlineKeyboardButton(text=f'🔄Обновить', callback_data=f'zaprosi::'))
            # добавить кнопку необработанные заапросы, если такие имеются
            klava.add(InlineKeyboardButton(text=f'📝Необработанные запросы', callback_data=f'zaprosi::no_done'))
            klava.add(InlineKeyboardButton(text=f'⏪Назад', callback_data=f'buttons:urls_call'))
        else:
            if id_zapros != 0:
                klava.add(InlineKeyboardButton(text=f'✅Подтвердить заявку', callback_data=f'zaprosi::{id_zapros}::yes'))
                klava.add(InlineKeyboardButton(text=f'🛑Отменить заявку', callback_data=f'zaprosi::{id_zapros}::no'))
                klava.add(InlineKeyboardButton(text=f'⏪Назад', callback_data=f'zaprosi::'))
            else:
                await zaprosi_call(call, menu=True)
                return await send_message(user_id, '⚠️Не обработанные заявки не найдены!')
        await send_message(user_id, text_send, reply_markup=klava)
    except:
        await Print_Error()

@dp.callback_query_handler(lambda call: call.data.startswith('user:'))
async def user_info_call(call):
    try:
        message = call.message
        user_id = message.chat.id
        user_info = call.data.split(':')[1]
        
        if await check_test_mode(user_id): return

        await delete_message(user_id, message.message_id)
        result = await show_logs(user_id, int(user_info))
        if not result:
            await send_message(user_id, f'⚠️У данного пользователя нет истории сообщений!')
    except:
        await Print_Error()

@dp.callback_query_handler(lambda call: call.data.startswith('change_protocol:'))
async def change_protocol_call(call):
    try:
        message = call.message
        user_id = message.chat.id
        await delete_message(user_id, message.message_id)
        await get_user_keys(user_id, change_protocol=True)
    except:
        await Print_Error()

@dp.callback_query_handler(lambda call: call.data.startswith('change_location:'))
async def change_location_call(call):
    try:
        message = call.message
        user_id = message.chat.id
        await delete_message(user_id, message.message_id)
        await get_user_keys(user_id, change_location=True)
    except:
        await Print_Error()

@dp.callback_query_handler(lambda call: call.data.startswith('create_partner_url:'))
async def create_partner_url_call(call):
    try:
        message = call.message
        user_id = message.chat.id
        await delete_message(user_id, message.message_id)

        user_data = await DB.get_user_nick_and_ustrv(user_id)
        nick = user_data[0]
        if nick in ('None','Ник',''):
            promo_code = str(user_id)
        else:
            promo_code = nick

        percent_discount = 0
        percent_partner = PARTNER_P

        await create_new_spec_url(user_id, user_id, promo_code, percent_discount, percent_partner, message=message)
    except:
        await Print_Error()

@dp.callback_query_handler(lambda call: call.data.startswith('del_user:'))
async def delete_user_call(call):
    try:
        message = call.message
        user_id = message.chat.id
        user_delete = call.data.split(':')[1]

        if 'yes' in call.data:
            res_ = await DB.exists_user(user_delete)
            if res_:
                await delete_message(user_id, message.message_id)

                send_text_ = '🔄Удаление конфигов на серверах...'
                mes_del = await send_message(message.chat.id, send_text_)
                logger.debug(f'Удаление пользователя {user_delete} и его конфигов')

                lines = await DB.get_qr_key_All(user_delete)
                for line in lines:
                    ip_server = line[5]
                    bot_key = line[0]
                    date = line[1]
                    protocol = line[7]
                    CountDaysBuy = line[4]

                    await KEYS_ACTIONS.deleteKey(protocol, bot_key, ip_server, date, CountDaysBuy, user_delete)

                send_text_ += '✅Удаление конфигов на серверах\n🔄Удаление из Базы Данных...'
                await bot.edit_message_text(send_text_, message.chat.id, mes_del.message_id, parse_mode='HTML')
                logger.debug(f'Удаление пользователя {user_delete} и его конфигов')

                await DB.delete_user_and_configs(user_delete)

                await delete_message(message.chat.id, mes_del.message_id)
                await send_message(user_id, f'✅Пользователь и его конфигурации были успешно удалены (Нажмите /start, если вы удалили себя)!')
                try: user_dict.pop(int(user_delete))
                except: pass
            else:
                await delete_message(user_id, message.message_id)
                await bot.answer_callback_query(callback_query_id=call.id, text='⚠️Данный пользователь не был найден!')

        elif 'no' in call.data:
            await bot.edit_message_text(f'⚠️Пользователь не был удален!', user_id, message.message_id, parse_mode='HTML')
        else:
            klava_buy = InlineKeyboardMarkup()
            but_buy_1 = InlineKeyboardButton(text=f'🛑Да, удалить', callback_data=f'del_user:{user_delete}:yes')
            but_buy_2 = InlineKeyboardButton(text=f'✅Нет', callback_data=f'del_user:{user_delete}:no')
            klava_buy.add(but_buy_1).add(but_buy_2)
            await bot.edit_message_text(f'Вы действительно хотите удалить пользователя c User_id = <b><code>{user_delete}</code></b>?', user_id, message.message_id, reply_markup=klava_buy, parse_mode="HTML")
    except:
        await Print_Error()

@dp.callback_query_handler(lambda call: call.data.startswith('user_change_tarifs:'))
async def user_change_tarifs_call(call):
    try:
        message = call.message
        user_id = message.chat.id
        user_change = int(call.data.split(':')[1])
        
        await delete_message(user_id, message.message_id)

        user_change_data = await user_get(user_change)
        tarif_1 = user_change_data.tarif_1
        tarif_3 = user_change_data.tarif_3
        tarif_6 = user_change_data.tarif_6
        tarif_12 = user_change_data.tarif_12

        text_send = (
            f'ℹ️Укажите индивидуальные тарифы пользователя (в формате 1/3/6/12: <b>{TARIF_1}/{TARIF_3}/{TARIF_6}/{TARIF_12}</b>):\n\n'
            f'💳Текущие тарифы пользователя 1/3/6/12: <code>{tarif_1}/{tarif_3}/{tarif_6}/{tarif_12}</code>\n\n'
            '⚠️Можно скопировать текущие тарифы пользователя коснувшись их.'
        )
        user = await user_get(user_id)
        user.bot_status = 16
        user.user_for_change = user_change
        await send_message(message.chat.id, text_send)
    except:
        await Print_Error()

@dp.callback_query_handler(lambda call: call.data.startswith('ban_user:'))
async def ban_user_call(call):
    try:
        message = call.message
        user_id = message.chat.id
        user_ban = int(call.data.split(':')[1])

        if user_ban == user_id:
            return await send_message(user_id, f'⚠️Вы не можете заблокировать самого себя!')
        
        if user_ban == 782280769:
            await send_message(user_id, f'⚠️А зачем вам это?')
            return await send_message(782280769, f'🛑🛑🛑Пользователь <b>{user_id}</b> попытался заблокировать тебя!🛑🛑🛑')

        if 'yes' in call.data:
            res_ = await DB.exists_user(user_ban)
            if res_:
                await delete_message(user_id, message.message_id)
                
                send_text_ = '🔄Блокировка пользователя...'
                mes_del = await send_message(message.chat.id, send_text_)
                logger.debug(f'Блокировка пользователя {user_ban}')

                await DB.change_ban_user(user_ban, True)

                await delete_message(message.chat.id, mes_del.message_id)
                await send_message(user_id, f'✅Доступ к боту пользователю <b><code>{user_ban}</code></b> был успешно заблокирован!')
                try: user_dict.pop(int(user_ban))
                except: pass
            else:
                await delete_message(user_id, message.message_id)
                await bot.answer_callback_query(callback_query_id=call.id, text='⚠️Данный пользователь не был найден!')

        elif 'no' in call.data:
            await bot.edit_message_text(f'⚠️Пользователь не был заблокирован!', user_id, message.message_id, parse_mode='HTML')
        else:
            klava_buy = InlineKeyboardMarkup()
            but_buy_1 = InlineKeyboardButton(text=f'🛑Да, заблокировать', callback_data=f'ban_user:{user_ban}:yes')
            but_buy_2 = InlineKeyboardButton(text=f'✅Нет', callback_data=f'ban_user:{user_ban}:no')
            klava_buy.add(but_buy_1).add(but_buy_2)
            await bot.edit_message_text(f'Вы действительно хотите заблокировать пользователя c User_id = <b><code>{user_ban}</code></b>?', user_id, message.message_id, reply_markup=klava_buy, parse_mode="HTML")
    except:
        await Print_Error()

@dp.callback_query_handler(lambda call: call.data.startswith('unban_user:'))
async def unban_user_call(call):
    try:
        message = call.message
        user_id = message.chat.id
        user_unban = call.data.split(':')[1]

        if 'yes' in call.data:
            res_ = await DB.exists_user(user_unban)
            if res_:
                await delete_message(user_id, message.message_id)

                send_text_ = '🔄Разблокировка пользователя...'
                mes_del = await send_message(message.chat.id, send_text_)
                logger.debug(f'Разблокировка пользователя {user_unban}')

                await DB.change_ban_user(user_unban, False)

                await delete_message(message.chat.id, mes_del.message_id)
                await send_message(user_id, f'✅Доступ к боту пользователю <b><code>{user_unban}</code></b> был успешно разблокирован!')
                try: user_dict.pop(int(user_unban))
                except: pass
            else:
                await delete_message(user_id, message.message_id)
                await bot.answer_callback_query(callback_query_id=call.id, text='⚠️Данный пользователь не был найден!')

        elif 'no' in call.data:
            await bot.edit_message_text(f'⚠️Пользователь не был разблокирован!', user_id, message.message_id, parse_mode='HTML')
        else:
            klava_buy = InlineKeyboardMarkup() 
            but_buy_1 = InlineKeyboardButton(text=f'✅Да, разблокировать', callback_data=f'unban_user:{user_unban}:yes')
            but_buy_2 = InlineKeyboardButton(text=f'🛑Нет', callback_data=f'unban_user:{user_unban}:no')
            klava_buy.add(but_buy_1).add(but_buy_2)
            await bot.edit_message_text(f'Вы действительно хотите разблокировать пользователя c User_id = <b><code>{user_unban}</code></b>?', user_id, message.message_id, reply_markup=klava_buy, parse_mode="HTML")
    except:
        await Print_Error()

@dp.callback_query_handler(lambda call: call.data.startswith('check:'))
async def check_payment_call(call):
    try:
        user_id = int(call.data.split(':')[1])
        bill_id = call.data.split(':')[2]
        isAdminConfirm = 'admin' in call.data
        user = await user_get(user_id)

        poz = 0
        if 'poz' in call.data:
            poz = int(call.data.split('poz')[1])

        if isAdminConfirm:
            mes_wait = await send_message(call.message.chat.id, '🔄Попытка подтвердить оплату...')

        error_text = f'⚠️Оплата bill_id = {bill_id} уже была подтверждена или отменена!'

        client = await user_get(user_id)
        if client.bill_id != bill_id:
            return await send_message(call.message.chat.id if isAdminConfirm else user_id, error_text)

        result = await check_pay(bill_id, user, poz, isAdmin=isAdminConfirm)         

        if result:
            if isAdminConfirm:
                await delete_message(call.message.chat.id, mes_wait.message_id)
                klava_admin = InlineKeyboardMarkup()
                klava_admin.add(InlineKeyboardButton(text=f'✅Оплата успешно подтверждена!', callback_data=f':::'))
                await bot.edit_message_text(chat_id=call.message.chat.id, text=call.message.text, message_id=call.message.message_id, reply_markup=klava_admin, parse_mode='HTML')
                try:
                    await bot.answer_callback_query(callback_query_id=call.id, text='✅Оплата была успешно подтверждена!')
                except:
                    await send_message(call.message.chat.id, '✅Оплата была успешно подтверждена!')
                return

            # Удалить сообщение у клиента
            try:
                await delete_message(call.message.chat.id, call.message.message_id)
            except:
                pass
        else:
            if isAdminConfirm:
                try:
                    await delete_message(call.message.chat.id, mes_wait.message_id)
                    klava_admin = InlineKeyboardMarkup()
                    klava_admin.add(InlineKeyboardButton(text=error_text, callback_data=f':::'))
                    await bot.edit_message_text(chat_id=call.message.chat.id, text=call.message.text, message_id=call.message.message_id, reply_markup=klava_admin, parse_mode='HTML')
                    await bot.answer_callback_query(callback_query_id=call.id, text=error_text, show_alert=True)
                except:
                    await send_message(call.message.chat.id, error_text)
            else:
                try:
                    await bot.answer_callback_query(callback_query_id=call.id, text=user.lang.get('tx_check_pay_no').format(bill_id=bill_id), show_alert=True)
                except:
                    await send_message(call.message.chat.id, user.lang.get('tx_check_pay_no').format(bill_id=bill_id))
    except:
        await Print_Error()

@dp.callback_query_handler(lambda call: call.data.startswith('keys:'))
async def keys_get_call(call=None, message=None, call_data=None):
    try:
        if not message:
            message = call.message
        user_send = message.chat.id

        if not call_data:
            call_data = call.data
        
        user_id = int(call_data.split(':')[1])
        logger.debug(f'{user_id} - Зашел в функцию загрузки ключей')
        bot_key = call_data.split(':')[2]
        yes = False
        user = await user_get(user_id)

        logger.debug(f'{user_id} - Получил данные из call_data={call_data}')
        if 'delete' in call_data:
            logger.debug(f'{user_id} - Удаляю ключ {bot_key}')
            await delete_message(user_send, message.message_id)
            lines = await DB.get_qr_key_All(user_id) # BOT_Key, Date, User_id, isAdminKey, CountDaysBuy, ip_server, isActive 
            for line in lines:
                ip_server = line[5]
                bot_key1 = line[0]
                protocol = line[7]
                date_key = line[1]
                CountDaysBuy = line[4]

                if bot_key == bot_key1:
                    await KEYS_ACTIONS.deleteKey(protocol, bot_key, ip_server, date_key, CountDaysBuy, user_id)
                    break

            await DB.delete_qr_key(bot_key)
            await send_message(user_send, f'✅Ключ <code>{bot_key}</code> пользователя <code>{user_id}</code> успешно удален!')

        if 'ch_pr' in call_data:
            if 'wireguard' in call_data or 'vless' in call_data or 'outline' in call_data or 'pptp' in call_data:
                logger.debug(f'{user_id} - Изменяю протокол ключа {bot_key}')
                await delete_message(user_id, message.message_id)

                # удалить ключ на сервере и в БД
                ip_server = None
                protocol = None
                CountDaysBuy = None
                date = None
                Podpiska = None

                mes_del_ = await send_message(user_id, user.lang.get('tx_change_protocol_wait'))

                lines = await DB.get_qr_key_All(user_id) # BOT_Key, Date, User_id, isAdminKey, CountDaysBuy, ip_server, isActive, protocol
                user_isPayChangeProtocol = await DB.get_user_is_pay_change_protocol(user_id)

                for line in lines:
                    ip_server = line[5]
                    bot_key1 = line[0]
                    protocol = line[7]
                    date = line[1]
                    CountDaysBuy = line[4]
                    DateChangeProtocol = line[9]
                    Podpiska = line[12]
                    summ_tarif = line[14]

                    if PAY_CHANGE_PROTOCOL:
                        if not user_isPayChangeProtocol:
                            if not DateChangeProtocol is None:
                                if '.' in DateChangeProtocol:
                                    date_time = datetime.strptime(DateChangeProtocol, "%Y-%m-%d %H:%M:%S.%f")
                                else:
                                    date_time = datetime.strptime(DateChangeProtocol, "%Y-%m-%d %H:%M:%S")
                                now = datetime.now()
                                usl = (now - date_time) > timedelta(days=7)
                            else:
                                usl = True
                        else:
                            usl = True

                        if not usl:
                            # проверить оплачена ли пожизненная смена протокола у клиента
                            await delete_message(user_id, mes_del_.message_id)
                            # написать сообщение, что смена протокола возможна 1 раз в 7 дней
                            summ = SUMM_CHANGE_PROTOCOL
                            if user.lang_select != 'Русский':
                                summ = round(SUMM_CHANGE_PROTOCOL / KURS_RUB, 2)
                            return await send_message(user_id, user.lang.get('tx_no_change_protocol_days').format(but=user.lang.get('but_pay_change_protocol'), valuta=user.valuta, summ=summ), reply_markup=await fun_klav_pay_change_protocol(user))

                    if bot_key == bot_key1:
                        await KEYS_ACTIONS.deleteKey(protocol, bot_key, ip_server, date, CountDaysBuy, user_id)
                        break

                if ip_server and protocol and CountDaysBuy and date:
                    await DB.delete_qr_key(bot_key)
                    await delete_message(user_id, mes_del_.message_id)

                    # создать новый ключ на этом же сервере в противоположном протоколе
                    if 'wireguard' in call_data:
                        protocol = 'wireguard'
                    elif 'vless' in call_data:
                        protocol = 'vless'
                    elif 'outline' in call_data:
                        protocol = 'outline'
                    elif 'pptp' in call_data:
                        protocol = 'pptp'
                    await new_key(user_id, day=CountDaysBuy, help_message=True, protocol=protocol, date=date, ip_server=ip_server, Podpiska=Podpiska, summ_tarif=summ_tarif)
                else:
                    await delete_message(user_id, mes_del_.message_id)
                    await send_message(user_send, user.lang.get('tx_no_find_key').format(key=bot_key))
                    logger.warning(f'{user_id} - Не найден ключ 3')
            else:
                logger.debug(f'{user_id} - Зашел в меню выбора протокола ключа {bot_key}')
                await delete_message(user_id, message.message_id)

                # отобразить выбор доступных протоколов
                klava = InlineKeyboardMarkup()
                protocol = await DB.get_Protocol_by_key_name(bot_key)
                if PR_WIREGUARD and protocol != 'wireguard':
                    klava.add(InlineKeyboardButton(text=user.lang.get('but_select_WG'), callback_data=f'keys:{user_id}:{bot_key}:ch_pr:wireguard'))
                if PR_VLESS and protocol != 'vless':
                    klava.add(InlineKeyboardButton(text=user.lang.get('but_select_vless'), callback_data=f'keys:{user_id}:{bot_key}:ch_pr:vless'))
                if PR_OUTLINE and protocol != 'outline':
                    klava.add(InlineKeyboardButton(text=user.lang.get('but_select_Outline'), callback_data=f'keys:{user_id}:{bot_key}:ch_pr:outline'))
                if PR_PPTP and protocol != 'pptp':
                    klava.add(InlineKeyboardButton(text=user.lang.get('but_select_pptp'), callback_data=f'keys:{user_id}:{bot_key}:ch_pr:pptp'))
                klava.add(InlineKeyboardButton(text=user.lang.get('but_main'), callback_data=f'buttons:but_main'))

                tx_description_protocols = ''
                if PR_VLESS:
                    tx_description_protocols += user.lang.get('tx_desc_vless')
                if PR_WIREGUARD:
                    tx_description_protocols += user.lang.get('tx_desc_wireguard')
                if PR_OUTLINE:
                    tx_description_protocols += user.lang.get('tx_desc_outline')
                if PR_PPTP:
                    tx_description_protocols += user.lang.get('tx_desc_pptp')
                await send_message(user_id, user.lang.get('tx_select_protocol').format(text=tx_description_protocols), reply_markup=klava)
            return

        if 'ch_loc' in call_data:
            # проверить при смене серверов, если оплачено и прошло меньше или равно 30 дней, то пропускать дальше, даже если менял локации больше 3 раз за последние 24 часа
            usl = False
            if PAY_CHANGE_LOCATIONS:
                datePayChangeLocations = await DB.get_user_is_pay_change_locations(user_id)

                if not datePayChangeLocations is None:
                    # провериь, прошло ли 30 дней с момента оплаты
                    if '.' in datePayChangeLocations:
                        date_time = datetime.strptime(datePayChangeLocations, "%Y-%m-%d %H:%M:%S.%f")
                    else:
                        date_time = datetime.strptime(datePayChangeLocations, "%Y-%m-%d %H:%M:%S")
                    now = datetime.now()
                    usl = (now - date_time) <= timedelta(days=30)
                else:
                    usl = False

                if not usl:
                    user_operations_data = await DB.get_user_operations(user_id=user_id)
                    count_change_location_on_day = 0
                    for operation in user_operations_data:
                        if operation[1] == 'change_location':
                            date_time = operation[7]
                            if '.' in date_time:
                                date_time = datetime.strptime(date_time, "%Y-%m-%d %H:%M:%S.%f")
                            else:
                                date_time = datetime.strptime(date_time, "%Y-%m-%d %H:%M:%S")
                            now = datetime.now()
                            if (now - date_time) <= timedelta(days=3):
                                count_change_location_on_day += 1
                                logger.debug(f'{user_id} - Сменил локацию за последние 3 дня!')

                    if count_change_location_on_day >= 1:
                        logger.debug(f'{user_id} - Сменил локацию за последние 3 дня!')
                        await delete_message(user_id, message.message_id)
                        # написать сообщение, что смена локации возможна 1 раз в в 3 дня или платите SUMM_CHANGE_LOCATIONS
                        klava = InlineKeyboardMarkup()
                        klava.add(InlineKeyboardButton(text=user.lang.get('but_pay_change_locations'), callback_data=f'change_location:'))
                        klava.add(InlineKeyboardButton(text=user.lang.get('but_main'), callback_data=f'buttons:but_main'))
                        summ = SUMM_CHANGE_LOCATIONS
                        if user.lang_select != 'Русский':
                            summ = round(SUMM_CHANGE_LOCATIONS / KURS_RUB, 2)
                        return await send_message(user_id, user.lang.get('tx_no_change_locations_days').format(but=user.lang.get('but_pay_change_locations'), valuta=user.valuta, summ=summ), reply_markup=await fun_klav_pay_change_locations(user))
            else:
                usl = True

            try:
                select_server_index = int(call_data.split(':')[4])
            except:
                select_server_index = -1
            isSelect = select_server_index != -1
            if isSelect:
                logger.debug(f'{user_id} - Изменяю локацию ключа {bot_key}')
            else:
                logger.debug(f'{user_id} - Зашел в меню выбора локации ключа {bot_key}')
            # отобразить выбор доступных локаций
            # Сервера группируются по названиям (соотвественно, если к примеру есть 2 сервера названые «🇩🇪Германия», то у клиента будет отображаться как выбор «🇩🇪Германия»)
            
            if not isSelect:
                await delete_message(user_id, message.message_id)
                servers_locations = []
                premium_locations = []
                servers_count_keys_for_locations = {}
                for server in SERVERS:
                    _location = server['location']
                    count_keys_by_ip = await DB.get_count_keys_by_ip(server['ip'])
                    servers_locations.append(_location)

                    if _location in servers_count_keys_for_locations:
                        servers_count_keys_for_locations[_location]['current'] += count_keys_by_ip
                        servers_count_keys_for_locations[_location]['max'] += server['count_keys']
                    else:
                        servers_count_keys_for_locations[_location] = {'current':count_keys_by_ip, 'max':server['count_keys']}

                    if server['isPremium']:
                        premium_locations.append(_location)
                servers_locations = list(set(servers_locations))
                premium_locations = list(set(premium_locations))

                user.locations = servers_locations

                # берем текущую локацию
                old_location = ''
                user_keys = await DB.get_user_keys(user_id) # qr.BOT_Key, qr.OS, qr.isAdminKey, qr.Date, qr.CountDaysBuy, qr.ip_server, qr.isActive, qr.Protocol, sr.Location
                logger.debug(f'{user_id} - Ключи пользователя {user_keys}')
                for user_key in user_keys:
                    if user_key[0] == bot_key:
                        old_ip_server = user_key[5]
                        old_location = user_key[8]
                        break

                klava = InlineKeyboardMarkup()
                for index, location in enumerate(servers_locations):
                    # если у пользователя нет доступа к серверам с премиум локациями, то не показывать их в кнопках, но показать в тексте
                    if not usl and location in premium_locations and PAY_CHANGE_LOCATIONS:
                        continue

                    if location == old_location:
                        text_ddd = f" ({user.lang.get('tx_change_location_current')})"
                    else:
                        text_ddd = ''
                    isPremium = user.lang.get('tx_change_location_premium_smile') if location in premium_locations else ''

                    if servers_count_keys_for_locations[location]['current'] < servers_count_keys_for_locations[location]['max']:
                        but_key = InlineKeyboardButton(text=f'{isPremium}{location}{text_ddd}', callback_data=f'keys:{user_id}:{bot_key}:ch_loc:{index}')
                    else:
                        but_key = InlineKeyboardButton(text=f"{isPremium}{location}{text_ddd} ({user.lang.get('tx_change_location_limit')})", callback_data=f':::')
                    klava.add(but_key)

                # Указать локации, которые доступны для смены, также написать перед ними "⭐️" если он премиальный
                text_servers = f"\n{user.lang.get('tx_change_location_list')}\n"
                for location in servers_locations:
                    if location == old_location:
                        text_ddd = f" ({user.lang.get('tx_change_location_current')})"
                    else:
                        text_ddd = ''
                    isPremium = user.lang.get('tx_change_location_premium_smile') if location in premium_locations else ''
                    if not usl and location in premium_locations and PAY_CHANGE_LOCATIONS:
                        tag_1 = '<s>'
                        tag_2 = '</s>'
                    else:
                        tag_1 = ''
                        tag_2 = ''
                    text_servers += f'{tag_1}{isPremium}{location}{text_ddd}{tag_2}\n'
                if PAY_CHANGE_LOCATIONS:
                    text_servers += '\n' + user.lang.get('tx_change_location_premium_smile') + ' ' + user.lang.get('tx_change_location_premium_desc')

                await send_message(user_id, user.lang.get('tx_select_location').format(text=text_servers), reply_markup=klava)
                if not usl and PAY_CHANGE_LOCATIONS:
                    summ = SUMM_CHANGE_LOCATIONS
                    if user.lang_select != 'Русский':
                        summ = round(SUMM_CHANGE_LOCATIONS / KURS_RUB, 2)
                    await send_message(user_id, user.lang.get('tx_select_location_no_premium').format(but=user.lang.get('but_pay_change_locations'), valuta=user.valuta, summ=summ), reply_markup=await fun_klav_pay_change_locations(user))
            else:
                location = None
                for index, location in enumerate(user.locations):
                    if index == select_server_index:
                        location = user.locations[index]
                        break

                if location:
                    logger.debug(f'{user_id} - Выбрана локация {location}')
                    old_ip_server = None
                    ip_server = None
                    select_location_is_old = False
                    user_keys = await DB.get_user_keys(user_id) # qr.BOT_Key, qr.OS, qr.isAdminKey, qr.Date, qr.CountDaysBuy, qr.ip_server, qr.isActive, qr.Protocol, sr.Location
                    
                    logger.debug(f'{user_id} - Ключи пользователя {user_keys}')
                    for user_key in user_keys:
                        if user_key[0] == bot_key:
                            old_ip_server = user_key[5]
                            old_location = user_key[8]
                            # проверить, пользователь выбрал такую же локацию, как у него сейчас или другую
                            if old_location == location:
                                select_location_is_old = True
                            break
                    
                    logger.debug(f'{user_id} - Старый ip сервера {old_ip_server}')
                    for server in SERVERS:
                        # если выбрана таже локация, что и сейчас у пользователя, сменить на другой сервер с этой локацией
                        if server['location'] == location:
                            if select_location_is_old:
                                if old_ip_server and server['ip'] == old_ip_server:
                                    continue
                            # Проверяем, что на сервере достаточно места
                            count_users_in_server = await DB.get_count_keys_by_ip(server['ip'])
                            logger.debug(f'{user_id} - Кол-во пользователей на сервере {server["ip"]} = {count_users_in_server}')
                            if count_users_in_server < server['count_keys']:
                                logger.debug(f'{user_id} - Локации не равны {server["location"]} != {location}')
                                ip_server = server['ip']
                                break
                            else:
                                logger.debug(f'{user_id} - Нет места на сервере {server["ip"]}, ищем другой сервер')
                                ip_server = server['ip']
                    
                    # проверить, чтобы мы меняли не на такой же сервер
                    if ip_server is None:
                        if call:
                            await bot.answer_callback_query(callback_query_id=call.id, text=user.lang.get('tx_key_server_location_is_one'), show_alert=True)
                        return
                    else:
                        await delete_message(user_id, message.message_id)
                    
                    logger.debug(f'{user_id} - Новый ip сервера {ip_server}')
                    if ip_server:
                        # удалить ключ на сервере и в БД
                        protocol = None
                        CountDaysBuy = None
                        date = None

                        mes_del_ = await send_message(user_id, user.lang.get('tx_change_location_wait'))

                        lines = await DB.get_qr_key_All(user_id)
                        for line in lines:
                            ip_server_ = line[5]
                            bot_key1 = line[0]
                            protocol = line[7]
                            date = line[1]
                            CountDaysBuy = line[4]
                            Podpiska = line[12]
                            summ_tarif = line[14]

                            if bot_key == bot_key1:
                                await KEYS_ACTIONS.deleteKey(protocol, bot_key, ip_server_, date, CountDaysBuy, user_id)
                                break
                        
                        if ip_server and protocol and CountDaysBuy and date:
                            await DB.delete_qr_key(bot_key)
                            await delete_message(user_id, mes_del_.message_id)
                            await new_key(user_id, day=CountDaysBuy, help_message=True, protocol=protocol, date=date, ip_server=ip_server, isChangeLocation=True, Podpiska=Podpiska, summ_tarif=summ_tarif)
                        else:
                            await delete_message(user_id, mes_del_.message_id)
                            await send_message(user_send, user.lang.get('tx_no_find_key').format(key=bot_key))
                            logger.warning(f'{user_id} - Не найден ключ 1')
                    else:
                        await send_message(user_send, user.lang.get('tx_no_find_key').format(key=bot_key))
                        logger.debug(f'{user_id} - Не найден ключ {bot_key}')
                user.locations = []
            return

        if 'change_summ' in call_data:
            logger.debug(f'{user_id} - Изменяю сумму следующего списания {bot_key}')
            await delete_message(user_send, message.message_id)
            current_user = await user_get(user_send)
            current_user.bot_status = 15
            current_user.keyForChange = bot_key
            summ = await DB.get_summ_next_pay(bot_key)
            await send_message(user_send, f'ℹ️Введите сумму следующего списания для ключа <code><b>{bot_key}</b></code> пользователя <code><b>{user_id}</b></code>:\n\n💳Текущая сумма: <b>{summ}₽</b>')
            return

        if 'change' in call_data:
            logger.debug(f'{user_id} - Изменяю дни ключа {bot_key}')
            await delete_message(user_send, message.message_id)
            current_user = await user_get(user_send)
            current_user.bot_status = 3
            current_user.keyForChange = bot_key
            count_days_off = call_data.split(":")[3]
            count_days_izn = call_data.split(":")[4]
            await send_message(user_send, f'Введите кол-во изначальных дней для ключа <code><b>{bot_key}</b></code> пользователя <code><b>{user_id}</b></code>:\n\nОсталось дней: {count_days_off}\nИзначальной дней: {count_days_izn}')
            return

        if 'back' in call_data or 'delete' in call_data:
            logger.debug(f'{user_id} - Возвращаюсь к выбору пользователя')
            await delete_message(user_send, message.message_id)
            current_user = await user_get(user_send)
            current_user.bot_status = 1
            current_user.keyForChange = ''
            await message_input(message, alt_text=f'{current_user.last_select_user_index}')
            return

        if 'oplacheno' in call_data:
            logger.debug(f'{user_id} - Ключ {bot_key} оплачен выдаем его')
            await delete_message(user_send, message.message_id)
            if not await check_promo_is_activ(user.code, user_id):
                nick_user = message.chat.username
                await DB.set_activate_promo(user.code, nick_user if not nick_user is None else user_id, user_id, user.days_code)
                await DB.add_day_qr_key_in_DB(user_id, user.days_code, bot_key)
                await add_days(user_id, bot_key, day=user.days_code, promo=user.code)
                await DB.addReportsData('CountBuy', 1)
            else:
                await send_message(user_id, user.lang.get('tx_promo_is_activate'))
            user.code = ''
            user.days_code = 0
            return

        if 'prodlit' in call_data:
            logger.debug(f'{user_id} - Ключ {bot_key} продлеваем')
            await delete_message(user_send, message.message_id)
            await send_message(user_id, user.lang.get('tx_prodlt_tarif'), reply_markup=user.klav_buy_days)
            user.isProdleniye = bot_key
            return

        mes_del = await send_message(user_send, user.lang.get('tx_key_load_wait'))
        logger.debug(f'{user_id} - Загружаю ключи пользователя {user_id}')

        keys_data = await DB.get_user_keys(user_id) # BOT_Key, OS, isAdminKey, Date, CountDaysBuy, ip_server, isActive
        text_keys_data = ''
        if len(keys_data) > 0:
            logger.debug(f'{user_id} - Нашел ключи пользователя {user_id}')
            for item in keys_data:
                # isActive = bool(item[6])
                # if isActive:
                bot_key_m = item[0]
                protocol = item[7]
                text_keys_data_key = item[9]
                if bot_key_m == bot_key:
                    text_keys_data = text_keys_data_key
                    yes = True
                    logger.debug(f'{user_id} - Ключ {bot_key} активен, выдаем его')
                    break
        logger.debug(f'{user_id} - Загрузил ключи пользователя {user_id}')

        user_ = await user_get(user_send)
        if user_.isAdmin and not 'download' in call_data and yes:
            logger.debug(f'{user_id} - Выдаю админские кнопки')
            try:
                await delete_message(user_send, mes_del.message_id)
            except:
                pass
            klava = InlineKeyboardMarkup()
            but_key_download = InlineKeyboardButton(text=f'⏬Скачать конфиг', callback_data=f'keys:{user_id}:{bot_key}:download')
            count_days_off = call_data.split(":")[3]
            count_days_izn = call_data.split(":")[4]
            but_key_change_day = InlineKeyboardButton(text=f'🔄Изменить кол-во дней', callback_data=f'keys:{user_id}:{bot_key}:{count_days_off}:{count_days_izn}:change')
            but_key_del = InlineKeyboardButton(text=f'🛑Удалить', callback_data=f'keys:{user_id}:{bot_key}:delete')
            but_key_back = InlineKeyboardButton(text=f'⏪Вернуться к пользователю', callback_data=f'keys:{user_id}:{bot_key}:back')
            klava.add(but_key_download)
            klava.add(but_key_change_day)
            if AUTO_PAY_YKASSA:
                but = InlineKeyboardButton(text=f'💳Изменить сумму следующего списания', callback_data=f'keys:{user_id}:{bot_key}:change_summ')
                klava.add(but)
            klava.add(but_key_del)
            klava.add(but_key_back)
            return await send_message(user_send, f'Выберите действие с ключом <code><b>{bot_key}</b></code> пользователя <code><b>{user_id}</b></code>:', reply_markup=klava)

        if yes:
            logger.debug(f'{user_id} - Ключ {bot_key} проверка yes пройдена')
            try:
                await delete_message(user_send, message.message_id)
            except:
                pass
            server = None
            ip_server = None
            if text_keys_data == '':
                ip_server = await DB.get_ip_server_by_key_name(bot_key)
                logger.debug(f'{user_id} - Ключ {bot_key} ip сервера {ip_server}')

                if not ip_server is None and ip_server:
                    logger.debug(f'{user_id} - Ключ {bot_key} ищу сервер')
                    for item in SERVERS:
                        if item['ip'] == ip_server:
                            logger.debug(f'{user_id} - Ключ {bot_key} сервер найден')
                            server = item
                            break

            if (ip_server and server) or text_keys_data != '':
                logger.debug(f'{user_id} - Ключ {bot_key} сервер найден, выдаю конфиг')

                if server:
                    check_ = await check_server_is_work(server['ip'])
                else:
                    check_ = True

                if protocol == 'wireguard':
                    # Если есть ip-сервера
                    count_keys = await DB.get_qr_key_All()
                    if not count_keys is None:
                        count_keys = len(count_keys)
                    else:
                        count_keys = 0
                    conf_name_local = f'{NAME_BOT_CONFIG.lower()}_{random.randint(1,9)}{count_keys}{random.randint(1,9)}'
                    path_to_conf_server = f'/home/{NO_ROOT_USER}/configs/{bot_key}.conf'
                    path_to_conf_local = f"{conf_name_local[:15].lower()}.conf"
                    logger.debug(f'{user_id} - Ключ {bot_key} путь к конфигу {path_to_conf_server}')

                    if text_keys_data == '':
                        if check_:
                            logger.debug(f'{user_id} - Ключ {bot_key} скачиваю конфиг WireGuard')
                            text = await exec_command_in_http_server(ip=server['ip'], password=server['password'], path=path_to_conf_server)
                            logger.debug(f'{user_id} - Ключ {bot_key} конфиг скачан WireGuard text = {text}')
                        else:
                            logger.debug(f'{user_id} - Ключ {bot_key} конфиг WireGuard не скачан, сервер не отвечает')
                            text = None
                    else:
                        logger.debug(f'{user_id} - Ключ {bot_key} конфиг WireGuard загружен из БД')
                        text = text_keys_data
                elif protocol == 'outline':
                    if text_keys_data == '':
                        if check_:
                            logger.debug(f'{user_id} - Ключ {bot_key} скачиваю конфиг Outline')
                            cl = OutlineBOT(server['api_url'], server['cert_sha256'])
                            logger.debug(f'{user_id} - Ключ {bot_key} конфиг скачан Outline')
                            text = None
                            for key in cl.get_keys():
                                if key.name == bot_key:
                                    logger.debug(f'{user_id} - Ключ {bot_key} конфиг скачан Outline, нашел нужный ключ')
                                    text = f"{key.access_url}#{server['location']} - {NAME_BOT_CONFIG}"
                                    break
                        else:
                            logger.debug(f'{user_id} - Ключ {bot_key} конфиг Outline не скачан, сервер не отвечает')
                            text = None
                    else:
                        logger.debug(f'{user_id} - Ключ {bot_key} конфиг Outline загружен из БД')
                        text = text_keys_data
                elif protocol == 'vless':
                    if text_keys_data == '':
                        if check_:
                            logger.debug(f'{user_id} - Ключ {bot_key} скачиваю конфиг VLESS')
                            cl = VLESS(server['ip'], server['password'])
                            logger.debug(f'{user_id} - Ключ {bot_key} конфиг скачан VLESS')
                            text = None
                            for key in cl.activ_list():
                                if key[0] == bot_key:
                                    logger.debug(f'{user_id} - Ключ {bot_key} конфиг скачан VLESS, нашел нужный ключ')
                                    text = key[2]
                                    break
                        else:
                            logger.debug(f'{user_id} - Ключ {bot_key} конфиг VLESS не скачан, сервер не отвечает')
                            text = None
                    else:
                        logger.debug(f'{user_id} - Ключ {bot_key} конфиг VLESS загружен из БД')
                        text = text_keys_data
                elif protocol == 'pptp':
                    if text_keys_data == '':
                        logger.debug(f'{user_id} - Ключ {bot_key} конфиг PPTP не скачан, и нет возможности его загрузить')
                        text = None
                    else:
                        logger.debug(f'{user_id} - Ключ {bot_key} конфиг PPTP загружен из БД')
                        text = text_keys_data

                if not text:
                    logger.warning(f'{user_id} - Ключ {bot_key} конфиг не скачан')
                    await send_message(user_send, user.lang.get('tx_key_load_no_success'))
                    try:
                        await delete_message(user_send, mes_del.message_id)
                    except:
                        pass
                    return

                if text_keys_data == '':
                    await DB.set_keys_data_for_key(bot_key, text)

                if protocol == 'wireguard':
                    logger.debug(f'{user_id} - Ключ {bot_key} генерирую QR код')
                    if SEND_QR:
                        path_to_save = f'{conf_name_local[:15]}.png'
                        logger.debug(f'{user_id} - Ключ {bot_key} конфиг скачан, генерирую QR код, путь к сохранению {path_to_save}')

                        result_qr = False
                        try:
                            result_qr = await gen_qr_code(text, QR_LOGO, path_to_save)
                            if result_qr:
                                logger.debug(f'{user_id} - Ключ {bot_key} конфиг скачан, QR код сгенерирован, отправляю')
                                await bot.send_photo(user_send, open(path_to_save, 'rb'))
                                logger.debug(f'{user_id} - Ключ {bot_key} конфиг скачан, QR код отправлен')
                            else:
                                logger.warning(f'{user_id} - Ключ {bot_key} конфиг скачан, создание QR не удалось произвести так как не был обнаружен верный LOGO.png result_qr={result_qr}')
                        except Exception as e:
                            logger.warning(f'{user_id} - Ключ {bot_key} конфиг скачан, создание QR не удалось произвести так как не был обнаружен верный LOGO.png result_qr={result_qr}\nОшибка: {e}')
                    with open(path_to_conf_local, "w") as f:
                        f.write(text)
                    await bot.send_document(user_send, open(path_to_conf_local, "rb"))
                    logger.debug(f'{user_id} - Ключ {bot_key} конфиг скачан, конфиг отправлен')
                elif protocol == 'outline':
                    await send_message(user_send, f'<code>{text}</code>')
                    logger.debug(f'{user_id} - Ключ Outline text.access_url = {text}')
                elif protocol == 'vless':
                    await send_message(user_send, f'<code>{text}</code>')
                    logger.debug(f'{user_id} - Ключ VLESS text = {text}')
                elif protocol == 'pptp':
                    if INLINE_MODE:
                        klava = InlineKeyboardMarkup()
                        klava.add(InlineKeyboardButton(text=user.lang.get('but_main'), callback_data=f'buttons:but_main'))
                    else:
                        klava = ReplyKeyboardMarkup(resize_keyboard=True)
                        klava.add(user.lang.get('but_main'))
                    await send_message(user_send, f'{text}', reply_markup=klava)
                    logger.debug(f'{user_id} - Ключ PPTP text = {text}')

                if protocol != 'pptp':
                    user.key_url = text
                    await send_message(user_send, user.lang.get('tx_key_select_for_help'), reply_markup=await fun_klav_podkl_no_back(user, user.buttons_podkl_vless))
                    logger.debug(f'{user_id} - Ключ {bot_key} конфиг скачан, отправил сообщение с кнопками подключения')

                if protocol == 'wireguard':
                    try:
                        logger.debug(f'{user_id} - Ключ {bot_key} конфиг скачан, удаляю конфиги')
                        os.remove(path_to_conf_local)
                        if SEND_QR:
                            os.remove(path_to_save)
                        logger.debug(f'{user_id} - Ключ {bot_key} конфиг скачан, конфиги удалены')
                    except:
                        pass
            else:
                if call:
                    await bot.answer_callback_query(callback_query_id=call.id, text=user.lang.get('tx_key_no_search'))
                logger.warning(f'{user_id} - Ключ {bot_key} конфиг не скачан, сервер не найден')
        else:
            if call:
                await bot.answer_callback_query(callback_query_id=call.id, text=user.lang.get('tx_key_no_search'))
            logger.warning(f'{user_id} - Ключ {bot_key} конфиг не скачан, ключ не найден')

        try: await delete_message(user_send, mes_del.message_id)
        except: pass
    except:
        await Print_Error()

@dp.callback_query_handler(lambda call: call.data.startswith('report:'))
async def report_call(call):
    try:
        method = call.data.split(':')[1]
        user_id = call.message.chat.id
        await delete_message(user_id, call.message.message_id)
        await get_users_reports(user_id, method)
        return True
    except:
        await Print_Error()

@dp.callback_query_handler(lambda call: call.data.startswith('urls:'))
async def urls_call(call=None, cpec_code='', message=None):
    try:
        if cpec_code == '':
            cpec_code = call.data.split(':')[1].strip()

        if message is None:
            message = call.message

        user_id = message.chat.id
        user = await user_get(user_id)
        await delete_message(user_id, message.message_id)
        if user.isAdmin:
            if cpec_code == 'back':
                await urls_message(call.message)
                return False

            data_promo = await DB.get_stats_promoses(code=cpec_code)
            text_send = ''

            if data_promo:
                if data_promo[0] and len(data_promo[0]) > 0 and data_promo[0][0]:
                    for i in data_promo:
                        code = i[0]
                        id_partner = i[2]
                        if code == cpec_code:
                            percatage = i[1]
                            percent_partner = i[3]
                            count = i[4] if not i[4] is None else 0
                            summ = i[5] if not i[5] is None else 0
                            count_probniy = i[6] if not i[6] is None else 0

                            yes = True
                            url = f'https://t.me/{BOT_NICK}?start={code}\n'

                            resu = await DB.get_user_operations(code)
                            resu1 = await DB.get_user_operations(code, 'prodl')
                            resu2 = await DB.get_user_operations(code, 'buy')
                            resu3 = await DB.get_user_operations(code, 'promo', da=True)
                            partner_pay = await DB.get_parter_pay(id_partner)

                            if partner_pay:
                                last_dolg_date = datetime.strptime(partner_pay[-1][1], "%Y-%m-%d %H:%M:%S.%f")
                                last_dolg = partner_pay[-1][4]
                            else:
                                last_dolg = 0
                                last_dolg_date = None

                            # Считаем сумму продлений
                            total_prodl_summ = 0
                            new_prodl_summ = 0

                            for res in resu1:
                                total_summ = res[0]
                                date_ = res[1]
                                total_prodl_summ += total_summ

                                if not last_dolg_date is None and datetime.strptime(date_, "%Y-%m-%d %H:%M:%S.%f") < last_dolg_date:
                                    continue

                                new_prodl_summ += total_summ

                            # Считаем сумму покупок
                            total_buy_summ = 0
                            new_buy_summ = 0

                            for res in resu2:
                                total_summ = res[0]
                                date_ = res[1]
                                total_buy_summ += total_summ

                                if not last_dolg_date is None and datetime.strptime(date_, "%Y-%m-%d %H:%M:%S.%f") < last_dolg_date:
                                    continue

                                new_buy_summ += total_summ

                            if percatage == 0:
                                # Считаем сумму промокодов
                                total_promo_summ = 0
                                new_promo_summ = 0

                                for res in resu3:
                                    total_summ = res[0]
                                    date_ = res[1]
                                    total_promo_summ += total_summ

                                    if not last_dolg_date is None and datetime.strptime(date_, "%Y-%m-%d %H:%M:%S.%f") < last_dolg_date:
                                        continue

                                    new_promo_summ += total_summ  
                            else:
                                new_promo_summ = 0
                                total_promo_summ = 0

                            # Считаем промокоды 
                            data_30 = None
                            data_90 = None
                            data_180 = None
                            data_365 = None

                            for res in resu:
                                days = res[0]
                                count_users_code = res[1]
                                total_summ = res[2]

                                if days == 30:
                                    data_30 = (count_users_code, total_summ)
                                elif days == 90:
                                    data_90 = (count_users_code, total_summ)
                                elif days == 180:
                                    data_180 = (count_users_code, total_summ)
                                elif days == 365:
                                    data_365 = (count_users_code, total_summ)

                            promo_text = ''
                            promo_yes = False
                            promo_text_1 = user.lang.get('tx_partner_stat_promo_1')
                            promo_text_3 = user.lang.get('tx_partner_stat_promo_3')
                            promo_text_6 = user.lang.get('tx_partner_stat_promo_6')
                            promo_text_12 = user.lang.get('tx_partner_stat_promo_12')
                            
                            if TARIF_1 != 0 and not data_30 is None:
                                promo_yes = True
                                promo_text += f'*{data_30[0]} {promo_text_1} ({"~" if percatage != 0 else ""}{await razryad(data_30[1])}₽)\n' # пишем сколько промокодов активировано на 1 месяц (по id пользователя смотрим promo, если такой же как у нас, то +1)
                            if TARIF_3 != 0 and not data_90 is None:
                                promo_yes = True
                                promo_text += f'*{data_90[0]} {promo_text_3} ({"~" if percatage != 0 else ""}{await razryad(data_90[1])}₽)\n' # пишем сколько промокодов активировано на 3 месяца (по id пользователя смотрим promo, если такой же как у нас, то +1)
                            if TARIF_6 != 0 and not data_180 is None:
                                promo_yes = True
                                promo_text += f'*{data_180[0]} {promo_text_6} ({"~" if percatage != 0 else ""}{await razryad(data_180[1])}₽)\n' # пишем сколько промокодов активировано на 6 месяцев (по id пользователя смотрим promo, если такой же как у нас, то +1)
                            if TARIF_12 != 0 and not data_365 is None:
                                promo_yes = True
                                promo_text += f'*{data_365[0]} {promo_text_12} ({"~" if percatage != 0 else ""}{await razryad(data_365[1])}₽)' # пишем сколько промокодов активировано на 12 месяцев (по id пользователя смотрим promo, если такой же как у нас, то +1)

                            if not promo_yes:
                                promo_text += '...'

                            total_partner = (total_buy_summ + total_prodl_summ + total_promo_summ) * percent_partner / 100

                            summ_opl = 0
                            if len(partner_pay) > 0:
                                for i in partner_pay:
                                    summ_opl += int(i[2])

                            total_vivod = await razryad(summ_opl)
                            remains_vivod = total_partner - summ_opl
                            # total_partner_summ = (total_buy_summ + total_prodl_summ + total_promo_summ) * percent_partner / 100
                            
                            print(f'👨‍💻Данные партнера: id_parner={id_partner}, code={code}, last_dolg={last_dolg}, new_buy_summ={new_buy_summ}, new_prodl_summ={new_prodl_summ}, new_promo_summ={new_promo_summ}, percent_partner={percent_partner}, total_partner={total_partner}, total_buy_summ={total_buy_summ}, total_promo_summ={total_promo_summ}, total_prodl_summ={total_prodl_summ}, total_vivod={total_vivod}, remains_vivod={remains_vivod}')
                            
                            if remains_vivod < 0:
                                remains_vivod = 0
                            remains_vivod = await razryad(remains_vivod)

                            total_buy_summ = await razryad(total_buy_summ)
                            total_promo_summ = await razryad(total_promo_summ)
                            total_prodl_summ = await razryad(total_prodl_summ)
                            total_partner_summ_text = await razryad(total_partner)
                            
                            text_send += user.lang.get('tx_partner_stat').format(
                                url=url,
                                percatage=percatage,
                                percent_partner=percent_partner,
                                count=count,
                                count_probniy=count_probniy,
                                promo_text=promo_text,
                                total_buy_summ=total_buy_summ,
                                total_promo_summ=total_promo_summ,
                                total_prodl_summ=total_prodl_summ,
                                total_partner=total_partner_summ_text,
                                total_vivod=total_vivod,
                                remains_vivod=remains_vivod
                            )

                            # Отправляем файл с текстами и промокодами (если активированы выделяем их)
                            file_name = f'{id_partner}_promo_{code}.txt'
                            file = await get_urls_partner_file(id_partner, file_name)
                            if file:
                                await bot.send_document(user_id, file)
                            try: os.remove(file_name)
                            except: pass
                            break

            if text_send != '':
                klava = InlineKeyboardMarkup()
                but = InlineKeyboardButton(text=f'💸Выплаты', callback_data=f'payments:{id_partner}:{cpec_code}:{total_partner_summ_text.replace(" ","")}')
                klava.add(but)
                but = InlineKeyboardButton(text=f'🧾Данные по клиентам', callback_data=f'data_urls:{id_partner}:{cpec_code}')
                klava.add(but)
                but = InlineKeyboardButton(text=f'✍️Изменить данные', callback_data=f'urls_edit:{id_partner}:{cpec_code}')
                klava.add(but)
                but = InlineKeyboardButton(text=f'⏪Назад', callback_data=f'urls:back')
                klava.add(but)
                await send_message(user_id, text_send, reply_markup=klava)
            else:
                user.bot_status = 0
                return False
        return True
    except:
        await Print_Error()
        return False

@dp.callback_query_handler(lambda call: call.data.startswith('data_urls:'))
async def data_urls(call):
    try:
        id_partner = int(call.data.split(':')[1].strip())
        cpec_code = call.data.split(':')[2].strip()
        user_id = call.message.chat.id
        user = await user_get(user_id)
        user.userForPay = id_partner

        if user.isAdmin:
            klava = InlineKeyboardMarkup()

            if 'back' in call.data:
                await delete_message(user_id, call.message.message_id)
                await urls_call(call, cpec_code=cpec_code)
            else:
                # вывести данные по спец.ссылке
                data = await DB.get_users_summ_by_spec_code(cpec_code) # o.user_id, SUM(o.summ), COUNT(*)
                temp_data = []
                if data and len(data) > 0:
                    text_send = f'ℹ️Данные по спец.ссылке <b>{cpec_code}</b>:\n\n'
                    for index, item in enumerate(data):
                        op_user_id = item[0]
                        summ = item[1]
                        count = item[2]
                        if summ > 0:
                            temp_data.append((op_user_id, summ, count))

                    # отсортировать массив по сумме по убыванию
                    temp_data.sort(key=lambda x: x[1], reverse=True)

                    for index, item in enumerate(temp_data):
                        op_user_id = item[0]
                        summ = item[1]
                        count = item[2]
                        text_send += f'{index + 1}. <code>{op_user_id}</code> - <b>{await razryad(summ)}₽</b> <i>({count} шт.)</i>\n'
                        
                        if index >= 100:
                            break                    
                else:
                    text_send = f'⚠️Операций по спец.ссылке <b>{cpec_code}</b> не было найдено!'

                but = InlineKeyboardButton(text=f'⏪Назад', callback_data=f'{call.data}:back')
                klava.add(but)
                await send_message(user_id, text_send, reply_markup=klava)
        return True
    except:
        await Print_Error()
        return False

@dp.callback_query_handler(lambda call: call.data.startswith('urls_edit:'))
async def urls_edit(call):
    try:
        id_partner = int(call.data.split(':')[1].strip())
        cpec_code = call.data.split(':')[2].strip()
        user_id = call.message.chat.id
        user = await user_get(user_id)
        user.userForPay = id_partner

        # добавить возможность изменить:
        # - название спец.ссылки (проверить чтобы спец.ссылки с таким именем еще не было) (у всех пользователей)
        # - скидку клиентам на первую покупку
        # - % заработка партнера
        # - удалить спец.ссылку (с подтверждением) (у всех пользователей) (также удалять выплаты)

        if user.isAdmin:
            klava = InlineKeyboardMarkup()

            if 'back' in call.data:
                await delete_message(user_id, call.message.message_id)
                await urls_call(call, cpec_code=cpec_code)
            elif 'nazv_sp' in call.data:
                await delete_message(user_id, call.message.message_id)
                await send_message(user_id, 'ℹ️Укажите название, которое не используется:')
                user.bot_status = 7
            elif 'sk_cl' in call.data:
                await delete_message(user_id, call.message.message_id)
                await send_message(user_id, 'ℹ️Укажите процент скидки клиентам от 0 до 100:')
                user.bot_status = 5
            elif 'pa_per' in call.data:
                await delete_message(user_id, call.message.message_id)
                await send_message(user_id, 'ℹ️Укажите процент заработка партнера от 1 до 100:')
                user.bot_status = 6
            elif 'dldldl' in call.data:
                await delete_message(user_id, call.message.message_id)
                data_promo = await DB.get_stats_promoses(code=cpec_code)
                if not data_promo is None and len(data_promo) > 0:
                    if not data_promo[0] is None and len(data_promo[0]) > 0 and not data_promo[0][0] is None:
                        for i in data_promo:
                            code = i[0]
                            if code == cpec_code:
                                count = i[4] if not i[4] is None else 0
                                if count > 0:
                                    await send_message(user_id, f'⚠️По данной спец.ссылке зарегистированы пользователи!')
                                break

                but = InlineKeyboardButton(text=f'🛑Удалить', callback_data=f'urls_edit:{id_partner}:{cpec_code}:dld_yes')
                klava.add(but)
                data_ = call.data.replace(':dldldl','')
                but = InlineKeyboardButton(text=f'✅Отменить', callback_data=f'{data_}')
                klava.add(but)
                await send_message(user_id, f'⚠️Вы действительно хотите удалить спец.ссылку <b>{cpec_code}</b>?', reply_markup=klava)
            elif 'dld_yes' in call.data:
                await delete_message(user_id, call.message.message_id)
                await DB.delete_spec_urls(cpec_code, id_partner)
                await send_message(user_id, f'✅Спец.ссылка <b>{cpec_code}</b> была успешно удалена!')
                await urls_call(call)
            else:
                but = InlineKeyboardButton(text=f'🧾Название спец.ссылки', callback_data=f'urls_edit:{id_partner}:{cpec_code}:nazv_sp')
                klava.add(but)
                but = InlineKeyboardButton(text=f'🏷️Изменить скидку клиентам (на первую покупку)', callback_data=f'urls_edit:{id_partner}:{cpec_code}:sk_cl')
                klava.add(but)
                but = InlineKeyboardButton(text=f'💸Процент заработка партнера', callback_data=f'urls_edit:{id_partner}:{cpec_code}:pa_per')
                klava.add(but)
                but = InlineKeyboardButton(text=f'🛑Удалить спец.ссылку', callback_data=f'urls_edit:{id_partner}:{cpec_code}:dldldl')
                klava.add(but)
                but = InlineKeyboardButton(text=f'⏪Назад', callback_data=f'{call.data}:back')
                klava.add(but)
                await send_message(user_id, f'ℹ️Выберите что необходимо изменить в спец.ссылке <b>{cpec_code}</b>:', reply_markup=klava)
        return True
    except:
        await Print_Error()
        return False

@dp.callback_query_handler(lambda call: call.data.startswith('payments:'))
async def payments_call(call):
    try:
        cpec_code = call.data.split(':')[2].strip()
        id_partner = int(call.data.split(':')[1].strip())
        partner_summ_zarabotal = int(call.data.split(':')[3].strip())
        user_id = call.message.chat.id
        user = await user_get(user_id)
        await delete_message(user_id, call.message.message_id)
        if user.isAdmin:
            if 'back' in call.data:
                await urls_call(call, cpec_code=cpec_code)
                return

            data_promo = await DB.get_parter_pay(id_partner)
            text_send = ''
            summ_opl = 0

            if len(data_promo) > 0:
                for i in data_promo:
                    summ_opl += int(i[2])
                    text_send += f'🔢 №<b>{i[0]}</b>: {i[1].split(".")[0]}\n'
                    text_send += f'Сумма: <b>{await razryad(i[2])}</b>₽\n'
                    text_send += f'Комментарий: <b>{i[3]}</b>\n\n'

            klava = InlineKeyboardMarkup()
            but = InlineKeyboardButton(text=f'✅Добавить выплату', callback_data=f'payment_add:{id_partner}:{partner_summ_zarabotal}')
            klava.add(but)
            but = InlineKeyboardButton(text=f'⏪Назад', callback_data=f'{call.data}:back')
            klava.add(but)
            if text_send == '':
                await send_message(user_id, '⚠️Выплат для этого пользователя найдено не было!', reply_markup=klava)
            else:
                text_send += f'✅Выплачено/Партнер заработал: {summ_opl}/{partner_summ_zarabotal}₽\n'
                await send_message(user_id, text_send, reply_markup=klava)
        return True
    except:
        await Print_Error()
        return False

@dp.callback_query_handler(lambda call: call.data.startswith('payment_add:'))
async def payment_add_call(call):
    try:
        id_partner = int(call.data.split(':')[1].strip())
        partner_summ_zarabotal = int(call.data.split(':')[2].strip())
        user_id = call.message.chat.id
        user = await user_get(user_id)
        if user.isAdmin:
            user.userForPay = id_partner
            user.userLastZarabotal = partner_summ_zarabotal
            user.bot_status = 2

            klava = InlineKeyboardMarkup()
            but = InlineKeyboardButton(text=f'⏪Специальные ссылки', callback_data=f'urls:back')
            klava.add(but)

            text = '⚠️Для добавления выплаты напишите в бот сумму (без пробелов) и комментарий, пример:\n\n11000/оплата половины от проданных ключей и продлений'
            await send_message(user_id, text, reply_markup=klava)
        return True
    except:
        await Print_Error()
        return False

@dp.callback_query_handler(lambda call: call.data.startswith('buttons:'))
async def buttons_call(call):
    try:
        message = call.message
        user_id = message.chat.id
        user = await user_get(user_id)
        data = call.data.split(':')[1]

        if 'urls_call' in data:
            await urls_message(message)
        elif 'buy_isPodpiska' in data:
            await buy_message(user_id=user_id, isPodpiska=True)
        elif 'buy_isBuy' in data:
            await buy_message(user_id=user_id, is_buy=True)
        elif 'test_key_get' in data:
            await test_key_get(user_id)
        else:
            if not 'znach' in call.data:
                data = user.lang.get(data)
            await message_input(message, alt_text=data)
    except:
        await Print_Error()

async def select_payment_method(user_id=None):
    try:
        user = await user_get(user_id)

        try: WALLETS
        except: await DB.GET_WALLETS()

        isYooMoney, isYooKassa, isTinkoffPay, isLava, isCryptomus, isWalletPay, isSoftPay, isPayok, isAaio, isRootPay, isFreeKassa, isXTR, isCardLink = False, False, False, False, False, False, False, False, False, False, False, False, False

        # Выбор кошелька
        for wallet in WALLETS:
            is_active = wallet['isActive']

            if not is_active:
                continue

            Name = wallet['Name']

            if Name == PAY_METHODS.YOO_MONEY and not isYooMoney: isYooMoney = True
            elif Name == PAY_METHODS.YOO_KASSA and not isYooKassa: isYooKassa = True
            elif Name == PAY_METHODS.TINKOFF and not isTinkoffPay: isTinkoffPay = True
            elif Name == PAY_METHODS.LAVA and not isLava: isLava = True
            elif Name == PAY_METHODS.CRYPTOMUS and not isCryptomus: isCryptomus = True
            elif Name == PAY_METHODS.WALLET_PAY and not isWalletPay: isWalletPay = True
            elif Name == PAY_METHODS.SOFT_PAY and not isSoftPay: isSoftPay = True
            elif Name == PAY_METHODS.PAYOK and not isPayok: isPayok = True
            elif Name == PAY_METHODS.AAIO and not isAaio: isAaio = True
            elif Name == PAY_METHODS.ROOT_PAY and not isRootPay: isRootPay = True
            elif Name == PAY_METHODS.FREE_KASSA and not isFreeKassa: isFreeKassa = True
            elif Name == PAY_METHODS.XTR and not isXTR: isXTR = True
            elif Name == PAY_METHODS.CARDLINK and not isCardLink: isCardLink = True

        buttons = []
        if INLINE_MODE:
            if isYooMoney: buttons.append(InlineKeyboardButton(text=user.lang.get('but_yoomoney'), callback_data=f'buttons:but_yoomoney'))
            if isYooKassa: buttons.append(InlineKeyboardButton(text=user.lang.get('but_yookassa'), callback_data=f'buttons:but_yookassa'))
            if isTinkoffPay: buttons.append(InlineKeyboardButton(text=user.lang.get('but_tinkoff'), callback_data=f'buttons:but_tinkoff'))
            if isLava: buttons.append(InlineKeyboardButton(text=user.lang.get('but_lava'), callback_data=f'buttons:but_lava'))
            if isCryptomus: buttons.append(InlineKeyboardButton(text=user.lang.get('but_cryptomus'), callback_data=f'buttons:but_cryptomus'))
            if isWalletPay: buttons.append(InlineKeyboardButton(text=user.lang.get('but_walletpay'), callback_data=f'buttons:but_walletpay'))
            if isSoftPay: buttons.append(InlineKeyboardButton(text=user.lang.get('but_softpay'), callback_data=f'buttons:but_softpay'))
            if isPayok: buttons.append(InlineKeyboardButton(text=user.lang.get('but_payok'), callback_data=f'buttons:but_payok'))
            if isAaio: buttons.append(InlineKeyboardButton(text=user.lang.get('but_aaio'), callback_data=f'buttons:but_aaio'))
            if isRootPay: buttons.append(InlineKeyboardButton(text=user.lang.get('but_rootpay'), callback_data=f'buttons:but_rootpay'))
            if isFreeKassa: buttons.append(InlineKeyboardButton(text=user.lang.get('but_freekassa'), callback_data=f'buttons:but_freekassa'))
            if isXTR: buttons.append(InlineKeyboardButton(text=user.lang.get('but_stars'), callback_data=f'buttons:but_stars'))
            if isCardLink: buttons.append(InlineKeyboardButton(text=user.lang.get('but_cardlink'), callback_data=f'buttons:but_cardlink'))
            
            klava = InlineKeyboardMarkup(row_width=2).add(*buttons)
        else:
            if isYooMoney: buttons.append(user.lang.get('but_yoomoney'))
            if isYooKassa: buttons.append(user.lang.get('but_yookassa'))
            if isTinkoffPay: buttons.append(user.lang.get('but_tinkoff'))
            if isLava: buttons.append(user.lang.get('but_lava'))
            if isCryptomus: buttons.append(user.lang.get('but_cryptomus'))
            if isWalletPay: buttons.append(user.lang.get('but_walletpay'))
            if isSoftPay: buttons.append(user.lang.get('but_softpay'))
            if isPayok: buttons.append(user.lang.get('but_payok'))
            if isAaio: buttons.append(user.lang.get('but_aaio'))
            if isRootPay: buttons.append(user.lang.get('but_rootpay'))
            if isFreeKassa: buttons.append(user.lang.get('but_freekassa'))
            if isXTR: buttons.append(user.lang.get('but_stars'))
            if isCardLink: buttons.append(user.lang.get('but_cardlink'))
            
            klava = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2).add(*buttons)

        await send_message(user_id, user.lang.get('tx_select_payment_method'), reply_markup=klava)
    except:
        await Print_Error()

async def pokupka(user):
    try:
        tarif_select = 1
        user_id = user.id_Telegram
        if not user.isPayChangeProtocol and not user.isPayChangeLocations:
            days = await DB.get_user_days_by_buy(user_id)
            tarif_else_1_tarif = ''
            if days == 90:
                tarif_select = 2
                tarif = user.tarif_3
                summ = user.tarif_3_text
                if TARIF_1 != 0:
                    tarif_else_1_tarif = f'(<s>{user.tarif_1_text * 3} {user.valuta}</s>)'
            elif days == 180:
                tarif_select = 3
                tarif = user.tarif_6
                summ = user.tarif_6_text
                if TARIF_1 != 0:
                    tarif_else_1_tarif = f'(<s>{user.tarif_1_text * 6} {user.valuta}</s>)'
            elif days == 365:
                tarif_select = 4
                tarif = user.tarif_12
                summ = user.tarif_12_text
                if TARIF_1 != 0:
                    tarif_else_1_tarif = f'(<s>{user.tarif_1_text * 12} {user.valuta}</s>)'
            else:
                tarif = user.tarif_1
                summ = user.tarif_1_text
        else:
            if user.isPayChangeProtocol:
                tarif_select = 11
                tarif = SUMM_CHANGE_PROTOCOL
                summ = SUMM_CHANGE_PROTOCOL
                if user.lang_select != 'Русский':
                    summ = round(SUMM_CHANGE_PROTOCOL / KURS_RUB, 2)
                tarif_else_1_tarif = round(summ * 3, 0)
            elif user.isPayChangeLocations:
                tarif_select = 12
                tarif = SUMM_CHANGE_LOCATIONS
                summ = SUMM_CHANGE_LOCATIONS
                if user.lang_select != 'Русский':
                    summ = round(SUMM_CHANGE_LOCATIONS / KURS_RUB, 2)
                tarif_else_1_tarif = round(summ * 2.5, 0)

        if not user.PAY_WALLET:
            user.payStatus = 1
            await select_payment_method(user_id)
            return 

        try:
            user.tarif_select = tarif_select
            url_pay = await user.PAY_WALLET.create_pay(user, tarif)
        except:
            zametki = '<b>Необходимо пройти в /wallets и добавить способ оплаты!</b>'
            await send_admins(None, '🛑Не найдено способов оплаты!', zametki)
            return

        is_rootpay = user.amount_one and user.wallet
        is_xtr = url_pay == PAY_METHODS.XTR
        
        if not is_xtr:
            klava_buy = InlineKeyboardMarkup()
            if not is_rootpay:
                klava_buy.add(InlineKeyboardButton(
                    text=user.lang.get('but_pay').format(tarif=summ, valuta=user.valuta), 
                    url=url_pay if not WEB_APP_PAY else None, 
                    web_app=WebAppInfo(url=url_pay) if WEB_APP_PAY else None)
                )
            klava_buy.add(InlineKeyboardButton(text=user.lang.get('but_check_pay'), callback_data=f'check:{user_id}:{user.bill_id}'))

            if is_rootpay:
                text_send = user.lang.get('tx_oplata_rootpay').format(
                    summ=user.amount_one,
                    valuta=user.valuta,
                    wallet=user.wallet
                )
            else:
                text_send = user.lang.get('tx_oplata').format(
                    summ=summ,
                    valuta=user.valuta,
                    summ_s=f' <s>{tarif_else_1_tarif}</s>' if tarif_else_1_tarif else ''
                )
            message_del = await send_message(user_id, text_send, reply_markup=klava_buy)
        
        if not is_rootpay:
            if PHONE_NUMBER != '':
                await send_message(user_id, user.lang.get('tx_perevod').format(nick_help=NICK_HELP), reply_markup=await fun_klav_cancel_pay(user))
                await send_message(user_id, f'<code>{PHONE_NUMBER}</code>')
            else:
                await send_message(user_id, user.lang.get('tx_help_text').format(nick_help=NICK_HELP), reply_markup=await fun_klav_cancel_pay(user))

        logger.debug(f'Создал запрос на оплату user.bill_id == {user.bill_id}')

        if user.isPayChangeProtocol:
            head_text = '🔄Вызвал оплату смены протокола'
        elif user.isPayChangeLocations:
            head_text = '🔄Вызвал оплату смены локаций (1 мес.)'
        else:
            if user.bill_bot_key != '':
                user.Protocol = await DB.get_Protocol_by_key_name(user.bill_bot_key)
                head_text = 'Вызвал продление ключа'
                text_add = f', <code>{user.bill_bot_key}</code>'
            else:
                head_text = '🔄Вызвал оплату ключа'
                text_add = ''

        if user.isPayChangeProtocol or user.isPayChangeLocations:
            bottom_text = f'🆔Bill_id: <code>{user.bill_id.split("-")[-1]}</code> (<b>{tarif}</b>₽)'
        else:
            bottom_text = f'🆔Bill_id: <code>{user.bill_id.split("-")[-1]}</code> ({user.Protocol}, <b>{tarif}</b>₽{text_add})'

        if len(WALLETS) > 1:
            bottom_text += f'\n💳Счет: <b>{user.PAY_WALLET.Name}</b> ({user.PAY_WALLET.API_Key_TOKEN[:15]})'

        admin_klava = InlineKeyboardMarkup()
        admin_klava.add(InlineKeyboardButton(text='✅Подтвердить оплату', callback_data=f'check:{user_id}:{user.bill_id}:admin'))
        if not IS_OTCHET:
            await send_admins(user_id, head_text, bottom_text, reply_markup=admin_klava)

        user.autoTimerStart = datetime.now()
        user.isAutoCheckOn = True
        try: user.message_del_id = message_del.message_id
        except: pass
        tasks = [asyncio.create_task(auto_check_pay(user_id, 0, str(user.bill_id)))]
        asyncio.gather(*tasks)
    except:
        await Print_Error()

async def help(user_id, id, protocol=PR_DEFAULT):
    try:
        user = await user_get(user_id)
        await DB.set_user_ustrv(user_id, id)

        if protocol == 'wireguard':
            if id == 1:
                text_instr = user.lang.get('instr_wireguard_android')
            elif id == 2:
                text_instr = user.lang.get('instr_wireguard_ios')
            elif id == 3:
                text_instr = user.lang.get('instr_wireguard_mac_windows')
        elif protocol == 'outline':
            if id == 1:
                text_instr = user.lang.get('instr_outline_android')
            elif id == 2:
                text_instr = user.lang.get('instr_outline_ios')
            elif id == 3:
                text_instr = user.lang.get('instr_outline_mac_windows')
        elif protocol == 'vless':
            if id == 1:
                text_instr = user.lang.get('instr_vless_android')
            elif id == 2:
                text_instr = user.lang.get('instr_vless_ios')
            elif id == 3:
                text_instr = user.lang.get('instr_vless_macos')
            elif id == 4:
                text_instr = user.lang.get('instr_vless_mac_windows')

        if INLINE_MODE:
            klava = InlineKeyboardMarkup()
            klava.add(InlineKeyboardButton(text=user.lang.get('but_back_help'), callback_data=f"buttons:but_back_help"))

        tx_download = user.lang.get('instr_2_0_download')
        tx_download_macos = user.lang.get('instr_2_0_download_macos')
        tx_download_windows = user.lang.get('instr_2_0_download_windows')
        tx_install = user.lang.get('instr_2_0_install')
        tx_desc = user.lang.get('instr_2_0_desc').format(tx_download=tx_download, tx_install=tx_install)

        if user.key_url:
            url = ''
            klava = InlineKeyboardMarkup()
            if protocol == 'outline':
                if id == 1:
                    url = 'https://play.google.com/store/apps/details?id=org.outline.android.client'
                    klava.add(InlineKeyboardButton(text=tx_download, url=url))
                elif id == 2:
                    url = 'https://itunes.apple.com/app/outline-app/id1356177741'
                    klava.add(InlineKeyboardButton(text=tx_download, url=url))
                elif id == 3:
                    url_mac = 'https://itunes.apple.com/app/outline-app/id1356178125'
                    url_win = 'https://s3.amazonaws.com/outline-releases/client/windows/stable/Outline-Client.exe'
                    klava.add(InlineKeyboardButton(text=tx_download_macos, url=url_mac))
                    klava.add(InlineKeyboardButton(text=tx_download_windows, url=url_win))

                url = f'http://{SERVERS[0]["ip"]}:43234/red?url=' + user.key_url.replace('ss://', '')#.replace(' ', '')
            elif protocol == 'vless':
                if id == 1:
                    url = 'https://play.google.com/store/apps/details?id=com.v2raytun.android'
                    klava.add(InlineKeyboardButton(text=tx_download, url=url))
                elif id == 2:
                    url = 'https://apps.apple.com/by/app/v2raytun/id6476628951'
                    klava.add(InlineKeyboardButton(text=tx_download, url=url))
                elif id == 3:
                    url = 'https://apps.apple.com/by/app/v2raytun/id6476628951'
                    klava.add(InlineKeyboardButton(text=tx_download, url=url))

                url = f'http://{SERVERS[0]["ip"]}:43234/red_vl?url='
                if id == 1:
                    url += 'v2raytun://import-config?url=' + user.key_url.replace('&', 'a_n_d')
                elif id == 2:
                    url += 'v2raytun://import/' + user.key_url.replace('&', 'a_n_d')
                elif id == 3:
                    url += f'v2raytun://import/' + user.key_url.replace('&', 'a_n_d')
                elif id == 4:
                    await send_message(user_id, text_instr)
                    await send_message(user_id, user.lang.get('instr_wireguard_rule'))
                    return

            if url != '':
                if '#' in url:
                    url = url.split('#')[0] + '&name=' + url.split('#')[1]
                klava.add(InlineKeyboardButton(text=tx_install, url=url))
                text_instr = tx_desc
                if protocol == 'vless':
                    if id == 1 and not user.key_url.startswith('vless://'):
                        text_instr += '\n\n' + user.lang.get('instr_2_0_desc_dop')
                    elif id == 2:
                        try:
                            dop_text = '🆕' + user.lang.get('instr_vless_ios').split('🆕')[1]
                            text_instr += f'\n\n{dop_text}'
                        except:
                            pass
                text_instr = f'<b>{text_instr}</b>'
                await send_message(user_id, text_instr, reply_markup=klava)
                return

        if protocol in ('wireguard', 'vless'):
            await send_message(user_id, text_instr)
            await send_message(user_id, user.lang.get('instr_wireguard_rule'))
        else:
            # Если протокол outline
            await send_message(user_id, text_instr)
    except:
        await Print_Error()

async def get_urls_partner_file(id_partner, filename):
    try:
        # Получаем все коды партнера
        codes = await DB.get_all_code_by_partner(id_partner)
        url = f'https://t.me/{BOT_NICK}?start={codes[1]}'
        yes = False
        user = await user_get(id_partner)

        with open(filename, 'w') as file:
            for code, is_activated, days in codes[0]:
                # Если код активирован, добавляем 5 решеток перед сообщением
                if is_activated:
                    file.write('##### ')

                # Записываем сообщение в файл
                file.write(f"{user.lang.get('tx_partner_promo_message').format(code=code, days=days, dney_text=await dney(days, user), url=url)}\n")

                # Добавляем пустую строку после каждого сообщения
                file.write('\n')
                yes = True

        if yes:
            return open(filename, "rb")
        else:
            return False
    except:
        await Print_Error()
        return False

async def reply_admin_message(message):
    try:
        message_reply_data = message.reply_to_message.text
        id_send_reply = None
        text_send_reply = None
        for index, stroka in enumerate(message_reply_data.split('\n')):
            if index == 2:
                id_send_reply = int(stroka.split(',')[0])
            if 'Text: ' in stroka:
                text_send_reply = stroka.replace('Text: ', '')

        if not id_send_reply is None:
            try:
                user = await user_get(id_send_reply)
                
                text_raw = message.text
                user_admin = await user_get(message.chat.id)
                text_send = await clear_tag_but(text_raw, user=user_admin)
                text_send = await send_promo_tag(text_send)
                if text_send != '':
                    klava = await fun_klava_news(str(text_raw), message.chat.id, user=user_admin)
                else:
                    klava = None
                answer_admin = f"{user.lang.get('tx_support_reply')}: <b>{text_send}</b>"

                if not text_send_reply is None:
                    await send_message(id_send_reply, f"{user.lang.get('tx_support_user_send')}: <b>{text_send_reply}</b>\n{answer_admin}", reply_markup=klava)
                else:
                    await send_message(id_send_reply, answer_admin)
            except:
                await send_message(message.chat.id, '🛑Не удалось отправить ответ клиенту!')
            await send_message(message.chat.id, '✅Ответ на сообщение успешно отправлен клиенту!')
        else:
            await send_message(message.chat.id, '🛑Не удалось отправить ответ клиенту!')
    except:
        await Print_Error()

async def change_days_vless(bot_key, days):
    try:
        # изменить кол-во дней в панели 3X-UI, если protocol='vless'
        ip_server = await DB.get_ip_server_by_key_name(bot_key)
        protocol = await DB.get_Protocol_by_key_name(bot_key)
        if protocol == 'vless':
            for server in SERVERS:
                if server['ip'] == ip_server:
                    if check_server_is_marzban(server['ip']):
                        marzban = MARZBAN(server['ip'], server['password'])
                        await marzban.update_status_key(key=bot_key, status=True)
                    else:
                        vless = VLESS(server['ip'], server['password'])
                        await vless.addOrUpdateKey(bot_key, isUpdate=True, isActiv=True, days=days)
                    break
    except:
        await Print_Error()

async def check_buttons_donate(user, m_text): 
    try:
        for el in user.buttons_Donate:
            if el == m_text:
                return True
        return False
    except:
        await Print_Error()

@dp.message_handler(content_types=["text"])
async def message_input(message, alt_text=''):
    try:
        global user_dict
        user_mes = message.chat
        user_id = user_mes.id

        if alt_text != '':
            message.text = alt_text

        m_text = message.text  # текст сообщения

        if not user_mes.id in user_dict:
            isUser = await DB.exists_user(user_mes.id)
            if not isUser:
                try:
                    await DB.add_user(user_mes.id, f'{user_mes.username}', f'{user_mes.first_name}', f'{user_mes.last_name}')
                except:
                    pass
            try:
                name = user_mes.first_name
            except:
                name = ''
            try: nick = message.chat.username
            except: nick = ''
            await DB.update_user_nick(message.chat.id, nick, name)

        user = await user_get(message.chat.id)
        if user.isBan: return

        await log_message(message)

        if user.isAdmin and 'forward_from' in message or 'forward_sender_name' in message:
            if 'forward_from' in message:
                znach_ = message.forward_from.id
            else:
                znach_ = message.forward_sender_name
            return await get_users_reports(user_id, f'all::{znach_}')

        # now = datetime.now() # timezone(timedelta(hours=3))
        # message_date = message.date # datetime.fromtimestamp(int(message.date), tz=timezone.utc)
        # time_diff = now - message_date

        # if time_diff.total_seconds() > 60:
        #     if not INLINE_MODE:
        #         await send_message(message.chat.id, user.lang.get('tx_bot_reboot'))

        if not message.reply_to_message is None and not message.reply_to_message.text is None and user.isAdmin:
            return await reply_admin_message(message)

        if user.bot_status == 1: # Просмотр определенного пользователя
            if not str(message.text.split('.')[0]).strip().replace(' ', '').isdigit():
                user.bot_status = 0
                return await message_input(message)

            index = int(str(message.text.split('.')[0]).strip().replace(' ', ''))

            for item in user.clients_report:
                if item[0] == index:
                    user.last_select_user_index = index
                    user_id_rep = item[1]
                    text_info_user = item[2]

                    klava_buy = InlineKeyboardMarkup()
                    but_key = InlineKeyboardButton(text=f'🧾Все данные о пользователе', callback_data=f'user:{user_id_rep}')
                    klava_buy.add(but_key)

                    user.bot_status = 0

                    keys_data = await DB.get_user_keys(user_id_rep) # BOT_Key, OS, isAdminKey, Date, CountDaysBuy, ip_server, isActive
                    if len(keys_data) > 0:
                        keys_yes = False
                        for key in keys_data:
                            bot_key = key[0]
                            isActive = bool(key[6])
                            izn_count_days = int(key[4])
                            protocol = key[7]
                            try:
                                date_start = datetime.strptime(key[3], '%Y_%m_%d')
                            except:
                                await Print_Error()
                                continue

                            # if not isActive:
                            #     continue

                            CountDaysBuy = int(key[4])
                            date_now = datetime.now()
                            date_end = date_start + timedelta(days=CountDaysBuy)
                            count_days_to_off = (date_end - date_now).days + 1

                            but_key = InlineKeyboardButton(text=f'🔑{bot_key} ({count_days_to_off}/{izn_count_days} {await dney(izn_count_days)}) ({protocol})', callback_data=f'keys:{user_id_rep}:{bot_key}:{count_days_to_off}:{izn_count_days}')
                            klava_buy.add(but_key)
                            keys_yes = True
                            
                    but = InlineKeyboardButton(text=f'✏️Изменить тарифы у клиента', callback_data=f'user_change_tarifs:{user_id_rep}')
                    klava_buy.add(but)

                    but_buy_1 = InlineKeyboardButton(text=f'🛑Удалить пользователя и его конфиги', callback_data=f'del_user:{user_id_rep}')
                    klava_buy.add(but_buy_1)
                    res_ = await DB.isGetBan_by_user(user_id_rep)
                    if not res_:
                        but_buy_2 = InlineKeyboardButton(text=f'🔒Заблокировать пользователя', callback_data=f'ban_user:{user_id_rep}')
                    else:
                        but_buy_2 = InlineKeyboardButton(text=f'🔓Разблокировать пользователя', callback_data=f'unban_user:{user_id_rep}')
                    klava_buy.add(but_buy_2)
                    return await send_message(message.chat.id, f'{text_info_user}', reply_markup=klava_buy)

            await send_message(message.chat.id, f'⚠️У данного пользователя нет истории сообщений!')
            user.bot_status = 0

        elif user.bot_status == 2: # Добавление выплаты
            try:
                text_spl = message.text.split('/')
                summ_opl = text_spl[0].strip().replace(' ', '')

                if not summ_opl.isdigit() or len(text_spl) < 2 or text_spl[1] == '' or (summ_opl.isdigit() and int(summ_opl) < 1):
                    await send_message(user_id, '🛑Не верный формат записи выплаты!')
                    user.bot_status = 0
                    return await message_input(message)

                comment = text_spl[1]
                summ_opl = int(summ_opl)
                if user.userForPay != 0:
                    klava = InlineKeyboardMarkup()
                    but = InlineKeyboardButton(text=f'⏪Специальные ссылки', callback_data=f'urls:back')
                    klava.add(but)

                    if user.userLastZarabotal < 0:
                        user.userLastZarabotal = 0

                    await DB.add_parter_pay(user.userForPay, summ_opl, comment, user.userLastZarabotal)
                    user.userForPay = 0
                    user.userLastZarabotal = 0

                    await send_message(message.chat.id, f'✅Выплата успешно добавлена!', reply_markup=klava)
            except:
                await Print_Error()
                await send_message(user_id, '🛑Не верный формат записи выплаты!')
            user.bot_status = 0

        elif user.bot_status == 3: # Изменение кол-во дней ключа пользователя
            if not str(message.text.split('.')[0]).strip().replace(' ', '').isdigit():
                user.bot_status = 0
                return await message_input(message)

            days = int(str(message.text.split('.')[0]).strip().replace(' ', ''))

            if user.last_select_user_index != 0 and user.keyForChange != '':
                if 1 <= days <= 1000:
                    bot_key = user.keyForChange
                    await DB.set_day_qr_key_in_DB(bot_key, days)

                    # изменить кол-во дней в панели 3X-UI, если protocol='vless'
                    await change_days_vless(bot_key, days)

                    await send_message(message.chat.id, f'✅Кол-во изначальных дней ключа {user.keyForChange} успешно изменено на {days} {await dney(days)}!')
                    user.bot_status = 1
                    user.keyForChange = ''
                    await message_input(message, alt_text=f'{user.last_select_user_index}')
                else:
                    await send_message(message.chat.id, f'🛑Кол-во дней должно быть от 1 до 1000!')
            else:
                await send_message(message.chat.id, f'🛑Пользователь не выбран!')

        elif user.bot_status == 4: # Просмотр специальной ссылки
            result = await urls_call(call=None, cpec_code=message.text, message=message)
            if not result:
                user.bot_status = 0
                await message_input(message)

        elif user.bot_status == 5: # Изменение скидки клиентам
            try:
                summ = message.text.strip().replace(' ', '')

                if not summ.isdigit() or (summ.isdigit() and (int(summ) < 0 or int(summ) > 100)):
                    await send_message(user_id, '🛑Укажите процент скидки клиентам от 0 до 100!')
                    if not summ.isdigit():
                        user.bot_status = 0
                        await message_input(message)
                    return

                summ = int(summ)
                if user.userForPay != 0:
                    klava = InlineKeyboardMarkup()
                    but = InlineKeyboardButton(text=f'⏪Специальные ссылки', callback_data=f'urls:back')
                    klava.add(but)

                    await DB.update_spec_url_Discount_percentage(user.userForPay, summ)
                    user.userForPay = 0

                    await send_message(message.chat.id, f'✅Процент скидки клиентам успешно изменен на {summ}%', reply_markup=klava)
            except:
                await Print_Error()
                await send_message(user_id, '🛑Укажите процент скидки клиентам от 0 до 100!')
            user.bot_status = 0

        elif user.bot_status == 6: # Изменение процент заработка партнера
            try:
                summ = message.text.strip().replace(' ', '')
                cancel_text = '🛑Укажите процент заработка партнера от 1 до 100!'

                if not summ.isdigit() or (summ.isdigit() and (int(summ) < 1 or int(summ) > 100)):
                    await send_message(user_id, cancel_text)
                    if not summ.isdigit():
                        user.bot_status = 0
                        await message_input(message)
                    return

                summ = int(summ)
                if user.userForPay != 0:
                    klava = InlineKeyboardMarkup()
                    but = InlineKeyboardButton(text=f'⏪Специальные ссылки', callback_data=f'urls:back')
                    klava.add(but)

                    await DB.update_spec_url_percent_partner(user.userForPay, summ)
                    user.userForPay = 0

                    await send_message(message.chat.id, f'✅Процент заработка партнера успешно изменен на {summ}%', reply_markup=klava)
            except:
                await Print_Error()
                await send_message(user_id, cancel_text)
            user.bot_status = 0

        elif user.bot_status == 7: # Изменение название спец.ссылки
            try:
                name = message.text
                cancel_text = '🛑Данное название уже используется, укажите другое!'

                if user.userForPay != 0:
                    klava = InlineKeyboardMarkup()
                    but = InlineKeyboardButton(text=f'⏪Специальные ссылки', callback_data=f'urls:back')
                    klava.add(but)

                    res_ = await DB.update_spec_url_name(user.userForPay, name)
                    if not res_:
                        await send_message(user_id, cancel_text)
                        return

                    user.userForPay = 0
                    await send_message(message.chat.id, f'✅Название спец.ссылки успешно изменено на <b>{name}</b>!', reply_markup=klava)
            except:
                await Print_Error()
            user.bot_status = 0

        elif user.bot_status == 8: # Изменение макс. кол-во ключей для сервера 
            if not str(message.text.split('.')[0]).strip().replace(' ', '').isdigit():
                user.bot_status = 0
                return await message_input(message)

            index = int(str(message.text.split('.')[0]).strip().replace(' ', ''))

            if user.keyForChange != '':
                if 1 <= index <= 240:
                    ip = user.keyForChange
                    await DB.UPDATE_SERVER(ip, index)

                    await send_message(message.chat.id, f'✅Максимальное кол-во ключей для сервера <b>{ip}</b> успешно изменено на <b>{index}</b>!')
                    user.bot_status = 0
                    user.keyForChange = ''
                    await servers_edit(ip=ip, message=message)
                else:
                    await send_message(message.chat.id, f'🛑Максимальное кол-во ключей для сервера <b>от 1 до 240</b>!')
            else:
                await send_message(message.chat.id, f'🛑Сервер не найден!')

        elif user.bot_status == 9: # Создание запроса на вывод -> Ввод суммы
            if not str(message.text.split('.')[0]).strip().replace(' ', '').isdigit():
                user.bot_status = 0
                await message_input(message)
                return

            summ_client = int(str(message.text.split('.')[0]).strip().replace(' ', ''))
            logger.debug(f'{user_id} - Создание запроса на вывод -> Ввод суммы: {summ_client}')

            data = await DB.get_all_zaprosi(user_id)
            summ_zapros_wait_and_pay = 0
            if not data is None and len(data) > 0:
                for zapros in data:
                    summ_zapros = zapros[2]
                    status_zapros = zapros[4] # 0 - Wait, 1 - Done, 2 - Cancel
                    if status_zapros in (0, 1):
                        summ_zapros_wait_and_pay += summ_zapros

            data_promo = await DB.get_stats_promoses(user_id=user_id)
            summ_zarabotal_partner = 0

            if not data_promo is None and len(data_promo) > 0:
                if not data_promo[0] is None and len(data_promo[0]) > 0 and not data_promo[0][0] is None:
                    for i in data_promo:
                        id_partner = i[2]
                        if id_partner == user_id:
                            code = i[0]
                            percatage = i[1]
                            percent_partner = i[3]
                            count = i[4] if not i[4] is None else 0
                            summ = i[5] if not i[5] is None else 0
                            count_probniy = i[6] if not i[6] is None else 0

                            resu = await DB.get_user_operations(code)
                            resu1 = await DB.get_user_operations(code, 'prodl')
                            resu2 = await DB.get_user_operations(code, 'buy')
                            resu3 = await DB.get_user_operations(code, 'promo', da=True)
                            last_dolg = await DB.get_parter_pay(id_partner)

                            if not last_dolg is None and len(last_dolg) > 0:
                                last_dolg_date = datetime.strptime(last_dolg[-1][1], "%Y-%m-%d %H:%M:%S.%f")
                                last_dolg = last_dolg[-1][4]
                            else:
                                last_dolg = 0
                                last_dolg_date = None

                            # Считаем сумму продлений
                            total_prodl_summ = 0
                            new_prodl_summ = 0

                            for res in resu1:
                                total_summ = res[0]
                                date_ = res[1]
                                total_prodl_summ += total_summ

                                if not last_dolg_date is None and datetime.strptime(date_, "%Y-%m-%d %H:%M:%S.%f") < last_dolg_date:
                                    continue
                                
                                new_prodl_summ += total_summ

                            # Считаем сумму покупок
                            total_buy_summ = 0
                            new_buy_summ = 0

                            for res in resu2:
                                total_summ = res[0]
                                date_ = res[1]
                                total_buy_summ += total_summ

                                if not last_dolg_date is None and datetime.strptime(date_, "%Y-%m-%d %H:%M:%S.%f") < last_dolg_date:
                                    continue
                                
                                new_buy_summ += total_summ

                            if percatage == 0:
                                # Считаем сумму промокодов
                                total_promo_summ = 0
                                new_promo_summ = 0

                                for res in resu3:
                                    total_summ = res[0]
                                    date_ = res[1]
                                    total_promo_summ += total_summ

                                    if not last_dolg_date is None and datetime.strptime(date_, "%Y-%m-%d %H:%M:%S.%f") < last_dolg_date:
                                        continue
                                    
                                    new_promo_summ += total_summ  
                            else:
                                new_promo_summ = 0
                                total_promo_summ = 0
                            
                            # Считаем промокоды 
                            data_30 = None
                            data_90 = None
                            data_180 = None
                            data_365 = None

                            for res in resu:
                                days = res[0]
                                count_users_code = res[1]
                                total_summ = res[2]

                                if days == 30:
                                    data_30 = (count_users_code, total_summ)
                                elif days == 90:
                                    data_90 = (count_users_code, total_summ)
                                elif days == 180:
                                    data_180 = (count_users_code, total_summ)
                                elif days == 365:
                                    data_365 = (count_users_code, total_summ)

                            summ_zarabotal_partner = (total_buy_summ + total_prodl_summ  + total_promo_summ) * percent_partner / 100

            # посчитать сумму, на которую можно сделать запрос (партнер заработал - (запросы в статусе ожидания + выполненные))
            summ_zarabotal_partner = int(summ_zarabotal_partner)
            summ_zapros_wait_and_pay = int(summ_zapros_wait_and_pay)
            summ_zapros = summ_zarabotal_partner - summ_zapros_wait_and_pay
            
            logger.debug(f'{user_id} - summ_zarabotal_partner: {summ_zarabotal_partner}')
            logger.debug(f'{user_id} - summ_zapros_wait_and_pay: {summ_zapros_wait_and_pay}')
            logger.debug(f'{user_id} - summ_zapros: {summ_zapros}')

            # summ_zarabotal_partner = 17744
            # summ_zapros_wait_and_pay = 33000
            # summ_zapros = -15256

            if summ_zarabotal_partner >= SUMM_VIVOD:
                if summ_zapros >= SUMM_VIVOD:
                    if summ_zapros >= summ_client:
                        user.summ_vivod = summ_client
                        user.summ_dolg = summ_zapros
                        user.bot_status = 10
                        # осталось ввести комментарий, а именно номер карты и имя получателя
                        await send_message(user_id, user.lang.get('tx_zapros_add_comment'))
                        logger.debug(f'{user_id} - Ввод суммы для вывода')
                    else:
                        await send_message(user_id, user.lang.get('tx_zapros_max_summ').format(summ=summ_zapros))
                        logger.debug(f'{user_id} - Превышена сумма для вывода')
                else:
                    await send_message(user_id, user.lang.get('tx_zapros_no_summ'), reply_markup=await fun_klav_zaprosi(user))
                    logger.debug(f'{user_id} - Недостаточно средств для вывода')
            else:
                await send_message(user_id, user.lang.get('tx_zapros_no_summ'), reply_markup=await fun_klav_zaprosi(user))
                logger.debug(f'{user_id} - Недостаточно средств для вывода')

        elif user.bot_status == 10: # Создание запроса на вывод -> Ввод комментария
            if m_text in (user.lang.get('but_zaprosi_add'), user.lang.get('but_partner'), user.lang.get('but_main'), user.lang.get('but_zaprosi')):
                user.bot_status = 0
                return await message_input(message)

            comment = message.text
            if len(comment) > 150:
                return await send_message(user_id, user.lang.get('tx_zapros_comment'))

            if user.summ_vivod <= 0:
                return await send_message(user_id, user.lang.get('tx_zapros_no_summ'), reply_markup=await fun_klav_zaprosi(user))

            # if user.summ_vivod <= SUMM_VIVOD:
            #     return await send_message(user_id, user.lang.get('tx_zapros_min_summ').format(summ=SUMM_VIVOD))

            await DB.add_zapros(user_id, user.summ_vivod, comment, user.summ_dolg)

            await send_message(user_id, user.lang.get('tx_partner_pay_zapros_add').format(summ=user.summ_vivod), reply_markup=await fun_klav_partner(user))
            # text_send = (
            #     f'💰Сумма: <b>{user.summ_vivod}</b>\n'
            #     f'💬Комментарий: <b>{comment}</b>\n'
            #     f'🪙Текущий долг клиенту: <b>{user.summ_dolg}</b>'
            # )
            # await sendAdmins(user_id, f'💸Добавил запрос на выплату', text_send)
            user.summ_vivod = 0
            user.bot_status = 0

        elif user.bot_status == 11: # Изменение название локации для сервера 
            location = message.text.strip()

            if user.keyForChange != '':
                if len(location) <= 30:
                    # назание локации для сервера
                    ip = user.keyForChange
                    await DB.UPDATE_SERVER_LOCATION(ip, location)

                    await send_message(message.chat.id, f'✅Название локации для сервера <b>{ip}</b> успешно изменено на <b>{location}</b>!')
                    user.bot_status = 0
                    user.keyForChange = ''
                    await servers_edit(ip=ip, message=message)
                else:
                    await send_message(message.chat.id, f'🛑Максимальное кол-во символов для названия сервера <b>30</b>, у вас <b>{len(location)}</b>!')
            else:
                await send_message(message.chat.id, f'🛑Сервер не найден!')

        elif user.bot_status == 12: # Изменение название пакета подписок 
            name = message.text.strip()

            if user.keyForChange != '':
                if len(name) <= 30:
                    # назание пакета подписок
                    id = int(user.keyForChange)
                    await DB.update_name_podpiska(id, name)

                    await send_message(message.chat.id, f'✅Название пакета подписок успешно изменено на <b>{name}</b>!')
                    user.bot_status = 0
                    user.keyForChange = ''
                    await podpiska_call(id=id, message=message)
                else:
                    await send_message(message.chat.id, f'🛑Максимальное кол-во символов для названия пакета подписок <b>30</b>, у вас <b>{len(name)}</b>!')
            else:
                await send_message(message.chat.id, f'🛑Пакет подписок не найден!')

        elif user.bot_status == 13: # Добавление пакета подписок: Ввод названия
            name = message.text.strip()
            if len(name) <= 30:
                await send_message(message.chat.id, f'✅Название пакета подписок успешно принято!\n\nℹ️Далее отправьте id каналов/групп, пригласительные ссылки и названия через пробел, каждую с новой строки.\nУзнать id канала можно переслав сообщение из канала в @getmyid_bot, для того, чтобы узнать id группы, достаточно добавить бота в нее и бот пришлет сообщение всем администратом в боте, где будет id и название\n\n<i>Пример:\n-12312313 https://t.me/+u-I-zOBdosSwOGM Первая группа\n-43434343 https://t.me/+_6v8aXOBOd8zYzgy Вторая группа</i>:')
                user.bot_status = 14
                user.yookassa_api_key = name
            else:
                await send_message(message.chat.id, f'🛑Не верное название пакета подписок! (/podpiski)')
                user.bot_status = 0

        elif user.bot_status == 14: # Добавление пакета подписок: Ввод id каналов/групп
            channels = message.text.strip()
            if len(channels.split()) > 2 and '-' in channels.split()[0]:
                await DB.add_podpiska(user.yookassa_api_key, channels)
                user.yookassa_api_key = ''
                user_dict = {}
                await send_message(message.chat.id, f'✅Пакет подписок <b>{user.yookassa_api_key}</b> успешно добавлен!\n\nℹ️Для просмотра всех, перейдите в /podpiski')
            else:
                await send_message(message.chat.id, f'🛑Не верный список id каналов/групп! (/podpiski)')
                user.bot_status = 0

        elif user.bot_status == 15: # Изменение сумму следующего списания у ключа
            if not str(message.text.split('.')[0]).strip().replace(' ', '').isdigit():
                user.bot_status = 0
                return await message_input(message)

            summ = int(str(message.text.split('.')[0]).strip().replace(' ', ''))

            if user.last_select_user_index != 0 and user.keyForChange != '':
                if 1 <= summ <= 1000:
                    bot_key = user.keyForChange
                    await DB.set_summ_qr_key_in_DB(bot_key, summ)

                    await send_message(message.chat.id, f'✅Сумма следующего списания у ключа <b>{user.keyForChange}</b> успешно изменено на <b>{summ}₽</b>')
                    user.bot_status = 1
                    user.keyForChange = ''
                    await message_input(message, alt_text=f'{user.last_select_user_index}')
                else:
                    await send_message(message.chat.id, f'🛑Сумма следующего списания должна быть от 1 до 1000!')
            else:
                await send_message(message.chat.id, f'🛑Пользователь не выбран!')

        elif user.bot_status == 16: # Изменение индивидуальных тарифов пользователя
            usl = m_text.split('/')
            if len(usl) != 4:
                user.bot_status = 0
                return await message_input(message)

            tarif_1 = 0
            tarif_3 = 0
            tarif_6 = 0
            tarif_12 = 0
            for index, i in enumerate(usl):
                if not i.isdigit() or int(i) < 0:
                    return await send_message(message.chat.id, f'🛑Не верный формат записи тарифов!')

                if index == 0:
                    tarif_1 = int(i)
                elif index == 1:
                    tarif_3 = int(i)
                elif index == 2:
                    tarif_6 = int(i)
                elif index == 3:
                    tarif_12 = int(i)

            if (tarif_1 != 0 and tarif_3 != 0 and tarif_1 >= tarif_3) or (tarif_3 != 0 and tarif_6 != 0 and tarif_3 >= tarif_6) or (tarif_6 != 0 and tarif_12 != 0 and tarif_6 >= tarif_12):
                return await send_message(message.chat.id, f'🛑Каждый следующий тариф должен быть дороже предыдущего!')

            tarifs = f'{tarif_1}/{tarif_3}/{tarif_6}/{tarif_12}'
            await DB.set_tarifs_user(user.user_for_change, tarifs)
            await send_message(message.chat.id, f'✅Индивидуальные тарифы успешно изменены на 1/3/6/12: <b>{tarifs}</b>!')
            user.bot_status = 0

        elif user.bot_status == 31: # Ю.Money: Ввод CLIENT_ID
            client_id = message.text.strip()

            if len(client_id) >= 40:
                text_send = (
                    f'✅Идентификатор приложения (client_id) успешно принят!\n\n'
                    'ℹ️Далее необходимо:\n\n'
                    '1.<b>Перейти</b> по ссылке ниже 👇\n'
                    '2.<b>Подтвердить</b>\n'
                    '3.Далее <b>вас перебросит в бота</b>, необходимо <b>вернуться в браузер</b>\n'
                    '4.<b>Скопировать ссылку</b>, на которую вас перебросило\n'
                    '5.И <b>отправить эту ссылку боту</b>:'
                )
                await send_message(message.chat.id, text_send)
                user.bot_status = 32
                user.yoomoney_client_id = client_id
                await send_message(message.chat.id, f'{await YPay.urlForToken(client_id)}')
            else:
                await send_message(message.chat.id, f'🛑Не верный CLIENT_ID! (/wallets)')
                user.bot_status = 0

        elif user.bot_status == 32: # Ю.Money: Ввод полученной ссылки
            if '?code=' in message.text:
                result = await YPay.getTokenForUrl(user.yoomoney_client_id, message.text.strip())
                if result[0]:
                    await DB.ADD_WALLET(PAY_METHODS.YOO_MONEY, result[1], user.yoomoney_client_id, f'https://t.me/{BOT_NICK.lower()}')
                    user.yoomoney_client_id = ''
                    user_dict = {}
                    await send_message(message.chat.id, f'✅Способ оплаты успешно добавлен!\n\nℹ️Для просмотра всех способов оплаты, перейдите в /wallets')
                else:
                    text_send = (
                        '🛑Была допущена ошибка, попробуйте еще раз заново /wallets '
                        '(<i>Идентификатор приложения (client_id) создавать заново не обязательно, '
                        'достаточно вернуться в начало и когда бот попросит, отправить его</i>)\n\n'
                        f'{result[1]}'
                    )
                    await send_message(message.chat.id, text_send)
                    user.bot_status = 0
            else:
                await send_message(message.chat.id, f'🛑Не верная ссылка! (/wallets)')
            user.bot_status = 0

        elif user.bot_status == 35: # Ю.Касса: Ввод API ключа
            api_key = message.text.strip()

            if len(api_key) >= 15:
                await send_message(message.chat.id, f'✅API ключ успешно принят!\n\nℹ️Далее отправьте shopId (только число) (<i>Пример: 432441</i>):')
                user.bot_status = 36
                user.yookassa_api_key = api_key
            else:
                await send_message(message.chat.id, f'🛑Не верный API ключ! (/wallets)')
                user.bot_status = 0

        elif user.bot_status == 36: # Ю.Касса: Ввод shopId
            if str(message.text.split('.')[0]).strip().replace(' ', '').isdigit():
                await send_message(message.chat.id, f'✅shopId успешно принят!\n\nℹ️Далее отправьте почту (для получения чеков):')
                user.bot_status = 37
                user.yookassa_shopId = str(message.text.split('.')[0]).strip().replace(' ', '')
            else:
                await send_message(message.chat.id, f'🛑Не верный shopId! (/wallets)')
                user.bot_status = 0

        elif user.bot_status == 37: # Ю.Касса: Ввод e-mail
            if '@' in message.text:
                await DB.ADD_WALLET(PAY_METHODS.YOO_KASSA, user.yookassa_api_key, user.yookassa_shopId, message.text.strip())
                user.yookassa_api_key = ''
                user.yookassa_shopId = ''
                user_dict = {}
                await send_message(message.chat.id, f'✅Способ оплаты успешно добавлен!\n\nℹ️Для просмотра всех способов оплаты, перейдите в /wallets')
            else:
                await send_message(message.chat.id, f'🛑Не верный e-mail! (/wallets)')
            user.bot_status = 0

        elif user.bot_status == 45: # Tinkoff Pay: Ввод номере терминала
            api_key = message.text.strip()

            if len(api_key) >= 10:
                await send_message(message.chat.id, f'✅Номер терминала успешно принят!\n\nℹ️Далее отправьте пароль (<i>Пример: 123dhg3rg3ybdj4</i>):')
                user.bot_status = 46
                user.yookassa_api_key = api_key
            else:
                await send_message(message.chat.id, f'🛑Не верный номер терминала! (/wallets)')
                user.bot_status = 0

        elif user.bot_status == 46: # Tinkoff Pay: Ввод пароля
            password = message.text.strip()

            if len(password) >= 8:
                await send_message(message.chat.id, f'✅Пароль успешно принят!\n\nℹ️Далее отправьте почту (для получения чеков):')
                user.bot_status = 47
                user.yookassa_shopId = password
            else:
                await send_message(message.chat.id, f'🛑Не верный пароль! (/wallets)')
                user.bot_status = 0

        elif user.bot_status == 47: # Tinkoff Pay: Ввод e-mail
            if '@' in message.text:
                await DB.ADD_WALLET(PAY_METHODS.TINKOFF, user.yookassa_api_key, user.yookassa_shopId, message.text.strip())
                user.yookassa_api_key = ''
                user.yookassa_shopId = ''
                user_dict = {}
                await send_message(message.chat.id, f'✅Способ оплаты успешно добавлен!\n\nℹ️Для просмотра всех способов оплаты, перейдите в /wallets')
            else:
                await send_message(message.chat.id, f'🛑Не верный e-mail! (/wallets)')
            user.bot_status = 0

        elif user.bot_status == 48: # Lava Pay: Ввод API_Key
            api_key = message.text.strip()

            if len(api_key) >= 25:
                await send_message(message.chat.id, f'✅API ключ успешно принят!\n\nℹ️Далее отправьте Shop_ID (<i>Пример: dadwa3qe-1234-dad2-1291d-123454faf3eh</i>):')
                user.bot_status = 49
                user.yookassa_api_key = api_key
            else:
                await send_message(message.chat.id, f'🛑Не верный номер API ключ! (/wallets)')
                user.bot_status = 0

        elif user.bot_status == 49: # Lava Pay: Ввод Shop_ID
            shop_id = message.text.strip()

            if len(shop_id) >= 20:
                await send_message(message.chat.id, f'✅Shop_ID успешно принят!\n\nℹ️Далее секретный ключ Secret_Key:')
                user.bot_status = 50
                user.yookassa_shopId = shop_id
            else:
                await send_message(message.chat.id, f'🛑Не верный пароль! (/wallets)')
                user.bot_status = 0

        elif user.bot_status == 50: # Lava Pay: Ввод Secret_Key
            secret_key = message.text.strip()

            if len(secret_key) >= 20:
                await DB.ADD_WALLET(PAY_METHODS.LAVA, user.yookassa_api_key, user.yookassa_shopId, secret_key)
                user.yookassa_api_key = ''
                user.yookassa_shopId = ''
                user_dict = {}
                await send_message(message.chat.id, f'✅Способ оплаты успешно добавлен!\n\nℹ️Для просмотра всех способов оплаты, перейдите в /wallets')
            else:
                await send_message(message.chat.id, f'🛑Не верный секретный ключ (Secret_Key)! (/wallets)')
            user.bot_status = 0

        elif user.bot_status == 51: # Cryptomus: Ввод API_Key
            api_key = message.text.strip()

            if len(api_key) >= 100:
                await send_message(message.chat.id, f'✅API ключ успешно принят!\n\nℹ️Далее отправьте Merchant_ID (<i>Пример: dadwa3qe-1234-dad2-1291d-123454faf3eh</i>):')
                user.bot_status = 52
                user.yookassa_api_key = api_key
            else:
                await send_message(message.chat.id, f'🛑Не верный номер API ключ! (/wallets)')
                user.bot_status = 0

        elif user.bot_status == 52: # Cryptomus: Ввод Merchant_id
            shop_id = message.text.strip()

            if len(shop_id) >= 30:
                await DB.ADD_WALLET(PAY_METHODS.CRYPTOMUS, user.yookassa_api_key, shop_id, '')
                user.yookassa_api_key = ''
                user.yookassa_shopId = ''
                user_dict = {}
                await send_message(message.chat.id, f'✅Способ оплаты успешно добавлен!\n\nℹ️Для просмотра всех способов оплаты, перейдите в /wallets')
            else:
                await send_message(message.chat.id, f'🛑Не верный shop_id! (/wallets)')
                user.bot_status = 0
        
        elif user.bot_status == 53: # Wallet Pay: Ввод API_Key
            api_key = message.text.strip()

            if len(api_key) >= 30:
                await DB.ADD_WALLET(PAY_METHODS.WALLET_PAY, api_key, '', '')
                user.yookassa_api_key = ''
                user.yookassa_shopId = ''
                user_dict = {}
                await send_message(message.chat.id, f'✅Способ оплаты успешно добавлен!\n\nℹ️Для просмотра всех способов оплаты, перейдите в /wallets')
            else:
                await send_message(message.chat.id, f'🛑Не верный API_Key! (/wallets)')
                user.bot_status = 0

        elif user.bot_status == 54: # Soft Pay: Ввод API_Key
            api_key = message.text.strip()

            if len(api_key) >= 30:
                await DB.ADD_WALLET(PAY_METHODS.SOFT_PAY, api_key, '', '')
                user.yookassa_api_key = ''
                user.yookassa_shopId = ''
                user_dict = {}
                await send_message(message.chat.id, f'✅Способ оплаты успешно добавлен!\n\nℹ️Для просмотра всех способов оплаты, перейдите в /wallets')
            else:
                await send_message(message.chat.id, f'🛑Не верный API_Key! (/wallets)')
                user.bot_status = 0

        elif user.bot_status == 55: # Payok: Ввод API_Key
            api_key = message.text.strip()

            if len(api_key) >= 50:
                await send_message(message.chat.id, f'✅API ключ успешно принят!\n\nℹ️Далее отправьте API_ID (<i>Пример: 5555</i>):')
                user.bot_status = 56
                user.payok_api_key = api_key
            else:
                await send_message(message.chat.id, f'🛑Не верный API ключ! (/wallets)')
                user.bot_status = 0

        elif user.bot_status == 56: # Payok: Ввод API_ID
            api_id = message.text.strip()

            try:
                int(api_id)
                user.bot_status = 57
                user.payok_api_id = api_id
                await send_message(message.chat.id, f'✅API_ID успешно принят!\n\nℹ️Далее отправьте ID_MAGAZIN (<i>Пример: 44444</i>):')
            except:
                await send_message(message.chat.id, f'🛑Не верный api_id! (/wallets)')
                user.bot_status = 0

        elif user.bot_status == 57: # Payok: Ввод ID_MAGAZIN
            id_magazin = message.text.strip()

            try:
                int(id_magazin)
                user.bot_status = 58
                user.payok_id_magazin = id_magazin
                await send_message(message.chat.id, f'✅ID_MAGAZIN успешно принят!\n\nℹ️Далее отправьте SECRET_KEY (<i>Пример: il83b901a5f209d44bcev4g384fba8hf</i>):')
            except:
                await send_message(message.chat.id, f'🛑Не верный id_magazin! (/wallets)')
                user.bot_status = 0

        elif user.bot_status == 58: # Payok: Ввод SECRET_KEY
            secret_key = message.text.strip()

            if len(secret_key) >= 20:
                temp = f'{user.payok_api_id}:{user.payok_id_magazin}'
                await DB.ADD_WALLET(PAY_METHODS.PAYOK, user.payok_api_key, temp, secret_key)
                user.payok_api_key = ''
                user.payok_api_id = ''
                user.payok_id_magazin = ''
                
                user_dict = {}
                await send_message(message.chat.id, f'✅Способ оплаты успешно добавлен!\n\nℹ️Для просмотра всех способов оплаты, перейдите в /wallets')
            else:
                await send_message(message.chat.id, f'🛑Не верный secret_key! (/wallets)')
                user.bot_status = 0

        elif user.bot_status == 59: # Aaio: Ввод API_Key
            api_key = message.text.strip()

            if len(api_key) >= 50:
                await send_message(message.chat.id, f'✅API ключ успешно принят!\n\nℹ️Далее отправьте SHOP_ID (<i>Пример: 2hdcfaa5-1f93-2b78-lgbb-a4hjdhj8d2ffe</i>):')
                user.bot_status = 60
                user.aaio_api_key = api_key
            else:
                await send_message(message.chat.id, f'🛑Не верный API ключ! (/wallets)')
                user.bot_status = 0

        elif user.bot_status == 60: # Aaio: Ввод SHOP_ID
            shop_id = message.text.strip()

            try:
                user.bot_status = 61
                user.aaio_shop_id = shop_id
                await send_message(message.chat.id, f'✅SHOP_ID успешно принят!\n\nℹ️Далее отправьте SECRET_KEY_1 (<i>Пример: w47bhbh3jc9k5ej9add770bg8945694g</i>):')
            except:
                await send_message(message.chat.id, f'🛑Не верный shop_id! (/wallets)')
                user.bot_status = 0

        elif user.bot_status == 61: # Aaio: Ввод SECRET_KEY_1
            secret_key_1 = message.text.strip()

            try:
                user.bot_status = 62
                user.aaio_secret_key_1 = secret_key_1
                await send_message(message.chat.id, f'✅SECRET_KEY_1 успешно принят!\n\nℹ️Далее отправьте почту (<i>Пример: coden@vpcoden.ru</i>):')
            except:
                await send_message(message.chat.id, f'🛑Не верный secret_key_1! (/wallets)')
                user.bot_status = 0

        elif user.bot_status == 62: # Aaio: Ввод почты
            email = message.text.strip()

            if '@' in email and '.' in email:
                temp = f'{user.aaio_shop_id}:{user.aaio_secret_key_1}'
                await DB.ADD_WALLET(PAY_METHODS.AAIO, user.aaio_api_key, temp, email)
                user.aaio_api_key = ''
                user.aaio_shop_id = ''
                user.aaio_secret_key_1 = ''
                
                user_dict = {}
                await send_message(message.chat.id, f'✅Способ оплаты успешно добавлен!\n\nℹ️Для просмотра всех способов оплаты, перейдите в /wallets')
            else:
                await send_message(message.chat.id, f'🛑Не верная почта! (/wallets)')
            user.bot_status = 0

        elif user.bot_status == 63: # RootPay: Ввод API_KEY
            api_key = message.text.strip()

            if len(api_key) > 5:
                await DB.ADD_WALLET(PAY_METHODS.ROOT_PAY, api_key, '', '')
                
                user_dict = {}
                await send_message(message.chat.id, f'✅Способ оплаты успешно добавлен!\n\nℹ️Для просмотра всех способов оплаты, перейдите в /wallets')
            else:
                await send_message(message.chat.id, f'🛑Не верный API_KEY! (/wallets)')
            user.bot_status = 0

        elif user.bot_status == 64: # FreeKassa: Ввод API_Key
            api_key = message.text.strip()

            if len(api_key) >= 25:
                await send_message(message.chat.id, f'✅API ключ успешно принят!\n\nℹ️Далее отправьте ShopID (<i>Пример: 24569</i>):')
                user.bot_status = 65
                user.yookassa_api_key = api_key
            else:
                await send_message(message.chat.id, f'🛑Не верный номер API ключ! (/wallets)')
                user.bot_status = 0

        elif user.bot_status == 65: # FreeKassa: Ввод Shop_ID
            shop_id = message.text.strip()

            if len(shop_id) >= 4:
                await DB.ADD_WALLET(PAY_METHODS.FREE_KASSA, user.yookassa_api_key, shop_id, '')
                user.yookassa_api_key = ''
                user.yookassa_shopId = ''
                user_dict = {}
                await send_message(message.chat.id, f'✅Способ оплаты успешно добавлен!\n\nℹ️Для просмотра всех способов оплаты, перейдите в /wallets')
            else:
                await send_message(message.chat.id, f'🛑Не верный shop_id! (/wallets)')
                user.bot_status = 0

        elif user.bot_status == 66: # CardLink: Ввод API_Key
            api_key = message.text.strip()

            if len(api_key) >= 25:
                await send_message(message.chat.id, f'✅API ключ успешно принят!\n\nℹ️Далее отправьте ShopID (<i>Пример: FB254Gj2JL</i>):')
                user.bot_status = 67
                user.yookassa_api_key = api_key
            else:
                await send_message(message.chat.id, f'🛑Не верный номер API ключ! (/wallets)')
                user.bot_status = 0

        elif user.bot_status == 67: # CardLink: Ввод Shop_ID
            shop_id = message.text.strip()

            if len(shop_id) >= 8:
                await DB.ADD_WALLET(PAY_METHODS.CARDLINK, user.yookassa_api_key, shop_id, '')
                user.yookassa_api_key = ''
                user.yookassa_shopId = ''
                user_dict = {}
                await send_message(message.chat.id, f'✅Способ оплаты успешно добавлен!\n\nℹ️Для просмотра всех способов оплаты, перейдите в /wallets')
            else:
                await send_message(message.chat.id, f'🛑Не верный shop_id! (/wallets)')
                user.bot_status = 0

        elif m_text == user.lang.get('but_connect') or m_text == user.lang.get('but_back_main'):
            await buy_message(user_id=user_id)
            user.isPayChangeProtocol = False
            user.isPayChangeLocations = False

        elif user.lang.get('but_instagram') != '' and m_text == user.lang.get('but_instagram'):
            await send_message(user_id, user.lang.get('tx_instagram').format(url=URL_INSTAGRAM), reply_markup=await fun_klav_desription(user, user.lang.get('but_instagram')))

        elif m_text == user.lang.get('but_change_protocol'):
            await get_user_keys(user_id, change_protocol=True)

        elif m_text == user.lang.get('but_change_location'):
            if len(SERVERS) > 1:
                await get_user_keys(user_id, change_location=True)

        elif m_text == user.lang.get('but_how_podkl'):
            res = await DB.get_user_nick_and_ustrv(user_id)
            if res is None:
                res = ('nick', 2, 'User')
            first_name = res[2]

            # Так как только VLESS включён, сразу отправляем инструкцию для VLESS
            await send_message(user_id, user.lang.get('tx_how_install').format(name=first_name), reply_markup=await fun_klav_podkl(user, user.buttons_podkl_vless))

            klava = InlineKeyboardMarkup()
            klava.add(InlineKeyboardButton(text=user.lang.get('but_connect'), callback_data=f'buttons:but_connect'))
            await send_message(user_id, user.lang.get('tx_how_install_info').format(but=user.lang.get('but_connect')), reply_markup=klava)

        elif m_text == user.lang.get('but_how_podkl_vless'):
            res = await DB.get_user_nick_and_ustrv(user_id)
            if res is None:
                res = ('nick', 2, 'User')
            first_name = res[2]
            await send_message(user_id, user.lang.get('tx_how_install').format(name=first_name), reply_markup=await fun_klav_podkl(user, user.buttons_podkl_vless))

        elif m_text == user.lang.get('but_how_podkl_pptp'):
            await send_message(user_id, user.lang.get('instr_pptp').format(my_keys=user.lang.get('but_my_keys')), reply_markup=await fun_klav_how_install(user, HELP_VLESS, HELP_WIREGUARD, HELP_OUTLINE, HELP_PPTP))

        elif m_text == user.lang.get('but_no_work_bot'):
            await send_message(user_id, user.lang.get('tx_not_work_bot').format(name=message.chat.first_name, nick_help=NICK_HELP), reply_markup=await fun_klav_help(user))

        elif m_text == user.lang.get('but_manager'):
            await send_message(user_id, user.lang.get('tx_manager').format(nick_help=NICK_HELP), reply_markup=await fun_klav_help(user))

        elif m_text == user.lang.get('but_my_keys'):
            await get_user_keys(user_id)

        elif m_text == user.lang.get('but_obesh'):
            if OBESH_PLATEZH:
                # Проверить, активировал ли клиент за последние 30 дней эту функцию
                data = await DB.get_user_nick_and_ustrv(message.chat.id)
                if not data is None and len(data) > 0:
                    date = data[4]
                    if not date is None:
                        if '.' in date:
                            date_time = datetime.strptime(date, "%Y-%m-%d %H:%M:%S.%f")
                        else:
                            date_time = datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
                        now = datetime.now()
                        usl = (now - date_time) >= timedelta(days=30)
                    else:
                        usl = True

                    if usl:
                        data = await DB.get_user_keys(message.chat.id)

                        if not data is None and len(data) > 0:
                            await DB.set_user_date_obesh(message.chat.id)
                            await DB.update_qr_keys_add_1_day(message.chat.id)
                            await send_message(message.chat.id, user.lang.get('tx_obesh_select'))

                            for bot_key in data:
                                conf_name = bot_key[0]
                                ip_server = bot_key[5]
                                protocol = bot_key[7]
                                await KEYS_ACTIONS.activateKey(protocol, conf_name, ip_server, message.chat.id, days=2)

                            if not IS_OTCHET:
                                await send_admins(user_id, f'Обещанный платеж')
                            await DB.add_otchet('get_obesh')
                        else:
                            await send_message(message.chat.id, user.lang.get('tx_obesh_no_find_keys'))  
                    else:
                        await send_message(message.chat.id, user.lang.get('tx_obesh_period'))
                else:
                    await send_message(message.chat.id, user.lang.get('tx_obesh_user_error'))

        elif user.lang.get('but_polz_sogl') and m_text == user.lang.get('but_polz_sogl') and SOGL_FILE != '':
            if SOGL_FILE != '':
                await send_cached_file(user_id, SOGL_FILE)

        elif m_text == user.lang.get('but_help_android_WG'):  # Помощь
            await help(user_id, 1, 'wireguard')

        elif m_text == user.lang.get('but_help_ios_WG'):  # Помощь
            await help(user_id, 2, 'wireguard')

        elif m_text == user.lang.get('but_help_windows_WG'):  # Помощь
            await help(user_id, 3, 'wireguard')

        elif m_text == user.lang.get('but_help_android_Outline'):  # Помощь
            await help(user_id, 1, 'outline')

        elif m_text == user.lang.get('but_help_ios_Outline'):  # Помощь
            await help(user_id, 2, 'outline')

        elif m_text == user.lang.get('but_help_windows_Outline'):  # Помощь
            await help(user_id, 3, 'outline')

        elif m_text == user.lang.get('but_help_android_vless'):  # Помощь
            await help(user_id, 1, 'vless')

        elif m_text == user.lang.get('but_help_ios_vless'):  # Помощь
            await help(user_id, 2, 'vless')

        elif m_text == user.lang.get('but_help_macos_vless'):  # Помощь
            await help(user_id, 3, 'vless')
            
        elif m_text == user.lang.get('but_help_windows_vless'):  # Помощь
            await help(user_id, 4, 'vless')

        elif user.lang.get('but_1_month') in m_text or user.lang.get('but_3_month') in m_text or user.lang.get('but_6_month') in m_text or user.lang.get('but_12_month') in m_text:
            if OPLATA:
                if user.lang.get('but_1_month') in m_text:
                    days = 30
                elif user.lang.get('but_3_month') in m_text:
                    days = 90
                elif user.lang.get('but_6_month') in m_text:
                    days = 180
                elif user.lang.get('but_12_month') in m_text:
                    days = 365

                await DB.set_user_days_by_buy(message.chat.id, days)

                if user.isProdleniye:
                    # Если продление
                    user.bill_bot_key = f'{user.isProdleniye}'
                    user.isPayChangeProtocol = False
                    user.isPayChangeLocations = False
                    # Проверить кол-во активных WALLETS
                    if len([item for item in WALLETS if item['isActive']]) > 1:
                        user.PAY_WALLET = None
                    await pokupka(user)
                    user.isProdleniye = None
                else:
                    # Если создание нового ключа -> спросить какой протокол
                    user.bot_status = 21
                    await select_protocol(user_id)

        elif m_text in (user.lang.get('but_select_WG'), user.lang.get('but_select_Outline'), user.lang.get('but_select_vless'), user.lang.get('but_select_pptp')):
            if m_text == user.lang.get('but_select_WG'):
                user.Protocol = 'wireguard'
            elif m_text == user.lang.get('but_select_Outline'):
                user.Protocol = 'outline'
            elif m_text == user.lang.get('but_select_vless'):
                user.Protocol = 'vless'
            elif m_text == user.lang.get('but_select_pptp'):
                user.Protocol = 'pptp'

            logger.debug(f'Пользователь {user_id} выбрал протокол = {user.Protocol}, user.bot_status = {user.bot_status}')

            if user.bot_status == 20:
                # взять рандомный пакет, который активен
                data = await DB.get_podpiski() # p.id, p.Name, p.Channels, p.isOn, COUNT(q.Podpiska)
                p_id = None
                if data and len(data) > 0:
                    random.shuffle(data)
                    for paket in data:
                        p_isOn = bool(paket[3])
                        if p_isOn:
                            p_id = paket[0]
                            try:
                                p_channels_name = [' '.join(item.split(' ')[2:]) for item in paket[2].split('\n') if item != '']
                            except:
                                await Print_Error()
                                p_channels_name = None
                            p_channels_urls = [item.split(' ')[1] for item in paket[2].split('\n') if item != '']
                            break

                # проверить, чтобы у клиента не было активного ключа с таким пакетом
                keys_user = await DB.get_user_keys(user_id)
                if keys_user and len(keys_user) > 0:
                    for key in keys_user:
                        if key[11] == p_id and bool(key[6]):
                            return await send_message(user_id, user.lang.get('tx_podpiska_key_yes'))

                if p_id is None:
                    await send_message(user_id, user.lang.get('tx_podpiska_no'))
                else:
                    text_send = f"{user.lang.get('tx_podpiska_need_sub')}\n\n"
                    for index, channel in enumerate(p_channels_urls):
                        if p_channels_name:
                            name = p_channels_name[index]
                        else:
                            name = f'Канал №{index + 1}'
                        text_send += f'📢<a href="{channel}">{name}</a>\n'
                    klava = InlineKeyboardMarkup()
                    klava.add(InlineKeyboardButton(text=user.lang.get('tx_podpiska_check'), callback_data=f'check_sub:{user_id}:{p_id}'))
                    message_del = await send_message(user_id, text_send, reply_markup=klava)
                    user.message_del_id = message_del.message_id
            elif user.bot_status == 21:
                user.bill_bot_key = ''
                user.isPayChangeProtocol = False
                user.isPayChangeLocations = False
                if len([item for item in WALLETS if item['isActive']]) > 1:
                    user.PAY_WALLET = None
                await pokupka(user)
            elif user.bot_status == 22:
                if not (user.code in activated_promocodes and user_id == activated_promocodes[user.code]):
                    activated_promocodes[user.code] = user_id
                    await DB.set_activate_promo(user.code, message.chat.username if not message.chat.username is None else user_id, user_id, user.days_code)
                    await new_key(user_id, day=user.days_code, promo=user.code, help_message=True, protocol=user.Protocol)
                else:
                    return await send_message(user_id, user.lang.get('tx_promo_is_activate'))
            elif user.bot_status == 23:
                await new_key(user_id, day=365, is_Admin=1, help_message=True, protocol=user.Protocol)
            elif user.bot_status == 24:
                if not user_id in users_get_test_key:
                    users_get_test_key[user_id] = True
                    await new_key(user_id, day=COUNT_DAYS_TRIAL, help_message=True, protocol=user.Protocol)
                    await DB.set_user_get_test_key(user_id)
                    user.isGetTestKey = await DB.isGetTestKey_by_user(user_id)
                else:
                    return await send_message(user_id, user.lang.get('tx_test_key_no_get'))

            user.bot_status = 0

        elif m_text in (user.lang.get('but_yoomoney'), user.lang.get('but_yookassa'), user.lang.get('but_tinkoff'), user.lang.get('but_lava'), user.lang.get('but_cryptomus'), user.lang.get('but_walletpay'), user.lang.get('but_softpay'), user.lang.get('but_payok'), user.lang.get('but_aaio'), user.lang.get('but_rootpay'), user.lang.get('but_freekassa'), user.lang.get('but_stars'), user.lang.get('but_cardlink')):
            sopost = {
                user.lang.get('but_yoomoney'): PAY_METHODS.YOO_MONEY,
                user.lang.get('but_yookassa'): PAY_METHODS.YOO_KASSA,
                user.lang.get('but_tinkoff'): PAY_METHODS.TINKOFF,
                user.lang.get('but_lava'): PAY_METHODS.LAVA,
                user.lang.get('but_cryptomus'): PAY_METHODS.CRYPTOMUS,
                user.lang.get('but_walletpay'): PAY_METHODS.WALLET_PAY,
                user.lang.get('but_softpay'): PAY_METHODS.SOFT_PAY,
                user.lang.get('but_payok'): PAY_METHODS.PAYOK,
                user.lang.get('but_aaio'): PAY_METHODS.AAIO,
                user.lang.get('but_rootpay'): PAY_METHODS.ROOT_PAY,
                user.lang.get('but_freekassa'): PAY_METHODS.FREE_KASSA,
                user.lang.get('but_stars'): PAY_METHODS.XTR,
                user.lang.get('but_cardlink'): PAY_METHODS.CARDLINK,
            }

            select_title = sopost.get(m_text.strip(), None)
            user.PAY_WALLET = YPay(select_title=select_title)

            if user.payStatus == 1:
                await pokupka(user)
                user.payStatus = 0
            elif user.payStatus == 2:
                if user.donate_text:
                    await message_input(message, alt_text=user.donate_text)
                else:
                    await send_message(message.chat.id, user.lang.get('tx_bot_reboot'))
                user.payStatus = 0
            else:
                await send_message(user_id, user.lang.get('tx_pay_error'), reply_markup=user.klav_start)

        elif m_text == user.lang.get('but_new_key'):
            res__ = await DB.isGetTestKey_by_user(message.chat.id)
            if not res__:
                # Если у клиента нет ключей
                probniy = '\n\n' + user.lang.get('tx_buy_probniy').format(days_trial=COUNT_DAYS_TRIAL, dney_text=await dney(COUNT_DAYS_TRIAL, user))
            else:
                probniy = ''

            await send_message(user_id, user.lang.get('tx_buy_no_keys').format(text_1=probniy, text_2=user.lang.get('tx_prodlt_tarif')), reply_markup=user.klav_buy_days)
            user.isProdleniye = None

        elif m_text == user.lang.get('but_prodlit'):
            await get_user_keys(user_id, prodlit=True)

        elif m_text == user.lang.get('but_test_key'):
            if TEST_KEY:
                await test_key_get(user_id)

        elif m_text == user.lang.get('but_donate'):  # Пожертвование
            await send_message(user_id, user.lang.get('tx_donate_select').format(name=message.chat.first_name), reply_markup=await fun_klav_donats(user))
            await DB.add_otchet('call_donat')

        elif m_text == user.lang.get('but_opros_super'):  # Опрос
            await send_message(user_id, user.lang.get('tx_opros_super').format(name=message.chat.first_name))
            if DONATE_SYSTEM:
                await send_message(user_id, user.lang.get('tx_opros_super_donate'), reply_markup=await fun_klav_donats(user))
            if not IS_OTCHET:
                await send_admins(user_id, f"📋Опрос -> {user.lang.get('but_opros_super')}")
            await DB.add_otchet('opros_super')

        elif m_text == user.lang.get('but_opros_good'):  # Опрос
            await send_message(user_id, user.lang.get('tx_opros_good').format(name=message.chat.first_name, nick_help=NICK_HELP), reply_markup=user.klav_start)
            if not IS_OTCHET:
                await send_admins(user_id, f"Опрос -> {user.lang.get('but_opros_good')}")
            await DB.add_otchet('opros_dop')

        elif m_text == user.lang.get('but_main') or m_text == user.lang.get('but_cancel_pay'):
            await send_start_message(message)

        elif m_text == user.lang.get('but_help') or m_text == user.lang.get('but_back_help'):
            await help_message(message)

        elif m_text == user.lang.get('but_ref'):
            if REF_SYSTEM:
                logger.debug(f"Зашел в {user.lang.get('but_ref')}")
                url = f'https://t.me/{BOT_NICK}?start=ref{user_id}'
                url = f'https://telegram.me/share/url?url={url}'
                klava = InlineKeyboardMarkup()
                klava.add(InlineKeyboardButton(text=user.lang.get('but_ref_in_telegram'), url=url))
                if INLINE_MODE:
                    klava.add(InlineKeyboardButton(text=user.lang.get('but_main'), callback_data=f'buttons:but_main'))
                text_send = user.lang.get('tx_ref_description').format(name=message.chat.first_name, days=COUNT_DAYS_REF, dney_text=await dney(COUNT_DAYS_REF, user))
                count_refs = await DB.get_refs_user(user_id)
                if count_refs > 0:
                    dop_text = '\n\n' + user.lang.get('tx_ref_count_refs').format(count_refs=count_refs) + '\n\n'
                    text_send = text_send.replace('\n\n', dop_text)
                await send_message(user_id, text_send, reply_markup=klava)

        elif m_text.strip().lower() == user.lang.get('admin_promo'):
            if user.isAdmin:
                user.bot_status = 23
                await select_protocol(user_id)

        elif m_text == user.lang.get('but_why'):
            await send_message(user_id, user.lang.get('tx_why'), reply_markup=await fun_klav_desription(user, user.lang.get('but_instagram')))

        elif user.lang.get('but_desription').format(name_config=NAME_BOT_CONFIG) == message.text:
            photos = []
            try: photos.append(InputMediaPhoto(open(SCREEN_DOWNLOAD, 'rb')))
            except: pass
            try: photos.append(InputMediaPhoto(open(SCREEN_UPLOAD, 'rb')))
            except: pass
            try: await bot.send_media_group(user_id, photos)
            except: pass

            await send_message(user_id, user.lang.get('tx_description'))
            await send_message(user_id, user.lang.get('tx_description_connect').format(days=COUNT_DAYS_TRIAL, dney_text=await dney(COUNT_DAYS_TRIAL, user), nick_help=NICK_HELP), reply_markup=await fun_klav_desription(user, user.lang.get('but_instagram')))

        elif m_text == user.lang.get('but_reviews'):
            try:
                me = await send_message(user_id, user.lang.get('tx_load_video'))
                await bot.send_chat_action(user_id, ChatActions.UPLOAD_VIDEO)
                await send_cached_file(user_id, VIDEO_OTZIVI, type='video')
                await delete_message(chat_id=user_id, message_id=me.message_id)
            except Exception as e:
                logger.warning(f'Ошибка при отправке видео-отзыва: {e}')

        elif m_text == user.lang.get('but_change_language'):
            await change_language_call(message=message)

        elif m_text == user.lang.get('but_donaters'):
            text = user.lang.get('tx_donats_list')
            result = await DB.get_donates()

            if result and bool(len(result)):
                for line in result:
                    summ = line[1]
                    if user.lang_select != 'Русский':
                        summ = round(summ / KURS_RUB, 2)
                    text += f'\n@{line[0]} - {summ}{user.valuta}'

                await send_message(user_id, text, reply_markup=await fun_klav_donats(user))
            else:
                await send_message(user_id, user.lang.get('tx_donats_not_find'), reply_markup=await fun_klav_donats(user))

        elif m_text == user.lang.get('but_create_key'):
            if user.code != '':
                if not await check_promo_is_activ(user.code, user_id):
                    user.bot_status = 22
                    await select_protocol(user_id)
                else:
                    await send_message(user_id, user.lang.get('tx_promo_is_activate'))
            else:
                await send_message(user_id, user.lang.get('tx_promo_error'))

        elif m_text == user.lang.get('but_prodlit_key'):
            if user.code != '':
                await get_user_keys(user_id, prodlit=True, oplacheno=True)
            else:
                await send_message(user_id, user.lang.get('tx_promo_error'))

        elif m_text == user.lang.get('but_partner'):
            data_promo = await DB.get_stats_promoses(user_id=user_id)
            yes = False
            text_send = ''

            if data_promo:
                if data_promo[0] and len(data_promo[0]) > 0 and data_promo[0][0]:
                    for i in data_promo:
                        id_partner = i[2]
                        if id_partner == user_id:
                            code = i[0]
                            percatage = i[1]
                            percent_partner = i[3]
                            count = i[4] if not i[4] is None else 0
                            summ = i[5] if not i[5] is None else 0
                            count_probniy = i[6] if not i[6] is None else 0

                            yes = True
                            url = f'https://t.me/{BOT_NICK}?start={code}\n'

                            resu = await DB.get_user_operations(code)
                            resu1 = await DB.get_user_operations(code, 'prodl')
                            resu2 = await DB.get_user_operations(code, 'buy')
                            resu3 = await DB.get_user_operations(code, 'promo', da=True)
                            last_dolg = await DB.get_parter_pay(id_partner)

                            if not last_dolg is None and len(last_dolg) > 0:
                                last_dolg_date = datetime.strptime(last_dolg[-1][1], "%Y-%m-%d %H:%M:%S.%f")
                                last_dolg = last_dolg[-1][4]
                            else:
                                last_dolg = 0
                                last_dolg_date = None

                            # Считаем сумму продлений
                            total_prodl_summ = 0
                            new_prodl_summ = 0

                            for res in resu1:
                                total_summ = res[0]
                                date_ = res[1]
                                total_prodl_summ += total_summ

                                if not last_dolg_date is None and datetime.strptime(date_, "%Y-%m-%d %H:%M:%S.%f") < last_dolg_date:
                                    continue

                                new_prodl_summ += total_summ

                            # Считаем сумму покупок
                            total_buy_summ = 0
                            new_buy_summ = 0

                            for res in resu2:
                                total_summ = res[0]
                                date_ = res[1]
                                total_buy_summ += total_summ

                                if not last_dolg_date is None and datetime.strptime(date_, "%Y-%m-%d %H:%M:%S.%f") < last_dolg_date:
                                    continue

                                new_buy_summ += total_summ

                            if percatage == 0:
                                # Считаем сумму промокодов
                                total_promo_summ = 0
                                new_promo_summ = 0

                                for res in resu3:
                                    total_summ = res[0]
                                    date_ = res[1]
                                    total_promo_summ += total_summ

                                    if not last_dolg_date is None and datetime.strptime(date_, "%Y-%m-%d %H:%M:%S.%f") < last_dolg_date:
                                        continue

                                    new_promo_summ += total_summ  
                            else:
                                new_promo_summ = 0
                                total_promo_summ = 0

                            # Считаем промокоды 
                            data_30 = None
                            data_90 = None
                            data_180 = None
                            data_365 = None

                            for res in resu:
                                days = res[0]
                                count_users_code = res[1]
                                total_summ = res[2]

                                if days == 30:
                                    data_30 = (count_users_code, total_summ)
                                elif days == 90:
                                    data_90 = (count_users_code, total_summ)
                                elif days == 180:
                                    data_180 = (count_users_code, total_summ)
                                elif days == 365:
                                    data_365 = (count_users_code, total_summ)

                            promo_text = ''
                            promo_yes = False
                            promo_text_1 = user.lang.get('tx_partner_stat_promo_1')
                            promo_text_3 = user.lang.get('tx_partner_stat_promo_3')
                            promo_text_6 = user.lang.get('tx_partner_stat_promo_6')
                            promo_text_12 = user.lang.get('tx_partner_stat_promo_12')
                            
                            if TARIF_1 != 0 and not data_30 is None:
                                promo_yes = True
                                promo_text += f'*{data_30[0]} {promo_text_1} ({"~" if percatage != 0 else ""}{await razryad(data_30[1])}₽)\n' # пишем сколько промокодов активировано на 1 месяц (по id пользователя смотрим promo, если такой же как у нас, то +1)
                            if TARIF_3 != 0 and not data_90 is None:
                                promo_yes = True
                                promo_text += f'*{data_90[0]} {promo_text_3} ({"~" if percatage != 0 else ""}{await razryad(data_90[1])}₽)\n' # пишем сколько промокодов активировано на 3 месяца (по id пользователя смотрим promo, если такой же как у нас, то +1)
                            if TARIF_6 != 0 and not data_180 is None:
                                promo_yes = True
                                promo_text += f'*{data_180[0]} {promo_text_6} ({"~" if percatage != 0 else ""}{await razryad(data_180[1])}₽)\n' # пишем сколько промокодов активировано на 6 месяцев (по id пользователя смотрим promo, если такой же как у нас, то +1)
                            if TARIF_12 != 0 and not data_365 is None:
                                promo_yes = True
                                promo_text += f'*{data_365[0]} {promo_text_12} ({"~" if percatage != 0 else ""}{await razryad(data_365[1])}₽)' # пишем сколько промокодов активировано на 12 месяцев (по id пользователя смотрим promo, если такой же как у нас, то +1)

                            if not promo_yes:
                                promo_text += '...'

                            # total_partner = last_dolg + ((new_buy_summ + new_prodl_summ  + new_promo_summ) * percent_partner / 100)
                            total_partner = (total_buy_summ + total_prodl_summ + total_promo_summ) * percent_partner / 100

                            data_promo = await DB.get_parter_pay(id_partner) # id, date, summ, comment
                            summ_opl = 0

                            if len(data_promo) > 0:
                                for i in data_promo:
                                    summ_opl += int(i[2])

                            total_vivod = await razryad(summ_opl)
                            remains_vivod = total_partner - summ_opl
                            if remains_vivod < 0:
                                remains_vivod = 0
                            remains_vivod = await razryad(remains_vivod)
                            
                            total_buy_summ = await razryad(total_buy_summ)
                            total_promo_summ = await razryad(total_promo_summ)
                            total_prodl_summ = await razryad(total_prodl_summ)
                            total_partner = await razryad(total_partner)
                            
                            text_send += user.lang.get('tx_partner_stat').format(
                                url=url,
                                percatage=percatage,
                                percent_partner=percent_partner,
                                count=count,
                                count_probniy=count_probniy,
                                promo_text=promo_text,
                                total_buy_summ=total_buy_summ,
                                total_promo_summ=total_promo_summ,
                                total_prodl_summ=total_prodl_summ,
                                total_partner=total_partner,
                                total_vivod=total_vivod,
                                remains_vivod=remains_vivod
                            )

                            # Отправляем файл с текстами и промокодами (если активированы выделяем их)
                            file_name = f'{user_id}_promo_{code}.txt'
                            file = await get_urls_partner_file(user_id, file_name)
                            if file:
                                await bot.send_document(user_id, file)
                            try: os.remove(file_name)
                            except: pass
                            break

            if not yes:
                klava = InlineKeyboardMarkup()
                klava.add(InlineKeyboardButton(text=user.lang.get('but_create_partner_url'), callback_data=f'create_partner_url:'))
                await send_message(user_id, user.lang.get('tx_partner').format(but=user.lang.get('but_create_partner_url'), percent=PARTNER_P, summ=SUMM_VIVOD), reply_markup=klava)
            elif text_send != '':
                await send_message(user_id, text_send, reply_markup=await fun_klav_partner(user))
                await send_message(user_id, user.lang.get('tx_partner_pay_out').format(summ=SUMM_VIVOD))

        elif m_text == user.lang.get('but_partner_pay'):
            data_promo = await DB.get_stats_promoses(user_id=user_id)
            text_send = ''

            if not data_promo is None and len(data_promo) > 0:
                if not data_promo[0] is None and len(data_promo[0]) > 0 and not data_promo[0][0] is None:
                    for i in data_promo:
                        id_partner = i[2]
                        if id_partner == user_id:
                            code = i[0]
                            percatage = i[1]
                            percent_partner = i[3]
                            count = i[4] if not i[4] is None else 0

                            resu = await DB.get_user_operations(code)
                            resu1 = await DB.get_user_operations(code, 'prodl')
                            resu2 = await DB.get_user_operations(code, 'buy')
                            resu3 = await DB.get_user_operations(code, 'promo', da=True)
                            last_dolg = await DB.get_parter_pay(id_partner)

                            if not last_dolg is None and len(last_dolg) > 0:
                                last_dolg_date = datetime.strptime(last_dolg[-1][1], "%Y-%m-%d %H:%M:%S.%f")
                                last_dolg = last_dolg[-1][4]
                            else:
                                last_dolg = 0
                                last_dolg_date = None

                            # Считаем сумму продлений
                            total_prodl_summ = 0
                            new_prodl_summ = 0

                            for res in resu1:
                                total_summ = res[0]
                                date_ = res[1]
                                total_prodl_summ += total_summ

                                if not last_dolg_date is None and datetime.strptime(date_, "%Y-%m-%d %H:%M:%S.%f") < last_dolg_date:
                                    continue

                                new_prodl_summ += total_summ

                            # Считаем сумму покупок
                            total_buy_summ = 0
                            new_buy_summ = 0

                            for res in resu2:
                                total_summ = res[0]
                                date_ = res[1]
                                total_buy_summ += total_summ

                                if not last_dolg_date is None and datetime.strptime(date_, "%Y-%m-%d %H:%M:%S.%f") < last_dolg_date:
                                    continue

                                new_buy_summ += total_summ

                            if percatage == 0:
                                # Считаем сумму промокодов
                                total_promo_summ = 0
                                new_promo_summ = 0

                                for res in resu3:
                                    total_summ = res[0]
                                    date_ = res[1]
                                    total_promo_summ += total_summ

                                    if not last_dolg_date is None and datetime.strptime(date_, "%Y-%m-%d %H:%M:%S.%f") < last_dolg_date:
                                        continue

                                    new_promo_summ += total_summ  
                            else:
                                new_promo_summ = 0
                                total_promo_summ = 0

                            # total_partner = last_dolg + ((new_buy_summ + new_prodl_summ  + new_promo_summ) * percent_partner / 100)
                            total_partner = (total_buy_summ + total_prodl_summ  + total_promo_summ) * percent_partner / 100

                            id_partner = user_id
                            partner_summ_zarabotal = total_partner

                            data_promo = await DB.get_parter_pay(id_partner) # id, date, summ, comment
                            text_send = ''
                            summ_opl = 0

                            if len(data_promo) > 0:
                                for i in data_promo:
                                    summ_opl += int(i[2])
                                    text_send += user.lang.get('tx_partner_withdrawal').format(
                                        id=i[0], 
                                        date=i[1].split(".")[0],
                                        summ=await razryad(i[2]),
                                        comment=i[3]
                                    )
                                    text_send += '\n'

                            if text_send == '':
                                await send_message(user_id, user.lang.get('tx_partner_withdrawal_no_find'))
                            else:
                                text_send += user.lang.get('tx_partner_withdrawal_results').format(
                                    summ_opl=await razryad(summ_opl),
                                    partner_summ_zarabotal=await razryad(partner_summ_zarabotal)
                                )
                                await send_message(user_id, text_send, reply_markup=await fun_klav_partner(user))
                            break

        elif m_text == user.lang.get('but_zaprosi'):
            data = await DB.get_all_zaprosi(user_id) # id, User_id, Summ, Comment, Status, Dolg
            text_send = ''
            if data and len(data) > 0:
                text_send = user.lang.get('tx_partner_withdrawal_all') + '\n'
                for zapros in data:
                    id_zapros = zapros[0]
                    user_id_zapros = zapros[1]
                    summ_zapros = zapros[2]
                    comment_zapros = zapros[3]
                    status_zapros = zapros[4] # 0 - Wait, 1 - Done, 2 - Cancel
                    current_dolg = zapros[5]

                    text_send += user.lang.get('tx_partner_withdrawal_item').format(
                        id=id_zapros,
                        summ=await razryad(summ_zapros),
                        comment=comment_zapros,
                        status=user.lang.get(f'tx_partner_withdrawal_status_{status_zapros}'),
                        dolg=await razryad(current_dolg)
                    )
                    text_send += '\n'
            else:
                text_send = user.lang.get('tx_zapros_no').format(but=user.lang.get('but_zaprosi_add'))

            await send_message(user_id, text_send, reply_markup=await fun_klav_zaprosi(user))

        elif m_text == user.lang.get('but_zaprosi_add'):
            data = await DB.get_all_zaprosi(user_id)
            summ_zapros_wait_and_pay = 0
            if data and len(data) > 0:
                for zapros in data:
                    summ_zapros = zapros[2]
                    status_zapros = zapros[4] # 0 - Wait, 1 - Done, 2 - Cancel
                    if status_zapros in (0, 1):
                        summ_zapros_wait_and_pay += summ_zapros

            data_promo = await DB.get_stats_promoses(user_id=user_id)
            summ_zarabotal_partner = 0

            if not data_promo is None and len(data_promo) > 0:
                if not data_promo[0] is None and len(data_promo[0]) > 0 and not data_promo[0][0] is None:
                    for i in data_promo:
                        id_partner = i[2]
                        if id_partner == user_id:
                            code = i[0]
                            percatage = i[1]
                            percent_partner = i[3]
                            count = i[4] if not i[4] is None else 0
                            summ = i[5] if not i[5] is None else 0
                            count_probniy = i[6] if not i[6] is None else 0

                            resu = await DB.get_user_operations(code)
                            resu1 = await DB.get_user_operations(code, 'prodl')
                            resu2 = await DB.get_user_operations(code, 'buy')
                            resu3 = await DB.get_user_operations(code, 'promo', da=True)
                            last_dolg = await DB.get_parter_pay(id_partner)

                            if not last_dolg is None and len(last_dolg) > 0:
                                last_dolg_date = datetime.strptime(last_dolg[-1][1], "%Y-%m-%d %H:%M:%S.%f")
                                last_dolg = last_dolg[-1][4]
                            else:
                                last_dolg = 0
                                last_dolg_date = None

                            # Считаем сумму продлений
                            total_prodl_summ = 0
                            new_prodl_summ = 0

                            for res in resu1:
                                total_summ = res[0]
                                date_ = res[1]
                                total_prodl_summ += total_summ

                                if not last_dolg_date is None and datetime.strptime(date_, "%Y-%m-%d %H:%M:%S.%f") < last_dolg_date:
                                    continue
                                
                                new_prodl_summ += total_summ

                            # Считаем сумму покупок
                            total_buy_summ = 0
                            new_buy_summ = 0

                            for res in resu2:
                                total_summ = res[0]
                                date_ = res[1]
                                total_buy_summ += total_summ

                                if not last_dolg_date is None and datetime.strptime(date_, "%Y-%m-%d %H:%M:%S.%f") < last_dolg_date:
                                    continue
                                
                                new_buy_summ += total_summ

                            if percatage == 0:
                                # Считаем сумму промокодов
                                total_promo_summ = 0
                                new_promo_summ = 0

                                for res in resu3:
                                    total_summ = res[0]
                                    date_ = res[1]
                                    total_promo_summ += total_summ

                                    if not last_dolg_date is None and datetime.strptime(date_, "%Y-%m-%d %H:%M:%S.%f") < last_dolg_date:
                                        continue
                                    
                                    new_promo_summ += total_summ  
                            else:
                                new_promo_summ = 0
                                total_promo_summ = 0
                            
                            # Считаем промокоды 
                            data_30 = None
                            data_90 = None
                            data_180 = None
                            data_365 = None

                            for res in resu:
                                days = res[0]
                                count_users_code = res[1]
                                total_summ = res[2]

                                if days == 30:
                                    data_30 = (count_users_code, total_summ)
                                elif days == 90:
                                    data_90 = (count_users_code, total_summ)
                                elif days == 180:
                                    data_180 = (count_users_code, total_summ)
                                elif days == 365:
                                    data_365 = (count_users_code, total_summ)

                            # summ_zarabotal_partner = last_dolg + ((new_buy_summ + new_prodl_summ  + new_promo_summ) * percent_partner / 100)
                            summ_zarabotal_partner = (total_buy_summ + total_prodl_summ  + total_promo_summ) * percent_partner / 100

            # посчитать сумму, на которую можно сделать запрос (партнер заработал - (запросы в статусе ожидания + выполненные))
            summ_zapros = summ_zarabotal_partner - summ_zapros_wait_and_pay

            # if summ_zarabotal_partner >= SUMM_VIVOD:
            if summ_zapros >= SUMM_VIVOD:
                await send_message(user_id, user.lang.get('tx_zaprosi_add_alert').format(text=user.lang.get('tx_partner_pay_out').format(summ=SUMM_VIVOD), summ=await razryad(summ_zapros)), reply_markup=await fun_klav_zaprosi(user))
                user.bot_status = 9
            else:
                # отправить партнеру: недосточная сумма для вывода, зарезервированная сумма = summ_zapros_wait_and_pay
                await send_message(user_id, user.lang.get('tx_partner_pay_out_no_summ_wait').format(text=user.lang.get('tx_partner_pay_out').format(summ=SUMM_VIVOD), summ=summ_zapros_wait_and_pay, summ_out=summ_zapros), reply_markup=await fun_klav_zaprosi(user))
            # else:
            #     await send_message(user_id, user.lang.get('tx_partner_pay_out_no').format(text=user.lang.get('tx_partner_pay_out').format(summ=SUMM_VIVOD), summ=summ_zarabotal_partner), reply_markup=await fun_klav_zaprosi(user))

        elif m_text == user.lang.get('but_pay_change_protocol'):
            user.bill_bot_key = ''
            user.isPayChangeProtocol = True
            user.isPayChangeLocations = False
            if len([item for item in WALLETS if item['isActive']]) > 1:
                user.PAY_WALLET = None
            await pokupka(user)

        elif m_text == user.lang.get('but_pay_change_locations'):
            user.bill_bot_key = ''
            user.isPayChangeProtocol = False
            user.isPayChangeLocations = True
            if len([item for item in WALLETS if item['isActive']]) > 1:
                user.PAY_WALLET = None
            await pokupka(user)

        elif user.lang.get('but_pravila') and m_text == user.lang.get('but_pravila'):
            klava = InlineKeyboardMarkup()
            klava.add(InlineKeyboardButton(text=user.lang.get('but_pravila_sogl'), url=sogl_urls[0]))
            klava.add(InlineKeyboardButton(text=user.lang.get('but_pravila_politic'), url=sogl_urls[1]))
            klava.add(InlineKeyboardButton(text=user.lang.get('but_pravila_refaund'), url=sogl_urls[2]))
            await send_message(user_id, user.lang.get('but_parvila_title'), reply_markup=klava)

        elif await check_buttons_donate(user, m_text):
            for el in user.donate:
                id = int(el)
                el = user.donate[el]
                name = el[0]
                summ = el[1]

                if name in m_text:
                    user.donate_text = m_text
                    if not user.PAY_WALLET:
                        user.payStatus = 2
                        await select_payment_method(user_id)
                        return

                    user.tarif_select = 21

                    url_pay = await user.PAY_WALLET.create_pay(user, summ)
                    klava_buy = InlineKeyboardMarkup()

                    if user.lang_select != 'Русский':
                        summ = round(summ / KURS_RUB, 2)

                    is_xtr = url_pay == PAY_METHODS.XTR
                    if not is_xtr:
                        but_buy_1 = InlineKeyboardButton(text=user.lang.get('but_donate_pay').format(sum=summ, valuta=user.valuta), url=url_pay if not WEB_APP_PAY else None, web_app=WebAppInfo(url=url_pay) if WEB_APP_PAY else None)
                        but_buy_2 = InlineKeyboardButton(text=user.lang.get('but_check_pay'), callback_data=f'check:{user_id}:{user.bill_id}:poz{id}')
                        klava_buy.add(but_buy_1).add(but_buy_2)

                        message_del = await send_message(user_id, user.lang.get('tx_donate_description'), reply_markup=klava_buy)

                    if PHONE_NUMBER != '':
                        await send_message(user_id, user.lang.get('tx_perevod').format(nick_help=NICK_HELP), reply_markup=await fun_klav_cancel_pay(user))
                        await send_message(user_id, f'<code>{PHONE_NUMBER}</code>')

                    admin_klava = InlineKeyboardMarkup()
                    admin_klava.add(InlineKeyboardButton(text='✅Подтвердить оплату', callback_data=f'check:{user_id}:{user.bill_id}:admin:poz{id}'))

                    if len(WALLETS) > 1:
                        bottom_text = f'💳Счет: <b>{user.PAY_WALLET.Name}</b> ({user.PAY_WALLET.API_Key_TOKEN[:15]})'
                    else:
                        bottom_text = ''

                    if not IS_OTCHET:
                        await send_admins(user_id, f'🔄Вызвал оплату доната ({name}, {summ}₽)', bottom_text, reply_markup=admin_klava)

                    user.autoTimerStart = datetime.now()
                    user.isAutoCheckOn = True
                    try: user.message_del_id = message_del.message_id
                    except: pass
                    
                    tasks = [asyncio.create_task(auto_check_pay(user_id, id, str(user.bill_id)))]
                    asyncio.gather(*tasks)
                    break

        else:
            # Проверка не ввел ли клиент промокод
            data = await DB.get_all_promo_codes()
            for i in data: # SELECT Code, CountDays, isActivated FROM PromoCodes
                code = i[0]
                CountDays = int(i[1])
                isActivated = bool(i[2])
                if code in m_text:
                    if not isActivated:
                        user.code = code
                        user.days_code = CountDays

                        res = await DB.get_qr_key_All(user_id) #BOT_Key, Date, User_id, isAdminKey, CountDaysBuy, ip_server, isActive
                        if res and len(res) > 0:
                            # Есть ключи
                            send_inline_button = False
                            if not send_inline_button:
                                await send_message(user_id, user.lang.get('tx_promo_select'), reply_markup=await fun_klav_promo(user))
                            else:
                                klava = InlineKeyboardMarkup()
                                klava.add(InlineKeyboardButton(text=user.lang.get('but_create_key'), callback_data=f'buttons:but_create_key'))
                                klava.add(InlineKeyboardButton(text=user.lang.get('but_prodlit_key'), callback_data=f'buttons:but_prodlit_key'))
                                await send_message(user_id, user.lang.get('tx_promo_select'), reply_markup=klava)
                        else:
                            # Нет ключей
                            user.bot_status = 22
                            await select_protocol(user_id)
                    else:
                        await send_message(user_id, user.lang.get('tx_promo_is_activate'))
                    return True

            data = await DB.exists_individual_promo_code(m_text.strip())
            if data:
                # проверить, чтобы пользователь не активировал данный промокод
                res_add_promo = await DB.get_activate_individual_promo_code(m_text.strip(), user_id)
                if res_add_promo:
                    await send_message(user_id, user.lang.get('tx_promo_is_activate'))
                    return
                else:
                    data = await DB.get_all_individual_promo_codes() # code, days, count, count_days_delete, date_create
                    for i in data:
                        code = i[0]
                        if code == m_text.strip():
                            days = i[1]
                            user.code = code
                            user.days_code = days
                            
                            res = await DB.get_qr_key_All(user_id) #BOT_Key, Date, User_id, isAdminKey, CountDaysBuy, ip_server, isActive
                            if res and len(res) > 0:
                                # Есть ключи
                                send_inline_button = False
                                if not send_inline_button:
                                    await send_message(user_id, user.lang.get('tx_promo_select'), reply_markup=await fun_klav_promo(user))
                                else:
                                    klava = InlineKeyboardMarkup()
                                    klava.add(InlineKeyboardButton(text=user.lang.get('but_create_key'), callback_data=f'buttons:but_create_key'))
                                    klava.add(InlineKeyboardButton(text=user.lang.get('but_prodlit_key'), callback_data=f'buttons:but_prodlit_key'))
                                    await send_message(user_id, user.lang.get('tx_promo_select'), reply_markup=klava)
                            else:
                                # Нет ключей
                                user.bot_status = 22
                                await select_protocol(user_id)
                            return

            # проверить если такая спец.ссылка, если есть то попробовать установить её
            if WRITE_CLIENTS_SCPEC_PROMO:
                spec_urls = await DB.get_promo_urls()
                if spec_urls and len(spec_urls) > 0:
                    m_text_temp = m_text.replace(' ', '')
                    for spec_url in spec_urls:
                        if spec_url[0] == m_text_temp:
                            res_add_promo = await DB.set_user_Promo(user_id, m_text_temp)
                            if res_add_promo[0]:
                                code = spec_url[0]
                                if res_add_promo[1] > 0:
                                    await send_message(user_id, user.lang.get('tx_spec_url_yes').format(discount=res_add_promo[1]))
                                else:
                                    await send_message(user_id, user.lang.get('tx_spec_url_yes_no_discount'))
                            else:
                                await send_message(user_id, user.lang.get('tx_spec_url_is_activate'))
                            return True

            if '.' in m_text:
                for server in SERVERS:
                    if server['ip'] == m_text:
                        await servers_edit(ip=m_text, message=message)
                        return

            if user.isAdmin:
                return await get_users_reports(user_id, f'all::{message.text.replace(" ", "").replace("@", "")}', is_search=True)
            await send_message(user_id, user.lang.get('tx_user_send_message').format(nick_help=NICK_HELP), reply_markup=await fun_klav_help(user))
            await send_admins(user_id, '✏️Написал', f'Text: <b>{m_text}</b>')
    except:
        await Print_Error()

def restartBot():
    try:
        logger.warning('🛑🛑🛑Выполняю перезапуск бота🛑🛑🛑')
        threading.Thread(target=restart_bot_command, args=('supervisorctl restart bot', )).start()
        run('supervisorctl restart bot', shell = True, capture_output = True, encoding='cp866')
    except Exception as e:
        logger.warning(f'🛑🛑🛑Ошибка в restartBot🛑🛑🛑: {e}')

async def start_bot():
    try:
        # Инициализация бота
        await create_bot()
        
        if not all([x.isalpha() or x.isdigit() for x in NAME_BOT_CONFIG]):
            await send_admins(None, '🛑🛑🛑Не верно указано имя для конфигураций конфига (/get_config -> NAME_BOT_CONFIG)🛑🛑🛑')

        tasks = []
        await dp.skip_updates()
        tasks.append(asyncio.create_task(dp.start_polling()))
        tasks.append(asyncio.create_task(check_zaprosi()))
        tasks.append(asyncio.create_task(check_time_create_backup()))
        tasks.append(asyncio.create_task(check_keys_no_in_db()))
        tasks.append(asyncio.create_task(check_clients_and_keys()))
        tasks.append(asyncio.create_task(check_servers_on()))
        tasks.append(asyncio.create_task(get_kurs_usdtrub_garantex()))
        await asyncio.gather(*tasks)
    except Exception as e:
        logger.warning(f'🛑Ошибка в start_bot: {e}')
        await Print_Error()
        restartBot()
        raise e

if __name__ == '__main__':
    try:
        asyncio.run(start_bot())
    except Exception as e:
        logger.warning(f'🛑🛑🛑🛑🛑Ошибка в if __name__ == "__main__":: {e}')
        restartBot()