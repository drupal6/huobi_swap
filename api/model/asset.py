# -*- coding:utf-8 -*-

"""
Asset module.
"""

import json


class Asset:
    """ Asset object.

    Args:
        assets: Asset information, e.g. {"BTC": {"free": "1.1", "locked": "2.2", "total": "3.3"}, ... }
        timestamp: Published time, millisecond.
        update: If any update? True or False.
    """

    def __init__(self, assets=None, timestamp=None, update=False):
        """ Initialize. """
        self.assets = assets
        self.timestamp = timestamp
        self.update = update

    @property
    def data(self):
        d = {
            "assets": self.assets,
            "timestamp": self.timestamp,
            "update": self.update
        }
        return d

    def __str__(self):
        info = json.dumps(self.data)
        return info

    def __repr__(self):
        return str(self)
