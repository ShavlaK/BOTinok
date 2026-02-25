#!/bin/bash

# =============================================================================
# Скрипт проверки мощностей сервера
# =============================================================================
# Проверяет: RAM, CPU, Disk, сеть
# Создаёт swap если RAM < 1GB
# =============================================================================

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Логирование
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
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

# =============================================================================
# Проверка оперативной памяти
# =============================================================================
check_ram() {
    log_info "Проверка оперативной памяти..."
    
    # Получаем общий объём RAM в KB
    TOTAL_RAM_KB=$(grep MemTotal /proc/meminfo | awk '{print $2}')
    TOTAL_RAM_MB=$((TOTAL_RAM_KB / 1024))
    TOTAL_RAM_GB=$((TOTAL_RAM_KB / 1024 / 1024))
    
    # Получаем доступную RAM в KB
    AVAILABLE_RAM_KB=$(grep MemAvailable /proc/meminfo | awk '{print $2}')
    AVAILABLE_RAM_MB=$((AVAILABLE_RAM_KB / 1024))
    
    # Получаем информацию о swap
    SWAP_TOTAL_KB=$(grep SwapTotal /proc/meminfo | awk '{print $2}')
    SWAP_TOTAL_MB=$((SWAP_TOTAL_KB / 1024))
    
    echo ""
    echo "════════════════════════════════════════"
    echo "  📊 ОПЕРАТИВНАЯ ПАМЯТЬ"
    echo "════════════════════════════════════════"
    echo "  Всего RAM:      ${TOTAL_RAM_MB} MB (~${TOTAL_RAM_GB} GB)"
    echo "  Доступно RAM:   ${AVAILABLE_RAM_MB} MB"
    echo "  Swap:           ${SWAP_TOTAL_MB} MB"
    echo "════════════════════════════════════════"
    echo ""
    
    # Определяем версию для установки
    if [ $TOTAL_RAM_MB -lt 512 ]; then
        log_error "Недостаточно RAM: ${TOTAL_RAM_MB} MB"
        log_error "Минимальные требования: 512 MB"
        exit 1
    elif [ $TOTAL_RAM_MB -lt 1024 ]; then
        log_warning "Мало RAM: ${TOTAL_RAM_MB} MB"
        log_warning "Рекомендуется версия LITE"
        RECOMMENDED_VERSION="lite"
        
        # Проверяем есть ли swap
        if [ $SWAP_TOTAL_MB -lt 512 ]; then
            log_warning "Swap меньше 512 MB, рекомендуется создать"
            NEED_SWAP=true
        fi
    elif [ $TOTAL_RAM_MB -lt 2048 ]; then
        log_info "Достаточно RAM: ${TOTAL_RAM_MB} MB"
        log_info "Можно использовать основную версию с swap"
        RECOMMENDED_VERSION="main"
        
        if [ $SWAP_TOTAL_MB -lt 1024 ]; then
            log_warning "Swap меньше 1 GB, рекомендуется создать"
            NEED_SWAP=true
        fi
    else
        log_success "Достаточно RAM: ${TOTAL_RAM_MB} MB"
        log_success "Рекомендуется основная версия"
        RECOMMENDED_VERSION="main"
        NEED_SWAP=false
    fi
    
    export TOTAL_RAM_MB
    export AVAILABLE_RAM_MB
    export SWAP_TOTAL_MB
    export RECOMMENDED_VERSION
    export NEED_SWAP
}

# =============================================================================
# Проверка процессора
# =============================================================================
check_cpu() {
    log_info "Проверка процессора..."
    
    # Количество ядер
    CPU_CORES=$(nproc)
    
    # Модель процессора
    CPU_MODEL=$(grep "model name" /proc/cpuinfo | head -1 | cut -d':' -f2 | xargs)
    
    # Частота (если доступна)
    CPU_FREQ=$(grep "cpu MHz" /proc/cpuinfo | head -1 | cut -d':' -f2 | xargs | cut -d'.' -f1)
    
    echo ""
    echo "════════════════════════════════════════"
    echo "  💻 ПРОЦЕССОР"
    echo "════════════════════════════════════════"
    echo "  Модель:  ${CPU_MODEL:0:50}..."
    echo "  Ядра:    ${CPU_CORES}"
    echo "  Частота: ~${CPU_FREQ} MHz"
    echo "════════════════════════════════════════"
    echo ""
    
    if [ $CPU_CORES -lt 1 ]; then
        log_error "Недостаточно ядер CPU: ${CPU_CORES}"
        exit 1
    fi
    
    export CPU_CORES
    export CPU_MODEL
}

