<%inherit file="rhombus:templates/plainbase.mako" />

<section class="login-block">
    <div class="container-fluid">
        <div class="row">
            <div class="col-sm-12">
                <form class="md-float-material form-material" action="#" method="POST">
                    <div class="auth-box card">
                        <div class="card-block">
                            <div class="row">
                                <div class="col-md-12">
                                    <h3 class="text-center heading">Log In: ${title}</h3>
                                </div>
%if msg:
    <div><p>${msg}</p></div>
%endif
                            </div>

                            <div class="form-group form-primary"> <input type="text" class="form-control" name="login" value="${login}" placeholder="Login" id="login"> </div>
                            <div class="form-group form-primary"> <input type="password" class="form-control" name="password" placeholder="Password" value="" id="password"> </div>
                            <div class="row">
                                <div class="col-md-12"> <input type="submit" class="btn btn-primary btn-md btn-block waves-effect text-center m-b-20" name="submit" value="Log In"> <!-- <button type="button" class="btn btn-primary btn-md btn-block waves-effect text-center m-b-20"><i class="fa fa-lock"></i> Signup Now </button> -->
                                </div>
                            </div>

%if 'rhombus.oauth2.google.client_id' in request.registry.settings:
                            <div class="or-container">
                                <div class="line-separator"></div>
                                <div class="or-label">or</div>
                                <div class="line-separator"></div>
                            </div>
                            <div class="row">
                                <div class="col-md-12"> <a class="btn btn-lg btn-google btn-block text-uppercase btn-outline" href="/g_login"><img width="20px" style="margin-bottom:3px; margin-right:5px" alt="Google sign-in" src="${request.static_url('rhombus:static/google-g-logo.svg')}"> Login Using Google</a> </div>
                            </div> <br>
%endif

                            <p class="text-inverse text-center">Forget password? <a href="" data-abc="true">Click here</a></p>
                        </div>
                    </div>
                </form>
            </div>
        </div>
    </div>
</section>

##
##
<%def name="stylelink()">
  <link href="${request.static_url('rhombus:static/css/login.css')}" rel="stylesheet" />
</%def>
##
