import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QLineEdit, QVBoxLayout, QWidget, QLabel, QTextEdit, QComboBox
from PyQt5.QtCore import QThread, pyqtSignal
from musinsa import MusinsaCrawler
import asyncio

class CrawlerThread(QThread):
    update_status = pyqtSignal(str)

    def __init__(self, keywords, save_format):
        super().__init__()
        self.keywords = keywords
        self.save_format = save_format
        self.crawler = MusinsaCrawler()

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.crawler.run(self.keywords, self.save_format))
        self.update_status.emit(f'{self.keywords} is Crawling completed.')

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('Musinsa Crawler')
        self.setGeometry(100, 100, 600, 400)

        self.keyword_input = QTextEdit(self)
        self.keyword_input.setPlaceholderText('Enter keywords separated by commas')

        self.save_format_combo = QComboBox(self)
        self.save_format_combo.addItems(['csv', 'json', 'db'])

        self.start_button = QPushButton('Start Crawling', self)
        self.start_button.clicked.connect(self.start_crawling)

        self.status_label = QLabel('', self)

        layout = QVBoxLayout()
        layout.addWidget(QLabel('Keywords (comma-separated):', self))
        layout.addWidget(self.keyword_input)
        layout.addWidget(QLabel('Save format:', self))
        layout.addWidget(self.save_format_combo)
        layout.addWidget(self.start_button)
        layout.addWidget(self.status_label)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def start_crawling(self):
        keywords = [keyword.strip() for keyword in self.keyword_input.toPlainText().split(',')]
        if keywords:
            self.status_label.setText('Crawling started...')
            save_format = self.save_format_combo.currentText()
            self.crawler_thread = CrawlerThread(keywords, save_format)
            self.crawler_thread.update_status.connect(self.update_status)
            self.crawler_thread.start()
        else:
            self.status_label.setText('Please enter at least one keyword.')

    def update_status(self, status):
        self.status_label.setText(status)

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
