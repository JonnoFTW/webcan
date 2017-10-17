<%inherit file="layout.mako"/>
<div class="content">
    <h1>Device: ${device}</h1>
    <div class="row">
        <div class="col-md-12">
            <div class="card">
                <div class="card-header">
                    <i class="fa fa-info fa-fw"></i> Map
                    <select class="form-control" id="select-trip">
                        %for t in trips:
                            <option value="${t}">${t}</option>
                        %endfor
                    </select>
                    <div class="float-right" id="csv-link"></div>
                </div>
                <div style="width:100%; height:800px" id="map"></div>
                <div class="col-12">
                    <div class="box">
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
<script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>
<script type="text/javascript">
    var map = null;

    var do_chart = function () {
        var readings = mReadings;
        var data = new google.visualization.DataTable();
        data.addColumn('datetime', 'Time');
        var vaxes = {};
        var series = {};
        var fields_using = $('#select-y').val();
        _.forEach(fields_using, function (v, idx) {
            data.addColumn('number', v);

            vaxes[idx] = {title: v};
            if (idx >1)
                vaxes[idx].textPosition=  'in';
            series[idx] = {targetAxisIndex: idx};

        });
        var fields = {};
        _.forEach(readings, function (v) {
            var row = [new Date(v.timestamp)];
            _.forEach(fields_using, function (f) {
                row.push(v[f]);
            });
            data.addRow(row);
            _.each(v, function (value, key) {
                fields[key] = 1;
            });
        });
        // set all the fields in
        $('#select-y').select2({
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
        console.log("Loading trip:", trip_id)
        window.location.hash = '#{}'.format(trip_id);
        $('#csv-link').html('<i class="fa fa-spinner fa-pulse fa-fw"></i>\n' +
                '<span class="sr-only">Loading...</span>');
        if (!trip_id) {
            return;
        }
        $.getJSON("/trip/{}.json".format(trip_id), function (readings) {
            if (readings.readings.length === 0) {
                $('#csv-link').html('No data!');
                return;
            }
            map.removeMarkers();
            readings.readings = show_path(readings.readings);

            $('#csv-link').html('<a class="btn btn-sm btn-outline-primary" href="/trip/{}.csv">Get {}.csv</a>'.format(trip_id, trip_id));
            if (readings.readings.length > 0)
                map.setCenter(readings.readings[0].lat, readings.readings[0].lng);
            mReadings = readings.readings;
            do_chart();
        });
    };
    $(document).ready(function () {
        google.charts.load('current', {'packages': ['corechart']});
        map = new GMaps({
            div: '#map',
            lat: lat,
            lng: lng,
            zoom: 16
        });
        $sel = $('#select-trip');
        $sel.select2({
            width: '340px'
        }).on('select2:select', function (evt) {
            load_trip($(this).val());
        });
        $('#select-y').select2().on('select2:select select2:unselect', function (evt) {
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
    });

</script>