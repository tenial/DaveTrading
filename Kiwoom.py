import sys
from PyQt4.QtGui import *
from PyQt4.QtCore import *
from PyQt4.QAxContainer import *
import time

class Kiwoom(QAxWidget):

    def __init__(self):
        super().__init__()
        self.setControl("KHOPENAPI.KHOpenAPICtrl.1")

        self.connect(self, SIGNAL("OnEventConnect(int)"), self.OnEventConnect)
        self.connect(self, SIGNAL("OnReceiveTrData(QString, QString, QString, QString, QString, int, QString, \
                                   QString, QString)"), self.OnReceiveTrData)
        self.connect(self, SIGNAL("OnReceiveChejanData(QString, int, QString)"), self.OnReceiveChejanData)
        self.connect(self, SIGNAL("OnReceiveMsg(QString, QString, QString, QString)"), self.OnReceiveMsg)

    def OnReceiveMsg(self, ScrNo, RQName, TrCode, Msg):
        print("ScrNo:" + ScrNo + "RQName:" + RQName + "TrCode:" + TrCode + "Msg:" + Msg)

    def init_opw00018_data(self):
        self.data_opw00018 = {'single': [], 'multi': []}

    def CommConnect(self):
        self.dynamicCall("CommConnect()")

        self.login_event_loop = QEventLoop()
        self.login_event_loop.exec_()

    def OnEventConnect(self, errCode):
        if errCode == 0:
            print("connected")
        else:
            print("disconnected")
        self.login_event_loop.exit()

    def SetInputValue(self, sID, sValue):
        self.dynamicCall("SetInputValue(QString, QString)", sID, sValue)

    def CommRqData(self, sRQName, sTRCode, nPrevNext, sScreenNo):
        self.dynamicCall("CommRqData(QString, QString, int, QString)", sRQName, sTRCode, nPrevNext, sScreenNo)

        self.tr_event_loop = QEventLoop()
        self.tr_event_loop.exec_()

    def CommGetData(self, sJongmokCode, sRealType, sFieldName, nIndex, sInnerFiledName):
        data = self.dynamicCall("CommGetData(QString, QString, QString, int, QString)", sJongmokCode, sRealType,
                                sFieldName, nIndex, sInnerFiledName)
        return data.strip()

    def OnReceiveTrData(self, ScrNo, RQName, TrCode, RecordName, PrevNext, DataLength, ErrorCode, Message, SplmMsg):
        self.prev_next = PrevNext
        print("OnReceiveTrData:" + RQName)
        if RQName == "주식기본정보":
            self.basic_info_code = []
            self.dynamicCall('GetRepeatCnt(QString, QString)', TrCode, RecordName)
            cur_price = self.dynamicCall('CommGetData(QString, QString, QString, int, QString)', TrCode, "", RecordName,
                                         0, "현재가")
            compare_price_yesterday = self.dynamicCall('CommGetData(QString, QString, QString, int, QString)', TrCode,
                                                       "", RecordName, 0, "전일대비")
            rate_price_yesterday = self.dynamicCall('CommGetData(QString, QString, QString, int, QString)', TrCode, "",
                                                    RecordName, 0, "등락율")
            self.basic_info_code.append(cur_price.strip())
            self.basic_info_code.append(compare_price_yesterday.strip())
            self.basic_info_code.append(rate_price_yesterday.strip())

        if RQName == "주식주문":
            volume = self.CommGetData(TrCode, "", RQName, 0, "주문번호")
            print("주식주문번호:" + volume)

        if RQName == "실시간미체결":
            self.order_data = []
            for i in range(self.GetRepeatCnt(TrCode, RQName)):
                data = [self.CommGetData(TrCode, "", RQName, i, "종목명"),
                        self.CommGetData(TrCode, "", RQName, i, "종목코드"),
                        self.CommGetData(TrCode, "", RQName, i, "주문가격"),
                        self.CommGetData(TrCode, "", RQName, i, "체결량"),
                        self.CommGetData(TrCode, "", RQName, i, "미체결수량"),
                        self.CommGetData(TrCode, "", RQName, i, "주문번호")]
                self.order_data.append(data)

        if RQName == "opt10081_req":
            cnt = self.GetRepeatCnt(TrCode, RQName)

            for i in range(cnt):
                date = self.CommGetData(TrCode, "", RQName, i, "일자")
                open = self.CommGetData(TrCode, "", RQName, i, "시가")
                high = self.CommGetData(TrCode, "", RQName, i, "고가")
                low = self.CommGetData(TrCode, "", RQName, i, "저가")
                close = self.CommGetData(TrCode, "", RQName, i, "현재가")
                volume = self.CommGetData(TrCode, "", RQName, i, "거래량")

                self.ohlcv['date'].append(date)
                self.ohlcv['open'].append(int(open))
                self.ohlcv['high'].append(int(high))
                self.ohlcv['low'].append(int(low))
                self.ohlcv['close'].append(int(close))
                self.ohlcv['volume'].append(int(volume))

        if RQName == "opw00001_req":
            estimated_day2_deposit = self.CommGetData(TrCode, "", RQName, 0, "d+2추정예수금")
            estimated_day2_deposit = self.change_format(estimated_day2_deposit)
            self.data_opw00001 = estimated_day2_deposit

        if RQName == "opw00018_req":
            # Single Data
            single = []

            total_purchase_price = self.CommGetData(TrCode, "", RQName, 0, "총매입금액")
            total_purchase_price = self.change_format(total_purchase_price)
            single.append(total_purchase_price)

            total_eval_price = self.CommGetData(TrCode, "", RQName, 0, "총평가금액")
            total_eval_price = self.change_format(total_eval_price)
            single.append(total_eval_price)

            total_eval_profit_loss_price = self.CommGetData(TrCode, "", RQName, 0, "총평가손익금액")
            total_eval_profit_loss_price = self.change_format(total_eval_profit_loss_price)
            single.append(total_eval_profit_loss_price)

            total_earning_rate = self.CommGetData(TrCode, "", RQName, 0, "총수익률(%)")
            total_earning_rate = self.change_format(total_earning_rate, 1)
            single.append(total_earning_rate)

            estimated_deposit = self.CommGetData(TrCode, "", RQName, 0, "추정예탁자산")
            estimated_deposit = self.change_format(estimated_deposit)
            single.append(estimated_deposit)

            self.data_opw00018['single'] = single

            # Multi Data
            cnt = self.GetRepeatCnt(TrCode, RQName)
            for i in range(cnt):
                data = [self.CommGetData(TrCode, "", RQName, i, "종목명"),
                        self.CommGetData(TrCode, "", RQName, i, "종목번호"),
                        self.change_format(self.CommGetData(TrCode, "", RQName, i, "보유수량")),
                        self.change_format(self.CommGetData(TrCode, "", RQName, i, "매입가")),
                        self.change_format(self.CommGetData(TrCode, "", RQName, i, "현재가")),
                        self.change_format(self.CommGetData(TrCode, "", RQName, i, "평가손익")),
                        self.change_format(self.CommGetData(TrCode, "", RQName, i, "수익률(%)"), 2)]
                self.data_opw00018['multi'].append(data)
        try:
            self.tr_event_loop.exit()
        except AttributeError:
            pass

    def OnReceiveChejanData(self, sGubun, nItemCnt, sFidList):
        print("sGubun: ", sGubun)
        print(self.GetChejanData(9203))
        print(self.GetChejanData(302))
        print(self.GetChejanData(900))
        print(self.GetChejanData(901))

    def GetRepeatCnt(self, sTrCode, sRecordName):
        ret = self.dynamicCall("GetRepeatCnt(QString, QString)", sTrCode, sRecordName)
        return ret

    def GetCodeListByMarket(self, sMarket):
        cmd = 'GetCodeListByMarket("%s")' % sMarket
        ret = self.dynamicCall(cmd)
        item_codes = ret.split(';')
        return item_codes

    def OnReceiveChejanData(self, sGubun, nItemCnt, sFidList):
        print(self.GetChejanData(9203))
        print(self.GetChejanData(302))
        print(self.GetChejanData(900))
        print(self.GetChejanData(901))

    def GetMasterCodeName(self, strCode):
        cmd = 'GetMasterCodeName("%s")' % strCode
        ret = self.dynamicCall(cmd)
        return ret

    def GetConnectState(self):
        ret = self.dynamicCall("GetConnectState()")
        return ret

    def GetLoginInfo(self, sTag):
        cmd = 'GetLoginInfo("%s")' % sTag
        ret = self.dynamicCall(cmd)
        return ret

    def GetChejanData(self, nFid):
        cmd = 'GetChejanData("%s")' % nFid
        ret = self.dynamicCall(cmd)
        return ret

    def SendOrder(self, sRQName, sScreenNo, sAccNo, nOrderType, sCode, nQty, nPrice, sHogaGb, sOrgOrderNo):
        ret = self.dynamicCall("SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
                               [sRQName, sScreenNo, sAccNo, nOrderType, sCode, nQty, nPrice, sHogaGb, sOrgOrderNo])
        return ret

    def InitOHLCRawData(self):
        self.ohlcv = {'date': [], 'open': [], 'high': [], 'low': [], 'close': [], 'volume': []}

    def change_format(self, data, percent=0):
        is_minus = False

        if data.startswith('-'):
            is_minus = True

        strip_str = data.lstrip('-0')

        if strip_str == '':
            if percent == 1:
                return '0.00'
            else:
                return '0'

        if percent == 1:
            strip_data = int(strip_str)
            strip_data = strip_data / 100
            form = format(strip_data, ',.2f')
        elif percent == 2:
            strip_data = float(strip_str)
            form = format(strip_data, ',.2f')
        else:
            strip_data = int(strip_str)
            form = format(strip_data, ',d')

        if form.startswith('.'):
            form = '0' + form
        if is_minus:
            form = '-' + form

        return form
