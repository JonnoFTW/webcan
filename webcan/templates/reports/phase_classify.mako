<%inherit file="../layout.mako"/>
<div class="content">
    <div class="row">
        <h2>Phase Classification</h2>
        <div class="col-md-12">
            <div class="card">
                <div class="card-header">
                    Generate Phase Classification Report
                </div>

                <div class="card-block">
                    <div class="row">
                        <div class="col-6">
                            <!-- Selections -->

                            <input type="hidden" name="map-hull" id="map-hull"/>
                            <div class="form-group col-12">
                                <label for="select-trips" class="col-2 col-form-label">Trips</label>
                                <select  style="width:500px" multiple id="select-trips">
                                    %for trip in reversed(trips):
                                        <option value="${trip}">${trip}</option>
                                    %endfor
                                </select>
                            </div>
                            <div class="form-group col-12">
                                <label for="select-vids" class="col-2 col-form-label">Vehicles</label>
                                <select style="width:500px" multiple id="select-vids">
                                    %for d in devices:
                                        <option value="${d['name']}">${d['name']}</option>
                                    %endfor
                                </select>
                            </div>
                             <div class="form-group col-12">
                                <label for="min-phase-seconds" class="col-12 col-form-label">Minimum Phase Duration (seconds)</label>                <input type="number" name="min-phase-seconds" id="min-phase-seconds" value="5" class="form-control"/>
                                </select>

                            </div>
                            <div class="form-group col-12">
                                <button class="btn btn-primary" id="load-phases">Load</button>
                                 <i id="load-icon" class="fa fa-refresh fa-spin fa-fw" style="display:none"></i>
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
                        <div class="col-3">
                            <% import re %>
                        ${re.sub(r'(\d+\.)', r'<br>\1', docs)|n}
                        </div>
                        <div class="col-9">
                            Speeds
                            <div id="chart_div" style="height: 600px;"></div>
                        </div>
                    </div>
                    <div id="stat-tables" class="row">

                    </div>
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
    google.charts.load('current', {'packages': ['corechart']});
    var phases = ['Idle', 'Acc from zero', 'Cruise', 'Dec to zero', 'Int Acc', 'Int Dec', 'N/A'];

    function drawChart(readings) {
        var data = new google.visualization.DataTable();
        data.addColumn('datetime', 'time', 'Time');
        for (var i = 0; i < phases.length; i++) {
            data.addColumn('number', 'Phase ' + i, 'speed_' + i);
            data.addColumn({type: 'string', role: 'tooltip', 'p': {'html': true}})
        }
        var rows = [];
        var trips = new Set();
        _.map(readings, function (r) {
            var phase = r['phase'],
                ##                 time  = moment.unix(r.timestamp['$date']/1000),
                time = new Date(r.timestamp.$date),
                    speed = r['PID_SPEED (km/h)'];

            var row = new Array(data.ng.length).fill({v: null});
            row[0] = {v: time};
            row[(phase) * 2 + 1] = {v: speed};
            row[(phase)* 2 + 2] = {v: '<div style="padding: 5px; width: 125px"><b>{0} ({2})</b> <br> {1} km/h</div>'.format(phases[phase], speed, phase)};

            ##             console.log(row);
            data.addRow(row);
            trips.add(r['trip_id'] + ' (' + r['vid'] + ')');
        });

        var options = {
            title: 'Phase Classification for trips ' + _.join(Array.from(trips), ', '),
            tooltip: {
                isHtml: true
            },
            explorer: {
                actions: ['dragToZoom', 'rightClickToReset'],
                axis: 'horizontal',
                keepInBounds: true,
                maxZoomIn: 0
            },
            ##             hAxis: {title: 'Time', minValue: readings[0].timestamp['$date'] / 1000},
            vAxis: {title: 'Speed', minValue: 0, maxValue: 80},
            legend: 'right',

            colors: ['#212121', '#009688', '#D81B60', '#5E35B1', '#E53935', '#43A047', '#616161']
        };

        var chart = new google.visualization.ScatterChart(document.getElementById('chart_div'));

        chart.draw(data, options);
    }
    $(document).ready(function () {
        $('select').select2({allowClear: true, placeholder: 'Leave blank to ignore field'});
        <%include file="../export_map.js"/>
        $('#load-phases').click(function () {
            $('#load-icon').toggle();
            $.post('/report/phase', {
                'trips': $('#select-trips').val(),
                'devices': $('#select-vids').val(),
                'hull': $('#map-hull').val(),
                'min-phase-seconds': $('#min-phase-seconds').val()
            }, function (data) {
                $stat_tables = $('#stat-tables');
                $stat_tables.empty();
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
                        } else if(stat_type === "Vehicles") {
                            islink = "<a href=\"/dev/{0}\">{0}</a>".format(stat_title);
                        }
                        var row = "<th scope=\"row\">{}</th>".format(islink);
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
                            "        <thead class=\"thead-inverse\">\n" +
                            "        <tr>{2}</tr>\n" +
                            "        </thead>\n" +
                            "        <tbody id=\"{0}-table\">{1}</tbody>\n" +
                            "    </table>\n" +
                            "</div>").format(stat_type, _.join(rows, ''), headers);
                    ##                     console.log(templ);
                    $stat_tables.append(templ);

                });
                drawChart(data['readings']);
                $('#load-icon').toggle();
            })
        });
    });
</script>