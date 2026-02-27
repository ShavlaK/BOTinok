#!/bin/bash

# =============================================================================
# BOTinok - Автоматическая установка Telegram бота
# =============================================================================
# Версия: 3.0.0
# Описание: Установка ТОЛЬКО бота. 3X-UI устанавливается через бота (/add_server)
# Требования: Ubuntu Server 20.04 LTS, 2GB RAM, 10GB disk
# =============================================================================

set -e

# =============================================================================
# Конфигурация
# =============================================================================
VERSION="3.0.0"
PROJECT_NAME="BOTinok"
INSTALL_DIR="/root/$PROJECT_NAME"
BOT_SERVICE_NAME="bot"

# Цвета
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Логирование
log() { echo -e "${BLUE}[INSTALL]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

show_banner() {
    clear
    echo ""
    echo "+======================================================+"
    echo "|                                                      |"
    echo "|     🤖 BOTinok - Установка Telegram бота             |"
    echo "|                                                      |"
    echo "|  Версия: $VERSION                                    |"
    echo "|  GitHub: https://github.com/ShavlaK/BOTinok          |"
    echo "|                                                      |"
    echo "+======================================================+"
    echo ""
}

# =============================================================================
# Проверка прав root
# =============================================================================
check_root() {
    log "Проверка прав доступа..."
    if [ "$EUID" -ne 0 ]; then
        log_error "Запустите скрипт от root (sudo -i)"
        exit 1
    fi
    log_success "Права root подтверждены"
}

# =============================================================================
# Очистка apt lock
# =============================================================================
cleanup_apt() {
    log "Очистка apt lock файлов..."
    killall -9 apt-get apt 2>/dev/null || true
    sleep 2
    rm -f /var/lib/dpkg/lock-frontend /var/lib/dpkg/lock /var/cache/apt/archives/lock
    dpkg --configure -a 2>/dev/null || true
    log_success "apt очищен"
}

# =============================================================================
# Проверка Ubuntu
# =============================================================================
check_ubuntu() {
    log "Проверка версии Ubuntu..."
    if [ -f /etc/os-release ]; then
        source /etc/os-release
        log_success "Ubuntu $VERSION_ID ($ID)"
    else
        log_error "Не удалось определить версию ОС"
        exit 1
    fi
}

# =============================================================================
# Проверка мощностей
# =============================================================================
check_server() {
    log "Проверка мощностей сервера..."
    TOTAL_RAM_KB=$(grep MemTotal /proc/meminfo | awk '{print $2}')
    TOTAL_RAM_MB=$((TOTAL_RAM_KB / 1024))
    DISK_FREE_KB=$(df -k / | tail -1 | awk '{print $4}')
    DISK_FREE_GB=$((DISK_FREE_KB / 1024 / 1024))
    
    if [ $TOTAL_RAM_MB -lt 1024 ]; then
        log_warning "Мало RAM: ${TOTAL_RAM_MB} MB (рекомендуется 2GB+)"
    else
        log_success "RAM: ${TOTAL_RAM_MB} MB"
    fi
    
    if [ $DISK_FREE_GB -lt 5 ]; then
        log_warning "Мало места: ${DISK_FREE_GB} GB (рекомендуется 10GB+)"
    else
        log_success "Disk: ${DISK_FREE_GB} GB свободно"
    fi
}

# =============================================================================
# Обновление системы
# =============================================================================
update_system() {
    log "Обновление системы..."
    apt-get update -y || { log_error "Не удалось обновить списки пакетов"; exit 1; }
    DEBIAN_FRONTEND=noninteractive apt-get upgrade -y || log_warning "Некоторые пакеты не обновились"
    log_success "Система обновлена"
}

# =============================================================================
# Установка зависимостей
# =============================================================================
install_dependencies() {
    log "Установка зависимостей..."
    
    apt-get install -y \
        curl wget git nano htop \
        build-essential libssl-dev libffi-dev \
        python3 python3-venv python3-dev python3-pip \
        ufw cron || {
        log_error "Не удалось установить зависимости"
        exit 1
    }
    
    log_success "Зависимости установлены"
}

# =============================================================================
# Создание директории
# =============================================================================
create_project_dir() {
    log "Создание директории проекта..."
    mkdir -p $INSTALL_DIR
    mkdir -p $INSTALL_DIR/data
    mkdir -p $INSTALL_DIR/logs
    mkdir -p $INSTALL_DIR/backups
    log_success "Директория создана: $INSTALL_DIR"
}

# =============================================================================
# Загрузка файлов бота
# =============================================================================
download_bot_files() {
    log "Загрузка файлов бота из GitHub..."
    cd $INSTALL_DIR
    
    # Скачиваем основные файлы
    curl -Ls https://raw.githubusercontent.com/ShavlaK/BOTinok/main/bot/bot.py -o bot.py || {
        log_error "Не удалось загрузить bot.py"
        exit 1
    }
    
    curl -Ls https://raw.githubusercontent.com/ShavlaK/BOTinok/main/bot/requirements.txt -o requirements.txt || {
        log_error "Не удалось загрузить requirements.txt"
        exit 1
    }
    
    # Скачиваем файлы конфигурации
    mkdir -p data
    curl -Ls https://raw.githubusercontent.com/ShavlaK/BOTinok/main/bot/data/config.py -o data/config.py || true
    curl -Ls https://raw.githubusercontent.com/ShavlaK/BOTinok/main/bot/data/lang.yml -o data/lang.yml || true
    curl -Ls https://raw.githubusercontent.com/ShavlaK/BOTinok/main/bot/data/markup.py -o data/markup.py || true
    curl -Ls https://raw.githubusercontent.com/ShavlaK/BOTinok/main/bot/data/markup_inline.py -o data/markup_inline.py || true
    curl -Ls https://raw.githubusercontent.com/ShavlaK/BOTinok/main/bot/data/whitelist_utils.py -o data/whitelist_utils.py || true
    
    # Медиафайлы
    curl -Ls https://raw.githubusercontent.com/ShavlaK/BOTinok/main/bot/data/LOGO.png -o data/LOGO.png 2>/dev/null || true
    curl -Ls https://raw.githubusercontent.com/ShavlaK/BOTinok/main/bot/data/download.jpg -o data/download.jpg 2>/dev/null || true
    curl -Ls https://raw.githubusercontent.com/ShavlaK/BOTinok/main/bot/data/upload.jpg -o data/upload.jpg 2>/dev/null || true
    
    log_success "Файлы бота загружены"
    cd - > /dev/null
}

