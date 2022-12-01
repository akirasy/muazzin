#!/usr/bin/env python3

import urllib, pathlib, time, datetime
import os, csv
import feedparser
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
    logger.info('Check for azan time in file.')
    if azan_csv.exists():
       azan_time_is_updated = csv_iscurrent()
    else:
       azan_time_is_updated = False

    if azan_time_is_updated:
        logger.info('-- Azan time in file is already updated.')
    else:
        logger.info('-- Azan time in file is not updated.')
        while True:
            try:
                feed = feedparser.parse(feed_link)
                logger.info('-- Update csv_file status: Success!')
                break
            except urllib.error.URLError:
                logger.exception('-- Update csv_file status: Failed! No internet connection.')
                logger.exception('-- Update csv_file status: Retrying in 6 minutes.')
                time.sleep(360)
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
    logger.info(f'-- Azan time csv_file is_current: {status}')
    return status

def create_job():
    logger.info('Create schedule job.')
    time_selection = ['Subuh', 'Zohor', 'Asar', 'Maghrib', 'Isyak']
    now = datetime.datetime.now()
    wait_time = None
    with open(azan_csv, newline='') as csvfile:
        reader = csv.reader(csvfile)
        for i in reader:
            if i[0] in time_selection:
                azan_time = datetime.datetime.strptime(i[1], '%H:%M')
                azan_dt = datetime.datetime(year=now.year, month=now.month, day=now.day, hour=azan_time.hour, minute=azan_time.minute)
                if now < azan_dt:
                    wait_time = (azan_dt - now).total_seconds()
                    logger.info(f'-- Schedule azan for: {i[0]}')
                    logger.info(f'-- Wait time till next job: {round(wait_time/(60*60), 2)} hours')
                    time.sleep(wait_time)
                    begin_azan()
                    return
                else:
                    logger.info(f'-- Azan for {i[0]} has passed')
    if wait_time is None:
        logger.info(f'-- Schedule job for next day')
        next_day_dt = datetime.datetime(year=now.year, month=now.month, day=now.day, hour=1) + datetime.timedelta(days=1)
        wait_time = (next_day_dt - now).total_seconds()
        logger.info(f'-- Wait time till next job: {round(wait_time/(60*60), 2)} hours')
        time.sleep(wait_time)
        update_csv()
        return

def begin_azan():
    logger.info('Playing azan now.')
    mplayer.loadfile(azan_music.resolve())

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
    while True:
        update_csv()
        create_job()

if __name__ == '__main__':
    try:
        main()
    except Exception:
        logger.exception('An error occured.')
