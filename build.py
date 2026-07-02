#!/usr/bin/env python3
"""Build the awsCcpPrep static site from Terms/ markdown sources."""

import os
import re
import json
from string import Template
from collections import OrderedDict

import markdown as md_lib

SRC_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_FILE = os.path.join(OUTPUT_DIR, 'templates', 'base.html')

SOURCE_DIRS = [
    '1_Concepts', '2_Global_Infrastructure',
    '3_Billing_And_Support', '4_Services',
]

SKIP_FILES = {'.DS_Store', 'General_Markdown_Notes_Guide.md', 'GEMINI.md', 'AGENTS.md'}

YAML_RE = re.compile(r'^---\s*\n(.*?)\n---\s*\n', re.DOTALL)
WIKILINK_RE = re.compile(r'\[\[([^\]|]+)(?:\|([^\]]+))?\]\]')
HIGHLIGHT_RE = re.compile(r'==([^=]+)==')
IMAGE_EMBED_RE = re.compile(r'!\[\[[^\]]+\]\]')
HEADING_RE = re.compile(r'^# (.+)$', re.MULTILINE)


def parse_yaml_frontmatter(text):
    m = YAML_RE.match(text)
    if not m:
        return {}, text
    raw = m.group(1)
    body = text[m.end():]
    data = {}
    current_key = None
    for line in raw.split('\n'):
        s = line.strip()
        if not s:
            continue
        if ':' in s and not s.startswith('- ') and not s.startswith(' '):
            key, _, val = s.partition(':')
            current_key = key.strip()
            val = val.strip()
            data[current_key] = [val] if val else []
        elif current_key and s.startswith('- '):
            data[current_key].append(s[2:])
    return data, body


def parse_title(body):
    m = HEADING_RE.search(body.strip())
    return m.group(1).strip() if m else 'Untitled'

def strip_first_heading(body):
    return HEADING_RE.sub('', body, count=1).strip()


def root_prefix(output_path):
    depth = output_path.count('/')
    return '../' * depth if depth else ''


def build_page_map():
    page_map = {}
    for rel_dir in SOURCE_DIRS:
        src_dir = os.path.join(SRC_DIR, rel_dir)
        if not os.path.isdir(src_dir):
            continue
        for root, _dirs, files in os.walk(src_dir):
            for fname in files:
                if not fname.endswith('.md') or fname in SKIP_FILES:
                    continue
                fpath = os.path.join(root, fname)
                output_rel = os.path.relpath(fpath, SRC_DIR)
                output_path = output_rel.replace('.md', '.html')
                with open(fpath, 'r', encoding='utf-8') as fh:
                    content = fh.read()
                fm, body = parse_yaml_frontmatter(content)
                title = parse_title(body)
                page_map[title] = output_path
                stem = fname[:-3]
                if stem != title:
                    page_map[stem] = output_path
                aliases = fm.get('aliases', [])
                if isinstance(aliases, str):
                    aliases = [aliases]
                for alias in aliases:
                    alias = alias.strip()
                    if alias:
                        page_map[alias] = output_path
    return page_map


def resolve_wikilink(match, page_map, root):
    target = match.group(1).strip()
    display = match.group(2)
    href = page_map.get(target)
    if href:
        rel_path = root + href
    else:
        slug = target.lower().replace(' ', '-').replace('(', '').replace(')', '')
        slug = re.sub(r'[^a-z0-9-]', '', slug)
        rel_path = root + slug + '.html'
    text = display if display else target
    return f'<a href="{rel_path}">{text}</a>'


def preprocess_body(body, page_map, root):
    body = IMAGE_EMBED_RE.sub('', body)
    body = HIGHLIGHT_RE.sub(r'<mark>\1</mark>', body)
    body = WIKILINK_RE.sub(lambda m: resolve_wikilink(m, page_map, root), body)
    return body


def render_markdown(text):
    return md_lib.markdown(text, extensions=[
        'fenced_code', 'codehilite', 'tables', 'sane_lists',
    ])


