import sqlite3
import sys

from widgets import AddNoteDialog, EditDialog, SignInDialog, SignUpDialog, GraphWidget
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableWidgetItem, QMessageBox, \
    QAbstractItemView
from PyQt5 import uic


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


# класс приложения
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

        self.sign_in.triggered.connect(self.signIn)
        self.sign_up.triggered.connect(self.signUp)
        self.action_exit.triggered.connect(self.logOut)

        self.tableWidget.horizontalHeader().sectionClicked.connect(self.sort)

    def __del__(self):
        self.logOut()
        self.con.close()

    # метод для получения данных в таблицу из базы данных
    def getDataFromDb(self):
        # проверка на то, что пользователь вошел в аккаунт
        if self.getUserId():
            # получаем из базы данных все записи пользователя
            cur = self.con.cursor()
            result = cur.execute(f'''SELECT Title, Date, SumCost FROM Cost INNER JOIN Category ON 
    Cost.CategoryId = Category.CategoryId WHERE UserId = {self.getUserId()}''').fetchall()
            cur.close()

            return result
        else:
            return []

    # метод для присваивания таблицы новых значений
    def setTable(self, new_table):
        self.table = new_table

    # метод для присваивания id пользователя
    def setUserId(self, user_id):
        self.user_id = user_id

    # метод для получения таблицы данных
    def getTable(self):
        return self.table

    # метод для получения id пользователя
    def getUserId(self):
        return self.user_id

    # метод для отображения таблицы в виджете
    def showNotes(self):
        self.tableWidget.setRowCount(len(self.getTable()))

        for i, row in enumerate(self.getTable()):
            for j, value in enumerate(row):
                # меняем формат представления даты
                if j == 1:
                    value = '.'.join(value.split('-')[::-1])

                # создаем ячейку
                item = QTableWidgetItem(str(value))

                # устанавливаем ячейки
                self.tableWidget.setItem(i, j, item)
        self.tableWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)

    # метод для добавления новой записи
    def add(self):
        # проверка на то, что пользователь еще не вошел в аккаунт
        if self.statusBarChange("Войдите в аккаунт, чтобы добавить запись",
                                self.getUserId() is None):
            return

        new_note_form = AddNoteDialog(self.getUserId(), "", "", "", self)
        new_note_form.exec_()

        # отображаем новую таблицу
        self.setTable(self.getDataFromDb())
        self.showNotes()

    # метод дял удаления записей
    def remove(self):
        # проверка на то, что пользователь еще не вошел в аккаунт
        if self.statusBarChange("Войдите в аккаунт, чтобы удалить запись", self.getUserId() is None):
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
                                    in sorted(list(set(map(lambda i: i.row(),
                                                           selected_items)))))
                          + '?', QMessageBox.Yes, QMessageBox.No)

            # если да, то удаляем записи из базы данных
            if valid == QMessageBox.Yes:
                cur = self.con.cursor()

                for selected_item in selected_items:
                    # получаем данные из выбранной ячейки
                    category, date, cost = self.getTable()[selected_item.row()]
                    # получаем id категории выбранной ячейки
                    category = cur.execute(f'''SELECT CategoryId FROM Category 
    WHERE Title = "{category}"''').fetchone()[0]
                    # удаляем запись соответствующую выбранной ячейки
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

                self.graph.updateDateEdit()

                # отображаем новую таблицу
                self.setTable(self.getDataFromDb())
                self.showNotes()
        else:
            return

    # метод для редактирования записи
    def edit(self):
        # проверка на то, что пользователь еще не вошел в аккаунт
        if self.statusBarChange("Войдите в аккаунт, чтобы изменить запись",
                                self.getUserId() is None):
            return

        # получаем выбранную ячейку в таблице
        selected_item = self.tableWidget.selectedItems()

        # проверка на то, что выбрана одна ячейка
        if self.statusBarChange("Должна быть выбрана одна запись", len(selected_item) != 1):
            return

        # получаем данные из выбранной ячейки
        row = selected_item[0].row()
        category, date, cost = self.getTable()[row]

        edit_form = EditDialog(self.getUserId(), category, date, cost, row, self)
        edit_form.exec_()

        # отображаем новую таблицу
        self.setTable(self.getDataFromDb())
        self.showNotes()

    # метод для сортировки записей в таблице
    def sort(self, index):
        # проверка на то, что пользователь еще не вошел в аккаунт
        if self.statusBarChange("Войдите в аккаунт, для сортировки записей",
                                self.getUserId() is None):
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

    # метод для входа в аккаунт
    def signIn(self):
        # проверка на то, что пользователь уже вошел в аккаунт
        if self.statusBarChange("Выйдите из аккаунта, чтобы войти в другой аккаунт",
                                self.getUserId()):
            return

        sign_in_form = SignInDialog(self)
        sign_in_form.exec_()

        # если пользователь вошел в аккаунт
        if self.getUserId():
            # показываем виджет графика
            self.graph = GraphWidget(self.getUserId(), self.graph_widget)
            self.graph.show()

            # присваеваим таблицу с значениями из базы данных
            self.setTable(self.getDataFromDb())
            # отображаем новую таблицу
            self.showNotes()

    # метод для регистрации нового аккаунта
    def signUp(self):
        # проверка на то, что пользователь уже вошел в аккаунт
        if self.statusBarChange("Выйдите из аккаунта, чтобы зарегистрироваться", self.getUserId()):
            return

        sign_up_form = SignUpDialog(self)
        sign_up_form.exec_()

        # если пользователь зарегистрировался
        if self.getUserId():
            # показываем виджет графика
            self.graph = GraphWidget(self.getUserId(), self.graph_widget)
            self.graph.show()

            # очищаем таблицы
            self.setTable([])

            # отображаем таблицу
            self.showNotes()

    # метод для выхода из аккаунта
    def logOut(self):
        # проверка на то, что пользователь еще не вошел в аккаунт
        if self.statusBarChange("Нельзя выйти, так как вы не вошли в аккаунт",
                                self.getUserId() is None):
            return

        # очищаем виджет графика и скрываем его
        self.graph.hide()
        self.graph = None

        # очищаем таблицы
        self.setTable([])

        # отображаем новую таблицу
        self.showNotes()

        self.setUserId(None)

    # метод для отображения ошибок в статус баре
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
