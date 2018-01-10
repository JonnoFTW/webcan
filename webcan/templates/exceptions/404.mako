<%inherit file="../layout.mako"/>
<div class="content">
    <div class="row justify-content-md-center">
        <div class="col-md-6 col-12">
            <div class="card card-inverse card-danger">
                <div class="card-header ">
                    <h3>404: Page Not Found</h3>
                </div>
                <div class="card-body">
                    Page not found on this server: ${req.path}
                </div>
            </div>
        </div>
    </div>
</div>