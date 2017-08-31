<%inherit file="../layout.mako"/>
<div class="content">
    <div class="row">
        <h2>Phase Classification</h2>
        <div class="col-md-12">
            <div class="card">
                <div class="card-header">
                    Trips
                    <select style="width:500px" multiple id="select-trips">
                        %for trip in reversed(trips):
                            <option value="${trip}">${trip}</option>
                        %endfor
                    </select>
                    <button class="btn btn-primary" id="load-phases">Load</button>
                </div>
            </div>
            <div class="card-block">
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
                <div class="row">
                    <div class="col-12" id="stats">
                        <h2>Summary Statistics</h2>

                    </div>
                </div>

            </div>
        </div>
    </div>
</div>
<script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>

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

            var row = new Array(data.ng.length).fill({v:null});
            row[0] = {v:time};
            row[(phase) * 2 + 1] = {v:speed};
##             row[(phase)* 2 + 2] = {v: '<div style="padding: 5px; width: 125px"><b>{0}</b> <br> {1} km/h<br> {2}°</div>'.format(phases[phase], speed, r.angle===undefined?0:r.angle)};

##             console.log(row);
            data.addRow(row);
            trips.add(r['trip_id'] + ' ('+r['vid']+')');
        });

        var options = {
            title: 'Phase Classification for trips '+_.join(Array.from(trips), ', '),
            tooltip: {
              isHtml: true
            },
            explorer: {
                actions: ['dragToZoom', 'rightClickToReset'],
                axis: 'horizontal',
                keepInBounds: true,
            },
##             hAxis: {title: 'Time', minValue: readings[0].timestamp['$date'] / 1000},
            vAxis: {title: 'Speed', minValue: 0, maxValue: 80},
            legend: 'right',
            colors: ['#212121', '#009688','#D81B60', '#5E35B1', '#E53935', '#43A047']
        };

        var chart = new google.visualization.ScatterChart(document.getElementById('chart_div'));

        chart.draw(data, options);
    }

    $(document).ready(function () {
        $('select').select2();
        $('#load-phases').click(function () {
            $.post('/report/phase', {'trips': $('select').val()}, function (data) {
                $summs = $('#stats');
                _.forEach(data.summary, function(val, key) {
                    $summs.append("<b>{}: </b> {}<br>".format(key, val));
                });
                drawChart(data['readings']);
            })
        });
    });
</script>