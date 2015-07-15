<%inherit file="rhombus:templates/base.mako" />

%if msg:
    <p>${msg}</p>
%endif

    <div class="bottom">
      <form action="" method="post">
        <input type="hidden" name="came_from" value="${came_from}"/>
        <input type="text" name="login" value="${login}"/><br/>
        <input type="password" name="password"
                 value=""/><br/>
        <input type="submit" name="form.submitted" value="Log In"/>
      </form>
    </div>
