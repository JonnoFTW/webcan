from bson import json_util
import json
import csv
import shapefile
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED
from datetime import date, time, datetime
import re

try:
    from StringIO import StringIO  # python 2

    BytesIO = StringIO
except ImportError:
    from io import BytesIO, StringIO  # python 3


class BaseRenderer:
    content_type = 'text/html'

    def _set_ct(self, system):
        request = system.get('request')
        if request is not None:
            response = request.response
            ct = response.content_type
            if ct == response.default_content_type:
                response.content_type = self.content_type


class BSONRenderer(BaseRenderer):
    content_type = 'application/json'

    def __init__(self, info):
        """ Constructor: info will be an object having the
        following attributes: name (the renderer name), package
        (the package that was 'current' at the time the
        renderer was registered), type (the renderer type
        name), registry (the current application registry) and
        settings (the deployment settings dictionary). """
        pass

    def __call__(self, value, system):
        self._set_ct(system)
        return json.dumps(value, default=json_util.default, indent=2)


class PyMongoCursorRenderer(BaseRenderer):
    content_type = 'application/json'

    def __init__(self, info):
        pass

    def __call__(self, value, system):
        self._set_ct(system)
        return '[' + (','.join([json.dumps(i, default=json_util.default) for i in value])) + ']'


class CSVRenderer(BaseRenderer):
    content_type = 'text/csv'

    def __init__(self, info):
        pass

    def __call__(self, value, system):
        """ Returns a plain CSV-encoded string with content-type
        ``text/csv``. The content-type may be overridden by
        setting ``request.response.content_type``."""

        self._set_ct(system)

        fout = StringIO()
        writer = csv.DictWriter(fout, fieldnames=value.get('header'), delimiter=',', quotechar='"',
                                quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        writer.writerows(value.get('rows', []))

        return fout.getvalue()


class ShapefileRenderer(BaseRenderer):
    content_type = 'application/zip'

    def __init__(self, info):
        pass

    def __call__(self, data, system):
        self._set_ct(system)
        writer = shapefile.Writer(shapeType=shapefile.POINT)
        writer.autoBalance = 1
        # iterate through the entire dataset and extract the field names
        headers = {}

        pattern = re.compile('[\W_]+')

        def fix_field(k: str):
            return pattern.sub('', k.strip().replace('PID_', '').split(' ')[0])

        for row in data:
            row['date'] = row['timestamp'].date()
            row['time'] = str(row['timestamp'].time())
            del row['timestamp']
            headers.update({fix_field(k): type(v) for k, v in row.items() if v is not None})
        del headers['pos']
        writer.field('latitude', 'N', '32', 15)
        writer.field('longitude', 'N', '32', 15)
        header_map = {
            int: ('N',),
            float: ('N', 7, 3),
            str: ('C', 30),
            date: ('D',),
            time: ('T',),
        }
        for h, t in headers.items():
            writer.field(h, *header_map[t])

        def check_field(f, r):
            if f[0] in r:
                return r[f[0]]
            else:
                return ""

        for row in data:
            row = {fix_field(k): v for k, v in row.items()}
            if 'pos' is None:
                continue
            if 'pos' in row and row['pos'] is not None:
                row['latitude'] = row['pos']['coordinates'][1]
                row['longitude'] = row['pos']['coordinates'][0]
                del row['pos']

            writer.point(row['longitude'], row['latitude'])
            writer.record(*[check_field(f, row) for f in writer.fields])
        dbfout = BytesIO()
        shpout = BytesIO()
        shxout = BytesIO()
        writer.save(shp=shpout, dbf=dbfout, shx=shxout)
        zipout = BytesIO()
        now = datetime.now()
        date_str = 'webcan_export_{}'.format(now.strftime('%Y%m%d_%H%M%S'))
        with ZipFile(zipout, 'w', ZIP_DEFLATED) as myzip:
            for k, v in [('shp', shpout), ('shx', shxout), ('dbf', dbfout)]:
                myzip.writestr(ZipInfo(f'{date_str}.{k}', date_time=now.timetuple()), v.getvalue())
        return zipout.getvalue()
