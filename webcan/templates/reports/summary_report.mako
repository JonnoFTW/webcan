<%inherit file="../layout.mako"/>
<div class="content">
    <div class="row">
        <h2>Summary Report</h2>
        <div class="col-md-12">
            <div class="card">
                <div class="card-header">
                    Generate Summary Report
                </div>
                <div class="card-body">
                    <div class="row">
                        <div class="col-6">
                            <div class="form-group col-12">
                                <label for="select-vids" class="col-12 col-form-label">Vehicles</label>
                                <select style="width:500px" multiple id="select-vids">
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
                        <div class="col-12">
                            <table class="table table-bordered table-striped">
                                <thead class="thead-dark">
                                    <tr>
                                        <th>Vehicle</th>
                                        <th>Trips</th>
                                        <th>Distance (km)</th>
                                        <th>Time</th>
                                        <th>First</th>
                                        <th>Last</th>
                                    </tr>
                                </thead>
                                <tbody id="output">

                                </tbody>
                            </table>

                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
<script type="text/javascript"
        src="https://cdn.rawgit.com/jsmreese/moment-duration-format/master/lib/moment-duration-format.js"></script>
<script>
    $(document).ready(function () {
        $('select').select2({allowClear: true, placeholder: 'Select vehicles'});
        $('#load-phases').click(function () {
            $('#load-icon').show();
            var $out = $('#output');
            $('.alert').alert('close');
            $out.text('');
            $.post('/report/summary',
                    {'devices': $('#select-vids').val(),
                    'min-trip-distance': $('#min-trip-distance').val()},
                    function (data) {
                        var $tbl = $('#output');
                        _.forEach(data.summary, function (row, vid) {
                            function getVid() {
                                return  vid === 'Aggregate' ? '<b>{0}</b>'.format(vid) : '<a href="/dev/{0}">{0}</a><br/><small>{1}: {2}</small>'.format(vid, row.vehicle.make, row.vehicle.type)
                            }
                            if (row.trips === 0) {
 var rowh = '<tr><td>{0}</td><td>{1}</td><td>0</td><td>0</td><td></td><td></td></tr>'.format(
                                        getVid(), row.trips);
                            } else {
                                var rowh = '<tr><td>{0}</td><td>{1}</td><td>{2}</td><td>{3}</td><td>{4}</td><td>{5}</td></tr>'.format(
                                        getVid(), row.trips, row.distance.toFixed(2), moment.duration(row.time, 'seconds').format(),
                                        moment(row.first.$date), moment(row.last.$date)
                                );
                            }
                            $tbl.append(rowh);
                        });

                    }, 'json').fail(function (x) {
                console.log(x);
                $('#load-button').append(
                        '<div class="alert alert-danger" role="alert">\n' +
                        '  <strong>Error</strong> {}'.format(x.responseJSON.message) +
                        '</div>');
                $('.alert').alert();

            }).always(function () {
                $('#load-icon').hide();
            });
        });
    })
    ;


</script>