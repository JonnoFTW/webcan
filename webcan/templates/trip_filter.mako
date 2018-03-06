<%inherit file="layout.mako"/>
<div class="content">
    <div class="row">
        <div class="col-md-12">
            <div class="card" id="app">
                <div v-if="loading" class="col-12 text-center" style="padding: 15px" id="loader">
                    <i class="fa fa-spinner fa-pulse fa-5x fa-fw"></i>
                    <span class="sr-only">Loading...</span>
                </div>
                <div id="content" style="display:none">
                    <div class="card-header">
                        Trips for ${vid}, provide a reason for filtering and that trip will be excluded from
                        reporting
                    </div>
                    <table class="table">
                        <thead>
                        <tr>
                            <th v-for="f in tfields">{{f}}</th>
                        </tr>
                        </thead>
                        <tbody id="tbody">
                        <tr is="trip-reason-component" v-for="trip in trips" :key="trip" :trip="trip"></tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
</div>
<%
    import json
%>
<script src="https://unpkg.com/vue"></script>
<script src="https://unpkg.com/vue-resource@1.3.4/dist/vue-resource.min.js"></script>
<script type="text/javascript">
    Vue.component('trip-reason-component',
            {
                data: function (trip) {
                    return {
                        reason: '',
                    }
                },
                mounted: function () {
                    this.reason = app.reasons[this.trip];
                },
                props: ['trip'],
                template: `
                    <tr>
                        <td><a :href="'/dev/${vid}#'+trip">{{trip}}</a></td>
                        <td><a :href="'/trip/'+trip+'.csv'" role="button" class="btn btn-primary">CSV</a></td>
                        <td><div class="form-group"><input class="form-control" v-model="reason" placeholder="Reason for filtering"/></div></td>
                        <td><button class="btn btn-primary" @click="set_filter">Save</button></td>
                        <td><button class="btn btn-danger" @click="delete_filter">Delete</button></td>
                    </tr>`,
                watch: {},
                methods: {
                    delete_filter: function (trigger) {
                        this.reason = '';
                        $trigger = $(trigger.currentTarget);
                        this.$http.delete('/trips_filter/' + this.trip, {emulateJSON: true}).then(
                                function (response) {
                                    console.log('Deleted', this.trip);
                                    this.setTooltip("Deleted filter", $trigger);
                                }
                        )

                    },
                    set_filter: function (trigger) {
                        $trigger = $(trigger.currentTarget);
                        if (this.reason === undefined || this.reason === '') {
                            this.setTooltip("Invalid reason", $trigger);
                        } else {
                            this.$http.post('/trips_filter/${vid}', {
                                trip_id: this.trip,
                                reason: this.reason
                            }, {emulateJSON: true}).then(
                                    function (response) {
                                        // success
                                        console.log("Updated filter", response.json());
                                        this.setTooltip("Saved filter", $trigger);

                                    }, function (response) {
                                        // error
                                    });
                        }
                    },
                    setTooltip: function (message, btn) {
                        btn.tooltip('hide')
                                .attr('data-original-title', message)
                                .tooltip('show');
                        setTimeout(function () {
                            btn.tooltip('hide');
                        }, 1000);
                    },

                }
            });
    var app = new Vue({
        el: '#app',
        data: {
            loading: true,
            trips: [],
            reasons: {},
            tfields: ['Trip ID', 'CSV', 'Reason', 'Save', 'Remove Filter']
        },

        mounted: function () {
            $('#loader').hide(500, function () {
                $('#content').show(500);
                this.loading = false;
            });
            this.trips = ${json.dumps(trips)|n};
            this.reasons = ${json.dumps(reasons)|n};

        },
        filters: {
            capitalize: function (str) {
                return str.charAt(0).toUpperCase() + str.slice(1)
            }
        },
    });
</script>