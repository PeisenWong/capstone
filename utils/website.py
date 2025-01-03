from flask import Flask, render_template, request
from database import MySQLHandler
from collections import defaultdict
from datetime import datetime

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    db = MySQLHandler(user="peisen", password="password")
    db.connect()

    # -------------------------------
    # 1) Retrieve form inputs
    # -------------------------------
    start_date = request.form.get('start_date', '')
    end_date   = request.form.get('end_date', '')
    robot_id   = request.form.get('robot_id', '')

    # =========================================================
    # PART A: Query for the LINE CHART (respects Robot ID)
    # =========================================================
    line_query = "SELECT * FROM ZoneLogs WHERE 1=1"
    line_params = []

    if start_date:
        line_query += " AND log_datetime >= %s"
        line_params.append(start_date)
    if end_date:
        line_query += " AND log_datetime <= %s"
        line_params.append(end_date)
    # Robot ID is considered here
    if robot_id:
        line_query += " AND robot_id = %s"
        line_params.append(robot_id)

    line_query += " ORDER BY log_datetime ASC"

    # Execute line chart query
    cursor = db.connection.cursor(dictionary=True)
    cursor.execute(line_query, tuple(line_params))
    line_logs = cursor.fetchall()

    # Prepare data for line chart
    daily_data = defaultdict(lambda: {'stop_zone': 0, 'slow_zone': 0})
    for log in line_logs:
        date_str = log['log_datetime'].strftime('%Y-%m-%d')
        zone_type = log['zone_type']  # 'stop_zone' or 'slow_zone'
        daily_data[date_str][zone_type] += 1

    # Sort the date keys
    line_categories = sorted(daily_data.keys())
    stop_zone_data = [daily_data[d]['stop_zone'] for d in line_categories]
    slow_zone_data = [daily_data[d]['slow_zone'] for d in line_categories]

    # =========================================================
    # PART B: Query for the BAR CHART (IGNORES Robot ID)
    # =========================================================
    bar_query = "SELECT robot_id, zone_type, COUNT(*) as cnt FROM ZoneLogs WHERE 1=1"
    bar_params = []

    # For the bar chart, ONLY consider date filters, ignore `robot_id`
    if start_date:
        bar_query += " AND log_datetime >= %s"
        bar_params.append(start_date)
    if end_date:
        bar_query += " AND log_datetime <= %s"
        bar_params.append(end_date)

    bar_query += " GROUP BY robot_id, zone_type ORDER BY robot_id ASC"

    cursor.execute(bar_query, tuple(bar_params))
    bar_results = cursor.fetchall()

    # Build data structure: bar_data[robot_id] = {'stop_zone': int, 'slow_zone': int}
    bar_data = {
        1: {'stop_zone': 0, 'slow_zone': 0},
        2: {'stop_zone': 0, 'slow_zone': 0},
        3: {'stop_zone': 0, 'slow_zone': 0},
        4: {'stop_zone': 0, 'slow_zone': 0},
        5: {'stop_zone': 0, 'slow_zone': 0},
    }

    for row in bar_results:
        rid = row['robot_id']
        ztype = row['zone_type']
        bar_data[rid][ztype] = row['cnt']

    # Robot IDs for the x-axis
    bar_categories = [str(rid) for rid in range(1, 6)]
    # We'll create two series: Stop zone and Slow zone
    bar_stop_data = [bar_data[rid]['stop_zone'] for rid in range(1,6)]
    bar_slow_data = [bar_data[rid]['slow_zone'] for rid in range(1,6)]

    # Close DB
    cursor.close()
    db.close_connection()

    # Render template, passing both line chart and bar chart data
    return render_template(
        'index.html',
        # Existing line chart data
        categories=line_categories,
        stop_zone_data=stop_zone_data,
        slow_zone_data=slow_zone_data,
        # Bar chart data
        bar_categories=bar_categories,
        bar_stop_data=bar_stop_data,
        bar_slow_data=bar_slow_data,
        # Filters
        start_date=start_date,
        end_date=end_date,
        robot_id=robot_id
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
