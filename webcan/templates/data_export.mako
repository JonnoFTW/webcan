<%inherit file="layout.mako"/>
<div class="content">
    <h1>Data Export</h1>
    <div class="row">
        <div class="col-md-12">
            <div class="card">
                <div class="card-header">
                    <i class="fa fa-info fa-fw"></i> Export
                </div>
                <div class="card-block">
                    <form action="/export" method="post" id="export-form" class="form-horizontal">
                        <fieldset>
                            <!-- Form Name -->
                            <input type="hidden" name="map-hull" id="map-hull"/>
                            <div class="row">
                                <div class="col-md-6">
                                    <!-- Prepended checkbox -->
                                    <div class="form-group">
                                        <label class="control-label" for="prependedcheckbox"><i
                                                class="glyphicon glyphicon-calendar fa fa-calendar"></i> Date Range
                                        </label>
                                        <div class="input-group">
                                            <input id="dateinput" name="daterange" class="form-control">
                                        </div>
                                    </div>

                                    <!-- Select Multiple -->
                                    <div class="form-group">
                                        <label class="control-label" for="selectDevices"><i class="fa fa-car"
                                                                                            aria-hidden="true"></i>
                                            Devices</label>
                                        <select id="selectDevices" name="selectDevices" class="form-control"
                                                multiple="multiple">
                                            %for d in devices:
                                                <option value="${d['name']}">${d['name']}</option>
                                            %endfor
                                        </select>
                                    </div>

                                    <!-- Select Multiple -->
                                    <div class="form-group">
                                        <label class="control-label" for="selectTrips"><i class="fa fa-map"
                                                                                          aria-hidden="true"></i> Trips</label>
                                        <select id="selectTrips" name="selectTrips" class="form-control"
                                                multiple="multiple">
                                            %for t in trips:
                                                <option value="${t}">${t}</option>
                                            %endfor
                                        </select>
                                    </div>


                                    <!-- Select Basic -->
                                    <div class="form-group">
                                        <label class="control-label" for="selectFormat"><i class="fa fa-file-archive-o"
                                                                                           aria-hidden="true"></i> Data
                                            Format</label>
                                        <select id="selectFormat" name="selectFormat" class="form-control">
                                            <option value="shp">Shapefile</option>
                                            <option value="json">JSON</option>
                                            <option value="csv">CSV</option>
                                        </select>
                                    </div>
                                    %if context.get('detail', None):
                                        <div class="form-group">
                                            <div class="alert alert-danger" role="alert">
                                                <strong>Error</strong> ${detail}
                                            </div>
                                        </div>
                                    %endif
                                    <!-- Button -->
                                    <div class="form-group">
                                        <button id="download" name="download" class="btn btn-primary">Download
                                        </button>
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="form-group">
                                        <label class="control-label" for="area"><i class="fa fa-globe"
                                                                                   aria-hidden="true"></i> Map Area
                                            (Select 4 points)</label>
                                        <div style="height:400px" id="map"></div>
                                    </div>
                                </div>
                            </div>
                        </fieldset>
                    </form>
                </div>
            </div>
        </div>
    </div>
</div>
<script type="application/javascript"
        src="https://rawgit.com/brian3kb/graham_scan_js/master/graham_scan.min.js"></script>
<script src="//cdnjs.cloudflare.com/ajax/libs/bootstrap-daterangepicker/2.1.25/daterangepicker.min.js"></script>
<script type="text/javascript">
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
    $(document).ready(function () {
        $('#selectTrips').select2({
            placeholder: 'All trips matching devices date range',
            ajax: {
                url: '/dev_trips',
                dataType: 'json',
                data: function (params) {
                    return {devices: $('#selectDevices').val()}
                },
                processResults: function (d, params) {
                    return {
                        results: _.map(d.trips, function (v) {
                            return {
                                id: v.trip_id,
                                text: v.vid + " " + v.trip_id
                            }
                        })
                    }
                }
            }
        });
        $('#selectDevices').select2({
            placeholder: 'All data in date range'
        }).on('change', function (e) {
            // trigger the ajax trigger on selectTrips
            $('#selectTrips').change();
        });
        var map = new GMaps({
            div: '#map',
            lat: lat,
            lng: lng,
            zoom: 13,
            click: function (e) {
                marker_count++;
                crash_area.push(map.addMarker({
                    lat: e.latLng.lat(),
                    lng: e.latLng.lng(),
                    icon: generateIcon((marker_count % 4) + 1, '000000')
                }));
                if (crash_area.length > 4) {
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
                if (crash_area.length >= 4) {
                    // get the crashes in that area!
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
        $('input#dateinput').daterangepicker({
            timePicker: true,
            timePickerIncrement: 10,
            autoUpdateInput: false,
            autoapply: true,
            locale: {
                format: 'DD/MM/YYYY h:mm A'
            }
        }).on('apply.daterangepicker', function (ev, picker) {
            $(this).val(picker.startDate.format(picker.locale.format) + ' - ' + picker.endDate.format(picker.locale.format));
        }).on('cancel.daterangepicker', function (ev, picker) {
            $(this).val('');
        }).attr('placeholder', 'All dates');
    });
</script>

