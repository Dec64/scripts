#!/usr/bin/env python
import requests
import logging
import sys
import json
from bs4 import BeautifulSoup

################################
# About
################################
#
# This script reads RSS feeds from most newznab based indexers (tested with nzbgeek and dog). 
# It then checks if you have any of the shows in the RSS feed added to sonarr, if not, adds them.
#
# The intention of this is to auto add 4K shows to a seperate 4k Sonarr instance as 4k versions become available.
#
# Run this script on a cron.
#
################################
# Config
################################

# Add rocket chat webhook here if you want to send notifcation on adding shows
# Leave blank if you do not want to use
uri = ''

sonarr_url = 'https://sonarr4k.domain.com:443'
sonarr_api = ''
sonarr_path = '/mnt/unionfs/Media/4K-TV'
rss_url = {'https://api.nzbgeek.info/rss?t=5045&dl=1&num=50&r=xxxxxxxxxxxxx',
           'https://dognzb.cr/rss.cfm?r=xxxxxxxxxxxxx&t=5045&num=100'}
quality_profile_id = 5

################################
# Logging
################################

# Logging format
formatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s')

# root logger
logger = logging.getLogger()
# Set initial level to INFO
logger.setLevel(logging.INFO)

# Console handler, log to stdout
consoleHandler = logging.StreamHandler(sys.stdout)
consoleHandler.setFormatter(formatter)
logger.addHandler(consoleHandler)

# Other modules logging levels
logging.getLogger('requests').setLevel(logging.INFO)

################################
# Init
################################

headers = {'X-Api-Key': sonarr_api}

options = {'ignoreEpisodesWithFiles': False, 'ignoreEpisodesWithoutFiles': False,
           'searchForMissingEpisodes': True}

################################
# Main
################################


def get_rss_tvdbid():
    tvdb_id_list = []

    for url in rss_url:
        req = requests.get(url)
        handler = req.text.encode('utf-8')
        soup = BeautifulSoup(handler, 'xml')

        for item in soup.findAll('item'):

            newznabs = item.findAll('newznab:attr')
            newz_dict = {}

            for attribute in newznabs:
                newz_dict[attribute['name'].split('.')[0]] = attribute['value'].split(".")[0]
                try:
                    if newz_dict['tvdbid'] not in tvdb_id_list:
                        tvdb_id_list.append(newz_dict['tvdbid'])
                except KeyError:
                    pass
    return tvdb_id_list


def get_library():
    library = []
    r = requests.get(sonarr_url + '/api/series', headers=headers, timeout=60)
    try:
        if r.status_code == 401:
            logger.warning("Error when connecting to sonarr, unauthorised. check api/url")
            sys.exit(1)
        tv_lib_raw = r.json()
        for n in tv_lib_raw:
            if n['tvdbId'] not in library:
                library.append(n['tvdbId'])
    except requests.ConnectionError:
        logger.warning('Can not connect to sonarr check if sonarr is up, or URL is right')
        sys.exit(1)
    return library


def send_to_sonarr(tvid):
    logger.info('Attempting to send to sonarr')

    payload = {'tvdbId': tvid, 'title': '', 'qualityProfileId': quality_profile_id, 'images': [],
               'seasons': [], 'seasonFolder': True, 'monitored': True, 'rootFolderPath': sonarr_path,
               'addOptions': options, }

    r = requests.post(sonarr_url + '/api/series', headers=headers, data=json.dumps(payload), timeout=30)

    if r.status_code == 201:
        logger.info('sent to sonarr successfully')
        return True

    else:
        logger.info('failed to send to sonarr, code return: {}'.format(r.status_code))
        logger.debug(r.content)


def library_compare(source, new):
    library = []
    for tvid in new:
        if int(tvid) not in source:
            library.append(tvid)
        else:
            logger.debug('{} is already in library'.format(tvid))
    return library


def send_notif(info):
    data = {
        "username": "Sonarr RSS Bot",
        "icon_emoji": ":robot:",
        "attachments": [
            {
                "title": "Sonarr RSS Feed",
                "text": "{} Show(s) where added to sonarr".format(info)
            }
        ]
    }

    r = requests.post(uri, json.dumps(data)).content
    return r


if __name__ == '__main__':
    library = get_library()
    rss_library = get_rss_tvdbid()
    content = library_compare(library, rss_library)
    logger.info(content)
    logger.info(library)
    if len(content) == 0:
        logger.info('no shows to add')
    else:
        for show in content:
            send_to_sonarr(show)
        if uri:
            send_notif(len(content))
            logger.info('Finished')
