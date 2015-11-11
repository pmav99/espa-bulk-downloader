#!/usr/bin/env python

"""
Author: David Hill
Date: 01/31/2014
Purpose: A simple python client that will download all available (completed) scenes for
         a user order(s).

Requires: Python feedparser and standard Python installation.
"""

import os
import shutil
import hashlib  # Python 2.5+ only; replaced md5 and sha modules
import logging
import urllib2
import argparse

import feedparser

MAX_RETRIES = 3

__author__ = "David V. Hill"
__version__ = "1.2.0"

EPILOG = r"""
ESPA Bulk Download Client Version 1.0.0. [Tested with Python 2.7]

Retrieves all completed scenes for the user/order
and places them into the target directory.
Scenes are organized by order.
It is safe to cancel and restart the client, as it will
only download scenes one time (per directory)

*** Important ***
If you intend to automate execution of this script,
please take care to ensure only 1 instance runs at a time.
Also please do not schedule execution more frequently than
once per hour.

Examples:
---------
Linux/Mac : ./download_espa_order.py -e your_email@server.com -o ALL -d /some/directory/with/free/space
Windows   : C:\python27\python download_espa_order.py -e your_email@server.com -o ALL -d C:\some\directory\with\free\spa
"""


# Configure logging
try:  # Python 2.7+
    from logging import NullHandler
except ImportError:
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass
finally:
    logger = logging.getLogger('espa_bulk')
    # Set default logging handler to avoid "No handler found" warnings.
    logger.addHandler(NullHandler())


class SceneFeed(object):
    """SceneFeed parses the ESPA RSS Feed for the named email address and generates
    the list of Scenes that are available"""

    def __init__(self, email, host="http://espa.cr.usgs.gov"):
        """Construct a SceneFeed.

        Keyword arguments:
        email -- Email address orders were placed with
        host  -- http url of the RSS feed host
        """

        self.email = email

        if not host.startswith('http://'):
            host = ''.join(["http://", host])
        self.host = host

        self.feed_url = "%s/ordering/status/%s/rss/" % (self.host, self.email)


    def get_items(self, orderid='ALL'):
        """get_items generates Scene objects for all scenes that are available to be
        downloaded.  Supply an orderid to look for a particular order, otherwise all
        orders for self.email will be returned"""

        #yield Scenes with download urls
        feed = feedparser.parse(self.feed_url)

        for entry in feed.entries:

            #description field looks like this
            #'scene_status:thestatus,orderid:theid,orderdate:thedate'
            scene_order = entry.description.split(',')[1].split(':')[1]

            #only return values if they are in the requested order
            if orderid == "ALL" or scene_order == orderid:
                yield Scene(entry.link, scene_order)


class Scene(object):
    def __init__(self, srcurl, orderid):
        self.srcurl = srcurl
        self.md5url = srcurl.replace('tar.gz', 'md5')
        self.orderid = orderid
        parts = self.srcurl.split("/")
        self.filename = parts[len(parts) - 1]
        self.name = self.filename.split('.tar.gz')[0]


class LocalStorage(object):

    def __init__(self, basedir):
        self.basedir = basedir

    def directory_path(self, scene):
        return ''.join([self.basedir, os.sep, scene.orderid, os.sep])

    def scene_path(self, scene):
        return ''.join([self.directory_path(scene), scene.filename])

    def tmp_scene_path(self, scene):
        return ''.join([self.directory_path(scene), scene.filename, '.part'])

    def is_stored(self, scene):
        return os.path.exists(self.scene_path(scene))

    def store(self, scene, check_md5=False):
        if self.is_stored(scene):
            logger.info("Scene is already downloaded. Skipping: %s", scene.name)
            return

        download_directory = self.directory_path(scene)

        #make sure we have a target to land the scenes
        if not os.path.exists(download_directory):
            os.makedirs(download_directory)
            logger.info("Created target_directory:%s", download_directory)

        dl_okay = False
        n_retries = 0
        while not dl_okay:
            logger.info("Copying %s to %s", scene.name, download_directory)
            req = urllib2.urlopen(scene.srcurl)

            with open(self.tmp_scene_path(scene), 'wb') as target_handle:
                shutil.copyfileobj(req, target_handle)

            if check_md5:
                try:
                    md5_req = urllib2.urlopen(scene.md5url)
                except urllib2.URLError:
                    logger.info("md5 checksum for %s not available", scene.name)
                    dl_okay = True
                else:
                    md5sum_truth = md5_req.readline().split()[0]
                    with open(self.tmp_scene_path(scene), 'r') as dl:
                        md5sum_test = hashlib.md5(dl.read()).hexdigest()

                    if md5sum_truth != md5sum_test:
                        if n_retries >= MAX_RETRIES:
                            logger.info("md5 checksum for %s is not valid, but maximum retries exceeded", scene.name)
                            os.remove(self.tmp_scene_path(scene))
                        else:
                            logger.info("md5 checksum for %s is not valid. Retrying download", scene.name)
                            n_retries += 1
                    else:
                        logger.info("md5 checksum for %s is OKAY", scene.name)
                        dl_okay = True

        os.rename(self.tmp_scene_path(scene), self.scene_path(scene))


def process(target_directory, email, order, check_md5):
    logger.info("Started scene processing.")
    storage = LocalStorage(target_directory)
    processed = False
    for scene in SceneFeed(email).get_items(order):
        logger.info("Processing scene: %s", scene.name)
        storage.store(scene, check_md5=check_md5)
        processed = True
    if processed is False:
        logger.warning("No scenes were processed!")
    logger.info("Finished scenes processing.")


def cli():
    # parse CLI arguments
    parser = argparse.ArgumentParser(epilog=EPILOG, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "-e", "--email",
        required=True,
        help="email address for the user that submitted the order)"
    )
    parser.add_argument(
        "-o", "--order",
        required=True,
        help="which order to download (use ALL for every order)"
    )
    parser.add_argument(
        "-d", "--target_directory",
        required=True,
        help="where to store the downloaded scenes"
    )
    parser.add_argument(
        "-c", "--check_downloads",
        action='store_true', default=False,
        help="validate downloads against checksums; retry download if necessary"
    )
    parser.add_argument(
        "-s", "--silent",
        action='store_false',
        help="set this flag if you don't want log messages"
    )
    args = parser.parse_args()

    # setup logging.
    log_level = logging.WARNING if args.silent else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(levelname)-8s; %(asctime)s; %(name)s; %(funcName)s; %(lineno)4d: %(message)s"
    )

    # start processing
    process(args.target_directory, args.email, args.order, args.check_downloads)

if __name__ == "__main__":
    cli()
