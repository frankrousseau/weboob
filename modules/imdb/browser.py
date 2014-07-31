# -*- coding: utf-8 -*-

# Copyright(C) 2013 Julien Veyssier
#
# This file is part of weboob.
#
# weboob is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# weboob is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with weboob. If not, see <http://www.gnu.org/licenses/>.

import re

from HTMLParser import HTMLParser
from weboob.tools.browser import BaseBrowser, BrowserHTTPNotFound
from weboob.capabilities.base import NotAvailable, NotLoaded
from weboob.capabilities.cinema import Movie, Person
from weboob.tools.json import json

from .pages import PersonPage, MovieCrewPage, BiographyPage,  ReleasePage

from datetime import datetime

__all__ = ['ImdbBrowser']


class ImdbBrowser(BaseBrowser):
    DOMAIN = 'www.imdb.com'
    PROTOCOL = 'http'
    ENCODING = 'utf-8'
    USER_AGENT = BaseBrowser.USER_AGENTS['wget']
    PAGES = {
        'http://www.imdb.com/title/tt[0-9]*/fullcredits.*': MovieCrewPage,
        'http://www.imdb.com/title/tt[0-9]*/releaseinfo.*': ReleasePage,
        'http://www.imdb.com/name/nm[0-9]*/*': PersonPage,
        'http://www.imdb.com/name/nm[0-9]*/bio.*': BiographyPage,
    }

    def iter_movies(self, pattern):
        res = self.readurl('http://www.imdb.com/xml/find?json=1&nr=1&tt=on&q=%s' % pattern.encode('utf-8'))
        jres = json.loads(res)
        htmlparser = HTMLParser()
        for cat in ['title_popular', 'title_exact', 'title_approx']:
            if cat in jres:
                for m in jres[cat]:
                    tdesc = unicode(m['title_description'])
                    if '<a' in tdesc and '>' in tdesc:
                        short_description = u'%s %s' % (tdesc.split('<')[
                                                        0].strip(', '), tdesc.split('>')[1].split('<')[0])
                    else:
                        short_description = tdesc.strip(', ')
                    movie = Movie(m['id'], htmlparser.unescape(m['title']))
                    movie.other_titles = NotLoaded
                    movie.release_date = NotLoaded
                    movie.duration = NotLoaded
                    movie.short_description = htmlparser.unescape(short_description)
                    movie.pitch = NotLoaded
                    movie.country = NotLoaded
                    movie.note = NotLoaded
                    movie.roles = NotLoaded
                    movie.all_release_dates = NotLoaded
                    movie.thumbnail_url = NotLoaded
                    yield movie

    def iter_persons(self, pattern):
        res = self.readurl('http://www.imdb.com/xml/find?json=1&nr=1&nm=on&q=%s' % pattern.encode('utf-8'))
        jres = json.loads(res)
        htmlparser = HTMLParser()
        for cat in ['name_popular', 'name_exact', 'name_approx']:
            if cat in jres:
                for p in jres[cat]:
                    person = Person(p['id'], htmlparser.unescape(unicode(p['name'])))
                    person.real_name = NotLoaded
                    person.birth_place = NotLoaded
                    person.birth_date = NotLoaded
                    person.death_date = NotLoaded
                    person.gender = NotLoaded
                    person.nationality = NotLoaded
                    person.short_biography = NotLoaded
                    person.short_description = htmlparser.unescape(p['description'])
                    person.roles = NotLoaded
                    person.thumbnail_url = NotLoaded
                    yield person

    def get_movie(self, id):
        res = self.readurl('http://www.omdbapi.com/?i=%s&plot=full' % id)
        if res is not None:
            jres = json.loads(res)
        else:
            return None
        htmlparser = HTMLParser()

        title = NotAvailable
        duration = NotAvailable
        release_date = NotAvailable
        pitch = NotAvailable
        country = NotAvailable
        note = NotAvailable
        short_description = NotAvailable
        thumbnail_url = NotAvailable
        other_titles = []
        genres = []
        roles = {}

        if 'Title' not in jres:
            return
        title = htmlparser.unescape(unicode(jres['Title'].strip()))
        if 'Poster' in jres:
            thumbnail_url = unicode(jres['Poster'])
        if 'Director' in jres:
            short_description = unicode(jres['Director'])
        if 'Genre' in jres:
            for g in jres['Genre'].split(', '):
                genres.append(g)
        if 'Runtime' in jres:
            m = re.search('(\d+?) min', jres['Runtime'])
            if m:
                duration = int(m.group(1))
        if 'Released' in jres:
            release_date = datetime.strptime(str(jres['Released']), '%d %b %Y')
        if 'Country' in jres:
            country = u''
            for c in jres['Country'].split(', '):
                country += '%s, ' % c
            country = country[:-2]
        if 'Plot' in jres:
            pitch = unicode(jres['Plot'])
        if 'imdbRating' in jres and 'imdbVotes' in jres:
            note = u'%s/10 (%s votes)' % (jres['imdbRating'], jres['imdbVotes'])
        for r in ['Actors', 'Director', 'Writer']:
            if '%s' % r in jres.keys():
                roles['%s' % r] = jres['%s' % r].split(', ')

        movie = Movie(id, title)
        movie.other_titles = other_titles
        movie.release_date = release_date
        movie.duration = duration
        movie.genres = genres
        movie.pitch = pitch
        movie.country = country
        movie.note = note
        movie.roles = roles
        movie.short_description = short_description
        movie.all_release_dates = NotLoaded
        movie.thumbnail_url = thumbnail_url
        return movie

    def get_person(self, id):
        try:
            self.location('http://www.imdb.com/name/%s' % id)
        except BrowserHTTPNotFound:
            return
        assert self.is_on_page(PersonPage)
        return self.page.get_person(id)

    def get_person_biography(self, id):
        self.location('http://www.imdb.com/name/%s/bio' % id)
        assert self.is_on_page(BiographyPage)
        return self.page.get_biography()

    def iter_movie_persons(self, movie_id, role):
        self.location('http://www.imdb.com/title/%s/fullcredits' % movie_id)
        assert self.is_on_page(MovieCrewPage)
        for p in self.page.iter_persons(role):
            yield p

    def iter_person_movies(self, person_id, role):
        self.location('http://www.imdb.com/name/%s' % person_id)
        assert self.is_on_page(PersonPage)
        return self.page.iter_movies(role)

    def iter_person_movies_ids(self, person_id):
        self.location('http://www.imdb.com/name/%s' % person_id)
        assert self.is_on_page(PersonPage)
        for movie in self.page.iter_movies_ids():
            yield movie

    def iter_movie_persons_ids(self, movie_id):
        self.location('http://www.imdb.com/title/%s/fullcredits' % movie_id)
        assert self.is_on_page(MovieCrewPage)
        for person in self.page.iter_persons_ids():
            yield person

    def get_movie_releases(self, id, country):
        self.location('http://www.imdb.com/title/%s/releaseinfo' % id)
        assert self.is_on_page(ReleasePage)
        return self.page.get_movie_releases(country)
