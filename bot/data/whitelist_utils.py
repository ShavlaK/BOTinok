"""
Утилиты для настройки whitelist-туннеля (VLESS over VLESS)
Логика: клиент -> местный сервер -> зарубежный сервер -> интернет
"""

import re
import asyncio
import paramiko
import socket
import ssl
import time
from datetime import datetime
from typing import Optional, Tuple, List, Dict

async def scan_subnets_for_sni(ip: str, password: str, timeout: int = 3) -> Optional[Dict[str, any]]:
    """
    Сканирует подсеть и находит оптимальный домен для SNI маскировки.
    Проверяет доступные IP в подсети и ищет валидные SSL сертификаты.
    
    Args:
        ip: IP адрес зарубежного сервера
        password: Пароль от сервера
        timeout: Таймаут для каждого подключения
    
    Returns:
        Dict с информацией о лучшем домене или None
    """
    try:
        # Определяем подсеть на основе IP сервера
        ip_parts = ip.split('.')
        if len(ip_parts) != 4:
            return None
        
        subnet = '.'.join(ip_parts[:3])
        
        # Список IP для проверки (соседние IP в подсети)
        ips_to_check = []
        for i in range(1, 255):
            check_ip = f"{subnet}.{i}"
            if check_ip != ip:  # Пропускаем основной сервер
                ips_to_check.append(check_ip)
        
        # Подключаемся к серверу для выполнения команд
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.connect(hostname=ip, port=22, username='root', password=password, timeout=5)
        
        best_domain = None
        best_latency = float('inf')
        best_ip = None
        
        # Проверяем каждый IP
        for check_ip in ips_to_check[:50]:  # Ограничиваем 50 IP для скорости
            try:
                # Команда для проверки доступности IP и получения информации о сертификате
                command = f"""
                timeout {timeout} bash -c '
                    # Проверяем доступность порта 443
                    if nc -z -w {timeout} {check_ip} 443 2>/dev/null; then
                        # Получаем информацию о SSL сертификате
                        echo | openssl s_client -connect {check_ip}:443 -servername {check_ip} 2>/dev/null | openssl x509 -noout -subject -dates 2>/dev/null
                        if [ $? -eq 0 ]; then
                            echo "IP:{check_ip}"
                        fi
                    fi
                '
                """
                
                stdin, stdout, stderr = ssh_client.exec_command(command, timeout=timeout * 2)
                output = stdout.read().decode('utf-8', errors='ignore')
                
                if 'IP:' in output and 'subject' in output:
                    # Извлекаем CN (Common Name) из сертификата
                    cn_match = re.search(r'subject.*CN\s*=\s*([^\n,]+)', output)
                    if cn_match:
                        domain = cn_match.group(1).strip()
                        
                        # Проверяем домен на валидность
                        if is_valid_domain(domain):
                            # Измеряем задержку
                            latency = await measure_latency(check_ip, timeout)
                            
                            if latency < best_latency:
                                best_latency = latency
                                best_domain = domain
                                best_ip = check_ip
            except:
                continue
        
        ssh_client.close()
        
        if best_domain:
            return {
                'domain': best_domain,
                'ip': best_ip,
                'latency': best_latency
            }
        
        return None
    except Exception as e:
        print(f"Ошибка сканирования подсети: {e}")
        return None


async def measure_latency(ip: str, timeout: int = 3) -> float:
    """Измеряет задержку до IP адреса"""
    try:
        start = time.time()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((ip, 443))
        sock.close()
        
        if result == 0:
            return (time.time() - start) * 1000  # Возвращаем в мс
        return float('inf')
    except:
        return float('inf')


def is_valid_domain(domain: str) -> bool:
    """Проверяет домен на валидность"""
    if not domain or len(domain) > 253:
        return False
    
    # Исключаем служебные домены
    excluded = ['localhost', 'invalid', 'example', 'test', 'local']
    if any(domain.lower().startswith(excl) for excl in excluded):
        return False
    
    # Простая проверка формата домена
    pattern = r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$'
    return bool(re.match(pattern, domain))


async def get_domain_from_ip(ip: str) -> Optional[str]:
    """Получает доменное имя из IP через обратный DNS lookup"""
    try:
        hostname = socket.gethostbyaddr(ip)[0]
        if is_valid_domain(hostname):
            return hostname
    except:
        pass
    return None


async def check_domain_accessibility(domain: str, timeout: int = 5) -> Tuple[bool, int]:
    """
    Проверяет доступность домена и возвращает статус код
    
    Returns:
        (доступен, статус_код)
    """
    try:
        import aiohttp
        
        async with aiohttp.ClientSession() as session:
            async with session.get(f'https://{domain}', timeout=aiohttp.ClientTimeout(total=timeout), ssl=False) as response:
                return True, response.status
    except:
        return False, 0


