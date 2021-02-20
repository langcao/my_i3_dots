#!/usr/bin/env python

### This program is free software; you can redistribute it and/or
### modify it under the terms of the GNU General Public License
### as published by the Free Software Foundation; either version 2
### of the License, or (at your option) any later version.
###
### This program is distributed in the hope that it will be useful,
### but WITHOUT ANY WARRANTY; without even the implied warranty of
### MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
### GNU General Public License for more details.
###
### You should have received a copy of the GNU General Public License
### along with this program; if not, write to the Free Software
### Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

### Copyright 2004-2019 Dag Wieers <dag@wieers.com>

from __future__ import absolute_import, division, generators, print_function
__metaclass__ = type

import collections
import fnmatch
import getopt
import getpass
import glob
import linecache
import os
import re
import resource
import sched
import six
import sys
import time
import copy

VERSION = '0.8.0'

theme = { 'default': '' }

if sys.version_info < (2, 2):
    sys.exit('error: Python 2.2 or later required')

pluginpath = [
    os.path.expanduser('~/.dstat/'),                                # home + /.dstat/
    os.path.abspath(os.path.dirname(sys.argv[0])) + '/plugins/',    # binary path + /plugins/
    '/usr/share/dstat/',
    '/usr/local/share/dstat/',
]

class Options:
    def __init__(self, args):
        self.args = args
        self.bits = False
        self.blackonwhite = False
        self.count = -1
        self.cpulist = None
        self.debug = 0
        self.delay = 1
        self.disklist = None
        self.full = False
        self.float = False
        self.integer = False
        self.intlist = None
        self.netlist = None
        self.swaplist = None
        self.color = None
        self.update = True
        self.header = True
        self.output = False
        self.pidfile = False
        self.profile = ''

        ### List of available plugins
        allplugins = listplugins()

        ### List of plugins to show
        self.plugins = []

        ### Implicit if no terminal is used
        if not sys.stdout.isatty():
            self.color = False
            self.header = False
            self.update = False

        ### Temporary hardcoded for my own project
        self.diskset = {
            'local': ('sda', 'hd[a-d]'),
            'lores': ('sd[b-k]', 'sd[v-z]', 'sda[a-e]'),
            'hires': ('sd[l-u]', 'sda[f-o]'),
        }

        try:
            opts, args = getopt.getopt(args, 'acdfghilmno:prstTvyC:D:I:M:N:S:V',
                ['all', 'all-plugins', 'bits', 'bw', 'black-on-white', 'color',
                 'debug', 'filesystem', 'float', 'full', 'help', 'integer',
                 'list', 'mods', 'modules', 'nocolor', 'noheaders', 'noupdate',
                 'output=', 'pidfile=', 'profile', 'version', 'vmstat'] + allplugins)
        except getopt.error as exc:
            print('dstat: %s, try dstat -h for a list of all the options' % exc)
            sys.exit(1)

        for opt, arg in opts:
            if opt in ['-c']:
                self.plugins.append('cpu')
            elif opt in ['-C']:
                self.cpulist = arg.split(',')
            elif opt in ['-d']:
                self.plugins.append('disk')
            elif opt in ['-D']:
                self.disklist = arg.split(',')
            elif opt in ['--filesystem']:
                self.plugins.append('fs')
            elif opt in ['-g']:
                self.plugins.append('page')
            elif opt in ['-i']:
                self.plugins.append('int')
            elif opt in ['-I']:
                self.intlist = arg.split(',')
            elif opt in ['-l']:
                self.plugins.append('load')
            elif opt in ['-m']:
                self.plugins.append('mem')
            elif opt in ['-M', '--mods', '--modules']:
                print('WARNING: Option %s is deprecated, please use --%s instead' % (opt, ' --'.join(arg.split(','))), file=sys.stderr)
                self.plugins += arg.split(',')
            elif opt in ['-n']:
                self.plugins.append('net')
            elif opt in ['-N']:
                self.netlist = arg.split(',')
            elif opt in ['-p']:
                self.plugins.append('proc')
            elif opt in ['-r']:
                self.plugins.append('io')
            elif opt in ['-s']:
                self.plugins.append('swap')
            elif opt in ['-S']:
                self.swaplist = arg.split(',')
            elif opt in ['-t']:
                self.plugins.append('time')
            elif opt in ['-T']:
                self.plugins.append('epoch')
            elif opt in ['-y']:
                self.plugins.append('sys')

            elif opt in ['-a', '--all']:
                self.plugins += [ 'cpu', 'disk', 'net', 'page', 'sys' ]
            elif opt in ['-v', '--vmstat']:
                self.plugins += [ 'proc', 'mem', 'page', 'disk', 'sys', 'cpu' ]
            elif opt in ['-f', '--full']:
                self.full = True

            elif opt in ['--all-plugins']:
                ### Make list unique in a fancy fast way
                plugins = list({}.fromkeys(allplugins).keys())
                plugins.sort()
                self.plugins += plugins
            elif opt in ['--bits']:
                self.bits = True
            elif opt in ['--bw', '--black-on-white', '--blackonwhite']:
                self.blackonwhite = True
            elif opt in ['--color']:
                self.color = True
                self.update = True
            elif opt in ['--debug']:
                self.debug = self.debug + 1
            elif opt in ['--float']:
                self.float = True
            elif opt in ['--integer']:
                self.integer = True
            elif opt in ['--list']:
                showplugins()
                sys.exit(0)
            elif opt in ['--nocolor']:
                self.color = False
            elif opt in ['--noheaders']:
                self.header = False
            elif opt in ['--noupdate']:
                self.update = False
            elif opt in ['-o', '--output']:
                self.output = arg
            elif opt in ['--pidfile']:
                self.pidfile = arg
            elif opt in ['--profile']:
                self.profile = 'dstat_profile.log'
            elif opt in ['-h', '--help']:
                self.usage()
                self.help()
                sys.exit(0)
            elif opt in ['-V', '--version']:
                self.version()
                sys.exit(0)
            elif opt.startswith('--'):
                self.plugins.append(opt[2:])
            else:
                print('dstat: option %s unknown to getopt, try dstat -h for a list of all the options' % opt)
                sys.exit(1)

        if self.float and self.integer:
            print('dstat: option --float and --integer are mutual exclusive, you can only force one')
            sys.exit(1)

        if not self.plugins:
            print('You did not select any stats, using -cdngy by default.')
            self.plugins = [ 'cpu', 'disk', 'net', 'page', 'sys' ]

        try:
            if len(args) > 0: self.delay = int(args[0])
            if len(args) > 1: self.count = int(args[1])
        except:
            print('dstat: incorrect argument, try dstat -h for the correct syntax')
            sys.exit(1)

        if self.delay <= 0:
            print('dstat: delay must be an integer, greater than zero')
            sys.exit(1)

        if self.debug:
            print('Plugins: %s' % self.plugins)

    def version(self):
        print('Dstat %s' % VERSION)
        print('Written by Dag Wieers <dag@wieers.com>')
        print('Homepage at http://dag.wieers.com/home-made/dstat/')
        print()
        print('Platform %s/%s' % (os.name, sys.platform))
        print('Kernel %s' % os.uname()[2])
        print('Python %s' % sys.version)
        print()

        color = ""
        if not gettermcolor():
            color = "no "
        print('Terminal type: %s (%scolor support)' % (os.getenv('TERM'), color))
        rows, cols = gettermsize()
        print('Terminal size: %d lines, %d columns' % (rows, cols))
        print()
        print('Processors: %d' % getcpunr())
        print('Pagesize: %d' % resource.getpagesize())
        print('Clock ticks per secs: %d' % os.sysconf('SC_CLK_TCK'))
        print()

        global op
        op = self
        showplugins()

    def usage(self):
        print('Usage: dstat [-afv] [options..] [delay [count]]')

    def help(self):
        print('''Versatile tool for generating system resource statistics)
Dstat options:
  -c, --cpu                enable cpu stats
     -C 0,3,total             include cpu0, cpu3 and total
  -d, --disk               enable disk stats
     -D total,hda             include hda and total
  -g, --page               enable page stats
  -i, --int                enable interrupt stats
     -I 5,eth2                include int5 and interrupt used by eth2
  -l, --load               enable load stats
  -m, --mem                enable memory stats
  -n, --net                enable network stats
     -N eth1,total            include eth1 and total
  -p, --proc               enable process stats
  -r, --io                 enable io stats (I/O requests completed)
  -s, --swap               enable swap stats
     -S swap1,total           include swap1 and total
  -t, --time               enable time/date output
  -T, --epoch              enable time counter (seconds since epoch)
  -y, --sys                enable system stats
  --aio                    enable aio stats
  --fs, --filesystem       enable fs stats
  --ipc                    enable ipc stats
  --lock                   enable lock stats
  --raw                    enable raw stats
  --socket                 enable socket stats
  --tcp                    enable tcp stats
  --udp                    enable udp stats
  --unix                   enable unix stats
  --vm                     enable vm stats
  --vm-adv                 enable advanced vm stats
  --zones                  enable zoneinfo stats
  --list                   list all available plugins
  --<plugin-name>          enable external plugin by name (see --list)
  -a, --all                equals -cdngy (default)
  -f, --full               automatically expand -C, -D, -I, -N and -S lists
  -v, --vmstat             equals -pmgdsc -D total
  --bits                   force bits for values expressed in bytes
  --float                  force float values on screen
  --integer                force integer values on screen
  --bw, --black-on-white   change colors for white background terminal
  --color                  force colors
  --nocolor                disable colors
  --noheaders              disable repetitive headers
  --noupdate               disable intermediate updates
  --output file            write CSV output to file
  --profile                show profiling statistics when exiting dstat
delay is the delay in seconds between each update (default: 1)
count is the number of updates to display before exiting (default: unlimited)
''')

### START STATS DEFINITIONS ###
class dstat:
    vars = None
    name = None
    nick = None
    type = 'f'
    types = ()
    width = 5
    scale = 1024
    scales = ()
    cols = 0
    struct = None
#    val = {}
#    set1 = {}
#    set2 = {}

    def prepare(self):
        if callable(self.discover):
            self.discover = self.discover()
        if callable(self.vars):
            self.vars = self.vars()
        if not self.vars:
            raise Exception('No counter objects to monitor')
        if callable(self.name):
            self.name = self.name()
        if callable(self.nick):
            self.nick = self.nick()
        if not self.nick:
            self.nick = self.vars

        self.val = {}; self.set1 = {}; self.set2 = {}
        if self.struct: ### Plugin API version 2
            for name in self.vars + [ 'total', ]:
                self.val[name] = self.struct
                self.set1[name] = self.struct
                self.set2[name] = {}
        elif self.cols <= 0: ### Plugin API version 1
            for name in self.vars:
                self.val[name] = self.set1[name] = self.set2[name] = 0
        else: ### Plugin API version 1
            for name in self.vars + [ 'total', ]:
                self.val[name] = list(range(self.cols))
                self.set1[name] = list(range(self.cols))
                self.set2[name] = list(range(self.cols))
                for i in list(range(self.cols)):
                    self.val[name][i] = self.set1[name][i] = self.set2[name][i] = 0
#        print(self.val)

    def open(self, *filenames):
        "Open stat file descriptor"
        self.file = []
        self.fd = []
        for filename in filenames:
            try:
                fd = dopen(filename)
                if fd:
                    self.file.append(filename)
                    self.fd.append(fd)
            except:
                pass
        if not self.fd:
            raise Exception('Cannot open file %s' % filename)

    def readlines(self):
        "Return lines from any file descriptor"
        for fd in self.fd:
            fd.seek(0)
            for line in fd.readlines():
               yield line
        ### Implemented linecache (for top-plugins) but slows down normal plugins
