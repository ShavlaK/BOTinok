#!/bin/bash

# =============================================================================
# BOTinok - Автоматическая установка для Ubuntu Server 20.04 LTS
# =============================================================================
# Версия: 1.0.0
# Описание: Скрипт для автоматической установки BOTinok на Ubuntu 20.04
# Требования: Ubuntu Server 20.04 LTS, 2GB RAM, 10GB disk
# =============================================================================

set -e

# =============================================================================
# Конфигурация
# =============================================================================
VERSION="1.0.0-UBUNTU"
PROJECT_NAME="BOTinok"
INSTALL_DIR="/root/$PROJECT_NAME"
BOT_SERVICE_NAME="bot"
XUI_VERSION="v2.3.5"
PYTHON_VERSION="3.8"  # Python 3.8 по умолчанию в Ubuntu 20.04

# Цвета
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Логирование
log() {
    echo -e "${BLUE}[INSTALL]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

show_banner() {
    clear
    echo -e "${CYAN}"
    echo "╔═══════════════════════════════════════════════════════╗"
    echo "║                                                       ║"
    echo "║     🚀 BOTinok - Установка для Ubuntu 20.04 LTS       ║"
    echo "║                                                       ║"
    echo "║  Версия: $VERSION                                     ║"
    echo "║  GitHub: https://github.com/ShavlaK/BOTinok           ║"
    echo "║                                                       ║"
    echo "╚═══════════════════════════════════════════════════════╝"
    echo -e "${NC}"
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
# Проверка Ubuntu версии
# =============================================================================
check_ubuntu_version() {
    log "Проверка версии Ubuntu..."
    
    if [ -f /etc/os-release ]; then
        source /etc/os-release
        if [[ "$ID" != "ubuntu" ]]; then
            log_warning "Скрипт предназначен для Ubuntu, но обнаружена: $ID"
            log_warning "Продолжаем установку..."
        fi
        
        if [[ "$VERSION_ID" != "20.04" ]]; then
            log_warning "Обнаружена Ubuntu $VERSION_ID (рекомендуется 20.04)"
            log_warning "Продолжаем установку..."
        fi
        
        log_success "Ubuntu $VERSION_ID ($ID)"
    else
        log_error "Не удалось определить версию ОС"
        exit 1
    fi
}

# =============================================================================
# Проверка мощностей сервера
# =============================================================================
check_server() {
    log "Проверка мощностей сервера..."
    
    # RAM
    TOTAL_RAM_KB=$(grep MemTotal /proc/meminfo | awk '{print $2}')
    TOTAL_RAM_MB=$((TOTAL_RAM_KB / 1024))
    
    if [ $TOTAL_RAM_MB -lt 1024 ]; then
        log_warning "Мало RAM: ${TOTAL_RAM_MB} MB (рекомендуется 2GB+)"
    else
        log_success "RAM: ${TOTAL_RAM_MB} MB"
    fi
    
    # Disk
    DISK_FREE_KB=$(df -k / | tail -1 | awk '{print $4}')
    DISK_FREE_GB=$((DISK_FREE_KB / 1024 / 1024))
    
    if [ $DISK_FREE_GB -lt 5 ]; then
        log_warning "Мало места: ${DISK_FREE_GB} GB (рекомендуется 10GB+)"
    else
        log_success "Disk: ${DISK_FREE_GB} GB свободно"
    fi
    
    export TOTAL_RAM_MB
    export DISK_FREE_GB
}

# =============================================================================
# Обновление системы
# =============================================================================
update_system() {
    log "Обновление системы..."
    
    # Обновляем списки пакетов
    apt-get update -y
    
    # Обновляем пакеты
    DEBIAN_FRONTEND=noninteractive apt-get upgrade -y
    
    # Устанавливаем необходимые пакеты для add-apt-repository
    apt-get install -y software-properties-common apt-transport-https ca-certificates
    
    log_success "Система обновлена"
}

# =============================================================================
# Установка зависимостей
# =============================================================================
install_dependencies() {
    log "Установка зависимостей..."
    
    # Основные пакеты
    apt-get install -y \
        curl \
        wget \
        git \
        nano \
        htop \
        net-tools \
        unzip \
        zip \
        jq \
        build-essential \
        libnss3-dev \
        zlib1g-dev \
        libgdbm-dev \
        libncurses5-dev \
        libssl-dev \
        libffi-dev \
        libreadline-dev \
        libsqlite3-dev \
        libbz2-dev \
        liblzma-dev \
        python3 \
        python3-venv \
        python3-dev \
        python3-pip \
        socat \
        ufw \
        cron \
        supervisor
    
    # Добавляем репозиторий для Python 3.11 (опционально, но рекомендуется)
    log "Добавление репозитория Deadsnakes для Python 3.11..."
    add-apt-repository -y ppa:deadsnakes/ppa
    
    # Обновляем после добавления репозитория
    apt-get update -y
    
    # Устанавливаем Python 3.11
    log "Установка Python 3.11..."
    apt-get install -y python3.11 python3.11-venv python3.11-dev
    
    log_success "Зависимости установлены"
}

# =============================================================================
# Установка Docker (опционально, для будущих версий)
# =============================================================================
install_docker() {
    log "Установка Docker..."
    
    # Проверяем есть ли Docker
    if command -v docker &> /dev/null; then
        log_success "Docker уже установлен"
        return 0
    fi
    
    # Скачиваем скрипт установки Docker
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    
    # Добавляем пользователя root в группу docker
    usermod -aG docker root
    
    log_success "Docker установлен"
}

# =============================================================================
# Установка Python зависимостей (ЧЕРЕЗ VENV)
# =============================================================================
install_python_deps() {
    log "Установка Python зависимостей..."

    cd $INSTALL_DIR

    # Создаём виртуальное окружение если нет
    if [ ! -d "$INSTALL_DIR/venv" ]; then
        log "Создание виртуального окружения Python..."
        
        # Используем Python 3.11 если доступен, иначе 3.8
        if command -v python3.11 &> /dev/null; then
            python3.11 -m venv venv
            log_success "Виртуальное окружение создано (Python 3.11)"
        else
            python3 -m venv venv
            log_success "Виртуальное окружение создано (Python 3.8)"
        fi
    fi

    # Активируем venv
    source $INSTALL_DIR/venv/bin/activate

    # Обновляем pip
    log "Обновление pip..."
    python -m pip install --upgrade pip --quiet

    # Устанавливаем зависимости
    if [ -f "$INSTALL_DIR/requirements.txt" ]; then
        log "Установка зависимостей из requirements.txt..."
        pip install -r $INSTALL_DIR/requirements.txt --quiet
        log_success "Зависимости установлены"
    else
        log_warning "requirements.txt не найден"
    fi

    # Деактивируем venv
    deactivate 2>/dev/null || true
    
    cd - > /dev/null
}

# =============================================================================
# Установка 3X-UI панели (ПОЛНОСТЬЮ АВТОМАТИЧЕСКИ)
# =============================================================================
install_xui() {
    log "Установка 3X-UI панели..."

    # Проверяем установлена ли панель
    if [ -f /usr/local/x-ui/x-ui ]; then
        log_success "3X-UI уже установлена"
        # Получаем существующие параметры
        XUI_PORT=$(/usr/local/x-ui/x-ui setting -show 2>/dev/null | grep "Port" | awk '{print $2}')
        XUI_USERNAME=$(/usr/local/x-ui/x-ui setting -show 2>/dev/null | grep "Username" | awk '{print $2}')
        return 0
    fi

    # Генерируем безопасные параметры
    XUI_PORT=$((RANDOM % 10000 + 10000))  # Порт 10000-20000
    XUI_USERNAME="admin$(shuf -i 1000-9999 -n 1)"
    XUI_PASSWORD=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 16 | head -n 1)
    XUI_BASE_PATH=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 15 | head -n 1)
    
    log "Генерация параметров..."
    log "  Порт панели: $XUI_PORT"
    log "  Пользователь: $XUI_USERNAME"
    log "  Пароль: ******"
    log "  Base Path: /$XUI_BASE_PATH"

    # Скачиваем установщик 3X-UI
    curl -Ls https://raw.githubusercontent.com/mhsanaei/3x-ui/master/install.sh > /tmp/x-ui-install.sh
    chmod +x /tmp/x-ui-install.sh
    
    # Устанавливаем с переменными окружения (полностью автоматически)
    export XUI_PANEL_PORT=$XUI_PORT
    export XUI_PANEL_USERNAME=$XUI_USERNAME
    export XUI_PANEL_PASSWORD=$XUI_PASSWORD
    export XUI_PANEL_BASE_PATH=$XUI_BASE_PATH
    
    # Автоматическая установка (перенаправляем весь ввод)
    yes "" | bash /tmp/x-ui-install.sh >/dev/null 2>&1
    
    # Очищаем
    rm -f /tmp/x-ui-install.sh
    unset XUI_PANEL_PORT XUI_PANEL_USERNAME XUI_PANEL_PASSWORD XUI_PANEL_BASE_PATH

    # Настраиваем SSL (автоматически, IP сертификат)
    log "Настройка SSL сертификата..."
    
    # Получаем внешний IP
    EXTERNAL_IP=$(curl -s ifconfig.me)
    log "  Внешний IP: $EXTERNAL_IP"
    
    # Устанавливаем acme.sh для SSL (если нет)
    if ! command -v ~/.acme.sh/acme.sh &> /dev/null; then
        curl https://get.acme.sh | sh &>/dev/null
        source ~/.bashrc
    fi
    
    # Создаём SSL сертификат для IP
    ~/.acme.sh/acme.sh --issue --standalone -d $EXTERNAL_IP --listen-v4 --force &>/dev/null
    
    # Устанавливаем сертификат в 3X-UI
    ~/.acme.sh/acme.sh --install-cert -d $EXTERNAL_IP \
        --key-file       /root/private.key  \
        --fullchain-file /root/cert.crt \
        --reloadcmd     "systemctl force-reload x-ui" &>/dev/null
    
    # Настраиваем 3X-UI на использование сертификата
    /usr/local/x-ui/x-ui cert -s &>/dev/null

    # Сохраняем учётные данные
    cat > $INSTALL_DIR/xui_credentials.txt << EOF
════════════════════════════════════════════════════════
  🔐 3X-UI PANEL CREDENTIALS
════════════════════════════════════════════════════════
  URL:      https://$EXTERNAL_IP:$XUI_PORT/$XUI_BASE_PATH
  Username: $XUI_USERNAME
  Password: $XUI_PASSWORD
  
  ⚠️  СОХРАНИТЕ ЭТИ ДАННЫЕ!
════════════════════════════════════════════════════════
EOF

    log_success "3X-UI установлена"
    log "🔐 Учётные данные сохранены в: $INSTALL_DIR/xui_credentials.txt"

    # Экспортируем для использования в боте
    export XUI_PORT=$XUI_PORT
    export XUI_USERNAME=$XUI_USERNAME
    export XUI_PASSWORD=$XUI_PASSWORD
    export EXTERNAL_IP=$EXTERNAL_IP
    export XUI_BASE_PATH=$XUI_BASE_PATH
}

