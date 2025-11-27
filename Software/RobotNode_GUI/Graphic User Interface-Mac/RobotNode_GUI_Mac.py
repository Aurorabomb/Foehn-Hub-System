import sys
import serial
import threading
from serial.tools import list_ports
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QGroupBox, QLabel, QComboBox, QPushButton, QSlider, QLineEdit, QRadioButton,
    QTextEdit, QScrollArea, QFrame, QButtonGroup, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal, QObject

class SerialSignals(QObject):
    received = pyqtSignal(str)

class SerialThread(threading.Thread):
    def __init__(self, serial, running):
        super().__init__()
        self.serial = serial
        self.running = running
        self.signals = SerialSignals()
        
    def run(self):
        while self.running[0] and self.serial and self.serial.is_open:
            try:
                if self.serial.in_waiting > 0:
                    line = self.serial.readline().decode('utf-8', errors='ignore').strip()
                    if line:
                        self.signals.received.emit(f"Received: {line}")
            except Exception as e:
                self.signals.received.emit(f"Serial read error: {str(e)}")
                break

class MotorControlApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ser = None
        self.running = [False]  # 使用列表以便在多个线程中共享状态
        self.serial_thread = None
        
        # 初始化电机状态
        self.motor_states = {
            1: {"speed": 0, "direction": "S"},
            2: {"speed": 0, "direction": "S"},
            3: {"speed": 0, "direction": "S"},
            4: {"speed": 0, "direction": "S"}
        }
        
        self.setup_ui()
        self.refresh_ports()
        
    def setup_ui(self):
        self.setWindowTitle("焚风中枢-Foehn Central Node GUI v2.0")
        self.setGeometry(100, 100, 800, 600)
        
        # 主窗口布局
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # 滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        
        # 串口设置区域
        port_group = QGroupBox("串口设置-Port Setup")
        port_layout = QHBoxLayout(port_group)
        
        self.port_combobox = QComboBox()
        self.port_combobox.setMinimumWidth(150)
        port_layout.addWidget(self.port_combobox)
        
        refresh_btn = QPushButton("刷新端口-Refresh")
        refresh_btn.clicked.connect(self.refresh_ports)
        port_layout.addWidget(refresh_btn)
        
        connect_btn = QPushButton("连接-Connect")
        connect_btn.clicked.connect(self.connect_serial)
        port_layout.addWidget(connect_btn)
        
        disconnect_btn = QPushButton("断开-Disconnect")
        disconnect_btn.clicked.connect(self.disconnect_serial)
        port_layout.addWidget(disconnect_btn)
        
        scroll_layout.addWidget(port_group)
        
        # 电机控制区域 (2x2网格)
        motors_group = QGroupBox()
        motors_layout = QGridLayout(motors_group)
        
        # 创建4个电机控制组
        self.motor_widgets = {}
        for i in range(1, 5):
            row = 0 if i in [1, 2] else 1
            col = 0 if i in [1, 3] else 1
            motor_group = self.create_motor_control(i)
            motors_layout.addWidget(motor_group, row, col)
            self.motor_widgets[i] = motor_group
        
        scroll_layout.addWidget(motors_group)
        
        # 磁力搅拌控制区域
        stir_group = QGroupBox("磁力搅拌控制-MagStir Control")
        stir_layout = QHBoxLayout(stir_group)
        
        stir_layout.addWidget(QLabel("持续时间(秒)-Duration(s):"))
        
        self.stir_duration = QLineEdit("5")
        self.stir_duration.setMaximumWidth(80)
        stir_layout.addWidget(self.stir_duration)
        
        start_stir_btn = QPushButton("开启搅拌-Start")
        start_stir_btn.clicked.connect(lambda: self.send_command(f"A{self.stir_duration.text()}"))
        stir_layout.addWidget(start_stir_btn)
        
        stop_stir_btn = QPushButton("停止搅拌-Stop")
        stop_stir_btn.clicked.connect(lambda: self.send_command("B"))
        stir_layout.addWidget(stop_stir_btn)
        
        scroll_layout.addWidget(stir_group)
        
        # 全局控制指令区域
        global_group = QGroupBox("全局控制指令-Global Commands")
        global_layout = QHBoxLayout(global_group)
        
        commands = [
            ("紧急停止-SSS", "SSS"),
            ("系统信息-BIOS", "BIOS"),
            ("原型机信息-INFO", "INFO"),
            ("设计信息-NOTE", "NOTE"),
            ("初始化-Foehn", "Foehn")
        ]
        
        for text, cmd in commands:
            btn = QPushButton(text)
            btn.clicked.connect(lambda _, c=cmd: self.send_command(c))
            global_layout.addWidget(btn)
        
        scroll_layout.addWidget(global_group)
        
        # 自定义指令区域
        custom_group = QGroupBox("自定义指令-Custom Command")
        custom_layout = QHBoxLayout(custom_group)
        
        custom_layout.addWidget(QLabel("输入指令:"))
        
        self.custom_command = QLineEdit()
        self.custom_command.returnPressed.connect(self.send_custom_command)
        custom_layout.addWidget(self.custom_command)
        
        send_custom_btn = QPushButton("发送指令-Send")
        send_custom_btn.clicked.connect(self.send_custom_command)
        custom_layout.addWidget(send_custom_btn)
        
        scroll_layout.addWidget(custom_group)
        
        # 状态显示区域
        status_group = QGroupBox("状态监控-Status Check")
        status_layout = QVBoxLayout(status_group)
        
        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)
        self.status_text.setMinimumHeight(150)
        status_layout.addWidget(self.status_text)
        
        clear_btn = QPushButton("清除状态-Clear")
        clear_btn.clicked.connect(self.clear_status)
        status_layout.addWidget(clear_btn, alignment=Qt.AlignRight)
        
        scroll_layout.addWidget(status_group)
        
        # 设置滚动区域
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)
        
        self.setCentralWidget(main_widget)
    
    def create_motor_control(self, motor_id):
        """创建单个电机控制组"""
        group = QGroupBox(f"电机{motor_id}控制-Pump{motor_id} Control")
        layout = QVBoxLayout(group)
        
        # 速度控制
        speed_layout = QHBoxLayout()
        speed_layout.addWidget(QLabel("速度(0-255)-Flow Rate:"))
        
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(0, 255)
        self.speed_slider.setValue(0)
        self.speed_slider.setObjectName(f"speed_slider_{motor_id}")
        speed_layout.addWidget(self.speed_slider)
        
        self.speed_entry = QLineEdit("0")
        self.speed_entry.setMaximumWidth(50)
        self.speed_entry.setObjectName(f"speed_entry_{motor_id}")
        speed_layout.addWidget(self.speed_entry)
        
        # 连接滑块和输入框
        self.speed_slider.valueChanged.connect(
            lambda value, entry=self.speed_entry: entry.setText(str(value))
        )
        self.speed_entry.textChanged.connect(
            lambda text, slider=self.speed_slider: 
                slider.setValue(int(text)) if text.isdigit() and 0 <= int(text) <= 255 else None
        )
        
        layout.addLayout(speed_layout)
        
        # 方向控制
        direction_group = QButtonGroup(self)
        direction_layout = QHBoxLayout()
        
        directions = [
            ("抽入-Pump In", "F"),
            ("停止-Stop", "S"),
            ("排出-PumpOut", "B")
        ]
        
        for text, value in directions:
            radio = QRadioButton(text)
            radio.setObjectName(f"direction_{motor_id}_{value}")
            if value == "S":
                radio.setChecked(True)
            radio.toggled.connect(
                lambda checked, m=motor_id, v=value: 
                    self.update_motor_direction(m, v) if checked else None
            )
            direction_group.addButton(radio)
            direction_layout.addWidget(radio)
        
        layout.addLayout(direction_layout)
        
        # 保存控件引用
        self.motor_states[motor_id]["slider"] = self.speed_slider
        self.motor_states[motor_id]["entry"] = self.speed_entry
        
        return group
    
    def update_motor_direction(self, motor_id, direction):
        """更新电机方向并发送命令"""
        self.motor_states[motor_id]["direction"] = direction
        self.update_motor(motor_id)
    
    def update_motor(self, motor_id):
        """更新电机状态并发送命令"""
        if not self.ser or not self.ser.is_open:
            return
        
        state = self.motor_states[motor_id]
        speed = state["slider"].value()
        direction = state["direction"]
        
        if direction != "S":
            cmd = f"{motor_id}{direction}{speed}\n"
        else:
            cmd = f"{motor_id}S\n"
        
        try:
            self.ser.write(cmd.encode())
            self.log_message(f"Sent: {cmd.strip()}")
        except Exception as e:
            self.log_message(f"Error: {str(e)}")
    
    def refresh_ports(self):
        """刷新可用串口列表"""
        self.port_combobox.clear()
        ports = [port.device for port in list_ports.comports()]
        self.port_combobox.addItems(ports)
        if ports:
            self.port_combobox.setCurrentIndex(0)
    
    def connect_serial(self):
        """连接串口"""
        port = self.port_combobox.currentText()
        if not port:
            self.log_message("错误：请选择有效串口！- Error! Please choose the right Port!")
            return
        
        try:
            self.ser = serial.Serial(port, 9600, timeout=2)
            self.running[0] = True
            self.serial_thread = SerialThread(self.ser, self.running)
            self.serial_thread.signals.received.connect(self.log_message)
            self.serial_thread.start()
            self.log_message(f"已连接串口 {port}-Connected!")
            # 发送初始化命令
            self.send_command("Foehn")
        except Exception as e:
            self.log_message(f"连接错误: {str(e)}")
    
    def disconnect_serial(self):
        """断开串口连接"""
        if self.ser and self.ser.is_open:
            self.running[0] = False
            self.ser.close()
            self.log_message("串口连接已关闭-Disconnected!")
    
    def send_command(self, command):
        """发送自定义命令"""
        if not self.ser or not self.ser.is_open:
            self.log_message("错误：未连接串口-Error: Not connected!")
            return
        
        try:
            self.ser.write(f"{command}\n".encode())
            self.log_message(f"Sent: {command}")
        except Exception as e:
            self.log_message(f"Error: {str(e)}")
    
    def send_custom_command(self):
        """发送用户自定义的命令"""
        command = self.custom_command.text().strip()
        if not command:
            self.log_message("错误：指令不能为空-Error: Command cannot be empty!")
            return
        
        self.send_command(command)
        self.custom_command.clear()
    
    def clear_status(self):
        """清除状态监控区域的内容"""
        self.status_text.clear()
    
    def log_message(self, message):
        """在状态框显示消息"""
        self.status_text.append(message)
        # 滚动到底部
        self.status_text.verticalScrollBar().setValue(
            self.status_text.verticalScrollBar().maximum()
        )
    
    def closeEvent(self, event):
        """关闭窗口时的清理操作"""
        self.running[0] = False
        if self.ser and self.ser.is_open:
            self.ser.close()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MotorControlApp()
    window.show()
    sys.exit(app.exec_())