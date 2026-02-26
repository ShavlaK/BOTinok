# 🚀 BOTinok для Ubuntu Server 20.04 LTS

## 📋 Оглавление

- [Требования](#-требования)
- [Быстрый старт](#-быстрый-старт)
- [Что устанавливается](#-что-устанавливается)
- [После установки](#-после-установки)
- [Особенности Ubuntu](#-особенности-ubuntu)
- [Troubleshooting](#-troubleshooting)

---

## 📋 Требования

### Минимальные:
- **ОС:** Ubuntu Server 20.04 LTS (64-bit)
- **RAM:** 2GB
- **Disk:** 10GB
- **CPU:** 1 ядро

### Рекомендуемые:
- **ОС:** Ubuntu Server 20.04 LTS (64-bit)
- **RAM:** 4GB
- **Disk:** 20GB
- **CPU:** 2 ядра
- **Сеть:** 1 Гбит/с

---

## 🚀 Быстрый старт

### Шаг 1: Подключитесь к серверу

```bash
ssh root@your_server_ip
```

### Шаг 2: Запустите установщик

```bash
bash <(curl -Ls https://raw.githubusercontent.com/ShavlaK/BOTinok/main/install-ubuntu.sh)
```

### Шаг 3: Дождитесь завершения

Установка займёт 5-10 минут.

---

## 📦 Что устанавливается

### Системные пакеты:
- ✅ Python 3.11 (из PPA Deadsnakes)
- ✅ Python 3.8 (системный)
- ✅ pip и venv
- ✅ curl, wget, git, nano, htop
- ✅ build-essential и библиотеки для компиляции
- ✅ UFW (брандмауэр)
- ✅ Cron (планировщик задач)
- ✅ Supervisor

### Приложения:
- ✅ 3X-UI панель (VLESS управление)
- ✅ SSL сертификат (Let's Encrypt)
- ✅ BOTinok (Telegram бот)
- ✅ Виртуальное окружение Python

---

## 📝 После установки

### 1. Откройте .env файл

```bash
nano /root/BOTinok/.env
```

### 2. Заполните обязательные поля

```bash
# Токен бота (получить в @BotFather)
TOKEN_MAIN='1234567890:ABCdefGHIjklMNOpqrsTUVwxyz'

# ID администратора (узнать в @userinfobot)
MY_ID_TELEG=123456789
```

### 3. Сохраните файл

```
Ctrl+O → Enter → Ctrl+X
```

### 4. Перезапустите бота

```bash
systemctl restart bot
```

### 5. Проверьте статус

```bash
systemctl status bot
```

Должно быть: `Active: active (running)`

### 6. Запустите бота в Telegram

1. Откройте вашего бота
2. Нажмите `/start`

---

## 🔧 Особенности Ubuntu 20.04

### Python 3.11 из PPA

В Ubuntu 20.04 по умолчанию Python 3.8. Установщик автоматически:
- Добавляет PPA Deadsnakes
- Устанавливает Python 3.11
- Создаёт виртуальное окружение на Python 3.11

### UFW вместо iptables

Ubuntu использует UFW для управления брандмауэром:

```bash
# Проверить статус
ufw status

# Открыть порт
ufw allow 8080/tcp

# Закрыть порт
ufw deny 8080/tcp

# Отключить брандмауэр
ufw disable
```

### Systemd

Ubuntu использует systemd для управления сервисами:

```bash
# Статус
systemctl status bot

# Журнал
journalctl -u bot -f

# Перезапуск
systemctl restart bot
```

---

## 🛠️ Troubleshooting

### Бот не запускается

**Проверьте логи:**
```bash
journalctl -u bot -f
```

**Частые ошибки:**

#### 1. Не заполнен .env
```bash
nano /root/BOTinok/.env
# Заполните TOKEN_MAIN и MY_ID_TELEG
systemctl restart bot
```

#### 2. Ошибка импорта модулей
```bash
cd /root/BOTinok
source venv/bin/activate
pip install -r requirements.txt
deactivate
systemctl restart bot
```

#### 3. Порт занят
```bash
# Найти процесс
lsof -i :8080

# Убить процесс
kill -9 PID
```

### 3X-UI панель не открывается

**Проверьте статус:**
```bash
x-ui status
```

**Перезапустите:**
```bash
x-ui restart
```

**Узнайте порт:**
```bash
cat /root/BOTinok/xui_credentials.txt
```

### Ошибка при установке Python

**Проблема с PPA:**
```bash
# Удалите проблемный PPA
add-apt-repository --remove ppa:deadsnakes/ppa

# Обновите списки
apt-get update

# Запустите установщик снова
bash <(curl -Ls https://raw.githubusercontent.com/ShavlaK/BOTinok/main/install-ubuntu.sh)
```

### UFW блокирует подключения

**Проверьте правила:**
```bash
ufw status verbose
```

**Откройте порты:**
```bash
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw allow 62050/tcp # 3X-UI (ваш порт может отличаться)
```

---

## 📊 Команды управления

### Бот:
```bash
systemctl status bot      # Статус
systemctl restart bot     # Перезапуск
systemctl stop bot        # Остановка
systemctl start bot       # Запуск
journalctl -u bot -f      # Логи
```

### 3X-UI:
```bash
x-ui status              # Статус
x-ui restart             # Перезапуск
x-ui stop                # Остановка
x-ui start               # Запуск
x-ui log                 # Логи
```

### Брандмауэр:
```bash
ufw status               # Статус
ufw enable               # Включить
ufw disable              # Отключить
ufw reload               # Перезагрузить
```

---

## 🔄 Обновление

### Обновление бота:

```bash
cd /root/BOTinok
git pull
source venv/bin/activate
pip install -r requirements.txt
deactivate
systemctl restart bot
```

### Обновление системы:

```bash
apt update && apt upgrade -y
```

### Обновление 3X-UI:

```bash
x-ui update
```

---

## 🗑️ Удаление

### Удалить бота:

```bash
systemctl stop bot
systemctl disable bot
rm -rf /root/BOTinok
rm /etc/systemd/system/bot.service
systemctl daemon-reload
```

### Удалить 3X-UI:

```bash
x-ui uninstall
```

---

## 📚 Дополнительные ресурсы

- [Официальная документация Ubuntu](https://ubuntu.com/server/docs)
- [Python 3.11 документация](https://docs.python.org/3.11/)
- [3X-UI GitHub](https://github.com/MHSanaei/3x-ui)
- [BOTinok Troubleshooting](TROUBLESHOOTING.md)

---

**Готово к использованию! 🎉**
