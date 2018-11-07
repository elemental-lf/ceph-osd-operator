# Copyright (c) 2018 Lars Fenneberg <lf@elemental.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

from six import raise_from
from ansible import errors
from ansible.plugins.lookup import LookupBase
from ansible.utils.listify import listify_lookup_plugin_terms
import hashlib
import json

class LookupModule(LookupBase):

    _CHARSET = 'utf-8'
    _HASH_ALGORITHM = 'sha512'

    def run(self, terms, variables, **kwargs):
        ret = []
        for term in terms:
            hash = hashlib.new(self._HASH_ALGORITHM)
            hash.update(json.dumps(term, separators=(',', ':'), sort_keys=True).encode(self._CHARSET))
            ret.append(hash.hexdigest())
        return ret
