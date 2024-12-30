from pymodbus.client import ModbusTcpClient
import time

class RobotController:
    def __init__(self, ip_address = "192.168.0.2", port=502):
        """
        Initialize the RobotController.
        :param ip_address: IP address of the robot controller
        :param port: Modbus TCP port (default is 502)
        """
        self.ip_address = ip_address
        self.port = port
        self.client = None
        self.connected = False

    def connect(self):
        """
        Establish connection to the robot controller.
        """
        if not self.client:
            self.client = ModbusTcpClient(self.ip_address, port=self.port)
        self.connected = self.client.connect()
        if not self.connected:
            raise ConnectionError(f"Unable to connect to the robot controller at {self.ip_address}:{self.port}")

    def disconnect(self):
        """
        Close the connection to the robot controller.
        """
        if self.client:
            self.client.close()
            self.connected = False

    def write(self, register_address, value, slave_id = 2):
        """
        Write a value to a specific register.
        :param register_address: Address of the register
        :param value: Value to write
        :param slave_id: Slave ID of the Modbus device
        """
        # if not self.connected:
        #     raise ConnectionError("Not connected to the robot controller.")
        if self.connected:
            print("Connected to the robot controller. Waiting for commands...")

            if not self.client.is_socket_open():
                print("Reconnecting...")
                self.connect()
            
            try:
                response = self.client.write_register(register_address*2+1, value, slave=slave_id)
            except BrokenPipeError:
                self.client = ModbusTcpClient(self.ip_address, port=self.port)
                self.connected = self.client.connect()
                response = self.client.write_register(register_address*2+1, value, slave=slave_id)

            if response.isError():
                raise ValueError(f"Error writing to register {register_address}: {response}")
            print(f"Successfully wrote value {value} to register {register_address}")

    def read_register(self, register_address, slave_id = 2):
        """
        Read a value from a specific register.
        :param register_address: Address of the register
        :param slave_id: Slave ID of the Modbus device
        :return: The value read from the register
        """
        # if not self.connected:
        #     raise ConnectionError("Not connected to the robot controller.")
        
        response = self.client.read_holding_registers(register_address*2+1, count=1, slave=slave_id)
        if response.isError():
            raise ValueError(f"Error reading register {register_address}: {response}")
        
        value = response.registers[0]
        print(f"Read value from register {register_address}: {value}")
        return value

    def start(self):
        """
        Example function to start the robotic arm.
        """
        # Define the address and value based on your protocol
        self.client = ModbusTcpClient(self.ip_address, port=self.port)
        self.connected = self.client.connect()
        self.write(register_address=65, value=1, slave_id=2)
        self.write(register_address=66, value=1, slave_id=2)
        self.write(register_address=67, value=0, slave_id=2)
        self.write(register_address=15213, value=30, slave_id=2)
        self.client.close()

    def stop(self):
        """
        Example function to stop the robotic arm.
        """
        # Define the address and value based on your protocol
        self.client = ModbusTcpClient(self.ip_address, port=self.port)
        self.connected = self.client.connect()
        self.write(register_address=65, value=1, slave_id=2)
        self.write(register_address=66, value=1, slave_id=2)
        self.write(register_address=67, value=1, slave_id=2)
        self.client.close()

    def fast(self):
        self.client = ModbusTcpClient(self.ip_address, port=self.port)
        self.connected = self.client.connect()
        self.write(register_address=65, value=1, slave_id=2)
        self.write(register_address=66, value=1, slave_id=2)
        self.write(register_address=15213, value=70, slave_id=2)
        self.client.close()

    def normal_speed(self):
        self.client = ModbusTcpClient(self.ip_address, port=self.port)
        self.connected = self.client.connect()
        self.write(register_address=65, value=1, slave_id=2)
        self.write(register_address=66, value=1, slave_id=2)
        self.write(register_address=15213, value=30, slave_id=2)
        self.client.close()

    def slow(self):
        self.client = ModbusTcpClient(self.ip_address, port=self.port)
        self.connected = self.client.connect()
        self.write(register_address=65, value=1, slave_id=2)
        self.write(register_address=66, value=1, slave_id=2)
        self.write(register_address=15213, value=10, slave_id=2)
        self.client.close()

    def servo_off(self):
        self.client = ModbusTcpClient(self.ip_address, port=self.port)
        self.connected = self.client.connect()
        self.write(register_address=65, value=0, slave_id=2)
        self.write(register_address=66, value=0, slave_id=2)
        self.write(register_address=67, value=0, slave_id=2)
        self.client.close()

# Testing logic directly in the same file
if __name__ == '__main__':
    robot_controller = RobotController()

    print("""
    Enter a command:
    s - Start the robot
    p - Stop the robot
    f - Set speed to fast
    l - Set speed to slow
    q - Quit the program
    """)

    while True:
        command = input("Enter command: ").strip().lower()

        if command == 's':
            print("Starting the robot...")
            robot_controller.start()
        elif command == 'p':
            print("Stopping the robot...")
            robot_controller.stop()
        elif command == 'f':
            print("Setting speed to fast...")
            robot_controller.normal_speed()
        elif command == 'l':
            print("Setting speed to slow...")
            robot_controller.slow()
        elif command == 'o':
            print("Setting speed to slow...")
            robot_controller.servo_off()
        elif command == 'q':
            print("Exiting the program...")
            break
        else:
            print("Invalid command. Please enter s, p, f, l, or q.")

"""
C36: Emergency Stop (Connected to R60)
C37: External RESET Command (Connected to R61)
R16: FeedRate Override (Fast: 70%, Slow: 20%)
R17: JOG Override (Fast: 70%, Slow: 20%)
"""
