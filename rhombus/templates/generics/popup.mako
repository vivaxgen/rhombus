<div class="modal-dialog" role="document"><div class="modal-content">
<div class="modal-header">
    <button type="button" class="close" data-dismiss="modal" aria-hidden="true">×</button>
    <h3 id="myModalLabel">${title}</h3>
</div>
<div class="modal-body">

    ${content}

</div>
<div class="modal-footer">
    ${buttons}
</div>
</div></div>

% if javascript:
<script type="text/javascript">
    //<![CDATA[
    ${javascript | n}
    //]]>
</script>
% endif
