from pymodbus.client import ModbusTcpClient

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

    def write_register(self, register_address, value, slave_id = 2):
        """
        Write a value to a specific register.
        :param register_address: Address of the register
        :param value: Value to write
        :param slave_id: Slave ID of the Modbus device
        """
        if not self.connected:
            raise ConnectionError("Not connected to the robot controller.")
        
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
        if not self.connected:
            raise ConnectionError("Not connected to the robot controller.")
        
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
        self.write_register(register_address=60, value=0, slave_id=2)
        self.write_register(register_address=61, value=1, slave_id=2)

    def stop(self):
        """
        Example function to stop the robotic arm.
        """
        # Define the address and value based on your protocol
        self.write_register(register_address=60, value=1, slave_id=2)

    def fast(self):
        self.write_register(register_address=16, value=70, slave_id=2)
        self.write_register(register_address=17, value=70, slave_id=2)

    def slow(self):
        self.write_register(register_address=16, value=20, slave_id=2)
        self.write_register(register_address=17, value=20, slave_id=2)

    def set_speed(self, speed):
        """
        Example function to set the speed of the robotic arm.
        :param speed: Speed value (e.g., 0 for slow, 1 for fast)
        """
        if speed not in (0, 1):
            raise ValueError("Invalid speed. Use 0 for slow or 1 for fast.")
        self.write_register(register_address=101, value=speed, slave_id=1)


# Testing logic directly in the same file
if __name__ == '__main__':
    robot_controller = RobotController()

    try:
        robot_controller.connect()
        print("Connected to the robot controller. Waiting for commands...")

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
                robot_controller.fast()
            elif command == 'l':
                print("Setting speed to slow...")
                robot_controller.slow()
            elif command == 'q':
                print("Exiting the program...")
                break
            else:
                print("Invalid command. Please enter s, p, f, l, or q.")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        robot_controller.disconnect()
        print("Disconnected from the robot controller.")

"""
C36: Emergency Stop (Connected to R60)
C37: External RESET Command (Connected to R61)
R16: FeedRate Override (Fast: 70%, Slow: 20%)
R17: JOG Override (Fast: 70%, Slow: 20%)
"""
