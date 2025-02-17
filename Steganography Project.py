from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import QLabel, QPushButton, QFileDialog, QLineEdit, QMessageBox, QVBoxLayout, QHBoxLayout, QWidget, QProgressBar, QSlider
import cv2
import os
import qdarkstyle

class SteganographyApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
    
    def initUI(self):
        self.setWindowTitle("Steganography Tool - PyQt Edition")
        self.setGeometry(100, 100, 600, 550)
        self.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
        
        layout = QVBoxLayout()
        
        self.image_label = QLabel("Drop an Image Here")
        self.image_label.setAlignment(QtCore.Qt.AlignCenter)
        self.image_label.setStyleSheet("border: 2px dashed gray; padding: 20px;")
        layout.addWidget(self.image_label)
        
        self.file_button = QPushButton("Choose Image")
        self.file_button.clicked.connect(self.select_image)
        layout.addWidget(self.file_button)
        
        self.msg_entry = QLineEdit()
        self.msg_entry.setPlaceholderText("Enter Secret Message")
        layout.addWidget(self.msg_entry)
        
        self.password_entry = QLineEdit()
        self.password_entry.setEchoMode(QLineEdit.Password)
        self.password_entry.setPlaceholderText("Enter Password")
        layout.addWidget(self.password_entry)
        
        self.toggle_password_button = QPushButton("👁")
        self.toggle_password_button.setFixedWidth(40)
        self.toggle_password_button.clicked.connect(self.toggle_password)
        
        password_layout = QHBoxLayout()
        password_layout.addWidget(self.password_entry)
        password_layout.addWidget(self.toggle_password_button)
        layout.addLayout(password_layout)
        
        self.opacity_slider = QSlider(QtCore.Qt.Horizontal)
        self.opacity_slider.setMinimum(20)
        self.opacity_slider.setMaximum(100)
        self.opacity_slider.setValue(100)
        self.opacity_slider.valueChanged.connect(self.change_opacity)
        layout.addWidget(QLabel("Adjust Window Opacity"))
        layout.addWidget(self.opacity_slider)
        
        self.encrypt_button = QPushButton("Encrypt Message")
        self.encrypt_button.clicked.connect(self.encode_message)
        layout.addWidget(self.encrypt_button)
        
        self.decrypt_button = QPushButton("Decrypt Message")
        self.decrypt_button.clicked.connect(self.decode_message)
        layout.addWidget(self.decrypt_button)
        
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)
        
        self.setLayout(layout)
        self.setAcceptDrops(True)
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event):
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path.lower().endswith(('png', 'jpg', 'jpeg')):
                self.image_path = file_path
                self.image_label.setText(f"Selected: {os.path.basename(file_path)}")
                pixmap = QtGui.QPixmap(file_path).scaled(300, 300, QtCore.Qt.KeepAspectRatio)
                self.image_label.setPixmap(pixmap)
    
    def select_image(self):
        options = QFileDialog.Options()
        self.image_path, _ = QFileDialog.getOpenFileName(self, "Select Image", "", "Images (*.png *.jpg *.jpeg)", options=options)
        if self.image_path:
            pixmap = QtGui.QPixmap(self.image_path).scaled(300, 300, QtCore.Qt.KeepAspectRatio)
            self.image_label.setPixmap(pixmap)
    
    def toggle_password(self):
        if self.password_entry.echoMode() == QLineEdit.Password:
            self.password_entry.setEchoMode(QLineEdit.Normal)
        else:
            self.password_entry.setEchoMode(QLineEdit.Password)
    
    def change_opacity(self):
        self.setWindowOpacity(self.opacity_slider.value() / 100)
    
    def encode_message(self):
        if not hasattr(self, 'image_path') or not self.image_path:
            QMessageBox.warning(self, "Error", "No image selected!")
            return
        
        self.progress_bar.setValue(30)
        
        msg = self.msg_entry.text()
        password = self.password_entry.text()
        output_path = "encryptedImage.png"
        
        img = cv2.imread(self.image_path)
        if img is None:
            QMessageBox.critical(self, "Error", "Image not found!")
            return
        
        h, w, _ = img.shape  
        msg_length = len(msg)
        if msg_length > h * w:
            QMessageBox.critical(self, "Error", "Message too long to encode in the given image.")
            return
        
        for i in range(4):
            img[i, 0, 0] = (msg_length >> (i * 8)) & 0xFF
        
        img[4, 0, 0] = len(password)
        for i in range(len(password)):
            img[5 + i, 0, 0] = ord(password[i])
        
        idx = 0
        for row in range(h):
            for col in range(w):
                if row == 0 and col < 5 + len(password):
                    continue
                if idx < msg_length:
                    img[row, col, 0] = ord(msg[idx])
                    idx += 1
                else:
                    break
        
        cv2.imwrite(output_path, img, [cv2.IMWRITE_PNG_COMPRESSION, 0])
        
        self.progress_bar.setValue(100)
        QMessageBox.information(self, "Success", "Message encoded successfully!")
    
    def decode_message(self):
        options = QFileDialog.Options()
        image_path, _ = QFileDialog.getOpenFileName(self, "Select Encrypted Image", "", "Images (*.png *.jpg *.jpeg)", options=options)
        if not image_path:
            return
        
        img = cv2.imread(image_path)
        if img is None:
            QMessageBox.critical(self, "Error", "Image not found!")
            return
        
        stored_length = sum(img[i, 0, 0] << (i * 8) for i in range(4))
        password_length = img[4, 0, 0]
        stored_password = "".join(chr(img[5 + i, 0, 0]) for i in range(password_length))
        
        entered_password = self.password_entry.text()
        if entered_password != stored_password:
            QMessageBox.critical(self, "Error", "Incorrect passcode! Access Denied.")
            return
        
        message = ""
        idx = 0
        h, w, _ = img.shape
        for row in range(h):
            for col in range(w):
                if row == 0 and col < 5 + password_length:
                    continue
                if idx < stored_length:
                    message += chr(img[row, col, 0])
                    idx += 1
                else:
                    break
        
        QMessageBox.information(self, "Decryption Successful", f"Decrypted Message: {message}")
        
if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    window = SteganographyApp()
    window.show()
    sys.exit(app.exec_())
