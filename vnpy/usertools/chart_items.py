from datetime import datetime
from typing import List, Tuple, Dict

from vnpy.trader.ui import create_qapp, QtCore, QtGui, QtWidgets
from pyqtgraph import ScatterPlotItem
import pyqtgraph as pg
import numpy as np
import talib
import copy

from vnpy.chart import ChartWidget, VolumeItem, CandleItem
from vnpy.chart.item import ChartItem
from vnpy.chart.manager import BarManager

from vnpy.trader.object import (
    BarData,
    OrderData,
    TradeData
)

from vnpy.trader.object import Direction, Exchange, Interval, Offset, Status, Product, OptionType, OrderType

from collections import OrderedDict
import pytz
CHINA_TZ = pytz.timezone("Asia/Shanghai")


class LineItem(CandleItem):
    """"""

    def __init__(self, manager: BarManager):
        """"""
        super().__init__(manager)

        self.white_pen: QtGui.QPen = pg.mkPen(color=(255, 255, 255), width=1)

    def _draw_bar_picture(self, ix: int, bar: BarData) -> QtGui.QPicture:
        """"""
        last_bar = self._manager.get_bar(ix - 1)

        # Create objects
        picture = QtGui.QPicture()
        painter = QtGui.QPainter(picture)

        # Set painter color
        painter.setPen(self.white_pen)

        # Draw Line
        end_point = QtCore.QPointF(ix, bar.close_price)

        if last_bar:
            start_point = QtCore.QPointF(ix - 1, last_bar.close_price)
        else:
            start_point = end_point

        painter.drawLine(start_point, end_point)

        # Finish
        painter.end()
        return picture

    def get_info_text(self, ix: int) -> str:
        """"""
        text = ""
        bar = self._manager.get_bar(ix)
        if bar:
            text = f"Close:{bar.close_price}"
        return text

class SmaItem(CandleItem):
    """"""

    def __init__(self, manager: BarManager):
        """"""
        super().__init__(manager)

        self.blue_pen: QtGui.QPen = pg.mkPen(color=(100, 100, 255), width=2)

        self.sma_window = 10
        self.sma_data: Dict[int, float] = {}

    def get_sma_value(self, ix: int) -> float:
        """"""
        if ix < 0:
            return 0

        # When initialize, calculate all rsi value
        if not self.sma_data:
            bars = self._manager.get_all_bars()
            close_data = [bar.close_price for bar in bars]
            sma_array = talib.SMA(np.array(close_data), self.sma_window)

            for n, value in enumerate(sma_array):
                self.sma_data[n] = value

        # Return if already calcualted
        if ix in self.sma_data:
            return self.sma_data[ix]

        # Else calculate new value
        close_data = []
        for n in range(ix - self.sma_window, ix + 1):
            bar = self._manager.get_bar(n)
            close_data.append(bar.close_price)

        sma_array = talib.SMA(np.array(close_data), self.sma_window)
        sma_value = sma_array[-1]
        self.sma_data[ix] = sma_value

        return sma_value

    def _draw_bar_picture(self, ix: int, bar: BarData) -> QtGui.QPicture:
        """"""
        sma_value = self.get_sma_value(ix)
        last_sma_value = self.get_sma_value(ix - 1)

        # Create objects
        picture = QtGui.QPicture()
        painter = QtGui.QPainter(picture)

        # Set painter color
        painter.setPen(self.blue_pen)

        # Draw Line
        start_point = QtCore.QPointF(ix-1, last_sma_value)
        end_point = QtCore.QPointF(ix, sma_value)
        painter.drawLine(start_point, end_point)

        # Finish
        painter.end()
        return picture

    def get_info_text(self, ix: int) -> str:
        """"""
        if ix in self.sma_data:
            sma_value = self.sma_data[ix]
            text = f"SMA {sma_value:.1f}"
        else:
            text = "SMA -"

        return text

