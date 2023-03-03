<div class="modal-dialog" role="document"><div class="modal-content">
<div class="modal-header">
	<h5 class="modal-title" id="myModalLabel">${title}</h3>
    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-lable="Close">
    </button>
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