#        for fd in self.fd:
#            i = 1
#            while True:
#                line = linecache.getline(fd.name, i);
#                if not line: break
#                yield line
#                i += 1

    def splitline(self, sep=None):
        for fd in self.fd:
            fd.seek(0)
            return fd.read().split(sep)

    def splitlines(self, sep=None, replace=None):
        "Return split lines from any file descriptor"
        for fd in self.fd:
            fd.seek(0)
            for line in fd.readlines():
                if replace and sep:
                    yield line.replace(replace, sep).split(sep)
                elif replace:
                    yield line.replace(replace, ' ').split()
                else:
                    yield line.split(sep)
#        ### Implemented linecache (for top-plugins) but slows down normal plugins
#        for fd in self.fd:
#                if replace and sep:
#                    yield line.replace(replace, sep).split(sep)
#                elif replace:
#                    yield line.replace(replace, ' ').split()
#                else:
#                    yield line.split(sep)
#                i += 1

    def statwidth(self):
        "Return complete stat width"
        if self.cols:
            return len(self.vars) * self.colwidth() + len(self.vars) - 1
        else:
            return len(self.nick) * self.colwidth() + len(self.nick) - 1

    def colwidth(self):
        "Return column width"
        if isinstance(self.name, six.string_types):
            return self.width
        else:
            return len(self.nick) * self.width + len(self.nick) - 1

    def title(self):
        ret = theme['title']
        if isinstance(self.name, six.string_types):
            width = self.statwidth()
            return ret + self.name[0:width].center(width).replace(' ', '-') + theme['default']
        for i, name in enumerate(self.name):
            width = self.colwidth()
            ret = ret + name[0:width].center(width).replace(' ', '-')
            if i + 1 != len(self.vars):
                if op.color:
                    ret = ret + theme['frame'] + char['dash'] + theme['title']
                else:
                    ret = ret + char['space']
        return ret

    def subtitle(self):
        ret = ''
        if isinstance(self.name, six.string_types):
            for i, nick in enumerate(self.nick):
                ret = ret + theme['subtitle'] + nick[0:self.width].center(self.width) + theme['default']
                if i + 1 != len(self.nick): ret = ret + char['space']
            return ret
        else:
            for i, name in enumerate(self.name):
                for j, nick in enumerate(self.nick):
                    ret = ret + theme['subtitle'] + nick[0:self.width].center(self.width) + theme['default']
                    if j + 1 != len(self.nick): ret = ret + char['space']
                if i + 1 != len(self.name): ret = ret + theme['frame'] + char['colon']
            return ret

    def csvtitle(self):
        if isinstance(self.name, six.string_types):
            return '"' + self.name + '"' + char['sep'] * (len(self.nick) - 1)
        else:
            ret = ''
            for i, name in enumerate(self.name):
                ret = ret + '"' + name + '"' + char['sep'] * (len(self.nick) - 1)
                if i + 1 != len(self.name): ret = ret + char['sep']
            return ret

    def csvsubtitle(self):
        ret = ''
        if isinstance(self.name, six.string_types):
            for i, nick in enumerate(self.nick):
                ret = ret + '"' + nick + '"'
                if i + 1 != len(self.nick): ret = ret + char['sep']
        elif len(self.name) == 1:
            for i, name in enumerate(self.name):
                for j, nick in enumerate(self.nick):
                    ret = ret + '"' + nick + '"'
                    if j + 1 != len(self.nick): ret = ret + char['sep']
                if i + 1 != len(self.name): ret = ret + char['sep']
        else:
            for i, name in enumerate(self.name):
                for j, nick in enumerate(self.nick):
                    ret = ret + '"' + name + ':' + nick + '"'
                    if j + 1 != len(self.nick): ret = ret + char['sep']
                if i + 1 != len(self.name): ret = ret + char['sep']
        return ret

    def check(self):
        "Check if stat is applicable"
#        if hasattr(self, 'fd') and not self.fd:
#            raise Exception, 'File %s does not exist' % self.fd
        if not self.vars:
            raise Exception('No objects found, no stats available')
        if not self.discover:
            raise Exception('No objects discovered, no stats available')
        if self.colwidth():
            return True
        raise Exception('Unknown problem, please report')

    def discover(self, *objlist):
        return True

    def show(self):
        "Display stat results"
        line = ''
        if hasattr(self, 'output'):
            return cprint(self.output, self.type, self.width, self.scale)
        for i, name in enumerate(self.vars):
            if i < len(self.types):
                ctype = self.types[i]
            else:
                ctype = self.type
            if i < len(self.scales):
                scale = self.scales[i]
            else:
                scale = self.scale
            if isinstance(self.val[name], collections.Sequence) and not isinstance(self.val[name], six.string_types):
                line = line + cprintlist(self.val[name], ctype, self.width, scale)
                sep = theme['frame'] + char['colon']
                if i + 1 != len(self.vars):
                    line = line + sep
            else:
                ### Make sure we don't show more values than we have nicknames
                if i >= len(self.nick): break
                line = line + cprint(self.val[name], ctype, self.width, scale)
                sep = char['space']
                if i + 1 != len(self.nick):
                    line = line + sep
        return line

    def showend(self, totlist, vislist):
        if vislist and self is not vislist[-1]:
            return theme['frame'] + char['pipe']
        elif totlist != vislist:
            return theme['frame'] + char['gt']
        return ''

    def showcsv(self):
        def printcsv(var):
            if var != round(var):
                return '%.3f' % var
            return '%d' % int(round(var))

        line = ''
        for i, name in enumerate(self.vars):
            if isinstance(self.val[name], types.ListType) or isinstance(self.val[name], types.TupleType):
                for j, val in enumerate(self.val[name]):
                    line = line + printcsv(val)
                    if j + 1 != len(self.val[name]):
                        line = line + char['sep']
            elif isinstance(self.val[name], types.StringType):
                line = line + self.val[name]
            else:
                line = line + printcsv(self.val[name])
            if i + 1 != len(self.vars):
                line = line + char['sep']
        return line

    def showcsvend(self, totlist, vislist):
        if vislist and self is not vislist[-1]:
            return char['sep']
        elif totlist and self is not totlist[-1]:
            return char['sep']
        return ''

class dstat_aio(dstat):
    def __init__(self):
        self.name = 'async'
        self.nick = ('#aio',)
        self.vars = ('aio',)
        self.type = 'd'
        self.width = 5;
        self.open('/proc/sys/fs/aio-nr')

    def extract(self):
        for l in self.splitlines():
            if len(l) < 1: continue
            self.val['aio'] = int(l[0])

class dstat_cpu(dstat):
    def __init__(self):
        self.nick = ( 'usr', 'sys', 'idl', 'wai', 'stl' )
        self.type = 'p'
        self.width = 3
        self.scale = 34
        self.open('/proc/stat')
        self.cols = 5

    def discover(self, *objlist):
        ret = []
        for l in self.splitlines():
            if len(l) < 9 or l[0][0:3] != 'cpu': continue
            ret.append(l[0][3:])
        ret.sort()
        for item in objlist: ret.append(item)
        return ret

    def vars(self):
        ret = []
        if op.cpulist and 'all' in op.cpulist:
            varlist = []
            cpu = 0
            while cpu < cpunr:
                varlist.append(str(cpu))
                cpu = cpu + 1
#           if len(varlist) > 2: varlist = varlist[0:2]
        elif op.cpulist:
            varlist = op.cpulist
        else:
            varlist = ('total',)
        for name in varlist:
            if name in self.discover + ['total']:
                ret.append(name)
        return ret

    def name(self):
        ret = []
        for name in self.vars:
            if name == 'total':
                ret.append('total cpu usage')
            else:
                ret.append('cpu' + name + ' usage')
        return ret

    def extract(self):
        for l in self.splitlines():
            if len(l) < 9: continue
            for name in self.vars:
                if l[0] == 'cpu' + name or ( l[0] == 'cpu' and name == 'total' ):
                    self.set2[name] = ( int(l[1]) + int(l[2]) + int(l[6]) + int(l[7]), int(l[3]), int(l[4]), int(l[5]), int(l[8]) )

        for name in self.vars:
            for i in list(range(self.cols)):
                if sum(self.set2[name]) > sum(self.set1[name]):
                    self.val[name][i] = 100.0 * (self.set2[name][i] - self.set1[name][i]) / (sum(self.set2[name]) - sum(self.set1[name]))
                else:
                    self.val[name][i] = 0
#                    print("Error: tick problem detected, this should never happen !", file=sys.stderr)

        if step == op.delay:
            self.set1.update(self.set2)

class dstat_cpu_use(dstat_cpu):
    def __init__(self):
        self.name = 'per cpu usage'
        self.type = 'p'
        self.width = 3
        self.scale = 34
        self.open('/proc/stat')
        self.cols = 7
        if not op.cpulist:
            self.vars = [ str(x) for x in list(range(cpunr)) ]

    def extract(self):
        for l in self.splitlines():
            if len(l) < 9: continue
            for name in self.vars:
                if l[0] == 'cpu' + name or ( l[0] == 'cpu' and name == 'total' ):
                    self.set2[name] = ( int(l[1]) + int(l[2]), int(l[3]), int(l[4]), int(l[5]), int(l[6]), int(l[7]), int(l[8]) )

        for name in self.vars:
            if sum(self.set2[name]) > sum(self.set1[name]):
                self.val[name] = 100.0 - 100.0 * (self.set2[name][2] - self.set1[name][2]) / (sum(self.set2[name]) - sum(self.set1[name]))
            else:
                self.val[name] = 0
#                    print("Error: tick problem detected, this should never happen !", file=sys.stderr)

        if step == op.delay:
            self.set1.update(self.set2)

class dstat_cpu_adv(dstat_cpu):
    def __init__(self):
        self.nick = ( 'usr', 'sys', 'idl', 'wai', 'hiq', 'siq', 'stl' )
        self.type = 'p'
        self.width = 3
        self.scale = 34
        self.open('/proc/stat')
        self.cols = 7

    def extract(self):
        for l in self.splitlines():
            if len(l) < 9: continue
            for name in self.vars:
                if l[0] == 'cpu' + name or ( l[0] == 'cpu' and name == 'total' ):
                    self.set2[name] = ( int(l[1]) + int(l[2]), int(l[3]), int(l[4]), int(l[5]), int(l[6]), int(l[7]), int(l[8]) )

        for name in self.vars:
            for i in list(range(self.cols)):
                if sum(self.set2[name]) > sum(self.set1[name]):
                    self.val[name][i] = 100.0 * (self.set2[name][i] - self.set1[name][i]) / (sum(self.set2[name]) - sum(self.set1[name]))
                else:
                    self.val[name][i] = 0
#                    print("Error: tick problem detected, this should never happen !", file=sys.stderr)

        if step == op.delay:
            self.set1.update(self.set2)

class dstat_cpu24(dstat):
    def __init__(self):
        self.nick = ( 'usr', 'sys', 'idl')
        self.type = 'p'
        self.width = 3
        self.scale = 34
        self.open('/proc/stat')
        self.cols = 3

    def discover(self, *objlist):
        ret = []
        for l in self.splitlines():
            if len(l) != 5 or l[0][0:3] != 'cpu': continue
            ret.append(l[0][3:])
        ret.sort()
        for item in objlist: ret.append(item)
        return ret

    def vars(self):
        ret = []
        if op.cpulist and 'all' in op.cpulist:
            varlist = []
            cpu = 0
            while cpu < cpunr:
                varlist.append(str(cpu))
                cpu = cpu + 1
