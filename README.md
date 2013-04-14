wikipedia-osm-check
===================

Checks entries in a given Wikipedia category against existing places in OpenStreetMap.

This is a simple python script that takes a Wikipedia category and a region
(as recognised by Overpass) and returns a list of places that are present
in the Wikipedia category but not in OpenStreetMap (within the region).

```bash
$ ./wikipedia_osm_check.py Category:Hamlets_in_Oxfordshire Oxfordshire
```

You can limit the types of place (village, town etc.) that are checked against in OpenStreetMap using the types option:

```bash
$ ./wikipedia_osm_check.py -t village Category:Villages_in_Oxfordshire Oxfordshire
```

The script lists its dependancies in the requirements.txt file, as is the fashion. It depends
on the requests library, to make my life easier, and it will also be quicker if you install simplejson.

Limitations
===========
* Categories are looked up using the English language Wikipedia.
* Regions are limited to those recognised by the OSM Overpass API
* Place name comparison is quite naïve
* Does not authenticate with Wikipedia, so limited to 500 entries in a category

