import logging
import os
import time
from datetime import datetime
from datetime import timedelta
from .xmlrpc import ServerProxy

log = logging.getLogger(__name__)


class Rtorrent:
    def __init__(self, url):
        self.url = "%s/RPC2" % url
        self.xmlrpc = ServerProxy(self.url)

    def get_torrents(self):
        """"Get all torrents"""
        torrent_list = {}
        try:
            with self.xmlrpc as proxy:
                torrent_list_raw = proxy.d.multicall2(
                    # List type
                    "",
                    # View
                    "",
                    # Attributes
                    "d.hash=",
                    "d.name=",
                    "d.is_multi_file=",
                    "d.base_path=",
                    "d.complete=",
                    "d.is_open=",
                    "d.custom1=",
                    "d.directory="
                )

                for t in torrent_list_raw:
                    # Get files if multifile torrent
                    files = None
                    if t[2]:
                        files = proxy.f.multicall(
                            # Hash
                            t[0],
                            # Pattern
                            "",
                            # Get files path
                            "f.path="
                        )
                        # Flatten list
                        files = [os.path.join(t[7], f) for subf in files for f in subf]
                    else:
                        files = [os.path.join(t[7], t[1])]

                    torrent_list[t[0]] = {
                        'hash': t[0],
                        'name': t[1],
                        'is_multi_file': t[2],
                        'base_path': t[3],
                        'files': files,
                        'complete': t[4],
                        'is_open': t[5],
                        'label': t[6],
                        'directory': t[7]
                    }
            return torrent_list

        except Exception:
            log.exception("Exception retrieving torrents: ")
        return {}

    def start(self, t_hash):
        """"Start the torrent"""
        with self.xmlrpc as proxy:
            proxy.d.try_start(t_hash)
            return proxy.d.is_active(t_hash)

    def stop(self, t_hash):
        """"Stop the torrent"""
        with self.xmlrpc as proxy:
            proxy.d.try_stop(t_hash)
            return proxy.d.is_active(t_hash)

    def pause(self, t_hash):
        """Pause the torrent"""
        with self.xmlrpc as proxy:
            m = proxy.d.pause(t_hash)
            return m

    def resume(self, t_hash):
        """Resume the torrent"""
        with self.xmlrpc as proxy:
            m = proxy.d.resume(t_hash)
            return m

    def close(self, t_hash):
        """Close the torrent"""
        with self.xmlrpc as proxy:
            m = proxy.d.close(t_hash)
            return m

    def delete(self, t_hash):
        """delete the torrent"""
        with self.xmlrpc as proxy:
            m = proxy.d.erase(t_hash)
            return m

    def check_message(self, t_hash):
        with self.xmlrpc as proxy:
            return proxy.d.message(t_hash)

    def ratio_check(self, t_hash, ratio_limit):
        with self.xmlrpc as proxy:
            ratio = proxy.d.ratio(t_hash)
            left = proxy.d.left_bytes(t_hash)
            if left == 0 and ratio > int(ratio_limit):
                return True
            else:
                return False

    def time_test(self, t_hash, t_time):
        with self.xmlrpc as proxy:
            if proxy.d.complete(t_hash) == 1:
                s1 = time.strftime("%H:%M:%S", time.localtime(proxy.d.timestamp.finished(t_hash)))
                currentDT = datetime.now()
                s2 = currentDT.strftime("%H:%M:%S")
                FMT = '%H:%M:%S'
                tdelta = datetime.strptime(s2, FMT) - datetime.strptime(s1, FMT)
                if tdelta.days < 0:
                    tdelta = timedelta(days=0,
                                       seconds=tdelta.seconds, microseconds=tdelta.microseconds)
                if tdelta.seconds >= int(t_time):
                    return True
                else:
                    return False

    def set_directory_base(self, t_hash, base_path):
        """Set base directory of torrent"""
        with self.xmlrpc as proxy:
            proxy.d.try_stop(t_hash)
            proxy.d.directory_base.set(t_hash, base_path)
            return proxy.d.base_path(t_hash)
