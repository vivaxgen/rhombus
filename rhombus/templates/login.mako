<%inherit file="rhombus:templates/base.mako" />

%if msg:
    <p>${msg}</p>
%endif

    <div class="row"><div class="col-md-10 col-md-offset-1"
    <div class="bottom">
      <form action="" method="post" class="form-horizontal">
        <input type="hidden" name="came_from" value="${came_from}"/>
        <div class="form-group">
          <label for="login" class="col-md-2 control-label">Login</label>
          <div class="col-md-3">
            <input type="text" name="login" class="form-control" value="${login}"/>
          </div>
        </div>
        <div class="form-group">
          <label for="login" class="col-md-2 control-label">Password</label>
          <div class="col-md-3">
            <input type="password" class="form-control" name="password" value=""/>
          </div>
        </div>
        <div class="form-group">
          <div class="col-md-offset-2 col-md-2">
            <input type="submit" class="btn" name="form.submitted" value="Log In"/>
          </div>
        </div>
      </form>
    </div>
    </div></div>
