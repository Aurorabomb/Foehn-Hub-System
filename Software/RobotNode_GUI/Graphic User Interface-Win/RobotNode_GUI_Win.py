import serial
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from serial.tools import list_ports
import os
import sys

class MotorControlApp:
    def __init__(self, root):
        self.root = root
        # ========== 新增图标设置 ==========
        try:
            # 优先尝试当前目录
            script_dir = os.path.dirname(os.path.abspath(__file__))
            icon_path = os.path.join(script_dir, '1.ico')
            self.root.iconbitmap(icon_path)
            # 获取脚本所在目录的绝对路径
        except tk.TclError:
            try:
                # 尝试打包后的临时目录
                base_path = sys._MEIPASS
            except AttributeError:
                base_path = os.path.abspath(".")
            icon_path = os.path.join(base_path, '1.ico')
            self.root.iconbitmap(icon_path)
        # ================================
        self.ser = None
        self.running = False
        self.current_speed_1 = 0
        self.current_speed_2 = 0
        self.current_speed_3 = 0
        self.current_speed_4 = 0
        self.current_direction_1 = "STOP"
        self.current_direction_2 = "STOP"
        self.current_direction_3 = "STOP"
        self.current_direction_4 = "STOP"
        
        # 创建界面
        self.setup_ui()
        
        # 自动检测可用串口
        self.refresh_ports()

    def setup_ui(self):
        """初始化用户界面组件"""
        self.root.title("焚风中枢-Foehn Central Node GUI v1.5")
        
        # 创建主框架和滚动条
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 串口选择区域
        port_frame = ttk.LabelFrame(scrollable_frame, text="串口设置-Port Setup")
        port_frame.grid(row=0, column=0, columnspan=2, padx=10, pady=5, sticky="ew")
        
        self.port_combobox = ttk.Combobox(port_frame, width=15)
        self.port_combobox.grid(row=0, column=0, padx=5)
        
        ttk.Button(port_frame, text="刷新端口-Refresh", command=self.refresh_ports).grid(row=0, column=1, padx=5)
        ttk.Button(port_frame, text="连接-Connect", command=self.connect_serial).grid(row=0, column=2, padx=5)
        ttk.Button(port_frame, text="断开-Disconnect", command=self.disconnect_serial).grid(row=0, column=3, padx=5)
        
        # 创建泵控制的主框架（2x2网格）
        pumps_frame = ttk.Frame(scrollable_frame)
        pumps_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=5, sticky="nsew")
        
        # 电机1控制区域 - 左上
        control_frame_1 = ttk.LabelFrame(pumps_frame, text="电机1控制-Pump1 Control")
        control_frame_1.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        
        # 1速度控制（现在放在方向控制上方）
        ttk.Label(control_frame_1, text="速度(0-255)-Flow Rate:").grid(row=0, column=0, pady=5, sticky="w")
        self.speed_scale_1 = ttk.Scale(control_frame_1, from_=0, to=255, orient=tk.HORIZONTAL,
                                    command=lambda v: self.speed_entry_1.delete(0, tk.END) or
                                    self.speed_entry_1.insert(0, f"{float(v):.0f}"))
        self.speed_scale_1.set(0)
        self.speed_scale_1.grid(row=0, column=1, columnspan=2, padx=5, sticky="ew")
        
        self.speed_entry_1 = ttk.Entry(control_frame_1, width=5)
        self.speed_entry_1.insert(0, "0")
        self.speed_entry_1.grid(row=0, column=3, padx=5)
        self.speed_entry_1.bind("<Return>", lambda e: self.speed_scale_1.set(self.speed_entry_1.get()))
        
        # 1方向选择（现在放在速度控制下方）
        self.direction_var_1 = tk.StringVar(value="STOP")
        directions = [("抽入-Pump In", "F"), ("停止-Stop", "S"), ("排出-PumpOut", "B")]
        for idx, (text, value) in enumerate(directions):
            rb = ttk.Radiobutton(control_frame_1, text=text, variable=self.direction_var_1,
                                value=value, command=lambda: self.update_motor(1))
            rb.grid(row=2, column=idx, padx=5, pady=5, sticky="w")
        
        # 1持续时间设置（新增加）
        ttk.Label(control_frame_1, text="持续时间(秒)-Duration(s):").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.duration_entry_1 = ttk.Entry(control_frame_1, width=5)
        self.duration_entry_1.insert(0, "5")  # 默认5秒
        self.duration_entry_1.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        # 电机2控制区域 - 右上
        control_frame_2 = ttk.LabelFrame(pumps_frame, text="电机2控制-Pump2 Control")
        control_frame_2.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")

        # 2速度控制（现在放在方向控制上方）
        ttk.Label(control_frame_2, text="速度(0-255)-Flow Rate:").grid(row=0, column=0, pady=5, sticky="w")
        self.speed_scale_2 = ttk.Scale(control_frame_2, from_=0, to=255, orient=tk.HORIZONTAL,
                                    command=lambda v: self.speed_entry_2.delete(0, tk.END) or
                                    self.speed_entry_2.insert(0, f"{float(v):.0f}"))
        self.speed_scale_2.set(0)
        self.speed_scale_2.grid(row=0, column=1, columnspan=2, padx=5, sticky="ew")
        
        self.speed_entry_2 = ttk.Entry(control_frame_2, width=5)
        self.speed_entry_2.insert(0, "0")
        self.speed_entry_2.grid(row=0, column=3, padx=5)
        self.speed_entry_2.bind("<Return>", lambda e: self.speed_scale_2.set(self.speed_entry_2.get()))
        
        # 2方向选择（现在放在速度控制下方）
        self.direction_var_2 = tk.StringVar(value="STOP")
        directions = [("抽入-Pump In", "F"), ("停止-Stop", "S"), ("排出-PumpOut", "B")]
        for idx, (text, value) in enumerate(directions):
            rb = ttk.Radiobutton(control_frame_2, text=text, variable=self.direction_var_2,
                                value=value, command=lambda: self.update_motor(2))
            rb.grid(row=2, column=idx, padx=5, pady=5, sticky="w")
        
        # 2持续时间设置（新增加）
        ttk.Label(control_frame_2, text="持续时间(秒)-Duration(s):").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.duration_entry_2 = ttk.Entry(control_frame_2, width=5)
        self.duration_entry_2.insert(0, "5")  # 默认5秒
        self.duration_entry_2.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        # 电机3控制区域 - 左下
        control_frame_3 = ttk.LabelFrame(pumps_frame, text="电机3控制-Pump3 Control")
        control_frame_3.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")

        # 3速度控制（现在放在方向控制上方）
        ttk.Label(control_frame_3, text="速度(0-255)-Flow Rate:").grid(row=0, column=0, pady=5, sticky="w")
        self.speed_scale_3 = ttk.Scale(control_frame_3, from_=0, to=255, orient=tk.HORIZONTAL,
                                    command=lambda v: self.speed_entry_3.delete(0, tk.END) or
                                    self.speed_entry_3.insert(0, f"{float(v):.0f}"))
        self.speed_scale_3.set(0)
        self.speed_scale_3.grid(row=0, column=1, columnspan=2, padx=5, sticky="ew")
        
        self.speed_entry_3 = ttk.Entry(control_frame_3, width=5)
        self.speed_entry_3.insert(0, "0")
        self.speed_entry_3.grid(row=0, column=3, padx=5)
        self.speed_entry_3.bind("<Return>", lambda e: self.speed_scale_3.set(self.speed_entry_3.get()))
        
        # 3方向选择（现在放在速度控制下方）
        self.direction_var_3 = tk.StringVar(value="STOP")
        directions = [("抽入-Pump In", "F"), ("停止-Stop", "S"), ("排出-PumpOut", "B")]
        for idx, (text, value) in enumerate(directions):
            rb = ttk.Radiobutton(control_frame_3, text=text, variable=self.direction_var_3,
                                value=value, command=lambda: self.update_motor(3))
            rb.grid(row=2, column=idx, padx=5, pady=5, sticky="w")
        
        # 3持续时间设置（新增加）
        ttk.Label(control_frame_3, text="持续时间(秒)-Duration(s):").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.duration_entry_3 = ttk.Entry(control_frame_3, width=5)
        self.duration_entry_3.insert(0, "5")  # 默认5秒
        self.duration_entry_3.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        # 电机4控制区域 - 右下
        control_frame_4 = ttk.LabelFrame(pumps_frame, text="电机4控制-Pump4 Control")
        control_frame_4.grid(row=1, column=1, padx=5, pady=5, sticky="nsew")

        # 4速度控制（现在放在方向控制上方）
        ttk.Label(control_frame_4, text="速度(0-255)-Flow Rate:").grid(row=0, column=0, pady=5, sticky="w")
        self.speed_scale_4 = ttk.Scale(control_frame_4, from_=0, to=255, orient=tk.HORIZONTAL,
                                    command=lambda v: self.speed_entry_4.delete(0, tk.END) or
                                    self.speed_entry_4.insert(0, f"{float(v):.0f}"))
        self.speed_scale_4.set(0)
        self.speed_scale_4.grid(row=0, column=1, columnspan=2, padx=5, sticky="ew")
        
        self.speed_entry_4 = ttk.Entry(control_frame_4, width=5)
        self.speed_entry_4.insert(0, "0")
        self.speed_entry_4.grid(row=0, column=3, padx=5)
        self.speed_entry_4.bind("<Return>", lambda e: self.speed_scale_4.set(self.speed_entry_4.get()))
        
        # 4方向选择（现在放在速度控制下方）
        self.direction_var_4 = tk.StringVar(value="STOP")
        directions = [("抽入-Pump In", "F"), ("停止-Stop", "S"), ("排出-PumpOut", "B")]
        for idx, (text, value) in enumerate(directions):
            rb = ttk.Radiobutton(control_frame_4, text=text, variable=self.direction_var_4,
                                value=value, command=lambda: self.update_motor(4))
            rb.grid(row=2, column=idx, padx=5, pady=5, sticky="w")
        
        # 4持续时间设置（新增加）
        ttk.Label(control_frame_4, text="持续时间(秒)-Duration(s):").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.duration_entry_4 = ttk.Entry(control_frame_4, width=5)
        self.duration_entry_4.insert(0, "5")  # 默认5秒
        self.duration_entry_4.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        # 磁力搅拌控制区域
        stir_frame = ttk.LabelFrame(scrollable_frame, text="磁力搅拌控制-MagStir Control")
        stir_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=5, sticky="ew")
        
        ttk.Label(stir_frame, text="持续时间(秒)-Duration(s):").grid(row=0, column=0, padx=5, pady=5)
        self.stir_duration = ttk.Entry(stir_frame, width=8)
        self.stir_duration.insert(0, "5")
        self.stir_duration.grid(row=0, column=1, padx=5)
        
        ttk.Button(stir_frame, text="开启搅拌-Start", 
                  command=lambda: self.send_command(f"A{self.stir_duration.get()}")).grid(row=0, column=2, padx=5)
        ttk.Button(stir_frame, text="停止搅拌-Stop", 
                  command=lambda: self.send_command("B")).grid(row=0, column=3, padx=5)
        
        # 全局控制指令区域
        global_frame = ttk.LabelFrame(scrollable_frame, text="全局控制指令-Global Commands")
        global_frame.grid(row=3, column=0, columnspan=2, padx=10, pady=5, sticky="ew")
        
        commands = [
            ("紧急停止-SSS", "SSS"),
            ("系统信息-BIOS", "BIOS"),
            ("原型机信息-INFO", "INFO"),
            ("设计信息-NOTE", "NOTE"),
            ("初始化-Foehn", "Foehn")
        ]
        
        for idx, (text, cmd) in enumerate(commands):
            ttk.Button(global_frame, text=text, 
                      command=lambda c=cmd: self.send_command(c)).grid(row=0, column=idx, padx=5, pady=5)
        
        # 自定义指令区域
        custom_frame = ttk.LabelFrame(scrollable_frame, text="自定义指令-Custom Command")
        custom_frame.grid(row=4, column=0, columnspan=2, padx=10, pady=5, sticky="ew")
        
        ttk.Label(custom_frame, text="输入指令:").grid(row=0, column=0, padx=5, pady=5)
        
        self.custom_command = ttk.Entry(custom_frame, width=30)
        self.custom_command.grid(row=0, column=1, padx=5, sticky="ew")
        self.custom_command.bind("<Return>", lambda e: self.send_custom_command())
        
        ttk.Button(custom_frame, text="发送指令-Send", 
                  command=self.send_custom_command).grid(row=0, column=2, padx=5)
        
        # 状态显示
        status_frame = ttk.LabelFrame(scrollable_frame, text="状态监控-Status Check")
        status_frame.grid(row=5, column=0, columnspan=2, padx=10, pady=5, sticky="ew")
        
        # 状态文本区域
        status_text_frame = ttk.Frame(status_frame)
        status_text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.status_text = tk.Text(status_text_frame, height=10)
        self.status_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 添加清除按钮
        button_frame = ttk.Frame(status_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(button_frame, text="清除状态-Clear", 
                  command=self.clear_status).pack(side=tk.RIGHT)
        
        # 初始化串口读取线程
        self.serial_thread = None

    def refresh_ports(self):
        """刷新可用串口列表"""
        ports = [port.device for port in list_ports.comports()]
        self.port_combobox['values'] = ports
        if ports:
            self.port_combobox.set(ports[0])

    def connect_serial(self):
        """连接串口"""
        port = self.port_combobox.get()
        if not port:
            messagebox.showerror("错误", "请选择有效串口！- Error! Please choose the right Port!")
            return
        
        try:
            self.ser = serial.Serial(port, 9600, timeout=1)
            self.running = True
            self.serial_thread = threading.Thread(target=self.read_serial)
            self.serial_thread.daemon = True
            self.serial_thread.start()
            self.log_message(f"已连接串口 {port}-Connected!")
            # 发送初始化命令
            self.send_command("Foehn")
        except Exception as e:
            messagebox.showerror("连接错误", str(e))

    def disconnect_serial(self):
        """断开串口连接"""
        if self.ser and self.ser.is_open:
            self.running = False
            self.ser.close()
            self.log_message("串口连接已关闭-Disconnected!")

    def update_motor(self, id):
        """更新电机状态"""
        if not self.ser or not self.ser.is_open:
            return
        
        # 获取持续时间（秒）并转换为毫秒
        try:
            if id == 1:
                duration_sec = float(self.duration_entry_1.get())
            elif id == 2:
                duration_sec = float(self.duration_entry_2.get())
            elif id == 3:
                duration_sec = float(self.duration_entry_3.get())
            elif id == 4:
                duration_sec = float(self.duration_entry_4.get())
            duration_ms = int(duration_sec * 1000)
        except ValueError:
            duration_ms = 5000  # 默认5秒（5000毫秒）
            self.log_message(f"警告：泵{id}时间格式错误，使用默认5秒")
        
        if id == 1:
            direction = self.direction_var_1.get()
            speed = int(self.speed_scale_1.get())
        elif id == 2:
            direction = self.direction_var_2.get()
            speed = int(self.speed_scale_2.get())
        elif id == 3:
            direction = self.direction_var_3.get()
            speed = int(self.speed_scale_3.get())
        elif id == 4:
            direction = self.direction_var_4.get()
            speed = int(self.speed_scale_4.get())
        
        # 停止命令不需要时间参数
        if direction != "S":
            cmd = f"{id}{direction}{speed}T{duration_ms}\n"
        else:
            cmd = f"{id}S\n"
        
        try:
            self.ser.write(cmd.encode())
            self.log_message(f"Sent: {cmd.strip()}") #发送指令
            #self.log_message(f"泵{id} 持续时间: {duration_sec}秒 ({duration_ms}毫秒)")
        except Exception as e:
            self.log_message(f"Error: {str(e)}")   #发送失败

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
        command = self.custom_command.get().strip()
        if not command:
            self.log_message("错误：指令不能为空-Error: Command cannot be empty!")
            return
            
        self.send_command(command)
        # 清空输入框
        self.custom_command.delete(0, tk.END)
        
    def clear_status(self):
        """清除状态监控区域的内容"""
        self.status_text.delete(1.0, tk.END)

    def read_serial(self):
        """持续读取串口数据"""
        while self.running and self.ser and self.ser.is_open:
            try:
                if self.ser.in_waiting > 0:
                    line = self.ser.readline().decode('utf-8').strip() 
                    self.root.after(0, self.log_message, f"Received: {line}") #接收指令
            except:
                break

    def log_message(self, message):
        """在状态框显示消息"""
        self.status_text.insert(tk.END, message + "\n")
        self.status_text.see(tk.END)

    def on_closing(self):
        """关闭窗口时的清理操作"""
        self.running = False
        if self.ser and self.ser.is_open:
            self.ser.close()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = MotorControlApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()