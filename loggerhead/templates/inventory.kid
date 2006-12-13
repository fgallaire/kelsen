<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#"
    py:extends="'master.kid'">
<head>
    <meta content="text/html; charset=utf-8" http-equiv="Content-Type" py:replace="''"/>
    <title> ${branch_name} : files for revision ${change.revno} </title>
</head>

<body>

${navbar()}

<h1> <span class="branch-name">${branch_name}</span> : files for revision ${change.revno} </h1>

<!-- !FIXME: this is just copied verbatim from revision.kid -->
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
                <span py:for="child in change.merge_points"> ${revlink(child.revid, '(' + child.revno + ')')} &nbsp; </span>
            </td>
        </tr>
        <tr py:if="len(change.parents) > 1">
        	<th class="parents"> merged from: </th>
        	<td class="parents">
        	    <span py:for="parent in change.parents"><span py:if="parent.revid != change.parents[0].revid"> ${revlink(parent.revid, '(' + parent.revno + ')')} &nbsp; </span></span>
        	</td>
        </tr>

        <tr>
            <th class="description">description:</th>
            <td class="description"><span py:for="line in change.comment_clean">${XML(line)} <br /></span></td>
        </tr>
    </table>
</div>

folder: <span class="folder"> ${path} </span>

<table class="inventory" width="100%">
    <tr class="header">
        <th class="permissions"> Permissions </th>
        <th> Filename </th>
        <th> Last change </th>
        <th> History </th>
    </tr>
    
    <tr class="parity1" py:if="updir">
        <td class="permissions">drwxr-xr-x</td>
        <td class="filename directory"><a href="${tg.url([ '/inventory', revid ], path=updir)}"> (up) </a></td>
        <td> </td> <td> </td>
    </tr>

    <tr py:for="file in filelist" class="parity${file.parity}">
        <td class="permissions"> ${util.fake_permissions(file.kind, file.executable)} </td>
        <td class="filename ${file.kind}">
            <a py:if="file.kind=='directory'" href="${tg.url([ '/inventory', revid ], path=posixpath.join(path, file.pathname))}">${file.filename}/</a>
            <span py:if="file.kind=='symlink'">${file.filename}@</span>
            <span py:if="file.kind=='file'">${file.filename}</span>
        </td>
        <td class="revision"> ${revlink(file.revid, file.revno)} </td>
        <td class="changes-link"> <a href="${tg.url([ '/changes', file.revid ], path=posixpath.join(path, file.pathname))}"> (changes) </a></td>
    </tr>
    <!-- #entries# -->
</table>

</body>
</html>