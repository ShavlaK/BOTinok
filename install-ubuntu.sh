#!/bin/bash

# =============================================================================
# BOTinok - Автоматическая установка для Ubuntu Server 20.04 LTS
# =============================================================================
# Версия: 2.0.0
# Описание: Полностью автоматическая установка BOTinok
# Требования: Ubuntu Server 20.04 LTS, 2GB RAM, 10GB disk
# =============================================================================

set -e

# =============================================================================
# Конфигурация
# =============================================================================
VERSION="2.0.0-UBUNTU"
PROJECT_NAME="BOTinok"
INSTALL_DIR="/root/$PROJECT_NAME"
BOT_SERVICE_NAME="bot"
PYTHON_VERSION="3.8"

# Цвета
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Логирование
log() { echo -e "${BLUE}[INSTALL]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

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
    apt-get update -y
    DEBIAN_FRONTEND=noninteractive apt-get upgrade -y
    apt-get install -y software-properties-common apt-transport-https ca-certificates
    log_success "Система обновлена"
}

# =============================================================================
# Установка зависимостей
# =============================================================================
install_dependencies() {
    log "Установка зависимостей..."
    
    apt-get install -y \
        curl wget git nano htop net-tools unzip zip jq \
        build-essential libnss3-dev zlib1g-dev libgdbm-dev libncurses5-dev \
        libssl-dev libffi-dev libreadline-dev libsqlite3-dev libbz2-dev liblzma-dev \
        python3 python3-venv python3-dev python3-pip \
        socat ufw cron supervisor
    
    log_success "Зависимости установлены"
    PYTHON_VER=$(python3 --version 2>&1 | awk '{print $2}')
    log "Python $PYTHON_VER доступен"
}

# =============================================================================
# Создание директории проекта
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
    curl -Ls https://raw.githubusercontent.com/ShavlaK/BOTinok/main/bot/bot.py -o bot.py
    curl -Ls https://raw.githubusercontent.com/ShavlaK/BOTinok/main/bot/requirements.txt -o requirements.txt
    
    # Скачиваем файлы конфигурации
    curl -Ls https://raw.githubusercontent.com/ShavlaK/BOTinok/main/bot/data/config.py -o data/config.py
    curl -Ls https://raw.githubusercontent.com/ShavlaK/BOTinok/main/bot/data/lang.yml -o data/lang.yml
    curl -Ls https://raw.githubusercontent.com/ShavlaK/BOTinok/main/bot/data/markup.py -o data/markup.py
    curl -Ls https://raw.githubusercontent.com/ShavlaK/BOTinok/main/bot/data/markup_inline.py -o data/markup_inline.py
    
    # Скачиваем медиафайлы
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
    
    if [ ! -d "$INSTALL_DIR/venv" ]; then
        log "Создание виртуального окружения Python..."
        python3 -m venv venv
        PYTHON_VER=$(python3 --version 2>&1 | awk '{print $2}')
        log_success "Виртуальное окружение создано (Python $PYTHON_VER)"
    fi
    
    source $INSTALL_DIR/venv/bin/activate
    log "Обновление pip..."
    python -m pip install --upgrade pip --quiet
    
    if [ -f "$INSTALL_DIR/requirements.txt" ]; then
        log "Установка зависимостей из requirements.txt..."
        pip install -r $INSTALL_DIR/requirements.txt --quiet
        log_success "Зависимости установлены"
    else
        log_error "requirements.txt не найден!"
        return 1
    fi
    
    deactivate 2>/dev/null || true
    cd - > /dev/null
}

