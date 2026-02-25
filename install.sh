#!/bin/bash

# =============================================================================
# BOT Bot - Автоматическая установка
# =============================================================================
# Версия: 1.0
# Описание: Скрипт для автоматической установки BOT бота с 3X-UI панелью
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
    echo "║           🚀 BOT Bot - Автоматическая установка       ║"
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
# Установка 3X-UI панели
# =============================================================================
install_xui() {
    log "Установка 3X-UI панели..."
    
    # Проверяем установлена ли панель
    if [ -f /usr/local/x-ui/x-ui ]; then
        log_success "3X-UI уже установлена"
        return 0
    fi
    
    # Загружаем и устанавливаем
    bash <(curl -Ls https://raw.githubusercontent.com/mhsanaei/3x-ui/master/install.sh)
    
    # Настраиваем порт и учётные данные
    XUI_PORT=$((RANDOM % 10000 + 10000))
    XUI_USERNAME="admin$(shuf -i 1000-9999 -n 1)"
    XUI_PASSWORD=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 12 | head -n 1)
    
    /usr/local/x-ui/x-ui setting -username $XUI_USERNAME -password $XUI_PASSWORD -port $XUI_PORT
    
    # Сохраняем учётные данные
    cat > $INSTALL_DIR/xui_credentials.txt << EOF
════════════════════════════════════════
  3X-UI PANEL CREDENTIALS
════════════════════════════════════════
  URL:      http://$(curl -s ifconfig.me):$XUI_PORT
  Username: $XUI_USERNAME
  Password: $XUI_PASSWORD
════════════════════════════════════════
EOF
    
    log_success "3X-UI установлена"
    log "Учётные данные сохранены в: $INSTALL_DIR/xui_credentials.txt"
    
    # Экспортируем для использования в боте
    export XUI_PORT=$XUI_PORT
    export XUI_USERNAME=$XUI_USERNAME
    export XUI_PASSWORD=$XUI_PASSWORD
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
# Создание .env файла
# =============================================================================
create_env() {
    log "Создание файла конфигурации..."
    
    cat > $INSTALL_DIR/.env << EOF
# =============================================================================
# BOT Bot Configuration
# =============================================================================

# Токен бота (получить в @BotFather)
TOKEN_MAIN=''

# ID Telegram администратора (узнать в @userinfobot)
MY_ID_TELEG=

# Ник для поддержки
NICK_HELP='codenlx'

# Имя автора BOT
NAME_AUTHOR_BOT='Александр'

# Название бота для конфигов
NAME_BOT_CONFIG='VPCoden'

# Порт 3X-UI панели
X3_UI_PORT_PANEL=$XUI_PORT

# =============================================================================
# Дополнительные настройки
# =============================================================================

# Протоколы (True/False)
PR_VLESS=True
PR_OUTLINE=False
PR_WIREGUARD=False
PR_PPTP=False

# Функции
TEST_KEY=True
REF_SYSTEM=True
OPLATA=True
DONATE_SYSTEM=True
WHY_BOT_PAY=True
OBESH_PLATEZH=True
SEND_QR=False

# Тарифы (руб)
TARIF_1=149
TARIF_3=379
TARIF_6=749
TARIF_12=1349

# Реферальная система
COUNT_DAYS_TRIAL=2
COUNT_DAYS_REF=7
PARTNER_P=30
SUMM_VIVOD=200
EOF
    
    log_success "Файл конфигурации создан: $INSTALL_DIR/.env"
    log_warning "Отредактируйте .env и укажите TOKEN_MAIN и MY_ID_TELEG"
}

# =============================================================================
# Создание systemd сервиса
# =============================================================================
create_service() {
    log "Создание systemd сервиса..."
    
    cat > /etc/systemd/system/$BOT_SERVICE_NAME.service << EOF
[Unit]
Description=BOT Bot Service
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
# Вывод итогов
# =============================================================================
print_summary() {
    echo ""
    echo "╔═══════════════════════════════════════════════════════╗"
    echo "║                                                       ║"
    echo "║           ✅ УСТАНОВКА ЗАВЕРШЕНА!                     ║"
    echo "║                                                       ║"
    echo "╚═══════════════════════════════════════════════════════╝"
    echo ""
    echo "📁 Директория установки: $INSTALL_DIR"
    echo ""
    echo "🔧 Команды управления:"
    echo "   systemctl status bot     - Статус бота"
    echo "   systemctl restart bot    - Перезапуск бота"
    echo "   systemctl stop bot       - Остановка бота"
    echo "   journalctl -u bot -f     - Логи бота"
    echo ""
    echo "📝 Следующие шаги:"
    echo "   1. Отредактируйте $INSTALL_DIR/.env"
    echo "   2. Укажите TOKEN_MAIN и MY_ID_TELEG"
    echo "   3. Перезапустите бота: systemctl restart bot"
    echo "   4. Запустите бота: /start"
    echo ""
    
    if [ -f $INSTALL_DIR/xui_credentials.txt ]; then
        echo "🔐 3X-UI панель:"
        cat $INSTALL_DIR/xui_credentials.txt
        echo ""
    fi
    
    echo "📚 Документация: https://github.com/ShavlaK/BOTinok"
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
