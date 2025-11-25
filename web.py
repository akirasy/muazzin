from flask import Flask, render_template
import sqlite3
import pathlib

BASE_DIR = pathlib.Path(__file__).parent
app_db = BASE_DIR.joinpath('userspace', 'app.db')
log_file = BASE_DIR.joinpath('userspace', 'logfile.txt')

app = Flask(__name__)

@app.route('/')
def index():
    # Fetch prayer times from the database
    with sqlite3.connect(app_db) as db_connection:
        cursor = db_connection.cursor()
        cursor.execute('SELECT imsak, subuh, syuruk, dhuha, zohor, asar, maghrib, isyak FROM daily WHERE rowid=1;')
        prayer_times_result = cursor.fetchone()
        
        cursor.execute('SELECT date FROM daily_updated WHERE rowid=1;')
        last_updated_result = cursor.fetchone()

    prayer_times = {
        'Imsak': prayer_times_result[0],
        'Subuh': prayer_times_result[1],
        'Syuruk': prayer_times_result[2],
        'Dhuha': prayer_times_result[3],
        'Zohor': prayer_times_result[4],
        'Asar': prayer_times_result[5],
        'Maghrib': prayer_times_result[6],
        'Isyak': prayer_times_result[7]
    }
    
    last_updated = last_updated_result[0]

    # Read the last 20 lines of the log file
    try:
        with open(log_file, 'r') as f:
            log_lines = f.readlines()[-20:]
            log_content = "".join(log_lines)
    except FileNotFoundError:
        log_content = "Log file not found."

    return render_template('index.html', prayer_times=prayer_times, last_updated=last_updated, log_content=log_content)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
