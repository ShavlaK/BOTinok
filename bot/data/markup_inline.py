from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

#############################
# 1. Переменная "row_width=1" отвечает за ширину кнопок в клавиатуре,
#       если необходимо увеличить ширину кнопок, то нужно увеличить значение переменной
# 2. Функция .add() добавляет к клавиатуре кнопки, которые указаны в скобках,
#       пример: klav.add(but_test_key, but_connect)
# 3. Если в функции .add() несколько кнопок, то они будут добавлены в клавиатуру в одну строку,
#       если необходимо добавить кнопки в разные строки, то нужно использовать несколько функций .add(), пример: klav.add(but_test_key).add(but_connect)
#############################

async def fun_klav_start(user, NAME_VPN_CONFIG):
    klav = InlineKeyboardMarkup()
    if not user.isGetTestKey:
        klav.add(InlineKeyboardButton(text=user.lang.get('but_test_key'), callback_data=f'buttons:but_test_key'))
    klav.add(InlineKeyboardButton(text=user.lang.get('but_connect'), callback_data=f'buttons:but_connect'))
    klav.add(InlineKeyboardButton(text=user.lang.get('but_my_keys'), callback_data=f'buttons:but_my_keys'))
    klav.add(InlineKeyboardButton(text=user.lang.get('but_change_protocol'), callback_data=f'buttons:but_change_protocol'))
    klav.add(InlineKeyboardButton(text=user.lang.get('but_change_location'), callback_data=f'buttons:but_change_location'))
    klav.add(InlineKeyboardButton(text=user.lang.get('but_ref'), callback_data=f'buttons:but_ref'))
    klav.add(InlineKeyboardButton(text=user.lang.get('but_desription').format(name_config=NAME_VPN_CONFIG), callback_data=f'buttons:but_desription'))
    klav.add(InlineKeyboardButton(text=user.lang.get('but_donate'), callback_data=f'buttons:but_donate'))
    klav.add(InlineKeyboardButton(text=user.lang.get('but_change_language'), callback_data=f'buttons:but_change_language'))
    klav.add(InlineKeyboardButton(text=user.lang.get('but_help'), callback_data=f'buttons:but_help'))
    klav.add(InlineKeyboardButton(text=user.lang.get('but_partner'), callback_data=f'buttons:but_partner'))
    return klav

async def fun_klav_buy_days(user):
    klav = InlineKeyboardMarkup()
    for button in user.buttons_days:
        klav.add(InlineKeyboardButton(text=button, callback_data=f'buttons:{button}:znach'))
    klav.add(InlineKeyboardButton(text=user.lang.get('but_main'), callback_data=f'buttons:but_main'))
    return klav

async def fun_klav_desription(user, but_instagram):
    klav = InlineKeyboardMarkup()
    klav.add(InlineKeyboardButton(text=user.lang.get('but_connect'), callback_data=f'buttons:but_connect'))
    klav.add(InlineKeyboardButton(text=user.lang.get('but_reviews'), callback_data=f'buttons:but_reviews'))
    klav.add(InlineKeyboardButton(text=user.lang.get('but_why'), callback_data=f'buttons:but_why'))
    klav.add(InlineKeyboardButton(text=but_instagram, callback_data=f'buttons:but_instagram'))
    klav.add(InlineKeyboardButton(text=user.lang.get('but_main'), callback_data=f'buttons:but_main'))
    return klav

async def fun_klav_opros(user):
    klav = InlineKeyboardMarkup()
    klav.add(InlineKeyboardButton(text=user.lang.get('but_opros_super'), callback_data=f'buttons:but_opros_super'))
    klav.add(InlineKeyboardButton(text=user.lang.get('but_opros_good'), callback_data=f'buttons:but_opros_good'))
    klav.add(InlineKeyboardButton(text=user.lang.get('but_main'), callback_data=f'buttons:but_main'))
    return klav

async def fun_klav_promo(user):
    klav = InlineKeyboardMarkup()
    klav.add(InlineKeyboardButton(text=user.lang.get('but_create_key'), callback_data=f'buttons:but_create_key'))
    klav.add(InlineKeyboardButton(text=user.lang.get('but_prodlit_key'), callback_data=f'buttons:but_prodlit_key'))
    klav.add(InlineKeyboardButton(text=user.lang.get('but_main'), callback_data=f'buttons:but_main'))
    return klav

async def fun_klav_cancel_pay(user):
    klav = InlineKeyboardMarkup()
    klav.add(InlineKeyboardButton(text=user.lang.get('but_cancel_pay'), callback_data=f'buttons:but_cancel_pay'))
    return klav

async def fun_klav_podkl(user, buttons_podkl):
    klav = InlineKeyboardMarkup()
    for button in buttons_podkl:
        klav.add(InlineKeyboardButton(text=button, callback_data=f'buttons:{button}:znach'))
    klav.add(InlineKeyboardButton(text=user.lang.get('but_back_help'), callback_data=f'buttons:but_back_help'))
    klav.add(InlineKeyboardButton(text=user.lang.get('but_main'), callback_data=f'buttons:but_main'))
    return klav

