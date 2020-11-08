import sqlite3
import sys

from widgets import AddNoteDialog, EditDialog, CategoryFilterDialog, DateFilterDialog, \
    CostFilterDialog, SignInDialog, SignUpDialog, GraphWidget
from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableWidgetItem, QMessageBox


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


class Window(QMainWindow):
    def __init__(self):
        super(QMainWindow, self).__init__()

        self.user_id = None

        self.con = sqlite3.connect("Cost.db")

        self.title = ["Категория", "Дата", "Цена"]
        self.table = self.getTable()

        uic.loadUi("ui/main_window.ui", self)

        self.graph = GraphWidget(self.graph_widget)
        self.graph.hide()

        self.setWindowTitle("Учет расходов")
        self.tableWidget.setColumnCount(len(self.title))
        self.tableWidget.setHorizontalHeaderLabels(self.title)

        self.showNotes()

        self.operation_add.triggered.connect(self.add)
        self.operation_edit.triggered.connect(self.edit)
        self.operation_remove.triggered.connect(self.remove)

        self.filter_by_categories.triggered.connect(self.filterByCategories)
        self.filter_by_dates.triggered.connect(self.filterByDates)
        self.filter_by_costs.triggered.connect(self.filterByCosts)

        self.sign_in.triggered.connect(self.signIn)
        self.sign_up.triggered.connect(self.signUp)
        self.action_exit.triggered.connect(self.exit)

        self.tableWidget.horizontalHeader().sectionClicked.connect(self.sort)

    def __del__(self):
        self.con.close()

    def getTable(self):
        if self.user_id:
            cur = self.con.cursor()
            result = cur.execute(f'''SELECT Title, Date, SumCost FROM Cost INNER JOIN Category ON 
    Cost.CategoryId = Category.CategoryId WHERE UserId = {self.user_id}''').fetchall()
            cur.close()

            return result
        else:
            return []

    def setTable(self, new_table):
        self.table = new_table

    def showNotes(self):
        if self.user_id:
            self.tableWidget.setRowCount(len(self.table))

            for i, row in enumerate(self.table):
                for j, value in enumerate(row):
                    if j == 1:
                        value = '.'.join(value.split('-')[::-1])
                    self.tableWidget.setItem(i, j, QTableWidgetItem(str(value)))

    def add(self):
        if self.statusBarChange("Войдите в аккаунт, чтобы добавить запись", self.user_id is None):
            return

        new_note_form = AddNoteDialog(self.user_id, "", "", "", self)
        new_note_form.exec_()

        self.table = self.getTable()
        self.showNotes()

    def remove(self):
        if self.statusBarChange("Войдите в аккаунт, чтобы удалить запись", self.user_id is None):
            return
        if self.statusBarChange("Должна быть хотя бы одна запись", not len(self.table)):
            return

        rows = self.tableWidget.selectedItems()

        if rows:
            valid = QMessageBox.question(
                self, '', "Действительно удалить записи с номерами " +
                          ", ".join(str(row + 1) for row in sorted(list(set(map(lambda i: i.row(),
                                                                                rows))))) + '?',
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
                                             + ", ".join(str(row + 1) for row in
                                                         sorted(list(set(map(lambda i: i.row(),
                                                                             rows)))))
                                             + " успешно удалены")

                cur.close()
                self.con.commit()

                self.table = self.getTable()
                self.showNotes()

    def edit(self):
        if self.statusBarChange("Войдите в аккаунт, чтобы изменить запись", self.user_id is None):
            return

        selected_item = self.tableWidget.selectedItems()

        if self.statusBarChange("Должна быть выбрана одна запись", len(selected_item) != 1):
            return

        category, date, cost = self.table[selected_item[0].row()]

        edit_form = EditDialog(self.user_id, category, date, cost, self)
        edit_form.exec_()

        self.table = self.getTable()
        self.showNotes()

    def filterByCategories(self):
        if self.filter_by_categories.isChecked():
            if self.statusBarChange("Войдите в аккаунт, чтобы отфильтровать записи",
                                    self.user_id is None):
                return
            if self.statusBarChange("Должна быть хотя бы одна запись", not len(self.table)):
                return

            categories = sorted(list(set(map(lambda x: x[0], self.table))))

            filter_form = CategoryFilterDialog(self.user_id, self.table, categories, parent=self)
            filter_form.exec_()

            self.showNotes()
        else:
            self.table = self.getTable()

    def filterByDates(self):
        if self.filter_by_dates.isChecked():
            if self.statusBarChange("Войдите в аккаунт, чтобы отфильтровать записи",
                                    self.user_id is None):
                return
            if self.statusBarChange("Должна быть хотя бы одна запись", not len(self.table)):
                return

            dates = sorted(list(set(map(lambda x: x[1], self.table))))

            filter_form = DateFilterDialog(self.user_id, self.table, dates, parent=self)
            filter_form.exec_()

            self.showNotes()
        else:
            self.table = self.getTable()

    def filterByCosts(self):
        if self.filter_by_costs.isChecked():
            if self.statusBarChange("Войдите в аккаунт, чтобы отфильтровать записи",
                                    self.user_id is None):
                return
            if self.statusBarChange("Должна быть хотя бы одна запись", not len(self.table)):
                return

            costs = sorted(list(set(map(lambda x: x[2], self.table))))

            filter_form = CostFilterDialog(self.user_id, self.table, costs, parent=self)
            filter_form.exec_()

            self.showNotes()
        else:
            self.table = self.getTable()

    def sort(self, index):
        if self.statusBarChange("Войдите в аккаунт, для сортировки записей", self.user_id is None):
            return
        if self.statusBarChange("Записей должно быть больше одной", len(self.table) <= 1):
            return

        self.tableWidget.horizontalHeader().setSortIndicatorShown(True)
        if not self.tableWidget.horizontalHeader().sortIndicatorOrder():
            self.table.sort(key=lambda note: note[index])
        else:
            self.table.sort(key=lambda note: note[index], reverse=True)
        self.showNotes()

    def signIn(self):
        if self.statusBarChange("Выйдите из аккаунта, чтобы войти в другой аккаунт", self.user_id):
            return

        sign_in_form = SignInDialog(self)
        sign_in_form.exec_()

        self.showGraph()

        self.table = self.getTable()
        self.showNotes()

    def signUp(self):
        if self.statusBarChange("Выйдите из аккаунта, чтобы зарегистрироваться", self.user_id):
            return

        sign_up_form = SignUpDialog(self)
        sign_up_form.exec_()

        self.showGraph()

        self.table.clear()
        self.showNotes()

    def exit(self):
        if self.statusBarChange("Нельзя выйти, так как вы не вошли в аккаунт", self.user_id is None):
            return

        self.graph.clear()
        self.graph.hide()

        self.table.clear()
        self.showNotes()

        self.user_id = None

    def showGraph(self):
        if self.user_id:
            self.graph.set_id(self.user_id)
            self.graph.show()

    def statusBarChange(self, message, condition):
        if condition:
            self.statusBar().showMessage(message)
            self.statusbar.setStyleSheet("background-color:red")
            self.statusbar.setStyleSheet("background-color:red")
            return 1
        else:
            self.statusBar().setStyleSheet("background-color:white")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main = Window()
    main.show()
    sys.excepthook = except_hook
    sys.exit(app.exec_())
