from PyQt5 import uic, QtGui
from PyQt5.QtWidgets import QDialog, QInputDialog

import sqlite3

LENGTH = 9
SEQUENCES = ("qwertyuiop", "asdfghjkl", "zxcvbnm", "йцукенгшщзхъ", "фывапролджэё", "ячсмитьбю")
DIGITS = "0123456789"


def change_border(widget, color):
    widget.setFont(QtGui.QFont('TimesNewRoman', 14))
    widget.setStyleSheet(f'''border-style: solid; border-width: 1px; border-color: {color};''')


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
        return len(self.password) > 8

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
            raise LengthError("Длина пароля <= 8")
        if not self.is_valid_registers():
            raise LetterError("В пароле символы одного регистра")
        if not self.contains_digit():
            raise DigitError("В пароле не содержится цифра")
        if not self.is_valid_sequences():
            raise SequenceError("В пароле есть последовательность из символов на клавиатуре")
        return True


class NoteWindow(QDialog):
    def __init__(self, user_id, parent=None):
        super(NoteWindow, self).__init__(parent)

        self.con = sqlite3.connect("Cost.db")

        self.user_id = user_id
        self.category = ""
        self.date = ""
        self.cost = ""

        uic.loadUi("ui/new_note_window.ui", self)
        self.setWindowTitle("Новая запись")

        cur = self.con.cursor()
        categories = map(lambda item: item[0], cur.execute("SELECT Title FROM Category").fetchall())
        self.select_category.addItems(categories)

        self.select_cost.setMaximum(10e9)

        self.button_add.clicked.connect(self.add_note)
        self.button_create_category.clicked.connect(self.new_category)
        self.button_exit.clicked.connect(self.exit)

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

    def add_note(self):
        cur = self.con.cursor()

        self.category = cur.execute(f'''SELECT CategoryId FROM Category 
WHERE Title = "{self.select_category.currentText()}"''').fetchone()[0]
        self.date = self.select_date.selectedDate().toString("yyyy-MM-dd")
        self.cost = self.select_cost.value()

        cur.execute(f'''INSERT INTO Cost(UserId, CategoryId, Date, SumCost) 
VALUES({self.user_id}, {self.category}, "{self.date}", {self.cost})''')
        cur.close()
        self.con.commit()
        self.con.close()

        self.exit()

    def exit(self):
        self.close()


class SignInWindow(QDialog):
    def __init__(self, parent=None):
        super(SignInWindow, self).__init__(parent)

        self.con = sqlite3.connect("Cost.db")

        uic.loadUi("ui/sign_in_window.ui", self)

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
                if result[1] == password:
                    self.parent().user_id = result[0]
                    change_border(self.input_login, "green")
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
VALUES("{login}", "{password.password}")''')
                change_border(self.input_password, "black")
                change_border(self.input_login, "black")
        except LoginError as error:
            self.error_handler(error, self.input_login, "red")
            return
        except LengthError as error:
            self.error_handler(error, self.input_password, "red")
            return
        except LetterError as error:
            self.error_handler(error, self.input_password, "red")
            return
        except DigitError as error:
            self.error_handler(error, self.input_password, "red")
            return
        except SequenceError as error:
            self.error_handler(error, self.input_password, "red")
            return
        except PasswordError as error:
            self.error_handler(error, self.input_password, "red")
            return

        self.con.commit()

        self.parent().user_id = cur.execute(f'''SELECT UserId FROM User 
WHERE Login = "{login}"''').fetchone()

        self.con.close()
        self.close()

    def error_handler(self, error, widget, color):
        self.status.setText(f"{error}")
        change_border(widget, color)
