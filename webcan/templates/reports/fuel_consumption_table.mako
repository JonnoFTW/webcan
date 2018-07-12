<%inherit file="../layout.mako"/>
## <div class="content">
##     <div class="row">
        <h2>Fuel Consumption Report Table</h2>
##         <div class="col-md-12">
##             <div class="card">
##                 <div class="card-header">
##                     Vehicle Fuel Consumption Report
##                 </div>
##                 <div class="card-body">
##                     <div class="row">

<div class="col row mb-4">
    <a href="${request.route_url('fuel_consumption_csv')}" class="btn btn-primary" role="button">Download CSV</a>
</div>
<table id="data" class="table table-bordered table-striped">
    <thead class="thead-dark">
        % for header in rows[0].keys():
            <th>
                ${header}
                %if header == 'vid':
                ## put a select input with all the available vids
                                             <select style="width:200px" multiple id="select-vid">
                    %for d in devices:
                        <option value="${d['name']}">${d['name']}</option>
                    %endfor
                </select>
                %endif
            </th>
        % endfor
    </thead>
    <tbody id="output">
        % for row in rows:
            <tr>
                %for key, val in row.items():
                    <td>
                        %if key == 'vid':
                            <a href="/dev/${val}">${val}</a>
                        %elif type(val) is float:
                            ${round(val,2)}
                        %else:
                            ${val}
                        %endif

                    </td>
                %endfor
            </tr>
        % endfor
    </tbody>
</table>

##                         </div>
##                     </div>
##                 </div>
##             </div>
##         </div>
##     </div>
## </div>

<script>

    $(document).ready(function () {
        var table = $('#data').DataTable();
        $('select').select2({allowClear: true}).on('select2:select select2:unselect', function (e) {

            table.search($(e.target).val());
        });


    });
</script>