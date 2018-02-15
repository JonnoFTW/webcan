<%inherit file="../layout.mako"/>
<div class="content">
    <div class="row">
        <h2>Phase Classification</h2>
        <div class="col-md-12">
            <div class="card">
                <div class="card-header">
                    Generate Phase Classification Report
                </div>

                <div class="card-body">
                    <div class="row">
                        <div class="col-6">
                            <!-- Selections -->

                            <input type="hidden" name="map-hull" id="map-hull"/>
                            <div class="form-group col-12">
                                <label for="select-trips" class="col-12 col-form-label">Trips</label>
                                <select style="width:500px" multiple id="select-trips">
                                    %for trip in reversed(trips):
                                        <option value="${trip}">${trip}</option>
                                    %endfor
                                </select>
                            </div>
                            <div class="form-group col-12">
                                <label for="select-vids" class="col-12 col-form-label">Vehicles</label>
                                <select style="width:500px" multiple id="select-vids">
                                    %for d in devices:
                                        <option value="${d['name']}">${d['name']}</option>
                                    %endfor
                                </select>
                            </div>
                            <div class="form-group col-12">
                                <label for="min-phase-seconds" class="col-12 col-form-label">Minimum Phase Duration
                                    (seconds)</label> <input type="number" name="min-phase-seconds"
                                                             id="min-phase-seconds" value="2" class="form-control"/>

                            </div>
                            <div class="form-group col-12">
                                <label for="cruise-window" class="col-12 col-form-label">Cruise Window</label>
                                <input type="number" name="cruise-window"
                                                             id="cruise-window" value="1" class="form-control"/>

                            </div>
                            <div class="form-group col-12" id="load-button">
                                <button class="btn btn-primary" id="load-phases">Load</button>
                                <i id="load-icon" class="fa fa-refresh fa-spin fa-fw" style="display:none"></i>
                            </div>
                            <div class="col-12">
                                <% import re %>
                                ${re.sub(r'(\d+\.)', r'<br>\1', docs)|n}
                            </div>
                        </div>
                        <div class="col-6">
                            <label class="control-label" for="area">
                                <i class="fa fa-globe" aria-hidden="true"></i> Map Area
                                (Select points)</label>
                            <div style="height:400px" id="map" data-markers="10"></div>
                        </div>
                    </div>

                    <div class="row">

                        <div class="col-12" id="chart_dash">
                            <div id="chart_div" style="height: 600px;width:100%"></div>
                            <div id="chart_ctrl" style="height: 100px;width:100%"></div>
                        </div>
                    </div>
                    <div id="stat-tables" class="row">

                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
<script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>
<script type="application/javascript"
        src="https://rawgit.com/brian3kb/graham_scan_js/master/graham_scan.min.js"></script>
