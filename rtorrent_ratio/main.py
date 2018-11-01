import shutil
import os

from utils.rtorrent import Rtorrent

# Config

# How long in seconds torrent must be to consider removing
torrent_age = 600

# https://user:pass@rutorrent.domain.com
url = ''

# If using cloudbox/docker then add the missing part of the start of the path. otherwise leave empty
docker_path = '/mnt/local/'

# Init

# fetch torrent list
rtorrent = Rtorrent(url)
torrents = rtorrent.get_torrents()


def delete_folder(path):
    path = '{}{}'.format(docker_path, path)
    try:
        shutil.rmtree(path)
    except NotADirectoryError:
        os.remove(path)


for torrent in torrents:

    msg = rtorrent.check_message(torrent)
    if 'Tracker: [Failure reason "Unregistered torrent"]' in str(msg):
        rtorrent.stop(torrent)
        delete_folder(torrents[torrent]['base_path'])
        rtorrent.delete(torrent)
        print('Deleted due unregistered torrent:\n{}'.format(torrents[torrent]['name']))
        continue
    if rtorrent.time_test(torrent, torrent_age) and rtorrent.ratio_check(torrent):
        rtorrent.stop(torrent)
        delete_folder(torrents[torrent]['base_path'])
        rtorrent.delete(torrent)
        print('Deleted due to meeting ratio and time requirement:\n{}'.format(torrents[torrent]['name']))