#           if len(varlist) > 2: varlist = varlist[0:2]
        elif op.cpulist:
            varlist = op.cpulist
        else:
            varlist = ('total',)
        for name in varlist:
            if name in self.discover + ['total']:
                ret.append(name)
        return ret

    def name(self):
        ret = []
        for name in self.vars:
            if name == 'total':
                ret.append('cpu usage')
            else:
                ret.append('cpu' + name)
        return ret

    def extract(self):
        for l in self.splitlines():
            for name in self.vars:
                if l[0] == 'cpu' + name or ( l[0] == 'cpu' and name == 'total' ):
                    self.set2[name] = ( int(l[1]) + int(l[2]), int(l[3]), int(l[4]) )

        for name in self.vars:
            for i in list(range(self.cols)):
                self.val[name][i] = 100.0 * (self.set2[name][i] - self.set1[name][i]) / (sum(self.set2[name]) - sum(self.set1[name]))

        if step == op.delay:
            self.set1.update(self.set2)

class dstat_disk(dstat):
    def __init__(self):
        self.nick = ('read', 'writ')
        self.type = 'b'
        self.diskfilter = re.compile('^([hsv]d[a-z]+\d+|cciss/c\d+d\d+p\d+|dm-\d+|md\d+|mmcblk\d+p\d0|VxVM\d+)$')
        self.open('/proc/diskstats')
        self.cols = 2

    def discover(self, *objlist):
        ret = []
        for l in self.splitlines():
            if len(l) < 13: continue
            if l[3:] == ['0',] * 11: continue
            name = l[2]
            ret.append(name)
        for item in objlist: ret.append(item)
        if not ret:
            raise Exception("No suitable block devices found to monitor")
        return ret

    def basename(self, disk):
        "Strip /dev/ and convert symbolic link"
        if disk[:5] == '/dev/':
            # file or symlink
            if os.path.exists(disk):
                # e.g. /dev/disk/by-uuid/15e40cc5-85de-40ea-b8fb-cb3a2eaf872
                if os.path.islink(disk):
                    target = os.readlink(disk)
                    # convert relative pathname to absolute
                    if target[0] != '/':
                        target = os.path.join(os.path.dirname(disk), target)
                        target = os.path.normpath(target)
                    print('dstat: symlink %s -> %s' % (disk, target))
                    disk = target
                # trim leading /dev/
                return disk[5:]
            else:
                print('dstat: %s does not exist' % disk)
        else:
            return disk

    def vars(self):
        ret = []
        if op.disklist:
            varlist = list(map(self.basename, op.disklist))
        elif not op.full:
            varlist = ('total',)
        else:
            varlist = []
            for name in self.discover:
                if self.diskfilter.match(name): continue
                if name not in blockdevices(): continue
                varlist.append(name)
#           if len(varlist) > 2: varlist = varlist[0:2]
            varlist.sort()
        for name in varlist:
            if name in self.discover + ['total'] or name in op.diskset:
                ret.append(name)
        return ret

    def name(self):
        return ['dsk/'+sysfs_dev(name) for name in self.vars]

    def extract(self):
        for name in self.vars: self.set2[name] = (0, 0)
        for l in self.splitlines():
            if len(l) < 13: continue
            if l[5] == '0' and l[9] == '0': continue
            name = l[2]
            if l[3:] == ['0',] * 11: continue
            if not self.diskfilter.match(name):
                self.set2['total'] = ( self.set2['total'][0] + int(l[5]), self.set2['total'][1] + int(l[9]) )
            if name in self.vars and name != 'total':
                self.set2[name] = ( self.set2[name][0] + int(l[5]), self.set2[name][1] + int(l[9]) )
            for diskset in self.vars:
                if diskset in op.diskset:
                    for disk in op.diskset[diskset]:
                        if fnmatch.fnmatch(name, disk):
                            self.set2[diskset] = ( self.set2[diskset][0] + int(l[5]), self.set2[diskset][1] + int(l[9]) )

        for name in self.set2:
            self.val[name] = list(map(lambda x, y: (y - x) * 512.0 / elapsed, self.set1[name], self.set2[name]))

        if step == op.delay:
            self.set1.update(self.set2)

class dstat_disk24(dstat):
    def __init__(self):
        self.nick = ('read', 'writ')
        self.type = 'b'
        self.diskfilter = re.compile('^([hsv]d[a-z]+\d+|cciss/c\d+d\d+p\d+|dm-\d+|md\d+|mmcblk\d+p\d0|VxVM\d+)$')
        self.open('/proc/partitions')
        if self.fd and not self.discover:
            raise Exception('Kernel has no per-partition I/O accounting [CONFIG_BLK_STATS], use at least 2.4.20')
        self.cols = 2

    def discover(self, *objlist):
        ret = []
        for l in self.splitlines():
            if len(l) < 15 or l[0] == 'major' or int(l[1]) % 16 != 0: continue
            name = l[3]
            ret.append(name)
        for item in objlist: ret.append(item)
        if not ret:
            raise Exception("No suitable block devices found to monitor")
        return ret

    def basename(self, disk):
        "Strip /dev/ and convert symbolic link"
        if disk[:5] == '/dev/':
            # file or symlink
            if os.path.exists(disk):
                # e.g. /dev/disk/by-uuid/15e40cc5-85de-40ea-b8fb-cb3a2eaf872
                if os.path.islink(disk):
                    target = os.readlink(disk)
                    # convert relative pathname to absolute
                    if target[0] != '/':
                        target = os.path.join(os.path.dirname(disk), target)
                        target = os.path.normpath(target)
                    print('dstat: symlink %s -> %s' % (disk, target))
                    disk = target
                # trim leading /dev/
                return disk[5:]
            else:
                print('dstat: %s does not exist' % disk)
        else:
            return disk

    def vars(self):
        ret = []
        if op.disklist:
            varlist = list(map(self.basename, op.disklist))
        elif not op.full:
            varlist = ('total',)
        else:
            varlist = []
            for name in self.discover:
                if self.diskfilter.match(name): continue
                varlist.append(name)
#           if len(varlist) > 2: varlist = varlist[0:2]
            varlist.sort()
        for name in varlist:
            if name in self.discover + ['total'] or name in op.diskset:
                ret.append(name)
        return ret

    def name(self):
        return ['dsk/'+sysfs_dev(name) for name in self.vars]

    def extract(self):
        for name in self.vars: self.set2[name] = (0, 0)
        for l in self.splitlines():
            if len(l) < 15 or l[0] == 'major' or int(l[1]) % 16 != 0: continue
            name = l[3]
            if not self.diskfilter.match(name):
                self.set2['total'] = ( self.set2['total'][0] + int(l[6]), self.set2['total'][1] + int(l[10]) )
            if name in self.vars:
                self.set2[name] = ( self.set2[name][0] + int(l[6]), self.set2[name][1] + int(l[10]) )
            for diskset in self.vars:
                if diskset in op.diskset:
                    for disk in op.diskset[diskset]:
                        if fnmatch.fnmatch(name, disk):
                            self.set2[diskset] = ( self.set2[diskset][0] + int(l[6]), self.set2[diskset][1] + int(l[10]) )

        for name in self.set2:
            self.val[name] = list(map(lambda x, y: (y - x) * 512.0 / elapsed, self.set1[name], self.set2[name]))

        if step == op.delay:
            self.set1.update(self.set2)

### FIXME: Needs rework, does anyone care ?
class dstat_disk24_old(dstat):
    def __init__(self):
        self.nick = ('read', 'writ')
        self.type = 'b'
        self.diskfilter = re.compile('^([hsv]d[a-z]+\d+|cciss/c\d+d\d+p\d+|dm-\d+|md\d+|mmcblk\d+p\d0|VxVM\d+)$')
        self.regexp = re.compile('^\((\d+),(\d+)\):\(\d+,\d+,(\d+),\d+,(\d+)\)$')
        self.open('/proc/stat')
        self.cols = 2

    def discover(self, *objlist):
        ret = []
        for l in self.splitlines(':'):
            if len(l) < 3: continue
            name = l[0]
            if name != 'disk_io': continue
            for pair in line.split()[1:]:
                m = self.regexp.match(pair)
                if not m: continue
                l = m.groups()
                if len(l) < 4: continue
                name = dev(int(l[0]), int(l[1]))
                ret.append(name)
            break
        for item in objlist: ret.append(item)
        if not ret:
            raise Exception("No suitable block devices found to monitor")
        return ret

    def vars(self):
        ret = []
        if op.disklist:
            varlist = op.disklist
        elif not op.full:
            varlist = ('total',)
        else:
            varlist = []
            for name in self.discover:
                if self.diskfilter.match(name): continue
                varlist.append(name)
#           if len(varlist) > 2: varlist = varlist[0:2]
            varlist.sort()
        for name in varlist:
            if name in self.discover + ['total'] or name in op.diskset:
                ret.append(name)
        return ret

    def name(self):
        return ['dsk/'+name for name in self.vars]

    def extract(self):
        for name in self.vars: self.set2[name] = (0, 0)
        for line in self.splitlines(':'):
            if len(l) < 3: continue
            name = l[0]
            if name != 'disk_io': continue
            for pair in line.split()[1:]:
                m = self.regexp.match(pair)
                if not m: continue
                l = m.groups()
                if len(l) < 4: continue
                name = dev(int(l[0]), int(l[1]))
                if not self.diskfilter.match(name):
                    self.set2['total'] = ( self.set2['total'][0] + int(l[2]), self.set2['total'][1] + int(l[3]) )
                if name in self.vars and name != 'total':
                    self.set2[name] = ( self.set2[name][0] + int(l[2]), self.set2[name][1] + int(l[3]) )
                for diskset in self.vars:
                    if diskset in op.diskset:
                        for disk in op.diskset[diskset]:
                            if fnmatch.fnmatch(name, disk):
                                self.set2[diskset] = ( self.set2[diskset][0] + int(l[2]), self.set2[diskset][1] + int(l[3]) )
            break

        for name in self.set2:
            self.val[name] = list(map(lambda x, y: (y - x) * 512.0 / elapsed, self.set1[name], self.set2[name]))

        if step == op.delay:
            self.set1.update(self.set2)

class dstat_epoch(dstat):
    def __init__(self):
        self.name = 'epoch'
        self.vars = ('epoch',)
        self.width = 10
        if op.debug:
            self.width = 13
        self.scale = 0

    ### We are now using the starttime instead of the execution time of this plugin
    def extract(self):
#        self.val['epoch'] = time.time()
        self.val['epoch'] = starttime

class dstat_fs(dstat):
    def __init__(self):
        self.name = 'filesystem'
        self.vars = ('files', 'inodes')
        self.type = 'd'
        self.width = 6
        self.scale = 1000

    def extract(self):
        for line in dopen('/proc/sys/fs/file-nr'):
            l = line.split()
            if len(l) < 1: continue
            self.val['files'] = int(l[0])
        for line in dopen('/proc/sys/fs/inode-nr'):
            l = line.split()
            if len(l) < 2: continue
            self.val['inodes'] = int(l[0]) - int(l[1])

class dstat_int(dstat):
    def __init__(self):
        self.name = 'interrupts'
        self.type = 'd'
        self.width = 5
        self.scale = 1000
        self.open('/proc/stat')
        self.intmap = self.intmap()

    def intmap(self):
        ret = {}
        for line in dopen('/proc/interrupts'):
            l = line.split()
            if len(l) <= cpunr: continue
            l1 = l[0].split(':')[0]
            l2 = ' '.join(l[cpunr+2:]).split(',')
            ret[l1] = l1
            for name in l2:
                ret[name.strip().lower()] = l1
        return ret

    def discover(self, *objlist):
        ret = []
        for l in self.splitlines():
            if l[0] != 'intr': continue
            for name, i in enumerate(l[2:]):
                if int(i) > 10: ret.append(str(name))
        return ret

