from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton

#############################
# 1. Переменная "row_width=1" отвечает за ширину кнопок в клавиатуре,
#       если необходимо увеличить ширину кнопок, то нужно увеличить значение переменной
# 2. Функция .add() добавляет к клавиатуре кнопки, которые указаны в скобках,
#       пример: klav.add(but_test_key, but_connect)
# 3. Если в функции .add() несколько кнопок, то они будут добавлены в клавиатуру в одну строку,
#       если необходимо добавить кнопки в разные строки, то нужно использовать несколько функций .add(), пример: klav.add(but_test_key).add(but_connect)
#############################

async def fun_klav_start(user, NAME_BOT_CONFIG):
    klav = ReplyKeyboardMarkup(resize_keyboard=True,row_width=2)
    if not user.isGetTestKey:
        klav.add(user.lang.get('but_test_key'))
    klav.add(user.lang.get('but_connect'), user.lang.get('but_my_keys'), user.lang.get('but_change_protocol'), user.lang.get('but_change_location'))
    klav.add(user.lang.get('but_ref'), user.lang.get('but_desription').format(name_config=NAME_BOT_CONFIG), user.lang.get('but_donate'), user.lang.get('but_change_language'), user.lang.get('but_help'), user.lang.get('but_partner'))
    return klav

async def fun_klav_buy_days(user):
    return ReplyKeyboardMarkup(resize_keyboard=True,row_width=3).add(*user.buttons_days).add(user.lang.get('but_main'))

async def fun_klav_desription(user, but_instagram):
    return ReplyKeyboardMarkup(resize_keyboard=True,row_width=2).add(user.lang.get('but_connect')).add(user.lang.get('but_reviews'), user.lang.get('but_why')).add(but_instagram).add(user.lang.get('but_main'))

async def fun_klav_opros(user):
    return ReplyKeyboardMarkup(resize_keyboard=True, row_width=2).add(user.lang.get('but_opros_super'), user.lang.get('but_opros_good')).add(user.lang.get('but_main'))

async def fun_klav_promo(user):
    return ReplyKeyboardMarkup(resize_keyboard=True, row_width=1).add(user.lang.get('but_create_key')).add(user.lang.get('but_prodlit_key')).add(user.lang.get('but_main'))

async def fun_klav_cancel_pay(user):
    return ReplyKeyboardMarkup(resize_keyboard=True, row_width=1).add(user.lang.get('but_cancel_pay'))

async def fun_klav_podkl(user, buttons_podkl):
    return ReplyKeyboardMarkup(resize_keyboard=True, row_width=3).add(*buttons_podkl).add(user.lang.get('but_back_help'), user.lang.get('but_main'))

async def fun_klav_how_install(user, HELP_VLESS, HELP_PPTP):
    """Упрощено - только VLESS и PPTP"""
    help_buttons = []
    if HELP_VLESS:
        help_buttons.append(user.lang.get('but_how_podkl_vless'))
    if HELP_PPTP:
        help_buttons.append(user.lang.get('but_how_podkl_pptp'))
    return ReplyKeyboardMarkup(resize_keyboard=True, row_width=2).add(*help_buttons).add(user.lang.get('but_back_help'))

async def fun_klav_select_protocol(user, PR_VLESS, PR_PPTP):
    """Упрощено - только VLESS и PPTP"""
    select_buttons = []
    if PR_VLESS:
        select_buttons.append(user.lang.get('but_select_vless'))
    if PR_PPTP:
        select_buttons.append(user.lang.get('but_select_pptp'))
    return ReplyKeyboardMarkup(resize_keyboard=True, row_width=2).add(*select_buttons).add(user.lang.get('but_main'))

async def fun_klav_podkl_no_back(user, buttons_podkl):
    return ReplyKeyboardMarkup(resize_keyboard=True, row_width=3).add(*buttons_podkl).add(user.lang.get('but_main'))

async def fun_klav_help(user):
    return ReplyKeyboardMarkup(resize_keyboard=True, row_width=1).add(user.lang.get('but_how_podkl')).add(user.lang.get('but_no_work_bot')).add(user.lang.get('but_manager')).add(user.lang.get('but_polz_sogl'), user.lang.get('but_pravila')).add(user.lang.get('but_main'))

async def fun_klav_donats(user):
    return ReplyKeyboardMarkup(resize_keyboard=True, row_width=3).add(*user.buttons_Donate).add(user.lang.get('but_donaters'), user.lang.get('but_main'))

async def fun_klav_buy_ustr(user):
    return ReplyKeyboardMarkup(resize_keyboard=True, row_width=1).add(user.lang.get('but_prodlit')).add(user.lang.get('but_new_key')).add(user.lang.get('but_main'))

async def fun_klav_partner(user):
    return ReplyKeyboardMarkup(resize_keyboard=True,row_width=1).add(user.lang.get('but_zaprosi')).add(user.lang.get('but_main'))

async def fun_klav_zaprosi(user):
    return ReplyKeyboardMarkup(resize_keyboard=True,row_width=2).add(user.lang.get('but_zaprosi_add')).add(user.lang.get('but_partner'))

async def fun_klav_pay_change_protocol(user):
    return ReplyKeyboardMarkup(resize_keyboard=True,row_width=1).add(user.lang.get('but_pay_change_protocol')).add(user.lang.get('but_main'))

async def fun_klav_change_protocol(user):
    return ReplyKeyboardMarkup(resize_keyboard=True,row_width=1).add(user.lang.get('but_change_protocol')).add(user.lang.get('but_main'))

async def fun_klav_pay_change_locations(user):
    return ReplyKeyboardMarkup(resize_keyboard=True,row_width=1).add(user.lang.get('but_pay_change_locations')).add(user.lang.get('but_main'))

async def fun_klav_change_locations(user):
    return ReplyKeyboardMarkup(resize_keyboard=True,row_width=1).add(user.lang.get('but_change_location')).add(user.lang.get('but_main'))

async def fun_klav_select_languages(LANG):
    klav = InlineKeyboardMarkup()
    for lang in LANG:
        klav.add(InlineKeyboardButton(text=f'🔹{lang}', callback_data=f'lang:{lang}'))
    return klav
