# -*- coding: utf-8 -*-

# Copyright(C) 2010  Nicolas Duhamel
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.

from weboob.tools.browser import BasePage
from .video import CanalplusVideo


__all__ = ['SearchResultPage']

class SearchResultPage(BasePage):
	def iter_results(self):
		for vid in self.document.getchildren():
			#id
			_id = vid[0].text
			#Titre
			titre = vid[2][9][0].text
			#Sous titre
			titre = titre + " " + vid[2][9][1].text
			yield CanalplusVideo(_id, title=titre)