# =============================================================================
# Установка Python зависимостей
# =============================================================================
install_python_deps() {
    log "Установка Python зависимостей..."
    cd $INSTALL_DIR

    # Создаём venv
    if [ ! -d "$INSTALL_DIR/venv" ]; then
        log "Создание виртуального окружения Python..."
        python3 -m venv venv || { log_error "Не удалось создать venv"; exit 1; }
        log_success "Виртуальное окружение создано"
    fi

    source $INSTALL_DIR/venv/bin/activate
    
    # Обновляем pip
    python -m pip install --upgrade pip -q || log_warning "Не удалось обновить pip"
    
    # Устанавливаем setuptools
    pip install setuptools wheel -q || { log_error "Не удалось установить setuptools"; exit 1; }
    
    # Устанавливаем зависимости
    if [ -f "$INSTALL_DIR/requirements.txt" ]; then
        log "Установка зависимостей из requirements.txt..."
        pip install -r $INSTALL_DIR/requirements.txt -q || {
            log_error "Не удалось установить зависимости"
            exit 1
        }
        log_success "Зависимости установлены"
    else
        log_error "requirements.txt не найден!"
        exit 1
    fi

    deactivate 2>/dev/null || true
    cd - > /dev/null
}

# =============================================================================
# Создание .env файла (ИНТЕРАКТИВНОЕ)
# =============================================================================
create_env() {
    log "Создание файла конфигурации..."
    mkdir -p $INSTALL_DIR
    
    echo ""
    echo "═══════════════════════════════════════════════════════"
    echo "  🤖 НАСТРОЙКА BOTinok"
    echo "═══════════════════════════════════════════════════════"
    echo ""
    echo "📝 Для работы бота необходимы:"
    echo ""
    echo "1️⃣  Токен бота Telegram"
    echo "   📌 Получить: @BotFather → /newbot или /mybots"
    echo ""
    
    # Запрашиваем токен
    while true; do
        read -p "🔑 Введите токен бота: " USER_TOKEN
        if [[ "$USER_TOKEN" == *":"* ]] && [ ${#USER_TOKEN} -ge 40 ]; then
            log_success "Токен принят"
            break
        else
            log_error "Неверный формат токена! Попробуйте ещё раз."
        fi
    done
    
    echo ""
    echo "2️⃣  ID Telegram администратора"
    echo "   📌 Узнать: @userinfobot"
    echo ""
    
    # Запрашиваем ID
    while true; do
        read -p "🔑 Введите ваш Telegram ID: " USER_ID
        if [[ "$USER_ID" =~ ^[0-9]+$ ]]; then
            log_success "ID принят"
            break
        else
            log_error "ID должен быть числом! Попробуйте ещё раз."
        fi
    done
    
    echo ""
    echo "3️⃣  Никнейм для поддержки (без @)"
    read -p "👤 Ник поддержки: " USER_NICK
    [ -z "$USER_NICK" ] && USER_NICK="codenlx"
    
    echo ""
    echo "4️⃣  Название бота"
    read -p "🏷️ Название бота: " USER_BOT_NAME
    [ -z "$USER_BOT_NAME" ] && USER_BOT_NAME="BOTinok"
    
    # Создаём .env файл
    cat > $INSTALL_DIR/.env << EOF
# BOTinok Configuration
# Сгенерировано: $(date '+%Y-%m-%d %H:%M:%S')

TOKEN_MAIN='$USER_TOKEN'
MY_ID_TELEG=$USER_ID
NICK_HELP='$USER_NICK'
NAME_AUTHOR_BOT='Александр'
NAME_BOT_CONFIG='$USER_BOT_NAME'
X3_UI_PORT_PANEL=62050

# Протоколы
PR_VLESS=True
PR_OUTLINE=False
PR_WIREGUARD=False
PR_PPTP=False

# Функции
TEST_KEY=True
REF_SYSTEM=True
OPLATA=True
DONATE_SYSTEM=True
OBESH_PLATEZH=True

# Тарифы
TARIF_1=149
TARIF_3=379
TARIF_6=749
TARIF_12=1349

# Реферальная система
COUNT_DAYS_TRIAL=2
COUNT_DAYS_REF=7
PARTNER_P=30
SUMM_VIVOD=200

# Дополнительно
KURS_RUB=94
KURS_XTR=2
LANG_DEFAULT='Русский'
EOF

    log_success "Файл .env создан и заполнен!"
}

# =============================================================================
# Создание базы данных
# =============================================================================
create_database() {
    log "Создание базы данных..."
    
    cd $INSTALL_DIR
    source venv/bin/activate
    
    python3 << 'PYEOF'
import asyncio
from aiosqlite import connect
import os

async def create_db():
    db_path = 'data/db.db'
    
    if os.path.exists(db_path):
        print("База данных уже существует")
        return
    
    conn = await connect(db_path)
    cursor = await conn.cursor()
    
    # Users
    await cursor.execute("""
        CREATE TABLE IF NOT EXISTS Users (
            User_id bigint PRIMARY KEY NOT NULL,
            First_Name text, Last_Name text, Nick text,
            Selected_id_Ustr integer DEFAULT(2),
            id_Otkuda integer DEFAULT(0),
            get_test_key bool DEFAULT(0),
            days_by_buy integer DEFAULT(30),
            Summ integer DEFAULT(0),
            Date date, Promo text, Date_reg date,
            isBan bool DEFAULT(0),
            isPayChangeProtocol bool DEFAULT(0),
            datePayChangeLocations date,
            Lang text, id_ref integer, tarifs text
        )
    """)
    
    # QR_Keys
    await cursor.execute("""
        CREATE TABLE IF NOT EXISTS QR_Keys (
            User_id bigint, VPN_Key text, Date text, OS text,
            isAdminKey integer DEFAULT(0), ip_server text,
            CountDaysBuy integer DEFAULT(30), isActive bool DEFAULT(1),
            isChangeProtocol bool DEFAULT(0), DateChangeProtocol date,
            Payment_id text, isPremium bool DEFAULT(0),
            Protocol text, Keys_Data text, Podpiska integer,
            date_time datetime, summ integer
        )
    """)
    
    # Servers
    await cursor.execute("""
        CREATE TABLE IF NOT EXISTS Servers (
            ip text PRIMARY KEY, password text,
            count_keys integer DEFAULT(240),
            api_url text, cert_sha256 text, Location text,
            isPremium bool DEFAULT(0), is_marzban bool DEFAULT(0),
            is_pptp bool DEFAULT(0)
        )
    """)
    
    await conn.commit()
    await conn.close()
    print("✅ База данных создана")

asyncio.run(create_db())
PYEOF
    
    deactivate
    cd - > /dev/null
    log_success "База данных создана"
}

# =============================================================================
# Создание systemd сервиса
# =============================================================================
create_service() {
    log "Создание systemd сервиса..."

    cat > /etc/systemd/system/$BOT_SERVICE_NAME.service << 'EOF'
[Unit]
Description=BOTinok - Telegram VPN Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/BOTinok
Environment=PATH=/root/BOTinok/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
Environment=PYTHONUNBUFFERED=1
ExecStart=/root/BOTinok/venv/bin/python /root/BOTinok/bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable $BOT_SERVICE_NAME
    log_success "Systemd сервис создан"
}

# =============================================================================
# Запуск бота
# =============================================================================
start_bot() {
    log "Запуск бота..."
    systemctl start $BOT_SERVICE_NAME
    sleep 3
    
    if systemctl is-active --quiet $BOT_SERVICE_NAME; then
        log_success "Бот успешно запущен"
    else
        log_error "Не удалось запустить бота"
        log "Проверьте логи: journalctl -u bot -f"
    fi
}

# =============================================================================
# Вывод итогов
# =============================================================================
print_summary() {
    echo ""
    echo "╔═══════════════════════════════════════════════════════╗"
    echo "║           ✅ УСТАНОВКА ЗАВЕРШЕНА!                     ║"
    echo "╚═══════════════════════════════════════════════════════╝"
    echo ""
    echo "📁 Директория: $INSTALL_DIR"
    echo ""
    echo "═══════════════════════════════════════════════════════"
    echo "  ✅ ЧТО УСТАНОВЛЕНО"
    echo "═══════════════════════════════════════════════════════"
    echo ""
    echo "✅ Telegram бот"
    echo "✅ Python зависимости"
    echo "✅ База данных"
    echo "✅ Systemd сервис"
    echo ""
    echo "═══════════════════════════════════════════════════════"
    echo "  📋 СЛЕДУЮЩИЕ ШАГИ"
    echo "═══════════════════════════════════════════════════════"
    echo ""
    echo "1. Откройте @botinocheck1_bot в Telegram"
    echo "2. Нажмите /start"
    echo "3. Для добавления сервера с 3X-UI:"
    echo "   /add_server ip password кол-во_ключей локация"
    echo ""
    echo "═══════════════════════════════════════════════════════"
    echo "  🔧 КОМАНДЫ УПРАВЛЕНИЯ"
    echo "═══════════════════════════════════════════════════════"
    echo ""
    echo "   systemctl status bot   - Статус"
    echo "   systemctl restart bot  - Перезапуск"
    echo "   journalctl -u bot -f   - Логи"
    echo ""
    echo "✅ Бот готов к работе!"
    echo ""
}

# =============================================================================
# Основная функция
# =============================================================================
main() {
    show_banner
    check_root
    cleanup_apt
    check_ubuntu
    check_server
    update_system
    install_dependencies
    create_project_dir
    download_bot_files
    install_python_deps
    create_env
    create_database
    create_service
    start_bot
    print_summary
}

main "$@"
