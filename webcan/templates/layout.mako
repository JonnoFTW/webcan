<!DOCTYPE html>
<html lang="${request.locale_name}">


<head>
    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="application to show CAN logs">
    <meta name="author" content="Jonathan Mackenzie">
    <link rel="icon" href="${request.static_url('webcan:static/favicon.ico')}">

    <title>WebCAN Viewer</title>

    <!-- Bootstrap core CSS -->
    <link rel="stylesheet" href="//cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css"/>
    <link href="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0-beta.2/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="//cdnjs.cloudflare.com/ajax/libs/tether/1.4.0/css/tether.min.css"/>
    <script src="//cdnjs.cloudflare.com/ajax/libs/jquery/3.2.1/jquery.min.js"></script>
    <!-- Custom styles for this scaffold -->
    <link href="${request.static_url('webcan:static/theme.css')}" rel="stylesheet">
    <link rel="stylesheet" href="//cdnjs.cloudflare.com/ajax/libs/select2/4.0.3/css/select2.min.css"/>
    <script src="//cdnjs.cloudflare.com/ajax/libs/moment.js/2.18.1/moment.min.js"></script>
    <link rel="stylesheet"
          href="//cdnjs.cloudflare.com/ajax/libs/bootstrap-daterangepicker/2.1.25/daterangepicker.min.css"/>
    <!-- HTML5 shim and Respond.js IE8 support of HTML5 elements and media queries -->
    <!--[if lt IE 9]>
    <script src="//cdnjs.cloudflare.com/ajax/libs/html5shiv/3.7.3/html5shiv.min.js"></script>
    <script src="//cdnjs.cloudflare.com/ajax/libs/respond.js/1.4.2/respond.min.js"></script>
    <![endif]-->
    <script src="//cdnjs.cloudflare.com/ajax/libs/string-format/0.5.0/string-format.min.js"></script>
    <script type="text/javascript">
        format.extend(String.prototype, {});
    </script>
    % if _pid is not undefined:
        <!-- PID: ${_pid} HOST: ${_host}-->
    % endif
</head>

<body>
<nav class="navbar navbar-expand-md fixed-top navbar-dark bg-dark">
    <div class="container">
        <button class="navbar-toggler navbar-toggler-right" type="button" data-toggle="collapse"
                data-target="#navbar" aria-controls="navbar" aria-expanded="false"
                aria-label="Toggle navigation">
            <span class="navbar-toggler-icon"></span>
        </button>

        <a class="navbar-brand" href="/">
            <i class="fa fa-car" style="color:#689F38" aria-hidden="true"></i>
            WebCAN Viewer
        </a>

        <div class="collapse navbar-collapse" id="navbar">
            <ul class="navbar-nav mr-auto">
                <li class="nav-item dropdown">
                    <a class="nav-link dropdown-toggle" href="/dev" id="dropdown01" data-toggle="dropdown"
                       aria-haspopup="true" aria-expanded="false">Devices</a>
                    <div class="dropdown-menu" aria-labelledby="dropdown01">
                        <a class="dropdown-item" href="/dev">My Devices</a>
                        <div class="dropdown-divider"></div>
                        %for d in devices:
                            <a class="dropdown-item" href="/dev/${d['name']}">${d['name']}</a>
                        %endfor
                    </div>
                </li>
                <li class="nav-item">
                    <a class="nav-link" href="/export">Export</a>
                </li>
                <li class="nav-item"><a class="nav-link" href="/report">Reports</a></li>

            </ul>
            <ul class="nav navbar-nav navbar-right">
                %if request.authenticated_userid:
                    %if request.user['level'] == 'admin':
                        <li class="nav-item disabled"><a class="nav-link disabled" href="#">${_host}</a></li>
                        <li class="nav-item"><a class="nav-link" href="/users">Users</a></li>
                    %endif
                    <li class="nav-item"><a class="nav-link" href="/logout">Logout</a></li>
                %endif

            </ul>

        </div>
    </div>
</nav>
<div class="container">
    <div class="row">
        <div class="col-md-12">
            ${ next.body() }
        </div>
    </div>
</div>


<!-- Bootstrap core JavaScript
================================================== -->
<!-- Placed at the end of the document so the pages load faster -->
<script src="//cdnjs.cloudflare.com/ajax/libs/popper.js/1.13.0/umd/popper.min.js"></script>
<script src="//cdnjs.cloudflare.com/ajax/libs/select2/4.0.3/js/select2.full.min.js"></script>
<script src="//maxcdn.bootstrapcdn.com/bootstrap/4.0.0-beta.2/js/bootstrap.min.js"></script>
<script src="//maps.googleapis.com/maps/api/js?key=AIzaSyDPLn4txz_v6bq0ayC_TgzELsgKYmVEwmU"></script>
<script src="//cdnjs.cloudflare.com/ajax/libs/gmaps.js/0.4.25/gmaps.min.js"></script>
<script src="//cdnjs.cloudflare.com/ajax/libs/lodash.js/4.17.4/lodash.min.js"></script>
</body>
</html>