class RsiItem(ChartItem):
    """"""

    def __init__(self, manager: BarManager):
        """"""
        super().__init__(manager)

        self.white_pen: QtGui.QPen = pg.mkPen(color=(255, 255, 255), width=1)
        self.yellow_pen: QtGui.QPen = pg.mkPen(color=(255, 255, 0), width=2)

        self.rsi_window = 14
        self.rsi_data: Dict[int, float] = {}

    def get_rsi_value(self, ix: int) -> float:
        """"""
        if ix < 0:
            return 50

        # When initialize, calculate all rsi value
        if not self.rsi_data:
            bars = self._manager.get_all_bars()
            close_data = [bar.close_price for bar in bars]
            rsi_array = talib.RSI(np.array(close_data), self.rsi_window)

            for n, value in enumerate(rsi_array):
                self.rsi_data[n] = value

        # Return if already calcualted
        if ix in self.rsi_data:
            return self.rsi_data[ix]

        # Else calculate new value
        close_data = []
        for n in range(ix - self.rsi_window, ix + 1):
            bar = self._manager.get_bar(n)
            close_data.append(bar.close_price)

        rsi_array = talib.RSI(np.array(close_data), self.rsi_window)
        rsi_value = rsi_array[-1]
        self.rsi_data[ix] = rsi_value

        return rsi_value

    def _draw_bar_picture(self, ix: int, bar: BarData) -> QtGui.QPicture:
        """"""
        rsi_value = self.get_rsi_value(ix)
        last_rsi_value = self.get_rsi_value(ix - 1)

        # Create objects
        picture = QtGui.QPicture()
        painter = QtGui.QPainter(picture)

        # Draw RSI line
        painter.setPen(self.yellow_pen)

        if np.isnan(last_rsi_value) or np.isnan(rsi_value):
            # print(ix - 1, last_rsi_value,ix, rsi_value,)
            pass
        else:
            end_point = QtCore.QPointF(ix, rsi_value)
            start_point = QtCore.QPointF(ix - 1, last_rsi_value)
            painter.drawLine(start_point, end_point)

        # Draw oversold/overbought line
        painter.setPen(self.white_pen)

        painter.drawLine(
            QtCore.QPointF(ix, 70),
            QtCore.QPointF(ix - 1, 70),
        )

        painter.drawLine(
            QtCore.QPointF(ix, 30),
            QtCore.QPointF(ix - 1, 30),
        )

        # Finish
        painter.end()
        return picture

    def boundingRect(self) -> QtCore.QRectF:
        """"""
        # min_price, max_price = self._manager.get_price_range()
        rect = QtCore.QRectF(
            0,
            0,
            len(self._bar_picutures),
            100
        )
        return rect

    def get_y_range( self, min_ix: int = None, max_ix: int = None) -> Tuple[float, float]:
        """  """
        return 0, 100

    def get_info_text(self, ix: int) -> str:
        """"""
        if ix in self.rsi_data:
            rsi_value = self.rsi_data[ix]
            text = f"RSI {rsi_value:.1f}"
            # print(text)
        else:
            text = "RSI -"

        return text


def to_int(value: float) -> int:
    """"""
    return int(round(value, 0))

""" 将y方向的显示范围扩大到1.1 """
def adjust_range(in_range:Tuple[float, float])->Tuple[float, float]:
    ret_range:Tuple[float, float]
    diff = abs(in_range[0] - in_range[1])
    ret_range = (in_range[0]-diff*0.05,in_range[1]+diff*0.05)
    return ret_range

