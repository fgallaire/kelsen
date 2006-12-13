<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<?python import sitetemplate ?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#" py:extends="sitetemplate">

<head py:match="item.tag=='{http://www.w3.org/1999/xhtml}head'" py:attrs="item.items()">
    <meta content="text/html; charset=UTF-8" http-equiv="content-type" py:replace="''"/>
    <title py:replace="''">Your title goes here</title>
    <meta py:replace="item[:]"/>
    <style type="text/css" media="screen">
@import "/static/css/style.css";
    </style>

<!-- !define common navbar -->
<span py:def="navbar()">
    <!-- !requires: ${navigation: revid, revlist, pagesize, buttons, scan_url}, ${history} -->
    <div class="navbar">
        <div class="bar">
            <table>
                <tr><td>
                    <span class="buttons">
                        <span py:for="label, url in navigation.buttons">
                            <a href="${url}"> ${label} </a>
                        </span>
                    </span>
                </td><td align="right" py:if="hasattr(navigation, 'revlist')">
                    <span class="navbuttons">
                        <span py:for="label, l_title, l_revid in history.scan_range(navigation.revlist, navigation.revid, navigation.pagesize)">
                            <a py:if="l_revid" href="${tg.url([ navigation.scan_url, l_revid ], path=navigation.path)}" title="${l_title}"> ${label} </a>
                            <span py:if="not l_revid"> ${label} </span>
                        </span>
                    </span>
                </td></tr>
            </table>
        </div>
        <div class="navposition">
            <table>
                <tr>
                    <td> </td>
                    <td class="navposition" align="right" py:if="hasattr(navigation, 'revlist')">
                        changes: ${len(navigation.revlist) - history.get_revid_sequence(navigation.revlist, navigation.revid)} / ${len(navigation.revlist)}
                    </td>
                </tr>
            </table>
        </div>
    </div>
</span>

<span py:def="revlink(revid, text)">
    <a title="Show revision" href="${tg.url([ '/revision', revid ])}" class="revlink"> ${text} </a>
</span>
<span py:def="revlink_path(revid, text, path)">
    <a title="Show revision" href="${tg.url([ '/revision', revid ], path=path)}" class="revlink"> ${text} </a>
</span>

</head>

<body py:match="item.tag=='{http://www.w3.org/1999/xhtml}body'" py:attrs="item.items()">

    <div py:replace="[item.text]+item[:]"/>

	<!-- End of main_content -->
</body>

</html>