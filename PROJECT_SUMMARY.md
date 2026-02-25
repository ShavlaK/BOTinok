# 📋 BOTinok Project - Полное резюме

## 🎯 Описание проекта

**BOTinok** - это готовое решение для автоматического развёртывания BOT бота Telegram с панелью управления 3X-UI.

### Ключевые особенности:

1. ✅ **Автоматическая установка** - одной командой
2. ✅ **Проверка сервера** - RAM, CPU, Disk, сеть
3. ✅ **Создание swap** - автоматически при необходимости
4. ✅ **Две версии** - основная (2GB+ RAM) и Lite (512MB+)
5. ✅ **VLESS протокол** - современный и безопасный
6. ✅ **Whitelist-туннель** - обход блокировок
7. ✅ **Платёжные системы** - ЮMoney, Crypto, карты
8. ✅ **Реферальная система** - привлечение клиентов

---

## 📁 Структура проекта

```
BOTinok-project/
│
├── 📄 README.md                  # Главная документация
├── 📄 LICENSE                    # MIT License
├── 📄 .gitignore                 # Игнорируемые файлы
├── 📄 .env.example               # Пример конфигурации
│
├── 🔧 install.sh                 # Основная установка (2GB+ RAM)
├── 🔧 install-lite.sh            # Lite версия (512MB+ RAM)
│
├── 📂 scripts/
│   ├── check_server.sh           # Проверка мощностей сервера
│   ├── setup_swap.sh             # Создание swap файла
│   ├── install_bot.sh            # Установка бота
│   ├── install_xui.sh            # Установка 3X-UI
│   └── firewall.sh               # Настройка брандмауэра
│
├── 📂 bot/
│   ├── bot.py                    # Основной файл бота
│   ├── requirements.txt          # Python зависимости
│   ├── data/
│   │   ├── config.py             # Конфигурация
│   │   ├── lang.yml              # Локализация
│   │   ├── markup.py             # Клавиатуры
│   │   ├── markup_inline.py      # Inline клавиатуры
│   │   └── whitelist_utils.py    # Утилиты whitelist-туннеля
│   └── logs/                     # Логи бота
│
├── 🐳 docker/
│   ├── Dockerfile                # Docker образ
│   └── docker-compose.yml        # Docker Compose
│
├── ⚙️ systemd/
│   └── bot.service               # Systemd сервис
│
└── 📚 docs/
    ├── bot-setup.md              # Настройка бота
    ├── servers-setup.md          # Настройка серверов
    ├── payments.md               # Платёжные системы
    ├── whitelist.md              # Whitelist-туннель
    └── troubleshooting.md        # Решение проблем
```

---

## 🚀 Быстрый старт

### Основная версия (2GB+ RAM)

```bash
bash <(curl -Ls https://raw.githubusercontent.com/ShavlaK/BOTinok/main/install.sh)
```

### Lite версия (512MB-1GB RAM)

```bash
bash <(curl -Ls https://raw.githubusercontent.com/ShavlaK/BOTinok/main/install-lite.sh)
```

---

## 🔧 Скрипты

### 1. `scripts/check_server.sh`

Проверка мощностей сервера:
- ✅ RAM (с созданием swap при необходимости)
- ✅ CPU (количество ядер)
- ✅ Disk (свободное место)
- ✅ Network (доступ к интернету)
- ✅ OS (поддерживаемая система)

**Результат:**
- Определяет рекомендуемую версию (main/lite)
- Создаёт swap если RAM < 1GB
- Сохраняет результаты в `/tmp/server_check_results.env`

### 2. `install.sh` (Основная версия)

**Что делает:**
1. Проверяет права root
2. Проверяет сервер (check_server.sh)
3. Обновляет систему
4. Устанавливает зависимости
5. Устанавливает Python 3.11
6. Устанавливает 3X-UI панель
7. Загружает файлы бота
8. Устанавливает Python зависимости
9. Создаёт .env файл
10. Создаёт systemd сервис
11. Настраивает брандмауэр
12. Настраивает cron (бэкапы)
13. Запускает бота

**Время установки:** 5-10 минут

### 3. `install-lite.sh` (Lite версия)

**Отличия от основной:**
- ✅ Минимальные зависимости (экономия RAM)
- ✅ Python 3.9 (меньше требований)
- ✅ Обязательное создание swap
- ✅ Ограничение памяти для сервиса (512M)
- ✅ Упрощённая конфигурация
- ✅ Только VLESS протокол
- ✅ Нет тяжёлых функций (QR-коды, отчёты)

**Время установки:** 3-7 минут

---

## 📊 Сравнение версий

| Параметр | Основная | Lite |
|----------|----------|------|
| **RAM** | 2GB+ | 512MB+ |
| **Disk** | 10GB+ | 5GB+ |
| **Клиентов** | до 500 | до 100 |
| **Протоколы** | VLESS | VLESS |
| **QR-коды** | ✅ | ❌ |
| **Отчёты** | ✅ | ❌ |
| **Python** | 3.11 | 3.9 |
| **Memory Limit** | 1GB | 512MB |
| **Скорость** | 1 Гбит/с | 100 Мбит/с |

