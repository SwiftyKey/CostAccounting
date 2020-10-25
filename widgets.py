from PyQt5 import uic
from PyQt5.QtCore import QDate
from PyQt5.QtWidgets import QWidget, QDialog, QInputDialog
from datetime import date

import sqlite3


class NoteWindow(QDialog):
    def __init__(self, user_id, parent=None):
        super(NoteWindow, self).__init__(parent)

        self.con = sqlite3.connect("Cost.db")

        self.user_id = user_id
        self.category = ""
        self.date = ""
        self.cost = ""

        uic.loadUi("new_note_window.ui", self)
        self.setWindowTitle("Новая запись")

        cur = self.con.cursor()
        categories = map(lambda item: item[0], cur.execute("SELECT Title FROM Category").fetchall())
        self.select_category.addItems(categories)

        self.select_date.setMinimumDate(QDate(date.today()))

        self.button_add.clicked.connect(self.add_note)
        self.button_create_category.clicked.connect(self.new_category)

    def new_category(self):
        title = QInputDialog.getText(self, "Новая категория",
                                     "Введите название новой категории")
        if title[0] and title[1]:
            cur = self.con.cursor()
            cur.execute(f"INSERT INTO Category(Title) VALUES('{title[0]}')")
            cur.close()
            self.con.commit()

            self.select_category.insertItem(0, title[0])
            self.select_category.setCurrentIndex(0)

    def add_note(self):
        cur = self.con.cursor()

        self.category = cur.execute(f'''SELECT CategoryId FROM Category 
WHERE Title = "{self.select_category.currentText()}"''').fetchone()[0]
        self.date = self.select_date.date().toString('yyyy-MM-dd')
        self.cost = self.select_cost.value()

        cur.execute(f'''INSERT INTO Cost(UserId, CategoryId, Date, SumCost) 
VALUES({self.user_id}, {self.category}, "{self.date}", {self.cost})''')
        cur.close()
        self.con.commit()

        self.close()


class LoginWidget(QWidget):
    pass


class Registration:
    pass
