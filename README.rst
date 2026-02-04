*****
hdate
*****

.. image:: https://img.shields.io/pypi/v/hdate
    :alt: PyPI - Version
    :target: https://pypi.org/project/hdate/
.. image:: https://readthedocs.org/projects/py-libhdate/badge/?version=latest
    :alt: Documentation Status
    :target: https://py-libhdate.readthedocs.io/en/latest/?badge=latest
.. image:: https://img.shields.io/python/required-version-toml?tomlFilePath=https%3A%2F%2Fraw.githubusercontent.com%2Fpy-libhdate%2Fpy-libhdate%2Fmain%2Fpyproject.toml
    :alt: Python Version from PEP 621 TOML
    :target: https://github.com/py-libhdate/py-libhdate/blob/main/pyproject.toml#L17
.. image:: https://img.shields.io/pypi/l/hdate
    :alt: PyPI - License
    :target: https://github.com/py-libhdate/py-libhdate/blob/main/LICENSE
.. image:: https://codecov.io/gh/py-libhdate/py-libhdate/graph/badge.svg?token=JGBmTslA1S 
    :alt: Code coverage status
    :target: https://codecov.io/gh/py-libhdate/py-libhdate

The ``hdate`` Python library's purpose is to provide information about the Hebrew date and times.

Originally ported from the C version of `libhdate <http://libhdate.sourceforge.net/>`_ by
`Royi Reshef <https://github.com/royi1000>`_, it is currently maintained by
`Tsvi Mostovicz <https://github.com/tsvi>`_ and is the backend library for
`Home Assistant's <https://home-assistant.io>`_ Jewish Calendar integration.

===========

Installation using pip:
#######################

.. code :: shell

    $ pip install hdate

===========

Examples:
#########

Provide the times of the day in Hebrew...

.. code :: python

    >>> import hdate
    >>> import datetime
    >>> c = hdate.Location("פתח תקוה", 32.08707, 34.88747, "Asia/Jerusalem", 54)
    >>> z = hdate.Zmanim(date=datetime.date(2016, 4, 18), location=c)
    >>> print(z)
    עלות השחר - 04:52:00
    משיכיר - 05:18:00
    הנץ החמה - 06:06:00
    סוף זמן קריאת שמע - 09:23:00
    סוף זמן תפילה - 10:28:40
    חצות היום - 12:40:00
    מנחה גדולה - 13:12:50
    מנחה גדולה 30 דק - 13:10:00
    מנחה קטנה - 16:29:50
    פלג המנחה - 17:51:55
    שקיעה - 19:14:00
    צאת הכוכבים (18 דק) - 19:50:00
    מוצאי צום - 19:40:00
    מוצאי שבת - 19:50:00
    לילה לרבנו תם - 20:32:48
    חצות הלילה - 00:40:00

... and in English.

.. code :: python

    >>> from hdate.translator import set_language
    >>> set_language("en")
    >>> z = hdate.Zmanim(date=datetime.date(2016, 4, 18), location=c)
    >>> print(z)
    Alot HaShachar - 04:52:00
    Misheyakir - 05:18:00
    Sunrise - 06:06:00
    Latest time for Shema - 09:23:00
    Latest time for Tefilla - 10:28:40
    Midday - 12:40:00
    Big Mincha - 13:12:50
    Big Mincha 30 min - 13:10:00
    Small Mincha - 16:29:50
    Plag Mincha - 17:51:55
    Sunset - 19:14:00
    Tset Hakochavim (18 minutes) - 19:50:00
    End of fast - 19:40:00
    End of Shabbat - 19:50:00
    Night by Rabbeinu Tam - 20:32:48
    Midnight - 00:40:00

===========

Provide the full Hebrew date ...

.. code :: python

    >>> set_language("he")
    >>> h = hdate.HDateInfo(datetime.date(2016, 4, 26))
    >>> print(h)
    יום שלישי י"ח בניסן ה' תשע"ו ג' לעומר חול המועד פסח

... and in English.

.. code :: python

    >>> set_language("en")
    >>> h = hdate.HDateInfo(datetime.date(2016, 4, 18))
    >>> print(h)
    Monday 10 Nisan 5776
