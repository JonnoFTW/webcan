<%inherit file="layout.mako"/>
<div class="content">
    <h1>Data Export</h1>
    <div class="row">
        <div class="col-md-12">
            <div class="card">
                <div class="card-header">
                    <i class="fa fa-info fa-fw"></i> Export
                </div>
                <div class="card-block">
                    <form action="/export" method="post" id="export-form" class="form-horizontal">
                        <fieldset>
                            <!-- Form Name -->
                            <input type="hidden" name="map-hull" id="map-hull"/>
                            <div class="row">
                                <div class="col-md-6">
                                    <!-- Prepended checkbox -->
                                    <div class="form-group">
                                        <label class="control-label" for="prependedcheckbox"><i
                                                class="glyphicon glyphicon-calendar fa fa-calendar"></i> Date Range
                                        </label>
                                        <div class="input-group">
                                            <input id="dateinput" name="daterange" class="form-control">
                                        </div>
                                    </div>

                                    <!-- Select Multiple -->
                                    <div class="form-group">
                                        <label class="control-label" for="selectDevices"><i class="fa fa-car"
                                                                                            aria-hidden="true"></i>
                                            Devices</label>
                                        <select id="selectDevices" name="selectDevices" class="form-control"
                                                multiple="multiple">
                                            %for d in devices:
                                                <option value="${d['name']}">${d['name']}</option>
                                            %endfor
                                        </select>
                                    </div>

                                    <!-- Select Multiple -->
                                    <div class="form-group">
                                        <label class="control-label" for="selectTrips"><i class="fa fa-map"
                                                                                          aria-hidden="true"></i> Trips</label>
                                        <select id="selectTrips" name="selectTrips" class="form-control"
                                                multiple="multiple">
                                            %for t in trips:
                                                <option value="${t}">${t}</option>
                                            %endfor
                                        </select>
                                    </div>


                                    <!-- Select Basic -->
                                    <div class="form-group">
                                        <label class="control-label" for="selectFormat"><i class="fa fa-file-archive-o"
                                                                                           aria-hidden="true"></i> Data
                                            Format</label>
                                        <select id="selectFormat" name="selectFormat" class="form-control">
                                            <option value="shp">Shapefile</option>
                                            <option value="json">JSON</option>
                                            <option value="csv">CSV</option>
                                        </select>
                                    </div>
                                    %if context.get('detail', None):
                                        <div class="form-group">
                                            <div class="alert alert-danger" role="alert">
                                                <strong>Error</strong> ${detail}
                                            </div>
                                        </div>
                                    %endif
                                    <!-- Button -->
                                    <div class="form-group">
                                        <button id="download" name="download" class="btn btn-primary">Download
                                        </button>
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="form-group">
                                        <label class="control-label" for="area"><i class="fa fa-globe"
                                                                                   aria-hidden="true"></i> Map Area
                                            (Select 4 points)</label>
                                        <div style="height:400px" id="map" data-markers="10"></div>
                                    </div>
                                </div>
                            </div>
                        </fieldset>
                    </form>
                </div>
            </div>
        </div>
    </div>
</div>
<script type="application/javascript"
        src="https://rawgit.com/brian3kb/graham_scan_js/master/graham_scan.min.js"></script>
<script src="//cdnjs.cloudflare.com/ajax/libs/bootstrap-daterangepicker/2.1.25/daterangepicker.min.js"></script>
<script type="text/javascript">
    $(document).ready(function () {
        $('#selectTrips').select2({
            placeholder: 'All trips matching devices date range',
            ajax: {
                url: '/dev_trips',
                dataType: 'json',
                data: function (params) {
                    return {devices: $('#selectDevices').val()}
                },
                processResults: function (d, params) {
                    return {
                        results: _.map(d.trips, function (v) {
                            return {
                                id: v.trip_id,
                                text: v.vid + " " + v.trip_id
                            }
                        })
                    }
                }
            }
        });
        $('#selectDevices').select2({
            placeholder: 'All data in date range'
        }).on('change', function (e) {
            // trigger the ajax trigger on selectTrips
            $('#selectTrips').change();
        });
        <%include file="export_map.js"/>
        $('input#dateinput').daterangepicker({
            timePicker: true,
            timePickerIncrement: 10,
            autoUpdateInput: false,
            autoapply: true,
            locale: {
                format: 'DD/MM/YYYY h:mm A'
            }
        }).on('apply.daterangepicker', function (ev, picker) {
            $(this).val(picker.startDate.format(picker.locale.format) + ' - ' + picker.endDate.format(picker.locale.format));
        }).on('cancel.daterangepicker', function (ev, picker) {
            $(this).val('');
        }).attr('placeholder', 'All dates');
    });
</script>

