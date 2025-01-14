import sys
import os
import sqlite3
import requests
from bs4 import BeautifulSoup
from PyQt5 import QtCore, QtGui, QtWidgets
import webbrowser
from html import unescape
import re
import logo


# Классы HTML блоков для парсинга
CARD_CLASS = "x-product-card__card"
NAME_CLASS = "x-product-card-description__product-name"
PRICE_CLASS = "x-product-card-description__price-WEB8507_price_no_bold"
LINK_CLASS = "x-product-card__link"

# Парсинг страницы и сохранение в базу
# Путь к базе данных
db_path = "db/products.db"

# Функция для создания директории, если она не существует
def create_db_directory(path):
    directory = os.path.dirname(path)
    if not os.path.exists(directory):
        os.makedirs(directory)

# Функция для проверки наличия базы данных
def check_db_exists(db_path):
    return os.path.exists(db_path)

# Парсинг страницы и сохранение в базу
def parse_and_save(url, db_path=db_path):
    try:
        # Создаем директорию, если её нет
        create_db_directory(db_path)

        # Проверяем, существует ли база данных
        if not check_db_exists(db_path):
            print(f"База данных не существует, будет создана: {db_path}")
        else:
            print(f"База данных существует: {db_path}")

        # Подключаемся к базе данных
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM products")
        cursor.execute("DELETE FROM about")
        cursor.execute("DELETE FROM review")

        # Создаем таблицы, если они не существуют
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                price INTEGER,
                link TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS about (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name_thing TEXT,
                article TEXT,
                structure TEXT,
                color TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS review (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                review_count TEXT,
                countreview TEXT
            )
        """)

        # Проверим, что таблицы созданы
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"Таблицы в базе данных: {tables}")

        # Парсим страницу
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")

        # Поиск карточек товаров
        products = soup.find_all("div", class_= CARD_CLASS)
        if not products:
            print("Не удалось найти товары на странице.")
            return

        for product in products:
            try:
                name = product.find("div", class_="x-product-card-description__product-name").get_text(strip=True)
                price_text = product.find("span", class_="x-product-card-description__price-WEB8507_price_no_bold").get_text(strip=True)
                price = int("".join(filter(str.isdigit, price_text)))
                link = "https://www.lamoda.ru" + product.find("a", class_="x-product-card__link").get("href")

                cursor.execute("INSERT INTO products (name, price, link) VALUES (?, ?, ?)", (name, price, link))
            except Exception as e:
                print(f"Ошибка при парсинге товара: {e}")

        conn.commit()
        conn.close()
        print("Парсинг завершен успешно.")

    except Exception as e:
        print(f"Ошибка при парсинге страницы: {e}")


# Функция для парсинга информации о товаре с его страницы
def parse_and_save_product_info(link, db_path=db_path):
    try:
        response = requests.get(link)
        
        with open('example.txt', 'w', encoding='utf-8') as file:
            file.write(response.text)

        with open('example.txt', 'r', encoding='utf-8') as file:
            content = file.read()

        souch = re.search(r'"brand":\s*{[^}]*"name":\s*"(&quot;.*?&quot;)', content)
        article = re.search(r'"sku":\s*"([^"]+)"', content)
        structure = re.search(r'<span class="x-premium-product-description-attribute__value">([^<]+)</span>', content)
        color = re.search(r'"title"\s*:\s*"Цвет",\s*"type"\s*:\s*"text",\s*"value"\s*:\s*"([^"]+)"', content)

        # Ищем значения ratingValue и reviewCount в блоке aggregateRating
        rating_match = re.search(r'"ratingValue":\s*"([^"]+)"', content)
        review_count_match = re.search(r'"reviewCount":\s*"([^"]+)"', content)

        # Извлекаем данные
        rating_value = rating_match.group(1) if rating_match else None
        review_count = review_count_match.group(1) if review_count_match else None


        if souch:
            name_things = souch.group(1)
            name_things = unescape(name_things)  # Преобразуем &quot; в кавычки
            name_thing = name_things
            print(name_thing)  # Выведет Innamore
        else:
            print("Бренд не найден.")
        
        

        if structure:
            structure = structure.group(1)
            print(f"Состав найден: {structure}")
        else:
            print("Состав не найден")

        if color:
            color = color.group(1)
            print(f"Цвет найден: {color}")
        else:
            print("Цвет не найден")
        
        # Записываем информацию о товаре в таблицу `about`
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO about (name_thing, article, structure, color) VALUES (?, ?, ?, ?)", 
                       (name_thing, article.group(1), structure, color))
        cursor.execute("INSERT INTO review (review_count, countreview) VALUES (?, ?)", 
                       (rating_value, review_count))
        conn.commit()
        conn.close()

    except Exception as e:
        print(f"Ошибка при парсинге страницы товара: {e}")


# Анализ и выбор самого дешевого товара
def get_cheapest_product_and_parse_info(db_path=db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Получаем самый дешевый товар из таблицы `products`
    cursor.execute("SELECT name, price, link FROM products ORDER BY price ASC LIMIT 1")
    product = cursor.fetchone()
    
    if product:
        name, price, link = product
        # Парсим информацию о товаре и записываем её в таблицу `about`
        parse_and_save_product_info(link, db_path)

    conn.close()
    return product


# Получение информации о составе
def get_about_info(db_path=db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name_thing, article, structure, color FROM about")
    about_info = cursor.fetchall()  # Получаем все строки
    conn.close()
    return about_info


class InfoWindow(QtWidgets.QWidget):
    def __init__(self, about_info=None):
        super().__init__()
        self.setWindowTitle("Информация о товаре")
        self.setGeometry(100, 100, 454, 383)

        if about_info is None:
            about_info = ["", "", "", ""]  # По умолчанию пустые значения

        self.plainTextEdit = QtWidgets.QPlainTextEdit(self)
        self.plainTextEdit.setGeometry(QtCore.QRect(170, 80, 171, 41))
        self.plainTextEdit.setPlainText(about_info[0])  
        self.plainTextEdit.setReadOnly(True)

        self.label = QtWidgets.QLabel(self)
        self.label.setGeometry(QtCore.QRect(40, 90, 121, 16))
        self.label.setText("Название бренда:")

        self.plainTextEdit_2 = QtWidgets.QPlainTextEdit(self)
        self.plainTextEdit_2.setGeometry(QtCore.QRect(170, 140, 171, 41))
        self.plainTextEdit_2.setPlainText(about_info[1] if len(about_info) > 1 else "")  
        self.plainTextEdit_2.setReadOnly(True)

        self.label_2 = QtWidgets.QLabel(self)
        self.label_2.setGeometry(QtCore.QRect(40, 140, 131, 41))
        self.label_2.setText("Артикул:")

        self.plainTextEdit_3 = QtWidgets.QPlainTextEdit(self)
        self.plainTextEdit_3.setGeometry(QtCore.QRect(170, 200, 171, 41))
        self.plainTextEdit_3.setPlainText(about_info[2] if len(about_info) > 2 else "")  
        self.plainTextEdit_3.setReadOnly(True)

        self.label_3 = QtWidgets.QLabel(self)
        self.label_3.setGeometry(QtCore.QRect(40, 200, 131, 41))
        self.label_3.setText("Состав:")

        self.plainTextEdit_4 = QtWidgets.QPlainTextEdit(self)
        self.plainTextEdit_4.setGeometry(QtCore.QRect(170, 250, 171, 41))
        self.plainTextEdit_4.setPlainText(about_info[3] if len(about_info) > 3 else "")  
        self.plainTextEdit_4.setReadOnly(True)

        self.label_4 = QtWidgets.QLabel(self)
        self.label_4.setGeometry(QtCore.QRect(40, 250, 131, 41))
        self.label_4.setText("Цвет:")

        self.pushButton = QtWidgets.QPushButton(self)
        self.pushButton.setGeometry(QtCore.QRect(160, 320, 141, 41))
        self.pushButton.setText("Закрыть")
        self.pushButton.clicked.connect(self.close)


class Ui_Parcer(object):
    def setupUi(self, Parcer):
        Parcer.setObjectName("Parcer")
        Parcer.resize(756, 480)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/logo/logo.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        Parcer.setWindowIcon(icon)
        self.centralwidget = QtWidgets.QWidget(Parcer)
        self.centralwidget.setObjectName("centralwidget")

        self.pushButton = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton.setGeometry(QtCore.QRect(512, 170, 181, 28))
        self.pushButton.setObjectName("pushButton")

        self.textEdit = QtWidgets.QTextEdit(self.centralwidget)
        self.textEdit.setGeometry(QtCore.QRect(60, 130, 631, 31))
        self.textEdit.setObjectName("textEdit")
        
        self.label = QtWidgets.QLabel(self.centralwidget)
        self.label.setGeometry(QtCore.QRect(140, -40, 481, 161))
        self.label.setObjectName("label")
        
        self.label_2 = QtWidgets.QLabel(self.centralwidget)
        self.label_2.setGeometry(QtCore.QRect(80, 110, 101, 16))
        self.label_2.setObjectName("label_2")
        
        self.label_3 = QtWidgets.QLabel(self.centralwidget)
        self.label_3.setGeometry(QtCore.QRect(80, 180, 101, 16))
        self.label_3.setObjectName("label_3")
        
        self.widget = QtWidgets.QWidget(self.centralwidget)
        self.widget.setEnabled(True)
        self.widget.setGeometry(QtCore.QRect(60, 210, 631, 181))
        self.widget.setMouseTracking(False)
        self.widget.setAutoFillBackground(False)
        self.widget.setStyleSheet("background-color: rgb(255, 255, 255)")
        self.widget.setObjectName("widget")
        
        self.scroll_area = QtWidgets.QScrollArea(self.widget)
        self.scroll_area.setGeometry(QtCore.QRect(0, 0, 631, 181))
        self.scroll_area.setWidgetResizable(True)
        
        self.result_view = QtWidgets.QTextBrowser(self.scroll_area)
        self.result_view.setReadOnly(True)
        self.scroll_area.setWidget(self.result_view)

        # Добавляем метки для рейтинга и количества отзывов
        self.rating_label = QtWidgets.QLabel(self.centralwidget)
        self.rating_label.setGeometry(QtCore.QRect(80, 410, 300, 30))
        self.rating_label.setObjectName("rating_label")

        self.review_count_label = QtWidgets.QLabel(self.centralwidget)
        self.review_count_label.setGeometry(QtCore.QRect(80, 440, 300, 30))
        self.review_count_label.setObjectName("review_count_label")

        self.pushButton_2 = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_2.setEnabled(False)
        self.pushButton_2.setGeometry(QtCore.QRect(320, 170, 181, 28))
        self.pushButton_2.setObjectName("pushButton_2")

        Parcer.setCentralWidget(self.centralwidget)
        self.retranslateUi(Parcer)
        QtCore.QMetaObject.connectSlotsByName(Parcer)

    def retranslateUi(self, Parcer):
        _translate = QtCore.QCoreApplication.translate
        Parcer.setWindowTitle(_translate("Parcer", "Парсер Lamoda"))
        self.pushButton.setText(_translate("Parcer", "Спарсить"))
        self.label.setText(_translate("Parcer", "<html><head/><body><p><img src=\":/logo/logo.png\"/></p></body></html>"))
        self.label_2.setText(_translate("Parcer", "URL страницы:"))
        self.label_3.setText(_translate("Parcer", "Результаты:"))
        self.pushButton_2.setText(_translate("Parcer", "Состав товара"))

    def set_reviews_info(self, rating, review_count):
        # Обновляем метки с рейтингом и количеством отзывов
        self.rating_label.setText(f"Рейтинг: {rating}")
        self.review_count_label.setText(f"Количество отзывов: {review_count}")

class MainWindow(QtWidgets.QMainWindow, Ui_Parcer):
    def __init__(self):
        super().__init__()
        self.setupUi(self)  # Настройка UI для главного окна
        self.pushButton.clicked.connect(self.start_parsing)
        self.result_view.anchorClicked.connect(self.open_link)  # Обработчик клика по ссылке
        self.pushButton_2.clicked.connect(self.show_about_info)  # Обработчик кнопки состав товара

    def start_parsing(self):
        url = self.textEdit.toPlainText().strip()
        if not url:
            self.result_view.setText("Ошибка: Введите URL для парсинга.")
            return

        # Проверяем, что URL содержит "lamoda.ru"
        if "lamoda.ru" not in url:
            self.result_view.setText("Ошибка: Ссылка должна быть с сайта lamoda.ru.")
            return

        try:
            # Парсинг и анализ
            parse_and_save(url)
            
            # Получаем самую дешевую ссылку и сразу же парсим её информацию
            cheapest = get_cheapest_product_and_parse_info()
            
            if cheapest:
                name, price, link = cheapest
                result = f"Товар с самой низкой стоимостью:<br>Название: {name}<br>Цена: {price} ₽<br>Ссылка: <a href='{link}'>Ссылка на товар</a><br><br>"

                self.result_view.setHtml(result)  # Используем setHtml для отображения HTML
                self.pushButton_2.setEnabled(True)  # Активируем кнопку "Состав товара"

                # Получаем данные о рейтинге и количестве отзывов из базы данных
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT review_count, countreview FROM review ORDER BY id DESC LIMIT 1")
                review_data = cursor.fetchone()
                conn.close()

                if review_data:
                    rating, review_count = review_data
                    self.set_reviews_info(rating, review_count)
                else:
                    self.set_reviews_info("Не найдено", "Не найдено")
            
            else:
                self.result_view.setText("Нет данных для отображения.")
        
        except Exception as e:
            self.result_view.setText(f"Ошибка: {e}")

    def open_link(self, link):
        # Открываем ссылку в системном браузере
        webbrowser.open(link.toString())

    def show_about_info(self):
        # Получаем информацию о составе товара
        about_info = get_about_info()
        
        # Проверяем, есть ли информация о составе товара
        if not about_info:
            self.result_view.setText("Информация о составе не найдена.")
            return
        
        # Если информация о составе есть, открываем окно с информацией
        info = about_info[0]  # Выбираем первую запись
        self.info_window = InfoWindow(about_info=info)  # Передаем данные в окно
        self.info_window.show()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()  # Создание главного окна
    window.show()  # Отображение окна
    sys.exit(app.exec_())  # Запуск цикла обработки событий приложения