async def fun_klav_how_install(user, HELP_VLESS, HELP_PPTP):
    """Упрощено - только VLESS и PPTP"""
    klav = InlineKeyboardMarkup()
    if HELP_VLESS:
        klav.add(InlineKeyboardButton(text=user.lang.get('but_how_podkl_vless'), callback_data=f'buttons:but_how_podkl_vless'))
    if HELP_PPTP:
        klav.add(InlineKeyboardButton(text=user.lang.get('but_how_podkl_pptp'), callback_data=f'buttons:but_how_podkl_pptp'))
    klav.add(InlineKeyboardButton(text=user.lang.get('but_back_help'), callback_data=f'buttons:but_back_help'))
    return klav

async def fun_klav_select_protocol(user, PR_VLESS, PR_PPTP):
    """Упрощено - только VLESS и PPTP"""
    klav = InlineKeyboardMarkup()
    if PR_VLESS:
        klav.add(InlineKeyboardButton(text=user.lang.get('but_select_vless'), callback_data=f'buttons:but_select_vless'))
    if PR_PPTP:
        klav.add(InlineKeyboardButton(text=user.lang.get('but_select_pptp'), callback_data=f'buttons:but_select_pptp'))
    klav.add(InlineKeyboardButton(text=user.lang.get('but_main'), callback_data=f'buttons:but_main'))
    return klav

async def fun_klav_podkl_no_back(user, buttons_podkl):
    klav = InlineKeyboardMarkup()
    for button in buttons_podkl:
        klav.add(InlineKeyboardButton(text=button, callback_data=f'buttons:{button}:znach'))
    klav.add(InlineKeyboardButton(text=user.lang.get('but_main'), callback_data=f'buttons:but_main'))
    return klav

async def fun_klav_help(user):
    klav = InlineKeyboardMarkup()
    klav.add(InlineKeyboardButton(text=user.lang.get('but_how_podkl'), callback_data=f'buttons:but_how_podkl'))
    klav.add(InlineKeyboardButton(text=user.lang.get('but_no_work_vpn'), callback_data=f'buttons:but_no_work_vpn'))
    klav.add(InlineKeyboardButton(text=user.lang.get('but_manager'), callback_data=f'buttons:but_manager'))
    klav.add(InlineKeyboardButton(text=user.lang.get('but_polz_sogl'), callback_data=f'buttons:but_polz_sogl'))
    klav.add(InlineKeyboardButton(text=user.lang.get('but_pravila'), callback_data=f'buttons:but_pravila'))
    klav.add(InlineKeyboardButton(text=user.lang.get('but_main'), callback_data=f'buttons:but_main'))
    return klav

async def fun_klav_donats(user):
    klav = InlineKeyboardMarkup()
    for button in user.buttons_Donate:
        klav.add(InlineKeyboardButton(text=button, callback_data=f'buttons:{button}:znach'))
    klav.add(InlineKeyboardButton(text=user.lang.get('but_donaters'), callback_data=f'buttons:but_donaters'))
    klav.add(InlineKeyboardButton(text=user.lang.get('but_main'), callback_data=f'buttons:but_main'))
    return klav

async def fun_klav_partner(user):
    klav = InlineKeyboardMarkup()
    klav.add(InlineKeyboardButton(text=user.lang.get('but_zaprosi'), callback_data=f'buttons:but_zaprosi'))
    klav.add(InlineKeyboardButton(text=user.lang.get('but_main'), callback_data=f'buttons:but_main'))
    return klav

async def fun_klav_zaprosi(user):
    klav = InlineKeyboardMarkup()
    klav.add(InlineKeyboardButton(text=user.lang.get('but_zaprosi_add'), callback_data=f'buttons:but_zaprosi_add'))
    klav.add(InlineKeyboardButton(text=user.lang.get('but_partner'), callback_data=f'buttons:but_partner'))
    return klav

async def fun_klav_pay_change_protocol(user):
    klav = InlineKeyboardMarkup()
    klav.add(InlineKeyboardButton(text=user.lang.get('but_pay_change_protocol'), callback_data=f'buttons:but_pay_change_protocol'))
    klav.add(InlineKeyboardButton(text=user.lang.get('but_main'), callback_data=f'buttons:but_main'))
    return klav

async def fun_klav_change_protocol(user):
    klav = InlineKeyboardMarkup()
    klav.add(InlineKeyboardButton(text=user.lang.get('but_change_protocol'), callback_data=f'buttons:but_change_protocol'))
    klav.add(InlineKeyboardButton(text=user.lang.get('but_main'), callback_data=f'buttons:but_main'))
    return klav

async def fun_klav_pay_change_locations(user):
    klav = InlineKeyboardMarkup()
    klav.add(InlineKeyboardButton(text=user.lang.get('but_pay_change_locations'), callback_data=f'buttons:but_pay_change_locations'))
    klav.add(InlineKeyboardButton(text=user.lang.get('but_main'), callback_data=f'buttons:but_main'))
    return klav

async def fun_klav_change_locations(user):
    klav = InlineKeyboardMarkup()
    klav.add(InlineKeyboardButton(text=user.lang.get('but_change_location'), callback_data=f'buttons:but_change_location'))
    klav.add(InlineKeyboardButton(text=user.lang.get('but_main'), callback_data=f'buttons:but_main'))
    return klav

async def fun_klav_select_languages(LANG):
    klav = InlineKeyboardMarkup()
    for lang in LANG:
        klav.add(InlineKeyboardButton(text=f'🔹{lang}', callback_data=f'lang:{lang}'))
    return klav
