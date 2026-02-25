# 🛠️ Troubleshooting - Решение проблем

## 📋 Оглавление

- [Бот не запускается](#бот-не-запускается)
- [Ошибка в .env](#ошибка-в-env)
- [Проблемы с 3X-UI](#проблемы-с-3x-ui)
- [Не работает оплата](#не-работает-оплата)
- [Клиенты не могут подключиться](#клиенты-не-могут-подключиться)
- [Частые ошибки](#частые-ошибки)

---

## 🔴 Бот не запускается

### Проверьте статус

```bash
systemctl status bot
```

**Что искать:**
- ✅ `Active: active (running)` - всё хорошо
- ❌ `Active: failed` - есть ошибка
- ❌ `Active: inactive (dead)` - бот остановлен

### Посмотрите логи

```bash
# Логи в реальном времени
journalctl -u bot -f

# Последние 50 строк
journalctl -u bot -n 50

# Логи за сегодня
journalctl -u bot --since today
```

### Частые причины и решения

#### 1. ❌ Не заполнен .env

**Симптомы:**
```
Error: TOKEN_MAIN is empty
```

**Решение:**
```bash
nano /root/BOTinok/.env
```

Заполните:
```bash
TOKEN_MAIN='1234567890:ABCdefGHIjklMNOpqrsTUVwxyz'
MY_ID_TELEG=123456789
```

#### 2. ❌ Неверный токен бота

**Симптомы:**
```
Unauthorized
Token is invalid
```

**Решение:**
1. Откройте @BotFather
2. `/mybots` → выберите бота
3. Bot Settings → Generate New Token
4. Скопируйте новый токен в `.env`

#### 3. ❌ Ошибка импорта модулей

**Симптомы:**
```
ModuleNotFoundError: No module named 'aiogram'
```

**Решение:**
```bash
cd /root/BOTinok
pip3.11 install -r requirements.txt
systemctl restart bot
```

#### 4. ❌ Порт занят

**Симптомы:**
```
Address already in use
```

**Решение:**
```bash
# Найти процесс на порту
lsof -i :8080

# Убить процесс
kill -9 PID

# Или сменить порт в .env
```

---

## 📝 Ошибка в .env

### Проверка синтаксиса

**Правильно:**
```bash
TOKEN_MAIN='1234567890:ABCdef'
MY_ID_TELEG=123456789
PR_VLESS=True
```

**Неправильно:**
```bash
TOKEN_MAIN=1234567890:ABCdef  # ❌ Нет кавычек
MY_ID_TELEG='123456789'       # ❌ ID без кавычек
PR_VLESS=true                 # ❌ Должно быть True с большой
```

### Восстановление .env

Если файл повреждён:

```bash
# Создать бэкап
cp /root/BOTinok/.env /root/BOTinok/.env.backup

# Переустановить бота (файлы обновятся, .env сохранится)
bash <(curl -Ls https://raw.githubusercontent.com/ShavlaK/BOTinok/main/install.sh)
```

---

## 🔧 Проблемы с 3X-UI

### Панель не открывается

**Проверьте статус:**
```bash
x-ui status
```

**Перезапустите:**
```bash
x-ui restart
```

**Проверьте порт:**
```bash
x-ui settings
```

### SSL сертификат истёк

**Обновить вручную:**
```bash
~/.acme.sh/acme.sh --renew -d ВАШ_IP --force
systemctl restart x-ui
```

### Забыли пароль от панели

**Сбросить:**
```bash
x-ui setting -username admin -password admin123
```

**Узнать текущий:**
```bash
cat /root/BOTinok/xui_credentials.txt
```

---

## 💳 Не работает оплата

### Общие проверки

1. **Проверьте кошельки в .env:**
```bash
nano /root/BOTinok/.env
```

2. **Проверьте баланс кошельков**

3. **Проверьте логи бота:**
```bash
journalctl -u bot -f | grep -i pay
```

### YooMoney

**Ошибка:**
```
YooMoney error: invalid_token
```

**Решение:**
1. Откройте https://yoomoney.ru/transfer/myservices/http-notification
2. Проверьте токен
3. Обновите в `.env`

### Cryptomus

**Ошибка:**
```
Cryptomus error: api_key invalid
```

**Решение:**
1. https://merchant.cryptomus.com/settings/api
2. Создайте новый API ключ
3. Обновите в `.env`

---

## 🔌 Клиенты не могут подключиться

### Проверьте сервер

**Пинг:**
```bash
ping 8.8.8.8
```

**Порты:**
```bash
netstat -tulpn | grep -E '443|62050'
```

**Брандмауэр:**
```bash
ufw status
```

Если порты закрыты:
```bash
ufw allow 443/tcp
ufw allow 62050/tcp
```

### Проверьте ключи

**Сгенерировать тестовый ключ:**
```bash
# В боте: /start → Пробный период
```

**Проверить ключ в панели:**
```bash
# 3X-UI панель → Inbounds → Проверить статус
```

### VLESS не работает

**Проверьте протокол:**
```bash
# В .env должно быть:
PR_VLESS=True
```

**Пересоздайте ключ:**
```bash
# В боте: /start → Мои активные ключи → Создать новый
```

---

## ⚠️ Частые ошибки

### "No module named 'paramiko'"

```bash
pip3.11 install paramiko
systemctl restart bot
```

### "database is locked"

```bash
# Убить все процессы бота
pkill -f bot.py

# Удалить lock файл
rm /root/BOTinok/data/*.db-journal

# Запустить бота
systemctl start bot
```

### "Too many open files"

```bash
# Увеличить лимит
ulimit -n 65535

# Добавить в /etc/security/limits.conf
root soft nofile 65535
root hard nofile 65535
```

### "Permission denied"

```bash
# Исправить права
chown -R root:root /root/BOTinok
chmod -R 755 /root/BOTinok
chmod 600 /root/BOTinok/.env
```

---

## 🔍 Диагностика

### Полная проверка

```bash
#!/bin/bash
echo "=== BOTinok Diagnostics ==="
echo ""
echo "1. Статус бота:"
systemctl status bot --no-pager
echo ""
echo "2. Последние логи:"
journalctl -u bot -n 20 --no-pager
echo ""
echo "3. Статус 3X-UI:"
x-ui status
echo ""
echo "4. Порты:"
netstat -tulpn | grep -E '443|62050|8080'
echo ""
echo "5. Использование ресурсов:"
htop -u root
```

Сохраните как `diag.sh` и запустите:
```bash
bash diag.sh
```

---

## 📞 Если ничего не помогло

### 1. Создайте Issue на GitHub

https://github.com/ShavlaK/BOTinok/issues

**Укажите:**
- Версию бота
- Логи ошибки
- Что уже пробовали

### 2. Проверьте документацию

https://github.com/ShavlaK/BOTinok#readme

### 3. Временное решение

Откат на предыдущую версию:

```bash
cd /root/BOTinok
git log --oneline -5  # Найти последний рабочий коммит
git checkout HASH_КОММИТА
systemctl restart bot
```

---

## 📚 Профилактика

### Регулярное обслуживание

**Ежедневно:**
```bash
# Проверка логов
journalctl -u bot -n 50

# Проверка места на диске
df -h
```

**Еженедельно:**
```bash
# Бэкап базы данных
cp /root/BOTinok/data/*.db /root/backups/

# Очистка старых логов
journalctl --vacuum-time=7d
```

**Ежемесячно:**
```bash
# Обновление бота
cd /root/BOTinok
git pull
systemctl restart bot

# Обновление системы
apt update && apt upgrade -y
```

---

**📌 Совет:** Всегда делайте бэкап перед изменениями!

```bash
cp -r /root/BOTinok /root/BOTinok.backup.$(date +%Y%m%d)
```
