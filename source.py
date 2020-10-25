import sys

from widgets import *
from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableWidgetItem


class Window(QMainWindow):
    def __init__(self):
        super(QMainWindow, self).__init__()

        self.user_id = 1

        self.con = sqlite3.connect("Cost.db")

        self.title = ["Категория", "Дата", "Цена"]
        self.table = self.getCostData()

        uic.loadUi("main_window.ui", self)

        self.setWindowTitle("Учет расходов")

        # self.graph = GraphWidget(self.centralWidget())
        # self.graph.setGeometry(440, 10, 751, 771)

        self.showNotes()

        self.button_add.clicked.connect(self.add)
        self.button_remove.clicked.connect(self.remove)
        self.button_edit.clicked.connect(self.edit)

    def getCostData(self):
        cur = self.con.cursor()
        result = cur.execute(f'''SELECT Title, Date, SumCost FROM Cost INNER JOIN Category ON 
Cost.CategoryId = Category.CategoryId WHERE UserId = {self.user_id}''').fetchall()
        cur.close()

        return result

    def showNotes(self):
        self.tableWidget.setRowCount(len(self.table))
        self.tableWidget.setColumnCount(len(self.title))
        self.tableWidget.setHorizontalHeaderLabels(self.title)

        for i, row in enumerate(self.table):
            for j, value in enumerate(row):
                self.tableWidget.setItem(i, j, QTableWidgetItem(str(value)))

    def sort(self):
        pass

    def add(self):
        new_note_form = NoteWindow(self.user_id, self)
        new_note_form.exec_()

        self.table = self.getCostData()
        self.showNotes()

    def remove(self):
        pass

    def edit(self):
        pass


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main = Window()
    main.show()
    sys.exit(app.exec_())
