<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#"
    py:extends="'master.kid'">
<head>
    <meta content="text/html; charset=utf-8" http-equiv="Content-Type" py:replace="''"/>
    <title> ${branch.friendly_name} : revision ${change.revno} </title>
    
    <span py:strip="True" py:def="file_link(filename, file_id)">
        <a href="${branch.url([ '/annotate', revid ],
            **util.get_context(file_id=file_id))}" title="Annotate ${filename}">${filename}</a>
    </span>
    
    <span py:replace="use_collapse_buttons()"></span>
    
    <script type="text/javascript"> <!--
    function show_sbs() {
        collapseDisplay('style', 'sbs', 'table');
        collapseDisplay('style', 'unified', 'none');
        document.cookie='diff=sbs';
    }
    function show_unified() {
        collapseDisplay('style', 'unified', 'table');
        collapseDisplay('style', 'sbs', 'none');
        document.cookie='diff=unified'; 
    }
    function load() {
        sortCollapseElements();
        if (document.cookie.indexOf('diff=unified') >= 0) { show_unified(); }
    }
    // --> </script>
</head>

<body onload="javascript:load()">

${navbar()}

<h1> <span class="branch-name">${branch.friendly_name}</span> : revision ${change.revno}
    <span py:if="compare_revid is not None"> (compared to revision ${history.get_revno(compare_revid)}) </span>
    
    <div class="links">
        <div> <b>&#8594;</b> <a href="${branch.url([ '/files', revid ], **util.get_context())}">
            browse files</a> </div>
        <div> <b>&#8594;</b> <a href="${branch.url('/changes', **util.get_context(start_revid=revid))}">
            view branch changes</a> </div>
        <span py:if="compare_revid is None" py:strip="True">
            <div> <b>&#8594;</b> <a href="${branch.url([ '/bundle', revid, 'bundle.txt' ])}">
                view/download patch</a> </div>
        </span>
        <span py:if="compare_revid is not None" py:strip="True">
            <div> <b>&#8594;</b> <a href="${branch.url([ '/bundle', revid, compare_revid, 'bundle.txt' ])}">
                view/download patch</a> </div>
        </span>
        <span py:if="(remember is not None) and (compare_revid is None)" py:strip="True">
            <div> <b>&#8594;</b> <a href="${branch.url([ '/revision', revid ],
                **util.get_context(compare_revid=remember))}">
                compare with revision ${history.get_revno(remember)} </a></div>
        </span>
        <span py:if="remember != revid" py:strip="True">
            <div> <b>&#8594;</b> <a href="${branch.url([ '/revision', revid ],
                **util.get_context(remember=revid, compare_revid=None))}">
                compare with another revision </a></div>
        </span>
        <span py:if="compare_revid is not None" py:strip="True">
            <div> <b>&#8594;</b> <a href="${branch.url([ '/revision', revid ],
                **util.get_context(remember=None, compare_revid=None))}">
                stop comparing to revision ${history.get_revno(compare_revid)} </a></div>
        </span>
    </div>
</h1>
 
<div class="revision-info">
    <table>
        <tr>
            <th class="author">committed by:</th>
            <td class="author"> ${util.hide_email(change.author)} </td>
        </tr>
        <tr>
            <th class="date">date:</th>
            <td class="date"> ${change.date.strftime('%d %b %Y %H:%M')} </td>
        </tr>

        <tr py:if="len(change.merge_points) > 0">
            <th class="children"> merged in: </th>
            <td class="children">
                <span py:for="child in change.merge_points">
                    ${revision_link(child.revid, '(' + child.revno + util.if_present(' %s', child.branch_nick) + ')', clear=1, start_revid=child.revid)} <br /> 
                </span>
            </td>
        </tr>
        <tr py:if="len(change.parents) > 1">
        	<th class="parents"> merged from: </th>
        	<td class="parents">
        	    <span py:for="parent in change.parents"><span py:if="parent.revid != change.parents[0].revid">
        	        ${revision_link(parent.revid, '(' + parent.revno + util.if_present(' %s', parent.branch_nick) + ')', clear=1, start_revid=parent.revid)} <br />
        	    </span></span>
        	</td>
        </tr>

        <tr>
            <th class="description">description:</th>
            <td class="description"><span py:for="line in change.comment_clean">${XML(line)} <br /></span> </td>
        </tr>
        
        <tr class="divider"> <th></th> <td></td> </tr>
        
        <tr py:if="change.changes.added">
            <th class="files"> files added: </th>
            <td class="files"> <span py:for="filename, file_id in change.changes.added" class="filename">${file_link(filename, file_id)} <br /></span> </td>
        </tr>
        <tr py:if="change.changes.removed">
            <th class="files"> files removed: </th>
            <td class="files"> <span py:for="filename, file_id in change.changes.removed" class="filename">${file_link(filename, file_id)} <br /></span> </td>
        </tr>
        <tr py:if="change.changes.renamed">
            <th class="files"> files renamed: </th>
            <td class="files"> <span py:for="old_filename, new_filename, file_id in change.changes.renamed" class="filename">
                ${file_link(old_filename, file_id)} => ${file_link(new_filename, file_id)}<br />
            </span> </td>
        </tr>
        <tr py:if="change.changes.modified">
            <th class="files"> files modified: </th>
            <td class="files">
                <span py:for="item in change.changes.modified">
                    <span class="filename">${file_link(item.filename, item.file_id)}</span> &nbsp; <a href="#${item.filename}" class="jump">&#8594; diff</a><br />
                </span>
            </td>
        </tr>
    </table>
