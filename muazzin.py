#!/usr/bin/env python3

import csv, logging, pathlib, shutil, sqlite3, time, tomllib
from datetime import datetime, timedelta
from logging.handlers import RotatingFileHandler

import feedparser
import requests
from playsound3 import playsound
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

def load_config():
    config_file = BASE_DIR.joinpath('userspace', 'config.toml')
    if not config_file.exists():
        logger.info('Setting app for first use.')
        shutil.copy(
            BASE_DIR.joinpath('defaults', 'config.toml'),
            config_file)
        shutil.copy(
            BASE_DIR.joinpath('defaults', 'azan.m4a'),
            BASE_DIR.joinpath('userspace', 'azan.m4a'))
    logger.info('Reloading app config.')
    with open(config_file, 'rb') as opened_file:
        app_config = tomllib.load(opened_file)
    return app_config

def setup_sqlite_db():
    if app_db.exists():
        logger.info('App database already exist.')
    else:
        logger.info('Setting up new app database.')
        with sqlite3.connect(app_db) as db_connection:
            cursor = db_connection.cursor()
            cursor.execute('''CREATE TABLE daily_updated (
                date TEXT);''')
            cursor.execute('''CREATE TABLE daily (
                imsak TEXT, subuh TEXT, syuruk TEXT, dhuha TEXT, 
                zohor TEXT, asar TEXT, maghrib TEXT, isyak TEXT);''')
            cursor.execute('''CREATE TABLE yearly (
                Tarikh TEXT, Hijri TEXT, Hari TEXT, Imsak TEXT, 
                Subuh TEXT, Syuruk TEXT, Zohor TEXT, Asar TEXT, 
                Maghrib TEXT, Isyak TEXT);''')
            cursor.execute('''INSERT INTO daily_updated(rowid, date)
                VALUES(1, '01-01-2001 01:00:00');''')
            cursor.execute('''INSERT INTO daily(rowid, imsak, subuh, syuruk, dhuha, zohor, asar, maghrib, isyak)
                VALUES(1, '05:50:00', '06:00:00', '07:10:00', '07:30:00', '13:00:00', '16:30:00', '19:30:00', '20:30:00');''')
            db_connection.commit()

def fetch_azan_times(feed_link):
    '''Get azan time from API server. Return value should be in this structure as string:
    { 'last_update': '%d-%m-%Y %H:%M:%S',
      'azan_times': { 'imsak'  : '%H:%M:%S',
                      'subuh'  : '%H:%M:%S',
                      'syuruk' : '%H:%M:%S',
                      'dhuha'  : '%H:%M:%S',
                      'zohor'  : '%H:%M:%S',
                      'asar'   : '%H:%M:%S',
                      'maghrib': '%H:%M:%S',
                      'isyak'  : '%H:%M:%S'
                    }
    }
    '''
    logger.info('Fetching data from API server.')
    last_update = None
    azan_times = None
    try:
        rss_request = requests.get(feed_link)
        parsed_feed = feedparser.parse(rss_request.content)
        last_update = parsed_feed.feed.updated
        azan_times = dict()
        for i in parsed_feed.entries:
            azan_times[i['title'].lower()] = i['summary']
        logger.info('-- Data received successfully.')
        return {'last_update':last_update, 'azan_times': azan_times}
    except requests.exceptions.ConnectionError:
        logger.error('-- Warning. No connection to the API server.')
        app_config = load_config()
        bot_token = app_config['Telegram']['BotToken']
        chat_id = app_config['Telegram']['ChatId']
        if bot_token != '':
            telegram_bot = telegram.TelegramBot(bot_token)
            telegram_bot.send_message(chat_id, 'Warning. No connection to the API server. Azan time will update using yearly database.')
        today = datetime.now()
        return fetch_azan_times_from_yearly(today)

def load_azan_csv():
    app_config = load_config()
    csv_file = BASE_DIR.joinpath('userspace', app_config['Settings']['YearlyAzanCsvFile'])
    if csv_file.exists():
        with open(csv_file, newline='') as csvfile:
            reader = csv.reader(csvfile)
            next(reader) # Skips header
            data_array = [row for row in reader]
        with sqlite3.connect(app_db) as db_connection:
            cursor = db_connection.cursor()
            cursor.executemany('INSERT INTO yearly VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', data_array)
            db_connection.commit()

def fetch_azan_times_from_yearly(date):
    with sqlite3.connect(app_db) as db_connection:
        cursor = db_connection.cursor()
        cursor.execute('''SELECT * FROM yearly WHERE Tarikh=?''', (date.strftime('%d-%b-%Y'),))
        query_result = cursor.fetchone()
        db_connection.commit()
    return { 
        'last_update': date.strftime('%d-%m-%Y %H:%M:%S'),
        'azan_times': { 
            'imsak'  : datetime.strptime(query_result[3], '%I:%M %p').strftime('%H:%M:%S'),
            'subuh'  : datetime.strptime(query_result[4], '%I:%M %p').strftime('%H:%M:%S'),
            'syuruk' : datetime.strptime(query_result[5], '%I:%M %p').strftime('%H:%M:%S'),
            'dhuha'  : '00:00:00',
            'zohor'  : datetime.strptime(query_result[6], '%I:%M %p').strftime('%H:%M:%S'),
            'asar'   : datetime.strptime(query_result[7], '%I:%M %p').strftime('%H:%M:%S'),
            'maghrib': datetime.strptime(query_result[8], '%I:%M %p').strftime('%H:%M:%S'),
            'isyak'  : datetime.strptime(query_result[9], '%I:%M %p').strftime('%H:%M:%S') 
            }
        }

