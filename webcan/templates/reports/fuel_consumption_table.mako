<%inherit file="../layout.mako"/>
<h2>Fuel Consumption Report Table</h2>
<div class="col row mb-4">
    <a href="${request.route_url('trip_summary_csv')}" class="btn btn-primary" role="button">Download CSV</a>
</div>
<table id="data" class="table table-bordered table-striped">
    <thead class="thead-dark">
        % for header in row.keys():
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
##         % for row in rows:
##             <tr>
##                 %for key, val in row.items():
##                     <td>
##                         %if key == 'vid':
##                             <a href="/dev/${val}">${val}</a>
##                         %elif key == 'trip_key':
##                             <a href="/dev/${row['vid']}?key=${val}">${val}</a>
##                         %elif type(val) is float:
##                             ${round(val,2)}
##                         %else:
##                             ${val}
##                         %endif
##
##                     </td>
##                 %endfor
##             </tr>
##         % endfor
    </tbody>
</table>

<script>
    $(document).ready(function () {
        var table = $('#data').DataTable({
            columnDefs: [
                {
                    render: function(data, type, row, meta) {
                        if(meta.col === 0)
                            return '<a href="/dev/{0}?key={1}">{1}</a>'.format(row.vid, row.trip_key);
                        if (meta.col === 1)
                            return '<a href="/dev/{0}">{0}</a>'.format(row.vid);
                    },
                    targets: [0,1]
                },
                {
                    render: function(data, type, row, meta) {
                        return moment.unix(data.$date/1000).format('LLLL');
                    },
                    targets: [2, 3]
                },
                {
                    render: function(data, type, row, meta) {
                        return data.toFixed(2);
                    },
                    targets: _.range(4,${len(row.keys())})
                }
            ],
            ajax: "/report/trips_summary/json",
            columns: ${json.dumps([{'data': x} for x in row.keys()])|n}
        });
        $('select').select2({allowClear: true}).on('select2:select select2:unselect', function (e) {
            table.search($(e.target).val()).draw();
        });


    });
</script>