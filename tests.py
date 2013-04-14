import unittest
import wikipedia_osm_check

class TestSanitise(unittest.TestCase):
    def setUp(self):
        self.obj = wikipedia_osm_check.WikipediaOSMCheck()

    def test_dot_removal(self):
        dirty = 'foo.bar.fish.'
        self.assertEqual(self.obj._sanitise_name(dirty), 'foobarfish')

    def test_lowercase(self):
        dirty = 'FooBarFISH'
        self.assertEqual(self.obj._sanitise_name(dirty), 'foobarfish')

    def test_comma_stripping(self):
        dirty = 'Foo, Bar'
        self.assertEqual(self.obj._sanitise_name(dirty), 'foo')

    def test_multi_comma(self):
        dirty = 'Foo, Bar, Fish'
        self.assertEqual(self.obj._sanitise_name(dirty), 'foo')


class TestPlaceNameFinding(unittest.TestCase):
    def setUp(self):
        self.obj = wikipedia_osm_check.WikipediaOSMCheck()

    def test_nothing(self):
        place = {'id':12234, 'tags':{}}
        self.assertEqual(self.obj._find_names(place), [])

    def test_name_tag(self):
        place = {'tags': {'name': 'fish'}}
        self.assertEqual(self.obj._find_names(place), ['fish'])

    def test_place_name_tag(self):
        place = {'tags': {'place_name': 'fish'}}
        self.assertEqual(self.obj._find_names(place), ['fish'])

    def test_multiple_names(self):
        place = {'tags': {'name': 'fish', 'place_name': 'dog', 'alt_name': 'horse'}}
        self.assertEqual(self.obj._find_names(place), ['fish', 'dog', 'horse'])

    def test_splitting_names(self):
        place = {'tags': {'name': 'fish; bat', 'place_name': 'dog'}}
        self.assertEqual(self.obj._find_names(place), ['fish', ' bat', 'dog'])


class TestPlaceComparison(unittest.TestCase):
    def setUp(self):
        self.obj = wikipedia_osm_check.WikipediaOSMCheck()

    def test_empty_sets(self):
        missing = self.obj.find_missing([], [])
        self.assertEqual(missing, set([]))

    def test_empty_existing(self):
        places = [
            'tusmore',
            'aston view',
            'smiths'
        ]
        missing = self.obj.find_missing(places, [])
        self.assertEqual(missing, set(places))

    def test_empty_places(self):
        existing = [
            'tusmore',
            'sandford on thames',
            'broughton poggs'
            ]
        missing = self.obj.find_missing([], existing)
        self.assertEqual(missing, set([]))

    def test_missing(self):
        places = [
            'tusmore',
            'aston view',
            'smiths'
        ]
        existing = [
            'tusmore',
            'sandford on thames',
            'broughton poggs',
            'aston view',
            'smiths estate'
        ]
        missing = self.obj.find_missing(places, existing)
        self.assertEqual(missing, set(['smiths']))


class MockWikipediaOSMCheck(wikipedia_osm_check.WikipediaOSMCheck):
    def _request_category(self, category_name):
        return self.mock_data
    def _request_existing(self, region_name):
        return self.mock_data

class TestLoadWikipediaNames(unittest.TestCase):
    def setUp(self):
        self.obj = MockWikipediaOSMCheck()

    def test_loading_names(self):
        self.obj.mock_data = {
            "limits":{"categorymembers":500},
            "query":{"categorymembers":[
                {"ns":0,"title": "Milton-under-Wychwood"},
                {"ns":0,"title": "Tiddington, Oxfordshire"},
                {"ns":0,"title":"Islip, Oxfordshire"},
                {"ns":0,"title":"Hardwick, West Oxfordshire"}
                ]}
            }
        names = self.obj.load_wikipedia_names('Category')
        self.assertEqual(names, ['milton under wychwood', 'tiddington', 'islip', 'hardwick'])

    def test_no_members(self):
        self.obj.mock_data = {
            "limits":{"categorymembers":500},
            "query":{"categorymembers":[
                ]}
            }
        names = self.obj.load_wikipedia_names('Category')
        self.assertEqual(names, [])


