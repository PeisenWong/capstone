from pymodbus.client import ModbusTcpClient

def main():
    # Replace with your robot controller's IP address
    robot_ip = '192.168.0.2'  # Update this
    robot_port = 502  # Default Modbus TCP port is 502

    # Create a Modbus TCP client
    client = ModbusTcpClient(robot_ip, port=robot_port)

    # Connect to the robot controller
    if not client.connect():
        print('Unable to connect to the robot controller.')
        return

    # Define parameters based on your command
    slave_id = 2           # I2 in your command
    register_address = 60  # A60000 in your command
    value = 0              # X1 in your command

    # Write value to the register
    try:
        response = client.write_register(register_address, value, slave=slave_id)

        if response.isError():
            print(f'Error writing to register {register_address}: {response}')
        else:
            print(f'Successfully wrote value {value} to register {register_address}')
    except Exception as e:
        print(f'Exception during write operation: {e}')

    # Optionally, read back the value
    try:
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

if __name__ == '__main__':
    main()
