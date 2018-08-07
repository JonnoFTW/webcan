<%inherit file="layout.mako"/>
<!--suppress ALL -->
## <div class="content">
##     <div class="row">
##         <div class="col-md-12">

<div class="card" id="app">
    <div v-if="loading" class="col-12 text-center" style="padding: 15px" id="loader">
        <i class="fa fa-spinner fa-pulse fa-5x fa-fw"></i>
        <span class="sr-only">Loading...</span>
    </div>
    <div id="content" style="display:none">


        <div class="card-header">
            Manage Users
            <form class="form-inline" id="new-user">
                <input class="form-control col-md-2 mr-sm-2" v-model="newuser.name" name="new-fan"
                       id="fan-input"
                       placeholder="Username/FAN"/>
                <v-select :options="login" :placeholder="'Login'" v-model="newuser.login"
                          :name="'new-login'"></v-select>
                <v-select :options="levels" :placeholder="'Level'" v-model="newuser.level"
                          :name="'new-level'"></v-select>
                <button type="button" id="submit" @click="add_user" class="btn btn-primary">Add</button>
                <div class="alert alert-danger" v-if="newerrorvisible" role="alert">
                    <strong>Error</strong> {{newerror}}
                </div>
            </form>
        </div>
        <table class="table">
            <thead>
            <tr>
                <th v-for="f in tfields">{{f}}</th>
            </tr>
            </thead>
            <tbody id="tbody">
            <tr is="user-component" :user="user" v-for="user in users" :key="user.username"></tr>
            </tbody>
        </table>
    </div>
</div>
##         </div>
##     </div>
## </div>
<%
    import json
%>
<script src="https://unpkg.com/vue"></script>
<script src="https://unpkg.com/vue-select@latest"></script>
<script src="https://unpkg.com/vue-resource@1.3.4/dist/vue-resource.min.js"></script>
<script type="text/javascript">
    Vue.component('v-select', VueSelect.VueSelect);
    Vue.component('user-component',
            {
                data: function () {
                    return {
                        levels: app.levels,
                        devices: app.devices,
                        login: app.login
                    }
                },
                props: ["user"],
                template: `
            <tr>
                <td><a :href="'/users/v/'+user.username">{{user.username}}</a><br>
                    <button v-if="user.login == 'external'"
                            @click="reset_pass(user.username)"
                            class="btn btn-danger btn-sm reset-password">Reset Pass
                    </button>
                </td>
                <td>
                    <v-select :name="user.username+'-login'" v-model="user.login" :placeholder="'Login'" :options="login"></v-select>
                    <input class="form-control" v-if="user.login == 'external'" v-model="user.email"  placeholder="Email"/>
                </td>
                <td>
                    <v-select :name="user.username+'-level'" v-model="user.level"
                              :options="levels"></v-select>
                </td>
                <td>
                    <v-select :options="devices" label="name" v-model="user.devices"
                              multiple :name="user.username+'-devices'"></v-select>
                </td>
            </tr>`,
                watch: {
                    user: {
                        handler: function (newValue, oldValue) {
                            ##  console.log(newValue.username + " modified")
                            ##  console.log("New", newValue.devices);
                            ##  console.log("Old", oldValue.devices);
                            this.update_user(newValue);
                        },
                        deep: true
                    }
                },
                methods: {
                    reset_pass: function (username) {
                        var route = '/users/reset/' + username;
                        this.$http.get(route).then(function (response) {
                            console.log(response);
                        });
                    },
                    update_user: function (user_obj) {
                        console.log("Updating user", user_obj);
                         this.$http.post('/users/update', user_obj, {emulateJSON: true});
                    }
                }
            });
    var app = new Vue({
        el: '#app',
        data: {
            loading: true,
            newuser: {},
            devices: [],
            newerror: '',
            newerrorvisible: false,
            users: [],
            levels: ${json.dumps(user_levels)|n},
            login: ${json.dumps(login_types)|n},
            tfields: ['Username', 'Login', 'Level', 'Devices']
        },

        mounted: function () {
            $('#loader').hide(500, function () {
                $('#content').show(500);
                this.loading = false;
            });
            this.devices = ${json.dumps([x['name'] for x in devices])|n};
            var allDev = {'name': 'ALL DEVICES', 'value': '*'};
            this.devices.unshift(allDev);
            this.users = ${json.dumps(users)|n};
            this.users.forEach(function (el) {
                if (el.devices === '*') {
                    el.devices = [allDev];
                }
            });

        },
        filters: {
            capitalize: function (str) {
                return str.charAt(0).toUpperCase() + str.slice(1)
            }
        },
        methods: {

            add_user: function (trigger) {
                console.log("adding user");
                this.$http.post('/users/add', this.newuser, {emulateJSON: true}).then(
                        function (response) {
                            // success
                            this.users.push(response.data);
                            this.newuser = {};
                            this.newerrorvisible = false;
                        }, function (response) {
                            // error
                            this.newerror = response.body.message;
                            this.newerrorvisible = true;
                        });
            }
        }
    });
</script>