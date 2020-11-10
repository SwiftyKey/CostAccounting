from PyQt5.QtWidgets import QWidget, QListWidgetItem, QLabel
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtCore import Qt, QDate
import matplotlib.pyplot as plt
from PyQt5 import uic
import sqlite3
from datetime import date
import numpy as np


# функция для сортировки списка дат
def sort_list_dates(dates):
    return sorted(dates, key=lambda x: str_date_to_datetime(x))


# функция приведения даты к формату date
def str_date_to_datetime(date_1):
    day, month, year = map(int, date_1.split('.'))
    return date(year, month, day)


# функция приведения дат "yyyy-mm-dd" к формату "dd.mm.yyyy"
def list_dates_to_format(dates):
    for i in range(len(dates)):
        for j in range(len(dates[i])):
            year, month, day = list(map(int, dates[i][j].split('-')))
            dates[i][j] = date(year, month, day).strftime("%d.%m.%Y")

    return dates


# функция форматирования строки для создания круговой диаграммы
def format_string(pct, number):
    return "{:.2f} руб.\n({:.2f}%)".format(float(pct / 100. * np.sum(number)), pct)


# функция приведения полученных данных к удобному виду для построения столбчатой диаграммы и графика
def do_data_to_format_bar_and_plot_graph(data, labels, dates):
    format_list = []
    all_dates = []  # создается список всех дат
    for i in dates:
        for j in i:
            if j not in all_dates:
                all_dates.append(j)
    all_dates = sort_list_dates(all_dates)

    # обрезается категория "иное", нужная только для построения круговой диаграммы
    if labels:
        if labels[-1] == 'Иное':
            labels = labels[:-1]
            data = data[:-1]

    for i in range(len(labels)):
        union_data_and_dates = zip(data[i], dates[i])
        # сортировка для того, чтобы покупки соответствовали датам
        sorted_union_data_and_dates = sorted(union_data_and_dates,
                                             key=lambda tup: (str_date_to_datetime(tup[1]), tup[0]))
        sorted_dates = all_dates
        sorted_data = [0] * len(all_dates)

        # цикл для того, чтобы не было случая, когда покупок больше чем дат
        # иначе построение графика окажется невозможным
        for j in sorted_union_data_and_dates:
            sorted_data[sorted_dates.index(j[1])] += j[0]

        format_list.append((sorted_data, sorted_dates, labels[i]))

    return format_list, all_dates


# функция приведения данных к формату, удобному для  построения круговой диаграммы
def do_data_to_format_pie_graph(data):
    format_data = []

    for i in range(len(data)):
        format_data.append(sum(data[i]))

    return format_data


