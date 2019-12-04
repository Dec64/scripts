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

host = "https://sonarr.domain.com/"
api_key = "xxxxxxxxxxxxxxxxxxxxxxx"

sortKey = "airDateUtc"
page_size = "150"
page = "1"
sortDirection = "descending"
monitored = "true"

delay = 10 # timer in seconds between requesting search

################################
# Logging
################################

logger = logging.getLogger(__name__)

################################
# Init
################################

headers = {'X-Api-Key': api_key,
           'Content-Type': 'application/json'}


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


missing_episodes = get_missing_list()
for episode in missing_episodes['records']:
    try:
        print("Forcing scan for {} - {}".format(episode['series']['title'], episode['title']))
    except:
        pass
    search_missing_ep(episode['id'])
    print("waiting {} seconds".format(delay))
    time.sleep(delay)

print("#################\n### Finished ###\n#################")