<script type="text/javascript">
    google.charts.load('current', {'packages': ['corechart', 'controls', 'table', 'gauge',]});

    var _phases = ['Idle', 'Acc from zero', 'Cruise', 'Dec to zero', 'Int Acc', 'Int Dec', 'N/A'];
    var cng_phases = ['Idle', 'Acc from zero', 'Cruise', 'Dec to zero', 'Int Acc', 'Int Dec', 'N/A', 'Match', 'No Match'];
    var speed_field = null;

    function drawChart(readings) {
        var data = new google.visualization.DataTable();
        var phases;
        if (_.has(readings[0], '__phase')) {
            phases = cng_phases;
        } else {
            phases = _phases;
        }
        data.addColumn('datetime', 'time', 'Time');
        for (var i = 0; i < phases.length; i++) {
            data.addColumn('number', 'Phase ' + i, 'speed_' + i);
            data.addColumn({type: 'string', role: 'tooltip', 'p': {'html': true}})
        }
        var phase_colours = ['#212121', '#009688', '#D81B60', '#5E35B1', '#DCE775', '#43A047', '#616161', '#009688', '#D81B60'];

        var rows = [];
        var trips = new Set();

        _.map(readings, function (r) {
            var phase = r['phase'],
                    time = new Date(r.timestamp.$date),
                    speed = r[speed_field];

            var row = new Array(data.ng.length).fill({v: null});
            row[0] = {v: time};
            row[(phase) * 2 + 1] = {v: speed};
            row[(phase) * 2 + 2] = {
                v: '<div style="padding: 5px; width: 125px"><b>{0} ({2})</b><br> {1} km/h ({3})<br>Avg: {4}<br>Std: {5}<br>Spd-Avg: {6}</div>'
                        .format(phases[phase], speed, phase, r['idx'], r['_avg_spd'], r['_std_spd'], Math.round(Math.abs(speed-r['_avg_spd'])), 2)
            };

            ##             console.log(row);
            if (_.has(r, '__phase_type')) {
                var tt = {v: '<div style="padding: 5px; width: 125px">Old Phase: {0}<br>New Phase: {1}<br>Idx: {2}</div>'.format(r['__phase_type'], r['phase'], r['idx'])};
                var p_idx = r['phase'] === r['__phase_type'] ? 7 : 8;
                row[p_idx * 2 + 1] = {v: -10};
                row[p_idx * 2 + 2] = tt;

            }
            data.addRow(row);
            trips.add(r['trip_id'] + ' (' + r['vid'] + ')');
        });

        var control = new google.visualization.ControlWrapper({
            'controlType': 'ChartRangeFilter',

            'containerId': 'chart_ctrl',
            'options': {
                // Filter by the date axis.
                'filterColumnIndex': 0,
                'ui': {
                    'chartType': 'ScatterChart',
                    'chartOptions': {
                        'chartArea': {'width': '90%'},
                        pointSize: 3,
                        colors: phase_colours,
                        'hAxis': {'baselineColor': 'none'}
                    },
                    ##  'chartView': {
                     ##      'columns': [0, 1,2,3,4,5,6]
                     ##  },
                    // 1 day in milliseconds = 24 * 60 * 60 * 1000 = 86,400,000
                    'minRangeSize': 30 * 1000
                }
            },
            // Initial range: 2012-02-09 to 2012-03-20.
            ##  'state': {
            ##      'range': {
            ##          'start': new Date(readings[0].timestamp.$date),
            ##          'end': new Date(readings[readings.length - 1].timestamp.$date)
            ##      }
            ##  }
        });

        var chart = new google.visualization.ChartWrapper({
            chartType: 'ScatterChart',
            containerId: 'chart_div',
            options: {
                title: 'Phase Classification for trips ' + _.join(Array.from(trips), ', '),
                tooltip: {
                    isHtml: true
                },
                pointSize: 3,
                explorer: {
                    actions: ['dragToZoom', 'rightClickToReset'],
                    axis: 'horizontal',
                    keepInBounds: true,
                    maxZoomIn: 0
                },
                ##             hAxis: {title: 'Time', minValue: readings[0].timestamp['$date'] / 1000},
                vAxis: {title: 'Speed', minValue: 0, maxValue: 80},
                legend: 'right',

                colors: phase_colours
            },
            ##  view: {
            ##      columns: [0,1,2,3,4,5,6]
            ##  }
        });
        var dashboard = new google.visualization.Dashboard(document.getElementById('chart_dash'));
        ##  chart.draw(data, options);
         dashboard.bind(control, chart);
        dashboard.draw(data);
        google.visualization.events.addListener(chart, 'statechange', function (a) {
            // set the control to use the updated bounds
            console.log(a);

            ##  control.setView();
        });
    }

    $(document).ready(function () {
        $('select').select2({allowClear: true, placeholder: 'Leave blank to ignore field'});
        <%include file="../export_map.js"/>
        $('#load-phases').click(function () {
            $('#load-icon').show();
            $('.alert').alert('close');
            $.post('/report/phase', {
                'trips': $('#select-trips').val(),
                'devices': $('#select-vids').val(),
                'hull': $('#map-hull').val(),
                'min-phase-seconds': $('#min-phase-seconds').val(),
                'cruise-window': $('#cruise-window').val()
            }, function (data) {
                var $stat_tables = $('#stat-tables');
                $stat_tables.empty();
                speed_field = data.speed_field;
                _.forEach(data.summary, function (thing_stats, stat_type) {
                    if (stat_type.startsWith('_')) {
                        return;
                    }
                    var heads = [];
                    var rows = [];
                    _.forEach(thing_stats, function (stat_obj, stat_title) {
                        var islink = stat_title;
                        if (stat_type === "Trips") {
                            var vid = data.summary._vid_trips[stat_title];
                            islink = "<a href='/dev/{0}#{1}'>{1}</a>".format(vid, stat_title);
                        } else if (stat_type === "Vehicles") {
                            islink = "<a href=\"/dev/{0}\">{0}</a>".format(stat_title);
                        }
                        var row = "<th scope=\"row\" class=\"col-md-3\">{}</th>".format(islink);
                        heads = _.keys(stat_obj);
                        _.forEach(stat_obj, function (stat_value, stat_name) {
                            row += "<td>{0}</td>".format(stat_value);
                            ##                             $summs.append("<b>{}: </b> {}<br>".format(stat_name, stat_value));
                        });
                        rows.push("<tr>{}</tr>".format(row));
                    });
                    var headers = _.join(_.map(_.concat([stat_type + " ID"], heads), function (x) {
                        return "<th>{}</th>".format(x);
                    }), '');

                    var templ = (
                            "<div class=\"col-12\" id=\"{0}-stats\">\n" +
                            "    <h3>{0} Statistics</h3>\n" +
                            "    <table class=\"table table-bordered table-striped\">\n" +
                            "        <thead class=\"thead-dark\">\n" +
                            "        <tr>{2}</tr>\n" +
                            "        </thead>\n" +
                            "        <tbody id=\"{0}-table\">{1}</tbody>\n" +
                            "    </table>\n" +
                            "</div>").format(stat_type, _.join(rows, ''), headers);
                    ##                     console.log(templ);
                    $stat_tables.append(templ);

                });
                drawChart(data['readings']);

            }).fail(function (err, text) {
                //
                console.log(err, text);
                $('#load-button').append(
                        '<div class="alert alert-danger" role="alert">\n' +
                        '  <strong>Error</strong> {}.\n'.format(text) +
                        '</div>');
                $('.alert').alert();
            }).always(function () {
                $('#load-icon').hide();
            });
        });
    });
</script>