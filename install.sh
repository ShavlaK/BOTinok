#!/bin/bash

# =============================================================================
# BOTinok - Автоматическая установка
# =============================================================================
# Версия: 1.0
# Описание: Скрипт для автоматической установки BOTinok с 3X-UI панелью
# Требования: Debian 11+, 2GB RAM (или 1GB + swap), 10GB disk
# =============================================================================

set -e

# =============================================================================
# Конфигурация
# =============================================================================
VERSION="1.0.0"
PROJECT_NAME="BOTinok"
INSTALL_DIR="/root/$PROJECT_NAME"
BOT_SERVICE_NAME="bot"
XUI_VERSION="v2.3.5"
PYTHON_VERSION="3.11"

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
    echo "║           🚀 BOTinok - Автоматическая установка       ║"
    echo "║                                                       ║"
    echo "║  Версия: $VERSION                                     ║"
    echo "║  GitHub: https://github.com/ShavlaK/BOTinok     ║"
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
# Проверка сервера
# =============================================================================
check_server() {
    log "Проверка мощностей сервера..."
    
    # Запускаем скрипт проверки
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    
    if [ -f "$SCRIPT_DIR/scripts/check_server.sh" ]; then
        bash "$SCRIPT_DIR/scripts/check_server.sh"
        
        # Загружаем результаты
        if [ -f /tmp/server_check_results.env ]; then
            source /tmp/server_check_results.env
            log_success "Проверка завершена: ${TOTAL_RAM_MB} MB RAM, ${CPU_CORES} CPU"
        else
            log_warning "Не удалось загрузить результаты проверки"
            RECOMMENDED_VERSION="main"
        fi
    else
        log_warning "Скрипт проверки не найден, продолжаем установку..."
        RECOMMENDED_VERSION="main"
    fi
    
    # Проверка рекомендуемой версии
    if [ "$RECOMMENDED_VERSION" = "lite" ]; then
        log_warning "Ваш сервер слабый, рекомендуется Lite версия"
        echo ""
        read -p "Продолжить установку основной версии? (y/n): " -n 1 -r
        echo ""
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log "Используйте install-lite.sh для слабых серверов"
            exit 0
        fi
    fi
}

# =============================================================================
# Обновление системы
# =============================================================================
update_system() {
    log "Обновление системы..."
    
    apt-get update -y
    apt-get upgrade -y
    
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
        software-properties-common \
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
        liblzma-dev
    
    # Docker (если нет)
    if ! command -v docker &> /dev/null; then
        log "Установка Docker..."
        curl -fsSL https://get.docker.com -o get-docker.sh
        sh get-docker.sh
        rm get-docker.sh
    fi
    
    # Docker Compose (если нет)
    if ! command -v docker-compose &> /dev/null; then
        log "Установка Docker Compose..."
        curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        chmod +x /usr/local/bin/docker-compose
    fi
    
    log_success "Зависимости установлены"
}

