import sys
import sqlite3
import requests
from bs4 import BeautifulSoup
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget, QLineEdit, QPushButton, QTextEdit, QLabel, QHBoxLayout
)


# Классы HTML блоков для парсинга
CARD_CLASS = "x-product-card__card"
NAME_CLASS = "x-product-card-description__product-name"
PRICE_CLASS = "x-product-card-description__price-WEB8507_price_no_bold"
LINK_CLASS = "x-product-card__link"

# Парсинг страницы и сохранение в базу
def parse_and_save(url, db_path="products.db"):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    # Очистка базы данных перед новым парсингом
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS products")
    cursor.execute("""
        CREATE TABLE products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            price INTEGER,
            link TEXT
        )
    """)

    # Поиск карточек товаров
    products = soup.find_all("div", class_=CARD_CLASS)
    for product in products:
        name = product.find("div", class_=NAME_CLASS).get_text(strip=True)
        price_text = product.find("span", class_=PRICE_CLASS).get_text(strip=True)
        price = int("".join(filter(str.isdigit, price_text)))
        link = "https://www.lamoda.ru" + product.find("a", class_=LINK_CLASS).get("href")
        cursor.execute("INSERT INTO products (name, price, link) VALUES (?, ?, ?)", (name, price, link))

    conn.commit()
    conn.close()

# Анализ и выбор самого дешевого товара
def get_cheapest_product(db_path="products.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name, price, link FROM products ORDER BY price ASC LIMIT 1")
    product = cursor.fetchone()
    conn.close()
    return product

# Интерфейс приложения
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Парсер Lamoda")
        self.setGeometry(100, 100, 600, 400)

        layout = QVBoxLayout()

        # Поле для ввода URL
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Введите URL страницы для парсинга")
        layout.addWidget(QLabel("URL страницы:"))
        layout.addWidget(self.url_input)

        # Кнопка для запуска парсинга
        self.parse_button = QPushButton("Спарсить")
        self.parse_button.clicked.connect(self.start_parsing)
        layout.addWidget(self.parse_button)

        # Текстовое поле для вывода результатов
        self.result_view = QTextEdit()
        self.result_view.setReadOnly(True)
        layout.addWidget(QLabel("Результаты:"))
        layout.addWidget(self.result_view)

        # Основной виджет и слой
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def start_parsing(self):
        url = self.url_input.text().strip()
        if not url:
            self.result_view.setText("Ошибка: Введите URL для парсинга.")
            return

        try:
            # Парсинг и анализ
            parse_and_save(url)
            cheapest = get_cheapest_product()
            if cheapest:
                name, price, link = cheapest
                self.result_view.setText(f"Самый дешевый товар:\n\nНазвание: {name}\nЦена: {price} ₽\nСсылка: {link}")
            else:
                self.result_view.setText("Нет данных для отображения.")
        except Exception as e:
            self.result_view.setText(f"Ошибка: {e}")

# Запуск приложения
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())