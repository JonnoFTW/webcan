<%inherit file="layout.mako"/>
<div class="content">
    <h1>Device: ${device}</h1>
    <div class="row">
        <div class="col-md-12">
            <div class="card">
                <div class="card-header">
                    <i class="fa fa-info fa-fw"></i> Map
                    <select class="form-control">
                        %for t in trips:
                            <option value="${t}">${t}</option>
                        %endfor
                    </select>
                    <div class="float-right" id="csv-link"></div>
                </div>
                <div style="width:100%; height:800px" id="map"></div>
            </div>
        </div>
    </div>
</div>
<%include file="show_device_path.mako"/>
<script type="text/javascript">
    var map = null;
    var load_trip = function (trip_id) {
        console.log("Loading trip:", trip_id)
        window.location.hash = '#{}'.format(trip_id);
        $('#csv-link').html('<i class="fa fa-spinner fa-pulse fa-fw"></i>\n' +
                '<span class="sr-only">Loading...</span>');
        $.getJSON("/trip/{}.json".format(trip_id), function (readings) {
            if (readings.readings.length===0) {
                $('#csv-link').html('No data!');
                return;
            }
            map.removeMarkers();
            show_path(readings.readings);

            map.setCenter(readings.readings[0].lat, readings.readings[0].lng);
            $('#csv-link').html('<a class="btn btn-sm btn-outline-primary" href="/trip/{}.csv">Get {}.csv</a>'.format(trip_id, trip_id));
        });
    };
    $(document).ready(function () {
        map = new GMaps({
            div: '#map',
            lat: lat,
            lng: lng,
            zoom: 16
        });
        $('select').select2({
            width: '180px'
        }).on('select2:select', function(evt){
            load_trip($(this).val());
        });

        $('.map-load').click(function () {
            load_trip($(this).data('trip'));
        });
        if (window.location.hash !== "") {
            // load up that
            load_trip(window.location.hash.substr(1));
        } else {
            load_trip($('select').val());
        }
    });

</script>