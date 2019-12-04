#!/usr/bin/env python
#

################################
# Simple script to get the wanted missing from radarr and force a
# search on them one by one with a delay timer in between
################################

import logging
import requests
import time

################################
# Config
################################

host = "https://radarr.domain.com/"
api_key = "xxxxxxxxxxxxxxxxxxxx"

sortKey = "physicalRelease"
page_size = "5000"
page = "1"
sortDirection = "asc"
filterKey = "monitored"

delay = 20

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
    data = "page={}&pageSize={}&sortDirection={}&sortKey={}&filterKey={}".format(
        page,
        page_size,
        sortDirection,
        sortKey,
        filterKey
    )
    r = requests.get(host + 'api/wanted/missing?{}'.format(data), headers=headers, timeout=60, json=data)
    try:
        if r.status_code == 401:
            logger.warning("Error when connecting to sonarr, unauthorised. check api/url")
    except requests.ConnectionError:
        logger.warning("Can not connect to sonarr check if sonarr is up, or URL is right")
    return r.json()


def search_missing_movie(mov_id):
    data = {"name": "MoviesSearch",
            "movieIds": [mov_id]}
    r = requests.post(host + 'api/command', headers=headers, timeout=60, json=data)
    print(r.json())


missing_movies = get_missing_list()
for movie in missing_movies['records']:
    try:
        print("Forcing scan for {}".format(movie['title']))
    except:
        pass
    search_missing_movie(movie['id'])
    print("waiting {} seconds".format(delay))
    time.sleep(delay)

print("#################\n### Finished ###\n#################")
