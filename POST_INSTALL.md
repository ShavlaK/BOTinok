# 🚀 BOTinok - Инструкция после установки

## ✅ Установка завершена!

Если вы видите это сообщение, значит установка BOTinok успешно завершена.

---

## 📝 ЧТО ДЕЛАТЬ ДАЛЬШЕ (ПОШАГОВО):

### 🔹 ШАГ 1: Откройте файл конфигурации

```bash
nano /root/BOTinok/.env
```

### 🔹 ШАГ 2: Заполните обязательные поля

Найдите эти строки в файле и заполните:

```bash
# Токен бота (получить в @BotFather)
TOKEN_MAIN='1234567890:ABCdefGHIjklMNOpqrsTUVwxyz'

# ID Telegram администратора (узнать в @userinfobot)
MY_ID_TELEG=123456789
```

**Как получить:**
1. **Токен бота:** Откройте @BotFather в Telegram → `/newbot` → следуйте инструкциям
2. **ID админа:** Откройте @userinfobot в Telegram → он покажет ваш ID

### 🔹 ШАГ 3: Сохраните файл

В nano:
1. Нажмите `Ctrl+O` → `Enter` (сохранить)
2. Нажмите `Ctrl+X` (выйти)

### 🔹 ШАГ 4: Перезапустите бота

```bash
systemctl restart bot
```

### 🔹 ШАГ 5: Проверьте статус

```bash
systemctl status bot
```

Должно быть: `Active: active (running)`

### 🔹 ШАГ 6: Запустите бота в Telegram

1. Откройте вашего бота в Telegram
2. Нажмите `/start`
3. Если бот отвечает - всё работает! ✅

---

## 🔐 3X-UI ПАНЕЛЬ

Учётные данные сохранены в файле:

```bash
cat /root/BOTinok/xui_credentials.txt
```

Или посмотрите выше в терминале - они выводятся после установки.

**Доступ к панели:**
```
https://ВАШ_IP:ПОРТ/ПУТЬ
```

---

## 🛠️ КОМАНДЫ УПРАВЛЕНИЯ

```bash
# Статус бота
systemctl status bot

# Перезапуск
systemctl restart bot

# Остановка
systemctl stop bot

# Запуск
systemctl start bot

# Логи в реальном времени
journalctl -u bot -f

# Логи бота
tail -f /root/BOTinok/logs/bot_*.log
```

---

## ⚠️ ВОЗМОЖНЫЕ ПРОБЛЕМЫ

### Бот не запускается

**Проверьте логи:**
```bash
journalctl -u bot -f
```

**Частые ошибки:**
1. ❌ Не указан `TOKEN_MAIN` → Заполните .env
2. ❌ Не указан `MY_ID_TELEG` → Заполните .env
3. ❌ Неверный токен → Проверьте в @BotFather

### .env файл пустой

Откройте и заполните:
```bash
nano /root/BOTinok/.env
```

### Порт 3X-UI не открывается

Проверьте брандмауэр:
```bash
ufw status
```

---

## 📚 ДОПОЛНИТЕЛЬНАЯ ИНФОРМАЦИЯ

- **GitHub:** https://github.com/ShavlaK/BOTinok
- **Документация:** https://github.com/ShavlaK/BOTinok#readme

---

## ✅ ВСЁ ГОТОВО!

После настройки .env и перезапуска бота:
1. Откройте бота в Telegram
2. Нажмите `/start`
3. Настройте через `/add_server`

**Успехов! 🎉**
