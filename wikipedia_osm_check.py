#!/usr/bin/env python
import requests
import argparse
import places

class WikipediaOSMCheck(object):
    """
    Checks place names described by Wikipedia category against
    existing place names in OpenStreetMap.
    """
    _headers = {
            "User-Agent": "WikipediaOSMCheck v0.1; https://github.com/craigloftus/wikipedia-osm-check/",
        }
    _overpass = {
        "url": "http://overpass-api.de/api/interpreter",
        "params": {}
        }
    _wikipedia = {
        "url": "http://{0}.wikipedia.org/w/api.php",
        "params": {
            "format": "json",
            "action": "query",
            "list": "categorymembers",
            "cmprop": "title",
            "cmtype": "page",
            "cmlimit": "max"
            }
        }
    _exclude = [
        places.PARISH,
        places.COUNTY,
        places.COUNTRY,
        places.FARM,
        places.ISOLATED_DWELLING,
        places.ISLET,
        places.ISLAND
        ]

    def __init__(self, language):
        self.missing = []
        self.missing_articles = []
        self.existing = []
        self.places = []
        self._wikipedia['url'] = self._wikipedia['url'].format(language)

    @staticmethod
    def find_missing(expected, existing):
        """
        Return names from expected list that are missing from existing list

        Arguments:
        expected -- list of strings of expected place names
        existing -- list of strings of existing place names
        """
        return set(expected).difference(existing)

    @staticmethod
    def _find_names(place):
        """
        Return the place names for a given place dict.

        It will split names separated by semi-colons.
        If a place has no name associated then it will print a warning

        Arguments:
        place -- dict, a JSON representation of the OSM element
        """
        tags = place['tags']
        tags_names = ['name', 'place_name', 'alt_name']
        names = []
        for tag in tags_names:
            try:
                names.extend(tags[tag].split(';'))
            except KeyError:
                pass
        if not names:
            print "Place has no name (#{})".format(place['id'])
        return names

    @staticmethod
    def _sanitise_name(place_name): 
        """
        Return a cleaned place name, where cleaning means:
            * Discard characters after a comma
            * Trim whitespace
            * Remove dots
            * Replace hyphens with spaces
            * Replace " Saint " with " St "
            * Make lowercase

        Arguments:
        place_name -- str, string to be cleaned up
        """
        return place_name\
                .split(',')[0]\
                .strip()\
                .replace('.', '')\
                .replace('-', ' ')\
                .replace(' Saint ', ' St ')\
                .lower()

    @staticmethod
    def _parse_place_types(types_str, delimiter='|'):
        """
        Return list of place types from given types_str

        Arguments:
        types_str -- str, concatenated string of place types

        Keyword arguments:
        delimiter -- str, character used to delimit types_str (default |)
        """
        return [p.strip() for p in types_str.split(delimiter)\
            if p.strip() in places.TYPES]

    def _request(self, opts, query, query_key='q'):
        """
        Return JSON response to request described by given options and query.

        Arguments:
        opts -- dict, containing url and params properties
        query -- str, query string to pass to URL

        Keyword arguments:
        query_key -- str, name of parameter to (default 'q')
        """
        params = opts['params']
        params[query_key] = query
        resp = requests.get(opts['url'], params=params, headers=self._headers)
        if not resp.ok:
            raise Exception("Server threw an error for: {}".format(resp.url))
        return resp.json()

    def _request_category(self, category_str):
        """
        Return json export of given Wikipedia category.

        Response from Wikipedia is of the form:
            {
                "limits":{"categorymembers":500},
                "query":{"categorymembers":[
                    {
                        "ns":0,
                        "title": "<article_name>"
                    }
                    ...
                    ]}
            }

        Arguments:
        category_name -- str, full category name, Category:Things
        """
        return self._request(self._wikipedia, category_str, query_key='cmtitle')

    def _request_existing(self, region_name):
        """
        Return list of place elements for the given region name.

        Response from Overpass is of the form:
            {
                "elements": [
                    {
                        "type": "node",
                        "id": 814072,
                        "lat": 51.5845416,
                        "lon": -1.0913475,
                        "tags": {
                            "name": "Cart Gap",
                            "place": "locality",
                            "source": "NPE"
                            } 
                    }
                    ...
                ]
            }

        Arguments:
        region_name -- str, that is a valid Overpass area
        """
        exclude = '|'.join(self._exclude)
        bits = [
            '[out:json]',
            'area[name="{}"]->.a'.format(region_name),
            '(node[place][place!~"{}"](area.a)'.format(exclude),
            'way[place][place!~"{}"](area.a)'.format(exclude),
            'rel[place][place!~"{}"](area.a);)'.format(exclude),
            'out;'
            ]

        resp = self._request(self._overpass, ';'.join(bits), query_key="data")
        return resp["elements"]

    def _request_typed_existing(self, region_name, place_types_str):
        """
        Return list of places for the given region and types specified

        Arguments:
        region_name --
        place_types_str - pipe concat'ed str of place types, see places.py
        """
        types = self._parse_place_types(place_types_str)

        if not types:
            raise Exception("No valid place types were supplied")

        include = "|".join(types)

        bits = [
            '[out:json]',
            'area[name="{}"]->.a'.format(region_name),
            '(node[place="{}"](area.a)'.format(include),
            'way[place="{}"](area.a)'.format(include),
            'rel[place="{}"](area.a);)'.format(include),
            'out;'
            ]

        resp = self._request(self._overpass, ';'.join(bits), query_key="data")
        return resp["elements"]

    def load_existing_names(self, region_name, types=None):
        """
        Return list of existing place names within the given region.

        Arguments:
        region_name -- str, that is a valid Overpass area

        Keyword arguments:
        types -- str|None, pipe concat'd str of place types to check for
        """
        if types:
            existing_places = self._request_typed_existing(region_name, types)
        else:
            existing_places = self._request_existing(region_name)
        place_names = []
        for place in existing_places:
            place_names.extend(self._find_names(place))
        return [self._sanitise_name(place) for place in place_names]

    def load_wikipedia_names(self, category_name):
        """
        Return list of place names within the given wikipedia category.

        Arguments:
        category_name -- str, full category name, Category:Things
        """
        try:
            wiki_places = self._request_category(category_name)\
                ['query']['categorymembers']
        except KeyError:
            return []
        return [self._sanitise_name(place['title']) for place in wiki_places]

    def run(self, category_name, region_name, types=None):
        """
        Find missing places for a given category name and region name

        Populates self.places, self.existing and self.missing

        Arguments:
        category_name -- str, full category name, Category:Things
        region_name -- str, that is a valid Overpass area

        Keyword arguments:
        types -- str|None, pipe concat'd str of place types to check for
        """
        self.places = self.load_wikipedia_names(category_name)
        if not self.places:
            print "No places found in category"
            return
        self.existing = self.load_existing_names(region_name, types=types)
        if not self.existing:
            print "No existing places found in region"
        self.missing = self.find_missing(self.places, self.existing)
        self.missing_articles = self.find_missing(self.existing, self.places)
        self.report()

    def report(self):
        """Print summary of findings"""
        print "Got {} places from Wikipedia.".format(len(self.places))
        print "Got {} existing places.".format(len(self.existing))
        print "Found {} missing places:".format(len(self.missing))
        print '\n'.join(self.missing)
        print "Found {} missing articles:".format(len(self.missing_articles))
        print '\n'.join(self.missing_articles)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('language', type=str, \
        help="Wikipedia language (ISO language code).")
    parser.add_argument('category', type=str, \
        help="Wikipedia category to check.")
    parser.add_argument('region', type=str, \
        help="Region to check within.")
    parser.add_argument('-t', '--types', help="Specify types of place to check;\
        should be of the form 'village|hamlet|farm'.")
    passed_args = vars(parser.parse_args())

    check = WikipediaOSMCheck(passed_args['language'])
    check.run(passed_args['category'], passed_args['region'],
            types=passed_args['types'])
