@echo off
REM -- Скрипт-загрузчик для запуска PowerShell скрипта с USB-флешки --

:: 1. Установка политики выполнения (важно для запуска скриптов)
powershell -ExecutionPolicy Bypass -Command "Set-ExecutionPolicy Bypass -Scope Process -Force"

:: 2. Определение текущего пути флешки (буква диска)
SET "FLASH_DRIVE=%~d0"

:: 3. Определение полного пути к PS скрипту
SET "PS_SCRIPT_PATH=%FLASH_DRIVE%\windalt.ps1"

:: 4. Запуск PowerShell скрипта
start /min powershell.exe -ExecutionPolicy Bypass -File "%PS_SCRIPT_PATH%"

:: 5. Задержка для выполнения скрипта (опционально, но рекомендуется)
timeout /t 3 /nobreak >nul

:: 6. Удаление следов (опционально: удалить сам .bat файл)
:: del "%~f0"

:: 7. Завершение
exit
