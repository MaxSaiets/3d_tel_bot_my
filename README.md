# Telegram Shop Stack (Bot + WebApp + EspoCRM + Nova Poshta)

Нижче інструкція саме під ваш запит: окремий venv для локальної розробки, швидкий перенос на сервер і автовідновлення сервісів.

## 1) Локально: окремий venv
### Windows (PowerShell)
```powershell
cd D:\3d_tel_bot_my
powershell -ExecutionPolicy Bypass -File .\scripts\bootstrap_venv.ps1 -VenvDir .venv-bot
```

### Linux/macOS
```bash
cd /path/to/3d_tel_bot_my
bash scripts/bootstrap_venv.sh .venv-bot
```

Після цього у вас ізольоване оточення `.venv-bot` тільки для цього проєкту.

## 2) Налаштування env файлів
### Основний бекенд
```bash
cp .env.example .env
```
Заповнити обов'язково:
- `BOT_TOKEN`
- `WEBHOOK_BASE_URL`
- `WEBHOOK_SECRET`
- `WEBAPP_URL`
- `ADMIN_GROUP_ID`
- `ESPOCRM_BASE_URL`
- `ESPOCRM_API_KEY`
- `NOVA_POSHTA_API_KEY` (якщо НП увімкнено)

### EspoCRM
```bash
cp deploy/espocrm/.env.example deploy/espocrm/.env
```
Заповнити:
- `ESPOCRM_SITE_URL`
- `ESPO_DB_ROOT_PASSWORD`
- `ESPO_DB_PASSWORD`
- `ESPO_ADMIN_PASSWORD`

## 3) Швидкий перенос на сервер
### На вашому ПК (створити архів)
```bash
bash scripts/package_for_server.sh
```
Отримаєте `telegram_stack_YYYYMMDD_HHMMSS.tar.gz`.

### Передати на сервер
```bash
scp telegram_stack_YYYYMMDD_HHMMSS.tar.gz root@YOUR_SERVER_IP:/tmp/
```

### На сервері
```bash
sudo mkdir -p /opt/telegram-shop
sudo tar -xzf /tmp/telegram_stack_YYYYMMDD_HHMMSS.tar.gz -C /opt/telegram-shop
cd /opt/telegram-shop
```

Скопіюйте/створіть там:
- `/opt/telegram-shop/.env`
- `/opt/telegram-shop/deploy/espocrm/.env`

## 4) Запуск всього стеку через Docker
```bash
cd /opt/telegram-shop
docker compose -f docker-compose.full.yml up -d --build
```

## 5) Автозапуск після ребуту + авто-recover
Встановити systemd юніти:
```bash
cd /opt/telegram-shop
bash deploy/scripts/install_systemd.sh
```

Що це дає:
- `telegram-shop-stack.service` — піднімає стек на старті сервера.
- `telegram-shop-health.timer` — кожні 2 хв перевіряє health і робить recover, якщо треба.

## 6) Telegram підключення
### Web App URL у BotFather
- `/mybots` -> ваш бот -> `Bot Settings` -> `Menu Button` -> `Configure menu button`
- URL = `WEBAPP_URL`

### Виставити webhook
```bash
cd /opt/telegram-shop
bash deploy/scripts/set_webhook.sh
```

## 7) Перевірка що все працює
1. Відкрити:
   - `https://t.me/<bot_username>?start=yt_video_01`
2. Натиснути `Open Store`, оформити замовлення.
3. Перевірити, що в EspoCRM створився `Lead`.
4. Натиснути `Support`, написати в бот.
5. В адмін-групі дати `Reply` на форвард — відповідь має повернутись користувачу.

## 8) Корисні команди на сервері
```bash
cd /opt/telegram-shop

docker compose -f docker-compose.full.yml ps
docker compose -f docker-compose.full.yml logs -f app
docker compose -f docker-compose.full.yml restart app nginx
docker compose -f docker-compose.full.yml down
```

Systemd статус:
```bash
systemctl status telegram-shop-stack.service --no-pager
systemctl status telegram-shop-health.timer --no-pager
```
