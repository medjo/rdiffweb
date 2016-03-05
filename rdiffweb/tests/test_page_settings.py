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
"""
Created on Jan 1, 2016

@author: ikus060
"""
from __future__ import unicode_literals

import logging
import unittest

from rdiffweb.test import WebCase


class SettingsTest(WebCase):

    login = True

    reset_app = True

    reset_testcases = True

    def _settings(self, repo):
        self.getPage("/settings/" + repo + "/")

    def _set_encoding(self, repo, encoding):
        self.getPage("/settings/" + repo + "/", method="POST",
                     body={'action': 'set_encoding', 'encoding': encoding})

    def _delete(self, repo, confirm_name):
        self.getPage("/settings/" + repo + "/", method="POST",
                     body={'action': 'delete', 'confirm_name': confirm_name})

    def test_check_encoding(self):
        self._settings(self.REPO)
        self.assertInBody("Character encoding")
        self.assertInBody("utf_8")

    def test_set_encoding(self):
        """
        Check to update the encoding.
        """
        self._set_encoding(self.REPO, 'cp1252')
        self.assertInBody("cp1252")

    def test_set_encoding_invalid(self):
        """
        Check to update the encoding.
        """
        self._set_encoding(self.REPO, 'invalid')
        self.assertStatus(400)
        self.assertInBody("invalid encoding value")

    def test_set_encoding_windows_1252(self):
        """
        Check to update the encoding.
        """
        self._set_encoding(self.REPO, 'windows_1252')
        self.assertStatus(200)
        self.assertInBody("cp1252")

    def test_check_delete(self):
        self._settings(self.REPO)
        self.assertInBody("Delete")

    def test_delete(self):
        """
        Check to delete a repo.
        """
        self._delete(self.REPO, self.REPO)
        self.assertStatus(303)

    def test_delete_wrong_confirm(self):
        """
        Check failure to delete a repo with wrong confirmation.
        """
        self._delete(self.REPO, 'wrong')
        self.assertInBody("confirmation doesn&#39;t matches")

if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
