#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys,os
"""
Example usage:
python robots2solr.py dir_with_robots/ output_dir/
"""

def convert(filename):
    """Converts robots.txt file into Solr-like XML format."""
    with file(sys.argv[2] + filename + '.xml', 'w') as xml_file:
        xml_file.write('<add>\n<doc>\n')
        domain = filename
        ext = filename.find('.txt')
        if ext >= 0:
            domain = domain[:ext]
        add_field(xml_file, "domain", domain)
        with file(sys.argv[1] + filename, 'r') as robots_file:
            for raw_line in robots_file:
                # remove whitespace
                line = raw_line.strip()

                # comments
                comment = line.find('#')
                if comment >= 0:
                    add_field(xml_file, "comment", line[comment + 1:].strip())
                    line = line[:comment].strip()

                # skip blank lines
                if line:

                    if ':' not in line:
                        # add to other field
                        add_field(xml_file, "other", line)
                        continue

                    # split line into field name and field value
                    field, value = [x.strip() for x in line.split(':', 1)]
                    field = field.lower()

                    # add new field to XML file
                    if field not in ['allow', 'disallow', 'crawl-delay', 'user-agent', 'sitemap']:
                        field = "other"
                        value = line

                    add_field(xml_file, field, value)

        xml_file.write('</doc>\n</add>\n')


def add_field(xml_file, field_name, field_value):
    """Adds a new Solr-like field to XML file."""
    if field_value:
        xml_file.write('<field name="' + field_name + '">' + encodeXMLText(field_value) + '</field>\n')


def encodeXMLText(text):
    """Converts XML special characters."""
    return text.replace("&", "&amp;").replace("\"", "&quot;").replace("'", "&apos;").replace("<", "&lt;").replace(">", "&gt;")


if __name__ == "__main__":
    for filename in os.listdir(sys.argv[1]):
        print '> ' + filename
        convert(filename)
