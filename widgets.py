import sqlite3
import uuid
import hashlib
import graph_widget

from PyQt5 import uic, QtGui
from PyQt5.QtCore import QDate, Qt
from PyQt5.QtWidgets import QDialog, QInputDialog, QListWidgetItem

# Глобальная переменная для хранения минимальной длины пароля
LENGTH = 9
# Глобальная переменная для хранения запрещенных последовательностей
# из 3 символов по рядам на клавиатуре
SEQUENCES = ("qwertyuiop", "asdfghjkl", "zxcvbnm", "йцукенгшщзхъ", "фывапролджэё", "ячсмитьбю")
# Глобальная переменная для хранения цифр
DIGITS = "0123456789"


# функция для изменения обводки виджета при ошибки
def change_border(widget, color):
    widget.setFont(QtGui.QFont('Times', 14))
    widget.setStyleSheet(f'''border-style: solid; border-width: 1px; border-color: {color};''')


# функция для шифрования пароля
def hash_password(password):
    # uuid используется для генерации случайного числа - salt
    salt = uuid.uuid4().hex
    return hashlib.sha256(salt.encode() + password.encode()).hexdigest() + ':' + salt


# функция для сравнения введенного пароля пользователем и пароля в базе данных
def checkPassword(hashed_password, user_password):
    password, salt = hashed_password.split(':')
    return password == hashlib.sha256(salt.encode() + user_password.encode()).hexdigest()


# родительский класс исключание, связанный с неправильным логином
class LoginError(Exception):
    pass


# родительский класс исключение, связанное с неправильным паролем
class PasswordError(Exception):
    pass


# класс исключения, связанный с неправильной длиной пароля
class LengthError(PasswordError):
    pass


# класс исключения, связанный с отсутствием разных регистров символов в пароле
class LetterError(PasswordError):
    pass


# класс исключения, связанный с отсутствием цифры в пароле
class DigitError(PasswordError):
    pass


# класс исключения, связанный с присутствием запрещенной последовательности в пароле
class SequenceError(PasswordError):
    pass


# класс для проверки пароля на правильность
class IsCorrectPassword:
    def __init__(self, password: str):
        self.password = password

    # метод для проверки длины пароля
    def isValidLength(self):
        return len(self.password) > LENGTH

    # метод для проверки на наличие разных регистров символов в пароле
    def isValidRegisters(self):
        return self.password != self.password.lower() and self.password != self.password.upper()

    # метод для проверки на наличие цифры в пароле
    def containsDigit(self):
        for digit in DIGITS:
            if digit in self.password:
                return True
        return False

    # метод для проверки на отсутствие в пароле запрещенных последовательностей
    def isValidSequences(self):
        for index, sym in enumerate(self.password):
            for sequence in SEQUENCES:
                # если символ есть в одной из запрещенных последовательностей
                if sym.lower() in sequence:
                    sym_index = sequence.index(sym.lower())
                    # если символ не стоит в последовательности и в пароле на последних двух позициях
                    if sym_index < len(sequence) - 2 and index < len(self.password) - 2:
                        # если последующие два символа входят в запрещенную последовательность
                        if (self.password[index + 1].lower(), self.password[index + 2].lower()) \
                                == (sequence[sym_index + 1], sequence[sym_index + 2]):
                            return False
                    break

        return True

    # метод для проверки пароля на корректность
    def checkPassword(self):
        if not self.isValidLength():
            raise LengthError(f"Длина пароля <= {LENGTH}")
        if not self.isValidRegisters():
            raise LetterError("В пароле символы одного регистра")
        if not self.containsDigit():
            raise DigitError("В пароле не содержится цифра")
        if not self.isValidSequences():
            raise SequenceError("В пароле есть последовательность из символов на клавиатуре")

        return True


