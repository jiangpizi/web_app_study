#!/usr/bin/env python
# -*- coding: utf-8 -*-

if __name__=="__main__":
    import re
    _RE_INTERCEPTROR_STARTS_WITH = re.compile(r'^([^\*\?]+)\*?$')
    m  = _RE_INTERCEPTROR_STARTS_WITH.match('/dad/dada/*')
    print m.groups()

