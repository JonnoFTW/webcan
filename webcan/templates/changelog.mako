<%inherit file="layout.mako"/>
<div class="content">
    <div class="row">
        <div class="col-md-12">
        <div class="card">
            <div class="card-header">
                Changelog
            </div>
            % for c in changes.splitlines():
                <div class="col-md-12">
                    ${c|n}
                </div>

            % endfor
        </div>

    </div>
</div>
</div>
