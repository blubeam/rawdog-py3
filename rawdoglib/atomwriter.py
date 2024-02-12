"""
Python module to generate Atom Syndication Format from feedparser data
structures.

The intention is to capture as much of the data available from feedparser as
Atom is able to represent, even for feeds that weren't Atom (or even valid RSS)
to start with, so the output from this module may not be valid Atom.

Adam Sampson <ats@offog.org>
"""

# FIXME: not writing dates for zeptobars?

# FIXME: Add test suite: given a feed file, check that parsing it with
# feedparser, writing it out with this, then parsing it again gives the same
# result. Try this out with all my rawdog feeds...

import xml.dom.minidom, codecs, time

atom_ns = "http://purl.org/atom/ns#"
w3_time_format = "%Y-%m-%dT%H:%M:%SZ"

def set_attr(node, name, value):
	if value is None:
		return
	node.setAttribute(name, value)

def add_text(doc, node, value):
	if value is None:
		return
	node.appendChild(doc.createTextNode(value))

def add_content(doc, node, name, data):
	if data is None:
		return
	content = doc.createElement(name)
	add_text(doc, content, data.get("value"))
	content.setAttribute("mode", "escaped")
	set_attr(content, "type", data.get("type"))
	set_attr(content, "xml:lang", data.get("language"))
	set_attr(content, "xml:base", data.get("base"))
	node.appendChild(content)

def add_link(doc, node, name, data):
	if data is None:
		return
	link = doc.createElement(name)
	set_attr(link, "rel", data.get("rel"))
	set_attr(link, "type", data.get("type"))
	set_attr(link, "href", data.get("href"))
	set_attr(link, "title", data.get("title"))
	node.appendChild(link)

def add_generator(doc, node, name, data):
	if data is None:
		return
	generator = doc.createElement(name)
	add_text(doc, generator, data.get("name"))
	set_attr(generator, "url", data.get("url"))
	set_attr(generator, "version", data.get("version"))
	node.appendChild(generator)

def add_date(doc, node, name, data):
	if data is None:
		return
	date = doc.createElement(name)
	add_text(doc, date, time.strftime(w3_time_format, data))
	node.appendChild(date)

def add_plain(doc, node, name, data):
	if data is None:
		return
	plain = doc.createElement(name)
	add_text(doc, plain, data)
	node.appendChild(plain)

def add_person(doc, node, name, data):
	if data is None:
		return
	person = doc.createElement(name)
	add_plain(doc, person, "name", data.get("name"))
	add_plain(doc, person, "url", data.get("url"))
	add_plain(doc, person, "email", data.get("email"))
	node.appendChild(person)

def add_entry(doc, node, name, data):
	if data is None:
		return
	entry = doc.createElement(name)

	add_content(doc, entry, "title", data.get("title_detail"))
	links_d = data.get("links")
	if links_d is not None:
		for link_d in links_d:
			add_link(doc, entry, "link", link_d)
	add_content(doc, entry, "summary", data.get("summary_detail"))
	contents_d = data.get("content")
	# This is not strictly correct, according to the Atom 0.3 spec for
	# multiple content, but feedparser gets confused if it's given a
	# multipart content.
	if contents_d is not None:
		for content_d in contents_d:
			add_content(doc, entry, "content", content_d)
	add_date(doc, entry, "issued", data.get("issued_parsed"))
	add_date(doc, entry, "created", data.get("created_parsed"))
	add_date(doc, entry, "modified", data.get("modified_parsed"))
	# Not supported: expired
	add_plain(doc, entry, "id", data.get("id"))
	add_person(doc, entry, "author", data.get("author_detail"))
	conts_d = data.get("contributors")
	if conts_d is not None:
		for cont_d in conts_d:
			add_person(doc, entry, "contributor", cont_d)
	# Not supported: enclosures, publisher, category, categories, source,
	# comments, license

	node.appendChild(entry)

def write_atom(data, f, encoding = "UTF-8"):
	"""Given the result of 'feedparser.parse' (or an equivalent data
	structure generated by other means), produce Atom Syndication Format
	XML output to the given file using the given encoding.

	For elements where feedparser provides a _detail or _parsed version of
	their content, this function will only use that version; for example,
	"title_detail" provides the content for atom:title, and "title" is
	ignored, even if "title_detail" is not present."""

	doc = xml.dom.minidom.Document()
	feed = doc.createElement("feed")
	feed.setAttribute("xmlns", atom_ns)
	feed.setAttribute("version", "0.3")

	feed_d = data["feed"]
	add_content(doc, feed, "title", feed_d.get("title_detail"))
	links_d = feed_d.get("links")
	if links_d is not None:
		for link_d in links_d:
			add_link(doc, feed, "link", link_d)
	add_content(doc, feed, "tagline", feed_d.get("tagline_detail"))
	add_content(doc, feed, "copyright", feed_d.get("copyright_detail"))
	add_generator(doc, feed, "generator", feed_d.get("generator_detail"))
	add_content(doc, feed, "info", feed_d.get("info_detail"))
	add_date(doc, feed, "modified", feed_d.get("modified_parsed"))
	add_plain(doc, feed, "id", feed_d.get("id"))
	add_person(doc, feed, "author", feed_d.get("author_detail"))
	conts_d = feed_d.get("contributors")
	if conts_d is not None:
		for cont_d in conts_d:
			add_person(doc, feed, "contributor", cont_d)
	# Not supported: image, textinput, cloud, published, category,
	# categories, docs, ttl, language, license, errorreportsto

	entries_d = data["entries"]
	entries = doc.createElement("entries")
	for entry_d in entries_d:
		add_entry(doc, entries, "entry", entry_d)
	feed.appendChild(entries)

	doc.appendChild(feed)
	doc.writexml(codecs.getwriter(encoding)(f), "", " ", "\n", encoding)
	doc.unlink()

if __name__ == "__main__":
	import feedparser, sys
	for arg in sys.argv[1:]:
		data = feedparser.parse(arg)
		write_atom(data, sys.stdout)