import sys
from PyQt5.QtWidgets import QWidget, QApplication, QListWidgetItem, QLabel
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtCore import Qt
import matplotlib.pyplot as plt
from PyQt5 import uic
import sqlite3
from datetime import date
import numpy as np


def sort_list_dates(dates):  # функция для сортировки списка дат
    return sorted(dates, key=lambda x: str_date_to_datetime(x))


def str_date_to_datetime(date_1):  # функция приведения даты к формату date
    day, month, year = map(int, date_1.split('.'))
    return date(year, month, day)


def list_dates_to_format(dates):  # функция приведения дат "yyyy-mm-dd" к формату "dd.mm.yyyy"
    for i in range(len(dates)):
        for j in range(len(dates[i])):
            year, month, day = list(map(int, dates[i][j].split('-')))
            dates[i][j] = date(year, month, day).strftime("%d.%m.%Y")
    return dates


def format_string(pct, number):  # функция форматирования строки для создания круговой диаграммы
    absolute = int(pct / 100. * np.sum(number))
    return "{:d} руб.\n({:.1f}%)".format(absolute, pct)


def do_data_to_format_bar_and_plot_graph(data, labels,
                                         dates):  # функция приведения полученных данных к удобному виду
    # для построения столбчатой диаграммы и графика
    format_list = []
    all_dates = []
    for i in dates:  # создается список всех дат
        for j in i:
            if j not in all_dates:
                all_dates.append(j)
    all_dates = sort_list_dates(all_dates)
    if labels:  # брезается категория "иное", нужная только для построения круговой диаграммы
        if labels[-1] == 'Иное':
            labels = labels[:-1]
            data = data[:-1]

    for i in range(len(labels)):
        union_data_and_dates = zip(data[i], dates[i])
        sorted_union_data_and_dates = sorted(union_data_and_dates,
                                             # сортировка для того, чтобы покупки соответствовали
                                             key=lambda tup: (
                                             str_date_to_datetime(tup[1]), tup[0]))  # датам
        sorted_dates = all_dates
        sorted_data = [0] * len(all_dates)
        for j in sorted_union_data_and_dates:  # цикл для того, чтобы не было случая, когда покупок больше чем дат
            sorted_data[sorted_dates.index(j[1])] += j[
                0]  # иначе построение графика окажется невозможным

        format_list.append((sorted_data, sorted_dates, labels[i]))

    return format_list, all_dates  # возвращает еще все даты, чтобы в дальнейшнем не пришлось их считать заново


def do_data_to_format_pie_graph(data):  # функция приведения данных к формату, удобному для
    format_data = []  # построения круговой диаграммы
    for i in range(len(data)):
        format_data.append(sum(data[i]))
    return format_data


