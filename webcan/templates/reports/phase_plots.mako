<%inherit file="../layout.mako"/>
<div class="content">
    <div class="row">
        <h2>Fuel Consumption Report</h2>
        <div class="col-md-12">
            <div class="card">
                <div class="card-header">
                    Vehicle Fuel Consumption Report
                </div>
                <div class="card-body">
                    <div class="row">
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
                                        <option value="${d}">${d}</option>
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


                        </div>
                        <div class="col-12" id="chart_div" style="height: 900px">
                            ## charts, first one shows accel phases

                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
<script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>
<script>
    function drawChart(dataIn, vehicleId, phases) {
        var data = google.visualization.arrayToDataTable(dataIn);
        var title = '{0} vs. {1} for {2}\nphases={3} n={4}'.format(
                dataIn[0][0], dataIn[0][1], vehicleId, phases, dataIn.length - 1);
        var options = {
            title: title,
            vAxis: {title: dataIn[0][1]},
            hAxis: {title: dataIn[0][0]},
            trendlines: {
                0: {
                    color: 'red',
                    visibleInLegend: true
                }
            }
        };
        var chart = new google.visualization.ScatterChart(document.getElementById('chart_div'));
        chart.draw(data, options);
    }

    $(document).ready(function () {

        google.charts.load("current", {packages: ["corechart"]});
        $('select').select2({allowClear: true});
        $('#load-phases').click(function () {
            $('#load-icon').show();
            var $out = $('#output');
            $('.alert').alert('close');
            $out.text('');
            var vehicle_id = $('#select-vid').val();
            var x = $('#select-x').val();
            var y = $('#select-y').val();
            var phases = $('#select-phase').val();
            $.post('/report/phase_plot',
                    {
                        'vid': [vehicle_id],
                        'x': x,
                        'y': y,
                        'phases': phases
                    },
                    function (data) {
                        drawChart(data, vehicle_id, phases);
                    }, 'json').fail(function (x) {
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