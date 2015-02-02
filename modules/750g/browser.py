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

from weboob.browser.exceptions import BrowserHTTPNotFound
from weboob.browser import PagesBrowser, URL
from .pages import RecipePage, ResultsPage


__all__ = ['SevenFiftyGramsBrowser']


class SevenFiftyGramsBrowser(PagesBrowser):
    BASEURL = 'http://www.750g.com/'

    search = URL('recettes_(?P<pattern>.*).htm', ResultsPage)
    recipe = URL('(?P<id>.*).htm', RecipePage)

    def iter_recipes(self, pattern):
        return self.search.go(pattern=pattern.replace(' ', '_')).iter_recipes()

    def get_recipe(self, id, recipe=None):
        try:
            recipe = self.recipe.go(id=id).get_recipe(obj=recipe)
            comments = list(self.page.get_comments())
            if comments:
                recipe.comments = comments
            return recipe
        except BrowserHTTPNotFound:
            return
