#!/usr/bin/env python

import logging
import jsonrpclib
import requests
import json
import sys
import os
import shutil

################################
# Config
################################

# Set any feature to False that you do not want
pause_checker = True
app_cleaner = True
nzbget_cleaner = True
folder_cleaner = True

log_level = 'INFO'

# Add any and all paths that you want orphaned downloads to be deleted from
download_paths = {'/mnt/unionfs/downloads/nzbget/completed/radarr4k/',
                  '/mnt/unionfs/downloads/nzbget/completed/sonarr4k/',
                  '/mnt/unionfs/downloads/nzbget/completed/radarr/',
                  '/mnt/unionfs/downloads/nzbget/completed/sonarr/'}

# Add root path outside of docker for downloads
path_swap = '/mnt/unionfs/downloads/nzbget/completed/'

# Nzbget
ssl = True
server_url = 'nzbget.domain.com'
server_port = '443'
username = 'password'
password = 'username'

# Sonarr/Radarr instances you wish to monitor
apps = {'sonarr':
            {'url': 'https://sonarr.domain.com:443',
             'api': 'xxxxxxxxxxxxxxxxxxxxxx'},
        'radarr':
            {'url': 'https://radarr.domain.com:443',
             'api': 'xxxxxxxxxxxxxxxxxxxxxx'},
        'sonarr4k':
            {'url': 'https://sonarr4k.domain.com:443',
             'api': 'xxxxxxxxxxxxxxxxxxxxxx'},
        'radarr4k':
            {'url': 'https://radarr4k.domain.com:443',
             'api': 'xxxxxxxxxxxxxxxxxxxxxx'}

        }

# Add text string for any message you see in radarr/sonarr that you want removing from downloads and blacklisting release. 
blacklist_messages = {'File quality does not match quality of the grabbed release', 'sample'}
# remove_messages = {}

################################
# Logging
################################

# Logging format
formatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s')

# root logger
logger = logging.getLogger()

# Set initial level
if log_level.upper() == 'DEBUG':
    logger.setLevel(logging.DEBUG)
if log_level.upper() == 'INFO':
    logger.setLevel(logging.INFO)
if log_level.upper() == 'WARNING':
    logger.setLevel(logging.WARNING)

# Console handler, log to stdout
consoleHandler = logging.StreamHandler(sys.stdout)
consoleHandler.setFormatter(formatter)
logger.addHandler(consoleHandler)

# Other modules logging levels
logging.getLogger("requests").setLevel(logging.WARNING)


################################
# Init
################################

if ssl:
    protocol = 'https://'
else:
    protocol = 'http://'

url = '{}{}:{}@{}:{}/jsonrpc'.format(protocol, username, password, server_url, server_port)

logger.debug('Connecting to nzbget with url: {}'.format(url))
server = jsonrpclib.Server(url)

logger.debug('Server version: {}'.format(server.version()))
serverstatus = server.status()

################################
# Main
################################


def megabyte_gigabyte(input_megabyte):
    gigabyte = 1.0 / 1024
    convert_gb = gigabyte * input_megabyte
    return convert_gb


def bytes_2_human_readable(number_of_bytes):
    if number_of_bytes < 0:
        raise ValueError("!!! number_of_bytes can't be smaller than 0 !!!")

    step_to_greater_unit = 1024.

    number_of_bytes = float(number_of_bytes)
    unit = 'bytes'

    if (number_of_bytes / step_to_greater_unit) >= 1:
        number_of_bytes /= step_to_greater_unit
        unit = 'KB'

    if (number_of_bytes / step_to_greater_unit) >= 1:
        number_of_bytes /= step_to_greater_unit
        unit = 'MB'

    if (number_of_bytes / step_to_greater_unit) >= 1:
        number_of_bytes /= step_to_greater_unit
        unit = 'GB'

    if (number_of_bytes / step_to_greater_unit) >= 1:
        number_of_bytes /= step_to_greater_unit
        unit = 'TB'

    precision = 1
    number_of_bytes = round(number_of_bytes, precision)

    return str(number_of_bytes) + ' ' + unit


def unpause():
    server.resumedownload()
    server.resumepost()
    server.resumescan()


def pause_check():
    down_speed = bytes_2_human_readable(serverstatus['DownloadRate'])
    freespace = int(megabyte_gigabyte(serverstatus['FreeDiskSpaceMB']))

    if serverstatus['ServerStandBy'] and serverstatus['DownloadPaused']:
        if freespace > 0:
            logger.debug('Un-pausing as free space is now: {}GB'.format(freespace))
            unpause()
        if freespace < 0:
            logger.debug('Skipping un-pause, free space is still under 100GB ({}GB)'.format(freespace))

    if serverstatus['ServerStandBy']:
        logger.debug('Nothing to do, nzbget is not paused and que is empty')
    else:
        logger.debug('Nothing to do, downloads are running with {}GB of free space, at {}/s'.format(freespace,
                                                                                                    down_speed))


