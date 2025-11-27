// BIOS版本号
char BIOS[] = "22101731H2.10";

// L298N-1针脚定义
const int ENA_1 = 5;   // 电机1 PWM调速引脚-黑
const int IN1_1 = 2;   // 电机1方向控制引脚1-白
const int IN2_1 = 3;   // 电机1方向控制引脚2-灰
const int ENB_1 = 6;  // 电机2 PWM调速引脚-绿
const int IN3_1 = 4;   // 电机2方向控制引脚1-紫
const int IN4_1 = 7;   // 电机2方向控制引脚2-蓝
// L298N-2针脚定义
const int ENA_2 = 11;   // 电机3 PWM调速引脚-黄
const int IN1_2 = 13;   // 电机3方向控制引脚1-桔
const int IN2_2 = 12;   // 电机3方向控制引脚2-红
const int ENB_2 = 10;  // 电机4 PWM调速引脚-白
const int IN3_2 = 9;   // 电机4方向控制引脚1-棕
const int IN4_2 = 8;   // 电机4方向控制引脚2-黑

// Stirrer针脚定义
const int magPin = 16; //磁力搅拌通断针脚1-白
//const int magPin = 15; //磁力搅拌通断针脚1-灰 [预留，暂时废弃]
//const int magPin = 16; //磁力搅拌通断针脚1-紫 [预留，暂时废弃]

// Signal Light针脚定义
const int light_R = A3; //红色信号灯
const int light_Y = A4; //黄色信号灯
const int light_G = A5; //绿色信号灯

// 添加全局定时器变量
unsigned long magStartTime = 0; // 是一种无符号整数类型，用于存储非负整数数据
unsigned long magDuration = 5000; // 默认持续时间5秒
unsigned long R_ledStartTime = 0; // 是一种无符号整数类型，用于存储非负整数数据
unsigned long R_ledDuration = 2000; // 默认持续时间2秒
unsigned long Y_ledStartTime = 0; // 是一种无符号整数类型，用于存储非负整数数据
unsigned long Y_ledDuration = 2000; // 默认持续时间2秒
unsigned long G_ledStartTime = 0; // 是一种无符号整数类型，用于存储非负整数数据
unsigned long G_ledDuration = 2000; // 默认持续时间2秒
unsigned long group_ledStartTime = 0; // 是一种无符号整数类型，用于存储非负整数数据
unsigned long group_ledDuration = 2000; // 默认持续时间2秒
// 添加4通道泵开关定时器
unsigned long P1_StartTime = 0; 
unsigned long P2_StartTime = 0; 
unsigned long P3_StartTime = 0; 
unsigned long P4_StartTime = 0; 
unsigned long P1_Duration = 5000; // 泵默认开启时间5秒
unsigned long P2_Duration = 5000; // 泵默认开启时间5秒
unsigned long P3_Duration = 5000; // 泵默认开启时间5秒
unsigned long P4_Duration = 5000; // 泵默认开启时间5秒


// 添加布尔变量用于LED控制
bool magActive = false; //异步操作架构，开启搅拌并持续监听其他命令
bool R_ledActive = false; //添加R信号灯控制布尔变量
bool Y_ledActive = false; //添加Y信号灯控制布尔变量
bool G_ledActive = false; //添加G信号灯控制布尔变量
bool P1_Active = false; //添加泵1状态变量
bool P2_Active = false; //添加泵2状态变量
bool P3_Active = false; //添加泵3状态变量
bool P4_Active = false; //添加泵4状态变量
bool group_ledActive = false; //LED组内控制-Foehn初始化指令

void setup() {
  // 初始化L298N引脚模式-#1 控制泵1&2
  pinMode(ENA_1, OUTPUT);
  pinMode(IN1_1, OUTPUT);
  pinMode(IN2_1, OUTPUT);
  pinMode(ENB_1, OUTPUT);
  pinMode(IN3_1, OUTPUT);
  pinMode(IN4_1, OUTPUT);
  // 初始化L298N引脚模式-#2 控制泵3&4
  pinMode(ENA_2, OUTPUT);
  pinMode(IN1_2, OUTPUT);
  pinMode(IN2_2, OUTPUT);
  pinMode(ENB_2, OUTPUT);
  pinMode(IN3_2, OUTPUT);
  pinMode(IN4_2, OUTPUT);

  pinMode(magPin, OUTPUT);
  pinMode(light_R, OUTPUT);
  pinMode(light_Y, OUTPUT);
  pinMode(light_G, OUTPUT);

  Serial.begin(9600);
}

