<%inherit file="../layout.mako"/>
<div class="content">
    <div class="row">
        <h2> Generate Phase and Trip Reports</h2>
        <div class="col-md-12">
            <div class="card">
                <div class="card-header">
                    Progress
                </div>
                <div class="card-body">
                    <div class="row">
                        <div class="col-12">
                            % if running:
                                Report Generator is Running
                                <table class="table">
                                    <thead>
                                    <th>Started</th>
                                    <th>Progress</th>
                                    <th>Done Trips</th>
                                    <th>Total Trips to Do</th>
                                    </thead>
                                    <tbody>
                                    <tr>
                                        <td>${running['started'].isoformat()}</td>
                                        <td>${running['progress']}%</td>
                                        <td>${running['done']}</td>
                                        <td>${running['total']}</td>
                                    </tr>
                                    </tbody>
                                </table>
                            % else:
                                <form action="/report/generate" method="post">
                                    <button type="submit" class="btn btn-info">Generate Reports</button>
                                </form>
                            % endif
                            % if error:
                                <p>Last error at ${error['dt']}:</p>
                                <code>
                                    <pre>
                                        ${error['err']}
                                    </pre>
                                </code>

                            % endif
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
<script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>
<script>

    $(document).ready(function () {

    });


</script>