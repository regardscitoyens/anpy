#           _   _ _______     __
#     /\   | \ | |  __ \ \   / /
#    /  \  |  \| | |__) \ \_/ /
#   / /\ \ | . ` |  ___/ \   /
#  / ____ \| |\  | |      | |
# /_/    \_\_| \_|_|      |_|

# Set default logging handler to avoid "No handler found" warnings.
import logging

__title__ = 'anpy'
__version__ = '0.1.8'
__author__ = 'Regards Citoyens'
__license__ = 'MIT'

from logging import NullHandler

logging.getLogger(__name__).addHandler(NullHandler())
