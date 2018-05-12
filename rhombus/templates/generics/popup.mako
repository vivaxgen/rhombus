<div class="modal-dialog" role="document"><div class="modal-content">
<div class="modal-header">
	<h5 class="modal-title" id="myModalLabel">${title}</h3>
    <button type="button" class="close" data-dismiss="modal" aria-lable="Close">
    	<span aria-hidden="true">&times;</span>
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
