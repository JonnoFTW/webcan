<%inherit file="layout.mako"/>
<div class="content">
    <div class="row">
        <div class="col-md-12">
            <div class="card">
                <div class="card-header">
                    Manage Users
                </div>
                <%
                    fields = ['username', 'login', 'level', 'devices']
                %>
                <table class="table">
                    <thead>
                    <tr>
                        % for f in fields:
                            <th>${f.title()}</th>
                        % endfor
                    </tr>
                    </thead>
                    <tbody>
                        %for i in users:

                            <tr>
                                <td>${i[fields[0]]}</td>
                                %for ft in (fields[2:4]):
                                    <td>
                                        ft
                                    </td>
                                %endfor
                                <td>${i[fields[1]]}</td>
                                <td>${i[fields[2]]}</td>
                                <td>
                                    <select style="width: 100%" multiple name="${i[fields[0]]}-devices">
                                        <%
                                             selected ='selected="selected"' if i['devices'] == '*'  else ''
                                            %>
                                        <option ${selected} value="*">ALL VEHICLES</option>
                                        %for d in devices:
                                            <%
                                                selected ='selected="selected"' if d['name'] in i['devices']  else ''
                                            %>
                                            <option ${selected} value="${d['name']}">${d['name']}</option>
                                        %endfor
                                    </select>
                                </td>
                            </tr>
                        %endfor
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</div>
<script type="text/javascript">
    $(document).ready(function () {
        $('select').select2();
    });

</script>