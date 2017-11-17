<%inherit file="layout.mako"/>
<div class="content">
    <div class="row">
        <div class="col-md-12">
            <div class="card">
                <div class="card-header">
                    Manage Users
                    <form class="form-inline" id="new-user">
                        <input class="form-control col-md-2 mr-sm-2" name="new-fan" id="fan-input"
                               placeholder="Username/FAN"/>
                        <select class="form-control  mb-2 mr-sm-2 mb-sm-0" name="new-login">
                            %for ft in ('ldap', 'external'):
                                <option value="${ft}">${ft}</option>
                            %endfor
                        </select>
                        <select class="form-control mb-2 mr-sm-2 mb-sm-0" name="new-level">
                            <option value="admin">Admin</option>
                            <option value="viewer">Viewer</option>
                        </select>
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
                                <td><a href="/users/v/${i[fields[0]]}">${i[fields[0]]}</a></td>
                                <td>
                                    <select name="${i[fields[0]]}-login" style="width:100%;">
                                        %for ft in ('ldap', 'external'):
                                        <%
                                            selected = ''
                                            if ft == i['login']: selected = 'selected'
                                        %>
                                            <option ${selected} value="${ft}">${ft}</option>
                                        %endfor
                                    </select>
                                    %if i['login'] == 'external':
                                        <button class="btn btn-primary">Reset Pass</button>
                                    %endif
                                </td>
                                <td>
                                    <select name="${i['username']}-level" style="width:100%;">

                                        %for v in ('admin', 'viewer'):

                                            <option value="${v}"
                                                %if i['level'] == v:
                                                    selected
                                                %endif
                                            >${v.title()}</option>
                                        %endfor

                                    </select>
                                </td>
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
        $('select').select2({
            width: 'resolve',
            dropdownAutoWidth: true
        });

        $('#new-user').submit(function (ev) {
            ev.preventDefault();
            $('#submit').click();
        });
        $('#submit').click(function () {
            $('.alert').alert('close');
            $.post({
                url: '/users/add',
                data: $('#new-user').serialize(),
                success: function (data) {
                    // return the new user object or null and add to the table

                    $('#tbody').append('<tr><td>{}</td><td>{}</td><td></td><td></td><td></td></tr>'.format(data.username, data.login));

                    $('#fan-input').val('')
                },
                headers: {Accept: "application/json; charset=utf-8"}

            }).fail(function (data, text, err) {
                console.log(data);
                $('#new-user').append(
                        '<div class="alert alert-danger" role="alert">\n' +
                        '  <strong>Error</strong> {}.\n'.format(data.responseJSON.message) +
                        '</div>');
                $('.alert').alert();

            });
        })
    });
</script>