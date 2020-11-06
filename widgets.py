import sqlite3
import uuid
import hashlib
import datetime

from PyQt5 import uic, QtGui
from PyQt5.QtCore import QDate, Qt
from PyQt5.QtWidgets import QDialog, QInputDialog, QListWidgetItem

LENGTH = 9
SEQUENCES = ("qwertyuiop", "asdfghjkl", "zxcvbnm", "йцукенгшщзхъ", "фывапролджэё", "ячсмитьбю")
DIGITS = "0123456789"


def change_border(widget, color):
    widget.setFont(QtGui.QFont('Times', 14))
    widget.setStyleSheet(f'''border-style: solid; border-width: 1px; border-color: {color};''')


def hash_password(password):
    salt = uuid.uuid4().hex
    return hashlib.sha256(salt.encode() + password.encode()).hexdigest() + ':' + salt


def check_password(hashed_password, user_password):
    password, salt = hashed_password.split(':')
    return password == hashlib.sha256(salt.encode() + user_password.encode()).hexdigest()


class LoginError(Exception):
    pass


class PasswordError(Exception):
    pass


class LengthError(PasswordError):
    pass


class LetterError(PasswordError):
    pass


class DigitError(PasswordError):
    pass


class SequenceError(PasswordError):
    pass


class IsCorrectPassword:
    def __init__(self, password: str):
        self.password = password

    def is_valid_length(self):
        return len(self.password) > LENGTH

    def is_valid_registers(self):
        return self.password != self.password.lower() and self.password != self.password.upper()

    def contains_digit(self):
        for digit in DIGITS:
            if digit in self.password:
                return True
        return False

    def is_valid_sequences(self):
        for index, sym in enumerate(self.password):
            for sequence in SEQUENCES:
                if sym.lower() in sequence:
                    sym_index = sequence.index(sym.lower())
                    if sym_index < len(sequence) - 2 and index < len(self.password) - 2:
                        if (self.password[index + 1].lower(), self.password[index + 2].lower()) \
                                == (sequence[sym_index + 1], sequence[sym_index + 2]):
                            return False
                    break
        return True

    def check_password(self):
        if not self.is_valid_length():
            raise LengthError(f"Длина пароля <= {LENGTH}")
        if not self.is_valid_registers():
            raise LetterError("В пароле символы одного регистра")
        if not self.contains_digit():
            raise DigitError("В пароле не содержится цифра")
        if not self.is_valid_sequences():
            raise SequenceError("В пароле есть последовательность из символов на клавиатуре")
        return True


class OperationsDialog(QDialog):
    def __init__(self, user_id, category, date, cost, filename, title, parent=None):
        super(OperationsDialog, self).__init__(parent)

        self.con = sqlite3.connect("Cost.db")

        self.user_id = user_id
        self.category = category
        self.date = date
        self.cost = cost

        self.loadUI(filename, title)

        cur = self.con.cursor()
        categories = map(lambda item: item[0], cur.execute("SELECT Title FROM Category").fetchall())
        self.select_category.addItems(categories)

        self.select_cost.setSingleStep(0.01)
        self.select_cost.setRange(0.01, 10e9)

        today = datetime.date.today()
        year, month, day = today.year, today.month, today.day
        self.select_date.setDate(QDate(year, month, day))

        self.button_create_category.clicked.connect(self.new_category)
        self.button_exit.clicked.connect(self.exit)

    def loadUI(self, filename, title):
        uic.loadUi(filename, self)
        self.setWindowTitle(title)

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

    def exit(self):
        self.con.close()
        self.close()


