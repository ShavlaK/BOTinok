# 🚀 BOTinok - Автоматическое развёртывание

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/ShavlaK/BOTinok)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11-yellow.svg)](https://www.python.org/)
[![Telegram](https://img.shields.io/badge/Telegram-Bot-blue.svg)](https://t.me/your_bot)

> **Автоматическая установка бота для Telegram с 3X-UI панелью**

---

## 📋 Оглавление

- [Возможности](#-возможности)
- [Требования](#-требования)
- [Быстрый старт](#-быстрый-старт)
- [Установка](#-установка)
- [Конфигурация](#-конфигурация)
- [Управление](#-управление)
- [🛠️ Troubleshooting](TROUBLESHOOTING.md) - Решение проблем
- [Документация](#-документация)
- [Поддержка](#-поддержка)

---

## ✨ Возможности

### 🎯 Основные функции

- ✅ **Автоматическая установка** - одной командой
- ✅ **Проверка сервера** - RAM, CPU, Disk, сеть
- ✅ **Создание swap** - автоматически при необходимости
- ✅ **3X-UI панель** - управление VLESS ключами
- ✅ **VLESS протокол** - современный и безопасный
- ✅ **Whitelist-туннель** - обход блокировок
- ✅ **Платёжные системы** - ЮMoney, Crypto, карты
- ✅ **Реферальная система** - привлечение клиентов
- ✅ **Партнёрская программа** - промокоды и скидки
- ✅ **Мультиязычность** - русский и английский

### 📊 Версии

| Версия | RAM | Disk | Клиентов | Скорость |
|--------|-----|------|----------|----------|
| **Основная** | 2GB+ | 10GB+ | до 500 | 1 Гбит/с |
| **Lite** | 512MB+ | 5GB+ | до 100 | 100 Мбит/с |

---

## 📋 Требования

### Основная версия:
- **ОС:** Debian 11/12, Ubuntu 20.04+
- **RAM:** 2GB+ (или 1GB + swap)
- **Disk:** 10GB+
- **CPU:** 1 ядро+
- **Сеть:** 1 Гбит/с

### Lite версия:
- **ОС:** Debian 11/12, Ubuntu 20.04+
- **RAM:** 512MB+
- **Disk:** 5GB+
- **CPU:** 1 ядро+
- **Сеть:** 100 Мбит/с+

---

## 🚀 Быстрый старт

### 1. Основная версия (2GB+ RAM)

```bash
bash <(curl -Ls https://raw.githubusercontent.com/ShavlaK/BOTinok/main/install.sh)
```

### 2. Lite версия (512MB-1GB RAM)

```bash
bash <(curl -Ls https://raw.githubusercontent.com/ShavlaK/BOTinok/main/install-lite.sh)
```

### 3. Docker версия

```bash
git clone https://github.com/ShavlaK/BOTinok.git
cd BOTinok/docker
docker-compose up -d
```

---

## 📦 Установка

### Подробная инструкция

#### Шаг 1: Подготовка сервера

```bash
# Подключитесь к серверу по SSH
ssh root@your_server_ip

# Обновите систему
apt update && apt upgrade -y

# Перейдите в директорию root
cd /root
```

#### Шаг 2: Загрузка установщика

```bash
# Скачайте установочный скрипт
wget https://raw.githubusercontent.com/ShavlaK/BOTinok/main/install.sh

# Сделайте его исполняемым
chmod +x install.sh
```

#### Шаг 3: Запуск установки

```bash
# Запустите установку
./install.sh
```

### Что делает установщик:

1. ✅ Проверяет мощности сервера (RAM, CPU, Disk)
2. ✅ Создаёт swap файл при необходимости
3. ✅ Устанавливает зависимости (Python, curl, wget)
4. ✅ Устанавливает 3X-UI панель
5. ✅ Загружает файлы бота
6. ✅ Устанавливает Python зависимости
7. ✅ Создаёт systemd сервис
8. ✅ Настраивает брандмауэр
9. ✅ Запускает бота

---

## ⚙️ Конфигурация

### После установки

1. **Откройте файл конфигурации:**

```bash
nano /root/BOTinok/.env
```

2. **Укажите обязательные параметры:**

```bash
# Токен бота (получить в @BotFather)
TOKEN_MAIN='1234567890:ABCdefGHIjklMNOpqrsTUVwxyz'

# ID Telegram администратора (узнать в @userinfobot)
MY_ID_TELEG=123456789

# Ник для поддержки
NICK_HELP='your_support_nick'
```

3. **Перезапустите бота:**

```bash
systemctl restart bot
```

### Все параметры .env

```bash
# =============================================================================
# Обязательные параметры
# =============================================================================

TOKEN_MAIN=''           # Токен бота Telegram
MY_ID_TELEG=            # ID администратора

# =============================================================================
# Основные настройки
# =============================================================================

NICK_HELP='codenlx'     # Ник поддержки
NAME_AUTHOR_BOT='Александр'  # Имя автора
NAME_BOT_CONFIG='VPCoden'    # Название бота

# =============================================================================
# Протоколы (True/False)
# =============================================================================

PR_VLESS=True           # VLESS протокол
PR_OUTLINE=False        # Outline (отключен)
PR_WIREGUARD=False      # WireGuard (отключен)
PR_PPTP=False           # PPTP (отключен)

# =============================================================================
# Функции
# =============================================================================

TEST_KEY=True           # Тестовые ключи
REF_SYSTEM=True         # Реферальная система
OPLATA=True             # Оплата
DONATE_SYSTEM=True      # Донаты
WHY_BOT_PAY=True        # Информация об оплате
OBESH_PLATEZH=True      # Обещанный платеж
SEND_QR=False           # QR-коды (отключено для VLESS)

# =============================================================================
# Тарифы (рубли)
# =============================================================================

TARIF_1=149             # 1 месяц
TARIF_3=379             # 3 месяца
TARIF_6=749             # 6 месяцев
TARIF_12=1349           # 12 месяцев

# =============================================================================
# Реферальная система
# =============================================================================

COUNT_DAYS_TRIAL=2      # Пробный период (дней)
COUNT_DAYS_REF=7        # Дней за реферала
PARTNER_P=30            # Процент партнёра (%)
SUMM_VIVOD=200          # Мин. сумма вывода (₽)
```

---

## 🎛️ Управление

### Команды systemctl

```bash
# Статус бота
systemctl status bot

# Запуск бота
systemctl start bot

# Остановка бота
systemctl stop bot

# Перезапуск бота
systemctl restart bot

# Автозагрузка при старте
systemctl enable bot

# Отключение автозагрузки
systemctl disable bot
```

### Просмотр логов

```bash
# Логи в реальном времени
journalctl -u bot -f

# Логи за сегодня
journalctl -u bot --since today

# Последние 100 строк
journalctl -u bot -n 100

# Логи с фильтром по времени
journalctl -u bot --since "2024-01-01 00:00:00" --until "2024-01-01 23:59:59"
```

### Команды бота (для админа)

```bash
/start              - Главное меню
/add_server         - Добавить сервер
/add_location       - Добавить локацию
/wallets            - Способы оплаты
/analytics          - Аналитика
/report             - Пользователи
/speed_test         - Тест скорости
/backup             - Бэкап
```

---

## 📚 Документация

### Дополнительные руководства

- [📖 Настройка бота](docs/bot-setup.md)
- [🌐 Настройка серверов](docs/servers-setup.md)
- [💳 Платёжные системы](docs/payments.md)
- [🔒 Whitelist-туннель](docs/whitelist.md)
- [🔧 Troubleshooting](docs/troubleshooting.md)

### Структура проекта

```
BOTinok/
├── install.sh              # Основной установщик
├── install-lite.sh         # Lite версия
├── scripts/
│   ├── check_server.sh     # Проверка сервера
│   ├── setup_swap.sh       # Создание swap
│   └── install_bot.sh      # Установка бота
├── bot/
│   ├── bot.py              # Основной файл
│   ├── data/
│   │   ├── config.py       # Конфигурация
│   │   ├── lang.yml        # Локализация
│   │   └── markup.py       # Клавиатуры
│   └── requirements.txt    # Зависимости
├── docker/
│   ├── Dockerfile          # Docker образ
│   └── docker-compose.yml  # Compose
├── systemd/
│   └── bot.service         # Systemd сервис
└── docs/
    ├── bot-setup.md
    ├── servers-setup.md
    └── payments.md
```

---

## 🔄 Обновление

### Автоматическое обновление

```bash
# Перейдите в директорию бота
cd /root/BOTinok

# Скачайте обновления
git pull

# Перезапустите бота
systemctl restart bot
```

### Ручное обновление

```bash
# Скачайте новую версию
wget https://raw.githubusercontent.com/ShavlaK/BOTinok/main/install.sh

# Запустите установку (обновит существующую)
bash install.sh
```

---

## 🗑️ Удаление

### Удаление бота

```bash
# Остановите бота
systemctl stop bot

# Удалите сервис
systemctl disable bot
rm /etc/systemd/system/bot.service

# Удалите файлы бота
rm -rf /root/BOTinok

# Перезагрузите systemd
systemctl daemon-reload
```

### Полное удаление (с 3X-UI)

```bash
# Удалите бота (см. выше)

# Удалите 3X-UI
/usr/local/x-ui/x-ui uninstall

# Удалите swap
swapoff /swapfile
rm /swapfile

# Очистите fstab
sed -i '/\/swapfile/d' /etc/fstab
```

---

## 🆘 Поддержка

### Контакты

- **Telegram:** `@your_support_nick`
- **Email:** support@example.com
- **GitHub Issues:** https://github.com/ShavlaK/BOTinok/issues

### Частые проблемы

#### Бот не запускается

```bash
# Проверьте логи
journalctl -u bot -f

# Проверьте .env файл
nano /root/BOTinok/.env

# Убедитесь что токен правильный
# Проверьте в @BotFather
```

#### Недостаточно памяти

```bash
# Проверьте память
free -h

# Создайте swap
./scripts/setup_swap.sh

# Или используйте Lite версию
bash <(curl -Ls https://raw.githubusercontent.com/ShavlaK/BOTinok/main/install-lite.sh)
```

#### Не работает оплата

```bash
# Проверьте кошельки в .env
# Проверьте баланс кошельков
# Обратитесь в поддержку платёжной системы
```

---

## 📈 Метрики и мониторинг

### Проверка использования ресурсов

```bash
# Использование памяти
htop

# Использование диска
df -h

# Использование сети
iftop

# Логи бота
tail -f /root/BOTinok/logs/bot_*.log
```

### Статистика бота

```bash
# Через бота
/analytics  - Общая статистика
/report     - Пользователи
```

---

## 📝 License

MIT License - см. файл [LICENSE](LICENSE)

---

## 🙏 Благодарности

- [3X-UI](https://github.com/MHSanaei/3x-ui) - Панель управления
- [aiogram](https://github.com/aiogram/aiogram) - Telegram Bot API
- [Xray-core](https://github.com/XTLS/Xray-core) - Протокол VLESS

---

## 📞 Контакты

**Разработчик:** ShavlaK  
**Telegram:** @your_support_nick  
**Email:** support@example.com

---

**Готово к использованию! 🚀**

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)
[![Docker](https://docker.com/static/images/docker-logo.svg)](https://www.docker.com/)
