#!/usr/bin/env python3

import urllib, pathlib, time, datetime
import os, csv
import feedparser, schedule
import mplayerSlave

# set vars and instances
ENV_KOD      = os.getenv('KOD')
BASE_DIR     = pathlib.Path(__file__).parent
azan_csv     = BASE_DIR.joinpath('azan.csv')
azan_music   = BASE_DIR.joinpath('azan.m4a')
log_file     = BASE_DIR.joinpath('logfile.txt')
feed_link    = 'https://www.e-solat.gov.my/index.php?r=esolatApi/xmlfeed&zon=' + ENV_KOD
mplayer      = mplayerSlave.MPlayer()

# Logging features
import logging
from logging.handlers import RotatingFileHandler

log_handler = RotatingFileHandler(log_file, mode='a', maxBytes=5*1024*1024, 
                                 backupCount=2, encoding=None, delay=0)
log_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
log_handler.setLevel(logging.INFO)
logger = logging.getLogger(__name__)
logger.addHandler(log_handler)
logger.setLevel(logging.INFO)

def update_csv():
    logger.info('Update time for azan in file.')
    while True:
        try:
            feed = feedparser.parse(feed_link)
        except urllib.error.URLError:
            logger.info('Update csv_file status: Success!')
            continue
        break
    last_update = datetime.datetime.strptime(feed.feed.updated, '%d-%m-%Y %H:%M:%S').strftime('%d-%m-%Y')
    with open(azan_csv, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(['Last update', last_update])
        for i in range(7):
            solat_name = feed.entries[i].title
            solat_time = datetime.datetime.strptime(feed.entries[i].summary, '%H:%M:%S').strftime('%H:%M')
            csvwriter.writerow([solat_name, solat_time])

def csv_iscurrent():
    with open(azan_csv, newline='') as csvfile:
        csvreader = csv.reader(csvfile)
        date_updated = csvreader.__next__()[1]
    date_today = datetime.datetime.now().date()
    date_csv = datetime.datetime.strptime(date_updated, '%d-%m-%Y').date()
    status = date_today == date_csv
    logger.info(f'Azan time csv_file is_current: {status}')
    return status

def create_azan_job():
    time_selection = ['Subuh', 'Zohor', 'Asar', 'Maghrib', 'Isyak']
    with open(azan_csv, newline='') as csvfile:
        reader = csv.reader(csvfile)
        for i in reader:
            if i[0] in time_selection:
                time_azan = datetime.datetime.strptime(i[1], '%H:%M').time()
                time_now = datetime.datetime.now().time()
                if time_now < time_azan:
                    schedule.every().day.at(i[1]).do(begin_azan)
                    logger.info(f'Azan job created for: {i[0]}')
                    break
                else:
                    logger.info(f'Azan for {i[0]} has passed')
    time.sleep(5)
    if schedule.idle_seconds() is None:
        schedule.every().day.at('01:00').do(wait_next_day)
        logger.info(f'Schedule job created for next day')
    else:
        pass

def wait_next_day():
    create_azan_job()
    return schedule.CancelJob

def wait_next_job():
    while True:
        n = schedule.idle_seconds()
        if n is None:
            time.sleep(5) 
        elif n > 0:
            logger.info(f'Next job in {round(n/60, 2)} minutes...')
            time.sleep(n)
            schedule.run_pending()
            break

def begin_azan():
    logger.info('Playing azan now.')
    mplayer.loadfile(azan_music.resolve())
    return schedule.CancelJob

def allow_no_certificate():
    import ssl 
    try: 
        _create_unverified_https_context = ssl._create_unverified_context 
    except AttributeError: 
        # Legacy Python that doesn't verify HTTPS certificates by default 
        pass 
    else: # Handle target environment that doesn't support HTTPS verification 
        ssl._create_default_https_context = _create_unverified_https_context

def main():
    allow_no_certificate()
    update_csv()
    while True:
        time.sleep(5)
        azan_time_is_updated = csv_iscurrent()
        if azan_time_is_updated:
            create_azan_job()
            wait_next_job()
        if not azan_time_is_updated:
            update_csv()
            create_azan_job()
            wait_next_job()

if __name__ == '__main__':
    try:
        main()
    except Exception:
        logger.exception('An error occured.')