class NoteWindow(OperationsDialog):
    def __init__(self, user_id, category, date, cost, parent=None):
        super(NoteWindow, self).__init__(user_id, category, date, cost,
                                         "ui/new_note_window.ui", "Новая запись", parent)

        self.button_add.clicked.connect(self.add_note)

    def add_note(self):
        cur = self.con.cursor()

        self.category = cur.execute(f'''SELECT CategoryId FROM Category 
WHERE Title = "{self.select_category.currentText()}"''').fetchone()[0]
        self.date = self.select_date.date().toString("yyyy-MM-dd")
        self.cost = self.select_cost.value()

        cur.execute(f'''INSERT INTO Cost(UserId, CategoryId, Date, SumCost) 
VALUES({self.user_id}, {self.category}, "{self.date}", {self.cost})''')
        cur.close()
        self.con.commit()

        self.exit()


class EditWindow(OperationsDialog):
    def __init__(self, user_id, category, date, cost, parent=None):
        super(EditWindow, self).__init__(user_id, category, date, cost,
                                         "ui/edit_window.ui", "Изменение записи", parent)

        self.select_category.setCurrentText(self.category)

        self.select_cost.setValue(float(self.cost))

        year, month, day = list(map(int, self.date.split('-')))
        self.select_date.setDate(QDate(year, month, day))

        self.button_edit.clicked.connect(self.edit_note)

    def edit_note(self):
        cur = self.con.cursor()

        self.category = cur.execute(f'''SELECT CategoryId FROM Category 
WHERE Title = "{self.category}"''').fetchone()[0]

        category = cur.execute(f'''SELECT CategoryId FROM Category 
WHERE Title = "{self.select_category.currentText()}"''').fetchone()[0]
        date = self.select_date.date().toString("yyyy-MM-dd")
        cost = self.select_cost.value()

        if self.cost != cost or self.category != category or self.date != date:
            cost_id = cur.execute(f'''SELECT CostId FROM Cost 
WHERE UserId={self.user_id} AND CategoryId={self.category} 
AND Date="{self.date}" AND SumCost={self.cost}''').fetchone()[0]
            cur.execute(f'''UPDATE Cost SET UserId={self.user_id}, 
CategoryId={category}, Date="{date}", SumCost={cost} WHERE CostId={cost_id}''')
        cur.close()
        self.con.commit()

        self.exit()


class FilterDialog(QDialog):
    def __init__(self, user_id, table, filename, title, *args, parent=None):
        super(FilterDialog, self).__init__(parent)

        self.user_id = user_id
        self.args = args[0][0]
        self.table = table

        self.loadUI(filename, title)

        self.button_filter.clicked.connect(self.filter_out)
        self.button_exit.clicked.connect(self.exit)

    def loadUI(self, filename, title):
        uic.loadUi(filename, self)
        self.setWindowTitle(title)

    def filter_out(self):
        pass

    def exit(self):
        self.close()


class CategoryFilter(FilterDialog):
    def __init__(self, user_id, table, *categories, parent=None):
        super(CategoryFilter, self).__init__(user_id, table, "ui/filter_by_categories.ui",
                                             "Фильтр по категория", categories, parent=parent)

        for category in self.args:
            item = QListWidgetItem(category)
            item.setCheckState(Qt.Checked)
            self.listWidget.addItem(item)

    def filter_out(self):
        categories_checked = []
        for i in range(self.listWidget.count()):
            list_item = self.listWidget.item(i)
            if list_item.checkState():
                categories_checked.append(list_item.text())

        self.parent().setTable(list(filter(lambda x: x[0] in categories_checked, self.table)))

        self.exit()


class DateFilter(FilterDialog):
    def __init__(self, user_id, table, *dates, parent=None):
        super(DateFilter, self).__init__(user_id, table, "ui/filter_by_dates.ui",
                                         "Фильтр по датам", dates, parent=parent)

        year_from, month_from, day_from = list(map(int, self.args[0].split('-')))
        self.date_from.setDate(QDate(year_from, month_from, day_from))

        year_to, month_to, day_to = list(map(int, self.args[-1].split('-')))
        self.date_to.setDate(QDate(year_to, month_to, day_to))

    def filter_out(self):
        date_from = self.date_from.date().toString("yyyy-MM-dd")
        date_to = self.date_to.date().toString("yyyy-MM-dd")

        self.parent().setTable(list(filter(lambda x: date_from <= x[1] <= date_to, self.table)))

        self.exit()


