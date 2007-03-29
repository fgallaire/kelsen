<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xmlns:py="http://purl.org/kid/ns#">
    <title> bazaar changes for ${branch.friendly_name} </title>
    <updated>${updated}</updated>
    <id>${branch.url(['atom'])}</id>
    <link rel="self" href="${branch.url([''])}" />

	<entry py:for="entry in changes">
	    <title> ${entry.revno}: ${entry.short_comment} </title>
	    <updated>${entry.date.isoformat() + 'Z'}</updated>
	    <id>${branch.url(['revision', entry.revid ])}</id>
	    <author> <name> ${util.hide_email(entry.author)} </name> </author>
	    <content type="text">
            ${entry.comment}
	    </content>
	    <link rel="alternate"
                  href="${branch.url(['revision', entry.revid ])}" />
	</entry>
</feed>
