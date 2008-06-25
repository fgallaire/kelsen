#
# Copyright (C) 2006  Robey Pointer <robey@lag.net>
# Copyright (C) 2006  Goffredo Baroncelli <kreijack@inwind.it>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

import time

from paste.request import path_info_pop, parse_querystring

from loggerhead import util
from loggerhead.templatefunctions import templatefunctions
from loggerhead.zptsupport import load_template

class TemplatedBranchView(object):

    template_path = None

    def __init__(self, branch):
        self._branch = branch
        self.log = branch.log

    def default(self, environ, start_response):
        z = time.time()
        h = self._branch.history
        kw = dict(parse_querystring(environ))
        util.set_context(kw)

        h._branch.lock_read()
        try:
            args = []
            while 1:
                arg = path_info_pop(environ)
                if arg is None:
                    break
                args.append(arg)

            vals = {
                'branch': self._branch,
                'util': util,
                'history': h,
                'url': self._branch.context_url,
            }
            vals.update(templatefunctions)
            headers = {}
            vals.update(self.get_values(h, args, kw, headers))

            self.log.info('Getting information for %s: %r secs' % (
                self.__class__.__name__, time.time() - z,))
            if 'Content-Type' not in headers:
                headers['Content-Type'] = 'text/html'
            writer = start_response("200 OK", headers.items())
            template = load_template(self.template_path)
            z = time.time()
            class W:
                def __init__(self):
                    self.bytes = 0
                def write(self, data):
                    self.bytes += len(data)
                    writer(data)
            w = W()
            template.expand_into(w, **vals)
            self.log.info('Rendering %s: %r secs, %s bytes' % (
                self.__class__.__name__, time.time() - z, w.bytes))
            return []
        finally:
            h._branch.unlock()

