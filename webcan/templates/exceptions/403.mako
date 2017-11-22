<%inherit file="../layout.mako"/>
<div class="content">
    <div class="row justify-content-md-center">
        <div class="col-6 col-">
            <div class="card card-inverse card-danger">
                <div class="card-header ">
                    <h3>403: Permission Denied</h3>
                </div>
                <div class="card-body">
                    You don't have access to: ${req.path}
                </div>
            </div>
        </div>
    </div>
</div>