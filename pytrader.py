# -*-coding: utf-8 -*-
import sqlite3
from datetime import date
from PyQt4 import uic
from Kiwoom import *

class MyWindow (QMainWindow, uic.loadUiType("Cultivator.ui")[0]):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        # Connect to Kiwoom
        self.kiwoom_func_set = Kiwoom()
        self.kiwoom_func_set.CommConnect()

        # Check Connection Every 1 Second
        self.conn_timer = QTimer(self)
        self.conn_timer.start(1000)
        self.conn_timer.timeout.connect(self.func_check_conn)

        # Get Account Number
        accounts_num = int(self.kiwoom_func_set.GetLoginInfo("ACCOUNT_CNT"))
        accounts = self.kiwoom_func_set.GetLoginInfo("ACCNO")
        accounts_list = accounts.split(';')[0:accounts_num]
        self.comboBox.addItems(accounts_list)

        # Connect check_balance func with ButtonBalanceReq
        self.ButtonBalanceReq.clicked.connect(self.check_balance)
        self.CheckBoxBalanceUpdate.stateChanged.connect(self.func_check_balance_req)
        self.ButtonOrder.clicked.connect(self.stock_order)
        self.ButtonBalanceReq_5.clicked.connect(self.check_order)
        self.conduct_buy_sell()

        # Test Function: Add data to Database directly
        # self.func_test_list()
        self.load_list()

        # Connect signal for item change
        self.RequestTable.itemChanged.connect(self.add_code)

    def load_list(self):
        # Get list from DB
        davedb = sqlite3.connect("davedb.db")
        davedb.isolation_level = None
        davedb_cursor = davedb.cursor()
        davedb_cursor.execute("SELECT * FROM DaveDBTable")

        row_list = davedb_cursor.fetchall()
        self.RequestTable.setRowCount(len(row_list) + 1)
        self.RequestTable.horizontalHeader().setResizeMode(0, QHeaderView.Stretch)

        # Set Table Header
        self.RequestTable.setColumnCount(16)
        column_headers = ['종목명', '종목코드', '현가격',
                          '1차매수가', '1차매수량', '2차매수가', '2차매수량', '3차매수가', '3차매수량',
                          '4차매수가', '4차매수량', '1차매도가', '1차매도량', '2차매도가', '2차매도량', '종목제외']
        self.RequestTable.setHorizontalHeaderLabels(column_headers)
        for i in range(16):
            self.RequestTable.setColumnWidth(i, 80)
        self.RequestTable.setColumnWidth(0, 120)
        self.RequestTable.setColumnWidth(1, 60)
        self.RequestTable.setColumnWidth(2, 110)

        # Set list and adding row
        self.set_list(row_list)
        self.set_add_row(row_list)
        self.RequestTable.resizeRowsToContents()

    def add_code(self, item):
        row = item.row()
        col = item.column()

        # Check code item
        if col == 1:
            # Check available code
            if len(self.RequestTable.item(row, col).text()) == 6 and self.RequestTable.item(row,
                                                                                            col).text().isnumeric():
                code_name = self.kiwoom_func_set.GetMasterCodeName(self.RequestTable.item(row, col).text())
                if code_name != "":
                    self.RequestTable.blockSignals(True)
                    self.update_code_name(code_name, row)
                    self.set_price(self.RequestTable.item(row, col).text(), 0, row)
                    self.RequestTable.blockSignals(False)
                    return
                else:
                    self.RequestTable.blockSignals(True)
                    self.RequestTable.setItem(row, col, QTableWidgetItem())
                    self.RequestTable.item(row, col).setTextAlignment(Qt.AlignVCenter | Qt.AlignCenter)
                    self.RequestTable.item(row, col).setBackground(QColor('#FFF9C4'))
                    self.RequestTable.blockSignals(False)
                    QMessageBox.about(self, "알림", "입력한 종목코드는 유효하지 않습니다.")
                    return
            elif len(self.RequestTable.item(row, col).text()) == 0:
                return
            else:
                self.RequestTable.blockSignals(True)
                self.RequestTable.setItem(row, col, QTableWidgetItem())
                self.RequestTable.item(row, col).setTextAlignment(Qt.AlignVCenter | Qt.AlignCenter)
                self.RequestTable.item(row, col).setBackground(QColor('#FFF9C4'))
                self.RequestTable.blockSignals(False)
                QMessageBox.about(self, "알림", "종목코드는 6자리 숫자값입니다.")
                return
        elif col == 3:
            if self.RequestTable.item(row, col).text().isnumeric() and int(self.RequestTable.item(row, col).text()) > 0:
                self.RequestTable.blockSignals(True)
                self.set_price(self.RequestTable.item(row, 1).text(), self.RequestTable.item(row, col).text(), row)
                self.update_db(row)
                self.RequestTable.blockSignals(False)
                return
            elif len(self.RequestTable.item(row, 4).text()) == 0:
                return
            else:
                self.RequestTable.setItem(row, col, QTableWidgetItem())
                self.RequestTable.item(row, col).setTextAlignment(Qt.AlignVCenter | Qt.AlignCenter)
                self.RequestTable.item(row, col).setBackground(QColor('#FFF9C4'))
                QMessageBox.about(self, "알림", "매수희망가격은 숫자입니다.")
                return
        elif 3 < col < 15:
            if self.RequestTable.item(row, col).text().isnumeric() and int(self.RequestTable.item(row, col).text()) > 0:
                self.RequestTable.blockSignals(True)
                self.RequestTable.setItem(row, col, QTableWidgetItem(self.RequestTable.item(row, col).text()))
                self.RequestTable.item(row, col).setTextAlignment(Qt.AlignVCenter | Qt.AlignCenter)
                self.RequestTable.item(row, col).setBackground(QColor('#FFF9C4'))
                self.RequestTable.blockSignals(False)
                self.update_db(row)
                return
            else:
                self.RequestTable.blockSignals(True)
                self.RequestTable.setItem(row, col, QTableWidgetItem())
                self.RequestTable.item(row, col).setTextAlignment(Qt.AlignVCenter | Qt.AlignCenter)
                self.RequestTable.item(row, col).setBackground(QColor('#FFF9C4'))
                self.RequestTable.blockSignals(False)
                QMessageBox.about(self, "알림", "숫자로 입력하세요.")
                return

    def update_code_name(self, code_name, row_num):
        code_name_item = QTableWidgetItem(code_name)
        code_name_item.setTextAlignment(Qt.AlignVCenter | Qt.AlignCenter)
        self.RequestTable.setItem(row_num, 0, code_name_item)
        self.RequestTable.item(row_num, 0).setFlags(Qt.ItemIsEnabled)
        self.RequestTable.item(row_num, 0).setBackground(QColor('#ECEFF1'))

    def func_check_balance_req(self):
        if self.checkBox.isChecked():
            # Check Balance Update Request Every 12 Seconds
            self.BalanceTimer = QTimer(self)
            self.BalanceTimer.start(1000 * 12)
            self.BalanceTimer.timeout.connect(self.check_balance)
        else:
            # Stop Balance Update Every 12 Seconds
            self.BalanceTimer.stop()

    def func_check_conn(self):
        current_time = QTime.currentTime()
        text_time = current_time.toString("hh:mm:ss")
        time_msg = "현재시간: " + text_time

        state = self.kiwoom_func_set.GetConnectState()
        if state == 1:
            state_msg = "서버 연결 중"
        else:
            state_msg = "서버 미 연결 중"
        self.statusbar.showMessage(state_msg + " | " + time_msg)

    def func_test_list(self):
        # Connect DataBase
        # CREATE TABLE `DaveDBTable` (`StockCode` TEXT, `IdealPrice` INTEGER, `OrderPriority` INTEGER, `Possession` TEXT)
        davedb = sqlite3.connect("davedb.db")
        davedb.isolation_level = None

        davedb_cursor = davedb.cursor()
        davedb_cursor.execute("INSERT INTO DaveDBTable VALUES('087600', 15000, 1);")
        davedb_cursor.execute("INSERT INTO DaveDBTable VALUES('058220', 5500, 2);")
        # davedb_cursor.execute("DELETE FROM DaveDBTable where StockCode=?", ('058220', ))
        # davedb_cursor.execute("UPDATE DaveDBTable set OrderPriority=? where StockCode=?", (3, '058220'))
        davedb_cursor.execute("SELECT * FROM DaveDBTable")
        davedb.close()

    def stock_order(self):
        # Get list from DB
        davedb = sqlite3.connect("davedb.db")
        davedb.isolation_level = None
        davedb_cursor = davedb.cursor()
        davedb_cursor.execute("SELECT * FROM DaveDBTable")

        row_list = davedb_cursor.fetchall()
        self.check_status(row_list)

    def check_status(self, row_list):
        self.kiwoom_func_set.init_opw00018_data()

        # Request opw00018
        self.kiwoom_func_set.SetInputValue("계좌번호", "8082829111")
        self.kiwoom_func_set.SetInputValue("비밀번호", "0000")
        self.kiwoom_func_set.CommRqData("opw00018_req", "opw00018", 0, "2000")

        while self.kiwoom_func_set.prev_next == '2':
            time.sleep(0.2)
            self.kiwoom_func_set.SetInputValue("계좌번호", "8082829111")
            self.kiwoom_func_set.SetInputValue("비밀번호", "0000")
            self.kiwoom_func_set.CommRqData("opw00018_req", "opw00018", 2, "2000")

        # Request opw00001
        self.kiwoom_func_set.SetInputValue("계좌번호", "8082829111")
        self.kiwoom_func_set.SetInputValue("비밀번호", "0000")
        self.kiwoom_func_set.CommRqData("opw00001_req", "opw00001", 0, "2000")

        # Item list
        item_count = len(self.kiwoom_func_set.data_opw00018['multi'])
        list_record_order = False
        for i, ListRecords in enumerate(row_list):
            for j in range(item_count):
                row = self.kiwoom_func_set.data_opw00018['multi'][j]
                list_record_order = False
                if ListRecords[1] == row[1].lstrip("A "):
                    list_record_order = True
                    self.make_order_by_plan(int(row[2]), ListRecords)
            if list_record_order is False:
                self.make_order_by_plan(0, ListRecords)

    def request_stock_order(self, code, price, volume, order_type):
        print("request_stock_order", code, price, volume, order_type)
        if volume > 0:
            account = self.comboBox.currentText()
            ret = self.kiwoom_func_set.SendOrder("주식주문", "0101", account, order_type, code, volume, price, "00", "")
            print(ret)

    def make_order_by_plan(self, curr_hold_volume, plan_data):
        print(str(plan_data[14]).strip(), str(date.today()).strip())
        if str(plan_data[14]).strip() == str(date.today()).strip():
            order_volume = [0, 0, 0, 0]
            hold_volume = curr_hold_volume
            for i in range(0, 4):
                if hold_volume > 0:
                    order_volume[i] = plan_data[i * 2 + 3] - hold_volume
                    hold_volume = hold_volume - plan_data[i * 2 + 3]
                else:
                    order_volume[i] = plan_data[i * 2 + 3]
                self.request_stock_order(plan_data[1], plan_data[i * 2 + 2], order_volume[i], 1)

            self.request_stock_order(plan_data[1], plan_data[10], int(curr_hold_volume * plan_data[11] / 100), 2)
            self.request_stock_order(plan_data[1], plan_data[12], int(curr_hold_volume * plan_data[13] / 100), 2)
            self.update_db_order_date(plan_data[1])

    def set_list(self, row_list):
        for j, ListRecords in enumerate(row_list):
            item = QTableWidgetItem(ListRecords[0])
            item.setTextAlignment(Qt.AlignVCenter | Qt.AlignCenter)
            self.RequestTable.setItem(j, 0, item)
            self.RequestTable.item(j, 0).setFlags(Qt.ItemIsEnabled)
            self.RequestTable.item(j, 0).setBackground(QColor('#ECEFF1'))

            item = QTableWidgetItem(ListRecords[1])
            item.setTextAlignment(Qt.AlignVCenter | Qt.AlignCenter)
            self.RequestTable.setItem(j, 1, item)
            self.RequestTable.item(j, 1).setFlags(Qt.ItemIsEnabled)
            self.RequestTable.item(j, 1).setBackground(QColor('#ECEFF1'))

            self.set_price(ListRecords[1], ListRecords[2], j)

            for col_num in range(3, 15):
                item = QTableWidgetItem(str(ListRecords[col_num - 1]))
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignCenter)
                self.RequestTable.setItem(j, col_num, item)
                self.RequestTable.item(j, col_num).setBackground(QColor('#FFF9C4'))

            self.button_remove_list = QPushButton('제외')
            self.button_remove_list.clicked.connect(self.handle_button_remove_clicked)
            self.RequestTable.setCellWidget(j, 15, self.button_remove_list)

    def set_price(self, code_num, expected_price, row_num):
        # Request 주식기본정보
        self.kiwoom_func_set.SetInputValue("종목코드", code_num)
        self.kiwoom_func_set.CommRqData("주식기본정보", "OPT10001", 0, "0101")

        curr_price = self.kiwoom_func_set.basic_info_code[0].lstrip("+- ")
        diff_price = int(curr_price) - int(expected_price)

        if diff_price == 0:
            item = QTableWidgetItem(curr_price + "(0)")
            item.setTextAlignment(Qt.AlignVCenter | Qt.AlignCenter)
            pass
        elif diff_price > 0:
            item = QTableWidgetItem(curr_price + "(+" + str(diff_price) + ")")
            item.setTextAlignment(Qt.AlignVCenter | Qt.AlignCenter)
            curr_price_set_font = QFont()
            curr_price_set_font.setBold(True)
            item.setFont(curr_price_set_font)
            item.setTextColor(QColor('#F44336'))
        else:
            item = QTableWidgetItem(curr_price + "(" + str(diff_price) + ")")
            item.setTextAlignment(Qt.AlignVCenter | Qt.AlignCenter)
            curr_price_set_font = QFont()
            curr_price_set_font.setBold(True)
            item.setFont(curr_price_set_font)
            item.setTextColor(QColor('#2196F3'))
        self.RequestTable.setItem(row_num, 2, item)
        self.RequestTable.item(row_num, 2).setFlags(Qt.ItemIsEnabled)
        self.RequestTable.item(row_num, 2).setBackground(QColor('#ECEFF1'))

        self.set_expected_price(code_num, expected_price, row_num)

    def set_expected_price(self, code_num, expected_price_str, row_num):
        expected_price = int(expected_price_str)
        buy_rule_amount = [1000000, 1000000, 2000000, 4000000]
        buy_rule_rate = [0, 20, 40, 60]
        sell_rule_amount_rate = [50, 50]
        sell_rule_rate = [10, 20]

        if expected_price == 0:
            for col_num in range(2, 14):
                item = QTableWidgetItem()
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignCenter)
                self.RequestTable.setItem(row_num, col_num + 1, item)
                self.RequestTable.item(row_num, col_num + 1).setBackground(QColor('#FFF9C4'))
        else:
            # set buying plan
            for buy_rule_num in range(0, 4):
                item = QTableWidgetItem(str(int(expected_price - (expected_price * buy_rule_rate[buy_rule_num] / 100))))
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignCenter)
                self.RequestTable.setItem(row_num, (buy_rule_num * 2) + 3, item)
                self.RequestTable.item(row_num, (buy_rule_num * 2) + 3).setBackground(QColor('#FFF9C4'))

                item = QTableWidgetItem(str(int(buy_rule_amount[buy_rule_num] / (
                expected_price - (expected_price * buy_rule_rate[buy_rule_num]) / 100))))
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignCenter)
                self.RequestTable.setItem(row_num, (buy_rule_num * 2) + 4, item)
                self.RequestTable.item(row_num, (buy_rule_num * 2) + 4).setBackground(QColor('#FFF9C4'))

            # set selling plan
            for sell_rule_num in range(0, 2):
                item = QTableWidgetItem(
                    str(int(expected_price + (expected_price * sell_rule_rate[sell_rule_num] / 100))))
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignCenter)
                self.RequestTable.setItem(row_num, (sell_rule_num * 2) + 11, item)
                self.RequestTable.item(row_num, (sell_rule_num * 2) + 11).setBackground(QColor('#FFF9C4'))

                item = QTableWidgetItem(
                    str(str(int(sell_rule_amount_rate[sell_rule_num] * 100 / 100))))
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignCenter)
                self.RequestTable.setItem(row_num, (sell_rule_num * 2) + 12, item)
                self.RequestTable.item(row_num, (sell_rule_num * 2) + 12).setBackground(QColor('#FFF9C4'))

    def set_add_row(self, row_list):
        for col_num in range(0, 15):
            self.RequestTable.setItem(len(row_list), col_num, QTableWidgetItem())
            self.RequestTable.item(len(row_list), col_num).setFlags(Qt.ItemIsEnabled)
            self.RequestTable.item(len(row_list), col_num).setTextAlignment(Qt.AlignVCenter | Qt.AlignCenter)
            self.RequestTable.item(len(row_list), col_num).setBackground(QColor('#ECEFF1'))

        self.RequestTable.setItem(len(row_list), 1, QTableWidgetItem())
        self.RequestTable.item(len(row_list), 1).setTextAlignment(Qt.AlignVCenter | Qt.AlignCenter)
        self.RequestTable.item(len(row_list), 1).setBackground(QColor('#FFF9C4'))

        self.button_add_list = QPushButton('추가')
        self.button_add_list.clicked.connect(self.handle_button_add_clicked)
        self.RequestTable.setCellWidget(len(row_list), 15, self.button_add_list)

    def update_db_order_date(self, code):
        davedb = sqlite3.connect("davedb.db")
        davedb.isolation_level = None
        davedb_cursor = davedb.cursor()
        davedb_update_sql = "UPDATE DaveDBTable SET OrderDate = ? WHERE StockCode= ?"

        try:
            davedb_cursor.execute(
                davedb_update_sql, (date.today(), code))
        except sqlite3.IntegrityError:
            QMessageBox.about(self, "알림", "동일한 종목코드가 존재합니다.")
            return

    def update_db(self, row_num):
        if self.RequestTable.item(row_num, 1) is None or self.RequestTable.item(row_num, 1).text() == "":
            QMessageBox.about(self, "알림", "종목코드가 입력되지 않았습니다.")
            return
        if self.RequestTable.item(row_num, 3) is None or self.RequestTable.item(row_num, 3).text() == "":
            QMessageBox.about(self, "알림", "희망매수가격이 입력되지 않았습니다.")
            return

        davedb = sqlite3.connect("davedb.db")
        davedb.isolation_level = None
        davedb_cursor = davedb.cursor()

        davedb_update_sql = "UPDATE DaveDBTable SET FirstBuyPrice = ?, "
        davedb_update_sql = davedb_update_sql + "FirstBuyNum = ?, "
        davedb_update_sql = davedb_update_sql + "SecondBuyPrice = ?, "
        davedb_update_sql = davedb_update_sql + "SecondBuyNum = ?, "
        davedb_update_sql = davedb_update_sql + "ThirdBuyPrice = ?, "
        davedb_update_sql = davedb_update_sql + "ThirdBuyNum = ?, "
        davedb_update_sql = davedb_update_sql + "FourthBuyPrice = ?, "
        davedb_update_sql = davedb_update_sql + "FourthBuyNum = ?, "
        davedb_update_sql = davedb_update_sql + "FirstSellPrice = ?, "
        davedb_update_sql = davedb_update_sql + "FirstSellNum = ?, "
        davedb_update_sql = davedb_update_sql + "SecondSellPrice = ?, "
        davedb_update_sql = davedb_update_sql + "SecondSellNum = ? "
        davedb_update_sql = davedb_update_sql + "WHERE StockCode= ?"

        try:
            davedb_cursor.execute(
                davedb_update_sql, (
                    self.RequestTable.item(row_num, 3).text(),
                    self.RequestTable.item(row_num, 4).text(),
                    self.RequestTable.item(row_num, 5).text(),
                    self.RequestTable.item(row_num, 6).text(),
                    self.RequestTable.item(row_num, 7).text(),
                    self.RequestTable.item(row_num, 8).text(),
                    self.RequestTable.item(row_num, 9).text(),
                    self.RequestTable.item(row_num, 10).text(),
                    self.RequestTable.item(row_num, 11).text(),
                    self.RequestTable.item(row_num, 12).text(),
                    self.RequestTable.item(row_num, 13).text(),
                    self.RequestTable.item(row_num, 14).text(),
                    self.RequestTable.item(row_num, 1).text()
                ))
        except sqlite3.IntegrityError:
            QMessageBox.about(self, "알림", "동일한 종목코드가 존재합니다.")
            return

    def handle_button_remove_clicked(self):
        button = self.sender()
        index = self.RequestTable.indexAt(button.pos())

        davedb = sqlite3.connect("davedb.db")
        davedb.isolation_level = None
        davedb_cursor = davedb.cursor()
        try:
            davedb_cursor.execute("DELETE FROM DaveDBTable where StockCode=?",
                                  (self.RequestTable.item(index.row(), 1).text(),))
        except:
            QMessageBox.about(self, "알림", "동일한 종목코드가 존재합니다.")
            return

        self.RequestTable.removeRow(index.row())

    def handle_button_add_clicked(self):
        row_count = self.RequestTable.rowCount() - 1
        if self.RequestTable.item(row_count, 1) is None or self.RequestTable.item(row_count, 1).text() == "":
            QMessageBox.about(self, "알림", "종목코드가 입력되지 않았습니다.")
            return
        if self.RequestTable.item(row_count, 3) is None or self.RequestTable.item(row_count, 3).text() == "":
            QMessageBox.about(self, "알림", "희망매수가격이 입력되지 않았습니다.")
            return

        davedb = sqlite3.connect("davedb.db")
        davedb.isolation_level = None
        davedb_cursor = davedb.cursor()
        try:
            davedb_cursor.execute("INSERT INTO DaveDBTable VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);", (
                self.RequestTable.item(row_count, 0).text(),
                self.RequestTable.item(row_count, 1).text(),
                self.RequestTable.item(row_count, 3).text(),
                self.RequestTable.item(row_count, 4).text(),
                self.RequestTable.item(row_count, 5).text(),
                self.RequestTable.item(row_count, 6).text(),
                self.RequestTable.item(row_count, 7).text(),
                self.RequestTable.item(row_count, 8).text(),
                self.RequestTable.item(row_count, 9).text(),
                self.RequestTable.item(row_count, 10).text(),
                self.RequestTable.item(row_count, 11).text(),
                self.RequestTable.item(row_count, 12).text(),
                self.RequestTable.item(row_count, 13).text(),
                self.RequestTable.item(row_count, 14).text(),
                ''
            ))
        except sqlite3.IntegrityError:
            QMessageBox.about(self, "알림", "동일한 종목코드가 존재합니다.")
            return

        self.RequestTable.blockSignals(True)
        self.load_list()
        self.RequestTable.blockSignals(False)

    def check_order(self):
        self.kiwoom_func_set.SetInputValue("계좌번호", "8082829111")
        self.kiwoom_func_set.SetInputValue("체결구분", "0")
        self.kiwoom_func_set.SetInputValue("매매구분", "0")
        self.kiwoom_func_set.CommRqData("실시간미체결", "opt10075", 0, "2000")

        # Item list
        item_count = len(self.kiwoom_func_set.order_data)
        self.OrderTable.setRowCount(item_count)

        for j in range(item_count):
            row = self.kiwoom_func_set.order_data[j]
            for i in range(len(row)):
                item = QTableWidgetItem(row[i])
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignCenter)
                self.OrderTable.setItem(j, i, item)

        self.OrderTable.resizeRowsToContents()

    def func_test_check_order(self):
        self.kiwoom_func_set.init_opw00018_data()
        self.request_stock_order("058220", 6100, 30, 1)

    def check_balance(self):
        self.kiwoom_func_set.init_opw00018_data()

        # Request opw00018
        self.kiwoom_func_set.SetInputValue("계좌번호", "8082829111")
        self.kiwoom_func_set.SetInputValue("비밀번호", "0000")
        self.kiwoom_func_set.CommRqData("opw00018_req", "opw00018", 0, "2000")

        while self.kiwoom_func_set.prev_next == '2':
            time.sleep(0.2)
            self.kiwoom_func_set.SetInputValue("계좌번호", "8082829111")
            self.kiwoom_func_set.SetInputValue("비밀번호", "0000")
            self.kiwoom_func_set.CommRqData("opw00018_req", "opw00018", 2, "2000")

        # Request opw00001
        self.kiwoom_func_set.SetInputValue("계좌번호", "8082829111")
        self.kiwoom_func_set.SetInputValue("비밀번호", "0000")
        self.kiwoom_func_set.CommRqData("opw00001_req", "opw00001", 0, "2000")

        # balance
        item = QTableWidgetItem(self.kiwoom_func_set.data_opw00001)
        item.setTextAlignment(Qt.AlignVCenter | Qt.AlignCenter)
        self.tableWidget.setItem(0, 0, item)

        for i in range(1, 6):
            item = QTableWidgetItem(self.kiwoom_func_set.data_opw00018['single'][i - 1])
            item.setTextAlignment(Qt.AlignVCenter | Qt.AlignCenter)
            self.tableWidget.setItem(0, i, item)
        self.tableWidget.resizeRowsToContents()

        # Item list
        item_count = len(self.kiwoom_func_set.data_opw00018['multi'])
        self.tableWidget_2.setRowCount(item_count)
        for j in range(item_count):
            row = self.kiwoom_func_set.data_opw00018['multi'][j]
            for i in range(len(row)):
                item = QTableWidgetItem(row[i])
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignCenter)
                self.tableWidget_2.setItem(j, i, item)
        self.tableWidget_2.resizeRowsToContents()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindow = MyWindow()
    myWindow.show()
    app.exec_()
