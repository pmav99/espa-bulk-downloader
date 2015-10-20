#!/usr/bin/env python
# -*- coding: utf-8 -*-
# author: Panagiotis Mavrogiorgos
# email: gmail, pmav99

"""

"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from setuptools import setup, find_packages

import espa_bulk_downloader as package

setup(
    name=package.__name__,
    version=package.__version__,
    author=package.__author__,
    packages=find_packages(),
    install_requires=[
        'feedparser',
    ],
    entry_points="""
        [console_scripts]
        download_espa_order.py=espa_bulk_downloader:main
    """,
)
