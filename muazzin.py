#!/usr/bin/env python3

import csv, logging, pathlib, shutil, sqlite3, subprocess, time, tomllib
from datetime import datetime, timedelta
from logging.handlers import RotatingFileHandler

import feedparser
import requests
import telegram

# Set variables and instances
BASE_DIR     = pathlib.Path(__file__).parent
log_file     = BASE_DIR.joinpath('userspace', 'logfile.txt')
app_db       = BASE_DIR.joinpath('userspace', 'app.db')

# Logging features
logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[RotatingFileHandler(
            log_file, mode='a', maxBytes=5*1024*1024,
            backupCount=2, encoding=None, delay=0)])
logger = logging.getLogger(__name__)

def copy_default_file(filename, overwrite=False):
    file = BASE_DIR.joinpath('userspace', filename)
    if file.exists() and not overwrite:
        logger.info(f'-- Notice: {filename} already exists.')
    else:
        shutil.copy(BASE_DIR.joinpath('defaults', filename), file)
        logger.info(f'-- Copied file: {filename}')

def create_app_db():
    if app_db.exists():
        logger.info('-- App database already exist.')
    else:
        logger.info('-- Setting up new app database.')
        with sqlite3.connect(app_db) as db_connection:
            cursor = db_connection.cursor()
            cursor.execute('''CREATE TABLE daily (
                subuh TEXT, zohor TEXT, asar TEXT, 
                maghrib TEXT, isyak TEXT);''')
            cursor.execute('''CREATE TABLE yearly (
                Tarikh TEXT, Hijri TEXT, Hari TEXT, Imsak TEXT, 
                Subuh TEXT, Syuruk TEXT, Zohor TEXT, Asar TEXT, 
                Maghrib TEXT, Isyak TEXT);''')
            db_connection.commit()

def populate_app_db():
    logger.info('-- Insert default values to app database.')
    yearly_azan_file = BASE_DIR.joinpath('userspace', 'jadual_waktu_solat_JAKIM_2025.csv')
    with open(yearly_azan_file , newline='') as opened_file:
        reader = csv.reader(opened_file)
        next(reader) # Skips header
        data_array = [row for row in reader]

    with sqlite3.connect(app_db) as db_connection:
        cursor = db_connection.cursor()
        cursor.execute('DELETE FROM yearly;')
        cursor.executemany('''INSERT INTO yearly 
            VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?);''', data_array)
        cursor.execute('''INSERT OR IGNORE INTO daily(rowid, subuh, zohor, asar, maghrib, isyak)
            VALUES(1, '06:00:00', '13:00:00', '16:30:00', '19:30:00', '20:30:00');''')
        db_connection.commit()

def load_app_config():
    config_file = BASE_DIR.joinpath('userspace', 'config.toml')
    with open(config_file, 'rb') as opened_file:
        app_config = tomllib.load(opened_file)
    return app_config

def fetch_azan_time_internal(date):
    logger.info('-- Loading azan time from database.')
    with sqlite3.connect(app_db) as db_connection:
        cursor = db_connection.cursor()
        cursor.execute('''SELECT * FROM yearly WHERE Tarikh=?''', (date.strftime('%d-%b-%Y'),))
        query_result = cursor.fetchone()
    return { 
            'subuh'  : datetime.strptime(query_result[4], '%I:%M %p').strftime('%H:%M:%S'),
            'zohor'  : datetime.strptime(query_result[6], '%I:%M %p').strftime('%H:%M:%S'),
            'asar'   : datetime.strptime(query_result[7], '%I:%M %p').strftime('%H:%M:%S'),
            'maghrib': datetime.strptime(query_result[8], '%I:%M %p').strftime('%H:%M:%S'),
            'isyak'  : datetime.strptime(query_result[9], '%I:%M %p').strftime('%H:%M:%S')
            }

def fetch_azan_time_feed(date, feed_link):
    logger.info('-- Fetching azan time from API server.')
    try:
        rss_request = requests.get(feed_link)
        parsed_feed = feedparser.parse(rss_request.content)
        azan_times = dict()
        for i in parsed_feed.entries:
            azan_times[i['title'].lower()] = i['summary']
        logger.info('-- Data received successfully.')
        return {
                'subuh'  : azan_times['subuh'],
                'zohor'  : azan_times['zohor'],
                'asar'   : azan_times['asar'],
                'maghrib': azan_times['maghrib'],
                'isyak'  : azan_times['isyak']
                }

    except Exception as error:
        logger.error(f'-- {error}')
        return { 
                'subuh'  :'00:00:00',
                'zohor'  :'00:00:00',
                'asar'   :'00:00:00',
                'maghrib':'00:00:00',
                'isyak'  :'00:00:00'
                }

def update_db_daily(azan_time):
    logger.info('Save data to app database.')
    with sqlite3.connect(app_db) as db_connection:
        cursor = db_connection.cursor()
        cursor.execute('''UPDATE daily SET 
            subuh = ?, zohor = ?, asar = ?, maghrib = ?, isyak = ?
            WHERE rowid=1;''',
            (azan_time['subuh'], azan_time['zohor'], azan_time['asar'], azan_time['maghrib'], azan_time['isyak'])
        )
        db_connection.commit()