# =============================================================================
# Проверка дискового пространства
# =============================================================================
check_disk() {
    log_info "Проверка дискового пространства..."
    
    # Свободное место на корневом разделе в KB
    DISK_FREE_KB=$(df -k / | tail -1 | awk '{print $4}')
    DISK_FREE_GB=$((DISK_FREE_KB / 1024 / 1024))
    DISK_FREE_MB=$((DISK_FREE_KB / 1024))
    
    # Всего места
    DISK_TOTAL_KB=$(df -k / | tail -1 | awk '{print $2}')
    DISK_TOTAL_GB=$((DISK_TOTAL_KB / 1024 / 1024))
    
    # Использовано
    DISK_USED_PERCENT=$(df -h / | tail -1 | awk '{print $5}')
    
    echo ""
    echo "════════════════════════════════════════"
    echo "  💾 ДИСКОВОЕ ПРОСТРАНСТВО"
    echo "════════════════════════════════════════"
    echo "  Всего:     ${DISK_TOTAL_GB} GB"
    echo "  Свободно:  ${DISK_FREE_GB} GB"
    echo "  Занято:    ${DISK_USED_PERCENT}"
    echo "════════════════════════════════════════"
    echo ""
    
    if [ $DISK_FREE_GB -lt 5 ]; then
        log_error "Недостаточно места на диске: ${DISK_FREE_GB} GB"
        log_error "Минимум: 5 GB"
        exit 1
    elif [ $DISK_FREE_GB -lt 10 ]; then
        log_warning "Мало места: ${DISK_FREE_GB} GB"
        log_warning "Рекомендуется: 10 GB"
    else
        log_success "Достаточно места: ${DISK_FREE_GB} GB"
    fi
    
    export DISK_FREE_GB
    export DISK_TOTAL_GB
}

# =============================================================================
# Проверка сети
# =============================================================================
check_network() {
    log_info "Проверка сетевого подключения..."
    
    # Проверка доступа к интернету
    if ping -c 2 8.8.8.8 > /dev/null 2>&1; then
        log_success "Интернет подключение есть"
        NETWORK_OK=true
    else
        log_error "Нет доступа к интернету"
        exit 1
    fi
    
    # Проверка доступа к GitHub
    if curl -s --connect-timeout 5 https://github.com > /dev/null; then
        log_success "Доступ к GitHub есть"
        GITHUB_OK=true
    else
        log_warning "Нет доступа к GitHub"
        GITHUB_OK=false
    fi
    
    # Получение внешнего IP
    EXTERNAL_IP=$(curl -s ifconfig.me 2>/dev/null || echo "N/A")
    
    echo ""
    echo "════════════════════════════════════════"
    echo "  🌐 СЕТЬ"
    echo "════════════════════════════════════════"
    echo "  Внешний IP:  ${EXTERNAL_IP}"
    echo "  Интернет:    ${NETWORK_OK}"
    echo "  GitHub:      ${GITHUB_OK}"
    echo "════════════════════════════════════════"
    echo ""
    
    export EXTERNAL_IP
    export NETWORK_OK
    export GITHUB_OK
}

# =============================================================================
# Проверка операционной системы
# =============================================================================
check_os() {
    log_info "Проверка операционной системы..."
    
    if [ -f /etc/os-release ]; then
        source /etc/os-release
        OS_NAME=$NAME
        OS_VERSION=$VERSION_ID
    else
        OS_NAME="Unknown"
        OS_VERSION="Unknown"
    fi
    
    echo ""
    echo "════════════════════════════════════════"
    echo "  🖥️ ОПЕРАЦИОННАЯ СИСТЕМА"
    echo "════════════════════════════════════════"
    echo "  Название:  ${OS_NAME}"
    echo "  Версия:    ${OS_VERSION}"
    echo "  Архитектура: $(uname -m)"
    echo "  Ядро:      $(uname -r)"
    echo "════════════════════════════════════════"
    echo ""
    
    # Проверка поддерживаемых ОС
    case "$OS_NAME" in
        *"Debian"*|*"Ubuntu"*|*"debian"*|*"ubuntu"*)
            log_success "Поддерживаемая ОС: ${OS_NAME}"
            OS_SUPPORTED=true
            ;;
        *)
            log_warning "ОС может не поддерживаться: ${OS_NAME}"
            OS_SUPPORTED=true  # Всё равно пробуем установить
            ;;
    esac
    
    export OS_NAME
    export OS_VERSION
    export OS_SUPPORTED
}

