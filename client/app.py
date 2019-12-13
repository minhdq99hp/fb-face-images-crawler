import sys
from PyQt5.QtWidgets import QMessageBox,QApplication,QLabel,QHBoxLayout,QProgressBar,QMainWindow,QApplication, QWidget, QInputDialog, QLineEdit, QFileDialog, QPushButton, QBoxLayout, QVBoxLayout
from PyQt5.QtGui import QIcon
from PyQt5 import QtWidgets
import time 
from PyQt5.QtCore import QThread, pyqtSignal

from browser_crawler import FBCrawler 
from random import shuffle
import json
import os
from lib.utils import *
from lib.utils import read_json, get_undone_friendlist, get_undownloaded_friendlist

TIME_LIMIT = None
TIME_FILTER_LIMIT = None
crawler = None 
undone_friendlist = None

class Login(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(Login, self).__init__(parent)
        self.textName = QtWidgets.QLineEdit(self)
        self.textPass = QtWidgets.QLineEdit(self)
        self.buttonLogin = QtWidgets.QPushButton('Login', self)
        self.buttonLogin.clicked.connect(self.handleLogin)
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.textName)
        layout.addWidget(self.textPass)
        layout.addWidget(self.buttonLogin)

    def handleLogin(self):
        if (self.textName.text() == 'infore' and
            self.textPass.text() == '2811'):
            self.accept()
        else:
            QtWidgets.QMessageBox.warning(
                self, 'Error', 'Bad user or password')
    
class ChooseFolderLayout(QWidget):
    def __init__(self, parent):        
        super(ChooseFolderLayout, self).__init__(parent)
        self.layout = QVBoxLayout(self)
        self.topLayout = QHBoxLayout(self)
        self.midLayout = QHBoxLayout(self)
        self.bottomLayout = QHBoxLayout(self)
        self.textInfo = QLabel()
        self.textInfo.setText("Choose folder to start crawling!")
        self.midLayout.addWidget(self.textInfo)
        
        self.buttonChooseFolder = QtWidgets.QPushButton('Choose Folder', self)
        self.buttonChooseFolder.clicked.connect(self.handleChooseFolder)
        self.topLayout.addWidget(self.buttonChooseFolder)

        self.progress = QProgressBar(self)
        self.progress.setGeometry(0, 0, 300, 25)
        self.progress.setMaximum(100)

        self.filterProgress = QProgressBar(self)
        self.filterProgress.setGeometry(0, 0, 300, 25)
        self.filterProgress.setMaximum(100)

        self.filterButton = QPushButton('Filter', self)
        self.filterButton.move(0,30)
        self.filterButton.clicked.connect(self.startFilterClick)
        self.filterButton.setEnabled(False)

        self.startButton = QPushButton('Start', self)
        self.startButton.move(0, 30)
        self.startButton.clicked.connect(self.onButtonClick)
        self.startButton.setEnabled(False)

        self.quitButton = QPushButton('Quit', self)
        self.quitButton.clicked.connect(self.quitProgram)

        self.topLayout.addWidget(self.startButton)
        self.topLayout.addWidget(self.quitButton)
        self.topLayout.addStretch(1)

        self.bottomLayout.addWidget(self.filterButton)
        self.bottomLayout.addStretch(1)

        self.layout.addLayout(self.topLayout)
        self.layout.addStretch(10)
        self.layout.addLayout(self.midLayout)
        self.layout.addWidget(self.progress)
        self.layout.addStretch(10)
        self.layout.addLayout(self.bottomLayout)
        self.layout.addWidget(self.filterProgress)

        self.setLayout(self.layout)
        

    def startFilterClick(self):
        # self.textInfo.setText("Start filtering ... ")
        self.calc = ExternalFilter()
        self.calc.countChanged.connect(self.onCountChangedFilter)
        self.calc.start()

    def handleChooseFolder(self):
        file = str(QFileDialog.getExistingDirectory(self, "Select Directory"))
        if file:
            print(file)
        self.textInfo.setText("Click start to begin!")
        self.startButton.setEnabled(True)

    def onButtonClick(self):
        ### start crawling images and save to folder
        ### replace count with the number of account in friend list
        self.textInfo.setText("Start crawling ... ")
        self.calc = External()
        self.calc.countChanged.connect(self.onCountChanged)
        self.calc.start()
        # self.textInfo.setText("Done!!!")
        self.filterButton.setEnabled(True)

    def onCountChanged(self, value):
        self.progress.setValue(value)

    def onCountChangedFilter(self, value):
        self.filterProgress.setValue(value)

    def quitProgram(self):
        ret = QMessageBox.question(self,'', "Are you sure to stop crawling?", QMessageBox.Yes | QMessageBox.No,QMessageBox.Yes)
        if ret == QMessageBox.Yes:
            QApplication.quit()
            crawler.quit()
            

class ExternalFilter(QThread):
    countChanged = pyqtSignal(int)
    def run(self):
        i = 0
        while i < TIME_FILTER_LIMIT:
            i += 1
            self.countChanged.emit(i)        


class External(QThread):
    """
    Runs a counter thread.
    """
    countChanged = pyqtSignal(int)

    def run(self):
        i = 0
        while i < TIME_LIMIT:
            i += 1
            
            # start = time.time()
            crawler.crawl_photos(crawler.user_info['friendlist'][i], 'photos_of')
            crawler.crawl_photos(crawler.user_info['friendlist'][i], 'photos_all')

            # write to metadata file
            metadata_path = os.path.join('data', crawler.user_info['friendlist'][i], 'metadata.json')
            metadata = read_json(metadata_path)
            if 'state' in metadata:
                if metadata['state'] not in ['done', 'downloaded']:
                    metadata['state'] = 'downloaded'
            else:
                metadata['state'] = 'downloaded'

            with open(os.path.join('data', crawler.user_info['friendlist'][i], 'metadata.json'), 'w', encoding='utf-8') as f:
                f.write(json.dumps(metadata, indent=4))
            
            print(f'--- {crawler.user_info["friendlist"][i]} IS FINISHED ---')

            self.countChanged.emit(i)

class MainWindow(QMainWindow):
    def __init__(self, parent = None):
        super(MainWindow, self).__init__(parent)
        self.chooseFolder = ChooseFolderLayout(self)
        self.setCentralWidget(self.chooseFolder)
        self.setGeometry(10, 10, 450, 150)
        

if __name__ == '__main__':
    crawler = FBCrawler(display_browser=True, fast_load=False, profile_name="crawler_profile")
    crawler.load_user_info_file()

    crawler.init_browser()

    if len(crawler.user_info['friendlist']) == 0:
        crawler.crawl_friendlist()
    shuffle(crawler.user_info['friendlist'])

    TIME_LIMIT = len(crawler.user_info['friendlist'])

    app = QtWidgets.QApplication(sys.argv)
    login = Login()

    if login.exec_() == QtWidgets.QDialog.Accepted:
        window = MainWindow()
        window.show()
        sys.exit(app.exec_())