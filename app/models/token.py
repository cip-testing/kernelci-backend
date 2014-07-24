# Copyright (C) 2014 Linaro Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""The API token class to store token in the DB."""

TOKEN_COLLECTION = 'api-token'


class APIToken(object):

    def __init__(self):
        self._token = None
        self._created = None
        self._expires = None
        self._expired = False
        self._username = None
        self._email = None
        self._properties = []

    @property
    def token(self):
        return self._token

    @token.setter
    def token(self, value):
        self._token = value