---

## 🎛️ Управление

### Команды

```bash
# Статус
systemctl status bot        # Основная
systemctl status bot-lite   # Lite

# Перезапуск
systemctl restart bot
systemctl restart bot-lite

# Логи
journalctl -u bot -f
journalctl -u bot-lite -f

# Остановка
systemctl stop bot
systemctl stop bot-lite
```

### Команды бота (админ)

```
/start              - Главное меню
/add_server         - Добавить сервер
/add_server_for_whitelist - Настроить whitelist-туннель
/wallets            - Способы оплаты
/analytics          - Аналитика
/report             - Пользователи
/speed_test         - Тест скорости
/backup             - Бэкап
```

---

## 🔐 Безопасность

### Что защищено:

- ✅ **Swap файл** - шифрование не требуется (временные данные)
- ✅ **.env файл** - в .gitignore, не попадает в Git
- ✅ **Systemd сервис** - ограничения прав (NoNewPrivileges)
- ✅ **Брандмауэр** - только необходимые порты
- ✅ **3X-UI панель** - случайный пароль при установке

### Рекомендации:

1. Смените пароли после установки
2. Используйте SSH ключи вместо паролей
3. Регулярно обновляйте систему
4. Делайте бэкапы базы данных

---

## 📈 Метрики

### Использование ресурсов (Основная версия)

| Ресурс | Минимум | Среднее | Максимум |
|--------|---------|---------|----------|
| **RAM** | 256MB | 400MB | 800MB |
| **CPU** | 1% | 5% | 25% |
| **Disk** | 2GB | 3GB | 5GB |
| **Сеть** | 10KB/s | 100KB/s | 1GB/s |

### Использование ресурсов (Lite версия)

| Ресурс | Минимум | Среднее | Максимум |
|--------|---------|---------|----------|
| **RAM** | 128MB | 256MB | 400MB |
| **CPU** | 1% | 3% | 15% |
| **Disk** | 1GB | 2GB | 3GB |
| **Сеть** | 10KB/s | 50KB/s | 100MB/s |

---

## 🔄 Обновление

### Автоматическое

```bash
cd /root/BOTinok
git pull
systemctl restart bot
```

### Ручное

```bash
# Скачайте новую версию
bash <(curl -Ls https://raw.githubusercontent.com/ShavlaK/BOTinok/main/install.sh)

# Установка поверх существующей
```

---

## 🗑️ Удаление

### Бот

```bash
systemctl stop bot
systemctl disable bot
rm -rf /root/BOTinok
rm /etc/systemd/system/bot.service
systemctl daemon-reload
```

### 3X-UI

```bash
/usr/local/x-ui/x-ui uninstall
```

### Swap

```bash
swapoff /swapfile
rm /swapfile
sed -i '/\/swapfile/d' /etc/fstab
```

---

## 🆘 Troubleshooting

### Бот не запускается

```bash
# Проверьте логи
journalctl -u bot -f

# Проверьте .env
nano /root/BOTinok/.env

# Проверьте токен
# @BotFather в Telegram
```

### Недостаточно памяти

```bash
# Проверьте память
free -h

# Создайте swap
./scripts/setup_swap.sh

# Или используйте Lite версию
```

### Не работает оплата

```bash
# Проверьте кошельки в .env
# Проверьте баланс
# Обратитесь в поддержку
```

---

## 📚 Документация

### Основные файлы

- **README.md** - главная документация
- **GITHUB_SETUP.md** - развёртывание на GitHub
- **PROJECT_SUMMARY.md** - этот файл

### Внутренняя документация

- **docs/bot-setup.md** - настройка бота
- **docs/servers-setup.md** - настройка серверов
- **docs/payments.md** - платёжные системы
- **docs/whitelist.md** - whitelist-туннель
- **docs/troubleshooting.md** - решение проблем

---

## 📝 Лицензия

MIT License - свободное использование с указанием автора.

---

## 📞 Поддержка

- **GitHub Issues:** https://github.com/ShavlaK/BOTinok/issues
- **Telegram:** @your_support_nick
- **Email:** support@example.com

---

## 🙏 Благодарности

- [3X-UI](https://github.com/MHSanaei/3x-ui) - Панель управления
- [aiogram](https://github.com/aiogram/aiogram) - Telegram Bot API
- [Xray-core](https://github.com/XTLS/Xray-core) - Протокол VLESS

---

## 📈 Roadmap

### v1.1.0
- [ ] Поддержка нескольких языков
- [ ] WebApp интерфейс
- [ ] Автообновление бота
- [ ] Статистика по трафику

### v1.2.0
- [ ] Поддержка Trojan протокола
- [ ] Мульти-серверная архитектура
- [ ] Балансировка нагрузки
- [ ] Мониторинг в реальном времени

### v2.0.0
- [ ] Kubernetes поддержка
- [ ] Microservices архитектура
- [ ] GraphQL API
- [ ] Mobile приложение

---

**Проект готов к развёртыванию! 🚀**
