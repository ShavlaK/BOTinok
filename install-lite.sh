#!/bin/bash

# =============================================================================
# VPN Bot - Lite версия для слабых серверов
# =============================================================================
# Версия: 1.0
# Описание: Облегчённая установка для серверов с 512MB-1GB RAM
# Требования: Debian 11+, 512MB RAM, 5GB disk
# =============================================================================

set -e

# =============================================================================
# Конфигурация
# =============================================================================
VERSION="1.0.0-LITE"
PROJECT_NAME="BOTinok-lite"
INSTALL_DIR="/root/$PROJECT_NAME"
BOT_SERVICE_NAME="bot-lite"
PYTHON_VERSION="3.9"  # Более старая версия для экономии памяти

# Цвета
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Логирование
log() {
    echo -e "${BLUE}[LITE]${NC} $1"
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
    echo "║        🚀 VPN Bot Lite - Для слабых серверов          ║"
    echo "║                                                       ║"
    echo "║  Версия: $VERSION                                     ║"
    echo "║  RAM: 512MB - 1GB                                     ║"
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
# Проверка RAM
# =============================================================================
check_ram() {
    log "Проверка оперативной памяти..."
    
    TOTAL_RAM_KB=$(grep MemTotal /proc/meminfo | awk '{print $2}')
    TOTAL_RAM_MB=$((TOTAL_RAM_KB / 1024))
    
    if [ $TOTAL_RAM_MB -gt 2048 ]; then
        log_warning "У вас много RAM (${TOTAL_RAM_MB} MB)"
        log_warning "Рекомендуется основная версия (install.sh)"
        echo ""
        read -p "Продолжить Lite установку? (y/n): " -n 1 -r
        echo ""
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 0
        fi
    elif [ $TOTAL_RAM_MB -lt 512 ]; then
        log_error "Недостаточно RAM: ${TOTAL_RAM_MB} MB"
        log_error "Минимум: 512 MB"
        exit 1
    fi
    
    log_success "RAM: ${TOTAL_RAM_MB} MB"
    export TOTAL_RAM_MB
}

# =============================================================================
# Создание swap (обязательно для Lite)
# =============================================================================
create_swap() {
    log "Создание swap файла..."
    
    SWAP_TOTAL_KB=$(grep SwapTotal /proc/meminfo | awk '{print $2}')
    SWAP_TOTAL_MB=$((SWAP_TOTAL_KB / 1024))
    
    if [ $SWAP_TOTAL_MB -gt 0 ]; then
        log_success "Swap уже существует: ${SWAP_TOTAL_MB} MB"
        return 0
    fi
    
    # Определяем размер swap
    if [ $TOTAL_RAM_MB -lt 512 ]; then
        SWAP_SIZE=1024  # 1GB
    else
        SWAP_SIZE=2048  # 2GB
    fi
    
    # Проверяем свободное место
    DISK_FREE_KB=$(df -k / | tail -1 | awk '{print $4}')
    DISK_FREE_MB=$((DISK_FREE_KB / 1024))
    
    if [ $DISK_FREE_MB -lt $SWAP_SIZE ]; then
        SWAP_SIZE=$((DISK_FREE_MB / 2))
        log_warning "Мало места на диске, создаём swap: ${SWAP_SIZE} MB"
    fi
    
    log "Размер swap: ${SWAP_SIZE} MB"
    
    # Создаём swap
    dd if=/dev/zero of=/swapfile bs=1M count=$SWAP_SIZE status=progress
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    
    # Добавляем в fstab
    if ! grep -q "/swapfile" /etc/fstab; then
        echo "/swapfile none swap sw 0 0" >> /etc/fstab
    fi
    
    log_success "Swap создан: ${SWAP_SIZE} MB"
}

# =============================================================================
# Обновление системы (минимальное)
# =============================================================================
update_system() {
    log "Обновление системы..."
    
    apt-get update -y
    apt-get upgrade -y -o Dpkg::Options::="--force-confold"
    
    log_success "Система обновлена"
}

# =============================================================================
# Установка минимальных зависимостей
# =============================================================================
install_dependencies() {
    log "Установка минимальных зависимостей..."
    
    # Только необходимые пакеты
    apt-get install -y \
        curl \
        wget \
        git \
        nano \
        htop \
        python3 \
        python3-pip \
        python3-venv \
        sqlite3
    
    log_success "Зависимости установлены"
}

# =============================================================================
# Установка 3X-UI (облегчённая)
# =============================================================================
install_xui() {
    log "Установка 3X-UI панели..."
    
    if [ -f /usr/local/x-ui/x-ui ]; then
        log_success "3X-UI уже установлена"
        return 0
    fi
    
    # Устанавливаем 3X-UI
    bash <(curl -Ls https://raw.githubusercontent.com/mhsanaei/3x-ui/master/install.sh)
    
    # Настраиваем
    XUI_PORT=$((RANDOM % 10000 + 10000))
    XUI_USERNAME="admin$(shuf -i 1000-9999 -n 1)"
    XUI_PASSWORD=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 12 | head -n 1)
    
    /usr/local/x-ui/x-ui setting -username $XUI_USERNAME -password $XUI_PASSWORD -port $XUI_PORT
    
    # Сохраняем учётные данные
    cat > $INSTALL_DIR/xui_credentials.txt << EOF
════════════════════════════════════════
  3X-UI PANEL CREDENTIALS (LITE)
════════════════════════════════════════
  URL:      http://$(curl -s ifconfig.me):$XUI_PORT
  Username: $XUI_USERNAME
  Password: $XUI_PASSWORD
════════════════════════════════════════
EOF
    
    log_success "3X-UI установлена"
    
    export XUI_PORT=$XUI_PORT
}

# =============================================================================
# Настройка бота (облегчённая)
# =============================================================================
setup_bot() {
    log "Настройка бота..."
    
    mkdir -p $INSTALL_DIR
    cd $INSTALL_DIR
    
    # Загружаем только необходимые файлы
    log "Загрузка файлов бота..."
    
    curl -Ls https://raw.githubusercontent.com/ShavlaK/BOTinok/main/bot/bot.py -o bot.py
    curl -Ls https://raw.githubusercontent.com/ShavlaK/BOTinok/main/bot/requirements.txt -o requirements.txt
    
    mkdir -p data
    curl -Ls https://raw.githubusercontent.com/ShavlaK/BOTinok/main/bot/data/config.py -o data/config.py
    curl -Ls https://raw.githubusercontent.com/ShavlaK/BOTinok/main/bot/data/lang.yml -o data/lang.yml
    curl -Ls https://raw.githubusercontent.com/ShavlaK/BOTinok/main/bot/data/markup.py -o data/markup.py
    
    # Создаём виртуальное окружение для экономии памяти
    log "Создание виртуального окружения..."
    python3 -m venv venv
    source venv/bin/activate
    
    # Устанавливаем зависимости
    log "Установка Python зависимостей..."
    pip install --upgrade pip
    pip install -r requirements.txt
    
    log_success "Бот настроен"
}

# =============================================================================
# Создание .env файла
# =============================================================================
create_env() {
    log "Создание файла конфигурации..."
    
    cat > $INSTALL_DIR/.env << EOF
# =============================================================================
# VPN Bot Configuration - LITE VERSION
# =============================================================================

# Токен бота
TOKEN_MAIN=''

# ID Telegram администратора
MY_ID_TELEG=

# Ник для поддержки
NICK_HELP='codenlx'

# Имя автора VPN
NAME_AUTHOR_VPN='Александр'

# Название бота
NAME_VPN_CONFIG='VPCoden'

# Порт 3X-UI
X3_UI_PORT_PANEL=$XUI_PORT

# =============================================================================
# Lite настройки (оптимизировано для слабых серверов)
# =============================================================================

# Только VLESS
PR_VLESS=True
PR_OUTLINE=False
PR_WIREGUARD=False
PR_PPTP=False

# Отключаем тяжёлые функции
SEND_QR=False
IS_OTCHET=False
INLINE_MODE=True

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
EOF
    
    log_success "Файл конфигурации создан"
}

# =============================================================================
# Создание systemd сервиса (облегчённый)
# =============================================================================
create_service() {
    log "Создание systemd сервиса..."
    
    cat > /etc/systemd/system/$BOT_SERVICE_NAME.service << EOF
[Unit]
Description=VPN Bot Service (Lite)
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$INSTALL_DIR
ExecStart=$INSTALL_DIR/venv/bin/python bot.py
Restart=always
RestartSec=10

# Логирование
StandardOutput=journal
StandardError=journal
SyslogIdentifier=BOTinok-lite

# Ограничения памяти для Lite версии
MemoryLimit=512M
MemoryHigh=400M

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
    log "Настройка брандмауэра..."
    
    if ! command -v ufw &> /dev/null; then
        apt-get install -y ufw
    fi
    
    ufw allow 22/tcp
    ufw allow 80/tcp
    ufw allow 443/tcp
    ufw allow $XUI_PORT/tcp
    
    echo "y" | ufw enable
    
    log_success "Брандмауэр настроен"
}

# =============================================================================
# Оптимизация системы для слабых серверов
# =============================================================================
optimize_system() {
    log "Оптимизация системы..."
    
    # Отключаем ненужные сервисы
    systemctl stop rsysync 2>/dev/null || true
    systemctl disable rsysync 2>/dev/null || true
    
    # Очищаем кэш
    apt-get clean
    apt-get autoremove -y
    
    # Оптимизируем swappiness
    echo "vm.swappiness=60" >> /etc/sysctl.conf
    sysctl -p
    
    log_success "Система оптимизирована"
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
        log "Проверьте логи: journalctl -u bot-lite -f"
    fi
}

# =============================================================================
# Вывод итогов
# =============================================================================
print_summary() {
    echo ""
    echo "╔═══════════════════════════════════════════════════════╗"
    echo "║                                                       ║"
    echo "║        ✅ LITE УСТАНОВКА ЗАВЕРШЕНА!                   ║"
    echo "║                                                       ║"
    echo "╚═══════════════════════════════════════════════════════╝"
    echo ""
    echo "📁 Директория: $INSTALL_DIR"
    echo ""
    echo "🔧 Команды:"
    echo "   systemctl status bot-lite     - Статус"
    echo "   systemctl restart bot-lite    - Перезапуск"
    echo "   journalctl -u bot-lite -f     - Логи"
    echo ""
    echo "⚠️  Lite версия имеет ограничения:"
    echo "   - Максимум 100 клиентов"
    echo "   - Только VLESS протокол"
    echo "   - Нет QR-кодов"
    echo "   - Упрощённая логика"
    echo ""
    echo "📝 Следующие шаги:"
    echo "   1. Отредактируйте $INSTALL_DIR/.env"
    echo "   2. Укажите TOKEN_MAIN и MY_ID_TELEG"
    echo "   3. systemctl restart bot-lite"
    echo ""
    
    if [ -f $INSTALL_DIR/xui_credentials.txt ]; then
        echo "🔐 3X-UI панель:"
        cat $INSTALL_DIR/xui_credentials.txt
        echo ""
    fi
}

# =============================================================================
# Основная функция
# =============================================================================
main() {
    show_banner
    
    check_root
    check_ram
    create_swap
    update_system
    install_dependencies
    install_xui
    setup_bot
    create_env
    create_service
    setup_firewall
    optimize_system
    start_bot
    print_summary
}

# Запуск
main "$@"