class MacdItem(ChartItem):
    """"""
    _values_ranges: Dict[Tuple[int, int], Tuple[float, float]] = {}

    last_range:Tuple[int, int] = (-1,-1)    # 最新显示K线索引范围

    def __init__(self, manager: BarManager):
        """"""
        super().__init__(manager)

        self.white_pen: QtGui.QPen = pg.mkPen(color=(255, 255, 255), width=1)
        self.yellow_pen: QtGui.QPen = pg.mkPen(color=(255, 255, 0), width=1)
        self.red_pen: QtGui.QPen = pg.mkPen(color=(255, 0, 0), width=1)
        self.green_pen: QtGui.QPen = pg.mkPen(color=(0, 255, 0), width=1)

        self.short_window = 12
        self.long_window = 26
        self.M = 9

        self.macd_data: Dict[int, Tuple[float,float,float]] = {}

    def get_macd_value(self, ix: int) -> Tuple[float,float,float]:
        """"""
        if ix < 0:
            return (0.0,0.0,0.0)

        # When initialize, calculate all macd value
        if not self.macd_data:
            bars = self._manager.get_all_bars()
            close_data = [bar.close_price for bar in bars]

            diffs,deas,macds = talib.MACD(np.array(close_data),
                                    fastperiod=self.short_window,
                                    slowperiod=self.long_window,
                                    signalperiod=self.M)

            for n in range(0,len(diffs)):
                self.macd_data[n] = (diffs[n],deas[n],macds[n])

        # Return if already calcualted
        if ix in self.macd_data:
            return self.macd_data[ix]

        # Else calculate new value
        close_data = []
        for n in range(ix-self.long_window-self.M+1, ix + 1):
            bar = self._manager.get_bar(n)
            close_data.append(bar.close_price)

        diffs,deas,macds = talib.MACD(np.array(close_data),
                                            fastperiod=self.short_window,
                                            slowperiod=self.long_window,
                                            signalperiod=self.M)
        diff,dea,macd = diffs[-1],deas[-1],macds[-1]
        self.macd_data[ix] = (diff,dea,macd)

        return (diff,dea,macd)

    def _draw_bar_picture(self, ix: int, bar: BarData) -> QtGui.QPicture:
        """"""
        macd_value = self.get_macd_value(ix)
        last_macd_value = self.get_macd_value(ix - 1)

        # # Create objects
        picture = QtGui.QPicture()
        painter = QtGui.QPainter(picture)

        # # Draw macd lines
        if np.isnan(macd_value[0]) or np.isnan(last_macd_value[0]):
            # print("略过macd lines0")
            pass
        else:
            end_point0 = QtCore.QPointF(ix, macd_value[0])
            start_point0 = QtCore.QPointF(ix - 1, last_macd_value[0])
            painter.setPen(self.white_pen)
            painter.drawLine(start_point0, end_point0)

        if np.isnan(macd_value[1]) or np.isnan(last_macd_value[1]):
            # print("略过macd lines1")
            pass
        else:
            end_point1 = QtCore.QPointF(ix, macd_value[1])
            start_point1 = QtCore.QPointF(ix - 1, last_macd_value[1])
            painter.setPen(self.yellow_pen)
            painter.drawLine(start_point1, end_point1)

        if not np.isnan(macd_value[2]):
            if (macd_value[2]>0):
                painter.setPen(self.red_pen)
                painter.setBrush(pg.mkBrush(255,0,0))
            else:
                painter.setPen(self.green_pen)
                painter.setBrush(pg.mkBrush(0,255,0))
            painter.drawRect(QtCore.QRectF(ix-0.3,0,0.6,macd_value[2]))
        else:
            # print("略过macd lines2")
            pass

        painter.end()
        return picture

    def boundingRect(self) -> QtCore.QRectF:
        """"""
        min_y, max_y = self.get_y_range()
        rect = QtCore.QRectF(
            0,
            min_y,
            len(self._bar_picutures),
            max_y
        )
        return rect

    def get_y_range(self, min_ix: int = None, max_ix: int = None) -> Tuple[float, float]:
        #   获得3个指标在y轴方向的范围
        #   hxxjava 修改，2020-6-29
        #   当显示范围改变时，min_ix,max_ix的值不为None，当显示范围不变时，min_ix,max_ix的值不为None，

        offset = max(self.short_window,self.long_window) + self.M - 1

        if not self.macd_data or len(self.macd_data) < offset:
            return 0.0, 1.0

        # print("len of range dict:",len(self._values_ranges),",macd_data:",len(self.macd_data),(min_ix,max_ix))

        if min_ix != None:          # 调整最小K线索引
            min_ix = max(min_ix,offset)

        if max_ix != None:          # 调整最大K线索引
            max_ix = min(max_ix, len(self.macd_data)-1)

        last_range = (min_ix,max_ix)    # 请求的最新范围

        if last_range == (None,None):   # 当显示范围不变时
            if self.last_range in self._values_ranges:
                # 如果y方向范围已经保存
                # 读取y方向范围
                result = self._values_ranges[self.last_range]
                # print("1:",self.last_range,result)
                return adjust_range(result)
            else:
                # 如果y方向范围没有保存
                # 从macd_data重新计算y方向范围
                min_ix,max_ix = 0,len(self.macd_data)-1

                macd_list = list(self.macd_data.values())[min_ix:max_ix + 1]
                ndarray = np.array(macd_list)
                max_price = np.nanmax(ndarray)
                min_price = np.nanmin(ndarray)

                # 保存y方向范围，同时返回结果
                result = (min_price, max_price)
                self.last_range = (min_ix,max_ix)
                self._values_ranges[self.last_range] = result
                # print("2:",self.last_range,result)
                return adjust_range(result)

        """ 以下为显示范围变化时 """

        if last_range in self._values_ranges:
            # 该范围已经保存过y方向范围
            # 取得y方向范围，返回结果
            result = self._values_ranges[last_range]
            # print("3:",last_range,result)
            return adjust_range(result)

        # 该范围没有保存过y方向范围
        # 从macd_data重新计算y方向范围
        macd_list = list(self.macd_data.values())[min_ix:max_ix + 1]
        ndarray = np.array(macd_list)
        max_price = np.nanmax(ndarray)
        min_price = np.nanmin(ndarray)

        # 取得y方向范围，返回结果
        result = (min_price, max_price)
        self.last_range = last_range
        self._values_ranges[self.last_range] = result
        # print("4:",self.last_range,result)
        return adjust_range(result)


    def get_info_text(self, ix: int) -> str:
        # """"""
        if ix in self.macd_data:
            diff,dea,macd = self.macd_data[ix]
            words = [
                f"diff {diff:.3f}"," ",
                f"dea {dea:.3f}"," ",
                f"macd {macd:.3f}"
                ]
            text = "\n".join(words)
        else:
            text = "diff - \ndea - \nmacd -"

        return text