class CostFilter(FilterDialog):
    def __init__(self, user_id, table, *costs, parent=None):
        super(CostFilter, self).__init__(user_id, table, "ui/filter_by_costs.ui",
                                         "Фильтр по ценам", costs, parent=parent)

        self.cost_from.setRange(float(self.args[0]), float(self.args[-1]))
        self.cost_from.setValue(float(self.args[0]))
        self.cost_to.setRange(float(self.args[0]), float(self.args[-1]))
        self.cost_to.setValue(float(self.args[-1]))

    def filter_out(self):
        cost_from = self.cost_from.value()
        cost_to = self.cost_to.value()

        self.parent().setTable(list(filter(lambda x: cost_from <= x[2] <= cost_to, self.table)))

        self.exit()


class SignInWindow(QDialog):
    def __init__(self, parent=None):
        super(SignInWindow, self).__init__(parent)

        self.con = sqlite3.connect("Cost.db")

        uic.loadUi("ui/sign_in_window.ui", self)
        self.setWindowTitle("Вход в аккаунт")

        self.button_sign_in.clicked.connect(self.signIn)

    def signIn(self):
        login = self.input_login.text()
        password = self.input_password.text()

        try:
            if not login:
                raise LoginError("В поле логина ничего не введено")

            if not password:
                raise PasswordError("В поле пароля ничего не введено")

            cur = self.con.cursor()
            result = cur.execute(f'''SELECT UserId, Password FROM User 
WHERE Login = "{login}"''').fetchone()
            if result:
                if check_password(result[1], password):
                    self.parent().user_id = result[0]
                    change_border(self.input_login, "black")
                    change_border(self.input_password, "black")
                else:
                    raise PasswordError("Неверный пароль")
            else:
                raise LoginError("Неправильный логин")
        except LoginError as error:
            self.error_handler(error, self.input_login, "red")
            return
        except PasswordError as error:
            self.error_handler(error, self.input_password, "red")
            return

        cur.close()
        self.con.close()
        self.close()

    def error_handler(self, error, widget, color):
        self.status.setText(f"{error}")
        change_border(widget, color)


class SignUpWindow(QDialog):
    def __init__(self, parent=None):
        super(SignUpWindow, self).__init__(parent)

        self.con = sqlite3.connect("Cost.db")

        uic.loadUi("ui/sign_up_window.ui", self)
        self.setWindowTitle("Регестрация аккаунта")

        self.button_sign_up.clicked.connect(self.signUp)

    def signUp(self):
        login = self.input_login.text()
        password = IsCorrectPassword(self.input_password.text())

        try:
            if not login:
                raise LoginError("В поле логина ничего не введено")

            if not password:
                raise PasswordError("В поле пароля ничего не введено")

            cur = self.con.cursor()
            if cur.execute(f'SELECT * FROM User WHERE Login = "{login}"').fetchone() is not None:
                raise LoginError("В системе уже имеется пользователь с таким логином")

            if password.check_password():
                cur.execute(f'''INSERT INTO USER(Login, Password) 
VALUES("{login}", "{hash_password(password.password)}")''')
                change_border(self.input_password, "black")
                change_border(self.input_login, "black")
        except LoginError as error:
            self.error_handler(error, self.input_login, "red")
            return
        except PasswordError as error:
            self.error_handler(error, self.input_password, "red")
            return

        self.con.commit()

        self.parent().user_id = cur.execute(f'''SELECT UserId FROM User 
WHERE Login = "{login}"''').fetchone()[0]

        cur.close()
        self.con.close()
        self.close()

    def error_handler(self, error, widget, color):
        self.status.setText(f"{error}")
        change_border(widget, color)