# =============================================================================
# Создание swap файла
# =============================================================================
create_swap() {
    if [ "$NEED_SWAP" != "true" ]; then
        log_info "Swap не требуется"
        return 0
    fi
    
    log_info "Создание swap файла..."
    
    # Определяем размер swap
    if [ $TOTAL_RAM_MB -lt 1024 ]; then
        # Если RAM < 1GB, создаём swap = RAM (но не больше доступного места)
        SWAP_SIZE_MB=$TOTAL_RAM_MB
        if [ $SWAP_SIZE_MB -gt $DISK_FREE_MB ]; then
            SWAP_SIZE_MB=$((DISK_FREE_MB / 2))
        fi
    else
        # Если RAM 1-2GB, создаём swap = 2GB
        SWAP_SIZE_MB=2048
        if [ $SWAP_SIZE_MB -gt $DISK_FREE_MB ]; then
            SWAP_SIZE_MB=$((DISK_FREE_MB / 2))
        fi
    fi
    
    # Минимальный swap 512MB
    if [ $SWAP_SIZE_MB -lt 512 ]; then
        SWAP_SIZE_MB=512
    fi
    
    log_info "Размер swap: ${SWAP_SIZE_MB} MB"
    
    # Проверяем есть ли уже swap
    if [ $SWAP_TOTAL_MB -gt 0 ]; then
        log_info "Swap уже существует: ${SWAP_TOTAL_MB} MB"
        return 0
    fi
    
    # Создаём swap файл
    SWAP_FILE="/swapfile"
    
    if [ -f "$SWAP_FILE" ]; then
        log_warning "Swap файл уже существует, удаляем..."
        rm -f "$SWAP_FILE"
    fi
    
    log_info "Создание swap файла (${SWAP_SIZE_MB} MB)..."
    
    # Создаём файл
    dd if=/dev/zero of=$SWAP_FILE bs=1M count=$SWAP_SIZE_MB status=progress
    
    # Устанавливаем права
    chmod 600 $SWAP_FILE
    
    # Форматируем в swap
    mkswap $SWAP_FILE
    
    # Включаем swap
    swapon $SWAP_FILE
    
    # Добавляем в fstab для автозагрузки
    if ! grep -q "$SWAP_FILE" /etc/fstab; then
        echo "$SWAP_FILE none swap sw 0 0" >> /etc/fstab
    fi
    
    # Проверяем что swap включился
    SWAP_NEW=$(grep SwapTotal /proc/meminfo | awk '{print $2}')
    SWAP_NEW_MB=$((SWAP_NEW / 1024))
    
    if [ $SWAP_NEW_MB -gt 0 ]; then
        log_success "Swap успешно создан: ${SWAP_NEW_MB} MB"
        export SWAP_CREATED=true
    else
        log_error "Не удалось создать swap"
        export SWAP_CREATED=false
    fi
}

# =============================================================================
# Вывод итогов проверки
# =============================================================================
print_summary() {
    echo ""
    echo "╔════════════════════════════════════════╗"
    echo "║       📋 ИТОГИ ПРОВЕРКИ СЕРВЕРА        ║"
    echo "╚════════════════════════════════════════╝"
    echo ""
    echo "  ✅ RAM:           ${TOTAL_RAM_MB} MB"
    echo "  ✅ CPU:           ${CPU_CORES} яд."
    echo "  ✅ Disk:          ${DISK_FREE_GB} GB св."
    echo "  ✅ OS:            ${OS_NAME} ${OS_VERSION}"
    echo "  ✅ Сеть:          ${NETWORK_OK}"
    echo ""
    echo "  📌 Рекомендуемая версия: ${RECOMMENDED_VERSION^^}"
    
    if [ "$SWAP_CREATED" = "true" ]; then
        echo "  ✅ Swap:          создан"
    elif [ "$NEED_SWAP" = "true" ]; then
        echo "  ⚠️  Swap:          требуется"
    else
        echo "  ✅ Swap:          не требуется"
    fi
    
    echo ""
    
    # Экспортируем результаты для установочного скрипта
    cat > /tmp/server_check_results.env << EOF
TOTAL_RAM_MB=$TOTAL_RAM_MB
CPU_CORES=$CPU_CORES
DISK_FREE_GB=$DISK_FREE_GB
OS_NAME=$OS_NAME
OS_VERSION=$OS_VERSION
RECOMMENDED_VERSION=$RECOMMENDED_VERSION
NEED_SWAP=$NEED_SWAP
SWAP_CREATED=$SWAP_CREATED
EXTERNAL_IP=$EXTERNAL_IP
EOF
    
    log_success "Результаты сохранены в /tmp/server_check_results.env"
}

# =============================================================================
# Основная функция
# =============================================================================
main() {
    echo ""
    echo "╔════════════════════════════════════════╗"
    echo "║     🔍 ПРОВЕРКА МОЩНОСТЕЙ СЕРВЕРА      ║"
    echo "╚════════════════════════════════════════╝"
    echo ""
    
    check_os
    check_ram
    check_cpu
    check_disk
    check_network
    
    if [ "$NEED_SWAP" = "true" ] && [ "$SWAP_TOTAL_MB" -lt 512 ]; then
        create_swap
    fi
    
    print_summary
    
    echo ""
    log_success "Проверка завершена!"
    echo ""
}

# Запуск
main "$@"