void loop() {
  // 检查Stir定时器
  if (magActive && (millis() - magStartTime >= magDuration)) {
    digitalWrite(magPin, LOW); //初始化时间均为0，不会触发关闭定时器
    magActive = false;
    digitalWrite(light_Y, LOW);
    Y_ledActive = false;
    Serial.print("Mag_stir auto-off after ");
    Serial.print(magDuration / 1000); // 显示秒数
    Serial.println(" seconds! 磁搅已自动关闭！");
  }

  // 检查P1定时器
  if (P1_Active && (millis() - P1_StartTime >= P1_Duration)) {
    P1_Active = false; //初始化时间均为0，不会触发关闭定时器
    digitalWrite(IN1_1, LOW);
    digitalWrite(IN2_1, LOW);
    analogWrite(ENA_1, 0);

    Serial.print("Safe trigger for P1 after ");
    Serial.print(P1_Duration / 1000.0, 3);  // 强制浮点运算并显示3位小数
    Serial.println(" s! P1已自动关闭！");
  }

// 检查P2定时器
  if (P2_Active && (millis() - P2_StartTime >= P2_Duration)) {
    P2_Active = false; //初始化时间均为0，不会触发关闭定时器
    digitalWrite(IN3_1, LOW);
    digitalWrite(IN4_1, LOW);
    analogWrite(ENB_1, 0);

    Serial.print("Safe trigger for P2 after ");
    Serial.print(P2_Duration / 1000.0, 3);  // 强制浮点运算并显示3位小数
    Serial.println(" s! P2已自动关闭！");
  }

// 检查P3定时器
  if (P3_Active && (millis() - P3_StartTime >= P3_Duration)) {
    P3_Active = false; //初始化时间均为0，不会触发关闭定时器
    digitalWrite(IN1_2, LOW);
    digitalWrite(IN2_2, LOW);
    analogWrite(ENA_2, 0);

    Serial.print("Safe trigger for P3 after ");
    Serial.print(P3_Duration / 1000.0, 3);  // 强制浮点运算并显示3位小数
    Serial.println(" s! P3已自动关闭！");
  }

// 检查P4定时器
  if (P4_Active && (millis() - P4_StartTime >= P4_Duration)) {
    P4_Active = false; //初始化时间均为0，不会触发关闭定时器
    digitalWrite(IN3_2, LOW);
    digitalWrite(IN4_2, LOW);
    analogWrite(ENB_2, 0);
    Serial.print("Safe trigger for P4 after ");
    Serial.print(P4_Duration / 1000.0, 3);  // 强制浮点运算并显示3位小数
    Serial.println(" s! P4已自动关闭！");
  }

  // 初始化检查3通信号灯定时器-Foehn指令[2s内不建议其他LED指令插入]
  if (group_ledActive && (millis() - group_ledStartTime >= group_ledDuration)) {
    digitalWrite(light_R, LOW); //初始化时间均为0，不会触发关闭定时器
    digitalWrite(light_Y, LOW); //初始化时间均为0，不会触发关闭定时器
    digitalWrite(light_G, LOW); //初始化时间均为0，不会触发关闭定时器
    group_ledActive = false;
    //Serial.print("Status light auto-off after ");
    //Serial.print(group_ledDuration / 1000); // 显示秒数
    //Serial.println(" seconds! 信号灯已自动关闭！");
  }
  // 初始化检查红色信号灯定时器-异常指令状态灯
  if (R_ledActive && (millis() - R_ledStartTime >= R_ledDuration)) {
    digitalWrite(light_R, LOW); //For turnning off unknown command status
    R_ledActive = false;
  }

  // 初始化检查泵运行状态|任意泵开启即为绿灯
  if (P1_Active ||P2_Active||P3_Active||P4_Active) {
    digitalWrite(light_G, HIGH); 
  } 
  else if (P1_Active == false && P2_Active == false && P3_Active == false && P4_Active == false && group_ledActive == false) {
    digitalWrite(light_G, LOW); 
  }

  // 读取串口行命令
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n'); // 读取整行命令
    command.trim(); // 移除前后空白字符
    
    // 分析Flex命令格式是否用于Pump模块
    char motor = command[0]; // 第一个字符表示电机（1或2）
    char action = command[1]; // 第二个字符表示动作（F/B/S）
    
    // 1.磁力搅拌模块 | A300, B, SS(Invalid)
    if (command.startsWith("A")) {
      // 解析持续时间参数
      if (command.length() > 1) {
        String durationStr = command.substring(1); // 获取'A'后面的数字部分
        unsigned long newDuration = durationStr.toInt() * 1000UL; // 转换为毫秒
        
        // 验证参数有效性（100ms - 24小时）
        if (newDuration >= 100 && newDuration <= 86400000UL) {
          magDuration = newDuration;
          Y_ledDuration = newDuration; //led与搅拌持续时长保持同步
        } else {
          Serial.println("Invalid duration! Using default 5s.");
          magDuration = 5000;
          Y_ledDuration = 5000; //led与搅拌持续时长保持同步
        }
      } else {
        // 没有指定时间，使用默认值
        magDuration = 5000;
        Y_ledDuration = 5000;
      }
  
      digitalWrite(magPin, HIGH);
      digitalWrite(light_Y, HIGH);
      magStartTime = millis(); // 打开磁搅后开启计时器
      Y_ledStartTime = magStartTime; // 打开磁搅后开启计时器
      magActive = true;
      Y_ledActive = true;
      Serial.print("Mag_stir start! Duration: ");
      Serial.print(magDuration / 1000);
      Serial.println("s");
      
    } else if (command == "B") {
      digitalWrite(magPin, LOW);
      digitalWrite(light_Y, LOW);
      magActive = false;
      Y_ledActive = false; 
      Serial.println("Mag_stir stop!");
    }
      else if (command == "Foehn") {
      digitalWrite(light_R, HIGH);
      digitalWrite(light_Y, HIGH);
      digitalWrite(light_G, HIGH);
      group_ledStartTime = millis(); // 打开磁搅后开启计时器
      group_ledDuration = 2000; //避免duration指令覆盖| 比如先A300后Foehn会导致红绿灯无法关闭
      group_ledActive = true; 
      Serial.println("Foehn Agent for Yueyang is Already Online..."); //成功初始化_老子的代理已上线
    }

    // 2.电机控制模块 1F128, 2S, 1B255, 3F70, 4B255
    else if (motor == '1' || motor == '2' || motor == '3' || motor == '4') {
      // 查找时间参数T
      int tIndex = command.indexOf('T');
      unsigned long duration = 5000;  // 默认持续时间5秒
      String speedStr;
      
      if (tIndex != -1) {
        // 提取速度部分（T之前）
        speedStr = command.substring(2, tIndex);
        // 提取时间部分（T之后）
        String timeStr = command.substring(tIndex + 1);
        unsigned long timeVal = timeStr.toInt();
        
        // 验证时间范围（100ms - 24小时）
        if (timeVal >= 100 && timeVal <= 86400000UL) {
          duration = timeVal;
        } else {
          Serial.println("Invalid time! Using default 5000ms.");
        }
      } else {
        // 没有时间参数
        speedStr = command.substring(2);
      }
      
      int speed = speedStr.toInt();
      speed = constrain(speed, 0, 255);  // 限制速度范围
      
      // 设置对应泵的工作函数
      if (motor == '1') {
        //P1_Duration = duration;
        controlMotor1(action, speed, duration);
      } else if (motor == '2') {
        //P2_Duration = duration;
        controlMotor2(action, speed, duration);
      } else if (motor == '3') {
        //P3_Duration = duration;
        controlMotor3(action, speed, duration);
      } else if (motor == '4') {
        //P4_Duration = duration;
        controlMotor4(action, speed, duration);
      }
      //Serial.print(", Duration: "); //持续时间统一添加到控制函数内，保证执行后返回响应一致
      //Serial.print(duration);
      //Serial.println("ms");
    }

     // 3. 全局控制指令 
     // 3.1 紧急停车，关闭所有运行模块
      else if (command == "SSS") {
      Serial.println("Stop all modules..."); //停止全部模组
      controlMotor1('S', 0, 0);
      controlMotor2('S', 0, 0);
      controlMotor3('S', 0, 0);
      controlMotor4('S', 0, 0);
      digitalWrite(magPin, LOW);
      magActive = false; //关磁搅
      digitalWrite(light_R, LOW);
      digitalWrite(light_Y, LOW);
      digitalWrite(light_G, LOW);
      Y_ledActive = false;  //关磁搅指示灯
    }
    // 3.2 BIOS信息
      else if (command == "BIOS") {
      Serial.print("Built in CPU: UNO R3 ATmega328P @ 16 MHz AVR");
      Serial.print(" ===Jupiter OS: ");
      Serial.print(BIOS);
      Serial.println("===");
    }

    // 3.3 原型机出生日期-Prototype of Foehn Dock
      else if (command == "INFO") {
      Serial.print("---My name is Foehn, the burning wind for the free world!");
      Serial.println(" | My birthday is 21 June 2025 11:32 A.M. UTC+1---");
    }

    // 3.4 设计组装信息
      else if (command == "NOTE") {
      Serial.print("---Designed by Yueyang Gao in London");
      Serial.println(" | Assembled in UK---");
    }

     // 4. 错误指令集不予执行
      else if (command.length() > 0) {
      Serial.println("Unknown command!");
      digitalWrite(light_R, HIGH);
      R_ledStartTime = millis(); // 打开磁搅后开启计时器
      R_ledDuration = 2000; //避免duration指令覆盖
      R_ledActive = true; 
    }
  }
}
// 控制电机1
void controlMotor1(char action, int speed, unsigned long duration) {
  switch(action) {
    case 'F': // 正转
      digitalWrite(IN1_1, HIGH);
      digitalWrite(IN2_1, LOW);
      analogWrite(ENA_1, speed);
      P1_StartTime = millis();
      P1_Active = true;
      break;
    case 'B': // 反转
      digitalWrite(IN1_1, LOW);
      digitalWrite(IN2_1, HIGH);
      analogWrite(ENA_1, speed);
      P1_StartTime = millis();
      P1_Active = true;
      break;
    case 'S': // 停止
      digitalWrite(IN1_1, LOW);
      digitalWrite(IN2_1, LOW);
      analogWrite(ENA_1, 0);
      P1_Active = false;
      duration = 0;
      break;
    default:
      Serial.println("Invalid direction! Use F/B/S.");
  }
  P1_Duration = duration;
  Serial.print("Pump1: ");
  Serial.print(action);
  Serial.print(", Flowrate: ");
  Serial.print(speed);
  Serial.print(", Duration: ");
  Serial.print(duration/1000.0, 3); // 返回秒数，强制转换3位小数
  Serial.println("s");
  
}