def save_azan_times(azan_times):
    logger.info('Save data to app database.')
    date_updated = azan_times['last_update']
    times = azan_times['azan_times']
    with sqlite3.connect(app_db) as db_connection:
        cursor = db_connection.cursor()
        cursor.execute('''UPDATE daily_updated SET 
            date = ? WHERE rowid=1;''',
            (date_updated,))
        cursor.execute('''UPDATE daily SET 
            imsak   = ?, subuh   = ?, syuruk  = ?, dhuha = ?,
            zohor   = ?, asar    = ?, maghrib = ?, isyak   = ?
            WHERE rowid=1;''',
            (times['imsak'], times['subuh'], times['syuruk'], times['dhuha'],
             times['zohor'], times['asar'], times['maghrib'], times['isyak']))
        db_connection.commit()

def check_azan_time_is_current():
    logger.info('Check if database is recent.')
    with sqlite3.connect(app_db) as db_connection:
        cursor = db_connection.cursor()
        cursor.execute('SELECT date FROM daily_updated WHERE rowid=1;')
        query_result = cursor.fetchone()[0]
        date_updated = datetime.strptime(query_result , '%d-%m-%Y %H:%M:%S').date()
    
    date_today = datetime.now().date()
    status = date_today == date_updated
    logger.info(f'-- Database last updated on: {date_updated}')
    logger.info(f'-- Azan time is current: {status}')
    return status

def schedule_for_next_azan():
    logger.info('Create schedule for next azan.')
    with sqlite3.connect(app_db) as db_connection:
        cursor = db_connection.cursor()
        cursor.execute('SELECT subuh, zohor, asar, maghrib, isyak FROM daily WHERE rowid=1;')
        query_result = cursor.fetchone()

    wait_time = None
    for i in query_result:
        now = datetime.now()
        logger.info(f'-- Checking azan at {i}')
        azan_dt = datetime(
            year=now.year, 
            month=now.month, 
            day=now.day, 
            hour=datetime.strptime(i, '%H:%M:%S').hour,
            minute=datetime.strptime(i, '%H:%M:%S').minute)
        if now < azan_dt:
            wait_time = (azan_dt - now).total_seconds()
            logger.info(f'-- Next azan is in {round(wait_time/60, 2)} minutes ({round(wait_time/(60*60), 2)} hours).')
            if wait_time > 60:
                wake_up_dt = now + timedelta(seconds=(wait_time-60))
                logger.info(f'-- Sleeping now. Will resume at: {wake_up_dt}.')
                if wake_up_dt > azan_dt:
                    time.sleep(wait_time-120)
                else:
                    time.sleep(wait_time-60)
            standby_azan(azan_dt)
        else:
            logger.info(f'-- It has already passed.')
    logger.info('-- Schedule check is done for today.')
    if wait_time is None:
        logger.info(f'-- Last azan for the day has passed. Prepare schedule for next day.')
        now = datetime.now()
        next_day_dt = datetime(
            year=now.year, 
            month=now.month, 
            day=now.day, 
            hour=1) + timedelta(days=1)
        wait_time = (next_day_dt - now).total_seconds()
        logger.info(f'-- Will check again at 1 am tomorrow ({round(wait_time/(60*60), 2)} hours)')
        time.sleep(wait_time)
    
def standby_azan(azan_dt):
    logger.info('Standby each seconds until next azan.')
    while True:
        if datetime.now().minute == azan_dt.minute:
            logger.info('-- Azan time is now.')
            app_config = load_config()
            playsound(BASE_DIR.joinpath('userspace', app_config['Settings']['AzanFile']).resolve())
            break
        time.sleep(1)

def main():
    logger.info('===== START MUAZZIN =====')
    setup_sqlite_db()
    load_azan_csv()
    while True:
        azan_time_is_current = check_azan_time_is_current()
        if azan_time_is_current:
            # Start polling for azan
            schedule_for_next_azan()
        else:
            # Update azan times
            app_config = load_config()
            kod_kawasan = app_config['Settings']['KodKawasan']
            feed_link = 'https://www.e-solat.gov.my/index.php?r=esolatApi/xmlfeed&zon=' + kod_kawasan
            azan_times = fetch_azan_times(feed_link)
            save_azan_times(azan_times)
            
            # Craft telegram message about azan times
            bot_token = app_config['Telegram']['BotToken']
            chat_id = app_config['Telegram']['ChatId']
            if bot_token != '':
                message = '' + \
                    f'*Waktu Azan {azan_times["last_update"]}*\n' + \
                    f'Imsak : {azan_times["azan_times"]["imsak"]}\n' + \
                    f'Subuh : {azan_times["azan_times"]["subuh"]}\n' + \
                    f'Syuruk : {azan_times["azan_times"]["syuruk"]}\n' + \
                    f'Dhuha : {azan_times["azan_times"]["dhuha"]}\n' + \
                    f'Zohor : {azan_times["azan_times"]["zohor"]}\n' + \
                    f'Asar : {azan_times["azan_times"]["asar"]}\n' + \
                    f'Maghrib : {azan_times["azan_times"]["maghrib"]}\n' + \
                    f'Isyak : {azan_times["azan_times"]["isyak"]}'
                telegram_bot = telegram.TelegramBot(bot_token)
                telegram_bot.send_message(chat_id=chat_id, text=message, parse_mode='Markdown')

if __name__ == '__main__':
    main()

