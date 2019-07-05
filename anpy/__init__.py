# -*- coding: utf-8 -*-

#           _   _ _______     __
#     /\   | \ | |  __ \ \   / /
#    /  \  |  \| | |__) \ \_/ /
#   / /\ \ | . ` |  ___/ \   /
#  / ____ \| |\  | |      | |
# /_/    \_\_| \_|_|      |_|

# Set default logging handler to avoid "No handler found" warnings.
import logging

__title__ = 'anpy'
__version__ = '0.1.17'
__author__ = 'Regards Citoyens'
__license__ = 'MIT'

try:  # Python 2.7+
    from logging import NullHandler
except ImportError:
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass

logging.getLogger(__name__).addHandler(NullHandler())
