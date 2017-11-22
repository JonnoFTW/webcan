<%inherit file="layout.mako"/>
<div class="content">
    <div class="row">
        <div class="col-md-12">
            <div class="card" id="app">
                <div class="card-header">
                    Manage Users
                    <form class="form-inline" id="new-user">
                        <input class="form-control col-md-2 mr-sm-2" name="new-fan" id="fan-input"
                               placeholder="Username/FAN"/>
                        <select class="form-control  mb-2 mr-sm-2 mb-sm-0" name="new-login">
                            <option v-for="log in login" :value="log">{{log | capitalize}}</option>
                        </select>
                        <select class="form-control mb-2 mr-sm-2 mb-sm-0" name="new-level">
                            <option v-for="level in levels" :value="level">{{level | capitalize}}</option>
                        </select>
                        <button type="button" id="submit" class="btn btn-primary">Add</button>
                    </form>
                </div>
                <table class="table">
                    <thead>
                    <tr>
                        <th v-for="f in tfields">{{f}}</th>
                    </tr>
                    </thead>
                    <tbody id="tbody">
                    <tr v-for="user in users">
                        <td><a :href="'/users/v/'+user.username">{{user.username}}</a></td>
                        <td>
                            <select :name="user.username+'-login'" style="width:100%;">
                                <option v-for="log in login" :value="log">{{log | capitalize}}</option>
                            </select>
                        </td>
                        <td>
                            <select :name="user.username+'-level'" style="width:100%;">
                                <option v-for="level in levels" :value="level">{{level | capitalize}}</option>
                            </select>
                        </td>
                        <td>
                            <select style="width: 100%" multiple :name="user.username+'-devices'">
                                <option :selected="user.devices == '*'" value="*">ALL VEHICLES</option>
                                <option v-for="d in devices" :value="d.name"
                                        :selected="user.devices.indexOf(d.name) != -1">{{d.name}}
                                </option>
                            </select>
                        </td>
                    </tr>
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</div>
<%
    import json
%>
<script src="https://unpkg.com/vue"></script>
<script type="text/javascript">
    var app = new Vue({
        el: '#app',
        data: {
            devices: [],
            users: [],
            levels: ${json.dumps(user_levels)|n},
            login: ${json.dumps(login_types)|n},
            tfields: ['Username', 'Login', 'Level', 'Devices']
        },
        mounted: function () {
            this.devices = ${json.dumps(devices)|n};
            this.users = ${json.dumps(users)|n};
        },
        filters: {
            capitalize: function (str) {
                return str.charAt(0).toUpperCase() + str.slice(1)
            }
        },
        methods: {
            createUser: function() {
                var newUser = {

                }

            },
            updateUser: function(user){

            }
        }
    });
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
                    $('#fan-input').val('')
                },
                headers: {Accept: "application/json; charset=utf-8"}
            }).fail(function (data) {
                $('#new-user').append(
                        '<div class="alert alert-danger" role="alert">\n' +
                        '  <strong>Error</strong> {}.\n'.format(data.responseJSON.message) +
                        '</div>');
                $('.alert').alert();

            });
        })
    });
</script>