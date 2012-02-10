# coding: utf-8
#
# Copyright 2010-2012 Alexandre Fiori
# based on the original Tornado by Facebook
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import cyclone.escape
from cyclone.web import RequestHandler

from twisted.internet import defer
from twisted.python import log

class JsonrpcRequestHandler(RequestHandler):
    def post(self, *args):
        self._auto_finish = False
        try:
            req = escape.json_decode(self.request.body)
            method = req["method"]
            assert isinstance(method, types.StringTypes), type(method)
            params = req["params"]
            assert isinstance(params, (types.ListType, types.TupleType)), type(params)
            jsonid = req["id"]
            assert isinstance(jsonid, types.IntType), type(jsonid)
        except Exception, e:
            log.err("Bad Request: %s" % str(e))
            raise HTTPError(400)

        function = getattr(self, "jsonrpc_%s" % method, None)
        if callable(function):
            args = list(args) + params
            d = defer.maybeDeferred(function, *args)
            d.addBoth(self._cbResult, jsonid)
        else:
            self._cbResult(AttributeError("method not found: %s" % method), jsonid)

    def _cbResult(self, result, jsonid):
        if isinstance(result, failure.Failure):
            error = str(result.value)
            result = None
        else:
            error = None
        json_data = escape.json_encode({"result":result, "error":error, "id":jsonid})
        self.finish(json_data)
