import sqlite3
import sys

from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableWidgetItem


class Window(QMainWindow):
    def __init__(self):
        super(QMainWindow, self).__init__()

        self.con = sqlite3.connect("Cost.db")
        cur = self.con.cursor()

        self.title = ["Категория", "Дата", "Цена"]
        self.table = cur.execute("SELECT CategoryId, Date, SumCost FROM Cost").fetchall()

        uic.loadUi("window.ui", self)

        self.setWindowTitle("Учет расходов")

        self.tableWidget.setRowCount(len(self.table))
        self.tableWidget.setColumnCount(len(self.title))
        self.tableWidget.setHorizontalHeaderLabels(self.title)

        # self.graph = GraphWidget(self.centralWidget())
        # self.graph.setGeometry(440, 10, 751, 771)

        self.show_records(self.table)

        self.button_add.clicked.connect(self.add)
        self.button_remove.clicked.connect(self.remove)
        self.button_edit.clicked.connect(self.edit)

    def show_records(self, table):
        for i, row in enumerate(table):
            for j, value in enumerate(row):
                self.tableWidget.setItem(i, j, QTableWidgetItem(str(value)))

    def sort(self):
        pass

    def add(self, event):
        pass

    def remove(self):
        pass

    def edit(self):
        pass

    def add_category(self):
        pass


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main = Window()
    main.show()
    sys.exit(app.exec_())
