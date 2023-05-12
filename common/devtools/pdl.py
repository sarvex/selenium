# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from __future__ import print_function
import collections
import json
import re
import sys

description = ''


primitiveTypes = ['integer', 'number', 'boolean', 'string', 'object',
                  'any', 'array', 'binary']


def assignType(item, type, is_array=False, map_binary_to_string=False):
    if is_array:
        item['type'] = 'array'
        item['items'] = collections.OrderedDict()
        assignType(item['items'], type, False, map_binary_to_string)
        return

    if type == 'enum':
        type = 'string'
    if map_binary_to_string and type == 'binary':
        type = 'string'
    if type in primitiveTypes:
        item['type'] = type
    else:
        item['$ref'] = type


def createItem(d, experimental, deprecated, name=None):
    result = collections.OrderedDict(d)
    if name:
        result['name'] = name
    global description
    if description:
        result['description'] = description.strip()
    if experimental:
        result['experimental'] = True
    if deprecated:
        result['deprecated'] = True
    return result


def parse(data, file_name, map_binary_to_string=False):
    protocol = collections.OrderedDict()
    protocol['version'] = collections.OrderedDict()
    protocol['domains'] = []
    domain = None
    item = None
    subitems = None
    nukeDescription = False
    global description
    lines = data.split('\n')
    for i in range(0, len(lines)):
        if nukeDescription:
            description = ''
            nukeDescription = False
        line = lines[i]
        trimLine = line.strip()

        if trimLine.startswith('#'):
            if len(description):
                description += '\n'
            description += trimLine[2:]
            continue
        else:
            nukeDescription = True

        if len(trimLine) == 0:
            continue

        match = re.compile(
            r'^(experimental )?(deprecated )?domain (.*)').match(line)
        if match:
            domain = createItem({'domain': match[3]}, match[1], match[2])
            protocol['domains'].append(domain)
            continue

        match = re.compile(r'^  depends on ([^\s]+)').match(line)
        if match:
            if 'dependencies' not in domain:
                domain['dependencies'] = []
            domain['dependencies'].append(match[1])
            continue

        match = re.compile(r'^  (experimental )?(deprecated )?type (.*) '
                           r'extends (array of )?([^\s]+)').match(line)
        if match:
            if 'types' not in domain:
                domain['types'] = []
            item = createItem({'id': match[3]}, match[1], match[2])
            assignType(item, match[5], match[4], map_binary_to_string)
            domain['types'].append(item)
            continue

        match = re.compile(
            r'^  (experimental )?(deprecated )?(command|event) (.*)').match(line)
        if match:
            list = []
            if match[3] == 'command':
                if 'commands' in domain:
                    list = domain['commands']
                else:
                    list = domain['commands'] = []
            elif 'events' in domain:
                list = domain['events']
            else:
                list = domain['events'] = []

            item = createItem({}, match[1], match[2], match[4])
            list.append(item)
            continue

        match = re.compile(
            r'^      (experimental )?(deprecated )?(optional )?'
            r'(array of )?([^\s]+) ([^\s]+)').match(line)
        if match:
            param = createItem({}, match[1], match[2], match[6])
            if match[3]:
                param['optional'] = True
            assignType(param, match[5], match[4], map_binary_to_string)
            if match[5] == 'enum':
                enumliterals = param['enum'] = []
            subitems.append(param)
            continue

        match = re.compile(r'^    (parameters|returns|properties)').match(line)
        if match:
            subitems = item[match[1]] = []
            continue

        match = re.compile(r'^    enum').match(line)
        if match:
            enumliterals = item['enum'] = []
            continue

        match = re.compile(r'^version').match(line)
        if match:
            continue

        if match := re.compile(r'^  major (\d+)').match(line):
            protocol['version']['major'] = match[1]
            continue

        if match := re.compile(r'^  minor (\d+)').match(line):
            protocol['version']['minor'] = match[1]
            continue

        if match := re.compile(r'^    redirect ([^\s]+)').match(line):
            item['redirect'] = match[1]
            continue

        if match := re.compile(r'^      (  )?[^\s]+$').match(line):
            # enum literal
            enumliterals.append(trimLine)
            continue

        print('Error in %s:%s, illegal token: \t%s' % (file_name, i, line))
        sys.exit(1)
    return protocol


def loads(data, file_name, map_binary_to_string=False):
    if file_name.endswith(".pdl"):
        return parse(data, file_name, map_binary_to_string)
    return json.loads(data)