# родительский класс для операций добавления и изменения записей
class OperationsDialog(QDialog):
    def __init__(self, user_id, category, date, cost, filename, title, parent=None):
        super(OperationsDialog, self).__init__(parent)

        self.con = sqlite3.connect("Cost.db")

        self.user_id = user_id
        self.category = category
        self.date = date
        self.cost = cost

        # загружаем ui диалога
        self.loadUI(filename, title)

        # добавление категорий в combo box
        cur = self.con.cursor()
        categories = map(lambda item: item[0], cur.execute("SELECT Title FROM Category").fetchall())
        self.select_category.addItems(categories)

        # настройка double spin box'а
        self.select_cost.setSingleStep(0.01)
        self.select_cost.setRange(0.01, 10e9)

        self.select_date.setDate(QDate.currentDate())

        self.button_create_category.clicked.connect(self.newCategory)
        self.button_exit.clicked.connect(self.exit)

    # метод для отображения ui диалога
    def loadUI(self, filename, title):
        uic.loadUi(filename, self)
        self.setWindowTitle(title)

    # метод для добавления новой категории
    def newCategory(self):
        # создаем диалог ввода названия новой категории
        title = QInputDialog.getText(self, "Новая категория",
                                     "Введите название новой категории")
        # если ввод не пустой и не отменен
        if title[0] and title[1]:
            # добавляем новую категорию в базу данных
            cur = self.con.cursor()
            cur.execute(f"INSERT INTO Category(Title) VALUES('{title[0]}')")
            cur.close()
            self.con.commit()

            # обновляем список категорий для виджета графика
            self.parent().graph.updateListCategories()

            # добавляем новую категорию в combo box и делаем его текущим
            self.select_category.insertItem(0, title[0])
            self.select_category.setCurrentIndex(0)

    # метод для отмены добавления или изменения записи
    def exit(self):
        self.con.close()
        self.close()


# класс предок добавления новой записи
class AddNoteDialog(OperationsDialog):
    def __init__(self, user_id, category, date, cost, parent=None):
        super(AddNoteDialog, self).__init__(user_id, category, date, cost,
                                            "ui/add_note_dialog.ui", "Новая запись", parent)

        self.button_add.clicked.connect(self.addNote)

    # метод для добавления записи
    def addNote(self):
        cur = self.con.cursor()
        # получаем id категории из базы данных
        self.category = cur.execute(f'''SELECT CategoryId FROM Category 
WHERE Title = "{self.select_category.currentText()}"''').fetchone()[0]
        self.date = self.select_date.date().toString("yyyy-MM-dd")
        self.cost = self.select_cost.value()

        # добавляем новую запись в базу данных
        cur.execute(f'''INSERT INTO Cost(UserId, CategoryId, Date, SumCost) 
VALUES({self.user_id}, {self.category}, "{self.date}", {self.cost})''')
        cur.close()
        self.con.commit()
        # добавляем запись в таблицу
        self.parent().setTable(self.parent().getTable() + [(self.select_category.currentText(),
                                                            self.date, int(self.cost)
                                                            if self.cost.is_integer()
                                                            else self.cost)])

        self.parent().graph.updateDateEdit()

        self.exit()


# класс предок изменеия выбранной записи
class EditDialog(OperationsDialog):
    def __init__(self, user_id, category, date, cost, row, parent=None):
        super(EditDialog, self).__init__(user_id, category, date, cost,
                                         "ui/edit_dialog.ui", "Изменение записи", parent)

        self.row = row

        # устанавливаем данные для изменения в виджеты диалога
        self.select_category.setCurrentText(self.category)
        self.select_cost.setValue(float(self.cost))
        year, month, day = list(map(int, self.date.split('-')))
        self.select_date.setDate(QDate(year, month, day))

        self.button_edit.clicked.connect(self.editNote)

    # метод для изменения выбранной записи
    def editNote(self):
        cur = self.con.cursor()
        # получаем id категории из базы данных
        self.category = cur.execute(f'''SELECT CategoryId FROM Category 
WHERE Title = "{self.category}"''').fetchone()[0]

        # получаем id новой категории из базы данных
        category = cur.execute(f'''SELECT CategoryId FROM Category 
WHERE Title = "{self.select_category.currentText()}"''').fetchone()[0]
        date = self.select_date.date().toString("yyyy-MM-dd")
        cost = self.select_cost.value()

        # если что-то изменено, то изменяем запись в базе данных
        if self.cost != cost or self.category != category or self.date != date:
            # получаем id выбранной записи из базы данных
            cost_id = cur.execute(f'''SELECT CostId FROM Cost 
WHERE UserId={self.user_id} AND CategoryId={self.category} 
AND Date="{self.date}" AND SumCost={self.cost}''').fetchone()[0]
            # изменяем запись базе данных
            cur.execute(f'''UPDATE Cost SET UserId={self.user_id}, 
CategoryId={category}, Date="{date}", SumCost={cost} WHERE CostId={cost_id}''')
            # изменяем запись в таблице
            table = self.parent().getTable()
            del table[self.row]
            category = cur.execute(f'''SELECT Title FROM Category 
WHERE CategoryId={category}''').fetchone()[0]
            table.insert(self.row, (category, date, cost))
            self.parent().setTable(table)
        cur.close()
        self.con.commit()

        self.parent().graph.updateDateEdit()

        self.exit()


