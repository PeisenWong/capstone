from flask import Flask, render_template
import mysql.connector

app = Flask(__name__)

@app.route('/')
def index():
    # Connect to MySQL
    cnx = mysql.connector.connect(
        host='192.168.x.x',
        user='your_user',
        password='your_password',
        database='your_db'
    )
    cursor = cnx.cursor()
    cursor.execute("SELECT * FROM your_table;")
    rows = cursor.fetchall()
    # ... prepare data for visualization ...
    cursor.close()
    cnx.close()

    return render_template('index.html', data=rows)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)  # 0.0.0.0 to allow external access
