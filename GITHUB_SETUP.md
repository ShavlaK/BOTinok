# 📤 Инструкция по развёртыванию на GitHub

## 🎯 Цель

Выгрузить проект на GitHub для автоматической установки одной командой.

---

## 📋 Шаг 1: Подготовка репозитория

### 1.1 Создайте репозиторий на GitHub

1. Зайдите на https://github.com
2. Нажмите **"New"** (создать репозиторий)
3. Название: `bot-bot`
4. Описание: `BOT Bot for Telegram - Автоматическая установка`
5. Видимость: **Public** (или Private для личного использования)
6. **Не** создавайте с README (у нас уже есть свой)
7. Нажмите **"Create repository"**

---

## 📤 Шаг 2: Загрузка файлов на GitHub

### Вариант A: Через Git (рекомендуется)

```bash
# Перейдите в директорию проекта
cd /Users/shavlak/Desktop/bot_bot/bot-bot-project

# Инициализируйте Git
git init

# Добавьте все файлы
git add .

# Сделайте первый коммит
git commit -m "Initial commit: BOT Bot v1.0"

# Добавьте удалённый репозиторий (замените ShavlaK)
git remote add origin https://github.com/ShavlaK/BOTinok.git

# Отправьте файлы на GitHub
git push -u origin main
```

### Вариант B: Через веб-интерфейс

1. В созданном репозитории нажмите **"uploading an existing file"**
2. Перетащите все файлы из папки `bot-bot-project`
3. Нажмите **"Commit changes"**

---

## ✏️ Шаг 3: Обновление ссылок в файлах

### 3.1 Отредактируйте файлы

Замените `ShavlaK` на ваш ник GitHub в следующих файлах:

1. **README.md** (3 места):
   - Строка 8: `https://github.com/ShavlaK/BOTinok`
   - Строка 36: `https://github.com/ShavlaK/BOTinok`
   - Строка 40: `https://github.com/ShavlaK/BOTinok`

2. **install.sh** (4 места):
   - Строка 135: `https://github.com/ShavlaK/BOTinok`

3. **install-lite.sh** (3 места):
   - Строка 133: `https://github.com/ShavlaK/BOTinok`

4. **docker/Dockerfile**:
   - Строка 8: `ShavlaK`

### 3.2 Как заменить

```bash
# В директории проекта
cd /Users/shavlak/Desktop/bot_bot/bot-bot-project

# Замените ShavlaK на ваш ник (пример: coden)
sed -i '' 's/ShavlaK/coden/g' README.md install.sh install-lite.sh docker/Dockerfile
```

---

## 🔄 Шаг 4: Обновление репозитория

После изменений отправьте их на GitHub:

```bash
# Проверьте изменения
git status

# Добавьте изменённые файлы
git add .

# Сделайте коммит
git commit -m "Update: replaced USERNAME with actual GitHub username"

# Отправьте на GitHub
git push
```

---

## ✅ Шаг 5: Проверка установки

### 5.1 Проверка ссылок

Откройте в браузере:
```
https://raw.githubusercontent.com/ShavlaK/BOTinok/main/install.sh
```

Вы должны увидеть содержимое установочного скрипта.

### 5.2 Тестовая установка

На чистом сервере (или VM) выполните:

```bash
# Основная версия
bash <(curl -Ls https://raw.githubusercontent.com/ShavlaK/BOTinok/main/install.sh)

# Lite версия
bash <(curl -Ls https://raw.githubusercontent.com/ShavlaK/BOTinok/main/install-lite.sh)
```

---

## 📊 Шаг 6: GitHub Actions (опционально)

### Автоматическая проверка кода

Создайте файл `.github/workflows/ci.yml`:

```yaml
name: CI/CD

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install flake8 mypy
      
      - name: Lint code
        run: |
          flake8 bot/ --count --select=E9,F63,F7,F82 --show-source --statistics

  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Run tests
        run: |
          echo "Tests would run here"
```

---

## 🏷️ Шаг 7: Создание релиза

### 7.1 Создание тега

```bash
# Создайте тег версии
git tag -a v1.0.0 -m "Release version 1.0.0"

# Отправьте тег на GitHub
git push origin v1.0.0
```

### 7.2 Создание релиза на GitHub

1. Зайдите в репозиторий на GitHub
2. Перейдите во вкладку **"Releases"**
3. Нажмите **"Draft a new release"**
4. Выберите тег: `v1.0.0`
5. Название: `Version 1.0.0`
6. Описание изменений
7. Нажмите **"Publish release"**

---

## 📝 Шаг 8: Документация

### 8.1 Обновите README

Добавьте бейджи в начало README.md:

```markdown
# 🚀 BOT Bot

[![Version](https://img.shields.io/github/v/release/ShavlaK/BOTinok)](https://github.com/ShavlaK/BOTinok/releases)
[![License](https://img.shields.io/github/license/ShavlaK/BOTinok)](LICENSE)
[![Stars](https://img.shields.io/github/stars/ShavlaK/BOTinok)](https://github.com/ShavlaK/BOTinok/stargazers)
[![Forks](https://img.shields.io/github/forks/ShavlaK/BOTinok)](https://github.com/ShavlaK/BOTinok/network/members)

> Автоматическая установка BOT бота для Telegram
```

### 8.2 Добавьте скриншоты

Создайте папку `screenshots/` и добавьте:
- Скриншот главного меню бота
- Скриншот процесса установки
- Скриншот панели 3X-UI

---

## 🔒 Шаг 9: Безопасность

### 9.1 .gitignore

Убедитесь что `.gitignore` содержит:

```
.env
*.db
*.log
xui_credentials.txt
```

### 9.2 Секреты

**Никогда не выкладывайте:**
- Токены бота
- API ключи платёжных систем
- Пароли от серверов
- Личные данные

---

## 📈 Шаг 10: Продвижение

### 10.1 Добавьте тему

В настройках репозитория добавьте темы:
- `bot`
- `telegram-bot`
- `vless`
- `proxy`
- `automation`

### 10.2 Описание

Краткое описание для репозитория:
```
🚀 Автоматическая установка BOT бота для Telegram с 3X-UI панелью. 
Поддержка VLESS, whitelist-туннели, платёжные системы.
```

---

## 🆘 Troubleshooting

### Ошибка: "remote: Repository not found"

**Решение:**
```bash
# Проверьте что репозиторий существует
# Проверьте права доступа
# Для private репозиториев используйте токен:
git remote set-url origin https://YOUR_TOKEN@github.com/ShavlaK/BOTinok.git
```

### Ошибка: "failed to push some refs"

**Решение:**
```bash
# Синхронизируйте с удалённым репозиторием
git pull origin main --rebase
git push
```

### Ошибка при установке: "404 Not Found"

**Решение:**
- Проверьте что заменили `ShavlaK` во всех файлах
- Убедитесь что репозиторий public (или используйте токен)

---

## 📚 Дополнительные ресурсы

- [Git Documentation](https://git-scm.com/doc)
- [GitHub Guides](https://guides.github.com/)
- [Creating Releases](https://docs.github.com/en/repositories/releasing-projects-on-github)
- [GitHub Actions](https://docs.github.com/en/actions)

---

## ✅ Чек-лист готовности

- [ ] Репозиторий создан на GitHub
- [ ] Все файлы загружены
- [ ] `ShavlaK` заменён на ваш ник
- [ ] `.env` в `.gitignore`
- [ ] README.md заполнен
- [ ] LICENSE добавлен
- [ ] Тестовая установка прошла успешно
- [ ] Ссылки работают
- [ ] Создан первый релиз

---

**Готово! Ваш проект на GitHub! 🎉**
