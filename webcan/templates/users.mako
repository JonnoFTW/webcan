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
                        <v-select :options="login" :placeholder="'Login'" name="new-login"></v-select>
                        <v-select :options="levels" :placeholder="'Level'" name="new-level"></v-select>
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
                        <td><a :href="'/users/v/'+user.username">{{user.username}}</a><br>
                            <button v-if="user.login == 'external'" class="btn btn-danger btn-sm reset-password">Reset
                                Pass
                            </button>
                        </td>
                        <td>
                            <v-select :name="user.username+'-login'" v-model="user.login" :options="login"></v-select>
                        </td>
                        <td>
                            <v-select :name="user.username+'-level'" v-model="user.level" :options="levels" ></v-select>
                        </td>
                        <td>
                            <v-select style="width: 100%" :options="devices" label="name" v-model="user.devices" multiple :name="user.username+'-devices'"></v-select>
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
<script src="https://unpkg.com/vue-select@latest"></script>
<script type="text/javascript">
    Vue.component('v-select', VueSelect.VueSelect);
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
            this.devices.unshift({'name': 'ALL DEVICES'});
            this.users = ${json.dumps(users)|n};
        },
        filters: {
            capitalize: function (str) {
                return str.charAt(0).toUpperCase() + str.slice(1)
            }
        },
        methods: {}
    });
    $(document).ready(function () {

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
                    $('#fan-input').val('');
                    app.users.push(data);
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