class TradeItem(ScatterPlotItem,CandleItem):
    """
    成交单绘图部件
    """
    def __init__(self, manager: BarManager):
        """"""
        ScatterPlotItem.__init__(self)
        # CandleItem.__init__(self,manager)
        # super(TradeItem,self).__init__(manager)
        super(CandleItem,self).__init__(manager)


        self.blue_pen: QtGui.QPen = pg.mkPen(color=(100, 100, 255), width=2)

        self.trades : Dict[int,Dict[str,TradeData]] = {} # {ix:{tradeid:trade}}

    def add_trades(self,trades:List[TradeData]):
        """ 增加成交单列表到TradeItem """
        for trade in trades:
            self.add_trade(trade)

        self.set_scatter_data()
        self.update()

    def add_trade(self,trade:TradeData,draw:bool=False):
        """ 增加一个成交单到TradeItem """
        # 这里使用reverse=True，是考虑到实盘成交往往发生在最新的bar里，可以加快搜索速度
        od = OrderedDict(sorted(self._manager._datetime_index_map.items(),key = lambda t:t[0],reverse=True))
        idx = self._manager.get_count() - 1
        for dt,ix in od.items():
            # print(f"dt={dt}\ntrade.datetime {trade.datetime}")
            dt1 = CHINA_TZ.localize(datetime.combine(dt.date(),dt.time()))
            if dt1 <= trade.datetime:
                # print(f"【dt={dt},dt1={dt1},dt2={trade.datetime} ix={ix}】")
                idx = ix
                break

        # 注意：一个bar期间可能发生多个成交单
        if idx in self.trades:
            self.trades[idx][trade.tradeid] = trade
        else:
            self.trades[idx] = {trade.tradeid:trade}

        if draw:
            self.set_scatter_data()
            self.update()

        # print(f"add_trade idx={idx} trade={trade}")

    def set_scatter_data(self):
        """ 把成交单列表绘制到ScatterPlotItem上 """
        scatter_datas = []
        for ix in self.trades:
            for trade in self.trades[ix].values():
                scatter = {
                    "pos" : (ix, trade.price),
                    "data": 1,
                    "size": 14,
                    "pen": pg.mkPen((255, 255, 255)),
                }

                if trade.direction == Direction.LONG:
                    scatter_symbol = "t1"   # Up arrow
                else:
                    scatter_symbol = "t"    # Down arrow

                if trade.offset == Offset.OPEN:
                    scatter_brush = pg.mkBrush((255, 255, 0))   # Yellow
                else:
                    scatter_brush = pg.mkBrush((0, 0, 255))     # Blue

                scatter["symbol"] = scatter_symbol
                scatter["brush"] = scatter_brush
                scatter_datas.append(scatter)

        self.setData(scatter_datas)

    def get_info_text(self, ix: int) -> str:
        """"""
        if ix in self.trades:
            text = "成交："
            for tradeid,trade in self.trades[ix].items():
                # TradeData
                text += f"\n{trade.price}{trade.direction.value}{trade.offset.value}{trade.volume}手"
        else:
            text = "成交：-"

        return text


