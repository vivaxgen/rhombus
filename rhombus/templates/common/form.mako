

##
<%def name="input_text(name, label, class_='form-group', class_span = 'form-control', value='')">
<div class='${class_}'>
  <label class='col-md-3 control-label' for='${name}'>${label}</label>
  <div class='col-md-9'>
    <input type='text' id='${name}' name='${name}' value='${value or ""}' ${"class='%s'" % class_ if class_.startswith('span') else "class='%s'" % class_span | n} />
  </div>
</div>
</%def>

##
<%def name="input_password(name, label, class_='form-group', class_span = 'form-control', value='')">
<div class='${class_}'>
  <label class='col-md-3 control-label' for='${name}'>${label}</label>
  <div class='col-md-9'>
    <input type='password' id='${name}' name='${name}' value='${value or ""}' ${"class='%s'" % class_ if class_.startswith('span') else "class='%s'" % class_span | n} />
  </div>
</div>
</%def>

##
<%def name="input_textarea(name, label, class_='form-group', class_span='form-control', value='', style='')">
<div class='${class_}'>
  <label class='col-md-3 control-label' for='${name}'>${label}</label>
  <div class='col-sm-9'>
    <textarea id='${name}' name='${name}' class='${class_span}' ${"style=%s" % style if style else ''}>${value or ""}</textarea>
  </div>
</div>
</%def>


##
## selection
## params: [ (key, value/text), ... ]
<%def name="selection(name, label, params, class_='form-group', class_span='', value='', multiple=False)">
<div class='${class_}'>
  <label class='col-md-3 control-label' for='${name}'>${label}</label>
  <div class='col-md-9'>
    <select id='${name}' name='${name}' class='${class_span}' ${'multiple="multiple"' if multiple else '' | n}>
    % for (key, val) in params:
      % if value and value == key:
        <option value='${key}' selected='selected'>${val}</option>
      % else:
        <option value='${key}'>${val}</option>
      % endif
    % endfor
    </select>
  </div>
</div>
</%def>


##
<%def name="checkboxes( name, label, params, class_='control-group', class_span='')">
<div class="${class_}">
  <label class="control-label" for="${name}">${label}</label>
  % for (n, l, c) in params:
  <div class="controls">
    <label class="checkbox">
      <input id="${name}" type="checkbox" name="${n}" value="1" ${"checked='checked'" if c else ''} />
      ${l}
    </label>
  </div>
  % endfor
</div>
</%def>


##
<%def name="radioboxes( name, label, params, class_='form-group', class_span='')">
<div class="${class_}">
  <label class="col-md-3 control-label">${label}</label>
  <div class="col-md-9">
  % for (l, v, c) in params:
    <div class="radio">
      <label>
        <input type="radio" name="${name}" id="${name}" value="${v}" ${"checked" if c else ''}>
            ${l}
      </label>
    </div>
  % endfor
  </div>
</div>
</%def>  


##
<%def name="selection_ek( name, label, ek_group, class_='control-group', class_span='', value='')">
${selection( name, label,
        [ (k.id, k.key) for k in request.EK().get_members(ek_group) ],
        value = value )}
</%def>


##
<%def name="submit_bar( name='Save', value='save')">
  <div class='form-group'>
    <div class='col-md-12'>
    <button class='btn btn-primary' type='submit' name='_method' value='${value}'>${name}</button>
    <button class='btn' type='reset'>Reset</button>
    </div>
  </div>
</%def>


##
<%def name="input_hidden( name, label='', class_='form-group', class_span='', style='', value='')">
% if label:
<div class='${class_}'>
  <label class='control-label' for='${name}'>${label}</label>
  <div class='controls'>
    <input type='hidden' id='${name}' name='${name}' value='${value}'
     ${"class='%s'" % class_ if class_.startswith('span') else "class='%s'" % class_span | n}
     ${"style='%s'" % style if style else ""| n} />
  </div>
</div>
% else:
  <input type='hidden' id='${name}' name='${name}' value='${value}' />
% endif
</%def>


##
<%def name="input_show(label, value, class_='control-group', class_span = 'input-large')">
<div class='${class_}'>
  <label class='control-label'>${label}</label>
  <div class='controls'>
    <span ${("class='%s uneditable-input'" % class_ if class_.startswith('span') else "class='%s uneditable-input'" % class_span) | n} >${value or ""}</span>
  </div>
</div>
</%def>


##
<%def name="textarea_show(label, value, class_='control-group', class_span = 'input-large', rows=3)">
<div class='${class_}'>
  <label class='control-label'>${label}</label>
  <div class='controls'>
    <span ${("class='%s uneditable-textarea'" % class_ if class_.startswith('span') else "class='%s uneditable-textarea'" % class_span) | n} ${"rows='%d'" % rows | n} >${value or ""}</span>
  </div>
</div>

</%def>

##
<%def name="button_edit(label, link)">
<div class='control-group'>
  <div class='controls'>
    <a href="${link}"><button type="button" class="btn btn-small btn-info"><i class='icon-edit icon-white'></i> ${label}</button></a>
  </div>
</div>
</%def>

##
<%def name="button(label, link, icon=None)">
<a href="${link}"><button type="button" class="btn btn-small btn-info">${("<i class='%s'></i>" % icon) if icon else "" | n} ${label}</button></a>
</%def>

##
<%def name="form_wrapper( action, content )">
<form class='form-horizontal' method='post' action='${action}'>
${content}
</form>
</%def>
##
##
<%def name="input_ck( name, label, url, class_='control-group', class_span='', value='')">
<div class='${class_}'>
  <label class='control-label' for='${name}'>${label}</label>
  <div class='controls'>
    <input type='text' id='${name}' name='${name}' value='${value}'
      ${"class='%s'" % class_ if class_.startswith('span') else "class='%s'" % class_span | n}
      data-provide="typeahead"
      data-source="function( query, process ){ return $.get('${url}', { q: query }, function(data) { return process(data);});}"
      />
  </div>
</div>
</%def>
##

##
<%def name="input_file(name, label, class_='form-group', class_span='form-control')">
<div class='${class_}'>
  <label class="col-sm-3 control-label" for='${name}'>${label}</label>
  <div class='col-sm-9'>
    <input type='file' id='${name}' name='${name}' />
  </div>
</div>
</%def>

