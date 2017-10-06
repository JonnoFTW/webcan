<script>
    var lat = -34.9271532,
            lng = 138.6003676;

    function componentToHex(c) {
        var hex = c.toString(16);
        return hex.length == 1 ? "0" + hex : hex;
    }

    function rgbToHex(r, g, b) {
        return componentToHex(r) + componentToHex(g) + componentToHex(b);
    }

    function Line(x1, y1, x2, y2) {
        this.x1 = x1;
        this.y1 = y1;
        this.x2 = x2;
        this.y2 = y2;
    }

    Line.prototype.drawWithArrowheads = function (ctx) {

        // arbitrary styling
        ctx.strokeStyle = "blue";
        ctx.fillStyle = "blue";
        ctx.lineWidth = 1;

        // draw the line
        ctx.beginPath();
        ctx.moveTo(this.x1, this.y1);
        ctx.lineTo(this.x2, this.y2);
        ctx.stroke();

        // draw the ending arrowhead
        var endRadians = Math.atan((this.y2 - this.y1) / (this.x2 - this.x1));
        endRadians += ((this.x2 > this.x1) ? 90 : -90) * Math.PI / 180;
        this.drawArrowhead(ctx, this.x2, this.y2, endRadians);

    };

    Line.prototype.drawArrowhead = function (ctx, x, y, radians) {
        ctx.save();
        ctx.beginPath();
        ctx.translate(x, y);
        ctx.rotate(radians);
        ctx.moveTo(0, 0);
        ctx.lineTo(5, 20);
        ctx.lineTo(-5, 20);
        ctx.closePath();
        ctx.restore();
        ctx.fill();
    };
    var generateIcon = function (reading) {
        var canvas = document.createElement('canvas');
        var label = String(reading.trip_sequence)
        var width = 32;
        var height = 32;
        canvas.width = width;
        canvas.height = height;
        var midx = width / 2;
        var midy = height / 2;
        var speed = reading['PID_SPEED (km/h)'];
        if (!speed) {
            speed = 0;
        }

        var topSpeed = 80.;
        var bgCol = rgbToHex(Math.floor(Math.min(speed, topSpeed) / topSpeed * 255), 0, 0);
        var textCol = "FFFFFF";
        if (!canvas.getContext)
            return 'http://chart.apis.google.com/chart?chst=d_map_pin_letter&chld={}|{}|{}'.format(label, bgCol, textCol);
        var context = canvas.getContext('2d');
        context.font = "14px Arial";
        context.textBaseline = 'middle';
        context.textAlign = 'center';


        context.beginPath();
        context.arc(midx, midy, midx - 1.5, 0, 2 * Math.PI, false);
        context.fillStyle = "#" + bgCol;
        context.fill();
        context.lineWidth = 3;
        var engine_load = reading['PID_ENGINE_LOAD (%)'];
        if (engine_load === undefined) {
            engine_load = 0;
        } else {
            engine_load = parseInt(engine_load / 100 * 255);
        }
        context.strokeStyle = "#00{}00".format(engine_load.toString(16));
        context.stroke();
        ##         context.endPath();

        ##         var course = reading['true_course'];
        ##         if (course) {
        ##             // put an arrow on there or something...
        ##             var courseRad = (((course % 360)) * (Math.PI/180)) - Math.PI/2;
        ##             var tox = midx+midx*Math.cos(courseRad),
        ##                 toy = midy+midy*Math.sin(courseRad);
        ##             var line = new Line(midx, midy, tox,toy);
        ##             line.drawWithArrowheads(context);
        ##         }
        context.fillStyle = "#" + textCol;
        context.fillText(label, width / 2, height / 2);
        return canvas.toDataURL();
    };
    var show_path = function (readings) {
        var last = null;
        var markers = [];
        var out = [];
        _.forEach(readings, function (reading) {
            var tooltip = "<h5>Reading {}</h5>".format(reading.trip_sequence);
            if (_.has(reading, 'latitude')) {
                reading.lat = reading.latitude;
                reading.lng = reading.longitude;
            } else if(_.has(reading, 'pos')){
                reading.lat = reading.pos.coordinates[1];
                reading.lng = reading.pos.coordinates[0];
            } else {
                return;
            }
            if(reading.lat == 0 && reading.lng == 0) {
                return;
            }
            out.push(reading);
            reading.timestamp = moment.unix(reading.timestamp['$date'] / 1000);
            if (last !== null) {
                reading.time_diff = "{}s".format(reading.timestamp.diff(last.timestamp, 'seconds', true));
            }
            last = reading;
            delete reading.pos;
            var fields = _.keys(reading).sort().reverse();
            _.forEach(fields, function (k) {
                var v = reading[k];
                if (v === null || k === "trip_id") {
                    return;
                }
                var suffix = "";
                if (_.startsWith(k, 'PID_')) {
                    suffix = _.last(k.split(" "));
                    k = _.first(k.substr(4).split(" "));
                }
                if (k === "pos") {
                    v = "lat={} lng={}".format(v.lat, v.lng);
                }

                tooltip += "<b>{}: </b> {} {}<br>".format(k, v, suffix);
            });
            markers.push({
                lat: reading.lat,
                lng: reading.lng,
                icon: generateIcon(reading),
                infoWindow: {
                    content: tooltip
                }
            });
        });
        map.addMarkers(markers);
        return out;
    }
</script>