#!/usr/bin/env python3

import urllib, pathlib, time, datetime
import linecache, logging, subprocess, os
import feedparser
import schedule

# Logging features
logging.basicConfig(
        # for debugging, uncomment this line to write log in file
        #filename='logfile.txt',
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='(%d-%b-%y %H:%M:%S)',
        level=logging.INFO)
logger = logging.getLogger(__name__)

# set variables
BASE_DIR = pathlib.Path(__file__).parent
feed_link = 'https://www.e-solat.gov.my/index.php?r=esolatApi/xmlfeed&zon=' + os.getenv('KOD')

azan_time = BASE_DIR.joinpath('azan-time.txt')
azan_music = BASE_DIR.joinpath('azan.m4a')

def update_time():
    logger.info('Update time for azan in file.')
    while True:
        try: feed = feedparser.parse(feed_link)
        except urllib.error.URLError: continue
        break
    last_update = datetime.datetime.strptime(feed.feed.updated, '%d-%m-%Y %H:%M:%S').strftime('%d-%m-%Y')
    solat_data = [['Last update', last_update]]
    for i in range(7):
        solat_name = feed.entries[i].title
        solat_time = datetime.datetime.strptime(feed.entries[i].summary, '%H:%M:%S').strftime('%H:%M')
        solat_data.append([solat_name, solat_time])
    with open(azan_time, 'w') as opened_file:
        for i in solat_data:
            opened_file.write(f'{i[0]}\n')
            opened_file.write(f'{i[1]}\n')

def create_job():
    logger.info('Create job schedule for azan today.')
    data = azan_time.read_text().split('\n')
    schedule.every().day.at(data[5]).do(begin_azan)
    schedule.every().day.at(data[9]).do(begin_azan)
    schedule.every().day.at(data[11]).do(begin_azan)
    schedule.every().day.at(data[13]).do(begin_azan)
    schedule.every().day.at(data[15]).do(begin_azan)

def create_job_once():
    logger.info('Check azan time for today.')
    now = datetime.datetime.now()
    data = azan_time.read_text().split('\n')
    pending = [data[5], data[9], data[11], data[13], data[15]]
    for i in pending:
        hour_min = i.split(':')
        pending_item = now.replace(hour=int(hour_min[0]), minute=int(hour_min[1]))
        if pending_item > now:
            schedule.every().day.at(i).do(begin_azan)
            logger.info(f'Schedule azan at {i}.')
    return schedule.CancelJob

def begin_azan():
    logger.info('Playing azan now.')
    bash_command = f'mplayer -volume {os.getenv("VOL")} {azan_music.resolve()}'
    subprocess.run(bash_command.split())
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
    if not azan_time.exists():
        logger.info('File "azan-time.txt" not exists.')
        update_time()
    schedule.every(3).seconds.do(create_job_once)
    schedule.every().day.at('00:05').do(update_time)
    schedule.every().day.at('00:10').do(create_job)
    logger.info('Running service in background...')
    while True:
        n = schedule.idle_seconds()
        logger.info(f'Next job in {round(n/60, 2)} minutes...')
        if n is None: break
        elif n > 0: time.sleep(n)
        schedule.run_pending()

if __name__ == '__main__':
    try:
        main()
    except Exception:
        logger.exception('An error occured.')