def build_nav_tree(page_info):
    """Build a hierarchical nav tree: source_dir → subdir → pages."""
    tree = OrderedDict()
    for info in page_info:
        path = info['output_path']
        parts = path.split('/')
        level1 = parts[0]
        level2 = parts[1] if len(parts) > 2 else None

        if level1 not in tree:
            tree[level1] = {'pages': [], 'subdirs': OrderedDict()}

        if level2:
            if level2 not in tree[level1]['subdirs']:
                tree[level1]['subdirs'][level2] = {'pages': []}
            tree[level1]['subdirs'][level2]['pages'].append(info)
        else:
            tree[level1]['pages'].append(info)
    return tree


def _is_active(current_path, prefix):
    if current_path == prefix:
        return True
    if current_path.startswith(prefix + '/') or current_path.startswith(prefix + '_'):
        return True
    return False


def render_nav(tree, current_path, root):
    lines = []
    for dir_name, dir_data in tree.items():
        display = dir_name.replace('_', ' ')
        open_cls = ' open' if _is_active(current_path, dir_name) else ''
        lines.append('<div class="nav-folder">')
        lines.append(f'<button class="nav-folder-header{open_cls}" onclick="toggleFolder(this)">{display}</button>')
        lines.append(f'<div class="nav-folder-content{open_cls}">')

        # Direct pages under this folder
        for info in sorted(dir_data['pages'], key=lambda x: x['title'].lower()):
            href = root + info['output_path']
            cls = ' active' if info['output_path'] == current_path else ''
            lines.append(f'<a class="nav-item{cls}" href="{href}">{info["title"]}</a>')

        # Subdirectories
        for sub_name, sub_data in dir_data['subdirs'].items():
            sub_prefix = dir_name + '/' + sub_name
            sub_open = ' open' if _is_active(current_path, sub_prefix) else ''
            sub_display = sub_name.replace('_', ' ')
            lines.append('<div class="nav-subfolder">')
            lines.append(f'<button class="nav-subfolder-header{sub_open}" onclick="toggleFolder(this)">{sub_display}</button>')
            lines.append(f'<div class="nav-subfolder-content{sub_open}">')
            for info in sorted(sub_data['pages'], key=lambda x: x['title'].lower()):
                href = root + info['output_path']
                cls = ' active' if info['output_path'] == current_path else ''
                lines.append(f'<a class="nav-item{cls}" href="{href}">{info["title"]}</a>')
            lines.append('</div></div>')

        lines.append('</div></div>')
    return '\n'.join(lines)


def render_tags(tags):
    if not tags:
        return ''
    if isinstance(tags, str):
        tags = [tags]
    parts = []
    for t in tags:
        cls = 'tag-badge aws' if t.startswith('aws/') else 'tag-badge'
        parts.append(f'<span class="{cls}">{t}</span>')
    return '<div class="tags">' + ' '.join(parts) + '</div>'


def write_page(template, output_path, title, nav_html, content_html, root):
    html = template.safe_substitute(
        title=title,
        root=root,
        navigation=nav_html,
        content=content_html,
    )
    out_file = os.path.join(OUTPUT_DIR, output_path)
    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    with open(out_file, 'w', encoding='utf-8') as fh:
        fh.write(html)