def app_get_queue(app):
    app_name = app
    app_url = apps[app]['url']
    app_api = apps[app]['api']

    headers = {'X-Api-Key': app_api}
    r = requests.get(app_url + '/api/queue', headers=headers, timeout=60)

    try:
        if r.status_code == 401:
            logger.warning("Error when connecting to {}, unauthorised. check api/url".format(app_name))
        try:
            return r.json()
        except json.decoder.JSONDecodeError:
            logger.warning('{} did not return valid json'.format(app_name))
            logger.debug(r.content)
    except requests.ConnectionError:
        logger.warning('Can not connect to {0} check if {0} is up, or URL is right'.format(app_name))


def app_delete(app, app_id, blacklist):
    app_name = app
    app_url = apps[app]['url']
    app_api = apps[app]['api']

    headers = {'X-Api-Key': app_api}

    # payload = {'id': app_id, 'blacklist': blacklist}

    r = requests.delete(app_url + '/api/queue/{}?blacklist={}'.format(app_id, blacklist),
                        headers=headers, timeout=30)

    try:
        if r.status_code == 401:
            logger.warning("Error when connecting to {}, unauthorised. check api/url".format(app_name))
        try:
            return r.json()
        except json.decoder.JSONDecodeError:
            logger.warning('{} did not return valid json'.format(app_name))
            logger.debug(r.content)

    except requests.ConnectionError:
        logger.warning('Can not connect to {0} check if {0} is up, or URL is right'.format(app_name))


def get_nzbget_data(data_type):
    nzbget_list = []
    return_list = {}

    if data_type == 'queue':
        nzbget_data = server.listgroups()
    elif data_type == 'history':
        nzbget_data = server.history()
    else:
        return False

    for item in nzbget_data:
        nzb_id = item['Parameters'][0]['Value']
        if nzb_id not in nzbget_list:
            nzbget_list.append(nzb_id)
            return_list[nzb_id] = item['ID']
    return return_list


def app_clean():
    for app in apps:
        queue = app_get_queue(app)
        for item in queue:
            if item['protocol'] == 'usenet':
                try:
                    for msg in item['statusMessages'][0]['messages']:
                        for x in blacklist_messages:
                            if msg in x:
                                app_delete(app, item['id'], 'true')
                                logger.info("Removing {} from {}'s queue and sending to blacklist".format(item['title'], app))
                except IndexError:
                    logger.debug('No status message found')


def nzbget_clean():
    history = get_nzbget_data('history')
    manager_list = []

    for app in apps:
        queue = app_get_queue(app)
        for id in queue:
            if (id['id']) not in manager_list:
                manager_list.append(id['id'])

    for item in history:
        if item not in manager_list:
            server.editqueue('HistoryDelete', '', [history[item]])


def delete_dir(path):
    shutil.rmtree(path)


def get_local_folders():
    subfolders = []
    try:
        for path in download_paths:
            path_list = os.listdir(path)
            for x in path_list:
                full = '{}{}'.format(path, x)
                if os.path.isdir(full):
                    subfolders.append(full)
        return subfolders
    except:
        logger.info('No such file or directory')


def get_live_folders():
    return_list = []
    history = server.history()

    for item in history:
        if item['DestDir'] not in return_list:
            return_list.append('{}{}/{}'.format(path_swap, item['DestDir'].split("/")[-2], item['DestDir'].split("/")[-1]))
    return return_list


def clean_folders():
    local = get_local_folders()
    live = get_live_folders()
    to_clean = []

    for file in local:
        if file not in live:
            to_clean.append(file)

    for orphan in to_clean:
        logger.info('Deleting: "{}"'.format(orphan))
        delete_dir(orphan)


if __name__ == "__main__":
    # Check apps for downloads with warnings and clean as config states
    if app_cleaner:
        logger.info('App cleaner function is on: Checking now')
        app_clean()
    # Check if nzbget is paused and resume if enough space
    if pause_checker:
        logger.info('Pause check function is on: Checking now')
        pause_check()
    # Check if nzbget history has orphaned items and clear them
    if nzbget_cleaner:
        logger.info('Nzbget cleaner function is on: Checking now')
        nzbget_clean()
    # Check if any folders in download are orphaned and delete them
    if folder_cleaner:
        logger.info('Folder cleaner function is on: Checking now')
        clean_folders()
