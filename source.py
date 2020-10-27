import sys

from widgets import *
from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableWidgetItem


class Window(QMainWindow):
    def __init__(self):
        super(QMainWindow, self).__init__()

        self.user_id = None

        self.con = sqlite3.connect("Cost.db")

        self.title = ["Категория", "Дата", "Цена"]
        self.table = self.getCostData()

        uic.loadUi("ui/main_window.ui", self)

        self.setWindowTitle("Учет расходов")
        self.tableWidget.setColumnCount(len(self.title))
        self.tableWidget.setHorizontalHeaderLabels(self.title)

        # self.graph = GraphWidget(self.centralWidget())
        # self.graph.setGeometry(440, 10, 751, 771)

        self.showNotes()

        self.operation_add.triggered.connect(self.add)
        self.operation_edit.triggered.connect(self.edit)
        self.operation_remove.triggered.connect(self.remove)

        self.sort_by_category.triggered.connect(self.sortByCategories)
        self.sort_by_date.triggered.connect(self.sortByDates)
        self.sort_by_cost.triggered.connect(self.sortByCosts)

        self.filter_by_categories.triggered.connect(self.filterByCategories)
        self.filter_by_dates.triggered.connect(self.filterByDates)
        self.filter_by_costs.triggered.connect(self.filterByCosts)

        self.sign_in.triggered.connect(self.signIn)
        self.sign_up.triggered.connect(self.signUp)

        self.button_exit.clicked.connect(self.exit)

    def getCostData(self):
        if self.user_id:
            cur = self.con.cursor()
            result = cur.execute(f'''SELECT Title, Date, SumCost FROM Cost INNER JOIN Category ON 
    Cost.CategoryId = Category.CategoryId WHERE UserId = {self.user_id}''').fetchall()
            cur.close()

            return result
        else:
            return []

    def showNotes(self):
        if self.user_id:
            self.tableWidget.setRowCount(len(self.table))

            for i, row in enumerate(self.table):
                for j, value in enumerate(row):
                    self.tableWidget.setItem(i, j, QTableWidgetItem(str(value)))

    def add(self):
        self.statusBarChange()

        new_note_form = NoteWindow(self.user_id, self)
        new_note_form.exec_()

        self.table = self.getCostData()
        self.showNotes()

    def remove(self):
        self.statusBarChange()

    def edit(self):
        self.statusBarChange()

    def filterByCategories(self):
        self.statusBarChange()

    def filterByDates(self):
        self.statusBarChange()

    def filterByCosts(self):
        self.statusBarChange()

    def sortByCategories(self):
        self.statusBarChange()

    def sortByDates(self):
        self.statusBarChange()

    def sortByCosts(self):
        self.statusBarChange()

    def signIn(self):
        sign_in_form = SignInWindow(self)
        sign_in_form.exec_()

        self.table = self.getCostData()
        self.showNotes()

    def signUp(self):
        self.statusBarChange()

        sign_up_form = SignUpWindow(self)
        sign_up_form.exec_()

        self.table.clear()
        self.showNotes()

    def exit(self):

        self.table.clear()
        self.showNotes()

        self.user_id = None

    def statusBarChange(self):
        if self.user_id is None:
            self.statusBar().showMessage("Нельзя выйти, так как вы еще не вошли ни в один аккаунт")
            self.statusbar.setStyleSheet("background-color:red")
            return
        else:
            self.statusBar().setStyleSheet("background-color:white")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main = Window()
    main.show()
    sys.exit(app.exec_())
