(function() {
  var root = typeof ROOT_PATH !== 'undefined' ? ROOT_PATH : '';
  var indexUrl = root + 'search-index.json';
  var searchIndex = [];

  var input = document.getElementById('search-input');
  var results = document.getElementById('search-results');
  if (!input || !results) return;

  function normalize(t) { return t.toLowerCase().replace(/[^a-z0-9\s]/g, ''); }

  var xhr = new XMLHttpRequest();
  xhr.open('GET', indexUrl, true);
  xhr.onload = function() {
    if (xhr.status === 200) {
      try { searchIndex = JSON.parse(xhr.responseText); } catch(e) {}
    }
  };
  xhr.send();

  input.addEventListener('input', function() {
    var q = normalize(this.value).trim();
    results.innerHTML = '';
    if (q.length < 2) { results.classList.remove('has-results'); return; }

    var terms = q.split(/\s+/);
    var hits = [];

    for (var i = 0; i < searchIndex.length; i++) {
      var item = searchIndex[i];
      var text = normalize(item.title + ' ' + item.tags.join(' ') + ' ' + item.content);
      var match = true;
      for (var t = 0; t < terms.length; t++) {
        if (text.indexOf(terms[t]) === -1) { match = false; break; }
      }
      if (match) hits.push(item);
      if (hits.length >= 20) break;
    }

    if (hits.length === 0) { results.classList.remove('has-results'); return; }

    results.classList.add('has-results');
    for (var h = 0; h < hits.length; h++) {
      var a = document.createElement('a');
      a.href = root + hits[h].path;
      a.innerHTML = hits[h].title + '<span class="search-path">' + hits[h].section + '</span>';
      results.appendChild(a);
    }
  });

  document.addEventListener('click', function(e) {
    if (!results.contains(e.target) && e.target !== input) {
      results.classList.remove('has-results');
    }
  });
})();
