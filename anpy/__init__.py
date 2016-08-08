# -*- coding: utf-8 -*-

#           _   _ _______     __
#     /\   | \ | |  __ \ \   / /
#    /  \  |  \| | |__) \ \_/ /
#   / /\ \ | . ` |  ___/ \   /
#  / ____ \| |\  | |      | |
# /_/    \_\_| \_|_|      |_|

__title__ = 'anpy'
__version__ = '0.1.8'
__author__ = 'Regards Citoyens'
__license__ = 'MIT'


from .model import Amendement, AmendementSummary, AmendementSearchResult, QuestionSearchResult, QuestionSummary
from .service import AmendementSearchService, QuestionSearchService

# Set default logging handler to avoid "No handler found" warnings.
import logging

try:  # Python 2.7+
    from logging import NullHandler
except ImportError:
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass

logging.getLogger(__name__).addHandler(NullHandler())
