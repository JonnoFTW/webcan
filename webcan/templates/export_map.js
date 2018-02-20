var generateIcon = function (label, bgCol) {
    var canvas = document.createElement('canvas');
    var width = 40;
    var height = 42;
    canvas.width = width;
    canvas.height = height;
    var textCol = "FFFFFF";
    if (!canvas.getContext)
        return 'http://chart.apis.google.com/chart?chst=d_map_pin_letter&chld={}|{}|{}'.format(label, bgCol, textCol);
    var context = canvas.getContext('2d');
    context.font = "15px Arial";
    context.textBaseline = 'middle';
    context.textAlign = 'center';
    context.beginPath();
    context.arc(width / 2, height / 2, width / 2, 0, 2 * Math.PI, false);
    context.fillStyle = "#" + bgCol;
    context.fill();
    context.lineWidth = 2;
    context.strokeStyle = "#FFFFFF";
    context.stroke();
    // context.endPath();

    context.fillStyle = "#" + textCol;
    context.fillText(label, width / 2, height / 2);
    return canvas.toDataURL();
};

var lat = -35.00803010577838,
    lng = 138.57349634170532;
var crash_area = [];
var marker_count = -1;
var total_markers = parseInt($('#map').data('markers'));
var map = new GMaps({
    div: '#map',
    clickableIcons: false,
    lat: lat,
    lng: lng,
    zoom: 13,
    click: function (e) {
        marker_count++;
        crash_area.push(map.addMarker({
            lat: e.latLng.lat(),
            lng: e.latLng.lng(),
            icon: generateIcon((marker_count % total_markers) + 1, '000000')
        }));
        if (crash_area.length > total_markers) {
            map.removeMarker(crash_area.shift());

        }
        var paths = _.map(crash_area, function (marker) {
            return marker.position
        });

        var convexHull = new ConvexHullGrahamScan();
        _(paths).forEach(function (v) {
            convexHull.addPoint(v.lng(), v.lat());
        });
        var hull = _.map(convexHull.getHull(), function (pos) {
            return [pos.x, pos.y]
        });
        var latlngs = _.map(hull, function (pos) {
            return new google.maps.LatLng(pos[1], pos[0])
        });
        crash_polygon.setPaths(latlngs);
        if (crash_area.length >= total_markers) {
            console.log(hull);
            $('#map-hull').val(_.join(hull))

        }
    }
});
var crash_polygon = map.drawPolygon({
    paths: [[0, 0], [0, 0], [0, 0], [0, 0]],
    strokeColor: '#BBD8E9',
    strokeOpacity: 1,
    strokeWeight: 3,
    fillColor: '#BBD8E9',
    fillOpacity: 0.6
});
CanvasRenderingContext2D.prototype.roundRect = function (x, y, width, height, radius, fill, stroke) {
    var cornerRadius = {upperLeft: 0, upperRight: 0, lowerLeft: 0, lowerRight: 0};
    if (typeof stroke === "undefined") {
        stroke = true;
    }
    if (typeof radius === "object") {
        for (var side in radius) {
            cornerRadius[side] = radius[side];
        }
    }

    this.beginPath();
    this.moveTo(x + cornerRadius.upperLeft, y);
    this.lineTo(x + width - cornerRadius.upperRight, y);
    this.quadraticCurveTo(x + width, y, x + width, y + cornerRadius.upperRight);
    this.lineTo(x + width, y + height - cornerRadius.lowerRight);
    this.quadraticCurveTo(x + width, y + height, x + width - cornerRadius.lowerRight, y + height);
    this.lineTo(x + cornerRadius.lowerLeft, y + height);
    this.quadraticCurveTo(x, y + height, x, y + height - cornerRadius.lowerLeft);
    this.lineTo(x, y + cornerRadius.upperLeft);
    this.quadraticCurveTo(x, y, x + cornerRadius.upperLeft, y);
    this.closePath();
    if (stroke) {
        this.stroke();
    }
    if (fill) {
        this.fill();
    }
};