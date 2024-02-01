import sys
from PyQt5.QtWidgets import QApplication, QHBoxLayout, QHeaderView ,QLabel, QMainWindow, QFileSystemModel, QTreeView, QTextEdit, QLineEdit, QCheckBox, QPushButton, QVBoxLayout, QWidget, QSplitter, QFileDialog
from PyQt5.QtCore import Qt,QSettings, QSize, QPoint, QTimer
from PyQt5.QtGui import QFont, QPixmap
import os
import re
import shutil
import subprocess

from datetime import datetime

class App(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = QSettings('MyCompany', 'MyApp')
        self.currentFilePath = None  # currentFilePath 초기화

        self.title = 'Jekyll Blog Manager'
        self.initUI()
        # self.showMaximized()  
        
    def initUI(self):
        self.setWindowTitle(self.title)
        
        
        
        self.gitButton = QPushButton('Github Post', self)
        self.gitButton.clicked.connect(self.git_operations)
        
        self.imageButton = QPushButton('Image', self)
        self.imageButton.clicked.connect(self.addImage)
        self.imageLabel = QLabel(self)
        
        self.resize(self.settings.value('windowSize', QSize(800, 600)))
        self.move(self.settings.value('windowPosition', QPoint(100, 100)))
        
        # 게시물 목록 뷰어 설정
        self.model = QFileSystemModel()
        self.initialPath = 'C:/Users/hoon1/huni'  # 초기 경로 설정
        self.model.setRootPath(self.initialPath)
        
        # 이미지 저장 폴더 설정 (예: self.initialPath/images)
        self.imagesFolder = os.path.join(self.initialPath, 'images')


        
        self.tree = QTreeView()
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(self.initialPath + '/_posts'))
        
        # Size와 Type 컬럼을 숨김
        self.tree.setColumnHidden(1, True)  # Size 컬럼
        self.tree.setColumnHidden(2, True)  # Type 컬럼
        self.tree.setColumnHidden(3, True) # Date Modified 컬럼은 표시

        # 컬럼 너비를 콘텐츠에 맞게 조정
        self.tree.header().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tree.header().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        # 메타데이터 에디터
        self.editor = CustomTextEdit()
        self.titleEdit = QLineEdit()
        self.commentsCheck = QCheckBox('Enable Comments')
        self.categoryEdit = QLineEdit()
        self.tagsEdit = QLineEdit()
        
        self.titleEditLabel = QLabel('Title')
        self.categoryEditLabel = QLabel('Categories')
        self.tagsEditLabel = QLabel('Tags')
        
        
        self.dateEditLabel = QLabel('Date')
        self.dateEdit = QLineEdit()
        self.dateEdit.setText(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        # 폴더 선택 버튼
        self.selectFolderButton = QPushButton('Select Directory')
        self.selectFolderButton.clicked.connect(self.selectFolder)
        
        # 저장 버튼 정의
        self.savePostButton = QPushButton('Save')
        # self.savePostButton.clicked.connect(self.saveFileContent)
        
        
        # 버튼 설정
        self.boldButton = QPushButton('Bold')
        self.italicButton = QPushButton('Italic')
        # ... 기타 마크다운 버튼들 ...
        self.newPostButton = QPushButton('New')
        self.deletePostButton = QPushButton('Delete')

        
        # New Post 버튼 클릭 시그널 연결
        self.newPostButton.clicked.connect(self.tree.clearSelection)
        self.newPostButton.clicked.connect(self.createNewPost)
        
        # Save Post 버튼 클릭 시그널 연결
        self.savePostButton.clicked.connect(self.savePost)
        self.deletePostButton.clicked.connect(self.deletePost)

        
        rightLayout = QVBoxLayout()
        horizonLayout= QHBoxLayout()
        horizonLayout1= QHBoxLayout()
        horizonLayout2= QHBoxLayout()

        # 라벨을 입력 칸 바로 위에 추가
        rightLayout.addWidget(self.titleEditLabel)
        rightLayout.addWidget(self.titleEdit)
        rightLayout.addWidget(self.dateEditLabel)
        rightLayout.addWidget(self.dateEdit)
        
        rightLayout.addWidget(self.categoryEditLabel)
        rightLayout.addWidget(self.categoryEdit)
        rightLayout.addWidget(self.tagsEditLabel)
        rightLayout.addWidget(self.tagsEdit)
        rightLayout.addWidget(self.commentsCheck)
        

        rightLayout.addWidget(self.imageButton)
        rightLayout.addWidget(self.editor)


        
        
        
        # 마크다운 버튼들 추가
        
        # ... 기타 버튼들 ...
        horizonLayout1.addWidget(self.newPostButton)
        horizonLayout1.addWidget(self.deletePostButton)
        horizonLayout1.addWidget(self.savePostButton)
        horizonLayout1.addWidget(self.selectFolderButton)
        horizonLayout1.addWidget(self.gitButton)
        rightLayout.addLayout(horizonLayout1)
      
        container = QWidget()
        container.setLayout(rightLayout)
        
        
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.addWidget(self.tree)
        self.splitter.addWidget(container)
        
        self.splitter.setSizes([self.width() // 3, self.width() // 3 * 3])
        
        self.setCentralWidget(self.splitter)
        
        
        self.tree.clicked.connect(self.loadFileContent)
        self.show()
        
    def addImage(self):
        imagePaths, _ = QFileDialog.getOpenFileNames(self, 'Open images', '', 'Image files (*.png *.jpg *.jpeg *.bmp *.gif)')
        
        for imagePath in imagePaths:
            if imagePath:
                if not os.path.exists(self.imagesFolder):
                    os.makedirs(self.imagesFolder)
                
                imageFilename = os.path.basename(imagePath)
                
                destination = os.path.join(self.imagesFolder, imageFilename)
                shutil.copyfile(imagePath, destination)
                
                relativeImagePath = os.path.join('images', imageFilename)

                markdownImageSyntax = f"![{imageFilename}]({relativeImagePath})\n"
                self.editor.insertPlainText(markdownImageSyntax)
                
    def selectFolder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Jekyll Folder")
        if folder:
            self.loadPosts(folder)

    
    def loadFileContent(self, index):
        file_path = self.model.filePath(index)
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                
                # Frontmatter와 본문을 분리
                frontmatter, body = self.parseMarkdown(content)
                
                # Frontmatter를 입력 칸에 설정
                self.titleEdit.setText(frontmatter.get('title', ''))
                self.commentsCheck.setChecked(frontmatter.get('comments', 'false') == 'true')
                self.categoryEdit.setText(', '.join(frontmatter.get('categories', [])))
                self.tagsEdit.setText(', '.join(frontmatter.get('tags', [])))
                if 'date' in frontmatter:
                    self.dateEdit.setText(frontmatter['date'])
                
                # 본문을 에디터에 설정
                self.editor.setPlainText(body)
                self.currentFilePath = file_path
        except PermissionError:
            print(f"Permission denied: {file_path}")

    def parseMarkdown(self, content):
        frontmatter = {}
        body = ""
        # Frontmatter의 시작과 끝을 찾는 정규 표현식
        match = re.search(r'^---\s+(.*?)\s+---\s+(.*)', content, re.DOTALL | re.MULTILINE)
        if match:
            frontmatter_content = match.group(1)
            body = match.group(2).strip()
            for line in frontmatter_content.split('\n'):
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()
                if value.startswith('[') and value.endswith(']'):
                    # 리스트로 파싱
                    frontmatter[key] = re.findall(r'\[([^]]+)\]', value)
                elif value.lower() in ['true', 'false']:
                    # 부울 값으로 파싱
                    frontmatter[key] = value.lower()
                else:
                    # 문자열로 파싱
                    frontmatter[key] = value.strip('"').strip("'")
        return frontmatter, body
    def createNewPost(self):
        # 모든 입력 필드 초기화
        self.titleEdit.clear()
        self.categoryEdit.clear()
        self.tagsEdit.clear()
        self.editor.clear()
        self.commentsCheck.setChecked(False)
        # 날짜를 현재 시각으로 설정
        self.dateEdit.setText(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        self.currentFilePath = None

        
    def savePost(self):
        if self.currentFilePath:
            # 현재 파일 경로가 설정되어 있으면, 해당 파일을 업데이트
            filepath = self.currentFilePath
        else:
            # 현재 파일 경로가 설정되어 있지 않으면, 새 파일 생성
            filename = datetime.now().strftime('%Y-%m-%d-%H-%M-%S') + '.md'
            filepath = os.path.join(self.initialPath, '_posts', filename)

        # Frontmatter와 본문을 파일에 저장
        self.saveMarkdown(filepath, self.createFrontmatter(), self.editor.toPlainText())
        
        # 파일 목록을 갱신 (선택적)
        self.model.setRootPath(self.initialPath)

    def createFrontmatter(self):
        # Frontmatter 생성
        frontmatter = '---\n'
        frontmatter += f"title: \"{self.titleEdit.text()}\"\n"
        frontmatter += f"date: {self.dateEdit.text()}\n"
        frontmatter += f"categories: [{self.categoryEdit.text()}]\n"
        frontmatter += f"tags: [{self.tagsEdit.text()}]\n"
        frontmatter += f"comments: {'true' if self.commentsCheck.isChecked() else 'false'}\n"
        frontmatter += '---\n\n'
        return frontmatter

    def saveMarkdown(self, filepath, frontmatter, content):
        # 파일 저장
        with open(filepath, 'w', encoding='utf-8') as file:
            file.write(frontmatter)
            file.write(content)
            
    def deletePost(self):
        if self.currentFilePath:
            # 이동할 경로 생성 (#trash 폴더가 존재한다고 가정)
            trash_path = os.path.join(self.initialPath, '_posts/#trash')
            if not os.path.exists(trash_path):
                os.makedirs(trash_path)

            # 파일을 #trash 폴더로 이동
            dest_path = os.path.join(trash_path, os.path.basename(self.currentFilePath))
            shutil.move(self.currentFilePath, dest_path)
            
            # 파일 목록을 갱신
            self.model.setRootPath(self.initialPath)
            self.tree.clearSelection()
            self.editor.clear()
            self.titleEdit.clear()
            self.categoryEdit.clear()
            self.tagsEdit.clear()
            self.commentsCheck.setChecked(False)
            self.dateEdit.setText(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

            # 현재 파일 경로 초기화
            self.currentFilePath = None
        else:
            # 오류 메시지를 표시하거나 로깅
            print("No file is selected to delete.")
    def closeEvent(self, event):
    # 윈도우 크기와 위치를 저장합니다.
        self.settings.setValue('windowSize', self.size())
        self.settings.setValue('windowPosition', self.pos())
        super().closeEvent(event)
        
    def git_operations(self):
        self.gitButton.setText("Loading..")
        self.gitButton.setEnabled(False)  # 버튼을 비활성화하여 중복 클릭 방지
        posts_directory = os.path.join(self.initialPath, '_posts')
        images_directory = os.path.join(self.initialPath, 'images')  # images 폴더 경로
        try:
            # Git add for _posts directory
            subprocess.run(["git", "-C", self.initialPath, "add", f"{posts_directory}/*"], check=True)
            # Git add for images directory
            subprocess.run(["git", "-C", self.initialPath, "add", f"{images_directory}/*"], check=True)
            # Git commit
            subprocess.run(["git", "-C", self.initialPath, "commit", "-m", "Update posts"], check=True)
            # Git push
            subprocess.run(["git", "-C", self.initialPath, "push"], check=True)
            self.gitButton.setText("Complete")
        except subprocess.CalledProcessError as e:
            self.gitButton.setText("Failed")
        QTimer.singleShot(2000, lambda: self.resetGitButton())

    def resetGitButton(self):
        self.gitButton.setText('Github Post')
        self.gitButton.setEnabled(True)


class CustomTextEdit(QTextEdit):
    def __init__(self):
        super().__init__()

    def keyPressEvent(self, event):
        # Ctrl과 + 키를 함께 눌렀을 때 글꼴 크기 증가
        if event.modifiers() & Qt.ControlModifier:
            if event.key() in [Qt.Key_Plus, Qt.Key_Equal]:
                self.changeFontSize(1)
            elif event.key() == Qt.Key_Minus:
                self.changeFontSize(-1)
        else:
            super().keyPressEvent(event)

    def wheelEvent(self, event):
        # Ctrl과 마우스 휠을 함께 사용했을 때 글꼴 크기 조절
        if QApplication.keyboardModifiers() & Qt.ControlModifier:
            delta = event.angleDelta().y()
            if delta > 0:
                self.changeFontSize(1)
            elif delta < 0:
                self.changeFontSize(-1)
        else:
            super().wheelEvent(event)

    def changeFontSize(self, delta):
        # 현재 글꼴 가져오기
        font = self.font()
        # 새 글꼴 크기 설정
        newSize = max(1, font.pointSize() + delta)  # 글꼴 크기가 1보다 작아지지 않도록 함
        font.setPointSize(newSize)
        # 변경된 글꼴 설정
        self.setFont(font)

if __name__ == '__main__':
    # qdarktheme.enable_hi_dpi()
    app = QApplication(sys.argv)
    default_font = QApplication.font()
    app.setFont(default_font)
    # qdarktheme.setup_theme("auto")

    # main_win = QMainWindow()
    # push_button = QPushButton("PyQtDarkTheme!!")
    # main_win.setCentralWidget(push_button)

    # main_win.show()
    
    ex = App()
    sys.exit(app.exec_())
    app.exec()
