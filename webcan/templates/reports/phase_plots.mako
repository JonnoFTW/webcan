<%inherit file="../layout.mako"/>
<div class="content">
    <div class="row">
        <h2>Phase Plots</h2>
        <div class="col-md-12">
            <div class="card">
                <div class="card-header">
                    Vehicle Phase Plots
                </div>
                <div class="card-body">
                    <div class="row">
                        <div class="col-12">
                            <p>
                                Select your vehicle(s), phase type(s), x value, y value and a scatter plot will be
                                generated. You can change x,y axis after loading
                            </p>
                        </div>
                        <div class="col-6">
                            <div class="form-group col-12">
                                <label for="select-vids" class="col-12 col-form-label">Vehicles</label>
                                <select style="width:500px" id="select-vid">
                                    %for d in devices:
                                        <option value="${d['name']}">${d['name']}</option>
                                    %endfor
                                </select>
                            </div>
                            <div class="form-group col-12">
                                <label for="select-phase" class="col-12 col-form-label">Phases</label>
                                <select style="width:500px" multiple id="select-phase">
                                    %for d in range(0,6):
                                        <option value="${d}">${d}</option>
                                    %endfor
                                </select>
                            </div>
                            <div class="form-check col-12">
                                <label class="form-check-label">
                                    <input class="form-check-input" name="remove-0" id="checkbox-0" type="checkbox"
                                           value="">
                                    Remove phases where y=0
                                </label>
                                <label class="form-check-label">
                                    <input class="form-check-input" name="lines-only" id="checkbox-trendsonly"
                                           type="checkbox" value="">
                                    Trendlines only (useful for comparing vehicles)
                                </label>
                            </div>
                            <div class="form-group col-12" id="load-button">
                                <button class="btn btn-primary" id="load-phases">Load</button>
                                <i id="load-icon" class="fa fa-refresh fa-spin fa-fw" style="display:none"></i>
                            </div>
                        </div>
                        <div class="col-6">
                            <div class="form-group col-12">
                                <label for="select-x" class="col-12 col-form-label">X Axis</label>
                                <select style="width:500px" id="select-x">
                                    %for d in fields:
                                        <option
                                            %if d=='Duration (s)':
                                                    selected
                                                %endif
                                                value="${d}">${d}</option>
                                    %endfor
                                </select>
                            </div>
                            <div class="form-group col-12">
                                <label for="select-y" class="col-12 col-form-label">Y Axis</label>
                                <select style="width:500px" id="select-y">
                                    %for d in fields:
                                        <option value="${d}">${d}</option>
                                    %endfor
                                </select>
                            </div>
                            <div class="form-group col-12">
                                <label for="select-trendline" class="col-12 col-form-label">Trendline Type</label>
                                <select style="width:500px" id="select-trendline">
                                    <option selected value="linear">Linear</option>
                                    <option value="exponential">Exponential</option>
                                    <option value="polynomial">Polynomial</option>
                                </select>
                            </div>


                        </div>

                        <div class="col-12" style="height: 900px">
                            ## charts, first one shows accel phases
                                <!--Div that will hold the dashboard-->
                            <div id="dashboard_div">
                                <!--Divs that will hold each control and chart-->
                                <div id="filter_div"></div>
                                <div id="chart_div" style="height:500px"></div>
                            </div>

                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
<script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>
<script>
    var plotDataTable = null;
    var columns = null;
    var numRows = null;
    function drawChart() {
        if (plotDataTable === null) {
            return;
        }
        plotData = new google.visualization.DataView(plotDataTable);
        var xf = $('#select-x').val();
        var yf = $('#select-y').val();
        var vehicleId = $('#select-vid').val();
        var phases = $('#select-phase').val();
        var remove0 = $('#checkbox-0').is(':checked');
        var rows = [...Array(plotData.getNumberOfRows()-1).keys()];


        if(remove0) {
            rows = plotData.getFilteredRows([
                {column: 1, test: function(value){
                    return value >0
                    }}
            ]);
        }
        plotData.setRows(rows);
        var trendlinesOnly = $('#checkbox-trendsonly').is(':checked');
        var title = '{0} vs. {1} for {2}\nphases={3} n={4}'.format(
                xf, yf, vehicleId, phases, rows.length);
        var options = {
            title: title,
            vAxis: {title: yf},
            hAxis: {title: xf},
            dataOpacity: 0.88,
            trendlines: {
                0: {
                    type: $('#select-trendline').val(),
                    showR2: true,
                    color: 'red',
                    opacity: 1,
                    visibleInLegend: true
                },
            }
        };
        if (trendlinesOnly) {
            options.pointsVisible = false;
        }
        var yIdx = columns.indexOf(yf)
        plotData.setColumns([columns.indexOf(xf), yIdx]);

        var chart = new google.visualization.ScatterChart(document.getElementById('chart_div'));
        chart.draw(plotData, options);
    }

    $(document).ready(function () {

        google.charts.load("current", {packages: ["corechart", 'controls']});
        google.charts.setOnLoadCallback(drawDashboard);

        function drawDashboard() {
            // Everything is loaded. Assemble your dashboard...
            // Create a dashboard.
            var dashboard = new google.visualization.Dashboard(
                    document.getElementById('dashboard_div'));
        }

        $('select').select2({allowClear: true});
        $('#select-x,#select-y,#checkbox-0,#select-trendline,#checkbox-trendsonly').on('change', function () {
            drawChart();
        });
        $('#load-phases').click(function () {
            $('#load-icon').show();
            var $out = $('#output');
            $('.alert').alert('close');
            $out.text('');
            var vehicle_id = $('#select-vid').val();

            var phases = $('#select-phase').val();
            $.post('/report/phase_plot',
                    {
                        'vid': [vehicle_id],
                        'phases': phases,
                    },
                    function (data) {
                        var json = JSON.parse(data.replace(/NaN/g, 'null'));
                        json.forEach(function (row, index, arr) {
                            if (index === 0)
                                return;
                            [3, 4].forEach(function (i) {
                                arr[index][i] = moment.unix(row[i]['$date'] / 1000).toDate();
                            });
                        });
                        columns = json[0];
                        numRows = json.length -1;
                        plotDataTable = google.visualization.arrayToDataTable(json);
                        drawChart();
                    }, 'text').fail(function (x) {
                console.log(x);
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