from pkg_resources import get_distribution, DistributionNotFound

from .retry import *
from .tasks import *
from .wait import *


try:
    __version__ = get_distribution(__name__).version
except DistributionNotFound:
    pass
