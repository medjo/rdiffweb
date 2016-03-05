#!/usr/bin/python
# -*- coding: utf-8 -*-
# rdiffweb, A web interface to rdiff-backup repositories
# Copyright (C) 2014 rdiffweb contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import absolute_import
from __future__ import unicode_literals

from builtins import bytes
from builtins import str
import cherrypy
from cherrypy._cperror import HTTPRedirect
import encodings
import logging

from rdiffweb import librdiff
from rdiffweb import page_main
from rdiffweb.exceptions import Warning
from rdiffweb.i18n import ugettext as _
from rdiffweb.rdw_helpers import unquote_url


# Define the logger
_logger = logging.getLogger(__name__)


class SettingsPage(page_main.MainPage):

    def _cp_dispatch(self, vpath):
        """Used to handle permalink URL.
        ref http://cherrypy.readthedocs.org/en/latest/advanced.html"""
        # Notice vpath contains bytes.
        if len(vpath) > 0:
            # /the/full/path/
            path = []
            while len(vpath) > 0:
                path.append(unquote_url(vpath.pop(0)))
            cherrypy.request.params['path'] = b"/".join(path)
            return self

        return vpath

    @cherrypy.expose
    def index(self, path=b"", **kwargs):
        assert isinstance(path, bytes)

        _logger.debug("repo settings [%r]", path)

        # Check user permissions
        repo_obj = self.validate_user_path(path)[0]

        # Check if any action to process.
        params = {}
        action = kwargs.get('action')
        if action:
            try:
                if action == "delete":
                    params.update(self._handle_delete(repo_obj, **kwargs))
                elif action == "set_encoding":
                    params.update(self._handle_set_encoding(repo_obj, **kwargs))
            except Warning as e:
                params['warning'] = str(e)

        # Get page data.
        params.update(self._get_parms_for_page(repo_obj))

        # Generate page.
        return self._compile_template("settings.html", **params)

    def _get_parms_for_page(self, repo_obj):
        assert isinstance(repo_obj, librdiff.RdiffRepo)

        current_encoding = repo_obj.get_encoding()
        current_encoding = encodings.normalize_encoding(current_encoding)

        return {
            'repo_name': repo_obj.display_name,
            'repo_path': repo_obj.path,
            'settings': True,
            'supported_encodings': self._get_encodings(),
            'current_encoding': current_encoding
        }

    def _get_encodings(self):
        """
        Return a complete list of valid encoding supported by current python.
        """
        return ["ascii", "big5", "big5hkscs", "cp037", "cp424", "cp437",
                "cp500", "cp720", "cp737", "cp775", "cp850", "cp852", "cp855",
                "cp856", "cp857", "cp858", "cp860", "cp861", "cp862", "cp863",
                "cp864", "cp865", "cp866", "cp869", "cp874", "cp875", "cp932",
                "cp949", "cp950", "cp1006", "cp1026", "cp1140", "cp1250",
                "cp1251", "cp1252", "cp1253", "cp1254", "cp1255", "cp1256",
                "cp1257", "cp1258", "euc_jp", "euc_jis_2004", "euc_jisx0213",
                "euc_kr", "gb2312", "gbk", "gb18030", "hz", "iso2022_jp",
                "iso2022_jp_1", "iso2022_jp_2", "iso2022_jp_2004",
                "iso2022_jp_3", "iso2022_jp_ext", "iso2022_kr", "latin_1",
                "iso8859_2", "iso8859_3", "iso8859_4", "iso8859_5",
                "iso8859_6", "iso8859_7", "iso8859_8", "iso8859_9",
                "iso8859_10", "iso8859_13", "iso8859_14", "iso8859_15",
                "iso8859_16", "johab", "koi8_r", "koi8_u", "mac_cyrillic",
                "mac_greek", "mac_iceland", "mac_latin2", "mac_roman",
                "mac_turkish", "ptcp154", "shift_jis", "shift_jis_2004",
                "shift_jisx0213", "utf_32", "utf_32_be", "utf_32_le",
                "utf_16", "utf_16_be", "utf_16_le", "utf_7", "utf_8",
                "utf_8_sig"]

    def _handle_delete(self, repo_obj, **kwargs):
        """
        Delete the repository.
        """
        # Validate the name
        confirm_name = kwargs.get('confirm_name')
        if confirm_name != repo_obj.display_name:
            raise Warning(_("confirmation doesn't matches"))

        # Update the repository encoding
        _logger.info("deleting repository [%s]", repo_obj)
        repo_obj.delete()

        # Refresh repository list
        username = self.app.currentuser.username
        repos = self.app.userdb.get_repos(username)
        # Remove the repository. Depending of rdiffweb, the name may contains '/'.
        for r in [repo_obj.path, b"/" + repo_obj.path, repo_obj.path + b"/", b"/" + repo_obj.path + b"/"]:
            if r in repos:
                repos.remove(r)
        self.app.userdb.set_repos(username, repos)

        raise HTTPRedirect("/")

    def _handle_set_encoding(self, repo_obj, **kwargs):
        """
        Change the encoding of the repository.
        """
        # Validate the encoding value
        new_encoding = kwargs.get('encoding')
        new_codec = encodings.search_function(new_encoding.lower())
        if not new_codec:
            raise cherrypy.HTTPError(400, _("invalid encoding value"))

        new_encoding = new_codec.name
        if not isinstance(new_encoding, str):
            # Python 2
            new_encoding = new_encoding.decode('ascii')

        # Update the repository encoding
        _logger.info("updating repository [%s] encoding [%s]", repo_obj, new_encoding)
        repo_obj.set_encoding(new_encoding)

        return {'success': _("Repository updated successfully with new encoding.")}