# родительский класс для фильтрации записей
class FilterDialog(QDialog):
    def __init__(self, user_id, table, filename, title, *args, parent=None):
        super(FilterDialog, self).__init__(parent)

        self.user_id = user_id
        self.args = args[0][0]
        self.table = table

        # загружаем ui диалога
        self.loadUI(filename, title)

        self.button_filter.clicked.connect(self.filterOut)
        self.button_exit.clicked.connect(self.exit)

    # метод для отображения ui диалога
    def loadUI(self, filename, title):
        uic.loadUi(filename, self)
        self.setWindowTitle(title)

    # метод фильтрации
    def filterOut(self):
        pass

    # метод для отмены фильтрации записей
    def exit(self):
        self.close()


# класс предок фильтрации записей по категориям
class CategoryFilterDialog(FilterDialog):
    def __init__(self, user_id, table, *categories, parent=None):
        super(CategoryFilterDialog, self).__init__(user_id, table,
                                                   "ui/filter_by_categories_dialog.ui",
                                                   "Фильтр по категория", categories, parent=parent)
        # добавляем категории в список
        for category in self.args:
            item = QListWidgetItem(category)
            item.setCheckState(Qt.Checked)
            self.listWidget.addItem(item)

    # метод фильтрации
    def filterOut(self):
        categories_checked = []
        for i in range(self.listWidget.count()):
            list_item = self.listWidget.item(i)
            # добавляем выбранные категории
            if list_item.checkState():
                categories_checked.append(list_item.text())

        # присваеваим отфильтрованную таблицу
        self.parent().setFilteredTable(list(filter(lambda x: x[0] in categories_checked,
                                                   self.table)))
        # устанавливаем параметр фильтрации
        self.parent().setFilterParameter("by_categories", lambda x: x[0] in categories_checked)

        self.exit()


# класс предок фильтрации записей по датам
class DateFilterDialog(FilterDialog):
    def __init__(self, user_id, table, *dates, parent=None):
        super(DateFilterDialog, self).__init__(user_id, table, "ui/filter_by_dates_dialog.ui",
                                               "Фильтр по датам", dates, parent=parent)

        # устанавливаем минимальную дату
        year_from, month_from, day_from = list(map(int, self.args[0].split('-')))
        self.date_from.setDate(QDate(year_from, month_from, day_from))

        # устанавливаем максимальную дату
        year_to, month_to, day_to = list(map(int, self.args[-1].split('-')))
        self.date_to.setDate(QDate(year_to, month_to, day_to))

    def filterOut(self):
        date_from = self.date_from.date().toString("yyyy-MM-dd")
        date_to = self.date_to.date().toString("yyyy-MM-dd")

        # присваеваим отфильтрованную таблицу
        self.parent().setFilteredTable(list(filter(lambda x: date_from <= x[1] <= date_to,
                                                   self.table)))
        # устанавливаем параметр фильтрации
        self.parent().setFilterParameter("by_dates", lambda x: date_from <= x[1] <= date_to)

        self.exit()


# класс предок фильтрации записей по ценам
class CostFilterDialog(FilterDialog):
    def __init__(self, user_id, table, *costs, parent=None):
        super(CostFilterDialog, self).__init__(user_id, table, "ui/filter_by_costs_dialog.ui",
                                               "Фильтр по ценам", costs, parent=parent)

        # настраиваем double spin box'ы
        self.cost_from.setRange(float(self.args[0]), float(self.args[-1]))
        self.cost_to.setRange(float(self.args[0]), float(self.args[-1]))
        # устанавливаем минимальную цену
        self.cost_from.setValue(float(self.args[0]))
        # устанавливаем максимальную цену
        self.cost_to.setValue(float(self.args[-1]))

    def filterOut(self):
        cost_from = self.cost_from.value()
        cost_to = self.cost_to.value()

        # присваеваим отфильтрованную таблицу
        self.parent().setFilteredTable(list(filter(lambda x: cost_from <= x[2] <= cost_to,
                                                   self.table)))
        # устанавливаем параметр фильтрации
        self.parent().setFilterParameter("by_dates", lambda x: cost_from <= x[2] <= cost_to)

        self.exit()


