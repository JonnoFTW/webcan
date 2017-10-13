<%inherit file="layout.mako"/>
<div class="content">
    <div class="row">
        <div class="col-md-12">
            <div class="card">
                <div class="card-header">
                    Manage Users
                    <form class="form-inline" id="new-user">
                        <input class="form-control col-md-2 mr-sm-2" name="fan" id="fan-input" placeholder="fan"/>
                        <button type="button" id="submit" class="btn btn-primary">Add</button>
                    </form>
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
                    <tbody id="tbody">
                        %for i in users:

                            <tr>
                                <td>${i[fields[0]]}</td>
                                %for ft in ('login','level'):
                                    <td>
                                        ${i[ft]}
                                    </td>
                                %endfor
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

        $('#new-user').submit(function (ev) {
            ev.preventDefault();
            $('#submit').click();
        });
        $('#submit').click(function () {
            $('.alert').alert('close');
            $.post('/users/add',
                    {fan: $('#fan-input').val()},
                    function (data) {
                        // return the new user object or null and add to the table
                        var user = data.user;
                        if (data.err) {
                            console.log(data.err);
                            $('#new-user').append(
                                    '<div class="alert alert-danger" role="alert">\n' +
                                    '  <strong>Error</strong> {}.\n'.format(data.err) +
                                    '</div>');
                            $('.alert').alert();
                        } else {
                            $('#tbody').append('<tr><td>{}</td><td>{}</td><td></td></tr>'.format(user.username, user.login));
                        }
                        $('#fan-input').val('');
                    });
        });
    });

</script>