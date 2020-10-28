import sys

from widgets import *
from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableWidgetItem, QMessageBox


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
        self.action_exit.triggered.connect(self.exit)

    def __del__(self):
        self.con.close()

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
        self.statusBarChange("Войдите в аккаунт, чтобы добавить запись", self.user_id is None)

        new_note_form = NoteWindow(self.user_id, self)
        new_note_form.exec_()

        self.table = self.getCostData()
        self.showNotes()

    def remove(self):
        self.statusBarChange("Войдите в аккаунт, чтобы удалить запись", self.user_id is None)
        self.statusBarChange("Должна быть хотя бы одна запись", not len(self.table))

        rows = self.tableWidget.selectedItems()

        if rows:
            valid = QMessageBox.question(
                self, '', "Действительно удалить записи с номерами " +
                          ", ".join(str(i.row() + 1) for i in rows) + '?',
                QMessageBox.Yes, QMessageBox.No)

            if valid == QMessageBox.Yes:
                cur = self.con.cursor()

                for row in rows:
                    category, date, cost = self.table[row.row()]
                    category = cur.execute(f'''SELECT CategoryId FROM Category 
    WHERE Title = "{category}"''').fetchone()[0]
                    cur.execute(f'''DELETE FROM Cost 
    WHERE CategoryId={category} AND Date="{date}" AND SumCost={cost}''')

                self.statusBar().showMessage("Записи с номерами "
                                             + ", ".join(str(row.row() + 1) for row in rows)
                                             + " успешно удалены")

                cur.close()
                self.con.commit()

                self.table = self.getCostData()
                self.showNotes()

    def edit(self):
        self.statusBarChange("Войдите в аккаунт, чтобы изменить запись", self.user_id is None)
        self.statusBarChange("Должна быть хотя бы одна запись", not len(self.table))
        pass

    def filterByCategories(self):
        pass

    def filterByDates(self):
        pass

    def filterByCosts(self):
        pass

    def sortByCategories(self):
        self.statusBarChange("Войдите в аккаунт, чтобы отсортировать записи", self.user_id is None)
        self.statusBarChange("Записей должно быть больше одной", len(self.table) <= 1)

        self.table.sort(key=lambda note: note[0])
        self.showNotes()

    def sortByDates(self):
        self.statusBarChange("Войдите в аккаунт, чтобы отсортировать записи", self.user_id is None)
        self.statusBarChange("Записей должно быть больше одной", len(self.table) <= 1)

        self.table.sort(key=lambda note: note[1])
        self.showNotes()

    def sortByCosts(self):
        self.statusBarChange("Войдите в аккаунт, чтобы отсортировать записи", self.user_id is None)
        self.statusBarChange("Записей должно быть больше одной", len(self.table) <= 1)

        self.table.sort(key=lambda note: note[2])
        self.showNotes()

    def signIn(self):
        self.statusBarChange("Выйдите из аккаунта, чтобы войти в другой аккаунт", self.user_id)

        sign_in_form = SignInWindow(self)
        sign_in_form.exec_()

        self.table = self.getCostData()
        self.showNotes()

    def signUp(self):
        self.statusBarChange("Выйдите из аккаунта, чтобы зарегистрироваться", self.user_id)

        sign_up_form = SignUpWindow(self)
        sign_up_form.exec_()

        self.table.clear()
        self.showNotes()

    def exit(self):
        self.statusBarChange("Нельзя выйти, так как вы не вошли в аккаунт", self.user_id is None)

        self.table.clear()
        self.showNotes()

        self.user_id = None

    def statusBarChange(self, message, condition):
        if condition:
            self.statusBar().showMessage(message)
            self.statusbar.setStyleSheet("background-color:red")
            return
        else:
            self.statusBar().setStyleSheet("background-color:white")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main = Window()
    main.show()
    sys.exit(app.exec_())