# класс входа в аккаунт пользователя
class SignInDialog(QDialog):
    def __init__(self, parent=None):
        super(SignInDialog, self).__init__(parent)

        self.con = sqlite3.connect("Cost.db")

        uic.loadUi("ui/sign_in_dialog.ui", self)
        self.setWindowTitle("Вход в аккаунт")

        self.button_sign_in.clicked.connect(self.signIn)

    # метод входа в аккаунт
    def signIn(self):
        login = self.input_login.text()
        password = self.input_password.text()

        try:
            if not login:
                raise LoginError("В поле логина ничего не введено")

            if not password:
                raise PasswordError("В поле пароля ничего не введено")

            cur = self.con.cursor()
            # получаем id и пароль пользователя из базы данных
            result = cur.execute(f'''SELECT UserId, Password FROM User 
WHERE Login = "{login}"''').fetchone()
            # если список пуст, сообщаем, что пользователь ввел неверный логин
            if result:
                # если пароль не верный, сообщаем, что пользователь ввел неверный пароль
                if checkPassword(result[1], password):
                    # присваиваем id пользователя
                    self.parent().setUserId(result[0])
                    change_border(self.input_login, "black")
                    change_border(self.input_password, "black")
                else:
                    raise PasswordError("Неверный пароль")
            else:
                raise LoginError("Неправильный логин")
        except LoginError as error:
            self.errorHandler(error, self.input_login, "red")
            return
        except PasswordError as error:
            self.errorHandler(error, self.input_password, "red")
            return

        cur.close()
        self.con.close()
        self.close()

    # метод отображения ошибок ввода
    def errorHandler(self, error, widget, color):
        self.status.setText(f"{error}")
        change_border(widget, color)


# класс регистрации пользователя
class SignUpDialog(QDialog):
    def __init__(self, parent=None):
        super(SignUpDialog, self).__init__(parent)

        self.con = sqlite3.connect("Cost.db")

        uic.loadUi("ui/sign_up_dialog.ui", self)
        self.setWindowTitle("Регистрация аккаунта")

        self.button_sign_up.clicked.connect(self.signUp)

    # метод для регистрации нового пользователя
    def signUp(self):
        login = self.input_login.text()
        password = IsCorrectPassword(self.input_password.text())

        try:
            if not login:
                raise LoginError("В поле логина ничего не введено")

            if not password:
                raise PasswordError("В поле пароля ничего не введено")

            cur = self.con.cursor()
            # если пользователь с таким логином уже существует, сообщаем пользователю
            if cur.execute(f'SELECT * FROM User WHERE Login = "{login}"').fetchone() is not None:
                raise LoginError("В системе уже имеется пользователь с таким логином")

            # если пароль корректен, добавляем нового пользователя в базу данных
            # иначе сообщаем пользователю где он ошибся
            if password.checkPassword():
                #
                cur.execute(f'''INSERT INTO USER(Login, Password) 
VALUES("{login}", "{hash_password(password.password)}")''')
                change_border(self.input_password, "black")
                change_border(self.input_login, "black")
        except LoginError as error:
            self.errorHandler(error, self.input_login, "red")
            return
        except PasswordError as error:
            self.errorHandler(error, self.input_password, "red")
            return

        self.con.commit()

        self.parent().user_id = cur.execute(f'''SELECT UserId FROM User 
WHERE Login = "{login}"''').fetchone()[0]

        cur.close()
        self.con.close()
        self.close()

    # метод отображения ошибок ввода
    def errorHandler(self, error, widget, color):
        self.status.setText(f"{error}")
        change_border(widget, color)


# класс виджета графика
class GraphWidget(graph_widget.GraphWidget):
    pass