// 控制电机2
void controlMotor2(char action, int speed, unsigned long duration) {
  switch(action) {
    case 'F': // 正转
      digitalWrite(IN3_1, HIGH);
      digitalWrite(IN4_1, LOW);
      analogWrite(ENB_1, speed);
      P2_StartTime = millis();
      P2_Active = true;
      break;
    case 'B': // 反转
      digitalWrite(IN3_1, LOW);
      digitalWrite(IN4_1, HIGH);
      analogWrite(ENB_1, speed);
      P2_StartTime = millis();
      P2_Active = true;
      break;
    case 'S': // 停止
      digitalWrite(IN3_1, LOW);
      digitalWrite(IN4_1, LOW);
      analogWrite(ENB_1, 0);
      P2_Active = false;
      duration = 0;
      break;
    default:
      Serial.println("Invalid direction! Use F/B/S.");
  }
  P2_Duration = duration;
  Serial.print("Pump2: ");
  Serial.print(action);
  Serial.print(", Flowrate: ");
  Serial.print(speed);
  Serial.print(", Duration: ");
  Serial.print(duration/1000.0, 3); // 返回秒数，强制转换3位小数
  Serial.println("s");
}

// 控制电机3
void controlMotor3(char action, int speed, unsigned long duration) {
  switch(action) {
    case 'F': // 正转
      digitalWrite(IN1_2, HIGH);
      digitalWrite(IN2_2, LOW);
      analogWrite(ENA_2, speed);
      P3_StartTime = millis();
      P3_Active = true;
      break;
    case 'B': // 反转
      digitalWrite(IN1_2, LOW);
      digitalWrite(IN2_2, HIGH);
      analogWrite(ENA_2, speed);
      P3_StartTime = millis();
      P3_Active = true;
      break;
    case 'S': // 停止
      digitalWrite(IN1_2, LOW);
      digitalWrite(IN2_2, LOW);
      analogWrite(ENA_2, 0);
      duration = 0;
      P3_Active = false;
      break;
    default:
      Serial.println("Invalid direction! Use F/B/S.");
  }
  P3_Duration = duration;
  Serial.print("Pump3: ");
  Serial.print(action);
  Serial.print(", Flowrate: ");
  Serial.print(speed);
  Serial.print(", Duration: ");
  Serial.print(duration/1000.0, 3); // 返回秒数，强制转换3位小数
  Serial.println("s");
}

// 控制电机4
void controlMotor4(char action, int speed, unsigned long duration) {
  switch(action) {
    case 'F': // 正转
      digitalWrite(IN3_2, HIGH);
      digitalWrite(IN4_2, LOW);
      analogWrite(ENB_2, speed);
      P4_StartTime = millis();
      P4_Active = true;
      break;
    case 'B': // 反转
      digitalWrite(IN3_2, LOW);
      digitalWrite(IN4_2, HIGH);
      analogWrite(ENB_2, speed);
      P4_StartTime = millis();
      P4_Active = true;
      break;
    case 'S': // 停止
      digitalWrite(IN3_2, LOW);
      digitalWrite(IN4_2, LOW);
      analogWrite(ENB_2, 0);
      P4_Active = false;
      duration = 0;
      break;
    default:
      Serial.println("Invalid direction! Use F/B/S.");
  }
  P4_Duration = duration;
  Serial.print("Pump4: ");
  Serial.print(action);
  Serial.print(", Flowrate: ");
  Serial.print(speed);
  Serial.print(", Duration: ");
  Serial.print(duration/1000.0, 3); // 返回秒数，强制转换3位小数
  Serial.println("s");
}