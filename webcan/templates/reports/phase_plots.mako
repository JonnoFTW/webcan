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

                            <div class="form-group col-12" id="load-button">
                                <button class="btn btn-primary" id="load-phases">Load</button>
                                <i id="load-icon" class="fa fa-refresh fa-spin fa-fw" style="display:none"></i>
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
    function drawChart(dataIn, vehicleId) {
        var data = google.visualization.arrayToDataTable(dataIn);
        var title = 'Duration vs. CO2e for {0} n={1}'.format(
            vehicleId, dataIn.length - 1);
        var options = {
            title: title,
            vAxis: {title: 'CO2e (g)'},
            hAxis: {
                title: 'Duration (s)'
            },
            trendlines: {0: {
                color: 'red',
                visibleInLegend: true
                }}
        };
        var chart = new google.visualization.ScatterChart(document.getElementById('chart_div'));
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
            $.post('/report/phase_plot',
                    {'vid': [vehicle_id]},
                    function (data) {
                        drawChart(data, vehicle_id);
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