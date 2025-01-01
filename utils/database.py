import mysql.connector
from mysql.connector import Error
from datetime import datetime

class MySQLHandler:
    def __init__(self):
        """
        Initialize the MySQLHandler class with database connection parameters.
        """
        self.host = "192.168.241.164"
        self.user = "rpi"
        self.password = "pi"
        self.database = "sys"
        self.connection = None

    def connect(self):
        """
        Establish a connection to the MySQL database and ensure required tables exist.
        """
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database
            )
            if self.connection.is_connected():
                print("Connection established successfully!")
                self.ensure_tables_exist()
        except Error as e:
            print(f"Error: '{e}'")
            self.connection = None

    def ensure_tables_exist(self):
        """
        Ensure that the required tables (RobotZones and ZoneLogs) exist in the database.
        """
        try:
            cursor = self.connection.cursor()

            # Create RobotZones table if not exists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS RobotZones (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    robot_id INT NOT NULL,
                    stop_zone_tl_x INT NOT NULL,
                    stop_zone_tl_y INT NOT NULL,
                    stop_zone_tr_x INT NOT NULL,
                    stop_zone_tr_y INT NOT NULL,
                    stop_zone_bl_x INT NOT NULL,
                    stop_zone_bl_y INT NOT NULL,
                    stop_zone_br_x INT NOT NULL,
                    stop_zone_br_y INT NOT NULL,
                    slow_zone_tl_x INT NOT NULL,
                    slow_zone_tl_y INT NOT NULL,
                    slow_zone_tr_x INT NOT NULL,
                    slow_zone_tr_y INT NOT NULL,
                    slow_zone_bl_x INT NOT NULL,
                    slow_zone_bl_y INT NOT NULL,
                    slow_zone_br_x INT NOT NULL,
                    slow_zone_br_y INT NOT NULL
                )
            """)
            print("Verified or created RobotZones table.")

            # Create ZoneLogs table if not exists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ZoneLogs (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    zone_type VARCHAR(255) NOT NULL,
                    log_datetime DATETIME NOT NULL
                )
            """)
            print("Verified or created ZoneLogs table.")

            cursor.close()
        except Error as e:
            print(f"Error ensuring tables exist: '{e}'")

    def insert_log(self, data):
        """
        Insert data into the specified table.
        """
        try:
            cursor = self.connection.cursor()
            
            query = "INSERT INTO ZoneLogs (zone_type, log_datetime) VALUES (%s, %s)"
            cursor.execute(query, data)
            self.connection.commit()
            print("Data inserted successfully!")
            cursor.close()
        except Error as e:
            print(f"Error inserting data: '{e}'")

    def insert_zone(self, data):
        """
        Insert a new record into the RobotZones table if `robot_id = 1` does not exist.
        Otherwise, update the record.
        
        Parameters:
        - data: A tuple containing the values for robot_id and all coordinates.
        """
        try:
            cursor = self.connection.cursor()

            # Check if robot_id = 1 exists
            check_query = "SELECT COUNT(*) FROM RobotZones WHERE robot_id = 1"
            cursor.execute(check_query)
            result = cursor.fetchone()

            if result[0] > 0:
                # If robot_id = 1 exists, update the record
                update_query = """
                    UPDATE RobotZones
                    SET 
                        stop_zone_tl_x = %s, stop_zone_tl_y = %s,
                        stop_zone_tr_x = %s, stop_zone_tr_y = %s,
                        stop_zone_bl_x = %s, stop_zone_bl_y = %s,
                        stop_zone_br_x = %s, stop_zone_br_y = %s,
                        slow_zone_tl_x = %s, slow_zone_tl_y = %s,
                        slow_zone_tr_x = %s, slow_zone_tr_y = %s,
                        slow_zone_bl_x = %s, slow_zone_bl_y = %s,
                        slow_zone_br_x = %s, slow_zone_br_y = %s
                    WHERE robot_id = 1
                """
                cursor.execute(update_query, data[1:])  # Exclude robot_id for update
                print("Record updated successfully!")
            else:
                # If robot_id = 1 does not exist, insert a new record
                insert_query = """
                    INSERT INTO RobotZones (
                        robot_id, stop_zone_tl_x, stop_zone_tl_y,
                        stop_zone_tr_x, stop_zone_tr_y, stop_zone_bl_x, stop_zone_bl_y,
                        stop_zone_br_x, stop_zone_br_y, slow_zone_tl_x, slow_zone_tl_y,
                        slow_zone_tr_x, slow_zone_tr_y, slow_zone_bl_x, slow_zone_bl_y,
                        slow_zone_br_x, slow_zone_br_y
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(insert_query, data)
                print("Record inserted successfully!")

            # Commit the transaction
            self.connection.commit()
            cursor.close()
        except Error as e:
            print(f"Error in insert_or_update_robot_zones: '{e}'")

    def get_zone_data(self):
        """
        Retrieve data from the RobotZones table based on a condition.
        """
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = f"SELECT * FROM RobotZones WHERE robot_id = 1"
            cursor.execute(query)
            results = cursor.fetchall()
            cursor.close()
            return results
        except Error as e:
            print(f"Error retrieving data: '{e}'")
            return []

    def get_log_data(self):
        """
        Retrieve data from the ZoneLogs table based on a condition.
        """
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = f"SELECT * FROM ZoneLogs robot_id = 1"
            cursor.execute(query)
            results = cursor.fetchall()
            cursor.close()
            return results
        except Error as e:
            print(f"Error retrieving log data: '{e}'")
            return []
        
    def get_log_data_today(self):
        """
        Retrieve data from the ZoneLogs table for logs created today.
        """
        try:
            # Get today's date in 'YYYY-MM-DD' format
            today_date = datetime.now().strftime('%Y-%m-%d')

            # Query to filter logs based on today's date
            cursor = self.connection.cursor(dictionary=True)
            query = f"SELECT * FROM ZoneLogs WHERE DATE(log_datetime) = '{today_date}' and robot_id = 1"
            cursor.execute(query)
            results = cursor.fetchall()
            cursor.close()
            return results
        except Error as e:
            print(f"Error retrieving today's log data: '{e}'")
            return []

    def close_connection(self):
        """
        Close the database connection.
        """
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("Connection closed successfully.")

if __name__ == '__main__':
    db = MySQLHandler()
    db.connect()

    # Insert data into RobotZones
    robot_data = (1, 10, 10, 20, 10, 10, 20, 20, 20, 30, 30, 40, 30, 30, 40, 40, 40)
    db.insert_zone(robot_data)

    # Retrieve data from RobotZones
    zones = db.get_zone_data()
    print("Robot Zones Data:", zones)

    logs = db.get_log_data_today()
    print("Zone Logs Data:", logs)
