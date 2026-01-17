#include <windows.h>
#include <iostream>
#include <cstdlib>

using namespace std;

int main() {
    cout << "=================================" << endl;
    cout << "   АВТОМАТИЧЕСКОЕ ВЫКЛЮЧЕНИЕ ПК" << endl;
    cout << "=================================" << endl << endl;
    
    // Добавляем в автозагрузку
    HKEY hKey;
    char exePath[MAX_PATH];
    GetModuleFileName(NULL, exePath, MAX_PATH);
    
    cout << "🔧 Добавляем в автозагрузку..." << endl;
    
    if (RegOpenKeyEx(HKEY_CURRENT_USER, 
        "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run", 
        0, KEY_WRITE, &hKey) == ERROR_SUCCESS) {
        
        RegSetValueEx(hKey, "PCManager", 0, REG_SZ, 
                     (BYTE*)exePath, strlen(exePath) + 1);
        RegCloseKey(hKey);
        cout << "✅ Успешно добавлено в автозагрузку" << endl;
    } else {
        cout << "❌ Ошибка добавления в автозагрузку" << endl;
    }
    
    // Выключаем компьютер
    cout << "🔌 Выключаем компьютер через 60 секунд..." << endl;
    system("shutdown /s /t 60");
    
    cout << "💡 Для отмены введите: shutdown /a" << endl;
    cout << "⏳ Ожидайте 10 секунд..." << endl;
    
    Sleep(10000);
    return 0;
}
