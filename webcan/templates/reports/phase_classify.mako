<%inherit file="../layout.mako"/>
<div class="content">
    <div class="row">
        <div class="col-md-12">
            <div class="card">
                <div class="card-header">
                    Trips
                </div>
            </div>
            <div class="card-block">
                Trips
                <select multiple id="select-trips">
                    %for trip in trips:
                        <option value="${trip}">${trip}</option>
                    %endfor
                </select>
            </div>
        </div>
    </div>
</div>
<script type="text/javascript">
    $(document).ready(function(){
       $('select').select2();
    });
</script>