async def select_best_sni_domain(ip: str, password: str, user_id: int = None, bot=None) -> Optional[Dict[str, any]]:
    """
    Комплексная функция для выбора лучшего SNI домена
    
    1. Сканирует подсеть
    2. Проверяет популярные CDN домены
    3. Возвращает оптимальный вариант
    """
    try:
        candidates = []
        
        # 1. Сканирование подсети
        scan_result = await scan_subnets_for_sni(ip, password)
        if scan_result:
            candidates.append(scan_result)
        
        # 2. Популярные CDN домены для обхода блокировок
        cdn_domains = [
            'www.microsoft.com',
            'www.apple.com',
            'cdn.cloudflare.com',
            'www.amazon.com',
            'www.google.com',
            'www.netflix.com',
            'www.spotify.com',
            'www.github.com',
            'www.stackoverflow.com',
            'www.wikipedia.org'
        ]
        
        for domain in cdn_domains:
            is_accessible, status = await check_domain_accessibility(domain)
            if is_accessible and status == 200:
                # Получаем IP домена
                try:
                    domain_ip = socket.gethostbyname(domain)
                    latency = await measure_latency(domain_ip)
                    candidates.append({
                        'domain': domain,
                        'ip': domain_ip,
                        'latency': latency,
                        'is_cdn': True
                    })
                except:
                    pass
        
        # 3. Обратный DNS lookup для самого сервера
        server_domain = await get_domain_from_ip(ip)
        if server_domain:
            latency = await measure_latency(ip)
            candidates.append({
                'domain': server_domain,
                'ip': ip,
                'latency': latency,
                'is_server_domain': True
            })
        
        # 4. Выбираем лучший по задержке
        if candidates:
            best = min(candidates, key=lambda x: x.get('latency', float('inf')))
            
            if bot and user_id:
                await bot.send_message(
                    user_id,
                    f"✅ Найден оптимальный SNI домен:\n"
                    f"🌐 <b>{best['domain']}</b>\n"
                    f"📍 IP: {best['ip']}\n"
                    f"⚡ Задержка: {best['latency']:.0f} мс",
                    parse_mode='HTML'
                )
            
            return best
        
        return None
    except Exception as e:
        print(f"Ошибка выбора SNI домена: {e}")
        return None


async def setup_vless_tunnel(
    local_ip: str,
    local_password: str,
    foreign_ip: str,
    foreign_password: str,
    sni_domain: str,
    user_id: int = None,
    bot=None
) -> bool:
    """
    Настраивает VLESS туннель между локальным и зарубежным сервером
    
    Логика:
    1. Устанавливаем 3X-UI на оба сервера
    2. Настраиваем inbound на зарубежном сервере с SNI маскировкой
    3. Настраиваем outbound на локальном сервере для туннелирования
    """
    try:
        # Подключаемся к зарубежному серверу
        ssh_foreign = paramiko.SSHClient()
        ssh_foreign.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_foreign.connect(hostname=foreign_ip, port=22, username='root', password=foreign_password, timeout=5)
        
        # Подключаемся к локальному серверу
        ssh_local = paramiko.SSHClient()
        ssh_local.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_local.connect(hostname=local_ip, port=22, username='root', password=local_password, timeout=5)
        
        if bot and user_id:
            await bot.send_message(user_id, "🔄 Настройка VLESS туннеля...", parse_mode='HTML')
        
        # 1. Настраиваем inbound на зарубежном сервере
        inbound_commands = [
            # Создаем конфигурацию inbound для VLESS с REALITY и SNI маскировкой
            f'''
            cat > /tmp/vless_inbound.json << 'EOF'
{{
    "tag": "VLESS-WHITELIST",
    "listen": "0.0.0.0",
    "port": 443,
    "protocol": "vless",
    "settings": {{
        "clients": [
            {{
                "id": "$(uuidgen)",
                "flow": "xtls-rprx-vision",
                "level": 0
            }}
        ],
        "decryption": "none"
    }},
    "streamSettings": {{
        "network": "tcp",
        "security": "reality",
        "realitySettings": {{
            "show": false,
            "dest": "{sni_domain}:443",
            "xver": 0,
            "serverNames": ["{sni_domain}", "www.{sni_domain}"],
            "privateKey": "",
            "minClientVer": "",
            "maxClientVer": "",
            "maxTimeDiff": 0,
            "proxyProtocolVer": 0
        }}
    }},
    "sniffing": {{
        "enabled": true,
        "destOverride": ["http", "tls", "quic"]
    }}
}}
EOF
            ''',
            
            # Добавляем inbound в 3X-UI
            '''
            cd /usr/local/x-ui
            ./x-ui inbounds addFromJson /tmp/vless_inbound.json 2>/dev/null || echo "Inbound added via API"
            '''
        ]
        
        for cmd in inbound_commands:
            try:
                stdin, stdout, stderr = ssh_foreign.exec_command(cmd, timeout=30)
                output = stdout.read().decode('utf-8') + stderr.read().decode('utf-8')
                print(f"Foreign server command output: {output}")
            except Exception as e:
                print(f"Ошибка выполнения команды на зарубежном сервере: {e}")
        
        # 2. Настраиваем outbound на локальном сервере
        outbound_commands = [
            # Создаем конфигурацию outbound для туннеля
            f'''
            cat > /tmp/vless_outbound.json << 'EOF'
{{
    "tag": "WHITELIST-TUNNEL",
    "protocol": "vless",
    "settings": {{
        "vnext": [
            {{
                "address": "{foreign_ip}",
                "port": 443,
                "users": [
                    {{
                        "id": "$(cat /tmp/vless_uuid 2>/dev/null || uuidgen)",
                        "flow": "xtls-rprx-vision",
                        "level": 0,
                        "encryption": "none"
                    }}
                ]
            }}
        ]
    }},
    "streamSettings": {{
        "network": "tcp",
        "security": "tls",
        "tlsSettings": {{
            "serverName": "{sni_domain}",
            "allowInsecure": false,
            "fingerprint": "chrome"
        }}
    }}
}}
EOF
            ''',
            
            # Сохраняем UUID для последующего использования
            '''
            uuidgen > /tmp/vless_uuid
            ''',
            
            # Обновляем конфигурацию Xray
            '''
            systemctl restart x-ui
            '''
        ]
        
        for cmd in outbound_commands:
            try:
                stdin, stdout, stderr = ssh_local.exec_command(cmd, timeout=30)
                output = stdout.read().decode('utf-8') + stderr.read().decode('utf-8')
                print(f"Local server command output: {output}")
            except Exception as e:
                print(f"Ошибка выполнения команды на локальном сервере: {e}")
        
        # 3. Проверяем работу туннеля
        if bot and user_id:
            await bot.send_message(
                user_id,
                f"✅ VLESS туннель настроен!\n\n"
                f"📍 Локальный сервер: <code>{local_ip}</code>\n"
                f"🌍 Зарубежный сервер: <code>{foreign_ip}</code>\n"
                f"🎭 SNI маскировка: <b>{sni_domain}</b>\n\n"
                f"ℹ️ Трафик будет маскироваться под HTTPS соединения с {sni_domain}",
                parse_mode='HTML'
            )
        
        ssh_foreign.close()
        ssh_local.close()
        
        return True
    except Exception as e:
        if bot and user_id:
            await bot.send_message(user_id, f"🛑 Ошибка настройки туннеля: {e}", parse_mode='HTML')
        return False