# =============================================================================
# Установка Python
# =============================================================================
install_python() {
    log "Установка Python $PYTHON_VERSION..."
    
    # Проверяем есть ли Python 3.11
    if python3.11 --version &> /dev/null; then
        log_success "Python $PYTHON_VERSION уже установлен"
        return 0
    fi
    
    # Установка Python 3.11
    cd /tmp
    
    # Загружаем исходники
    wget -q https://www.python.org/ftp/python/$PYTHON_VERSION.4/Python-$PYTHON_VERSION.4.tgz
    tar -xzf Python-$PYTHON_VERSION.4.tgz
    cd Python-$PYTHON_VERSION.4
    
    # Компиляция
    ./configure --enable-optimizations
    make -j$(nproc)
    make install
    
    # Создаём симлинки
    ln -sf /usr/local/bin/python3.11 /usr/bin/python3.11
    ln -sf /usr/local/bin/pip3.11 /usr/bin/pip3.11
    
    # Очистка
    cd /tmp
    rm -rf Python-$PYTHON_VERSION.4*
    
    log_success "Python $PYTHON_VERSION установлен"
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
# Настройка бота
# =============================================================================
setup_bot() {
    log "Настройка бота..."
    
    # Создаём директорию
    mkdir -p $INSTALL_DIR
    
    # Копируем файлы бота
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    
    if [ -d "$SCRIPT_DIR/bot" ]; then
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
    fi
    
    # Устанавливаем зависимости Python
    log "Установка Python зависимостей..."
    cd $INSTALL_DIR
    pip3.11 install -r requirements.txt
    
    log_success "Бот настроен"
}

# =============================================================================
# Создание .env файла (ПОЛНОСТЬЮ ГОТОВЫЙ К РАБОТЕ)
# =============================================================================
create_env() {
    log "Создание файла конфигурации..."

    # Создаём директорию если нет
    mkdir -p $INSTALL_DIR

    # Генерируем временный токен если нет (пользователь заменит на свой)
    TEMP_TOKEN="TEMP_$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1)"
    
    # Получаем ID админа автоматически если возможно
    AUTO_ADMIN_ID="${MY_ID_TELEG:-0}"

    cat > $INSTALL_DIR/.env << EOF
# ═══════════════════════════════════════════════════════════════════════════
# BOTinok Configuration - Полностью готовый к работе файл
# GitHub: https://github.com/ShavlaK/BOTinok
# ═══════════════════════════════════════════════════════════════════════════
#
# 📝 ИНСТРУКЦИЯ ПО НАСТРОЙКЕ:
#
# 1. Откройте этот файл: nano /root/BOTinok/.env
#
# 2. Замените TOKEN_MAIN на токен вашего бота:
#    - Откройте @BotFather в Telegram
#    - Отправьте /mybots
#    - Выберите вашего бота
#    - Bot Settings → Generate Token
#    - Скопируйте токен и вставьте ниже вместо 'TEMP_...'
#
# 3. Замените MY_ID_TELEG на ваш Telegram ID:
#    - Откройте @userinfobot в Telegram
#    - Он покажет ваш ID
#    - Вставьте число вместо 0
#
# 4. Сохраните файл: Ctrl+O → Enter → Ctrl+X
#
# 5. Перезапустите бота: systemctl restart bot
#
# ═══════════════════════════════════════════════════════════════════════════

# -----------------------------------------------------------------------------
# 🔴 ОБЯЗАТЕЛЬНЫЕ ПАРАМЕТРЫ (замените значения!)
# -----------------------------------------------------------------------------

# Токен бота Telegram
# ПОЛУЧИТЬ: @BotFather → /mybots → Bot Settings → Generate Token
TOKEN_MAIN='$TEMP_TOKEN'

# ID Telegram администратора
# ПОЛУЧИТЬ: @userinfobot (просто отправьте боту любое сообщение)
MY_ID_TELEG=$AUTO_ADMIN_ID

# -----------------------------------------------------------------------------
# ⚙️ ОСНОВНЫЕ НАСТРОЙКИ (можно не менять)
# -----------------------------------------------------------------------------

# Ник для поддержки (без @)
NICK_HELP='codenlx'

# Имя автора
NAME_AUTHOR_BOT='Александр'

# Название бота для конфигов
NAME_BOT_CONFIG='BOTinok'

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

# Тестовые ключи
TEST_KEY=True           # Выдавать тестовый период (2 дня)

# Реферальная система
REF_SYSTEM=True         # Включить реферальную систему
REF_SYSTEM_AFTER_PAY=False  # Начислять дни только после оплаты

# Платёжная система
OPLATA=True             # Включить оплату

# Донаты
DONATE_SYSTEM=True      # Система пожертвований
WHY_BOT_PAY=True        # Показывать почему VPN платный
OBESH_PLATEZH=True      # Обещанный платеж (+1 день раз в месяц)

# QR-коды
SEND_QR=False           # Отправлять QR (для VLESS не нужно)

# Интерфейс
INLINE_MODE=False       # Inline кнопки (под сообщениями)
IS_OTCHET=False         # Ежедневные отчёты

# -----------------------------------------------------------------------------
# 💰 ТАРИФЫ (рубли)
# -----------------------------------------------------------------------------
# Укажите 0 чтобы отключить тариф

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

KURS_RUB=94             # Курс доллара (для конвертации)
KURS_XTR=2              # Курс USDT
LANG_DEFAULT='Русский'  # Язык по умолчанию

# ═══════════════════════════════════════════════════════════════════════════
# 📚 Документация: https://github.com/ShavlaK/BOTinok#readme
# 🆘 Поддержка: https://github.com/ShavlaK/BOTinok/issues
# ═══════════════════════════════════════════════════════════════════════════
EOF

    log_success "Файл .env создан"
    
    # Проверяем есть ли существующие данные
    if [ -f "$INSTALL_DIR/.env.backup" ]; then
        log "Восстановление предыдущих настроек..."
    fi
    
    log_warning "⚠️  ОТКРОЙТЕ .env И ЗАПОЛНИТЕ TOKEN_MAIN и MY_ID_TELEG"
    log_info "   nano $INSTALL_DIR/.env"
}

# =============================================================================
# Создание systemd сервиса
# =============================================================================
create_service() {
    log "Создание systemd сервиса..."
    
    cat > /etc/systemd/system/$BOT_SERVICE_NAME.service << EOF
[Unit]
Description=BOTinok Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$INSTALL_DIR
ExecStart=/usr/local/bin/python3.11 $INSTALL_DIR/bot.py
Restart=always
RestartSec=10
Environment=PYTHONUNBUFFERED=1

# Логирование
StandardOutput=journal
StandardError=journal
SyslogIdentifier=BOTinok

# Лимиты
LimitNOFILE=65535
Nice=-5

[Install]
WantedBy=multi-user.target
EOF
    
    # Перезагружаем systemd и включаем сервис
    systemctl daemon-reload
    systemctl enable $BOT_SERVICE_NAME
    
    log_success "Systemd сервис создан"
}

# =============================================================================
# Настройка брандмауэра
# =============================================================================
setup_firewall() {
    log "Настройка брандмауэра..."
    
    # Устанавливаем ufw если нет
    if ! command -v ufw &> /dev/null; then
        apt-get install -y ufw
    fi
    
    # Открываем порты
    ufw allow 22/tcp    # SSH
    ufw allow 80/tcp    # HTTP
    ufw allow 443/tcp   # HTTPS
    ufw allow $XUI_PORT/tcp  # 3X-UI панель
    
    # Включаем брандмауэр
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
    echo "  🎯 СЛЕДУЮЩИЕ ШАГИ (ВЫПОЛНИТЬ ПОСЛЕДОВАТЕЛЬНО)"
    echo "═══════════════════════════════════════════════════════"
    echo ""
    echo "📝 ШАГ 1: Откройте файл конфигурации"
    echo "───────────────────────────────────────────────────────"
    echo "   nano $INSTALL_DIR/.env"
    echo ""
    echo "📝 ШАГ 2: Укажите обязательные параметры"
    echo "───────────────────────────────────────────────────────"
    echo "   TOKEN_MAIN='ваш_токен_бота'     # Получить в @BotFather"
    echo "   MY_ID_TELEG=ваш_id              # Узнать в @userinfobot"
    echo ""
    echo "   Пример:"
    echo "   TOKEN_MAIN='1234567890:ABCdefGHIjklMNOpqrsTUVwxyz'"
    echo "   MY_ID_TELEG=123456789"
    echo ""
    echo "📝 ШАГ 3: Сохраните файл"
    echo "───────────────────────────────────────────────────────"
    echo "   Ctrl+O → Enter → Ctrl+X"
    echo ""
    echo "📝 ШАГ 4: Перезапустите бота"
    echo "───────────────────────────────────────────────────────"
    echo "   systemctl restart bot"
    echo ""
    echo "📝 ШАГ 5: Проверьте статус"
    echo "───────────────────────────────────────────────────────"
    echo "   systemctl status bot"
    echo ""
    echo "📝 ШАГ 6: Запустите бота в Telegram"
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
    echo ""
    echo "═══════════════════════════════════════════════════════"
    echo ""
    echo "💡 СОВЕТ: После настройки бота, добавьте сервер через:"
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
    check_server
    update_system
    install_dependencies
    install_python
    install_xui
    setup_bot
    create_env
    create_service
    setup_firewall
    setup_cron
    start_bot
    print_summary
}

# Обработка аргументов
case "${1:-}" in
    --lite)
        log "Режим Lite установки"
        # Тут можно добавить логику для Lite версии
        ;;
    --help|-h)
        echo "Использование: $0 [OPTIONS]"
        echo ""
        echo "OPTIONS:"
        echo "  --lite     Lite версия для слабых серверов"
        echo "  --help     Показать эту справку"
        exit 0
        ;;
esac

# Запуск
main "$@"
