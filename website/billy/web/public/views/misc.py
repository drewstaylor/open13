"""
    views that are not object specific
"""
import json
import urllib2

import pymongo

from django.shortcuts import render, redirect
from django.conf import settings
from django.http import HttpResponse

from billy.models import db, Metadata, Legislator
from billy.models.pagination import CursorPaginator
from billy.core import settings as billy_settings
from .utils import templatename, RelatedObjectsList


def homepage(request):
    '''
    Context:
        all_metadata

    Templates:
        - billy/web/public/homepage.html
    '''
    return render(request, templatename('homepage'),
                  dict(
              all_metadata=map(Metadata.get_object, settings.ACTIVE_STATES)))


def downloads(request):
    '''
    Context:
        - all_metadata

    Templates:
        - billy/web/public/downloads.html
    '''
    all_metadata = sorted(db.metadata.find(), key=lambda x: x['name'])
    return render(request, 'billy/web/public/downloads.html',
                  {'all_metadata': all_metadata})


def find_your_legislator(request):
    '''
    Context:
        - request
        - lat
        - long
        - located
        - legislators

    Templates:
        - billy/web/public/find_your_legislator_table.html
    '''

    # check if lat/lon are set
    # if leg_search is set, they most likely don't have ECMAScript enabled.
    # XXX: fallback behavior here for alpha.

    get = request.GET
    context = {}
    template = 'find_your_legislator'

    context['request'] = ""
    if "q" in get:
        context['request'] = get['q']

    if "lat" in get and "lon" in get:
        # We've got a passed lat/lon. Let's build off it.
        lat = get['lat']
        lon = get['lon']

        context['lat'] = lat
        context['lon'] = lon
        context['located'] = True

        qurl = "%slegislators/geo/?long=%s&lat=%s&apikey=%s" % (
            billy_settings.API_BASE_URL,
            lon,
            lat,
            getattr(billy_settings, 'API_KEY', '')
        )
        leg_resp = json.load(urllib2.urlopen(qurl))
        # allow limiting lookup to region for region map views
        if 'abbr' in get:
            leg_resp = [leg for leg in leg_resp
                        if leg[billy_settings.LEVEL_FIELD] == get['abbr']]
            context['abbr'] = get['abbr']

        if "boundary" in get:
            to_search = []
            for leg in leg_resp:
                to_search.append(leg['boundary_id'])
            borders = set(to_search)
            ret = {}
            for border in borders:
                qurl = "%sdistricts/boundary/%s/?apikey=%s" % (
                    billy_settings.API_BASE_URL,
                    border,
                    getattr(billy_settings, 'API_KEY', '')
                )
                resp = json.load(urllib2.urlopen(qurl))
                ret[border] = resp
            return HttpResponse(json.dumps(ret))

        context['legislators'] = map(Legislator, leg_resp)
        template = 'find_your_legislator_table'

    return render(request, templatename(template), context)


def get_district(request, district_id):
    qurl = "%sdistricts/boundary/%s/?apikey=%s" % (
        billy_settings.API_BASE_URL,
        district_id,
        billy_settings.API_KEY
    )
    f = urllib2.urlopen(qurl)
    return HttpResponse(f)


### Votes & News don't really fit here or anywhere


class VotesList(RelatedObjectsList):
    '''
    Context (see utils.ListViewBase an utils.RelatedObjectsList):
        - column_headers
        - rowtemplate_name
        - description_template
        - object_list
        - nav_active
        - abbr
        - metadata
        - url
        - use_table
        - obj
        - collection_name

    Templates:
        - billy/web/public/object_list.html
        - billy/web/public/votes_list_row.html
    '''
    list_item_context_name = 'vote'
    collection_name = 'votes'
    mongo_sort = [('date', pymongo.DESCENDING)]
    paginator = CursorPaginator
    query_attr = 'votes_manager'
    use_table = True
    rowtemplate_name = templatename('votes_list_row')
    column_headers_tmplname = templatename('votes_column_headers')
    nav_active = 'bills'
    description_template = '''
        Votes by <a href="{{obj.get_absolute_url}}">{{obj.display_name}}</a>
        '''
    title_template = '''
        {% if obj.collection_name == 'bills' %}
            Votes on bill {{obj.display_name}} - {{metadata.legislature_name}}
        {% elif obj.collection_name == 'legislators' %}
            Votes by {{obj.display_name}} - {{metadata.legislature_name}}
        {% endif %}
        '''

    def get(self, request, abbr, collection_name, _id):
        # hack to redirect to proper legislator on legislators/_id_/votes
        if collection_name == 'legislators':
            leg = db.legislators.find_one({'_all_ids': _id})
            if leg and leg['_id'] != _id:
                return redirect('votes_list', abbr, collection_name,
                                leg['_id'])
        return super(VotesList, self).get(request, abbr, collection_name, _id)


class NewsList(RelatedObjectsList):
    '''
    Context (see utils.ListViewBase an utils.RelatedObjectsList):
        - column_headers
        - rowtemplate_name
        - description_template
        - object_list
        - nav_active
        - abbr
        - metadata
        - url
        - use_table
        - obj
        - collection_name

    Templates:
        - billy/web/public/object_list.html
        - billy/web/public/feed_entry.html
    '''
    list_item_context_name = 'entry'
    mongo_sort = [('published_parsed', pymongo.DESCENDING)]
    paginator = CursorPaginator
    query_attr = 'feed_entries'
    rowtemplate_name = templatename('feed_entry')
    column_headers_tmplname = templatename('news_column_headers')
    nav_active = 'bills'
    collection_name = 'entries'
    description_template = '''
        news and blog entries mentioning
        <a href="{{obj.get_absolute_url}}">{{obj.display_name}}</a>
        '''
    title_template = '''
        News and blogs mentioning {{obj.display_name}} -
        {{metadata.legislature_name}}
        '''

    def get(self, request, abbr, collection_name, _id, slug):
        # hack to redirect to proper legislator on legislators/_id_/news
        if collection_name == 'legislators':
            leg = db.legislators.find_one({'_all_ids': _id})
            if leg and leg['_id'] != _id:
                return redirect('news_list', abbr, collection_name,
                                leg['_id'], slug)
        return super(NewsList, self).get(request, abbr, collection_name, _id,
                                          slug)
