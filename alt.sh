#!/bin/bash
FLASH_PATH=$(dirname "$0")
OUTPUT_FILE="$FLASH_PATH/usr_data.txt"

# Сбор структуры /usr и сохранение на флешку
find /usr -type d 2>/dev/null > "$OUTPUT_FILE"

echo "Готово." # Единственный вывод