# класс виджета для построения графиков на основе данных из db
class GraphWidget(QWidget):
    def __init__(self, user_id, parent=None):
        super(GraphWidget, self).__init__(parent)

        self.user_id = user_id

        uic.loadUi('ui/graph_widget.ui', self)

        self.figure = plt.figure()

        self.label_if_not_found_inf = QLabel(self)
        self.label_if_not_found_inf.setText("")

        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)

        self.verticalLayout_3.addWidget(self.canvas)
        self.verticalLayout_3.addWidget(self.label_if_not_found_inf)

        self.con = sqlite3.connect('Cost.db')
        self.updateListCategories()

        self.first_date_year, self.first_date_month, self.first_date_day = None, None, None
        self.last_date_year, self.last_date_month, self.last_date_day = None, None, None
        self.index_diagram, self.list_categories = None, None

        self.dateEdit.setDate(QDate.currentDate())
        self.dateEdit_2.setDate(QDate.currentDate())

        self.pushButton.clicked.connect(self.plot)

        self.updateDateEdit()

    def __del__(self):
        self.con.close()

    # метод для построения НЕОБХОДИМОЙ нам диаграммы
    def plot(self):
        # получаем все нужные данные для построения диаграмм
        user_data = self.gerUserData()
        self.first_date_year, self.first_date_month, self.first_date_day = user_data[:3]
        self.last_date_year, self.last_date_month, self.last_date_day = user_data[3:6]
        self.index_diagram, self.list_categories = user_data[6:]

        if self.index_diagram == 0:
            self.buildPiePlot()
        elif self.index_diagram == 1:
            self.buildPlot()
        else:
            self.buildBarPlot()

    # метод для очистки поля для построения графиков
    def clear(self):
        self.figure.clear()

    # метод для построения круговой диаграммы
    def buildPiePlot(self):
        self.clear()

        data, labels_graph, _ = self.findInfo()
        data = do_data_to_format_pie_graph(data)

        # если были найдены данные в таблице, то рисуем по ним график
        if labels_graph:
            self.label_if_not_found_inf.setText("")

            ax = self.figure.add_subplot(111)

            patches, x, t = plt.pie(data, autopct=lambda pct: format_string(pct, data),
                                    textprops=dict(color="w"))

            ax.legend(patches, labels_graph, title="Расходы", loc="lower right",
                      bbox_to_anchor=(1, 0, 0.5, 1))
            ax.set_title("Круговая диаграмма ваших расходов:")

            self.canvas.draw()
        # иначе выводим надпись о том, что не найдены данные, удовлетворяющие запросу
        else:
            self.clear()
            self.label_if_not_found_inf.setText("Не было найдено информации, "
                                                "убедитесь, что данные"
                                                " введены верно и повторите запрос.")

    # метод для построения столбчатой диаграммы
    def buildBarPlot(self):
        self.clear()

        data, labels_graph, dates = self.findInfo()
        data_to_build_graph, all_dates = \
            do_data_to_format_bar_and_plot_graph(data, labels_graph, list_dates_to_format(dates))

        if labels_graph:
            self.label_if_not_found_inf.setText("")

            ax = self.figure.add_subplot(111)

            # значения для аргумента bottom, чтобы столбцы не наслаивались друг на друга
            values = [0] * len(all_dates)

            for i in range(len(data_to_build_graph)):
                ax.bar(data_to_build_graph[i][1], data_to_build_graph[i][0],
                       width=0.25, bottom=values, label=data_to_build_graph[i][2])

                # обновляются значения values для аргумента bottom
                for val in range(len(data_to_build_graph[i][1])):
                    values[all_dates.index(data_to_build_graph[i][1][val])] += \
                        data_to_build_graph[i][0][val]

            ax.set_title("Гистограмма ваших расходов:")
            ax.set_ylabel("Затраты")
            ax.set_xlabel("Даты покупок")
            ax.legend()

            self.canvas.draw()
        else:
            self.label_if_not_found_inf.setText("Не было найдено информации, "
                                                "убедитесь, что данные введены "
                                                "верно и повторите запрос.")

    # метод для построения графика
    def buildPlot(self):
        self.clear()

        data, labels_graph, data_to_build_graph = self.findInfo()

        data_to_build_graph, all_dates = \
            do_data_to_format_bar_and_plot_graph(data, labels_graph,
                                                 list_dates_to_format(data_to_build_graph))

        if labels_graph:
            self.label_if_not_found_inf.setText("")

            ax = self.figure.add_subplot(111)

            # строятся графики расходов по категориям по очереди
            for i in range(len(data_to_build_graph)):
                ax.plot(data_to_build_graph[i][1], data_to_build_graph[i][0], "o-",
                        label=data_to_build_graph[i][2])

            ax.set_title("График ваших расходов:")
            ax.set_ylabel("Затраты")
            ax.set_xlabel("Даты покупок")
            ax.legend()

            self.canvas.draw()
        else:
            self.label_if_not_found_inf.setText("Не было найдено информации, "
                                                "убедитесь, что данные введены"
                                                " верно и повторите запрос.")

    # метод для нахождения суммы расходов по категориям
    def findInfo(self):
        first_date = date(self.first_date_year, self.first_date_month, self.first_date_day).strftime(
            "%Y-%m-%d")
        second_date = date(self.last_date_year, self.last_date_month, self.last_date_day).strftime(
            "%Y-%m-%d")

        # приводим даты к правильному формату для того, чтобы работать с SqLite
        cur = self.con.cursor()

        data = []
        labels = []
        dates = []

        something = 0
        result = cur.execute("""SELECT * FROM Cost 
        WHERE (date(Date) >= date(?) and date(Date) <= date(?)) and UserId = ?""",
                             (first_date, second_date, self.getUserId())).fetchall()

        # получаем все данные, удовлетворяющие временному отрезку, указанному пользователем
        for i in range(len(result)):
            category = cur.execute("""SELECT Title FROM Category WHERE CategoryId = ?""",
                                   (result[i][2],)).fetchone()[0]
            if category not in labels:
                if category in self.list_categories:
                    # заполняются двумерные списки дат и значений, соответствующих друг другу
                    labels.append(category)
                    data.append([result[i][4]])
                    dates.append([result[i][3]])
                else:
                    # заполняется значение иных категорий, не выбранных пользователем
                    something += result[i][4]
            else:
                data[labels.index(category)].append(result[i][4])
                dates[labels.index(category)].append(result[i][3])

        if something != 0 and data:
            data.append([something])
            labels.append("Иное")

        return data, labels, dates

    # метод для получения необходимой для нас информации для построения диаграммы
    def gerUserData(self):
        list_categories = []

        for i in range(self.listWidget.count()):
            list_item = self.listWidget.item(i)
            if list_item.checkState():
                list_categories.append(list_item.text())

        first_date = self.dateEdit.date()  # возвращает объект типа QDate
        last_date = self.dateEdit_2.date()  # возвращает объект типа QDate

        diagram = self.comboBox.currentIndex()  # индекс графика
        # раскладываем даты на три составляющих для дальнейших операций с ними

        result = [first_date.year(), first_date.month(), first_date.day(),
                  last_date.year(), last_date.month(), last_date.day(), diagram, list_categories]
        return result

    # обновление списка категорий
    def updateListCategories(self):
        cur = self.con.cursor()
        iterations = cur.execute('SELECT title FROM Category').fetchall()
        # получаем список всех категорий из БД
        names_categories = [i[0] for i in iterations]
        self.list_categories = names_categories
        # ListWidget заполняется категориями из БД с возможностью отмечать необходимые ему категории

        self.listWidget.clear()

        for i in names_categories:
            item = QListWidgetItem()
            item.setText(i)
            item.setCheckState(Qt.Checked)
            self.listWidget.addItem(item)

    # метод для нахождения минимальной даты в записях
    def findMinDate(self):
        cur = self.con.cursor()
        min_date = cur.execute("SELECT MIN (Date) FROM COST WHERE UserId = ?",
                               (self.getUserId(),)).fetchone()[0]
        if min_date:
            year, month, day = min_date.split('-')
            return year, month, day
        else:
            return None

    def findMaxDate(self):
        cur = self.con.cursor()
        max_date = cur.execute("SELECT MAX (Date) FROM COST WHERE UserId = ?",
                               (self.getUserId(),)).fetchone()[0]
        if max_date:
            year, month, day = max_date.split('-')
            return year, month, day
        else:
            return None

    # метод для установки минимальной даты
    def updateDateEdit(self):
        min_date = self.findMinDate()
        if min_date:
            year, day, month = min_date
            self.dateEdit.setDate(QDate(int(year), int(day), int(month)))
        else:
            self.dateEdit.setDate(QDate.currentDate())

        max_date = self.findMaxDate()
        if max_date:
            year, day, month = max_date
            self.dateEdit_2.setDate(QDate(int(year), int(day), int(month)))
        else:
            self.dateEdit.setDate(QDate.currentDate())
            
    # метод для получения id пользователя
    def getUserId(self):
        return self.user_id

    # метод для присваиваня нового id пользователя
    def setUserId(self, user_id):
        self.user_id = user_id
