from pymodbus.client import ModbusTcpClient

robot_ip = '192.168.0.2'
robot_port = 502
register_address = 120

client = ModbusTcpClient(robot_ip, port=robot_port)

for slave_id in range(1, 10):  # Adjust the range as needed
    print(f"Testing Slave ID: {slave_id}")
    if client.connect():
        response = client.read_holding_registers(register_address, count=1, slave=slave_id)
        if not response.isError():
            print(f"Success with Slave ID: {slave_id}")
            print(f"Response: {response.registers}")
            break
        else:
            print(f"No response for Slave ID: {slave_id}")
        client.close()
