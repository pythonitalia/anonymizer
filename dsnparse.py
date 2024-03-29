# https://github.com/Jaymon/dsnparse/blob/master/dsnparse.py
from __future__ import unicode_literals, division, print_function, absolute_import
try:
    import urlparse
    from urllib import unquote, quote
except ImportError:
    import urllib.parse as urlparse
    from urllib.parse import unquote, quote
import re
import os


__version__ = '0.1.15'


class ParseResult(object):
    """
    hold the results of a parsed dsn
    this is very similar to urlparse.ParseResult tuple
    http://docs.python.org/2/library/urlparse.html#results-of-urlparse-and-urlsplit
    it exposes the following attributes --
        scheme
        schemes -- if your scheme has +'s in it, then this will contain a list of schemes split by +
        path
        paths -- the path segment split by /, so "/foo/bar" would be ["foo", "bar"]
        host -- same as hostname (I just like host better)
        hostname
        hostloc -- host:port
        username
        password
        netloc
        query -- a dict of the query string
        query_str -- the raw query string
        port
        fragment
        anchor -- same as fragment, just an alternative name
    """
    @classmethod
    def verify(cls, dsn):
        if not re.match(r"^\S+://\S+", dsn):
            raise ValueError("{dsn} is invalid, only full dsn urls (scheme://host...) allowed".format(dsn=dsn))

    @classmethod
    def parse_scheme(cls, dsn):
        first_colon = dsn.find(':')
        scheme = dsn[0:first_colon]
        dsn = dsn[first_colon+1:]
        return scheme, dsn

    @classmethod
    def parse_credentials(cls, dsn):
        # so urlparse doesn't support passwords with special characters /+. So
        # I'm going to parse out the username:password with a more lenient
        # parser, the problem is something like "example.com:1000/@" will now
        # fail but I think it's probably far more common for a dsn to have a
        # username/password at the beginning than not have one but have a port
        # and @ symbol in the path
        username = password = None
        m = re.match(r"^//([^:]*):([^@]*)@", dsn)
        if m:
            username = m.group(1)
            password = m.group(2)
            dsn = "//{}".format(dsn[m.end():])

        return username, password, dsn

    @classmethod
    def parse_query(cls, url):
        # parse the query into options
        options = {}
        if url.query:
            for k, kv in urlparse.parse_qs(url.query, True, True).items():
                if len(kv) > 1:
                    options[k] = kv
                else:
                    options[k] = kv[0]

        return options

    @classmethod
    def parse(cls, dsn, **defaults):
        cls.verify(dsn)

        scheme, dsn_url = cls.parse_scheme(dsn)
        username, password, dsn_url = cls.parse_credentials(dsn_url)

        url = urlparse.urlparse(dsn_url)

        username = url.username or username
        password = url.password or password
        hostname = url.hostname
        path = url.path

        if url.netloc == ":memory:":
            # the special :memory: signifier is used in SQLite to define a fully in
            # memory database, I think it makes sense to support it since dsnparse is all
            # about making it easy to parse *any* dsn
            path = url.netloc
            hostname = None
            port = None

        else:
            # compensate for relative path
            if url.hostname == "." or url.hostname == "..":
                path = "".join([hostname, path])
                hostname = None

            port = url.port

        if hostname is not None:
            hostname = unquote(hostname)

        options = cls.parse_query(url)
        ret = {
            "dsn": dsn,
            "scheme": scheme,
            "hostname": hostname,
            "path": path,
            "port": port,
            "username": username,
            "password": password,
        }
        ret = cls.merge(ret, url, defaults, options)
        return ret

    @classmethod
    def merge(cls, ret, url, defaults, options):
        ret.update(dict(
            params=url.params,
            query=options,
            fragment=url.fragment,
            query_str=url.query,
        ))

        for k, v in defaults.items():
            if not ret.get(k, None):
                ret[k] = v

        for k in list(options.keys()):
            if k in ret:
                if ret[k] is None:
                    ret[k] = options.pop(k)
                else:
                    raise ValueError("{} specified in query string and dsn".format(k))

        for ret_k, options_k in [("hostname", "host")]:
            if options_k in options:
                if ret[ret_k] is None:
                    ret[ret_k] = options.pop(options_k)
                else:
                    raise ValueError("{} specified in query string and dsn".format(options_k))

        return ret

    def __init__(self, dsn, **defaults):
        kwargs = self.parse(dsn, **defaults)
        for k, v in kwargs.items():
            setattr(self, k, v)
        self.configure()

    def configure(self):
        """designed to be overridden in a child class"""
        pass

    def __iter__(self):
        mapping = ['scheme', 'netloc', 'path', 'params', 'query', 'fragment']
        for k in mapping:
            yield getattr(self, k, '')

    def __getitem__(self, index):
        index = int(index)
        mapping = {
            0: 'scheme',
            1: 'netloc',
            2: 'path',
            3: 'params',
            4: 'query',
            5: 'fragment',
        }

        return getattr(self, mapping[index], '')

    @property
    def schemes(self):
        """the scheme, split by plus signs"""
        return self.scheme.split('+')

    @property
    def netloc(self):
        """return username:password@hostname:port"""
        s = ''
        prefix = ''
        if self.username:
            s += self.username
            prefix = '@'

        if self.password:
            s += ":{password}".format(password=self.password)
            prefix = '@'

        s += "{prefix}{hostloc}".format(prefix=prefix, hostloc=self.hostloc)
        return s

    @property
    def paths(self):
        """the path attribute split by /"""
        return list(filter(None, self.path.split('/')))

    @property
    def host(self):
        """the hostname, but I like host better"""
        return self.hostname

    @property
    def user(self):
        """alias for username to match psycopg2"""
        return self.username

    @property
    def secret(self):
        """alias for password to match postgres dsn
        https://www.postgresql.org/docs/9.2/static/libpq-connect.html#LIBPQ-CONNSTRING
        """
        return self.password

    @property
    def hostloc(self):
        """return host:port"""
        hostloc = quote(self.hostname, safe="")
        #hostloc = self.hostname
        if self.port:
            hostloc = '{hostloc}:{port}'.format(hostloc=hostloc, port=self.port)

        return hostloc

    @property
    def anchor(self):
        """alternative name for the fragment"""
        return self.fragment

    @property
    def database(self):
        # sqlite uses database in its connect method https://docs.python.org/3.6/library/sqlite3.html
        if self.hostname is None:
            database = self.path
        else:
            # we have a host, which means the dsn is in the form: hostname/database most
            # likely, so let's get rid of the slashes when setting the db
            database = self.path.strip("/")
        return database
    # psycopg2 uses dbname: http://initd.org/psycopg/docs/module.html#psycopg2.connect
    dbname = database

    def setdefault(self, key, val):
        """
        set a default value for key
        this is different than dict's setdefault because it will set default either
        if the key doesn't exist, or if the value at the key evaluates to False, so
        an empty string or a None value will also be updated
        :param key: string, the attribute to update
        :param val: mixed, the attributes new value if key has a current value
            that evaluates to False
        """
        if not getattr(self, key, None):
            setattr(self, key, val)

    def geturl(self):
        """return the dsn back into url form"""
        return urlparse.urlunparse((
            self.scheme,
            self.netloc,
            self.path,
            self.params,
            self.query_str,
            self.fragment,
        ))


