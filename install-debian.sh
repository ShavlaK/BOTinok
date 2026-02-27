#!/bin/bash
# =============================================================================
# BOTinok - Полный скрипт установки для Debian 11
# =============================================================================
# Использование: curl -Ls [URL] | bash
# =============================================================================

set -e

VERSION="3.0.2-DEBIAN"
INSTALL_DIR="/opt/BOTinok"
BOT_SERVICE_NAME="bot"

# Цвета
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() { echo -e "${BLUE}[INSTALL]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

echo ""
echo "+======================================================+"
echo "|     🤖 BOTinok - Установка для Debian 11             |"
echo "|     Версия: $VERSION                                 |"
echo "+======================================================+"
echo ""

# Проверка root
if [ "$EUID" -ne 0 ]; then
    log_error "Запустите от root (sudo -i)"
    exit 1
fi
log_success "Права root подтверждены"

# Обновление
log "Обновление системы..."
apt-get update -y
DEBIAN_FRONTEND=noninteractive apt-get upgrade -y
log_success "Система обновлена"

# Зависимости
log "Установка зависимостей..."
apt-get install -y curl wget git nano htop python3 python3-venv python3-pip ufw cron
log_success "Зависимости установлены"

# Директория
mkdir -p $INSTALL_DIR/{data,logs,backups}
log_success "Директория создана: $INSTALL_DIR"

# Файлы бота
cd $INSTALL_DIR
log "Загрузка файлов бота..."
curl -Ls https://raw.githubusercontent.com/ShavlaK/BOTinok/main/bot/bot.py -o bot.py
curl -Ls https://raw.githubusercontent.com/ShavlaK/BOTinok/main/bot/requirements.txt -o requirements.txt
mkdir -p data
curl -Ls https://raw.githubusercontent.com/ShavlaK/BOTinok/main/bot/data/config.py -o data/config.py
curl -Ls https://raw.githubusercontent.com/ShavlaK/BOTinok/main/bot/data/lang.yml -o data/lang.yml
curl -Ls https://raw.githubusercontent.com/ShavlaK/BOTinok/main/bot/data/markup.py -o data/markup.py
curl -Ls https://raw.githubusercontent.com/ShavlaK/BOTinok/main/bot/data/markup_inline.py -o data/markup_inline.py
curl -Ls https://raw.githubusercontent.com/ShavlaK/BOTinok/main/bot/data/whitelist_utils.py -o data/whitelist_utils.py
log_success "Файлы загружены"

# Python venv
log "Создание Python окружения..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip -q
pip install setuptools wheel -q
log "Установка зависимостей Python..."
pip install -r requirements.txt -q
log_success "Python зависимости установлены"

# .env файл
log "Создание .env файла..."
cat > .env << 'EOF'
TOKEN_MAIN='8573117319:AAG1pMrC9iMV9xjIhDakHS6Ia67y8vbd3xA'
MY_ID_TELEG=475692645
NICK_HELP='ShavlaK'
NAME_AUTHOR_BOT='Aleksandr'
NAME_BOT_CONFIG='BOTinok'
X3_UI_PORT_PANEL=62050
PR_VLESS=True
PR_OUTLINE=False
PR_WIREGUARD=False
PR_PPTP=False
TEST_KEY=True
REF_SYSTEM=True
OPLATA=True
DONATE_SYSTEM=True
OBESH_PLATEZH=True
TARIF_1=149
TARIF_3=379
TARIF_6=749
TARIF_12=1349
COUNT_DAYS_TRIAL=2
COUNT_DAYS_REF=7
PARTNER_P=30
SUMM_VIVOD=200
KURS_RUB=94
KURS_XTR=2
LANG_DEFAULT='Russian'
EOF
log_success ".env создан"

# База данных
log "Создание базы данных..."
python3 << 'PYEOF'
import asyncio
from aiosqlite import connect

async def create_db():
    conn = await connect('data/db.db')
    cursor = await conn.cursor()
    
    await cursor.execute("""CREATE TABLE IF NOT EXISTS Users (
        User_id bigint PRIMARY KEY, First_Name text, Last_Name text, Nick text,
        Selected_id_Ustr integer DEFAULT(2), id_Otkuda integer DEFAULT(0),
        get_test_key bool DEFAULT(0), days_by_buy integer DEFAULT(30),
        Summ integer DEFAULT(0), Date date, Promo text, Date_reg date,
        isBan bool DEFAULT(0), isPayChangeProtocol bool DEFAULT(0),
        datePayChangeLocations date, Lang text, id_ref integer, tarifs text)""")
    
    await cursor.execute("""CREATE TABLE IF NOT EXISTS QR_Keys (
        User_id bigint, VPN_Key text, Date text, OS text, isAdminKey integer DEFAULT(0),
        ip_server text, CountDaysBuy integer DEFAULT(30), isActive bool DEFAULT(1),
        isChangeProtocol bool DEFAULT(0), DateChangeProtocol date, Payment_id text,
        isPremium bool DEFAULT(0), Protocol text, Keys_Data text, Podpiska integer,
        date_time datetime, summ integer)""")
    
    await cursor.execute("""CREATE TABLE IF NOT EXISTS Servers (
        ip text PRIMARY KEY, password text, count_keys integer DEFAULT(240),
        api_url text, cert_sha256 text, Location text, isPremium bool DEFAULT(0),
        is_marzban bool DEFAULT(0), is_pptp bool DEFAULT(0))""")
    
    await conn.commit()
    await conn.close()
    print("✅ База данных создана")

asyncio.run(create_db())
PYEOF

deactivate
log_success "База данных создана"

# Systemd сервис
log "Создание systemd сервиса..."
cat > /etc/systemd/system/bot.service << 'EOF'
[Unit]
Description=BOTinok - Telegram VPN Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/BOTinok
Environment=PATH=/opt/BOTinok/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
Environment=PYTHONUNBUFFERED=1
ExecStart=/opt/BOTinok/venv/bin/python /opt/BOTinok/bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable bot
log_success "Systemd сервис создан"

# Запуск
log "Запуск бота..."
systemctl start bot
sleep 3

if systemctl is-active --quiet bot; then
    log_success "✅ БОТ УСПЕШНО ЗАПУЩЕН!"
else
    log_error "❌ Не удалось запустить бота"
    log "Проверьте логи: journalctl -u bot -f"
fi

# Итоги
echo ""
echo "╔═══════════════════════════════════════════════════════╗"
echo "║           ✅ УСТАНОВКА ЗАВЕРШЕНА!                     ║"
echo "╚═══════════════════════════════════════════════════════╝"
echo ""
echo "📁 Директория: $INSTALL_DIR"
echo ""
echo "🔧 Команды:"
echo "   systemctl status bot   - Статус"
echo "   systemctl restart bot  - Перезапуск"
echo "   journalctl -u bot -f   - Логи"
echo ""
echo "📱 Telegram: @botinocheck1_bot → /start"
echo ""
