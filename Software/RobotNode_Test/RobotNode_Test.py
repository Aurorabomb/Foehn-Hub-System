import serial
import time

metadata = {
    'protocolName': '# Foehn-α Test.py',
    'author': 'Yueyang Gao',
    'date of birth': '2025/08/26',
    'description': 'Control test of the Foehn-Alpha Central Node:'
                    'Burning wind of the free world, Good luck...commander!',
}

# 1.Connect to the Foehn-Alpha Central Node | use your USB Cable
def connect_to_Foehn(Foehn_port="COM3"):
    try:
        Foehn = serial.Serial(
            Foehn_port, 
            baudrate = 9600, 
            timeout = 2, 
            dsrdtr=False, 
            rtscts = False ) # Prohibit DTR, RTS & CTS 
        
        time.sleep(0.5)    # Ensure the Initilization
        print(f"Successfully connected to {Foehn_port}")
        return Foehn

    except serial.SerialException as e:
        print(f"Connection failed: {str(e)}")
        return None


# 2.Define the command format
def send_command(Foehn, command):
    if not Foehn or not Foehn.is_open:
        print("Device not connected!")
        return None
    
    # 2.1 Format adjust: terminated with CR-LF | 以\r\n结尾
    full_cmd = command if command.endswith('\n') else command + '\n'
    encoded_cmd = full_cmd.encode('utf-8') 

    try:
        Foehn.reset_input_buffer()
        Foehn.write(encoded_cmd)
        print(f"Sent: {full_cmd.strip()}")
        
        # Ensure the responsiveness of the Foehn
        time.sleep(0.5)
        
        response = Foehn.read_until(b'\n') # 原始response
        decoded_res = response.decode('utf-8', errors='ignore').strip()  # 通用response
        return decoded_res
    
    except serial.SerialException as e:
        print(f"Communication error: {str(e)}")
        return None


# 3 Test of the Foehn-Alpha
def main():
    "测试一下指令集"
    # 连接Foehn 
    Foehn_device = connect_to_Foehn()
    if not Foehn_device:
        print("Exiting program.")
        return
    # List of all commands    
    print("\n--- Good morning, welcome to the Foehn Control Test ---")
    print("---------------------")
    print("Available commands:")
    print("0. Foehn - Initilization Process")
    print("1. INFO.  - Device name and description")
    print("2. SSS  - Stop all sub modules")
    print("3. A  - Start the stirrer")
    print("4. B  - Stop the stirrer")
    print("5. 1F128  - Start Pump1 with 50%_flowrate")
    print("6. TEST  - Sequential test of the Foehn-Alpha")  
    print("7. EXIT    - Exit program")
    print("---------------------")
    
    try:
        while True:
            cmd = input("\nEnter command: ").strip()
            
            if cmd == "EXIT":
                break
                
            # Specific command lists
            if cmd == "TEST":
                # Start the test sequence
                print("\nRunning test sequence...")
                test_commands = [
                    "Foehn",                        # Initialization
                    "NOTE",
                    "INFO",
                    "1F128",                        # Pump1 pumps in at 50% flowrate
                    "A6",                           # Start the stirrer for 6s
                    "2B200",                        # Pump2 pumps out at 90% flowrate
                    "3F190",                        # Pump3 pumps in at 90% flowrate  (max flowrate: 255)
                    "SSS"                           # Stop all modules
                ]
                
                for test_cmd in test_commands:
                    response = send_command(Foehn_device, test_cmd)
                    print(f"---Foehn-α: {response}")
                    time.sleep(3)
                continue
            
            # Get the response
            response = send_command(Foehn_device, cmd)
            
            if response is not None:
                print(f"---Foehn-α: {response}")
            else:
                print("No response received")
                
    except KeyboardInterrupt:
        print("\nProgram interrupted by user")
    
    finally:
        # Ensure the Foehn is closed safely
        if Foehn_device.is_open:
            send_command(Foehn_device, "SSS")
            Foehn_device.close()
            print("Device connection closed")
        print("Exiting program")

if __name__ == "__main__":
    main()

