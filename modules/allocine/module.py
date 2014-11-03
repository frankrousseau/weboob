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

from weboob.capabilities.cinema import CapCinema, Person, Movie
from weboob.tools.backend import Module

from .browser import AllocineBrowser

from urllib import quote_plus

__all__ = ['AllocineModule']


class AllocineModule(Module, CapCinema):
    NAME = 'allocine'
    MAINTAINER = u'Julien Veyssier'
    EMAIL = 'julien.veyssier@aiur.fr'
    VERSION = '1.1'
    DESCRIPTION = u'AlloCiné French cinema database service'
    LICENSE = 'AGPLv3+'
    BROWSER = AllocineBrowser

    def get_movie(self, id):
        return self.browser.get_movie(id)

    def get_person(self, id):
        return self.browser.get_person(id)

    def iter_movies(self, pattern):
        return self.browser.iter_movies(quote_plus(pattern.encode('utf-8')))

    def iter_persons(self, pattern):
        return self.browser.iter_persons(quote_plus(pattern.encode('utf-8')))

    def iter_movie_persons(self, id, role=None):
        return self.browser.iter_movie_persons(id, role)

    def iter_person_movies(self, id, role=None):
        return self.browser.iter_person_movies(id, role)

    def iter_person_movies_ids(self, id):
        return self.browser.iter_person_movies_ids(id)

    def iter_movie_persons_ids(self, id):
        return self.browser.iter_movie_persons_ids(id)

    def get_person_biography(self, id):
        return self.browser.get_person_biography(id)

    def get_movie_releases(self, id, country=None):
        return self.browser.get_movie_releases(id, country)

    def fill_person(self, person, fields):
        if 'real_name' in fields or 'birth_place' in fields\
            or 'death_date' in fields or 'nationality' in fields\
            or 'short_biography' in fields or 'roles' in fields\
            or 'birth_date' in fields or 'thumbnail_url' in fields\
            or 'biography' in fields\
                or 'gender' in fields or fields is None:
            per = self.get_person(person.id)
            person.real_name = per.real_name
            person.birth_date = per.birth_date
            person.death_date = per.death_date
            person.birth_place = per.birth_place
            person.gender = per.gender
            person.nationality = per.nationality
            person.short_biography = per.short_biography
            person.short_description = per.short_description
            person.roles = per.roles
            person.biography = per.biography
            person.thumbnail_url = per.thumbnail_url

        return person

    def fill_movie(self, movie, fields):
        if 'other_titles' in fields or 'release_date' in fields\
            or 'duration' in fields or 'country' in fields\
            or 'roles' in fields or 'note' in fields\
                or 'thumbnail_url' in fields:
            mov = self.get_movie(movie.id)
            movie.other_titles = mov.other_titles
            movie.release_date = mov.release_date
            movie.duration = mov.duration
            movie.pitch = mov.pitch
            movie.country = mov.country
            movie.note = mov.note
            movie.roles = mov.roles
            movie.genres = mov.genres
            movie.short_description = mov.short_description
            movie.thumbnail_url = mov.thumbnail_url

        if 'all_release_dates' in fields:
            movie.all_release_dates = self.get_movie_releases(movie.id)

        return movie

    OBJECTS = {
        Person: fill_person,
        Movie: fill_movie
    }
