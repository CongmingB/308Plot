from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

import pyqtgraph as pg
import pyqtgraph.exporters
import sys
import os
from collections import defaultdict
from itertools import cycle
from pprint import pprint


pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')

DEFAULT_BASE_CURRENCY = 'EUR'
DEFAULT_DISPLAY_CURRENCIES = ['CAD','CYP','AUD','USD', 'EUR', 'GBP', 'NZD', 'SGD']
#BREWER12PAIRED = cycle(['#a6cee3', '#1f78b4', '#b2df8a', '#33a02c', '#fb9a99', '#e31a1c', '#fdbf6f', '#ff7f00',
#                  '#cab2d6', '#6a3d9a', '#ffff99', '#b15928' ])
BREWER12PAIRED = cycle(['#0033ff', '#36bf36', '#ff4d00',
                        '#00c3d1', '#ff00ff', '#cd853f'])
                        
SYMBOLTYPE = cycle(['o', 't', 's',
                    'p', 'h', '+', 'd'])

class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        app = QApplication(sys.argv)

        super(MainWindow, self).__init__(*args, **kwargs)

        self.ax = pg.PlotWidget()
        self.ax.showGrid(True, True)
        self.curve = self.ax.getPlotItem()
        #self.curve.addLegend()
        self.legend = self.curve.addLegend()

        self._data_colors = dict()
        self._data_symbols = dict()
        self._data_visible = []
        self._data_lines = dict()
        self.data = defaultdict(list)

        self.line = pg.InfiniteLine(
            pos = -20,
            pen = pg.mkPen('k', width=3),
            movable=True
        )

        #self.ax.addItem(self.line)
        
        self.tableView = QTableView()
        self.model = QStandardItemModel()
        self.model.itemChanged.connect(self.checkCheckState)
        self.tableView.setModel(self.model)
        #self.tableView.verticalHeader().hide()
        self.tableView.horizontalHeader().hide()
        self.initModel(100, 100)

        # tianjia gongju lan
        toolbar_1 = QToolBar()
        toolbar_2 = QToolBar()

        toolbar_1.addAction(QIcon('./images/open-folder.png'),
            'Open', self.open_datas)
        toolbar_1.addAction(QIcon('./images/save-256.png'),
            'Save', self.savePicture)

        self.currencyCombo = QComboBox()
        self.currencyCombo.setSizeAdjustPolicy(0)
        # 0: Adjust to Content, 1: Adjust to FirstShow
        self.currencyCombo.addItem('All')
        self.currencyCombo.highlighted.connect(self.comboChoose)
        toolbar_2.addWidget(self.currencyCombo)

        self.addToolBar(toolbar_1)
        self.addToolBar(toolbar_2)

        #splitter = QSplitter()
        #splitter.addWidget(self.ax)
        #splitter.addWidget(self.tableView)

        #layout = QHBoxLayout()
        #layout.addWidget(splitter)

        #widget = QWidget()
        #widget.setLayout(layout)
        
        #self.setCentralWidget(widget)

        splitter = QSplitter()
        splitter.addWidget(self.ax)
        splitter.addWidget(self.tableView)
        self.setCentralWidget(splitter)

        self.show()
        sys.exit(app.exec_())

    def setHeaderFormat(self, item):
        item.setForeground(QBrush(QColor(
            self.getDataColor(item.text())
        )))
        if not item.isCheckable():
            item.setCheckable(True)       
            item.setCheckState(Qt.Checked)
        item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        item.setFont(QFont("Consolas", 14, QFont.Bold))
        return item

    def setCellFormat(self, item):
        item.setTextAlignment(Qt.AlignVCenter | Qt.AlignHCenter)
        item.setFont(QFont("Consolas", 10))
        return item

    def addFileDataHeader(self, i, dataHeader):
        item = QStandardItem()
        item.setText(dataHeader)
        item = self.setHeaderFormat(item)
        self.model.setItem(0, 2*i, item)

    def addFileCellData(self, row, col, celldata):
        item = QStandardItem()
        item.setText(celldata)
        self.setCellFormat(item)
        self.model.setItem(row, col, item)

    def addInputCellData(self, item):
        row = self.model.indexFromItem(item).row()
        column = self.model.indexFromItem(item).column()
        headerColumn = column if column%2==0 else column-1
        try:
            header = self.model.item(0, headerColumn).text()
        except AttributeError:
            self.headerRedAlert(headerColumn)
            text, ok = QInputDialog.getText(self,
                'Warning', 'Please Input Header.')
            if ok:
                self.addFileDataHeader(headerColumn, text)
            else:
                item.setText('')
                self.headerRedAlert(headerColumn, color='White')
                self.model.item(0, headerColumn).setCheckable(False)
                return

        if column%2 == 0:
            return
        else:
            try:
                a = float(self.model.item(row, column-1).text())
                b = float(self.model.item(row, column).text())
                self.data[header].append((a, b))
            except (AttributeError, ValueError):
                text, ok = QInputDialog.getText(self,
                    'Warning', 'Please Input x First.')
                if ok:
                    self.addFileCellData(row, column-1, text)
                    self.addFileCellData(row, column, item.text())
                    a = float(self.model.item(row, column-1).text())
                    b = float(self.model.item(row, column).text())
                    self.data[header].append((a, b))
            
            #try:
            #    b = float(self.model.item(row, column).text())
            #    self.data[header].append((a, b))
            #except Exception as e:
            #    print(e)
    
    def headerRedAlert(self, column, color='Red'):
        item = QStandardItem()
        item.setBackground(QBrush(QColor(color)))
        self.model.setItem(0, column, item)

    def open_datas(self):
        files, _ = QFileDialog.getOpenFileNames(self, 'Choose Files', './')
        for i, file in enumerate(files):
            with open(file, 'r') as fh:
                _, filename = os.path.split(file)
                fnWithoutExt, _ = os.path.splitext(filename)
                self.updateComboBox(fnWithoutExt)
                self.addFileDataHeader(i, fnWithoutExt)
                for row, line in enumerate(fh.readlines()[1:]):
                    a, b = line.strip().split()
                    self.addFileCellData(row+1, 2*i, a)
                    self.addFileCellData(row+1, 2*i+1, b)
                    #self.data[fnWithoutExt].append((float(a), float(b)))

    def checkCheckState(self, item):
        indexOfItem = self.model.indexFromItem(item)
        if indexOfItem.row() == 0:
            self.setHeaderFormat(item)
        else:
            self.addInputCellData(item)

        column = indexOfItem.column()
        headerColumn = column if column%2==0 else column-1
        headerItem = self.model.item(0, headerColumn)
        group = headerItem.text()
        checked = headerItem.checkState() == Qt.Checked
        #```if i.checkedState() == Qt.Checked:``` is not available. (why?)
        if group in self._data_visible:
            if not checked:
                self._data_visible.remove(group)
                self.draw()
            if checked:
                self.draw()
        else:
            if checked:
                self._data_visible.append(group)
                self.draw()

    def updateComboBox(self, dataHeader):
        if self.currencyCombo.findText(dataHeader) == -1:
            self.currencyCombo.addItem(dataHeader)
        self.currencyCombo.model().sort(0)

    def initModel(self, row, col):
        self.model.setRowCount(row)
        self.model.setColumnCount(col)
        for i in range(col):
            self.tableView.setColumnWidth(i,60)

        for i in range(0, col, 2):
            self.tableView.setSpan(0, i, 1, 2)

    def comboChoose(self, index):
        choosedGroup = self.currencyCombo.itemText(index)
        if choosedGroup == 'All' and len(self._data_visible) > 1:
            self._data_visible_bak = self._data_visible.copy()
        else:
            self._data_visible = [choosedGroup]
            self.draw()
        if choosedGroup == 'All':
            try:
                self._data_visible = self._data_visible_bak
                self.draw()
            except AttributeError:
                pass
        
    def getDataColor(self, data):
        if data not in self._data_colors:
            self._data_colors[data] = next(BREWER12PAIRED)
        return self._data_colors[data]

    def getDataSymbol(self, data):
        if data not in self._data_symbols:
            self._data_symbols[data] = next(SYMBOLTYPE)
        return self._data_symbols[data]

    def draw(self):
        y_min, y_max = -sys.maxsize, sys.maxsize
        keys = sorted(self.data.keys())
        for group in keys:
            x, y = zip(*self.data[group])
            if group in self._data_visible:
                y_min = min(y_min, *y)
                y_max = max(y_max, *y)
            else:
                x, y = [], []
            
            if group in self._data_lines:
                self._data_lines[group].setData(x, y)
            else:
                self._data_lines[group] = self.curve.plot(
                    x, y, symbol=self.getDataSymbol(group),
                    symbolBrush=self.getDataColor(group),
                    pen=pg.mkPen(self.getDataColor(group),
                    width=3), name=group
                )
        self.ax.setLimits(yMin=y_min*0.9, yMax=y_max*1.1)

    def savePicture(self):
        exporter = pg.exporters.ImageExporter(self.ax.getPlotItem())
        exporter.parameters()['width'] = 1000   # (note this also affects height parameter)
        exporter.parameters()['height'] = 1000   # (note this also affects height parameter)
        exporter.export('abc.png')

    #def add_data_row(self, dataFilePath):
    #    citem = QStandardItem()
    #    with open(dataFilePath, 'r') as fh:
    #        fileHeader = fh.readlines()[0]
    #    citem.setText(fileHeader)
    #    
    #    vitem = QStandardItem()

    #    self.model.appendRow([citem, vitem])

if __name__ == '__main__':
    MainWindow()