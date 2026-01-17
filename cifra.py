import random

# Список всех возможных цифр
digits = [1, 2, 3, 4, 5, 6, 7, 8, 9]
# Что мы уже знаем о позициях
guessed = [None, None, None, None]
# Список цифр, которые точно НЕ подходят для конкретных позиций
bad_variants = [set(), set(), set(), set()]

print("Загадайте 4 цифры от 1 до 9.")

while None in guessed:
    attempt = []
    # Собираем попытку
    for i in range(4):
        if guessed[i] is not None:
            attempt.append(guessed[i])
        else:
            # Выбираем только те цифры, которые не заняты и не помечены как "плохие" для этого места
            valid_choices = [d for d in digits if d not in attempt and d not in bad_variants[i]]
            if not valid_choices: # Если исключили всё, сбрасываем плохие варианты (на случай ошибки ввода)
                bad_variants[i].clear()
                valid_choices = [d for d in digits if d not in attempt]
            
            pick = random.choice(valid_choices)
            attempt.append(pick)
    
    print(f"\nМоя попытка: {attempt}")
    
    for i in range(4):
        if guessed[i] is None:
            print(f"Цифра {attempt[i]} на месте {i+1} верна? (1-да, 0-нет)")
            answer = input()
            if answer == "1":
                guessed[i] = attempt[i]
            else:
                bad_variants[i].add(attempt[i])

print(f"\nГотово! Ваше число: {guessed}")