class GraphWidget(QWidget):
    def __init__(self, parent=None):
        self.userId = None
        super(GraphWidget, self).__init__(parent)
        uic.loadUi('ui/graph_window.ui', self)
        self.figure = plt.figure()
        self.label_if_not_found_inf = QLabel(self)
        self.label_if_not_found_inf.setText("")
        self.canvas = FigureCanvas(self.figure)
        self.pushButton.clicked.connect(self.plot)
        self.verticalLayout_3.addWidget(self.canvas)
        self.verticalLayout_3.addWidget(self.label_if_not_found_inf)
        con = sqlite3.connect('Cost.db')
        cur = con.cursor()
        iterations = cur.execute('SELECT title FROM Category').fetchall()
        names_categories = [i[0] for i in iterations]  # получаем список всех категорий из БД
        self.list_categories = names_categories
        for i in names_categories:  # ListWidget заполняется категориями из БД
            item = QListWidgetItem()  # с возможностью отмечать необходимые ему категории
            item.setText(i)
            item.setCheckState(Qt.Checked)
            self.listWidget.addItem(item)
        con.close()

    def plot(self):  # функция для построения НЕОБХОДИМОЙ нам диаграммы
        self.first_date_year, self.first_date_month, self.first_date_day, \
        self.last_date_year, self.last_date_month, self.last_date_day, \
        self.index_diagram, self.list_categories = self.get_users_data()  # получаем все нужные данные
        # для построения диаграмм
        if self.index_diagram == 0:
            self.build_pie_plot()
        elif self.index_diagram == 1:
            self.build_plot()
        else:
            self.build_bar_plot()

    def build_pie_plot(self):  # функция для построения круговой диаграммы
        self.figure.clear()
        data, labels_graph, _ = self.find_information_for_graph()
        data = do_data_to_format_pie_graph(data)
        if labels_graph:  # если были найдены данные в таблице, то рисуем по ним график
            self.label_if_not_found_inf.setText("")
            ax = self.figure.add_subplot(111)
            patches, x, t = plt.pie(data, autopct=lambda pct: format_string(pct, data),
                                    textprops=dict(color="w"))
            ax.legend(patches, labels_graph, title="Расходы", loc="lower right",
                      bbox_to_anchor=(1, 0, 0.5, 1))
            ax.set_title("Круговая диаграмма ваших расходов:")
            self.canvas.draw()
        else:  # иначе выводим надпись о том, что не найдены данные, удовлетворяющие запросу
            self.figure.clear()
            self.label_if_not_found_inf.setText("Не было найдено информации, "
                                                "убедитесь, что данные введены верно и повторите запрос.")

    def build_bar_plot(self):  # функция для построения столбчатой диаграммы
        self.figure.clear()
        data, labels_graph, dates = self.find_information_for_graph()
        data_to_build_graph, all_dates = do_data_to_format_bar_and_plot_graph(data,
                                                                              labels_graph,
                                                                              list_dates_to_format(
                                                                                  dates))
        if labels_graph:
            self.label_if_not_found_inf.setText("")
            ax = self.figure.add_subplot(111)

            values = [0] * len(
                all_dates)  # значения для аргумента bottom, чтобы столбцы не наслаивались друг на друга

            for i in range(len(data_to_build_graph)):
                ax.bar(data_to_build_graph[i][1], data_to_build_graph[i][0],
                       width=0.25, bottom=values, label=data_to_build_graph[i][2])

                for val in range(len(data_to_build_graph[i][
                                         1])):  # обновляются значения values для аргумента bottom
                    values[all_dates.index(data_to_build_graph[i][1][val])] += \
                        data_to_build_graph[i][0][val]

            ax.set_title("Гистограмма ваших расходов:")
            ax.set_ylabel("Затраты")
            ax.set_xlabel("Даты покупок")
            ax.legend()
            self.canvas.draw()
        else:
            self.label_if_not_found_inf.setText("Не было найдено информации, "
                                                "убедитесь, что данные введены верно и повторите запрос.")

    def build_plot(self):
        self.figure.clear()
        data, labels_graph, data_to_build_graph = self.find_information_for_graph()
        data_to_build_graph, all_dates = do_data_to_format_bar_and_plot_graph(data, labels_graph,
                                                                              list_dates_to_format(
                                                                                  data_to_build_graph))
        if labels_graph:
            self.label_if_not_found_inf.setText("")
            ax = self.figure.add_subplot(111)
            for i in range(
                    len(data_to_build_graph)):  # строятся графики расходов по категориям по очереди
                ax.plot(data_to_build_graph[i][1], data_to_build_graph[i][0], "o-",
                        label=data_to_build_graph[i][2])
            ax.set_title("График ваших расходов:")
            ax.set_ylabel("Затраты")
            ax.set_xlabel("Даты покупок")
            ax.legend()
            self.canvas.draw()
        else:
            self.label_if_not_found_inf.setText("Не было найдено информации, "
                                                "убедитесь, что данные введены верно и повторите запрос.")

    def find_information_for_graph(self):  # функция для нахождения суммы расходов по категориям
        first_date = date(self.first_date_year, self.first_date_month, self.first_date_day).strftime(
            "%Y-%m-%d")
        second_date = date(self.last_date_year, self.last_date_month, self.last_date_day).strftime(
            "%Y-%m-%d")
        # приводим даты к правильному формату для того, чтобы работать с SqLite
        con = sqlite3.connect('Cost.db')
        cur = con.cursor()
        data = []
        labels = []
        dates = []
        something = 0
        result = cur.execute("""SELECT * FROM Cost WHERE 
                                     (date(Date) >= date(?)
                                     and date(Date) <= date(?)) and UserId = ?""",
                             (first_date,
                              second_date,
                              self.get_id())).fetchall()  # получаем все данные, удовлетворяющие временному отрезку, указанному пользователем
        for i in range(len(result)):
            category = cur.execute("""SELECT Title FROM Category WHERE CategoryId = ?""",
                                   (result[i][2],)).fetchone()[0]
            if category not in labels:
                if category in self.list_categories:  # заполняются двумерные списки дат и значений, соответствующих
                    labels.append(category)  # друг другу
                    data.append([result[i][4]])
                    dates.append([result[i][3]])
                else:
                    something += result[i][
                        4]  # заполняется значение иных категорий, не выбранных пользователем
            else:
                data[labels.index(category)].append(result[i][4])
                dates[labels.index(category)].append(result[i][3])
        con.close()

        if something != 0 and data:
            data.append([something])
            labels.append("Иное")

        return data, labels, dates

    def get_users_data(
            self):  # функция для получения необходимой для нас информации для построения диаграммы
        list_categories = []
        for i in range(self.listWidget.count()):
            list_item = self.listWidget.item(i)
            if list_item.checkState():
                list_categories.append(list_item.text())
        first_date = self.dateEdit.date()  # возвращает объект типа QDate
        last_date = self.dateEdit_2.date()  # возвращает объект типа QDate
        diagram = self.comboBox.currentIndex()  # индекс графика
        return first_date.year(), first_date.month(), first_date.day(), \
               last_date.year(), last_date.month(), last_date.day(), \
               diagram, list_categories  # раскладываем даты на три составляющих для дальнейших операций с ними

    def get_id(self):
        return self.userId

    def set_id(self, id):
        self.userId = id


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main = GraphWidget()
    main.show()
    sys.excepthook = except_hook
    sys.exit(app.exec_())