#   def check(self):
#       if self.fd[0] and self.vars:
#           self.fd[0].seek(0)
#           for l in self.fd[0].splitlines():
#               if l[0] != 'intr': continue
#               return True
#       return False

    def vars(self):
        ret = []
        if op.intlist:
            varlist = op.intlist
        else:
            varlist = self.discover
            for name in varlist:
                if name in ('0', '1', '2', '8', 'NMI', 'LOC', 'MIS', 'CPU0'):
                    varlist.remove(name)
            if not op.full and len(varlist) > 3: varlist = varlist[-3:]
        for name in varlist:
            if name in self.discover + ['total',]:
                ret.append(name)
            elif name.lower() in self.intmap:
                ret.append(self.intmap[name.lower()])
        return ret

    def extract(self):
        for l in self.splitlines():
            if not l or l[0] != 'intr': continue
            for name in self.vars:
                if name != 'total':
                    self.set2[name] = int(l[int(name) + 2])
            self.set2['total'] = int(l[1])

        for name in self.vars:
            self.val[name] = (self.set2[name] - self.set1[name]) * 1.0 / elapsed

        if step == op.delay:
            self.set1.update(self.set2)

class dstat_int24(dstat):
    def __init__(self):
        self.name = 'interrupts'
        self.type = 'd'
        self.width = 5
        self.scale = 1000
        self.open('/proc/interrupts')

    def intmap(self):
        ret = {}
        for l in self.splitlines():
            if len(l) <= cpunr: continue
            l1 = l[0].split(':')[0]
            l2 = ' '.join(l[cpunr+2:]).split(',')
            ret[l1] = l1
            for name in l2:
                ret[name.strip().lower()] = l1
        return ret

    def discover(self, *objlist):
        ret = []
        for l in self.splitlines():
            if len(l) < cpunr+1: continue
            name = l[0].split(':')[0]
            if int(l[1]) > 10:
                ret.append(name)
        return ret

#   def check(self):
#       if self.fd and self.discover:
#           self.fd[0].seek(0)
#           for l in self.fd[0].splitlines():
#               if l[0] != 'intr' or len(l) > 2: continue
#               return True
#       return False

    def vars(self):
        ret = []
        if op.intlist:
            varlist = op.intlist
        else:
            varlist = self.discover
            for name in varlist:
                if name in ('0', '1', '2', '8', 'CPU0', 'ERR', 'LOC', 'MIS', 'NMI'):
                    varlist.remove(name)
            if not op.full and len(varlist) > 3: varlist = varlist[-3:]
        for name in varlist:
            if name in self.discover:
                ret.append(name)
            elif name.lower() in self.intmap:
                ret.append(self.intmap[name.lower()])
        return ret

    def extract(self):
        for l in self.splitlines():
            if len(l) < cpunr+1: continue
            name = l[0].split(':')[0]
            if name in self.vars:
                self.set2[name] = 0
                for i in l[1:1+cpunr]:
                    self.set2[name] = self.set2[name] + int(i)
#           elif len(l) > 2 + cpunr:
#               for hw in self.vars:
#                   for mod in l[2+cpunr:]:
#                       self.set2[mod] = int(l[1])

        for name in self.set2:
            self.val[name] = (self.set2[name] - self.set1[name]) * 1.0 / elapsed

        if step == op.delay:
            self.set1.update(self.set2)

class dstat_io(dstat):
    def __init__(self):
        self.nick = ('read', 'writ')
        self.type = 'f'
        self.width = 5
        self.scale = 1000
        self.diskfilter = re.compile('^([hsv]d[a-z]+\d+|cciss/c\d+d\d+p\d+|dm-\d+|md\d+|mmcblk\d+p\d0|VxVM\d+)$')
        self.open('/proc/diskstats')
        self.cols = 2

    def discover(self, *objlist):
        ret = []
        for l in self.splitlines():
            if len(l) < 13: continue
            if l[3:] == ['0',] * 11: continue
            name = l[2]
            ret.append(name)
        for item in objlist: ret.append(item)
        if not ret:
            raise Exception("No suitable block devices found to monitor")
        return ret

    def vars(self):
        ret = []
        if op.disklist:
            varlist = op.disklist
        elif not op.full:
            varlist = ('total',)
        else:
            varlist = []
            for name in self.discover:
                if self.diskfilter.match(name): continue
                if name not in blockdevices(): continue
                varlist.append(name)
#           if len(varlist) > 2: varlist = varlist[0:2]
            varlist.sort()
        for name in varlist:
            if name in self.discover + ['total'] or name in op.diskset:
                ret.append(name)
        return ret

    def name(self):
        return ['io/'+name for name in self.vars]

    def extract(self):
        for name in self.vars: self.set2[name] = (0, 0)
        for l in self.splitlines():
            if len(l) < 13: continue
            if l[3] == '0' and l[7] == '0': continue
            name = l[2]
            if l[3:] == ['0',] * 11: continue
            if not self.diskfilter.match(name):
                self.set2['total'] = ( self.set2['total'][0] + int(l[3]), self.set2['total'][1] + int(l[7]) )
            if name in self.vars and name != 'total':
                self.set2[name] = ( self.set2[name][0] + int(l[3]), self.set2[name][1] + int(l[7]) )
            for diskset in self.vars:
                if diskset in op.diskset:
                    for disk in op.diskset[diskset]:
                        if fnmatch.fnmatch(name, disk):
                            self.set2[diskset] = ( self.set2[diskset][0] + int(l[3]), self.set2[diskset][1] + int(l[7]) )

        for name in self.set2:
            self.val[name] = list(map(lambda x, y: (y - x) * 1.0 / elapsed, self.set1[name], self.set2[name]))

        if step == op.delay:
            self.set1.update(self.set2)

class dstat_ipc(dstat):
    def __init__(self):
        self.name = 'sysv ipc'
        self.vars = ('msg', 'sem', 'shm')
        self.type = 'd'
        self.width = 3
        self.scale = 10

    def extract(self):
        for name in self.vars:
            self.val[name] = len(dopen('/proc/sysvipc/'+name).readlines()) - 1

class dstat_load(dstat):
    def __init__(self):
        self.name = 'load avg'
        self.nick = ('1m', '5m', '15m')
        self.vars = ('load1', 'load5', 'load15')
        self.type = 'f'
        self.width = 4
        self.scale = 0.5
        self.open('/proc/loadavg')

    def extract(self):
        for l in self.splitlines():
            if len(l) < 3: continue
            self.val['load1'] = float(l[0])
            self.val['load5'] = float(l[1])
            self.val['load15'] = float(l[2])

class dstat_lock(dstat):
    def __init__(self):
        self.name = 'file locks'
        self.nick = ('pos', 'lck', 'rea', 'wri')
        self.vars = ('posix', 'flock', 'read', 'write')
        self.type = 'f'
        self.width = 3
        self.scale = 10
        self.open('/proc/locks')

    def extract(self):
        for name in self.vars: self.val[name] = 0
        for l in self.splitlines():
            if len(l) < 4: continue
            if l[1] == 'POSIX': self.val['posix'] += 1
            elif l[1] == 'FLOCK': self.val['flock'] += 1
            if l[3] == 'READ': self.val['read'] += 1
            elif l[3] == 'WRITE': self.val['write'] += 1

class dstat_mem(dstat):
    def __init__(self):
        self.name = 'memory usage'
        self.nick = ('used', 'free', 'buff', 'cach')
        self.vars = ('MemUsed', 'MemFree', 'Buffers', 'Cached')
        self.open('/proc/meminfo')

    def extract(self):
        adv_extract_vars = ('MemTotal', 'Shmem', 'SReclaimable')
        adv_val={}
        for l in self.splitlines():
            if len(l) < 2: continue
            name = l[0].split(':')[0]
            if name in self.vars:
                self.val[name] = int(l[1]) * 1024.0
            if name in adv_extract_vars:
                adv_val[name] = int(l[1]) * 1024.0

        self.val['MemUsed'] = adv_val['MemTotal'] - self.val['MemFree'] - self.val['Buffers'] - self.val['Cached'] - adv_val['SReclaimable'] + adv_val['Shmem']

class dstat_mem_adv(dstat_mem):
    """
    Advanced memory usage
    Displays memory usage similarly to the internal plugin but with added total, shared and reclaimable counters.
    Additionally, shared memory is added and reclaimable memory is subtracted from the used memory counter.
    """
    def __init__(self):
        self.name = 'advanced memory usage'
        self.nick = ('total', 'used', 'free', 'buff', 'cach', 'dirty', 'shmem', 'recl')
        self.vars = ('MemTotal', 'MemUsed', 'MemFree', 'Buffers', 'Cached', 'Dirty', 'Shmem', 'SReclaimable')
        self.open('/proc/meminfo')

class dstat_net(dstat):
    def __init__(self):
        self.nick = ('recv', 'send')
        self.type = 'b'
        self.totalfilter = re.compile('^(lo|bond\d+|face|.+\.\d+)$')
        self.open('/proc/net/dev')
        self.cols = 2

    def discover(self, *objlist):
        ret = []
        for l in self.splitlines(replace=':'):
            if len(l) < 17: continue
            if l[2] == '0' and l[10] == '0': continue
            name = l[0]
            if name not in ('lo', 'face'):
                ret.append(name)
        ret.sort()
        for item in objlist: ret.append(item)
        return ret

    def vars(self):
        ret = []
        if op.netlist:
            varlist = op.netlist
        elif not op.full:
            varlist = ('total',)
        else:
            varlist = self.discover
#           if len(varlist) > 2: varlist = varlist[0:2]
            varlist.sort()
        for name in varlist:
            if name in self.discover + ['total', 'lo']:
                ret.append(name)
        if not ret:
            raise Exception("No suitable network interfaces found to monitor")
        return ret

    def name(self):
        return ['net/'+name for name in self.vars]

    def extract(self):
        self.set2['total'] = [0, 0]
        for l in self.splitlines(replace=':'):
            if len(l) < 17: continue
            if l[2] == '0' and l[10] == '0': continue
            name = l[0]
            if name in self.vars :
                self.set2[name] = ( int(l[1]), int(l[9]) )
            if not self.totalfilter.match(name):
                self.set2['total'] = ( self.set2['total'][0] + int(l[1]), self.set2['total'][1] + int(l[9]))

        if update:
            for name in self.set2:
                self.val[name] = list(map(lambda x, y: (y - x) * 1.0 / elapsed, self.set1[name], self.set2[name]))
                if self.val[name][0] < 0: self.val[name][0] += maxint + 1
                if self.val[name][1] < 0: self.val[name][1] += maxint + 1

        if step == op.delay:
            self.set1.update(self.set2)

class dstat_page(dstat):
    def __init__(self):
        self.name = 'paging'
        self.nick = ('in', 'out')
        self.vars = ('pswpin', 'pswpout')
        self.type = 'd'
        self.open('/proc/vmstat')

    def extract(self):
        for l in self.splitlines():
            if len(l) < 2: continue
            name = l[0]
            if name in self.vars:
                self.set2[name] = int(l[1])

        for name in self.vars:
            self.val[name] = (self.set2[name] - self.set1[name]) * pagesize * 1.0 / elapsed

        if step == op.delay:
            self.set1.update(self.set2)

