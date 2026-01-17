import turtle

# Настройка экрана
screen = turtle.Screen()
screen.title("DVD Logo Animation")
screen.bgcolor("black")
screen.setup(width=800, height=600)
screen.tracer(0) # Отключаем анимацию для плавности

# Создание "логотипа"
dvd = turtle.Turtle()
dvd.shape("square") # Можно заменить на круг 'circle'
dvd.shapesize(stretch_wid=2, stretch_len=4) # Делаем прямоугольник
dvd.penup()
dvd.color("white")
dvd.goto(0, 0)

# Начальная скорость
dvd.dx = 0.15
dvd.dy = 0.15

colors = ["red", "blue", "green", "yellow", "purple", "orange", "cyan"]
color_index = 0

while True:
    screen.update() # Обновляем кадр вручную
    
    # Движение
    dvd.setx(dvd.xcor() + dvd.dx)
    dvd.sety(dvd.ycor() + dvd.dy)

    # Проверка границ (отскок)
    # По горизонтали
    if dvd.xcor() > 360 or dvd.xcor() < -360:
        dvd.dx *= -1
        color_index = (color_index + 1) % len(colors)
        dvd.color(colors[color_index])

    # По вертикали
    if dvd.ycor() > 280 or dvd.ycor() < -280:
        dvd.dy *= -1
        color_index = (color_index + 1) % len(colors)
        dvd.color(colors[color_index])
