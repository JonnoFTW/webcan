<%inherit file="../layout.mako"/>
<div class="content" >
    <h3>Areas Excluded From Summary</h3>
    <div id="map" style="height:800px"></div>

</div>
<script>

    var lat = -35.00803010577838,
            lng = 138.57349634170532;
    $(document).ready(function () {
        var map = new GMaps({
            div: '#map',
            lat: lat,
            lng: lng,
            zoom: 13
        });
        $.post('/report/exclusions', function (data) {
            _.forEach(data.polys, function (i) {
                var infoWindow = new google.maps.InfoWindow({content: i.name});
                var polygon = map.drawPolygon({
                    paths: [[i.poly.coordinates]],
                    useGeoJSON: true,
                    strokeOpacity: 1,
                    strokeWeight: 3,
                    fillColor: '#BBD8E9',
                    fillOpacity: 0.6,
                    click: function (clickEvent) {

                        var position = clickEvent.latLng;

                        infoWindow.setPosition(position);
                        infoWindow.open(map.map);
                    }
                });
            });
        });
    });


</script>