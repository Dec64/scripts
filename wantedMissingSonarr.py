#!/usr/bin/env python
#

################################
# Simple script to get the wanted missing from sonarr and force a
# search on them one by one with a delay timer in between
################################

import logging
import requests
import time

################################
# Config
################################

host = "https://sonarr.doamin.com/" # Sonarr URL
api_key = "xxxxxxxxxxxxxxxxxxx" # Sonarr API Key

page_size = "150" # Number of episodes to go back and search

refresh = True # Refresh series before performing a search

delay = 10 # timer in seconds between requesting search
refresh_delay = 5 # timer in seconds to delay between refreshing and searching

################################
# Logging
################################

logger = logging.getLogger(__name__)

################################
# Init
################################

headers = {'X-Api-Key': api_key,
           'Content-Type': 'application/json'}
page = "1" # Do not change
sortDirection = "descending" # Do not change
monitored = "true" # Do not change
sortKey = "airDateUtc" # Do not change


################################
# Main
################################


def get_missing_list():
    missing = []
    data = "page={}&pageSize={}&sortDirection={}&sortKey={}&monitored={}".format(
        page,
        page_size,
        sortDirection,
        sortKey,
        monitored
    )
    r = requests.get(host + 'api/wanted/missing?{}'.format(data), headers=headers, timeout=60, json=data)
    try:
        if r.status_code == 401:
            logger.warning("Error when connecting to sonarr, unauthorised. check api/url")
    except requests.ConnectionError:
        logger.warning("Can not connect to sonarr check if sonarr is up, or URL is right")
    return r.json()


def search_missing_ep(ep_id):
    data = {"name": "EpisodeSearch",
            "episodeIds": [ep_id]}
    r = requests.post(host + 'api/v3/command', headers=headers, timeout=60, json=data)


def refresh_series(s_id):
    data = {"name": "RefreshSeries",
            "seriesId": s_id}
    r = requests.post(host + 'api/v3/command', headers=headers, timeout=60, json=data)
    if r.status_code == 201:
        return True
    else:
        return False


missing_episodes = get_missing_list()
for episode in missing_episodes['records']:
    refreshed = []
    if refresh and episode['series']['id'] not in refreshed:
        print("Refreshing series: {}".format(episode['series']['title']))
        refresh_series(episode['series']['id'])
        refreshed.append(episode['series']['id'])
        print("Waiting {} seconds for refresh".format(refresh_delay))
        time.sleep(refresh_delay)
    try:
        print("Forcing scan: {} - {}".format(episode['series']['title'], episode['title']))
    except:
        pass
    search_missing_ep(episode['id'])
    print("Waiting {} seconds until moving to next episode".format(delay))
    print("#################")
    time.sleep(delay)

print("#################\n### Finished ###\n#################")
