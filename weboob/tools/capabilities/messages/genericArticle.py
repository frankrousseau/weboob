# -*- coding: utf-8 -*-

# Copyright(C) 2011  Julien Hebert
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

from weboob.tools.browser import BasePage
from weboob.tools.browser import BrokenPageError
from lxml.etree import Comment


def try_remove(parser, base_element, selector):
    try:
        base_element.remove(parser.select(base_element, selector, 1))
    except (BrokenPageError, ValueError):
        pass


def try_drop_tree(parser, base_element, selector):
    for el in parser.select(base_element, selector):
        el.drop_tree()


def remove_from_selector_list(parser, base_element, selector_list):
    for selector in selector_list:
        base_element.remove(parser.select(base_element, selector, 1))


def try_remove_from_selector_list(parser, base_element, selector_list):
    for selector in selector_list:
        try_remove(parser, base_element, selector)


def drop_comments(base_element):
    for comment in base_element.getiterator(Comment):
        comment.drop_tree()

# Replace relative url in link and image with a complete url
# Arguments: the html element to clean, and the domain name (with http:// prefix)


def clean_relativ_urls(base_element, domain):
    for a in base_element.findall('.//a'):
        if "href" in a.attrib:
            if a.attrib["href"] and a.attrib["href"][0:7] != "http://" and a.attrib["href"][0:7] != "https://":
                a.attrib["href"] = domain + a.attrib["href"]
    for img in base_element.findall('.//img'):
        if img.attrib["src"][0:7] != "http://" and img.attrib["src"][0:7] != "https://":
            img.attrib["src"] = domain + img.attrib["src"]


class NoAuthorElement(BrokenPageError):
    pass


class NoBodyElement(BrokenPageError):
    pass


class NoTitleException(BrokenPageError):
    pass


class NoneMainDiv(AttributeError):
    pass


class Article(object):
    author = u''
    title = u''

    def __init__(self, browser, _id):
        self.browser = browser
        self.id = _id
        self.body = u''
        self.url = u''
        self.date = None


class GenericNewsPage(BasePage):
    __element_body = NotImplementedError
    __article = Article
    element_title_selector = NotImplementedError
    main_div = NotImplementedError
    element_body_selector = NotImplementedError
    element_author_selector = NotImplementedError

    def get_body(self):
        return self.parser.tostring(self.get_element_body())

    def get_author(self):
        try:
            return u'%s' % self.get_element_author().text_content().strip()
        except (NoAuthorElement, NoneMainDiv):
            #TODO: Mettre un warning
            return self.__article.author

    def get_title(self):
        try:
            return u'%s' % self.parser.select(
                self.main_div,
                self.element_title_selector,
                1).text_content().strip()
        except AttributeError:
            if self.main_div is None:
                #TODO: Mettre un warning
                return self.__article.title
            else:
                raise
        except BrokenPageError:
            if self.element_title_selector == 'h1':
                raise NoTitleException("no title on %s" % (self.browser))
            self.element_title_selector = "h1"
            return self.get_title()

    def get_element_body(self):
        try:
            return self.parser.select(self.main_div, self.element_body_selector, 1)
        except BrokenPageError:
            raise NoBodyElement("no body on %s" % (self.browser))
        except AttributeError:
            if self.main_div is None:
                raise NoneMainDiv("main_div is none on %s" % (self.browser))
            else:
                raise

    def get_element_author(self):
        try:
            return self.parser.select(self.main_div, self.element_author_selector, 1)
        except BrokenPageError:
            raise NoAuthorElement()
        except AttributeError:
            if self.main_div is None:
                raise NoneMainDiv("main_div is none on %s" % (self.browser))
            else:
                raise

    def get_article(self, _id):
        __article = Article(self.browser, _id)
        __article.author = self.get_author()
        __article.title  = self.get_title()
        __article.url    = self.url
        __article.body   = self.get_body()

        return __article
