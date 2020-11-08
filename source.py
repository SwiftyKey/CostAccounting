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
        self.table = []

        uic.loadUi("ui/main_window.ui", self)

        self.graph = None

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
        self.action_exit.triggered.connect(self.logOut)

        self.tableWidget.horizontalHeader().sectionClicked.connect(self.sort)

    def __del__(self):
        self.con.close()

    # функция для получения данных в таблицу из базы данных
    def getDataFromDb(self):
        # проверка на то, что пользователь вошел в аккаунт
        if self.user_id:
            cur = self.con.cursor()
            result = cur.execute(f'''SELECT Title, Date, SumCost FROM Cost INNER JOIN Category ON 
    Cost.CategoryId = Category.CategoryId WHERE UserId = {self.user_id}''').fetchall()
            cur.close()

            return result
        else:
            return []

    # функция для присваивания таблицы новых значений
    def setTable(self, new_table):
        self.table = new_table

    # функция для отображения таблицы в виджете
    def showNotes(self):
        self.tableWidget.setRowCount(len(self.table))

        for i, row in enumerate(self.table):
            for j, value in enumerate(row):
                # меняем формат представления даты
                if j == 1:
                    value = '.'.join(value.split('-')[::-1])
                self.tableWidget.setItem(i, j, QTableWidgetItem(str(value)))

    # функция для добавления новой записи
    def add(self):
        # проверка на то, что пользователь еще не вошел в аккаунт
        if self.statusBarChange("Войдите в аккаунт, чтобы добавить запись", self.user_id is None):
            return

        new_note_form = AddNoteDialog(self.user_id, "", "", "", self)
        new_note_form.exec_()

        # присваеваим таблицу с удаленными значениями
        self.setTable(self.getDataFromDb())
        # отображаем новую таблицу
        self.showNotes()

    # функция дял удаления записей
    def remove(self):
        # проверка на то, что пользователь еще не вошел в аккаунт
        if self.statusBarChange("Войдите в аккаунт, чтобы удалить запись", self.user_id is None):
            return
        # проверка на то, что выбрано не меньше одной записи
        if self.statusBarChange("Должна быть хотя бы одна запись", not len(self.table)):
            return

        # получаем выбранные ячейки в таблице
        selected_items = self.tableWidget.selectedItems()

        # если есть выбранные ячейки
        if not self.statusBarChange("Должна быть хотя бы одна запись", not selected_items):
            # создаем диалог для пользователя с проверкой, что он действительно хочет удалить записи
            valid = QMessageBox.question(
                self, '', "Действительно удалить записи с номерами " +
                          ", ".join(str(selected_item + 1) for selected_item
                                    in sorted(list(set(map(lambda i: i.selected_item(),
                                                           selected_items)))))
                          + '?', QMessageBox.Yes, QMessageBox.No)

            # если да, то удаляем записи из базы данных
            if valid == QMessageBox.Yes:
                cur = self.con.cursor()

                for selected_item in selected_items:
                    # получаем данные из выбранной ячейки
                    category, date, cost = self.table[selected_item.row()]
                    category = cur.execute(f'''SELECT CategoryId FROM Category 
    WHERE Title = "{category}"''').fetchone()[0]
                    cur.execute(f'''DELETE FROM Cost 
    WHERE CategoryId={category} AND Date="{date}" AND SumCost={cost}''')

                # говорим пользователю, что все успешно удалилось
                self.statusBar().showMessage("Записи с номерами "
                                             + ", ".join(str(selected_item + 1) for selected_item in
                                                         sorted(list(set(map(lambda i: i.row(),
                                                                             selected_items)))))
                                             + " успешно удалены")

                cur.close()
                self.con.commit()

                # присваеваим таблицу с удаленными значениями
                self.setTable(self.getDataFromDb())
                # отображаем новую таблицу
                self.showNotes()
        else:
            return

    # функция для редактирования записи
    def edit(self):
        # проверка на то, что пользователь еще не вошел в аккаунт
        if self.statusBarChange("Войдите в аккаунт, чтобы изменить запись", self.user_id is None):
            return

        # получаем выбранную ячейку в таблице
        selected_item = self.tableWidget.selectedItems()

        # проверка на то, что выбрана одна ячейка
        if self.statusBarChange("Должна быть выбрана одна запись", len(selected_item) != 1):
            return

        # получаем данные из выбранной ячейки
        category, date, cost = self.table[selected_item[0].row()]

        edit_form = EditDialog(self.user_id, category, date, cost, self)
        edit_form.exec_()

        # присваеваим таблицу с удаленными значениями
        self.setTable(self.getDataFromDb())
        # отображаем новую таблицу
        self.showNotes()

    # функция для фильтрации по категориям
    def filterByCategories(self):
        # если пользователь нажал на фильтр, и он не был еще применен
        if self.filter_by_categories.isChecked():
            # проверка на то, что пользователь еще не вошел в аккаунт
            if self.statusBarChange("Войдите в аккаунт, чтобы отфильтровать записи",
                                    self.user_id is None):
                return
            # проверка на то, что записей в таблице не меньше одной
            if self.statusBarChange("Должна быть хотя бы одна запись", not len(self.table)):
                return

            # получаем все категории, которые выбирал пользователь
            categories = sorted(list(set(map(lambda x: x[0], self.table))))

            filter_form = CategoryFilterDialog(self.user_id, self.table, categories, parent=self)
            filter_form.exec_()

            # отображаем новую таблицу
            self.showNotes()
        else:
            self.setTable(self.getDataFromDb())

    # функция для фильтрации по датам
    def filterByDates(self):
        # если пользователь нажал на фильтр, и он не был еще применен
        if self.filter_by_dates.isChecked():
            # проверка на то, что пользователь еще не вошел в аккаунт
            if self.statusBarChange("Войдите в аккаунт, чтобы отфильтровать записи",
                                    self.user_id is None):
                return
            # проверка на то, что записей в таблице не меньше одной
            if self.statusBarChange("Должна быть хотя бы одна запись", not len(self.table)):
                return

            # получаем все даты, которые выбирал пользователь
            dates = sorted(list(set(map(lambda x: x[1], self.table))))

            filter_form = DateFilterDialog(self.user_id, self.table, dates, parent=self)
            filter_form.exec_()

            # отображаем новую таблицу
            self.showNotes()
        else:
            self.setTable(self.getDataFromDb())

    # функция для фильтрации по ценам
    def filterByCosts(self):
        # если пользователь нажал на фильтр, и он не был еще применен
        if self.filter_by_costs.isChecked():
            # проверка на то, что пользователь еще не вошел в аккаунт
            if self.statusBarChange("Войдите в аккаунт, чтобы отфильтровать записи",
                                    self.user_id is None):
                return
            # проверка на то, что записей в таблице не меньше одной
            if self.statusBarChange("Должна быть хотя бы одна запись", not len(self.table)):
                return

            # получаем все цены, которые выбирал пользователь
            costs = sorted(list(set(map(lambda x: x[2], self.table))))

            filter_form = CostFilterDialog(self.user_id, self.table, costs, parent=self)
            filter_form.exec_()

            # отображаем новую таблицу
            self.showNotes()
        else:
            self.setTable(self.getDataFromDb())

    # функция для сортировки записей в таблице
    def sort(self, index):
        # проверка на то, что пользователь еще не вошел в аккаунт
        if self.statusBarChange("Войдите в аккаунт, для сортировки записей", self.user_id is None):
            return
        # проверка на то, что записей больше одной
        if self.statusBarChange("Записей должно быть больше одной", len(self.table) <= 1):
            return

        # устанавливаем индикатор сортировки
        self.tableWidget.horizontalHeader().setSortIndicatorShown(True)
        # сортируем данные по возрастнаю, если индиктор направлен по возрастанию
        if not self.tableWidget.horizontalHeader().sortIndicatorOrder():
            self.table.sort(key=lambda note: note[index])
        # иначе по убыванию
        else:
            self.table.sort(key=lambda note: note[index], reverse=True)

        # отображаем новую таблицу
        self.showNotes()

    # функция для входа в аккаунт
    def signIn(self):
        # проверка на то, что пользователь уже вошел в аккаунт
        if self.statusBarChange("Выйдите из аккаунта, чтобы войти в другой аккаунт", self.user_id):
            return

        sign_in_form = SignInDialog(self)
        sign_in_form.exec_()

        # показываем виджет графика
        self.graph = GraphWidget(self.graph_widget)
        self.graph.show()

        # присваеваим таблицу с удаленными значениями
        self.setTable(self.getDataFromDb())
        # отображаем новую таблицу
        self.showNotes()

    # функция для регистрации нового аккаунта
    def signUp(self):
        # проверка на то, что пользователь уже вошел в аккаунт
        if self.statusBarChange("Выйдите из аккаунта, чтобы зарегистрироваться", self.user_id):
            return

        sign_up_form = SignUpDialog(self)
        sign_up_form.exec_()

        # показываем виджет графика
        self.graph = GraphWidget(self.graph_widget)
        self.graph.show()

        # очищаем таблицу
        self.table.clear()
        # отображаем новую таблицу
        self.showNotes()

    # функция для выхода из аккаунта
    def logOut(self):
        # проверка на то, что пользователь еще не вошел в аккаунт
        if self.statusBarChange("Нельзя выйти, так как вы не вошли в аккаунт", self.user_id is None):
            return

        # очищаем виджет графика и скрываем его
        self.graph.clear()
        self.graph.hide()

        # очищаем таблицу
        self.table.clear()
        # отображаем новую таблицу
        self.showNotes()

        self.user_id = None

    # функция для отображения ошибок в статус баре
    def statusBarChange(self, message, condition):
        if condition:
            # отображаем ошибку в статус баре
            self.statusBar().showMessage(message)
            # изменяем цвет статус бара
            self.statusbar.setStyleSheet("background-color:red")
            return 1
        else:
            # изменяем цвет статус бара
            self.statusBar().setStyleSheet("background-color:white")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main = Window()
    main.show()
    sys.excepthook = except_hook
    sys.exit(app.exec_())