# =============================================================================
# Установка 3X-UI панели
# =============================================================================
install_xui() {
    log "Установка 3X-UI панели..."

    if [ -f /usr/local/x-ui/x-ui ]; then
        log_success "3X-UI уже установлена"
        XUI_PORT=$(/usr/local/x-ui/x-ui setting -show 2>/dev/null | grep "Port" | awk '{print $2}')
        return 0
    fi

    # Генерируем параметры
    XUI_PORT=$((RANDOM % 10000 + 10000))
    XUI_USERNAME="admin$(shuf -i 1000-9999 -n 1)"
    XUI_PASSWORD=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 16 | head -n 1)
    XUI_BASE_PATH=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 15 | head -n 1)
    
    log "Генерация параметров..."
    log "  Порт панели: $XUI_PORT"
    log "  Пользователь: $XUI_USERNAME"
    log "  Пароль: ******"
    log "  Base Path: /$XUI_BASE_PATH"

    # Скачиваем и устанавливаем 3X-UI
    curl -Ls https://raw.githubusercontent.com/mhsanaei/3x-ui/master/install.sh > /tmp/x-ui-install.sh
    chmod +x /tmp/x-ui-install.sh
    
    export XUI_PANEL_PORT=$XUI_PORT
    export XUI_PANEL_USERNAME=$XUI_USERNAME
    export XUI_PANEL_PASSWORD=$XUI_PASSWORD
    export XUI_PANEL_BASE_PATH=$XUI_BASE_PATH
    
    yes "" | bash /tmp/x-ui-install.sh >/dev/null 2>&1
    rm -f /tmp/x-ui-install.sh
    unset XUI_PANEL_PORT XUI_PANEL_USERNAME XUI_PANEL_PASSWORD XUI_PANEL_BASE_PATH

    # Настраиваем SSL
    log "Настройка SSL сертификата..."
    EXTERNAL_IP=$(curl -s ifconfig.me)
    log "  Внешний IP: $EXTERNAL_IP"
    
    if ! command -v ~/.acme.sh/acme.sh &> /dev/null; then
        curl https://get.acme.sh | sh &>/dev/null
        source ~/.bashrc
    fi
    
    ~/.acme.sh/acme.sh --issue --standalone -d $EXTERNAL_IP --listen-v4 --force &>/dev/null
    ~/.acme.sh/acme.sh --install-cert -d $EXTERNAL_IP \
        --key-file /root/private.key \
        --fullchain-file /root/cert.crt \
        --reloadcmd "systemctl force-reload x-ui" &>/dev/null
    
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
    log "🔐 Учётные данные: $INSTALL_DIR/xui_credentials.txt"
    
    export XUI_PORT=$XUI_PORT
    export XUI_USERNAME=$XUI_USERNAME
    export XUI_PASSWORD=$XUI_PASSWORD
    export EXTERNAL_IP=$EXTERNAL_IP
    export XUI_BASE_PATH=$XUI_BASE_PATH
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
    echo "   📌 Пример: 1234567890:ABCdefGHIjklMNOpqrsTUVwxyz"
    echo ""
    
    while true; do
        read -p "🔑 Введите токен бота: " USER_TOKEN
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
    echo "   📌 Пример: codenlx"
    echo ""
    
    read -p "👤 Ник поддержки: " USER_NICK
    [ -z "$USER_NICK" ] && USER_NICK="codenlx"
    
    echo ""
    echo "4️⃣  Название бота"
    echo "   📌 Только буквы и цифры"
    echo "   📌 Пример: BOTinok"
    echo ""
    
    read -p "🏷️ Название бота: " USER_BOT_NAME
    [ -z "$USER_BOT_NAME" ] && USER_BOT_NAME="BOTinok"
    
    # Создаём .env файл
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

TOKEN_MAIN='$USER_TOKEN'
MY_ID_TELEG=$USER_ID

# -----------------------------------------------------------------------------
# ⚙️ ОСНОВНЫЕ НАСТРОЙКИ
# -----------------------------------------------------------------------------

NICK_HELP='$USER_NICK'
NAME_AUTHOR_BOT='Александр'
NAME_BOT_CONFIG='$USER_BOT_NAME'
X3_UI_PORT_PANEL=$XUI_PORT

# -----------------------------------------------------------------------------
# 🔒 ПРОТОКОЛЫ
# -----------------------------------------------------------------------------

PR_VLESS=True
PR_OUTLINE=False
PR_WIREGUARD=False
PR_PPTP=False

# -----------------------------------------------------------------------------
# 🎯 ФУНКЦИИ
# -----------------------------------------------------------------------------

TEST_KEY=True
REF_SYSTEM=True
REF_SYSTEM_AFTER_PAY=False
OPLATA=True
DONATE_SYSTEM=True
WHY_BOT_PAY=True
OBESH_PLATEZH=True
SEND_QR=False
INLINE_MODE=False
IS_OTCHET=False

# -----------------------------------------------------------------------------
# 💰 ТАРИФЫ
# -----------------------------------------------------------------------------

TARIF_1=149
TARIF_3=379
TARIF_6=749
TARIF_12=1349

# -----------------------------------------------------------------------------
# 👥 РЕФЕРАЛЬНАЯ СИСТЕМА
# -----------------------------------------------------------------------------

COUNT_DAYS_TRIAL=2
COUNT_DAYS_REF=7
PARTNER_P=30
SUMM_VIVOD=200

# -----------------------------------------------------------------------------
# 🌍 ДОПОЛНИТЕЛЬНО
# -----------------------------------------------------------------------------

KURS_RUB=94
KURS_XTR=2
LANG_DEFAULT='Русский'

# ═══════════════════════════════════════════════════════════════════════════
# 📚 Документация: https://github.com/ShavlaK/BOTinok#readme
# 🆘 Поддержка: https://github.com/ShavlaK/BOTinok/issues
# ═══════════════════════════════════════════════════════════════════════════
EOF

    log_success "Файл .env создан и заполнен!"
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
Wants=network-online.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/BOTinok

