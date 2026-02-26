# =============================================================================
# BOTinok Configuration
# =============================================================================
# Этот файл загружает настройки из .env файла или использует значения по умолчанию
# =============================================================================

import os
from pathlib import Path

# Определяем директорию проекта
BASE_DIR = Path(__file__).resolve().parent.parent

# Пытаемся загрузить .env файл
env_file = BASE_DIR / '.env'
if env_file.exists():
    # Читаем .env файл вручную (без сторонних библиотек)
    try:
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip("'\"")
                    # Используем прямое присваивание вместо setdefault
                    os.environ[key] = value
    except (UnicodeDecodeError, IOError) as e:
        # Если не удалось прочитать .env, используем значения по умолчанию
        print(f"Warning: Could not read .env file: {e}")

# =============================================================================
# Токены ботов
# =============================================================================

TOKEN_MAIN = os.environ.get('TOKEN_MAIN', '') # Основной токен бота

# =============================================================================
# Основные данные
# =============================================================================

ADMINS_IDS = [] # Дополнительные администраторы (указывать через запятую = [123456789, 987654321])
MY_ID_TELEG = int(os.environ.get('MY_ID_TELEG', 782280769)) # Id администратора Telegram
PHONE_NUMBER = '' # Номер телефона для переводов (если необходимо отключить возможностью перевода, просто установите поле = '')
NICK_HELP = os.environ.get('NICK_HELP', 'codenlx') # Ник пользователя для помощи
NAME_AUTHOR_BOT = os.environ.get('NAME_AUTHOR_BOT', 'Александр') # Имя кто создал BOT
NAME_BOT_CONFIG = os.environ.get('NAME_BOT_CONFIG', 'VPCoden') # Название бота (только буквы и цифры)

# Маркетинг
COUNT_DAYS_TRIAL = int(os.environ.get('COUNT_DAYS_TRIAL', 2))
COUNT_DAYS_REF = int(os.environ.get('COUNT_DAYS_REF', 7))
COUNT_DAYS_OTCHET = int(os.environ.get('COUNT_DAYS_OTCHET', 7))
DAYS_PARTNER_URLS_DELETE = int(os.environ.get('DAYS_PARTNER_URLS_DELETE', 7))
HOUR_CHECK = int(os.environ.get('HOUR_CHECK', 7))

# Модули (True - включен, False - выключен)
PAY_CHANGE_PROTOCOL = os.environ.get('PAY_CHANGE_PROTOCOL', 'False').lower() == 'true'
PAY_CHANGE_LOCATIONS = os.environ.get('PAY_CHANGE_LOCATIONS', 'False').lower() == 'true'
STOP_KEY = os.environ.get('STOP_KEY', 'True').lower() == 'true'

OPLATA = os.environ.get('OPLATA', 'True').lower() == 'true'
REF_SYSTEM = os.environ.get('REF_SYSTEM', 'True').lower() == 'true'
REF_SYSTEM_AFTER_PAY = os.environ.get('REF_SYSTEM_AFTER_PAY', 'False').lower() == 'true'
TEST_KEY = os.environ.get('TEST_KEY', 'True').lower() == 'true'

WEB_APP_PAY = os.environ.get('WEB_APP_PAY', 'False').lower() == 'true'
INLINE_MODE = os.environ.get('INLINE_MODE', 'False').lower() == 'true'
IS_OTCHET = os.environ.get('IS_OTCHET', 'False').lower() == 'true'

WHY_BOT_PAY = os.environ.get('WHY_BOT_PAY', 'True').lower() == 'true'
DONATE_SYSTEM = os.environ.get('DONATE_SYSTEM', 'True').lower() == 'true'
OBESH_PLATEZH = os.environ.get('OBESH_PLATEZH', 'True').lower() == 'true'
SEND_QR = os.environ.get('SEND_QR', 'False').lower() == 'true'
OPROS = os.environ.get('OPROS', 'True').lower() == 'true'

# Протоколы - ОСТАВЛЕН ТОЛЬКО VLESS
PR_VLESS = os.environ.get('PR_VLESS', 'True').lower() == 'true'
PR_OUTLINE = os.environ.get('PR_OUTLINE', 'False').lower() == 'true'
PR_WIREGUARD = os.environ.get('PR_WIREGUARD', 'False').lower() == 'true'
PR_PPTP = os.environ.get('PR_PPTP', 'False').lower() == 'true'

DEFAULT_PROTOCOL = os.environ.get('DEFAULT_PROTOCOL', 'vless')
VLESS_LIMIT_IP = int(os.environ.get('VLESS_LIMIT_IP', 1))

# Инструкции - ОСТАВЛЕНА ТОЛЬКО VLESS
HELP_VLESS = os.environ.get('HELP_VLESS', 'True').lower() == 'true'
HELP_OUTLINE = os.environ.get('HELP_OUTLINE', 'False').lower() == 'true'
HELP_WIREGUARD = os.environ.get('HELP_WIREGUARD', 'False').lower() == 'true'
HELP_PPTP = os.environ.get('HELP_PPTP', 'False').lower() == 'true'

### Откуда пришел клиент
# Для создания специальной ссылки необходимо в указать номер по порядку, допустим:
# https://t.me/vpcoden_bot?start=global_1 - это будет специальная ссылка, перейдя по которой, бот запишет, что клиент пришел из Моей группы в Telegram
LINK_FROM = {
    1: 'Моя группа в Telegram',
    2: 'VK',
    3: 'Одноклассники',
    4: 'YouTube',
    5: 'Instagramm'
}
