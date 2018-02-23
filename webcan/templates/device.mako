<%inherit file="layout.mako"/>
<div class="content">
    <h1>Device: ${device}</h1>
    <div class="row">
        <div class="col-md-12">
            <div class="card">
                <div class="card-header">
                    <form class="form-inline">
                        <i class="fa fa-info fa-fw"></i> Map
                        <div class="input-group mb-3 mr-sm-2 mb-sm-0">
                            <select class="form-control" id="select-trip">
                                %for t in trips:
                                    <option value="${t}">${t}</option>
                                %endfor
                            </select>
                        </div>
                        <label for="time_diff">Time Diff </label>
                        <input class="form-control col-1" placeholder="Diff" name="time_diff" value="1.0"
                               id="time_diff"
                               type="number"
                               step="0.5"/>
                        <div class="text-right float-right pull-right col" id="phase-report-link"></div>
                        <div class="text-right float-right pull-right col" id="csv-link"></div>
                    </form>

                </div>
                <div style="width:100%; height:800px" id="map"></div>
                <div class="col-12">

                    <div class="box">
                        <label for="select-x">X Axis</label>
                        <select class="form-control" id="select-x">
                            <option selected>datetime</option>
                        </select>
                        <label for="select-y">Y Axis</label>
                        <select class="form-control" multiple id="select-y">
                            <option selected>spd_over_grnd</option>
                        </select>
                        <div id="chart" style="width: 100%; height: 800px"></div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
<%include file="show_device_path.mako"/>
<script type="text/javascript"
        src="https://cdn.rawgit.com/englercj/jquery-ajax-progress/fd98e923/js/jquery.ajax-progress.js"></script>
<script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>
<script type="text/javascript">
    var map = null;

    var do_chart = function () {
        var readings = mReadings;
        var data = new google.visualization.DataTable();
        var $selx = $("#select-x");
        var tsXaxis = true;
        if ($selx.val() === "datetime") {
            data.addColumn('datetime', 'Time');
        } else {
            tsXaxis = false;
            data.addColumn('number', $selx.val())
        }

        var vaxes = {};
        var series = {};
        var $sely = $('#select-y');
        var fields_using = $sely.val();
        _.forEach(fields_using, function (v, idx) {
            data.addColumn('number', v);

            vaxes[idx] = {title: v};
            if (idx > 1)
                vaxes[idx].textPosition = 'in';
            series[idx] = {targetAxisIndex: idx};

        });
        var fields = {};
        _.forEach(readings, function (v) {

            var row = [];
            if (tsXaxis)
                row.push(new Date(v.timestamp));
            else
                row.push(v[$selx.val()]);
            _.forEach(fields_using, function (f) {
                row.push(v[f]);
            });
            data.addRow(row);
            _.each(v, function (value, key) {
                fields[key] = 1;
            });
        });
        // set all the fields in
        $selx.select2({
            data: _.keys(fields)
        });
        $sely.select2({
            data: _.keys(fields)
        });
        var title = _.join(fields_using, ', ');
        var options = {
            title: title + ' vs. Time',
            curveType: 'function',
            animation: {
                duration: 100,
                startup: true
            },
            chartArea: {
                width: '95%',
                height: '100%',
                top: 72,
                left: 60,
                bottom: 48,
                right: 84
            },
            vAxes: vaxes,
            series: series,
            explorer: {
                actions: ['dragToZoom', 'rightClickToReset'],
                axis: 'horizontal',
                keepInBounds: true,
                maxZoomIn: 0
            },
            legend: {position: 'top'}
        };

        var chart = new google.visualization.LineChart(document.getElementById('chart'));
        chart.draw(data, options);
    };
    var mReadings = null;
    var load_trip = function (trip_id) {
        console.log("Loading trip:", trip_id);
        window.location.hash = '#{}'.format(trip_id);
        var $csvlink = $('#csv-link');
        if (!trip_id) {
            $csvlink.html('No Data for this vehicle');
            return;
        }
        $csvlink.html('<i class="fa fa-spinner fa-pulse fa-fw"></i>\n' +
                '<span class="sr-only">Loading...</span>');

        $.ajax({
            type: 'GET',
            dataType: 'json',
            data: {'time_diff': $('#time_diff').val()},
            url: "/trip/{}.json".format(trip_id),
            progress: function (e) {
                //make sure we can compute the length
                if (e.lengthComputable) {
                    //calculate the percentage loaded
                    var pct = (e.loaded / e.total) * 100;

                    //log percentage loaded
                    console.log(pct);
                }
                //this usually happens when Content-Length isn't set
                else {
                    console.warn('Content Length not reported!');
                }
            },
            success: function (readings) {
                if (readings.readings.length === 0) {
                    $csvlink.html('No data!');
                    return;
                }
                $('#phase-report-link').html('<a class="btn btn-sm btn-outline-secondary" href="/report/phase?trip_id={}">Phase Report</a>'.format(trip_id));
                $csvlink.html('<a class="btn btn-sm btn-outline-primary" href="/trip/{}.csv">Get {}.csv</a>'.format(trip_id, trip_id));
                map.removeMarkers();
                readings.readings = show_path(readings.readings);

                if (readings.readings.length > 0)
                    map.setCenter(readings.readings[0].lat, readings.readings[0].lng);
                mReadings = readings.readings;
                do_chart();
            }
        });
        ##                 $.getJSON("/trip/{}.json".format(trip_id), function (readings) {);
    };
    $(document).ready(function () {
        google.charts.load('current', {
            'packages': ['corechart'], 'callback': function () {
                map = new GMaps({
                    div: '#map',
                    lat: lat,
                    lng: lng,
                    zoom: 16
                });
                var $sel = $('#select-trip');
                $sel.select2({
                    width: '340px'
                }).on('select2:select', function (evt) {
                    load_trip($(this).val());
                });
                $('#select-y, #select-x').select2().on('select2:select select2:unselect', function (evt) {
                    do_chart();
                });
                $('.map-load').click(function () {
                    load_trip($(this).data('trip'));
                });
                if (window.location.hash !== "") {
                    // load up that
                    var trip_id = window.location.hash.substr(1);
                    $sel.val(trip_id).trigger('select2:select');
                } else {
                    load_trip($sel.val());
                }
            }
        });

    });

</script>