def query_azan_time():
    with sqlite3.connect(app_db) as db_connection:
        cursor = db_connection.cursor()
        cursor.execute('SELECT subuh, zohor, asar, maghrib, isyak FROM daily WHERE rowid=1;')
        query_result = cursor.fetchone()
    return query_result

def schedule_for_next_azan(app_config, telegram_bot):
    logger.info('Create schedule for next azan.')
    waktu = ['Subuh', 'Zohor', 'Asar', 'Maghrib', 'Isyak']
    query_result = query_azan_time()
    wait_time = None

    for waktu_name, azan_time in zip(waktu, query_result):
        logger.info(f'-- Checking azan {waktu_name} at {azan_time}')
        now = datetime.now()
        azan_dt = datetime(
                year=now.year,
                month=now.month,
                day=now.day,
                hour=datetime.strptime(azan_time, '%H:%M:%S').hour,
                minute=datetime.strptime(azan_time, '%H:%M:%S').minute)

        if now < azan_dt:
            wait_time = (azan_dt - now).total_seconds()
            logger.info(f'-- Next azan is in {round(wait_time/60, 2)} minutes ({round(wait_time/(60*60), 2)} hours).')
            if wait_time > 60:
                time.sleep(wait_time-60)
            standby_azan(azan_dt, app_config, telegram_bot, waktu_name)
        else:
            logger.info(f'-- It has already passed.')

    logger.info('-- Schedule check is done for today.')

    if wait_time is None:
        logger.info(f'-- Last azan for the day has passed. Prepare schedule for next day.')
        next_day_dt = datetime(
                year=now.year,
                month=now.month,
                day=now.day,
                hour=1) + timedelta(days=1)
        wait_time = (next_day_dt - now).total_seconds()
        logger.info(f'-- Will check again at 1 am tomorrow ({round(wait_time/(60*60), 2)} hours)')
        time.sleep(wait_time)

def standby_azan(azan_dt, app_config, telegram_bot, waktu_name):
    logger.info('Standby each seconds until next azan.')
    send_telegram_message(telegram_bot, f'Azan {waktu_name} will commence within 1 minutes.')
    while True:
        if datetime.now().minute == azan_dt.minute:
            logger.info(f'-- Azan {waktu_name} is now.')
            send_telegram_message(telegram_bot, 'It is now time for {waktu_name} prayer.')
            soundfile = BASE_DIR.joinpath('userspace', app_config['Settings']['AzanFile']).resolve()
            subprocess.run(['gst-play-1.0', '--no-interactive', '--quiet', soundfile])
            break
        time.sleep(1)

def get_telegram_creds(app_config):
    bot_token = app_config['Telegram']['BotToken']
    chat_id = app_config['Telegram']['ChatId']
    if bot_token != '':
        return {
                'telegram_bot': telegram.TelegramBot(bot_token),
                'chat_id': chat_id
                }
    else:
        logger.info('TelegramBot service not set.')
        return None

def send_telegram_message(telegram_creds, message, parse_mode='Markdown'):
    if telegram_creds:
        telegram_bot = telegram_creds['telegram_bot']
        chat_id = telegram_creds['chat_id']
        telegram_bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode=parse_mode
                )
    else:
        logger.info('TelegramBot service not set. No message sent.')


def create_message_azan_daily(azan_times):
    message = '' + \
            f'*Waktu Azan*\n' + \
            f'Subuh : {azan_times["subuh"]}\n' + \
            f'Zohor : {azan_times["zohor"]}\n' + \
            f'Asar : {azan_times["asar"]}\n' + \
            f'Maghrib : {azan_times["maghrib"]}\n' + \
            f'Isyak : {azan_times["isyak"]}'
    return message

def main():
    logger.info('===== START MUAZZIN =====')

    logger.info('Preparing muazzin setup.')

    existing_config_file = BASE_DIR.joinpath('userspace', 'config.toml')
    copy_default_file('config.toml')
    copy_default_file('azan.m4a')
    copy_default_file('jadual_waktu_solat_JAKIM_2025.csv')

    create_app_db()
    populate_app_db()

    app_config = load_app_config()
    kod_kawasan = app_config['Settings']['KodKawasan']
    feed_link = 'https://www.e-solat.gov.my/index.php?r=esolatApi/xmlfeed&zon=' + kod_kawasan
    telegram_bot = get_telegram_creds(app_config)

    while True:
        logger.info('Muazzin is working.')
        today = datetime.now()
        azan_time_internal = fetch_azan_time_internal(today)
        azan_time_feed = fetch_azan_time_feed(today, feed_link)

        if azan_time_internal == azan_time_feed:
            azan_data = azan_time_feed
        else:
            azan_data = azan_time_internal
            logger.info('Warning! There is difference in local azan time and web azan time.')
            send_telegram_message(telegram_bot, 'There is difference in local azan time and web azan time.')
        update_db_daily(azan_data)
        message = create_message_azan_daily(azan_data)
        send_telegram_message(telegram_bot, message)

        schedule_for_next_azan(app_config, telegram_bot)

if __name__ == '__main__':
    main()