</div>

<table class="diff-option-buttons">
<tr>
    <td> ${collapse_all_button('file', 'table-row')} </td>

    <td class="spacey">
        <a href="javascript:show_sbs()" class="hide-all collapse-style-sbs-show" title="collapse">
            <img src="${tg.url('/static/images/nav-small-out.gif')}" width="22" height="10" class="collapse-triangle" />show side by side</a>
        <a href="javascript:show_unified()" class="hide-all collapse-style-unified-show" title="expand">
            <img src="${tg.url('/static/images/nav-small-in.gif')}" width="22" height="10" class="collapse-triangle" />show unified diff</a>
    </td>
    
    <td class="diff-key-block diff-insert"></td>
    <td class="label"> added </td>
    <td class="diff-key-block diff-delete"></td>
    <td class="label"> removed</td>
</tr>
</table>

<!-- ! i'm not a big fan of embedding python code here, but the alternatives all seem to be worse -->
<?python uniqs={}; ?>

<div class="diff" py:if="change.changes.modified">
    <!-- ! side-by-side diff -->
    <table class="diff-block collapse-style-sbs-content">
        <span py:strip="True" py:for="item in change.changes.modified">
            <tr><th class="filename" colspan="4">
                ${collapse_button('file', util.uniq(uniqs, item.file_id), 'table-row')}
                <a href="${branch.url([ '/annotate', change.revid ], **util.get_context(file_id=item.file_id))}" name="${item.filename}">${item.filename}</a>
            </th></tr>

            <span py:strip="True" py:for="chunk in item.sbs_chunks">
                <tr class="diff-chunk collapse-file-${util.uniq(uniqs, item.file_id)}-content">
                    <th class="lineno">old</th> <th></th> <th class="lineno">new</th> <th></th>
                </tr>
                <tr py:for="line in chunk.diff" class="diff-chunk collapse-file-${util.uniq(uniqs, item.file_id)}-content">
                    <span py:if="line.old_lineno" py:strip="True">
                        <td class="lineno">${line.old_lineno}</td>
                        <td class="diff-${line.old_type}">${XML(line.old_line)}</td>
                    </span>
                    <span py:if="not line.old_lineno" py:strip="True">
                        <td class="lineno-skip">${line.old_lineno}</td>
                        <td class="diff-${line.old_type}-skip">${XML(line.old_line)}</td>
                    </span>
                    <span py:if="line.new_lineno" py:strip="True">
                        <td py:if="line.new_lineno" class="lineno">${line.new_lineno}</td>
                        <td class="diff-${line.new_type}">${XML(line.new_line)}</td>
                    </span>
                    <span py:if="not line.new_lineno" py:strip="True">
                        <td py:if="not line.new_lineno" class="lineno-skip">${line.new_lineno}</td>
                        <td class="diff-${line.new_type}-skip">${XML(line.new_line)}</td>
                    </span>
                </tr>
                <tr class="diff-chunk-spacing collapse-file-${util.uniq(uniqs, item.file_id)}-content"> <td colspan="4"> &nbsp; </td> </tr>
            </span>
            <tr class="diff-spacing"> <td colspan="4"> &nbsp; </td> </tr>
        </span>
    </table>
    
    <!-- ! unified diff -->
    <table class="diff-block collapse-style-unified-content">
	    <span py:strip="True" py:for="item in change.changes.modified">
	        <tr><th class="filename" colspan="4">
	            ${collapse_button('file', util.uniq(uniqs, item.file_id), 'table-row')}
	            <a href="${branch.url([ '/annotate', change.revid ], **util.get_context(file_id=item.file_id))}" name="${item.filename}">${item.filename}</a>
	        </th></tr>
	
	        <span py:strip="True" py:for="chunk in item.chunks">
	            <tr class="diff-chunk collapse-file-${util.uniq(uniqs, item.file_id)}-content"> <th class="lineno">old</th> <th class="lineno">new</th> <th></th> <th></th> </tr>
	            <tr py:for="line in chunk.diff" class="diff-chunk collapse-file-${util.uniq(uniqs, item.file_id)}-content">
	                <td class="lineno">${line.old_lineno}</td>
	                <td class="lineno">${line.new_lineno}</td>
	                <td class="diff-${line.type} text">${XML(line.line)}</td>
	                <td> </td>
	            </tr>
	            <tr class="diff-chunk-spacing collapse-file-${util.uniq(uniqs, item.file_id)}-content"> <td colspan="4"> &nbsp; </td> </tr>
	        </span>
	        <tr class="diff-spacing"> <td colspan="4"> &nbsp; </td> </tr>
	    </span>
    </table>

</div>

<div py:if="navigation.prev_page_revid or navigation.next_page_revid" class="bar">
    <table>
        <tr>
        <td class="buttons">
            <a py:if="navigation.prev_page_revid" href="${navigation.prev_page_url}"> &lt; revision ${history.get_revno(navigation.prev_page_revid)} </a>
        </td>
        <td class="rbuttons" align="right">
            <a py:if="navigation.next_page_revid" href="${navigation.next_page_url}"> revision ${history.get_revno(navigation.next_page_revid)} &gt; </a>
        </td>
	</tr>
    </table>
</div>

</body>
</html>
