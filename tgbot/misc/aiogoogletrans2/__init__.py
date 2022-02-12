"""Free Google Translate API for Python. Translates totally free of charge."""
__all__ = 'Translator',
__version__ = '0.0.1'


#from aiogoogletrans2.client import Translator
from tgbot.misc.aiogoogletrans2.constants import LANGCODES, LANGUAGES  # noqa

from tgbot.misc.aiogoogletrans2.client import Translator

