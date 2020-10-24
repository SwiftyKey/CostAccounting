import sqlite3
import sys

from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableWidgetItem
from PyQt5.QtWidgets import QWidget, QPushButton, QVBoxLayout
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt
import random


class GraphWidget(QWidget):
    def __init__(self, parent=None):
        super(GraphWidget, self).__init__(parent)

        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.button = QPushButton('Plot')
        self.button.clicked.connect(self.plot)

        layout = QVBoxLayout()
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        layout.addWidget(self.button)

        self.setLayout(layout)

    def plot(self):
        data = [random.random() for i in range(10)]
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.plot(data, '*-')
        self.canvas.draw()


class AddRecordWidget(QWidget):
    pass


class LoginWidget(QWidget):
    pass


class Registration:
    pass


class Window(QMainWindow):
    def __init__(self):
        super(QMainWindow, self).__init__()

        self.con = sqlite3.connect("Cost.db")
        cur = self.con.cursor()

        self.title = ["ID", "Категория", "Дата", "Цена"]
        self.table = cur.execute("SELECT UserId, CategoryId, Date, SumCost FROM Cost").fetchall()

        uic.loadUi("ui.ui", self)

        self.setWindowTitle("Учет расходов")

        self.tableWidget.setRowCount(len(self.table))
        self.tableWidget.setColumnCount(len(self.title))
        self.tableWidget.setHorizontalHeaderLabels(self.title)

        self.graph = GraphWidget(self.centralWidget())
        self.graph.setGeometry(440, 10, 751, 771)

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