class dstat_page24(dstat):
    def __init__(self):
        self.name = 'paging'
        self.nick = ('in', 'out')
        self.vars = ('pswpin', 'pswpout')
        self.type = 'd'
        self.open('/proc/stat')

    def extract(self):
        for l in self.splitlines():
            if len(l) < 3: continue
            name = l[0]
            if name != 'swap': continue
            self.set2['pswpin'] = int(l[1])
            self.set2['pswpout'] = int(l[2])
            break

        for name in self.vars:
            self.val[name] = (self.set2[name] - self.set1[name]) * pagesize * 1.0 / elapsed

        if step == op.delay:
            self.set1.update(self.set2)

class dstat_proc(dstat):
    def __init__(self):
        self.name = 'procs'
        self.nick = ('run', 'blk', 'new')
        self.vars = ('procs_running', 'procs_blocked', 'processes')
        self.type = 'f'
        self.width = 3
        self.scale = 10
        self.open('/proc/stat')

    def extract(self):
        for l in self.splitlines():
            if len(l) < 2: continue
            name = l[0]
            if name == 'processes':
                self.val['processes'] = 0
                self.set2[name] = int(l[1])
            elif name == 'procs_running':
                self.set2[name] = self.set2[name] + int(l[1]) - 1
            elif name == 'procs_blocked':
                self.set2[name] = self.set2[name] + int(l[1])

        self.val['processes'] = (self.set2['processes'] - self.set1['processes']) * 1.0 / elapsed
        for name in ('procs_running', 'procs_blocked'):
            self.val[name] = self.set2[name] * 1.0

        if step == op.delay:
            self.set1.update(self.set2)
            for name in ('procs_running', 'procs_blocked'):
                self.set2[name] = 0

class dstat_raw(dstat):
    def __init__(self):
        self.name = 'raw'
        self.nick = ('raw',)
        self.vars = ('sockets',)
        self.type = 'd'
        self.width = 4
        self.scale = 1000
        self.open('/proc/net/raw')

    def extract(self):
        lines = -1
        for line in self.readlines():
            lines += 1
        self.val['sockets'] = lines
        ### Cannot use len() on generator
#        self.val['sockets'] = len(self.readlines()) - 1

class dstat_socket(dstat):
    def __init__(self):
        self.name = 'sockets'
        self.type = 'd'
        self.width = 4
        self.scale = 1000
        self.open('/proc/net/sockstat')
        self.nick = ('tot', 'tcp', 'udp', 'raw', 'frg')
        self.vars = ('sockets:', 'TCP:', 'UDP:', 'RAW:', 'FRAG:')

    def extract(self):
        for l in self.splitlines():
            if len(l) < 3: continue
            self.val[l[0]] = int(l[2])

        self.val['other'] = self.val['sockets:'] - self.val['TCP:'] - self.val['UDP:'] - self.val['RAW:'] - self.val['FRAG:']

class dstat_swap(dstat):
    def __init__(self):
        self.name = 'swap'
        self.nick = ('used', 'free')
        self.type = 'd'
        self.open('/proc/swaps')

    def discover(self, *objlist):
        ret = []
        for l in self.splitlines():
            if len(l) < 5: continue
            if l[0] == 'Filename': continue
            try:
                int(l[2])
                int(l[3])
            except:
                continue
#           ret.append(improve(l[0]))
            ret.append(l[0])
        ret.sort()
        for item in objlist: ret.append(item)
        return ret

    def vars(self):
        ret = []
        if op.swaplist:
            varlist = op.swaplist
        elif not op.full:
            varlist = ('total',)
        else:
            varlist = self.discover
#           if len(varlist) > 2: varlist = varlist[0:2]
            varlist.sort()
        for name in varlist:
            if name in self.discover + ['total']:
                ret.append(name)
        if not ret:
            raise Exception("No suitable swap devices found to monitor")
        return ret

    def name(self):
        return ['swp/'+improve(name) for name in self.vars]

    def extract(self):
        self.val['total'] = [0, 0]
        for l in self.splitlines():
            if len(l) < 5 or l[0] == 'Filename': continue
            name = l[0]
            self.val[name] = ( int(l[3]) * 1024.0, (int(l[2]) - int(l[3])) * 1024.0 )
            self.val['total'] = ( self.val['total'][0] + self.val[name][0], self.val['total'][1] + self.val[name][1])

class dstat_swap_old(dstat):
    def __init__(self):
        self.name = 'swap'
        self.nick = ('used', 'free')
        self.vars = ('SwapUsed', 'SwapFree')
        self.type = 'd'
        self.open('/proc/meminfo')

    def extract(self):
        for l in self.splitlines():
            if len(l) < 2: continue
            name = l[0].split(':')[0]
            if name in self.vars + ('SwapTotal',):
                self.val[name] = int(l[1]) * 1024.0

        self.val['SwapUsed'] = self.val['SwapTotal'] - self.val['SwapFree']

class dstat_sys(dstat):
    def __init__(self):
        self.name = 'system'
        self.nick = ('int', 'csw')
        self.vars = ('intr', 'ctxt')
        self.type = 'd'
        self.width = 5
        self.scale = 1000
        self.open('/proc/stat')

    def extract(self):
        for l in self.splitlines():
            if len(l) < 2: continue
            name = l[0]
            if name in self.vars:
                self.set2[name] = int(l[1])

        for name in self.vars:
            self.val[name] = (self.set2[name] - self.set1[name]) * 1.0 / elapsed

        if step == op.delay:
            self.set1.update(self.set2)

class dstat_tcp(dstat):
    def __init__(self):
        self.name = 'tcp sockets'
        self.nick = ('lis', 'act', 'syn', 'tim', 'clo')
        self.vars = ('listen', 'established', 'syn', 'wait', 'close')
        self.type = 'd'
        self.width = 4
        self.scale = 1000
        self.open('/proc/net/tcp', '/proc/net/tcp6')

    def extract(self):
        for name in self.vars: self.val[name] = 0
        for l in self.splitlines():
            if len(l) < 12: continue
            ### 01: established, 02: syn_sent,  03: syn_recv, 04: fin_wait1,
            ### 05: fin_wait2,   06: time_wait, 07: close,    08: close_wait,
            ### 09: last_ack,    0A: listen,    0B: closing
            if l[3] in ('0A',): self.val['listen'] += 1
            elif l[3] in ('01',): self.val['established'] += 1
            elif l[3] in ('02', '03', '09',): self.val['syn'] += 1
            elif l[3] in ('06',): self.val['wait'] += 1
            elif l[3] in ('04', '05', '07', '08', '0B',): self.val['close'] += 1

class dstat_time(dstat):
    def __init__(self):
        self.name = 'system'
        self.timefmt = os.getenv('DSTAT_TIMEFMT') or '%d-%m %H:%M:%S'
        self.type = 's'
        if op.debug:
            self.width = len(time.strftime(self.timefmt, time.localtime())) + 4
        else:
            self.width = len(time.strftime(self.timefmt, time.localtime()))
        self.scale = 0
        self.vars = ('time',)

    ### We are now using the starttime for this plugin, not the execution time of this plugin
    def extract(self):
        if op.debug:
            self.val['time'] = time.strftime(self.timefmt, time.localtime(starttime)) + ".%03d" % (round(starttime * 1000 % 1000 ))
        else:
            self.val['time'] = time.strftime(self.timefmt, time.localtime(starttime))

class dstat_udp(dstat):
    def __init__(self):
        self.name = 'udp'
        self.nick = ('lis', 'act')
        self.vars = ('listen', 'established')
        self.type = 'd'
        self.width = 4
        self.scale = 1000
        self.open('/proc/net/udp', '/proc/net/udp6')

    def extract(self):
        for name in self.vars: self.val[name] = 0
        for l in self.splitlines():
            if l[3] == '07': self.val['listen'] += 1
            elif l[3] == '01': self.val['established'] += 1

class dstat_unix(dstat):
    def __init__(self):
        self.name = 'unix sockets'
        self.nick = ('dgm', 'str', 'lis', 'act')
        self.vars = ('datagram', 'stream', 'listen', 'established')
        self.type = 'd'
        self.width = 4
        self.scale = 1000
        self.open('/proc/net/unix')

    def extract(self):
        for name in self.vars: self.val[name] = 0
        for l in self.splitlines():
            if l[4] == '0002': self.val['datagram'] += 1
            elif l[4] == '0001':
                self.val['stream'] += 1
                if l[5] == '01': self.val['listen'] += 1
                elif l[5] == '03': self.val['established'] += 1

class dstat_vm(dstat):
    def __init__(self):
        self.name = 'virtual memory'
        self.nick = ('majpf', 'minpf', 'alloc', 'free')
        ### Page allocations should include all page zones, not just ZONE_NORMAL,
        ### but also ZONE_DMA, ZONE_HIGHMEM, ZONE_DMA32 (depending on architecture)
        self.vars = ('pgmajfault', 'pgfault', 'pgalloc_*', 'pgfree')
        self.type = 'd'
        self.width = 5
        self.scale = 1000
        self.open('/proc/vmstat')

    def extract(self):
        for name in self.vars:
            self.set2[name] = 0
        for l in self.splitlines():
            if len(l) < 2: continue
            for name in self.vars:
                if fnmatch.fnmatch(l[0], name):
                    self.set2[name] += int(l[1])

        for name in self.vars:
            self.val[name] = (self.set2[name] - self.set1[name]) * 1.0 / elapsed

        if step == op.delay:
            self.set1.update(self.set2)

class dstat_vm_adv(dstat_vm):
    def __init__(self):
        self.name = 'advanced virtual memory'
        self.nick = ('steal', 'scanK', 'scanD', 'pgoru', 'astll')
        self.vars = ('pgsteal_*', 'pgscan_kswapd_*', 'pgscan_direct_*', 'pageoutrun', 'allocstall')
        self.type = 'd'
        self.width = 5
        self.scale = 1000
        self.open('/proc/vmstat')

class dstat_zones(dstat):
    def __init__(self):
        self.name = 'zones memory'
#        self.nick = ('dmaF', 'dmaH', 'd32F', 'd32H', 'movaF', 'movaH')
#        self.vars = ('DMA_free', 'DMA_high', 'DMA32_free', 'DMA32_high', 'Movable_free', 'Movable_high')
        self.nick = ('d32F', 'd32H', 'normF', 'normH')
        self.vars = ('DMA32_free', 'DMA32_high', 'Normal_free', 'Normal_high')
        self.type = 'd'
        self.width = 5
        self.scale = 1000
        self.open('/proc/zoneinfo')

    ### Page allocations should include all page zones, not just ZONE_NORMAL,
    ### but also ZONE_DMA, ZONE_HIGHMEM, ZONE_DMA32 (depending on architecture)
    def extract(self):
        for l in self.splitlines():
            if len(l) < 2: continue
            if l[0].startswith('Node'):
                zone = l[3]
                found_high = 0
            if l[0].startswith('pages'):
                self.val[zone+'_free'] = int(l[2])
            if l[0].startswith('high') and not found_high:
                self.val[zone+'_high'] = int(l[1])
                found_high = 1


### END STATS DEFINITIONS ###

color = {
    'black': '\033[0;30m',
    'darkred': '\033[0;31m',
    'darkgreen': '\033[0;32m',
    'darkyellow': '\033[0;33m',
    'darkblue': '\033[0;34m',
    'darkmagenta': '\033[0;35m',
    'darkcyan': '\033[0;36m',
    'gray': '\033[0;37m',

    'darkgray': '\033[1;30m',
    'red': '\033[1;31m',
    'green': '\033[1;32m',
    'yellow': '\033[1;33m',
    'blue': '\033[1;34m',
    'magenta': '\033[1;35m',
    'cyan': '\033[1;36m',
    'white': '\033[1;37m',

    'blackbg': '\033[40m',
    'redbg': '\033[41m',
    'greenbg': '\033[42m',
    'yellowbg': '\033[43m',
    'bluebg': '\033[44m',
    'magentabg': '\033[45m',
    'cyanbg': '\033[46m',
    'whitebg': '\033[47m',
}

