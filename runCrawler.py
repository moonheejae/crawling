import subprocess
import os

def run_crawler():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    crawler_ui_path = os.path.join(current_dir, 'crawlerUI.py')
    subprocess.run(['python', crawler_ui_path])

if __name__ == '__main__':
    run_crawler()
