<%inherit file="../layout.mako"/>
<div class="content">
    <div class="row">
        <h2> Vehicle Fuel Consumption Histogram Report</h2>
        <div class="col-md-12">
            <div class="card">
                <div class="card-header">
                    Vehicle Fuel Consumption Histogram Report
                </div>
                <div class="card-body">
                    <div class="row">
                        <div class="col-6">
                            <div class="form-group col-12">
                                <label for="select-vids" class="col-12 col-form-label">Vehicles</label>
                                <select style="width:500px" id="select-vid" multiple>
                                    %for d in devices:
                                        <option value="${d['name']}">${d['name']}</option>
                                    %endfor
                                </select>
                            </div>
                            <div class="form-group col-12">
                                <label for="min-trip-distance">Minimum Trip Distance (km)</label>
                                <input type="number" step="any" min="0" id="min-trip-distance" name="min-trip-distance"
                                       value="5" class="form-control"/>
                            </div>
                            <div class="form-group col-12" id="load-button">
                                <button class="btn btn-primary" id="load-phases">Load</button>
                                <i id="load-icon" class="fa fa-refresh fa-spin fa-fw" style="display:none"></i>
                            </div>
                        </div>
                        <div class="col-12" id="chart_div" style="height: 900px">

                            ## Histogram of litres per 100km
## Basically just need to json in the fuel consumption of every trip we have, bin width  1

                        </div>
                        <div class="col-12" id="selected-info">

                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
<script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>
<script>
    function drawChart(dataIn) {
        var data = google.visualization.arrayToDataTable(dataIn['table']);
        var title = 'Histogram of Fuel Economy (L/100km)\n';
        _.each(dataIn, function(val, key) {
            if (key === 'table'  || key ==='labels') {
                return;
            }
            title += "{0}: n={1}, std={2} mean={3}\n".format(
                        key, val['n'], val['std'], val['mean']);

        });
        ##  data.addColumn({'type': 'string', 'role': 'tooltip', 'p': {'html': true}});

        var options = {
            title: title,
            interpolateNulls: false,
            ##  legend: {position: 'none'},
            histogram: {
                 bucketSize: 1,
                 minValue: 0,

                 hideBucketItems: false
                 ##  maxValue: 80
             },
            ##  isStacked: true,
            vAxis: {title: 'Count'},
            hAxis: {
                type: 'category',
                title: 'L/100km',
                ##  ticks: _.range(0, 60)
            }
        };

        var chart = new google.visualization.Histogram(document.getElementById('chart_div'));
        google.visualization.events.addListener(chart, 'select', function() {
             var selection = chart.getSelection();
             ##  console.log(selection);
             for (var i = 0; i < selection.length; i++) {
                 console.log(data.getValue(selection[i].row, selection[i].column));
                 var col_lbl = data.getColumnLabel(selection[i].column)
                 var trip_key = dataIn['labels'][col_lbl][selection[i].row];
                console.log(col_lbl, trip_key);
                $.getJSON('/report/trip_summary_info/{}'.format(trip_key), function(d) {
                    var html = '<b>Vehicle:</b> <a href="/dev/{0}">{0}</a><br><b>Trip Key:</b> <a href="/dev/{0}?key={1}">{1}</a><br>'.format(col_lbl, trip_key);
                    _.each(d, function(val, key) {
                        if(_.isObject(val)) {
                            val = moment.unix(val.$date/1000).format();
                        }
                       html += "<b>{0}:</b> {1}<br>".format(key, val);
                    });
                    $('#selected-info').html(html);
                });

             }
        });
        ##  google.visualization.events.addListener(chart, 'onmouseover', function(rc) {
        ##      console.log(data.getValue(rc.row, rc.column-1));
        ##  });
        chart.draw(data, options);
    }

    $(document).ready(function () {

        google.charts.load("current", {packages: ["corechart"]});
        $('select').select2({allowClear: true, placeholder: 'Select vehicles'});
        $('#load-phases').click(function () {
            $('#load-icon').show();
            var $out = $('#output');
            $('.alert').alert('close');
            $out.text('');
            var vehicle_id = $('#select-vid').val();
            $.post('/report/fuel',
                    {'device': vehicle_id,
                    'min_trip_distance': $('#min-trip-distance').val()},
                    function (data) {
                        drawChart(data, vehicle_id);
                    }, 'json').
            fail(function (x, text, err) {
                console.log(x, text, err);
                $('#load-button').append(
                        '<div class="alert alert-danger" role="alert">\n' +
                        '  <strong>Error</strong> {}'.format(x.statusText) +
                        '</div>');
                $('.alert').alert();

            }).always(function () {
                $('#load-icon').hide();
            });
        });
    });


</script>