from pymodbus.client import ModbusTcpClient
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)  # Enable detailed debugging logs

def main():
    # Replace with your robot controller's IP address
    robot_ip = '192.168.0.2'
    robot_port = 502  # Default Modbus TCP port is 502

    # Create a Modbus TCP client
    client = ModbusTcpClient(robot_ip, port=robot_port)

    # Connect to the robot controller
    if not client.connect():
        print('Unable to connect to the robot controller.')
        return
    print('Connected to the robot controller.')

    # Define parameters
    slave_id = 2           # I2 in your command
    register_address = 33  # A60000 in your command
    value = 50             # X1 in your command

    # Write value to the register
    try:
        if not client.is_socket_open():
            print("Socket not open. Reconnecting...")
            client.connect()

        response = client.write_register(register_address, value, slave=slave_id)

        if response.isError():
            print(f'Error writing to register {register_address}: {response}')
        else:
            print(f'Successfully wrote value {value} to register {register_address}')
    except Exception as e:
        print(f'Exception during write operation: {e}')

    # Read back the value
    try:
        if not client.is_socket_open():
            print("Socket not open. Reconnecting...")
            client.connect()

        read_response = client.read_holding_registers(register_address, count=1, slave=slave_id)
        if read_response.isError():
            print(f'Error reading register {register_address}: {read_response}')
        else:
            read_value = read_response.registers[0]
            print(f'Read value from register {register_address}: {read_value}')
    except Exception as e:
        print(f'Exception during read operation: {e}')

    # Close the client connection
    client.close()
    print('Disconnected from the robot controller.')

main()
