import configparser
import xml.sax, xml.sax.handler
from pymongo import MongoClient
from zipfile import ZipFile


class PlacemarkHandler(xml.sax.handler.ContentHandler):
    def __init__(self):
        self.inName = False  # handle XML parser events
        self.inPlacemark = False
        self.mapping = {}
        self.buffer = ""
        self.name_tag = ""

    def startElement(self, name, attributes):
        if name == "Placemark":  # on start Placemark tag
            self.inPlacemark = True
            self.buffer = ""
        if self.inPlacemark:
            if name == "name":  # on start title tag
                self.inName = True  # save name text to follow

    def characters(self, data):
        if self.inPlacemark:  # on text within tag
            self.buffer += data  # save text if in title

    def endElement(self, name):
        self.buffer = self.buffer.strip('\n\t')

        if name == "Placemark":
            self.inPlacemark = False
            self.name_tag = ""  # clear current name

        elif name == "name" and self.inPlacemark:
            self.inName = False  # on end title tag
            self.name_tag = self.buffer.strip()
            self.mapping[self.name_tag] = {}
        elif self.inPlacemark:
            if name in self.mapping[self.name_tag]:
                self.mapping[self.name_tag][name] += self.buffer
            else:
                self.mapping[self.name_tag][name] = self.buffer
        self.buffer = ""


if __name__ == "__main__":
    conf = configparser.ConfigParser()
    conf.read('../../development.ini')
    uri = conf['app:webcan']['mongo_uri']

    polys = MongoClient(uri)['webcan']['polygons']

    kmz = ZipFile('/scratch/shapes/Depots and Service Centres.kmz', 'r')
    kml = kmz.open('doc.kml', 'r')
    parser = xml.sax.make_parser()
    handler = PlacemarkHandler()
    parser.setContentHandler(handler)
    parser.parse(kml)
    kmz.close()
    for k, v in handler.mapping.items():
        print(k)
        points = [[float(y) for y in x.split(',')[:2]] for x in v['coordinates'].strip().split(' ')]

        polys.insert_one({
            'name': k,
            'exclude': True,
            'poly': {
                'type': "Polygon",
                'coordinates': points
            }
        })