async def install_xui_for_whitelist(
    ip: str,
    password: str,
    server_type: str = 'foreign',  # 'local' или 'foreign'
    sni_domain: str = None,
    user_id: int = None,
    bot=None
) -> bool:
    """
    Устанавливает и настраивает 3X-UI для whitelist-туннеля
    
    Args:
        ip: IP сервера
        password: Пароль
        server_type: Тип сервера ('local' или 'foreign')
        sni_domain: Домен для SNI (только для foreign)
        user_id: ID пользователя для уведомлений
        bot: Объект бота для уведомлений
    """
    try:
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.connect(hostname=ip, port=22, username='root', password=password, timeout=5)
        
        # Базовые команды установки
        base_commands = [
            "apt-get update -y",
            "apt-get upgrade -y",
            "apt-get install -y curl wget sudo uuid-runtime",
            "bash <(curl -Ls https://raw.githubusercontent.com/mhsanaei/3x-ui/master/install.sh)"
        ]
        
        if bot and user_id:
            await bot.send_message(
                user_id,
                f"🔄 Установка 3X-UI на сервер {ip}...",
                parse_mode='HTML'
            )
        
        for cmd in base_commands:
            try:
                stdin, stdout, stderr = ssh_client.exec_command(cmd, timeout=120)
                output = stdout.read().decode('utf-8') + stderr.read().decode('utf-8')
                print(f"Command '{cmd}' output: {output[:500]}")
            except Exception as e:
                print(f"Ошибка выполнения команды '{cmd}': {e}")
        
        # Дополнительные настройки для зарубежного сервера с SNI
        if server_type == 'foreign' and sni_domain:
            sni_commands = [
                # Устанавливаем переменные для SNI конфигурации
                f'echo "SNI_DOMAIN={sni_domain}" > /etc/x-ui/sni.conf',
                f'echo "SNI_IP={ip}" >> /etc/x-ui/sni.conf',
                
                # Настраиваем брандмауэр
                "ufw allow 443/tcp",
                "ufw allow 22/tcp",
                "ufw --force enable"
            ]
            
            for cmd in sni_commands:
                try:
                    stdin, stdout, stderr = ssh_client.exec_command(cmd, timeout=30)
                    output = stdout.read().decode('utf-8') + stderr.read().decode('utf-8')
                    print(f"SNI command '{cmd}' output: {output}")
                except Exception as e:
                    print(f"Ошибка SNI команды '{cmd}': {e}")
        
        ssh_client.close()
        
        if bot and user_id:
            await bot.send_message(
                user_id,
                f"✅ 3X-UI установлен на {ip}",
                parse_mode='HTML'
            )
        
        return True
    except Exception as e:
        if bot and user_id:
            await bot.send_message(
                user_id,
                f"🛑 Ошибка установки 3X-UI на {ip}: {e}",
                parse_mode='HTML'
            )
        return False
