metadata = dict(
    name='Ontario',
    capitol_timezone='America/Toronto',
    abbreviation='on',
    legislature_name='Legislative Assembly of Ontario',
    # this should all go away once metadata v2 lands
    lower_chamber_name='',
    upper_chamber_name='',
    lower_chamber_title='',
    upper_chamber_title='MPP',
    upper_chamber_term='',
    lower_chamber_term='',
    terms=[
        dict(name='40', sessions=['40:1'],
             start_year=2011, end_year=2013),
    ],
    session_details={
        '40:1': {'type': 'primary',
                 'display_name': '40th Legislature, 1st Session',
                 '_scraped_name': u'40:1 (2011-11-21 - 2012-10-15)',
                },
    },
    feature_flags=[],
    _ignored_scraped_sessions=[u'39:2 (2010-03-08 - 2011-06-01)',
                               u'39:1 (2007-11-28 - 2010-03-04)',
                               u'38:2 (2005-10-11 - 2007-09-10)',
                               u'38:1 (2003-11-19 - 2005-09-19)',
                               u'37:4 (2003-04-30 - 2003-09-02)',
                               u'37:3 (2002-05-09 - 2003-03-12)',
                               u'37:2 (2001-04-19 - 2002-03-01)',
                               u'37:1 (1999-10-20 - 2001-03-02)',
                               u'36:3 (1999-04-22 - 1999-05-04)',
                               u'36:2 (1998-04-23 - 1998-12-18)',
                               u'36:1 (1995-09-26 - 1997-12-18)']

)


def session_list():
    from billy.scrape.utils import url_xpath
    import re
    options = url_xpath('http://www.ontla.on.ca/web/bills/bills_all.do?locale=en', '//option/text()')
    return [re.sub('\s+', ' ', opt.strip()) for opt in options]