def build():
    page_map = build_page_map()
    page_info = []

    with open(TEMPLATE_FILE, 'r') as fh:
        template = Template(fh.read())

    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # Collect all pages
    for rel_dir in SOURCE_DIRS:
        src_dir = os.path.join(SRC_DIR, rel_dir)
        if not os.path.isdir(src_dir):
            continue
        for root, _dirs, files in os.walk(src_dir):
            for fname in sorted(files):
                if not fname.endswith('.md') or fname in SKIP_FILES:
                    continue
                fpath = os.path.join(root, fname)
                output_rel = os.path.relpath(fpath, SRC_DIR)
                output_path = output_rel.replace('.md', '.html')
                with open(fpath, 'r', encoding='utf-8') as fh:
                    content = fh.read()
                fm, body = parse_yaml_frontmatter(content)
                title = parse_title(body)
                tags = fm.get('tags', [])
                if isinstance(tags, str):
                    tags = [tags]
                page_info.append({
                    'title': title,
                    'tags': tags,
                    'rel_dir': rel_dir,
                    'output_path': output_path,
                    'body': strip_first_heading(body),
                })

    nav_tree = build_nav_tree(page_info)

    # Write content pages
    for info in page_info:
        root = root_prefix(info['output_path'])
        body_html = preprocess_body(info['body'], page_map, root)
        body_html = render_markdown(body_html)
        tags_html = render_tags(info['tags'])

        # See Also section
        see_also = ''
        see_also_match = re.search(r'\*\*See Also:\*\*(.*?)$', body_html, re.DOTALL)
        if see_also_match:
            see_also = '<div class="see-also"><h3>See Also</h3>' + see_also_match.group(1) + '</div>'
            body_html = body_html.replace(see_also_match.group(0), '')

        nav_html = render_nav(nav_tree, info['output_path'], root)
        content_html = f'<h1>{info["title"]}</h1>\n{tags_html}\n{body_html}\n{see_also}'
        write_page(template, info['output_path'], info['title'], nav_html, content_html, root)

    # Directory indexes (all intermediate directories)
    all_dirs = set()
    for info in page_info:
        d = os.path.dirname(info['output_path'])
        while d:
            all_dirs.add(d)
            d = os.path.dirname(d)
    all_dirs.add('1_Concepts')
    all_dirs.add('2_Global_Infrastructure')
    all_dirs.add('3_Billing_And_Support')
    all_dirs.add('4_Services')

    for dir_path in sorted(all_dirs):
        pages_in_dir = [p for p in page_info if p['output_path'].startswith(dir_path + '/')]
        if not pages_in_dir:
            continue
        title_parts = dir_path.replace('_', ' ').split('/')
        page_title = ' / '.join(p.title() for p in title_parts)
        listing = []
        for p in sorted(pages_in_dir, key=lambda x: x['title'].lower()):
            href = root_prefix(dir_path + '/index.html') + p['output_path']
            listing.append(f'<li><a href="{href}">{p["title"]}</a></li>')
        listing_html = '<ul class="dir-listing">' + '\n'.join(listing) + '</ul>'

        root = root_prefix(dir_path + '/index.html')
        nav_html = render_nav(nav_tree, dir_path + '/', root)
        content_html = f'<h1>{page_title}</h1>\n<p>{len(pages_in_dir)} notes</p>\n{listing_html}'
        write_page(template, dir_path + '/index.html', page_title, nav_html, content_html, root)

    # Root index
    root = ''
    domain_list = []
    for _dir, label in [
        ('1_Concepts', 'Cloud Concepts'),
        ('2_Global_Infrastructure', 'Global Infrastructure'),
        ('3_Billing_And_Support', 'Billing, Pricing & Support'),
        ('4_Services', 'AWS Services'),
    ]:
        count = sum(1 for p in page_info if p['output_path'].startswith(_dir))
        domain_list.append(
            f'<li><a href="{_dir}/index.html"><strong>{label}</strong>'
            f'<span class="file-count">{count} notes</span></a></li>'
        )
    nav_html = render_nav(nav_tree, 'index.html', root)
    content_html = '''<h1>AWS Certified Cloud Practitioner (CLF-C02)</h1>
<p>Study notes organized by exam domain.</p>
<ul class="dir-listing">''' + '\n'.join(domain_list) + '\n</ul>'
    write_page(template, 'index.html', 'Home', nav_html, content_html, root)

    # Search index
    search_index = []
    for info in page_info:
        body_plain = re.sub(r'<[^>]+>', '', info['body'])
        body_plain = re.sub(r'==([^=]+)==', r'\1', body_plain)
        body_plain = re.sub(r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]', r'\1', body_plain)
        search_index.append({
            'title': info['title'],
            'path': info['output_path'],
            'tags': info['tags'],
            'section': os.path.dirname(info['output_path']),
            'content': body_plain[:500],
        })
    with open(os.path.join(OUTPUT_DIR, 'search-index.json'), 'w', encoding='utf-8') as fh:
        json.dump(search_index, fh, ensure_ascii=False)

    print(f'Done. {len(page_info)} pages + {len(all_dirs)} indexes + search index.')
    print(f'file://{os.path.join(OUTPUT_DIR, "index.html")}')
    print(f'python3 -m http.server -d "{OUTPUT_DIR}"')


if __name__ == '__main__':
    build()
