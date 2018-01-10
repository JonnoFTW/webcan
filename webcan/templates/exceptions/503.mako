<%inherit file="../simple/layout.mako"/>
<div class="content">
    <div class="row justify-content-md-center">
        <div class="col-md-6 col-12">
            <div class="card card-inverse card-danger">
                <div class="card-header text-center">
                    <h3>503: Service Unavailable</h3>
                </div>
                <div class="card-body">
                    The server is currently unavailable. Please try again at a later time <br>
                    <b>Error:</b> ${msg}
                </div>
            </div>
        </div>
    </div>
</div>