def parse_environ(name, parse_class=ParseResult, **defaults):
    """
    same as parse() but you pass in an environment variable name that will be used
    to fetch the dsn
    :param name: string, the environment variable name that contains the dsn to parse
    :param parse_class: ParseResult, the class that will be used to hold parsed values
    :param **defaults: dict, any values you want to have defaults for if they aren't in the dsn
    :returns: ParseResult() tuple
    """
    return parse(os.environ[name], parse_class, **defaults)


def parse_environs(name, parse_class=ParseResult, **defaults):
    """
    same as parse_environ() but will also check name_1, name_2, ..., name_N and
    return all the found dsn strings from the environment
    this will look for name, and name_N (where N is 1 through infinity) in the environment,
    if it finds them, it will assume they are dsn urls and will parse them.
    The num checks (eg PROM_DSN_1, PROM_DSN_2) go in order, so you can't do PROM_DSN_1, PROM_DSN_3,
    because it will fail on _2 and move on, so make sure your num dsns are in order (eg, 1, 2, 3, ...)
    example --
        export DSN_1=some.Interface://host:port/dbname#i1
        export DSN_2=some.Interface://host2:port/dbname2#i2
        $ python
        >>> import dsnparse
        >>> print dsnparse.parse_environs('DSN') # prints list with 2 parsed dsn objects
    :param dsn_env_name: string, the name of the environment variables, _1, ... will be appended
    :param parse_class: ParseResult, the class that will be used to hold parsed values
    :returns: list all the found dsn strings in the environment with the given name prefix
    """
    ret = []
    if name in os.environ:
        ret.append(parse_environ(name, parse_class, **defaults))

    # now try importing _1 -> _N dsns
    increment_name = lambda name, num: '{name}_{num}'.format(name=name, num=num)
    dsn_num = 0 if increment_name(name, 0) in os.environ else 1
    dsn_env_num_name = increment_name(name, dsn_num)
    if dsn_env_num_name in os.environ:
        try:
            while True:
                ret.append(parse_environ(dsn_env_num_name, parse_class, **defaults))
                dsn_num += 1
                dsn_env_num_name = increment_name(name, dsn_num)

        except KeyError:
            pass

    return ret


def parse(dsn, parse_class=ParseResult, **defaults):
    """
    parse a dsn to parts similar to parseurl
    :param dsn: string, the dsn to parse
    :param parse_class: ParseResult, the class that will be used to hold parsed values
    :param **defaults: dict, any values you want to have defaults for if they aren't in the dsn
    :returns: ParseResult() tuple-like instance
    """
    r = parse_class(dsn, **defaults)
    return r
