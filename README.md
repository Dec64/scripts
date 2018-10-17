# scripts
A bunch of Misc scripts that I created to make my life easier.


# sonarr_rss_4k.py

sonarr_rss_4k.py takes newznab based rss feeds, hopefully one's from the TV 4K Catagory,
and adds any show that I do not already have into sonarr to be watched. This way I can download 4k TV as/when it's released
rather then add all TV and have a huge database of missing content.

# dl_manager.py

dl_manager.py is a catch-all lazy script that just automates tasks I do everyday to upkeep the server. It can check if NZBGET
is paused due to low space, and resume it if there is now enough free space to continue. It can also check all instances of
sonarr and radarr to see any downloads that have warnings due to issues and it removes/blacklists the releases based upon what
the issue is. Nzbget cleaner function will remove any leftover records from history as sometimes radarr/sonarr do not fully remove
completed downloads from history. It can also check any completed download folders you wish for orphaned files pointlessly using up
diskspace, and removes them.
