# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2018 - 2022 Provincie Zuid-Holland

from flask.testing import FlaskClient


class LoggedInClient(FlaskClient):
    def __init__(self, *args, **kwargs):
        self._gebruiker = kwargs.pop("gebruiker")
        self._access_token = kwargs.pop("access_token")
        super(LoggedInClient, self).__init__(*args, **kwargs)

    def get(self, *args, **kwargs):
        kwargs["headers"] = kwargs.get("headers", {})
        kwargs["headers"]["Authorization"] = f"Bearer {self._access_token}"

        return super(LoggedInClient, self).get(*args, **kwargs)

    def post(self, *args, **kwargs):
        kwargs["headers"] = kwargs.get("headers", {})
        kwargs["headers"]["Authorization"] = f"Bearer {self._access_token}"

        return super(LoggedInClient, self).post(*args, **kwargs)

    def put(self, *args, **kwargs):
        kwargs["headers"] = kwargs.get("headers", {})
        kwargs["headers"]["Authorization"] = f"Bearer {self._access_token}"

        return super(LoggedInClient, self).put(*args, **kwargs)

    def delete(self, *args, **kwargs):
        kwargs["headers"] = kwargs.get("headers", {})
        kwargs["headers"]["Authorization"] = f"Bearer {self._access_token}"

        return super(LoggedInClient, self).delete(*args, **kwargs)

    def patch(self, *args, **kwargs):
        kwargs["headers"] = kwargs.get("headers", {})
        kwargs["headers"]["Authorization"] = f"Bearer {self._access_token}"

        return super(LoggedInClient, self).patch(*args, **kwargs)

    def options(self, *args, **kwargs):
        kwargs["headers"] = kwargs.get("headers", {})
        kwargs["headers"]["Authorization"] = f"Bearer {self._access_token}"

        return super(LoggedInClient, self).options(*args, **kwargs)

    def head(self, *args, **kwargs):
        kwargs["headers"] = kwargs.get("headers", {})
        kwargs["headers"]["Authorization"] = f"Bearer {self._access_token}"

        return super(LoggedInClient, self).head(*args, **kwargs)

    def gebruiker(self):
        return self._gebruiker
    
    def uuid(self):
        return self._gebruiker.UUID
