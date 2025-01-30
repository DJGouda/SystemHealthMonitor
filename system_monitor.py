import mysql.connector 
import psutil 
import smtplib
import matplotlib.pyplot as plt
import pandas as pd
import time
from datetime import datetime
from email.mime.text import MIMEText

# ++++++++++++++++++++++++++++++++++ CONFIGURATION +++++++++++++++++++++++++++++++++
MYSQL_HOST = "localhost"
MYSQL_USER = "root"
MYSQL_PASSWORD = "Dj@7489273401"
MYSQL_DB = "system_monitor"

ALERT_THRESHOLD_CPU = 0  #  trigger an alert
ALERT_THRESHOLD_MEMORY = 80  #  trigger an alert

EMAIL_SENDER = "djgouda26@gmail.com"
EMAIL_RECEIVER = "djgouda26@gmail.com"
EMAIL_PASSWORD = "ymiz ammy vlqg tftm" 


# ++++++++++++++++++++++++++++++++ DATABASE CONNECTION +++++++++++++++++++++++++++++++++++
def connect_db():
    try:
        conn = mysql.connector.connect(
            host=MYSQL_HOST, user=MYSQL_USER, password=MYSQL_PASSWORD, database=MYSQL_DB
        )
        return conn
    except mysql.connector.Error as err:
        print(f"Database Error: {err}")
        return None


# +++++++++++++++++++++++++++ CREATE TABLE IF NOT EXISTS ++++++++++++++++++++++++++++++++++++++++++++++
def setup_database():
    conn = connect_db()
    if conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS system_metrics (
                id INT AUTO_INCREMENT PRIMARY KEY,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                cpu_usage FLOAT,
                memory_usage FLOAT,
                disk_usage FLOAT,
                network_sent FLOAT,
                network_received FLOAT
            )
            """
        )
        conn.commit()
        conn.close()


# ++++++++++++++++++++++++++++++++ COLLECT SYSTEM METRICS +++++++++++++++++++++++++++++++++++
def collect_metrics():
    cpu_usage = psutil.cpu_percent(interval=1)
    memory_usage = psutil.virtual_memory().percent
    disk_usage = psutil.disk_usage('/').percent
    net_io = psutil.net_io_counters()

    network_sent = net_io.bytes_sent / (1024 * 1024)  #  bytes to MB
    network_received = net_io.bytes_recv / (1024 * 1024)  #  bytes to MB

    return datetime.now(), cpu_usage, memory_usage, disk_usage, network_sent, network_received


# +++++++++++++++++++++++++++++++ LOG DATA TO DATABASE +++++++++++++++++++++++++++
def log_system_metrics():
    conn = connect_db()
    if conn:
        cursor = conn.cursor()
        timestamp, cpu, memory, disk, net_sent, net_received = collect_metrics()
        cursor.execute(
            """
            INSERT INTO system_metrics (timestamp, cpu_usage, memory_usage, disk_usage, network_sent, network_received)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (timestamp, cpu, memory, disk, net_sent, net_received),
        )
        conn.commit()
        conn.close()
        print(f"Logged data at {timestamp}")

        # Check if an alert should be sent
        if cpu > ALERT_THRESHOLD_CPU:
            send_alert("CPU", cpu)
        if memory > ALERT_THRESHOLD_MEMORY:
            send_alert("Memory", memory)


# +++++++++++++++++++++++++++++++++ SEND EMAIL ALERT +++++++++++++++++++++++++++
def send_alert(metric, value):
    subject = f"System Alert: High {metric} Usage"
    message = f"Warning! {metric} usage is at {value}%."
    
    msg = MIMEText(message)
    msg['Subject'] = subject
    msg['From'] = EMAIL_SENDER
    msg['To'] = EMAIL_RECEIVER

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())
        print(f"Alert Sent: {subject}")
    except Exception as e:
        print(f"Email Error: {e}")


# +++++++++++++++++++++++++++++++ FETCH & DISPLAY DATA +++++++++++++++++++++
def fetch_data():
    conn = connect_db()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT timestamp, cpu_usage, memory_usage FROM system_metrics ORDER BY timestamp DESC LIMIT 50")
        data = cursor.fetchall()
        conn.close()
        return data
    return []


#  ++++++++++++++++++++++++++++ PLOT SYSTEM USAGE+++++++++++++++++++++++
def plot_data():
    data = fetch_data()
    if not data:
        print("No data available for plotting.")
        return

    df = pd.DataFrame(data, columns=['Timestamp', 'CPU Usage', 'Memory Usage'])

    plt.figure(figsize=(10, 5))
    plt.plot(df['Timestamp'], df['CPU Usage'], label="CPU Usage (%)", color='red')
    plt.plot(df['Timestamp'], df['Memory Usage'], label="Memory Usage (%)", color='blue')
    plt.xlabel("Time")
    plt.ylabel("Usage (%)")
    plt.legend()
    plt.xticks(rotation=45)
    plt.title("CPU & Memory Usage Over Time")
    plt.tight_layout()
    plt.show()


# main
if __name__ == "__main__":
    setup_database()
    log_system_metrics()
    plot_data()   
        