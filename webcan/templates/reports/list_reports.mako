<%inherit file="../layout.mako"/>
<div class="content">
    <div class="row">
        <div class="col-md-12">
            <div class="card">
                <div class="card-header">
                    Reports
                </div>

                <div class="card-body">
                    <div class="row">
                        <ul>
                            %for r in sorted(reports, key=lambda x:x['name']):
                                <li><a href="${r['pattern']}">${r['name'].replace('_',' ').title()}</a></li>
                            %endfor
                        </ul>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>