class TestLoadOverpassElements(unittest.TestCase):
    def setUp(self):
        self.obj = MockWikipediaOSMCheck()

    def test_load_elements(self):
        self.obj.mock_data = [
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
            },
            {
            "type": "node",
            "id": 2510592,
            "lat": 51.5375786,
            "lon": -0.9050287,
            "tags": {
            "name": "Henley-on-Thames",
            "place": "town"
            }
            },
            {
            "type": "node",
            "id": 5287295,
            "lat": 51.8224193,
            "lon": -1.3175230,
            "tags": {
            "is_in": "Oxfordshire, England, UK",
            "name": "Begbroke",
            "place": "village"
            }
            }]
        out = self.obj.load_existing_names('region')
        expected = ['cart gap', 'henley on thames', 'begbroke']
        self.assertEqual(out, expected)

    def test_no_elements(self):
        self.obj.mock_data = []
        self.assertEqual(self.obj.load_existing_names('region'), [])


class MockRequestWikipediaOSMCheck(wikipedia_osm_check.WikipediaOSMCheck):
    def _request(self, *args, **kwargs):
        return self.mock_data 

class TestRequestExisting(unittest.TestCase):
    def setUp(self):
        self.obj = MockRequestWikipediaOSMCheck()

    def test_request_existing(self):
        self.obj.mock_data = {
              "version": 0.6,
              "generator": "Overpass API",
              "osm3s": {
                "timestamp_osm_base": "2013-04-11T10:39:04Z",
                "timestamp_areas_base": "2013-04-11T04:42:03Z",
                "copyright": "The data included in this document is from www.openstreetmap.org. The data is made available under ODbL."
              },
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
            },
            {
              "type": "node",
              "id": 2510592,
              "lat": 51.5375786,
              "lon": -0.9050287,
              "tags": {
                "name": "Henley-on-Thames",
                "place": "town"
              }
            },
            {
              "type": "node",
              "id": 5287295,
              "lat": 51.8224193,
              "lon": -1.3175230,
              "tags": {
                "is_in": "Oxfordshire, England, UK",
                "name": "Begbroke",
                "place": "village"
              }
            }
            ]}
        out = self.obj._request_existing('Region')
        self.assertEqual(out, self.obj.mock_data['elements'])


class MockRunWikipediaOSMCheck(wikipedia_osm_check.WikipediaOSMCheck):
    def report(self):
        return
    def load_wikipedia_names(self, category_name):
        return self.mock_places
    def load_existing_names(self, region_name, types=None):
        return self.mock_existing


class TestRun(unittest.TestCase):
    def setUp(self):
        self.obj = MockRunWikipediaOSMCheck()

    def test_empty_places(self):
        import sys
        import StringIO

        self.obj.mock_places = []
        out = StringIO.StringIO()
        sys.stdout = out
        self.assertEqual(self.obj.run('category', 'region'), None)
        self.assertEqual(out.getvalue().strip(), "No places found in category")

    def test_empty_existing(self):
        import sys
        import StringIO

        self.obj.mock_places = ['fish', 'dog', 'horse']
        self.obj.mock_existing = []
        out = StringIO.StringIO()
        sys.stdout = out
        self.obj.run('category', 'region')
        self.assertEqual(out.getvalue().strip(), "No existing places found in region")
        self.assertEqual(self.obj.missing, set(self.obj.mock_places))

    def test_run(self):
        self.obj.mock_places = ['fish', 'dog', 'horse']
        self.obj.mock_existing = ['dog']
        self.obj.run('category', 'region')
        self.assertEqual(self.obj.missing, set(['fish', 'horse']))


if __name__ == '__main__':
    unittest.main()