ansi = {
    'reset': '\033[0;0m',
    'bold': '\033[1m',
    'reverse': '\033[2m',
    'underline': '\033[4m',

    'clear': '\033[2J',
#   'clearline': '\033[K',
    'clearline': '\033[2K',
    'save': '\033[s',
    'restore': '\033[u',
    'save_all': '\0337',
    'restore_all': '\0338',
    'linewrap': '\033[7h',
    'nolinewrap': '\033[7l',

    'up': '\033[1A',
    'down': '\033[1B',
    'right': '\033[1C',
    'left': '\033[1D',

    'default': '\033[0;0m',
}

char = {
    'pipe': '|',
    'colon': ':',
    'gt': '>',
    'space': ' ',
    'dash': '-',
    'plus': '+',
    'underscore': '_',
    'sep': ',',
}

def set_theme():
    "Provide a set of colors to use"
    if op.blackonwhite:
        theme = {
            'title': color['darkblue'],
            'subtitle': color['darkcyan'] + ansi['underline'],
            'frame': color['darkblue'],
            'default': ansi['default'],
            'error': color['white'] + color['redbg'],
            'roundtrip': color['darkblue'],
            'debug': color['darkred'],
            'input': color['darkgray'],
            'done_lo': color['black'],
            'done_hi': color['darkgray'],
            'text_lo': color['black'],
            'text_hi': color['darkgray'],
            'unit_lo': color['black'],
            'unit_hi': color['darkgray'],
            'colors_lo': (color['darkred'], color['darkmagenta'], color['darkgreen'], color['darkblue'],
                          color['darkcyan'], color['black'], color['red'], color['green']),
            'colors_hi': (color['red'], color['magenta'], color['green'], color['blue'],
                          color['cyan'], color['darkgray'], color['darkred'], color['darkgreen']),
        }
    else:
        theme = {
            'title': color['darkblue'],
            'subtitle': color['blue'] + ansi['underline'],
            'frame': color['darkblue'],
            'default': ansi['default'],
            'error': color['white'] + color['redbg'],
            'roundtrip': color['darkblue'],
            'debug': color['darkred'],
            'input': color['darkgray'],
            'done_lo': color['white'],
            'done_hi': color['gray'],
            'text_lo': color['gray'],
            'text_hi': color['darkgray'],
            'unit_lo': color['darkgray'],
            'unit_hi': color['darkgray'],
            'colors_lo': (color['red'], color['yellow'], color['green'], color['blue'],
                          color['cyan'], color['white'], color['darkred'], color['darkgreen']),
            'colors_hi': (color['darkred'], color['darkyellow'], color['darkgreen'], color['darkblue'],
                          color['darkcyan'], color['gray'], color['red'], color['green']),
        }
    return theme

def ticks():
    "Return the number of 'ticks' since bootup"
    try:
        for line in open('/proc/uptime', 'r').readlines():
            l = line.split()
            if len(l) < 2: continue
            return float(l[0])
    except:
        for line in dopen('/proc/stat').readlines():
            l = line.split()
            if len(l) < 2: continue
            if l[0] == 'btime':
                return time.time() - int(l[1])

def improve(devname):
    "Improve a device name"
    if devname.startswith('/dev/mapper/'):
        devname = devname.split('/')[3]
    elif devname.startswith('/dev/'):
        devname = devname.split('/')[2]
    return devname

def dopen(filename):
    "Open a file for reuse, if already opened, return file descriptor"
    global fds
    if not os.path.exists(filename):
        raise Exception('File %s does not exist' % filename)
    if 'fds' not in globals():
        fds = {}
    if filename in fds:
        fds[filename].seek(0)
    else:
        fds[filename] = open(filename, 'r')
    return fds[filename]

def dclose(filename):
    "Close an open file and remove file descriptor from list"
    global fds
    if not 'fds' in globals(): fds = {}
    if filename in fds:
        fds[filename].close()
        del(fds[filename])