Environment=PATH=/root/BOTinok/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
Environment=PYTHONUNBUFFERED=1
Environment=PYTHONIOENCODING=utf-8

ExecStart=/root/BOTinok/venv/bin/python /root/BOTinok/bot.py
Restart=always
RestartSec=10
RestartPreventExitStatus=1

StandardOutput=journal
StandardError=journal
SyslogIdentifier=botinok

LimitNOFILE=65535
Nice=-5
NoNewPrivileges=false

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable $BOT_SERVICE_NAME
    log_success "Systemd сервис создан"
}

# =============================================================================
# Настройка брандмауэра
# =============================================================================
setup_firewall() {
    log "Настройка брандмауэра UFW..."
    
    if ! command -v ufw &> /dev/null; then
        apt-get install -y ufw
    fi
    
    ufw allow 22/tcp
    ufw allow 80/tcp
    ufw allow 443/tcp
    
    if [ ! -z "$XUI_PORT" ]; then
        ufw allow $XUI_PORT/tcp
    fi
    
    echo "y" | ufw enable
    log_success "Брандмауэр настроен"
}

# =============================================================================
# Настройка cron задач
# =============================================================================
setup_cron() {
    log "Настройка cron задач..."
    
    cat > $INSTALL_DIR/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/root/backups"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR
cp /root/BOTinok/data/*.db $BACKUP_DIR/db_backup_$DATE.tar.gz 2>/dev/null || true
tar -czf $BACKUP_DIR/config_backup_$DATE.tar.gz /root/BOTinok/.env /root/BOTinok/data/config.py
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
echo "Backup completed: $DATE"
EOF
    
    chmod +x $INSTALL_DIR/backup.sh
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
# Вывод итогов
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
    echo "📁 Директория: $INSTALL_DIR"
    echo ""
    echo "═══════════════════════════════════════════════════════"
    echo "  ✅ СТАТУС УСТАНОВКИ"
    echo "═══════════════════════════════════════════════════════"
    echo ""
    echo "✅ Файл .env создан и заполнен"
    echo "✅ Виртуальное окружение Python создано"
    echo "✅ Зависимости установлены"
    echo "✅ 3X-UI панель установлена"
    echo "✅ Systemd сервис создан"
    echo "✅ Брандмауэр настроен"
    echo ""
    
    if systemctl is-active --quiet $BOT_SERVICE_NAME; then
        echo "✅ Бот ЗАПУЩЕН и работает"
    else
        echo "⚠️  Бот требует перезапуска после проверки .env"
    fi
    
    echo ""
    echo "═══════════════════════════════════════════════════════"
    echo "  🔐 3X-UI ПАНЕЛЬ"
    echo "═══════════════════════════════════════════════════════"
    
    if [ -f $INSTALL_DIR/xui_credentials.txt ]; then
        echo ""
        cat $INSTALL_DIR/xui_credentials.txt
    fi
    
    echo ""
    echo "═══════════════════════════════════════════════════════"
    echo "  🔧 КОМАНДЫ УПРАВЛЕНИЯ"
    echo "═══════════════════════════════════════════════════════"
    echo ""
    echo "   systemctl status bot      - Статус бота"
    echo "   systemctl restart bot     - Перезапуск"
    echo "   systemctl stop bot        - Остановка"
    echo "   journalctl -u bot -f      - Логи"
    echo ""
    echo "═══════════════════════════════════════════════════════"
    echo "  📚 ДОКУМЕНТАЦИЯ"
    echo "═══════════════════════════════════════════════════════"
    echo ""
    echo "   GitHub: https://github.com/ShavlaK/BOTinok"
    echo "   Docs: https://github.com/ShavlaK/BOTinok#readme"
    echo "   Help: https://github.com/ShavlaK/BOTinok/blob/main/TROUBLESHOOTING.md"
    echo ""
    echo "═══════════════════════════════════════════════════════"
    echo ""
    echo "💡 СЛЕДУЮЩИЕ ДЕЙСТВИЯ:"
    echo ""
    echo "1. Проверьте файл .env:"
    echo "   nano $INSTALL_DIR/.env"
    echo ""
    echo "2. Если всё верно, перезапустите бота:"
    echo "   systemctl restart bot"
    echo ""
    echo "3. Проверьте статус:"
    echo "   systemctl status bot"
    echo ""
    echo "4. Откройте бота в Telegram и нажмите /start"
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
    create_project_dir
    download_bot_files
    install_python_deps
    install_xui
    create_env
    create_service
    setup_firewall
    setup_cron
    start_bot
    print_summary
}

# Запуск
main "$@"
