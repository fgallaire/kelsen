var unified = true;

function make_unified(chunk) {
  var pending_added = [];
  function flush_adds(before) {
    for (var i = 0; i < pending_added.length; i++) {
      before.ancestor().insertBefore(pending_added[i], before);
    }
    pending_added.length = 0;
  }
  chunk.get('children').filter(".pseudorow").each(
    function (line) {
      if (line.hasClass("context-row")) {
        flush_adds(line);
        line.removeChild(line.query('.code'));
      }
      else if (line.hasClass("both-row")) {
        var added_line = line.create('<div class="pseudorow insert-row"><div class="lineNumber first">&nbsp;</div><div class="clear">&nbsp;</div></div>');
        var clear = added_line.query('.clear');
        added_line.insertBefore(line.query('.lineNumber.second'), clear);
        added_line.insertBefore(line.query('.code.insert'), clear);
        pending_added[pending_added.length] = added_line;
        line.insertBefore(line.create('<div class="lineNumber second">&nbsp;</div>'), line.query('.code.delete'));
        line.replaceClass("both-row", "delete-row");
      }
      else if (line.hasClass("insert-row")) {
        flush_adds(line);
        line.removeChild(line.query('.blank'));
      }
      else if (line.hasClass("delete-row")) {
        line.removeChild(line.query('.blank'));
        line.insertBefore(line.query('.lineNumber.second'), line.query('.code.delete'));
      }
    });
  flush_adds(null);
  chunk.replaceClass('sbs', 'unified');
}

function make_sbs(chunk) {
  var added = [];
  var removed = [];
  function clear_bufs(before) {
    if (!added.length && !removed.length) return;
    var common = Math.min(added.length, removed.length);
    for (var i = 0; i < common; i++) {
      var a = added[i];
      var r = removed[i];
      a.ancestor().removeChild(a);
      r.removeChild(r.query('.lineNumber.second'));
      r.insertBefore(a.query('.lineNumber.second'), r.query('.clear'));
      r.insertBefore(a.query('.code.insert'), r.query('.clear'));
      r.replaceClass('removed-row', 'both-row');
    }
    if (added.length > removed.length) {
      for (var j = common; j < added.length; j++) {
        a = added[j];
        a.insertBefore(a.create('<div class="code blank">&nbsp;</div>'), a.query('.lineNumber.second'));
      }
    }
    else if (added.length < removed.length) {
      for (var j = common; j < removed.length; j++) {
        r = removed[j];
        r.insertBefore(r.query('.code.delete'), r.query('.lineNumber.second'));
        r.insertBefore(r.create('<div class="code blank">&nbsp;</div>'), r.query('.clear'));
      }
    }
    added.length = 0;
    removed.length = 0;
  }
  chunk.get('children').filter(".pseudorow").each(
    function (line) {
      if (line.hasClass("context-row")) {
        clear_bufs(line);
        line.insertBefore(line.query('.code').cloneNode(true), line.query(".second"));
      }
      else if (line.hasClass("insert-row")) {
        added[added.length] = line;
      }
      else if (line.hasClass("delete-row")) {
        removed[removed.length] = line;
      }
    });
  clear_bufs(null);
  chunk.replaceClass('unified', 'sbs');

}

function toggle_unified_sbs(event) {
  event.preventDefault();
  var pts = Y.all(".pseudotable");
  if (unified) {
    pts && pts.each(make_sbs);
    unified = false;
    Y.get("#toggle_unified_sbs").set('innerHTML', "Show unified diffs");
  }
  else {
    pts && pts.each(make_unified);
    unified = true;
    Y.get("#toggle_unified_sbs").set('innerHTML', "Show diffs side-by-side");
  }
}

Y.on("click", toggle_unified_sbs, '#toggle_unified_sbs');

function toggle_expand_all_revisionview(action)
{
  var diffs = Y.all('.diff');
  if (diffs == null) return;
  diffs.each(
    function(item, i)
    {
      var collapsable = item.collapsable;
      if(action == 'close')
      {
        Y.get('#expand_all').setStyle('display','block');
        Y.get('#collapse_all').setStyle('display','none');
        collapsable.close();
      }
      else if(action == 'open')
      {
        Y.get('#expand_all').setStyle('display','none');
        Y.get('#collapse_all').setStyle('display','block');
        collapsable.open();
      }
    });
}

Y.on(
  'click',
  function (event) {
    event.preventDefault();
    toggle_expand_all_revisionview('open');
  },
  '#expand_all a'
);

Y.on(
  'click',
  function (event) {
    event.preventDefault();
    toggle_expand_all_revisionview('close');
  },
  '#collapse_all a'
);

function node_process(node) {
  if (!unified) {
    node.get('children').filter('.pseudotable').each(make_sbs);
  }
}

function zoom_to_diff (path) {
  var collapsable = Y.get('#' + path_to_id[path]).collapsable;
  if (!collapsable.is_open) {
    collapsable.open(
      function () {
        window.location.hash = '#' + path;
      });
  }
}

var original_diff_download_link = null;

function compute_diff_links() {
  var diffs = Y.all('.diff');
  if (diffs == null) return;
  var numlines = document.getElementById('contextLines').value;
  diffs.each(
    function(item, i)
    {
      item.collapsable.source = global_path + '+filediff/' + link_data[item.get('id')] + '?context=' + numlines; 
    });
  if(original_diff_download_link == null) original_diff_download_link = document.getElementById('download_link').href;
  document.getElementById('download_link').href = original_diff_download_link + '?context=' + numlines;
}

function get_num_lines() {
  var numlines = document.getElementById('contextLines').value;
  return numlines;
}

Y.on(
  "domready", function () {
    Y.all(".show_if_js").removeClass("show_if_js");
    if (!specific_path) {
      Y.all("#list-files a").on(
        'click',
        function (e) {
          e.preventDefault();
          var path = decodeURIComponent(e.target.get('href').split('#')[1]);
          window.location.hash = '#' + path;
          zoom_to_diff(path);
        });
    }
    var diffs = Y.all('.diff');
    if (diffs == null) return;
    var numlines = document.getElementById('contextLines').value;
    diffs.each(
      function(item, i)
      {
        var source_url = global_path + '+filediff/' + link_data[item.get('id')] + '?context=' + numlines;
        item.query('.the-link').on(
          'click',
          function(e) {
            e.preventDefault();
            item.collapsable.source = global_path + '+filediff/' + link_data[item.get('id')] + '?context=' + document.getElementById('contextLines').value;
            collapsable.toggle();
          });
        var collapsable = new Collapsable(
          {
            expand_icon: item.query('.expand_diff'),
            open_node: item.query('.diffinfo'),
            close_node: null,
            source: source_url,
            is_open: specific_path != null,
            loading: item.query('.loading'),
            node_process: node_process
          });
       item.collapsable=collapsable;
       });
    compute_diff_links();
    if (window.location.hash && !specific_path) {
      zoom_to_diff(window.location.hash.substring(1));
    }
  });