def dpopen(cmd):
    "Open a pipe for reuse, if already opened, return pipes"
    global pipes, select
    import select
    if 'pipes' not in globals(): pipes = {}
    if cmd not in pipes:
        try:
            import asubprocess
            p = subprocess.Popen(cmd, shell=True, bufsize=0, close_fds=True,
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            pipes[cmd] = (p.stdin, p.stdout, p.stderr)
        except ImportError:
            pipes[cmd] = os.popen3(cmd, 't', 0)
    return pipes[cmd]

def readpipe(fileobj, tmout = 0.001):
    "Read available data from pipe in a non-blocking fashion"
    ret = ''
    while not select.select([fileobj.fileno()], [], [], tmout)[0]:
        pass
    while select.select([fileobj.fileno()], [], [], tmout)[0]:
        ret = ret + fileobj.read(1)
    return ret.split('\n')

def greppipe(fileobj, str, tmout = 0.001):
    "Grep available data from pipe in a non-blocking fashion"
    ret = ''
    while not select.select([fileobj.fileno()], [], [], tmout)[0]:
        pass
    while select.select([fileobj.fileno()], [], [], tmout)[0]:
        character = fileobj.read(1)
        if character != '\n':
            ret = ret + character
        elif ret.startswith(str):
            return ret
        else:
            ret = ''
    if op.debug:
        raise Exception('Nothing found during greppipe data collection')
    return None

def matchpipe(fileobj, string, tmout = 0.001):
    "Match available data from pipe in a non-blocking fashion"
    ret = ''
    regexp = re.compile(string)
    while not select.select([fileobj.fileno()], [], [], tmout)[0]:
        pass
    while select.select([fileobj.fileno()], [], [], tmout)[0]:
        character = fileobj.read(1)
        if character != '\n':
            ret = ret + character
        elif regexp.match(ret):
            return ret
        else:
            ret = ''
    if op.debug:
        raise Exception('Nothing found during matchpipe data collection')
    return None

def cmd_test(cmd):
    pipes = os.popen3(cmd, 't', 0)
    for line in pipes[2].readlines():
        raise Exception(line.strip())

def cmd_readlines(cmd):
    pipes = os.popen3(cmd, 't', 0)
    for line in pipes[1].readlines():
       yield line

def cmd_splitlines(cmd, sep=None):
    pipes = os.popen3(cmd, 't', 0)
    for line in pipes[1].readlines():
       yield line.split(sep)

def proc_readlines(filename):
    "Return the lines of a file, one by one"
#    for line in open(filename).readlines():
#       yield line

    ### Implemented linecache (for top-plugins)
    i = 1
    while True:
        line = linecache.getline(filename, i);
        if not line: break
        yield line
        i += 1

def proc_splitlines(filename, sep=None):
    "Return the splitted lines of a file, one by one"
#    for line in open(filename).readlines():
#       yield line.split(sep)

    ### Implemented linecache (for top-plugins)
    i = 1
    while True:
        line = linecache.getline(filename, i);
        if not line: break
        yield line.split(sep)
        i += 1

def proc_readline(filename):
    "Return the first line of a file"
#    return open(filename).read()
    return linecache.getline(filename, 1)

def proc_splitline(filename, sep=None):
    "Return the first line of a file splitted"
#    return open(filename).read().split(sep)
    return linecache.getline(filename, 1).split(sep)

### FIXME: Should we cache this within every step ?
def proc_pidlist():
    "Return a list of process IDs"
    dstat_pid = str(os.getpid())
    for pid in os.listdir('/proc/'):
        try:
            ### Is it a pid ?
            int(pid)

            ### Filter out dstat
            if pid == dstat_pid: continue

            yield pid

        except ValueError:
            continue

def snmpget(server, community, oid):
    errorIndication, errorStatus, errorIndex, varBinds = cmdgen.CommandGenerator().getCmd(
        cmdgen.CommunityData('test-agent', community, 0),
        cmdgen.UdpTransportTarget((server, 161)),
        oid
    )
#    print('%s -> ind: %s, stat: %s, idx: %s' % (oid, errorIndication, errorStatus, errorIndex))
    for x in varBinds:
        return str(x[1])

def snmpwalk(server, community, oid):
    ret = []
    errorIndication, errorStatus, errorIndex, varBindTable = cmdgen.CommandGenerator().nextCmd(
        cmdgen.CommunityData('test-agent', community, 0),
        cmdgen.UdpTransportTarget((server, 161)),
        oid
    )
#    print('%s -> ind: %s, stat: %s, idx: %s' % (oid, errorIndication, errorStatus, errorIndex))
    for x in varBindTable:
        for y in x:
            ret.append(str(y[1]))
    return ret

def dchg(var, width, base):
    "Convert decimal to string given base and length"
    c = 0
    while True:
        ret = str(int(round(var)))
        if len(ret) <= width:
            break
        var = var / base
        c = c + 1
    else:
        c = -1
    return ret, c

def fchg(var, width, base):
    "Convert float to string given scale and length"
    c = 0
    while True:
        if var == 0:
            ret = str('0')
            break
#       ret = repr(round(var))
#       ret = repr(int(round(var, maxlen)))
        ret = str(int(round(var, width)))
        if len(ret) <= width:
            i = width - len(ret) - 1
            while i > 0:
                ret = ('%%.%df' % i) % var
                if len(ret) <= width and ret != str(int(round(var, width))):
                    break
                i = i - 1
            else:
                ret = str(int(round(var)))
            break
        var = var / base
        c = c + 1
    else:
        c = -1
    return ret, c

def tchg(var, width):
    "Convert time string to given length"
    ret = '%2dh%02d' % (var / 60, var % 60)
    if len(ret) > width:
        ret = '%2dh' % (var / 60)
        if len(ret) > width:
            ret = '%2dd' % (var / 60 / 24)
            if len(ret) > width:
                ret = '%2dw' % (var / 60 / 24 / 7)
    return ret

def cprintlist(varlist, ctype, width, scale):
    "Return all columns color printed"
    ret = sep = ''
    for var in varlist:
        ret = ret + sep + cprint(var, ctype, width, scale)
        sep = char['space']
    return ret

def cprint(var, ctype = 'f', width = 4, scale = 1000):
    "Color print one column"

    base = 1000
    if scale == 1024:
        base = 1024

    ### Use units when base is exact 1000 or 1024
    unit = False
    if scale in (1000, 1024) and width >= len(str(base)):
        unit = True
        width = width - 1

    ### If this is a negative value, return a dash
    if ctype != 's' and var < 0:
        if unit:
            return theme['error'] + '-'.rjust(width) + char['space'] + theme['default']
        else:
            return theme['error'] + '-'.rjust(width) + theme['default']

    if base != 1024:
        units = (char['space'], 'k', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y')
    elif op.bits and ctype in ('b', ):
        units = ('b', 'k', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y')
        base = scale = 1000
        var = var * 8.0
    else:
        units = ('B', 'k', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y')

    if step == op.delay:
        colors = theme['colors_lo']
        ctext = theme['text_lo']
        cunit = theme['unit_lo']
        cdone = theme['done_lo']
    else:
        colors = theme['colors_hi']
        ctext = theme['text_hi']
        cunit = theme['unit_hi']
        cdone = theme['done_hi']

    ### Convert value to string given base and field-length
    if op.integer and ctype in ('b', 'd', 'p', 'f'):
        ret, c = dchg(var, width, base)
    elif op.float and ctype in ('b', 'd', 'p', 'f'):
        ret, c = fchg(var, width, base)
    elif ctype in ('b', 'd', 'p'):
        ret, c = dchg(var, width, base)
    elif ctype in ('f',):
        ret, c = fchg(var, width, base)
    elif ctype in ('s',):
        ret, c = str(var), ctext
    elif ctype in ('t',):
        ret, c = tchg(var, width), ctext
    else:
        raise Exception('Type %s not known to dstat.' % ctype)

    ### Set the counter color
    if ret == '0':
        color = cunit
    elif scale <= 0:
        color = ctext
    elif ctype in ('p') and round(var) >= 100.0:
        color = cdone
#    elif type in ('p'):
#        color = colors[int(round(var)/scale)%len(colors)]
    elif scale not in (1000, 1024):
        color = colors[int(var/scale)%len(colors)]
    elif ctype in ('b', 'd', 'f'):
        color = colors[c%len(colors)]
    else:
        color = ctext

    ### Justify value to left if string
    if ctype in ('s',):
        ret = color + ret.ljust(width)
    else:
        ret = color + ret.rjust(width)

    ### Add unit to output
    if unit:
        if c != -1 and round(var) != 0:
            ret += cunit + units[c]
        else:
            ret += char['space']

    return ret

def header(totlist, vislist):
    "Return the header for a set of module counters"
    line = ''
    ### Process title
    for o in vislist:
        line += o.title()
        if o is not vislist[-1]:
            line += theme['frame'] + char['space']
        elif totlist != vislist:
            line += theme['title'] + char['gt']
    line += '\n'
    ### Process subtitle
    for o in vislist:
        line += o.subtitle()
        if o is not vislist[-1]:
            line += theme['frame'] + char['pipe']
        elif totlist != vislist:
            line += theme['title'] + char['gt']
    return line + '\n'

def csvheader(totlist):
    "Return the CVS header for a set of module counters"
    line = ''
    ### Process title
    for o in totlist:
        line = line + o.csvtitle()
        if o is not totlist[-1]:
            line = line + char['sep']
    line += '\n'
    ### Process subtitle
    for o in totlist:
        line = line + o.csvsubtitle()
        if o is not totlist[-1]:
            line = line + char['sep']
    return line + '\n'

def info(level, msg):
    "Output info message"
#   if level <= op.verbose:
    print(msg, file=sys.stderr)

def die(ret, msg):
    "Print error and exit with errorcode"
    print(msg, file=sys.stderr)
    exit(ret)

def initterm():
    "Initialise terminal"
    global termsize

    ### Unbuffered sys.stdout
#    sys.stdout = os.fdopen(1, 'w', 0)

    termsize = None, 0
    try:
        global fcntl, struct, termios
        import fcntl, struct, termios
        termios.TIOCGWINSZ
    except:
        try:
            curses.setupterm()
            curses.tigetnum('lines'), curses.tigetnum('cols')
        except:
            pass
        else:
            termsize = None, 2
    else:
        termsize = None, 1

def gettermsize():
    "Return the dynamic terminal geometry"
    global termsize

#    if not termsize[0] and not termsize[1]:
    if not termsize[0]:
        try:
            if termsize[1] == 1:
                s = struct.pack('HHHH', 0, 0, 0, 0)
                x = fcntl.ioctl(sys.stdout.fileno(), termios.TIOCGWINSZ, s)
                return struct.unpack('HHHH', x)[:2]
            elif termsize[1] == 2:
                curses.setupterm()
                return curses.tigetnum('lines'), curses.tigetnum('cols')
            else:
                termsize = (int(os.environ['LINES']), int(os.environ['COLUMNS']))
        except:
            termsize = 25, 80
    return termsize

def gettermcolor():
    "Return whether the system can use colors or not"
    if sys.stdout.isatty():
        try:
            import curses
            curses.setupterm()
            if curses.tigetnum('colors') < 0:
                return False
        except ImportError:
            print('Color support is disabled as python-curses is not installed.', file=sys.stderr)
            return False
        except:
            print('Color support is disabled as curses does not find terminal "%s".' % os.getenv('TERM'), file=sys.stderr)
            return False
        return True
    return False

### We only want to filter out paths, not ksoftirqd/1
def basename(name):
    "Perform basename on paths only"
    if name[0] in ('/', '.'):
        return os.path.basename(name)
    return name

def getnamebypid(pid, name):
    "Return the name of a process by taking best guesses and exclusion"
    ret = None
    try:
        #### man proc tells me there should be nulls in here, but sometimes it seems like spaces (esp google chrome)
#        cmdline = open('/proc/%s/cmdline' % pid).read().split(('\0', ' '))
        cmdline = linecache.getline('/proc/%s/cmdline' % pid, 1).split(('\0', ' '))
        ret = basename(cmdline[0])
        if ret in ('bash', 'csh', 'ksh', 'perl', 'python', 'ruby', 'sh'):
            ret = basename(cmdline[1])
        if ret.startswith('-'):
            ret = basename(cmdline[-2])
            if ret.startswith('-'): raise
        if not ret: raise
    except:
        ret = basename(name)
    return ret

def getcpunr():
    "Return the number of CPUs in the system"

    # POSIX
    try:
        return os.sysconf("SC_NPROCESSORS_ONLN")
    except ValueError:
        pass

    # Python 2.6+
    try:
        import multiprocessing
        return multiprocessing.cpu_count()
    except (ImportError, NotImplementedError):
       pass

    # Fallback 1
    try:
        cpunr = open('/proc/cpuinfo', 'r').read().count('processor\t:')
        if cpunr > 0:
            return cpunr
    except IOError:
        pass

    # Fallback 2
    try:
        search = re.compile('^cpu\d+')
        cpunr = 0
        for line in dopen('/proc/stat').readlines():
            if search.match(line):
                cpunr += 1
        if cpunr > 0:
            return cpunr
    except:
        raise Exception("Problem finding number of CPUs in system.")

def blockdevices():
    ### We have to replace '!' by '/' to support cciss!c0d0 type devices :-/
    return [os.path.basename(filename).replace('!', '/') for filename in glob.glob('/sys/block/*')]

### FIXME: Add scsi support too and improve
def sysfs_dev(device):
    "Convert sysfs device names into device names"
    m = re.match('ide/host(\d)/bus(\d)/target(\d)/lun(\d)/disc', device)
    if m:
        l = m.groups()
        # ide/host0/bus0/target0/lun0/disc -> 0 -> hda
        # ide/host0/bus1/target0/lun0/disc -> 2 -> hdc
        nr = int(l[1]) * 2 + int(l[3])
        return 'hd' + chr(ord('a') + nr)
    m = re.match('cciss/(c\dd\d)', device)
    if m:
        l = m.groups()
        return l[0]
    m = re.match('placeholder', device)
    if m:
        return 'sdX'
    return device

def dev(maj, min):
    "Convert major/minor pairs into device names"
    ram = [1, ]
    ide = [3, 22, 33, 34, 56, 57, 88, 89, 90, 91]
    loop = [7, ]
    scsi = [8, 65, 66, 67, 68, 69, 70, 71, 128, 129, 130, 131, 132, 133, 134, 135]
    md = [9, ]
    ida = [72, 73, 74, 75, 76, 77, 78, 79]
    ubd = [98,]
    cciss = [104,]
    dm =  [253,]
    if maj in scsi:
        disc = chr(ord('a') + scsi.index(maj) * 16 + min / 16)
        part = min % 16
        if not part: return 'sd%s' % disc
        return 'sd%s%d' % (disc, part)
    elif maj in ide:
        disc = chr(ord('a') + ide.index(maj) * 2 + min / 64)
        part = min % 64
        if not part: return 'hd%s' % disc
        return 'hd%s%d' % (disc, part)
    elif maj in dm:
        return 'dm-%d' % min
    elif maj in md:
        return 'md%d' % min
    elif maj in loop:
        return 'loop%d' % min
    elif maj in ram:
        return 'ram%d' % min
    elif maj in cciss:
        disc = cciss.index(maj) * 16 + min / 16
        part = min % 16
        if not part: return 'c0d%d' % disc
        return 'c0d%dp%d' % (disc, part)
    elif maj in ida:
        cont = ida.index(maj)
        disc = min / 16
        part = min % 16
        if not part: return 'ida%d-%d' % (cont, disc)
        return 'ida%d-%d-%d' % (cont, disc, part)
    elif maj in ubd:
        disc = ubd.index(maj) * 16 + min / 16
        part = min % 16
        if not part: return 'ubd%d' % disc
        return 'ubd%d-%d' % (disc, part)
    else:
        return 'dev%d-%d' % (maj, min)

#def mountpoint(dev):
#   "Return the mountpoint of a mounted device/file"
#   for entry in dopen('/etc/mtab').readlines():
#       if entry:
#           devlist = entry.split()
#           if dev == devlist[0]:
#               return devlist[1]

#def readfile(file):
#    ret = ''
#    for line in open(file,'r').readlines():
#        ret = ret + line
#    return ret

#cdef extern from "sched.h":
#    struct sched_param:
#        int sched_priority
#        int sched_setscheduler(int pid, int policy,sched_param  *p)
#
#SCHED_FIFO = 1
#
#def switchRTCPriority(nb):
#    cdef sched_param sp
#    sp.sched_priority = nb
#    sched_setscheduler (0,SCHED_FIFO , &sp);

def listplugins():
    plugins = []
    remod = re.compile('dstat_(.+)$')
    for filename in globals():
        if filename.startswith('dstat_'):
            plugins.append(remod.match(filename).groups()[0].replace('_', '-'))
    remod = re.compile('.+/dstat_(.+).py$')
    for path in pluginpath:
        for filename in glob.glob(path + '/dstat_*.py'):
            plugins.append(remod.match(filename).groups()[0].replace('_', '-'))
    plugins.sort()
    return plugins

def showplugins():
    rows, cols = gettermsize()
    print('internal:\n\t', end='')
    remod = re.compile('^dstat_(.+)$')
    plugins = []
    for filename in globals():
        if filename.startswith('dstat_'):
            plugins.append(remod.match(filename).groups()[0].replace('_', '-'))
    plugins.sort()
    cols2 = cols - 8
    for mod in plugins:
        cols2 = cols2 - len(mod) - 2
        if cols2 <= 0:
            print('\n\t', end='')
            cols2 = cols - len(mod) - 10
        if mod != plugins[-1]:
            print(mod, end=',')
    print(mod)
    remod = re.compile('.+/dstat_(.+).py$')
    for path in pluginpath:
        plugins = []
        for filename in glob.glob(path + '/dstat_*.py'):
            plugins.append(remod.match(filename).groups()[0].replace('_', '-'))
        if not plugins: continue
        plugins.sort()
        cols2 = cols - 8
        print('%s:' % os.path.abspath(path), end='\n\t')
        for mod in plugins:
            cols2 = cols2 - len(mod) - 2
            if cols2 <= 0:
                print(end='\n\t')
                cols2 = cols - len(mod) - 10
            if mod != plugins[-1]:
                print(mod, end=',')
        print(mod)

def exit(ret):
    sys.stdout.write(ansi['reset'])
    sys.stdout.flush()

    if op.pidfile and os.path.exists(op.pidfile):
        os.remove(op.pidfile)

    if op.profile and os.path.exists(op.profile):
        rows, cols = gettermsize()
        import pstats
        p = pstats.Stats(op.profile)
#        p.sort_stats('name')
#        p.print_stats()
        p.sort_stats('cumulative').print_stats(rows - 13)
#        p.sort_stats('time').print_stats(rows - 13)
#        p.sort_stats('file').print_stats('__init__')
#        p.sort_stats('time', 'cum').print_stats(.5, 'init')
#        p.print_callees()
    elif op.profile:
        print('No profiling data was found, maybe profiler was interrupted ?', file=sys.stderr)

    sys.exit(ret)

def main():
    "Initialization of the program, terminal, internal structures"
    global cpunr, hz, maxint, ownpid, pagesize
    global ansi, theme, outputfile
    global totlist, inittime
    global update, missed

    cpunr = getcpunr()
    hz = os.sysconf('SC_CLK_TCK')
    try:
        maxint = (sys.maxint + 1) * 2
    except:
        # Support Python 3
        maxint = float("inf")
    ownpid = str(os.getpid())
    pagesize = resource.getpagesize()
    interval = 1

    user = getpass.getuser()
    hostname = os.uname()[1]

    ### Write term-title
    if sys.stdout.isatty():
        shell = os.getenv('XTERM_SHELL')
        term = os.getenv('TERM')
        if shell == '/bin/bash' and term and re.compile('(screen*|xterm*)').match(term):
            sys.stdout.write('\033]0;(%s@%s) %s %s\007' % (user, hostname.split('.')[0], os.path.basename(sys.argv[0]), ' '.join(op.args)))

    ### Check background color (rxvt)
    ### COLORFGBG="15;default;0"
#   if os.environ['COLORFGBG'] and len(os.environ['COLORFGBG'].split(';')) >= 3:
#       l = os.environ['COLORFGBG'].split(';')
#       bg = int(l[2])
#       if bg < 7:
#           print 'Background is dark'
#       else:
#           print 'Background is light'
#   else:
#       print 'Background is unknown, assuming dark.'

    ### Check terminal capabilities
    if op.color == None:
        op.color = gettermcolor()

    ### Prepare CSV output file (unbuffered)
    if op.output:
        if not os.path.exists(op.output):
            outputfile = open(op.output, 'w')
            outputfile.write('"Dstat %s CSV output"\n' % VERSION)
            header = ('"Author:","Dag Wieers <dag@wieers.com>"','','','','"URL:"','"http://dag.wieers.com/home-made/dstat/"\n')
            outputfile.write(char['sep'].join(header))
        else:
            outputfile = open(op.output, 'a')
            outputfile.write('\n\n')

        header = ('"Host:"','"%s"' % hostname,'','','','"User:"','"%s"\n' % user)
        outputfile.write(char['sep'].join(header))
        header = ('"Cmdline:"','"dstat %s"' % ' '.join(op.args),'','','','"Date:"','"%s"\n' % time.strftime('%d %b %Y %H:%M:%S %Z', time.localtime()))
        outputfile.write(char['sep'].join(header))

    ### Create pidfile
    if op.pidfile:
        try:
            pidfile = open(op.pidfile, 'w')
            pidfile.write(str(os.getpid()))
            pidfile.close()
        except Exception as e:
            print('Failed to create pidfile %s: %s' % (op.pidfile, e), file=sys.stderr)
            op.pidfile = False

    ### Empty ansi and theme database if no colors are requested
    if not op.color:
        for key in color:
            color[key] = ''
        for key in theme:
            theme[key] = ''
        for key in ansi:
            ansi[key] = ''
        theme['colors_hi'] = (ansi['default'],)
        theme['colors_lo'] = (ansi['default'],)
#        print color['blackbg']

    ### Disable line-wrapping (does not work ?)
    sys.stdout.write(ansi['nolinewrap'])

    if not op.update:
        interval = op.delay

    ### Build list of requested plugins
    linewidth = 0
    totlist = []
    for plugin in op.plugins:

        ### Set up fallback lists
        if plugin == 'cpu':  mods = ( 'cpu', 'cpu24' )
        elif plugin == 'disk': mods = ( 'disk', 'disk24', 'disk24-old' )
        elif plugin == 'int':  mods = ( 'int', 'int24' )
        elif plugin == 'page': mods = ( 'page', 'page24' )
        elif plugin == 'swap': mods = ( 'swap', 'swap-old' )
        else: mods = ( plugin, )

        for mod in mods:
            pluginfile = 'dstat_' + mod.replace('-', '_')
            try:
                if pluginfile not in globals():
                    import imp
                    fp, pathname, description = imp.find_module(pluginfile, pluginpath)
                    fp.close()

                    ### TODO: Would using .pyc help with anything ?
                    ### Try loading python plugin
                    if description[0] in ('.py', ):
                        exec(open(pathname).read())
                        #execfile(pathname)
                        exec('global plug; plug = dstat_plugin(); del(dstat_plugin)')
                        plug.filename = pluginfile
                        plug.check()
                        plug.prepare()

                    ### Try loading C plugin (not functional yet)
                    elif description[0] == '.so':
                        exec('import %s; global plug; plug = %s.new()' % (pluginfile, pluginfile))
                        plug.check()
                        plug.prepare()
#                        print(dir(plug))
#                        print(plug.__module__)
#                        print(plug.name)
                    else:
                        print('Module %s is of unknown type.' % pluginfile, file=sys.stderr)

                else:
                    exec('global plug; plug = %s()' % pluginfile)
                    plug.check()
                    plug.prepare()
#                print(plug.__module__)
            except Exception as e:
                if mod == mods[-1]:
                    print('Module %s failed to load. (%s)' % (pluginfile, e), file=sys.stderr)
                elif op.debug:
                    print('Module %s failed to load, trying another. (%s)' % (pluginfile, e), file=sys.stderr)
                if op.debug >= 3:
                    raise
#                tb = sys.exc_info()[2]
                continue
            except:
                print('Module %s caused unknown exception' % pluginfile, file=sys.stderr)

            linewidth = linewidth + plug.statwidth() + 1
            totlist.append(plug)

            if op.debug:
                print('Module %s' % pluginfile, end='')
                if hasattr(plug, 'file'):
                    print(' requires %s' % plug.file, end='')
                print()
            break

    if not totlist:
        die(8, 'None of the stats you selected are available.')

    if op.output:
        outputfile.write(csvheader(totlist))

    scheduler = sched.scheduler(time.time, time.sleep)
    inittime = time.time()

    update = 0
    missed = 0

    ### Let the games begin
    while update <= op.delay * (op.count-1) or op.count == -1:
        scheduler.enterabs(inittime + update, 1, perform, (update,))
#        scheduler.enter(1, 1, perform, (update,))
        scheduler.run()
        sys.stdout.flush()
        update = update + interval
        linecache.clearcache()

    if op.update:
        sys.stdout.write('\n')

def perform(update):
        "Inner loop that calculates counters and constructs output"
        global totlist, oldvislist, vislist, showheader, rows, cols
        global elapsed, totaltime, starttime
        global loop, step, missed
        global header_flag

        starttime = time.time()

        loop = (update - 1 + op.delay) / op.delay
        step = ((update - 1) % op.delay) + 1

        ### Get current time (may be different from schedule) for debugging
        if not op.debug:
            curwidth = 0
        else:
            if step == 1 or loop == 0:
                totaltime = 0
            curwidth = 8

        ### FIXME: This is temporary functionality, we should do this better
        ### If it takes longer than 500ms, than warn !
        if loop != 0 and starttime - inittime - update > 1:
            missed = missed + 1
            return 0

        ### Initialise certain variables
        if loop == 0:
            elapsed = ticks()
            rows, cols = 0, 0
            vislist = []
            oldvislist = []
            showheader = True
        else:
            elapsed = step

        ### FIXME: Make this part smarter
        if sys.stdout.isatty():
            oldcols = cols
            rows, cols = gettermsize()

            ### Trim object list to what is visible on screen
            if oldcols != cols:
                vislist = []
                for o in totlist:
                    newwidth = curwidth + o.statwidth() + 1
                    if newwidth <= cols or ( vislist == totlist[:-1] and newwidth < cols ):
                        vislist.append(o)
                        curwidth = newwidth

            ### Check when to display the header
            if op.header and rows >= 6:
                if oldvislist != vislist:
                    showheader = True
                elif not op.update and loop % (rows - 2) == 0:
                    showheader = True
                elif op.update and step == 1 and loop % (rows - 1) == 0:
                    showheader = True

            oldvislist = vislist
        else:
            vislist = totlist

        ### Prepare the colors for intermediate updates, last step in a loop is definitive
        if step == op.delay:
            theme['default'] = ansi['reset']
        else:
            theme['default'] = theme['text_lo']

        ### The first step is to show the definitive line if necessary
        newline = ''
        if op.update:
            if step == 1 and update != 0:
                newline = '\n' + ansi['reset'] + ansi['clearline'] + ansi['save']
            elif loop != 0:
                newline = ansi['restore']

        ### Display header
        # if showheader:
        #     if loop == 0 and totlist != vislist:
        #         print('Terminal width too small, trimming output.', file=sys.stderr)
        #     showheader = False
        #     sys.stdout.write(newline)
        #     newline = header(totlist, vislist)
        # newline = header(totlist, vislist)
        # print(newline)

        ### Calculate all objects (visible, invisible)
        line = newline
        oline = ''
        for o in totlist:
            o.extract()
            if o in vislist:
                line = line + o.show() + o.showend(totlist, vislist)
            if op.output and step == op.delay:
                oline = oline + o.showcsv() + o.showcsvend(totlist, vislist)

        ### Print stats
        # sys.stdout.write(line + theme['input'])
        # os.system('dunstify -r %d -u critical "%s"'%(tag, '\\'+line))
        os.system('notify-send.sh -R /tmp/dstat_id -u critical " -total-cpu-usage-  -dsk/total- -net/total-   -paging-   -system-\nusr sys idl wai stl| read  writ| recv  send|  in   out | int   csw " "%s"'%line)

        # if op.output and step == op.delay:
        #     outputfile.write(oline + '\n')
#            outputfile.flush()

        ### Print debugging output
        if op.debug:
            totaltime = totaltime + (time.time() - starttime) * 1000.0
            if loop == 0:
                totaltime = totaltime * step
            if op.debug == 1:
                sys.stdout.write('%s%6.2fms%s' % (theme['roundtrip'], totaltime / step, theme['input']))
            elif op.debug == 2:
                sys.stdout.write('%s%6.2f %s%d:%d%s' % (theme['roundtrip'], totaltime / step, theme['debug'], loop, step, theme['input']))
            elif op.debug > 2:
                sys.stdout.write('%s%6.2f %s%d:%d:%d%s' % (theme['roundtrip'], totaltime / step, theme['debug'], loop, step, update, theme['input']))

        if missed > 0:
#            sys.stdout.write(' '+theme['error']+'= warn =')
            sys.stdout.write(' ' + theme['error'] + 'missed ' + str(missed+1) + ' ticks' + theme['input'])
            missed = 0

        ### Finish the line
        # if not op.update:
        #     sys.stdout.write('\n')

### Main entrance
if __name__ == '__main__':
    if os.path.exists("/tmp/dstat.lck"):
        sys.exit()
    else:
        os.system("touch /tmp/dstat.lck")
    try:
        header_flag = True

        initterm()
        op = Options(os.getenv('DSTAT_OPTS','').split() + sys.argv[1:])
        theme = set_theme()
        if op.profile:
            import profile
            if os.path.exists(op.profile):
                os.remove(op.profile)
            profile.run('main()', op.profile)
        else:
            main()
    except KeyboardInterrupt as e:
        if op.update:
            sys.stdout.write('\n')
    exit(0)
else:
    op = Options('')
    step = 1

# vim:ts=4:sw=4:et