class OrderItem(ScatterPlotItem,CandleItem):
    """
    委托单绘图部件
    """
    def __init__(self, manager: BarManager):
        """"""
        ScatterPlotItem.__init__(self)
        super(CandleItem,self).__init__(manager)

        self.orders : Dict[int,Dict[str,OrderData]] = {} # {ix:{orderid:order}}

    def add_orders(self,orders:List[OrderData]):
        """ 增加委托单列表到OrderItem """
        for order in orders:
            if order.datetime:
                self.add_order(order)

        self.set_scatter_data()
        self.update()

    def add_order(self,order:OrderData,draw:bool=False):
        """ 增加一个委托单到OrderItem """
        # 这里使用reverse=True，是考虑到实盘成交往往发生在最新的bar里，可以加快搜索速度

        od = OrderedDict(sorted(self._manager._datetime_index_map.items(),key = lambda t:t[0],reverse=True))
        idx = self._manager.get_count() - 1
        for dt,ix in od.items():
            # print(f"dt={dt}\ntrade.datetime {trade.datetime}")
            dt1 = CHINA_TZ.localize(datetime.combine(dt.date(),dt.time()))
            if dt1 <= order.datetime:
                # print(f"【dt={dt},dt1={dt1},dt2={order.datetime} ix={ix}】")
                idx = ix
                break

        # 注意：一个bar期间可能发生多个委托单
        if idx in self.orders:
            self.orders[idx][order.orderid] = order
        else:
            self.orders[idx] = {order.orderid:order}

        if draw:
            self.set_scatter_data()
            self.update()

    def set_scatter_data(self):
        """ 把委托单列表绘制到ScatterPlotItem上 """
        scatter_datas = []
        for ix in self.orders:
            lowest,highest=self.get_y_range()
            # print(f"range={lowest,highest}")
            for order in self.orders[ix].values():
                # 处理委托报价超出显示范围的问题
                if order.price>highest:
                    show_price = highest - 7
                elif order.price<lowest:
                    show_price = lowest + 7
                else:
                    show_price = order.price

                scatter = {
                    "pos" : (ix, show_price),
                    "data": 1,
                    "size": 14,
                    "pen": pg.mkPen((255, 255, 255)),
                }

                if order.direction == Direction.LONG:
                    scatter_symbol = "t1"   # Up arrow
                else:
                    scatter_symbol = "t"    # Down arrow

                if order.offset == Offset.OPEN:
                    scatter_brush = pg.mkBrush((0, 128, 128))   # Yellow
                else:
                    scatter_brush = pg.mkBrush((128, 128, 0))     # Blue

                scatter["symbol"] = scatter_symbol
                scatter["brush"] = scatter_brush
                scatter_datas.append(scatter)

        self.setData(scatter_datas)

    def get_info_text(self, ix: int) -> str:
        """"""
        if ix in self.orders:
            text = "委托："
            for orderid,order in self.orders[ix].items():
                # OrderData
                text += f"\n{order.price}{order.direction.value}{order.offset.value}{order.volume}手"
        else:
            text = "委托：-"


        return text