# =============================================================================
# Настройка бота (ПОЛНОСТЬЮ АВТОМАТИЧЕСКИ)
# =============================================================================
setup_bot() {
    log "Настройка бота..."

    # Создаём директорию
    mkdir -p $INSTALL_DIR
    mkdir -p $INSTALL_DIR/data
    mkdir -p $INSTALL_DIR/logs

    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

    if [ -d "$SCRIPT_DIR/bot" ]; then
        # Копируем локальные файлы
        log "Копирование файлов бота..."
        cp -r $SCRIPT_DIR/bot/* $INSTALL_DIR/
    else
        # Загружаем из GitHub
        log "Загрузка файлов бота из GitHub..."
        cd $INSTALL_DIR

        curl -Ls https://raw.githubusercontent.com/ShavlaK/BOTinok/main/bot/bot.py -o bot.py
        curl -Ls https://raw.githubusercontent.com/ShavlaK/BOTinok/main/bot/requirements.txt -o requirements.txt

        mkdir -p data
        curl -Ls https://raw.githubusercontent.com/ShavlaK/BOTinok/main/bot/data/config.py -o data/config.py
        curl -Ls https://raw.githubusercontent.com/ShavlaK/BOTinok/main/bot/data/lang.yml -o data/lang.yml
        curl -Ls https://raw.githubusercontent.com/ShavlaK/BOTinok/main/bot/data/markup.py -o data/markup.py
        curl -Ls https://raw.githubusercontent.com/ShavlaK/BOTinok/main/bot/data/markup_inline.py -o data/markup_inline.py
        
        # Копируем медиафайлы если есть
        curl -Ls https://raw.githubusercontent.com/ShavlaK/BOTinok/main/bot/data/LOGO.png -o data/LOGO.png 2>/dev/null || true
        curl -Ls https://raw.githubusercontent.com/ShavlaK/BOTinok/main/bot/data/download.jpg -o data/download.jpg 2>/dev/null || true
    fi

    log_success "Файлы бота загружены"
}

# =============================================================================
# Создание .env файла (ИНТЕРАКТИВНОЕ - с автозаполнением)
# =============================================================================
create_env() {
    log "Создание файла конфигурации..."

    # Создаём директорию если нет
    mkdir -p $INSTALL_DIR
    
    # Получаем внешний IP
    EXTERNAL_IP=$(curl -s ifconfig.me)
    
    echo ""
    echo "═══════════════════════════════════════════════════════"
    echo "  🤖 НАСТРОЙКА BOTinok"
    echo "═══════════════════════════════════════════════════════"
    echo ""
    echo "📝 Для работы бота необходимы:"
    echo ""
    echo "1️⃣  Токен бота Telegram"
    echo "   📌 Получить: @BotFather → /newbot или /mybots"
    echo "   📌 Пример: 1234567890:ABCdefGHIjklMNOpqrsTUVwxyz"
    echo ""
    
    # Запрашиваем токен
    while true; do
        read -p "🔑 Введите токен бота: " USER_TOKEN
        
        # Проверяем формат токена (должен содержать :)
        if [[ "$USER_TOKEN" == *":"* ]] && [ ${#USER_TOKEN} -ge 40 ]; then
            log_success "Токен принят"
            break
        else
            log_error "Неверный формат токена! Попробуйте ещё раз."
            log_info "Пример: 1234567890:ABCdefGHIjklMNOpqrsTUVwxyz"
        fi
    done
    
    echo ""
    echo "2️⃣  ID Telegram администратора"
    echo "   📌 Узнать: @userinfobot (просто отправьте боту сообщение)"
    echo "   📌 Пример: 123456789"
    echo ""
    
    # Запрашиваем ID
    while true; do
        read -p "🔑 Введите ваш Telegram ID: " USER_ID
        
        # Проверяем что это число
        if [[ "$USER_ID" =~ ^[0-9]+$ ]]; then
            log_success "ID принят"
            break
        else
            log_error "ID должен быть числом! Попробуйте ещё раз."
        fi
    done
    
    echo ""
    echo "3️⃣  Никнейм для поддержки (без @)"
    echo "   📌 Пример: codenlx"
    echo ""
    
    read -p "👤 Ник поддержки: " USER_NICK
    if [ -z "$USER_NICK" ]; then
        USER_NICK="codenlx"
    fi
    
    echo ""
    echo "4️⃣  Название бота"
    echo "   📌 Только буквы и цифры"
    echo "   📌 Пример: BOTinok"
    echo ""
    
    read -p "🏷️ Название бота: " USER_BOT_NAME
    if [ -z "$USER_BOT_NAME" ]; then
        USER_BOT_NAME="BOTinok"
    fi
    
    # Создаём .env файл с данными пользователя
    cat > $INSTALL_DIR/.env << EOF
# ═══════════════════════════════════════════════════════════════════════════
# BOTinok Configuration - Автоматически сгенерированный файл
# GitHub: https://github.com/ShavlaK/BOTinok
# Ubuntu Server 20.04 LTS
# Сгенерировано: $(date '+%Y-%m-%d %H:%M:%S')
# ═══════════════════════════════════════════════════════════════════════════

# -----------------------------------------------------------------------------
# 🔴 ОБЯЗАТЕЛЬНЫЕ ПАРАМЕТРЫ (заполнено автоматически)
# -----------------------------------------------------------------------------

# Токен бота Telegram
TOKEN_MAIN='$USER_TOKEN'

# ID Telegram администратора
MY_ID_TELEG=$USER_ID

# -----------------------------------------------------------------------------
# ⚙️ ОСНОВНЫЕ НАСТРОЙКИ
# -----------------------------------------------------------------------------

# Ник для поддержки (без @)
NICK_HELP='$USER_NICK'

# Имя автора
NAME_AUTHOR_BOT='Александр'

# Название бота для конфигов
NAME_BOT_CONFIG='$USER_BOT_NAME'

# Порт 3X-UI панели (указывается автоматически)
X3_UI_PORT_PANEL=$XUI_PORT

# -----------------------------------------------------------------------------
# 🔒 ПРОТОКОЛЫ (True=включен, False=выключен)
# -----------------------------------------------------------------------------

PR_VLESS=True           # ✅ VLESS - основной протокол (рекомендуется)
PR_OUTLINE=False        # ❌ Outline - отключен
PR_WIREGUARD=False      # ❌ WireGuard - отключен
PR_PPTP=False           # ❌ PPTP - отключен

# -----------------------------------------------------------------------------
# 🎯 ФУНКЦИИ (True=включено, False=выключено)
# -----------------------------------------------------------------------------

TEST_KEY=True           # Выдавать тестовый период (2 дня)
REF_SYSTEM=True         # Включить реферальную систему
REF_SYSTEM_AFTER_PAY=False
OPLATA=True             # Включить оплату
DONATE_SYSTEM=True      # Система пожертвований
WHY_BOT_PAY=True        # Показывать почему VPN платный
OBESH_PLATEZH=True      # Обещанный платеж (+1 день раз в месяц)
SEND_QR=False           # Отправлять QR (для VLESS не нужно)
INLINE_MODE=False       # Inline кнопки
IS_OTCHET=False         # Ежедневные отчёты

# -----------------------------------------------------------------------------
# 💰 ТАРИФЫ (рубли)
# -----------------------------------------------------------------------------

TARIF_1=149             # 1 месяц
TARIF_3=379             # 3 месяца
TARIF_6=749             # 6 месяцев
TARIF_12=1349           # 12 месяцев

# -----------------------------------------------------------------------------
# 👥 РЕФЕРАЛЬНАЯ СИСТЕМА
# -----------------------------------------------------------------------------

COUNT_DAYS_TRIAL=2      # Пробный период (дней)
COUNT_DAYS_REF=7        # Дней доступа за приглашённого
PARTNER_P=30            # Процент партнёра (%)
SUMM_VIVOD=200          # Мин. сумма вывода (₽)

# -----------------------------------------------------------------------------
# 🌍 ДОПОЛНИТЕЛЬНО
# -----------------------------------------------------------------------------

KURS_RUB=94             # Курс доллара
KURS_XTR=2              # Курс USDT
LANG_DEFAULT='Русский'  # Язык по умолчанию

# ═══════════════════════════════════════════════════════════════════════════
# 📚 Документация: https://github.com/ShavlaK/BOTinok#readme
# 🆘 Поддержка: https://github.com/ShavlaK/BOTinok/issues
# ═══════════════════════════════════════════════════════════════════════════
EOF

    log_success "Файл .env создан и заполнен!"
    log "Сохранён в: $INSTALL_DIR/.env"
}

# =============================================================================
# Создание systemd сервиса (ПРАВИЛЬНЫЙ ФОРМАТ + VENV)
# =============================================================================
create_service() {
    log "Создание systemd сервиса..."

    cat > /etc/systemd/system/$BOT_SERVICE_NAME.service << 'EOF'
[Unit]
Description=BOTinok - Telegram VPN Bot
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/BOTinok

# Активируем виртуальное окружение и запускаем бота
Environment=PATH=/root/BOTinok/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
Environment=PYTHONUNBUFFERED=1
Environment=PYTHONIOENCODING=utf-8

ExecStart=/root/BOTinok/venv/bin/python /root/BOTinok/bot.py
Restart=always
RestartSec=10
RestartPreventExitStatus=1

# Логирование
StandardOutput=journal
StandardError=journal
SyslogIdentifier=botinok

# Лимиты
LimitNOFILE=65535
Nice=-5

# Безопасность
NoNewPrivileges=false

[Install]
WantedBy=multi-user.target
EOF

    # Перезагружаем systemd и включаем сервис
    systemctl daemon-reload
    systemctl enable $BOT_SERVICE_NAME
    
    log_success "Systemd сервис создан"
}

# =============================================================================
# Настройка брандмауэра UFW
# =============================================================================
setup_firewall() {
    log "Настройка брандмауэра UFW..."
    
    # Проверяем установлен ли ufw
    if ! command -v ufw &> /dev/null; then
        apt-get install -y ufw
    fi
    
    # Открываем необходимые порты
    ufw allow 22/tcp    # SSH
    ufw allow 80/tcp    # HTTP (для SSL)
    ufw allow 443/tcp   # HTTPS
    
    # Если известен порт 3X-UI, открываем его
    if [ ! -z "$XUI_PORT" ]; then
        ufw allow $XUI_PORT/tcp
    fi
    
    # Включаем брандмауэр (но не блокируем текущую сессию SSH)
    echo "y" | ufw enable
    
    log_success "Брандмауэр настроен"
}

# =============================================================================
# Настройка cron задач
# =============================================================================
setup_cron() {
    log "Настройка cron задач..."
    
    # Создаём скрипт для ежедневного бэкапа
    cat > $INSTALL_DIR/backup.sh << 'EOF'
#!/bin/bash
# Ежедневный бэкап базы данных и конфигов

BACKUP_DIR="/root/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Бэкап базы данных
cp /root/BOTinok/data/*.db $BACKUP_DIR/db_backup_$DATE.tar.gz 2>/dev/null || true

# Бэкап конфигов
tar -czf $BACKUP_DIR/config_backup_$DATE.tar.gz /root/BOTinok/.env /root/BOTinok/data/config.py

# Удаляем старые бэкапы (старше 7 дней)
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "Backup completed: $DATE"
EOF
    
    chmod +x $INSTALL_DIR/backup.sh
    
    # Добавляем в cron
    (crontab -l 2>/dev/null; echo "0 3 * * * $INSTALL_DIR/backup.sh") | crontab -
    
    log_success "Cron задачи настроены"
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
# Вывод итогов (ПОДРОБНАЯ ИНСТРУКЦИЯ)
# =============================================================================
print_summary() {
    EXTERNAL_IP=$(curl -s ifconfig.me)
    
    echo ""
    echo "╔═══════════════════════════════════════════════════════╗"
    echo "║                                                       ║"
    echo "║           ✅ УСТАНОВКА ЗАВЕРШЕНА!                     ║"
    echo "║                                                       ║"
    echo "╚═══════════════════════════════════════════════════════╝"
    echo ""
    echo "📁 Директория установки: $INSTALL_DIR"
    echo ""
    echo "═══════════════════════════════════════════════════════"
    echo "  🎯 СЛЕДУЮЩИЕ ШАГИ"
    echo "═══════════════════════════════════════════════════════"
    echo ""
    echo "✅ Файл .env уже создан и заполнен!"
    echo ""
    echo "📝 Проверьте данные в файле:"
    echo "───────────────────────────────────────────────────────"
    echo "   nano $INSTALL_DIR/.env"
    echo ""
    echo "📝 Если нужно изменить - отредактируйте и сохраните:"
    echo "───────────────────────────────────────────────────────"
    echo "   Ctrl+O → Enter → Ctrl+X"
    echo ""
    echo "📝 Перезапустите бота:"
    echo "───────────────────────────────────────────────────────"
    echo "   systemctl restart bot"
    echo ""
    echo "📝 Проверьте статус:"
    echo "───────────────────────────────────────────────────────"
    echo "   systemctl status bot"
    echo ""
    echo "📝 Запустите бота в Telegram:"
    echo "───────────────────────────────────────────────────────"
    echo "   Откройте бота и нажмите /start"
    echo ""
    echo "═══════════════════════════════════════════════════════"
    echo "  🔐 3X-UI ПАНЕЛЬ (УПРАВЛЕНИЕ КЛЮЧАМИ)"
    echo "═══════════════════════════════════════════════════════"
    
    if [ -f $INSTALL_DIR/xui_credentials.txt ]; then
        echo ""
        cat $INSTALL_DIR/xui_credentials.txt
    fi
    
    echo ""
    echo "═══════════════════════════════════════════════════════"
    echo "  🔧 КОМАНДЫ УПРАВЛЕНИЯ БОТОМ"
    echo "═══════════════════════════════════════════════════════"
    echo ""
    echo "   systemctl status bot      - Статус бота"
    echo "   systemctl restart bot     - Перезапуск"
    echo "   systemctl stop bot        - Остановка"
    echo "   systemctl start bot       - Запуск"
    echo "   journalctl -u bot -f      - Логи в реальном времени"
    echo "   tail -f $INSTALL_DIR/logs/bot_*.log - Логи бота"
    echo ""
    echo "═══════════════════════════════════════════════════════"
    echo "  📚 ДОПОЛНИТЕЛЬНАЯ ИНФОРМАЦИЯ"
    echo "═══════════════════════════════════════════════════════"
    echo ""
    echo "   GitHub:      https://github.com/ShavlaK/BOTinok"
    echo "   Документация: https://github.com/ShavlaK/BOTinok#readme"
    echo "   Troubleshooting: https://github.com/ShavlaK/BOTinok/blob/main/TROUBLESHOOTING.md"
    echo "   Ubuntu Setup: https://github.com/ShavlaK/BOTinok/blob/main/UBUNTU_SETUP.md"
    echo ""
    echo "═══════════════════════════════════════════════════════"
    echo ""
    echo "💡 СОВЕТ: После проверки бота, добавьте сервер через:"
    echo "   /add_server в Telegram боте"
    echo ""
    echo "✅ Всё готово к использованию!"
    echo ""
}

# =============================================================================
# Основная функция
# =============================================================================
main() {
    show_banner

    check_root
    check_ubuntu_version
    check_server
    update_system
    install_dependencies
    install_python_deps      # Установка pip и зависимостей
    install_xui
    setup_bot                # Загрузка файлов бота
    install_python_deps      # Повторная установка зависимостей (после загрузки requirements.txt)
    create_env
    create_service
    setup_firewall
    setup_cron
    start_bot
    print_summary
}

# Обработка аргументов
case "${1:-}" in
    --help|-h)
        echo "Использование: $0 [OPTIONS]"
        echo ""
        echo "OPTIONS:"
        echo "  --help     Показать эту справку"
        exit 0
        ;;
esac

# Запуск
main "$@"
