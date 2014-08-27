# -*- coding: utf-8 -*-

# Copyright(C) 2012-2014 Florent Fourcot
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


import calendar
from StringIO import StringIO
import lxml.html as html
from datetime import datetime
from decimal import Decimal

from weboob.tools.browser2.page import HTMLPage, method, LoggedPage
from weboob.tools.browser2.elements import ItemElement, ListElement
from weboob.tools.browser2.filters import Date, CleanText, Attr, Filter,\
    CleanDecimal, Regexp, Field, DateTime, Format, Env
from weboob.capabilities.bill import Detail, Bill


__all__ = ['HistoryPage', 'DetailsPage', 'BadUTF8Page']


class FormatDate(Filter):
    def filter(self, txt):
        return datetime.strptime(txt, "%Y%m%d").date()


class BadUTF8Page(HTMLPage):
    def __init__(self, browser, response, *args, **kwargs):
        super(HTMLPage, self).__init__(browser, response, *args, **kwargs)
        parser = html.HTMLParser(encoding='UTF-8')
        self.doc = html.parse(StringIO(response.content), parser)


class DetailsPage(LoggedPage, BadUTF8Page):
    def load_virtual(self, phonenumber):
        for div in self.doc.xpath('//div[@class="infosLigne pointer"]'):
            if CleanText('.')(div).split("-")[-1].strip() == phonenumber:
                return Attr('.', 'onclick')(div).split('(')[1][1]

    def on_load(self):
        self.details = {}
        for div in self.doc.xpath('//div[@class="infosConso"]'):
            num = div.attrib['id'].split('_')[1][0]
            self.details[num] = []

            # National parsing
            divnat = div.xpath('div[@class="national"]')[0]
            self._parse_div(divnat, "National : %s | International : %s", num, False)

            # International parsing
            divint = div.xpath('div[@class="international hide"]')[0]
            if divint.xpath('div[@class="detail"]'):
                self._parse_div(divint, u"Appels émis : %s | Appels reçus : %s", num, True)

    def _parse_div(self, divglobal, string, num, inter=False):
        divs = divglobal.xpath('div[@class="detail"]')
        # Two pieces of information in one div...
        div = divs.pop(0)
        voice = self._parse_voice(div, string, num, inter)
        self.details[num].append(voice)
        self._iter_divs(divs, num, inter)

    def _iter_divs(self, divs, num, inter=False):
        for div in divs:
            detail = Detail()
            detail.label = CleanText('div[@class="titre"]/p')(div)
            detail.id = "-" + detail.label.split(' ')[1].lower()
            if inter:
                detail.label = detail.label + u" (international)"
                detail.id = detail.id + "-inter"
            detail.infos = CleanText('div[@class="conso"]/p')(div)
            detail.price = CleanDecimal('div[@class="horsForfait"]/p/span', default=Decimal(0), replace_dots=True)(div)

            self.details[num].append(detail)

    def _parse_voice(self, div, string, num, inter=False):
        voicediv = div.xpath('div[@class="conso"]')[0]
        voice = Detail()
        voice.id = "-voice"
        voice.label = CleanText('div[@class="titre"]/p')(div)
        if inter:
            voice.label = voice.label + " (international)"
            voice.id = voice.id + "-inter"
        voice.price = CleanDecimal('div[@class="horsForfait"]/p/span', default=Decimal(0), replace_dots=True)(div)
        voice1 = CleanText('.//span[@class="actif"][1]')(voicediv)
        voice2 = CleanText('.//span[@class="actif"][2]')(voicediv)
        voice.infos = unicode(string) % (voice1, voice2)

        return voice

    # XXX
    def get_details(self, subscription):
        for detail in self.details[subscription._virtual]:
            detail.id = subscription.id + detail.id
            yield detail

    @method
    class date_bills(ListElement):
        item_xpath = '//div[@class="factLigne hide "]'

        class item(ItemElement):
            klass = Bill

            obj__url = Attr('.//div[@class="pdf"]/a', 'href')
            obj__localid = Regexp(Field('_url'), '&l=(\d*)&id', u'\\1')
            obj_label = Regexp(Field('_url'), '&date=(\d*)$', u'\\1')
            obj_id = Format('%s.%s', Env('subid'), Field('label'))
            obj_date = FormatDate(Field('label'))
            obj_format = u"pdf"
            obj_price = CleanDecimal('div[@class="montant"]', default=Decimal(0), replace_dots=False)

    def get_renew_date(self, subscription):
        div = self.doc.xpath('//div[@login="%s"]' % subscription._login)[0]
        mydate = Date(CleanText('//div[@class="resumeConso"]/span[@class="actif"][1]'), dayfirst=True)(div)
        if mydate.month == 12:
            mydate = mydate.replace(month=1)
            mydate = mydate.replace(year=mydate.year + 1)
        else:
            try:
                mydate = mydate.replace(month=mydate.month + 1)
            except ValueError:
                lastday = calendar.monthrange(mydate.year, mydate.month + 1)[1]
                mydate = mydate.replace(month=mydate.month + 1, day=lastday)
        return mydate


class HistoryPage(LoggedPage, BadUTF8Page):
    @method
    class get_calls(ListElement):
        item_xpath = '//tr'

        class item(ItemElement):
            klass = Detail

            def condition(self):
                txt = self.el.xpath('td[1]')[0].text
                return (txt is not None) and (txt != "Date")

            obj_id = None
            obj_datetime = DateTime(CleanText('td[1]', symbols=u'à'), dayfirst=True)
            obj_label = Format(u'%s %s %s', CleanText('td[2]'), CleanText('td[3]'),
                               CleanText('td[4]'))
            obj_price = CleanDecimal('td[5]', default=Decimal(0), replace_dots=True)
