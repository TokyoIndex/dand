'''
Nicholas Cica
Data Wrangling the Pittsburgh OpenStreetMap Data
10/2016
-Audit
-Clean
-Export to CSV for Import to SQL Database
'''

import re

import xml.etree.cElementTree as ET
import pprint

from collections import defaultdict

import csv
import codecs
import cerberus
import schema

OSMFILE = "sample6.osm"
street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)
phone_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)
state_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)

print "Welcome to Pittsburgh!  Enjoy your stay!"
print "Let's explore the data..."

# Explore the Data
def count_tags(filename):
    tags = {}
    for event, elem in ET.iterparse(filename):
        if elem.tag not in tags.keys():
            tags[elem.tag] = 1
        else :
            tags[elem.tag] += 1
    print "Counting the Tags:"
    pprint.pprint(tags)
    return tags


#"lower", for tags that contain only lowercase letters and are valid,
#"lower_colon", for otherwise valid tags with a colon in their names,
#"problemchars", for tags with problematic characters, and
#"other", for other tags that do not fall into the other three categories.

lower = re.compile(r'^([a-z]|_)*$')
lower_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*$')
problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

def key_type(element, keys):
    if element.tag == "tag":
        k_val = element.get("k")
        if bool(lower.search(k_val)):
            keys["lower"] += 1
        elif bool(lower_colon.search(k_val)): 
            keys["lower_colon"] += 1
        elif bool(problemchars.search(k_val)):
            keys["problemchars"] += 1
        else:
            keys["other"] += 1
    #print keys
    return keys

def process_keys(filename):
	print "Now let's look for potenatial problems..."
	keys = {"lower": 0, "lower_colon": 0, "problemchars": 0, "other": 0}
	for _, element in ET.iterparse(filename):
		keys = key_type(element, keys)
	pprint.pprint(keys)
	return keys

# Find out how many unique users have contributed to the map of Pittsburgh
def unique_users(filename):
	print "Let's find out how many unique users have contributed to the map of Pittsburgh..."
	users = set()
	for _, element in ET.iterparse(filename):
		tag = element.tag
		if tag in [ 'node', 'way', 'relation']:
			id = element.attrib['uid']
			users.add(id)
	print 'Number of Unique Users: ', len(users)
	return users

### Audit the Data
# Streets Names
street_expected = ["Street", "Avenue", "Boulevard", "Drive", "Court", "Place", "Square", "Lane", "Road", 
            "Trail", "Parkway", "Commons", "Highway", "Way"]

street_mapping = { "St": "Street",
            "St.": "Street", 
            "Av": "Avenue",
            "Av.": "Avenue",
            "Ave": "Avenue",
            "Ave.": "Avenue",
            "Blvd": "Boulevard",
            "Ct": "Court",
            "Dr": "Drive",
            "Hwy": "Highway",
            "Pl": "Place",
            "Rd": "Road",
            "Rd.": "Road",
            "Sq": "Square",
            }

# Phone Numbers
phone_expected = ('412-', '1-', '724-')

# State Abbr,
state_expected = ["PA"]

state_mapping = {"pa": "PA",
				 "P": "PA",
				 "Pa": "PA",
				 "Ohio": "OH"
				 }

# audit
def audit_street_type(street_types, street_name):
    m = street_type_re.search(street_name)
    # print 'street', m
    if m:
        street_type = m.group()
        if street_type not in street_expected:
            street_types[street_type].add(street_name)

def audit_phone_number(phone_types, phone_numbers):
	m = phone_type_re.search(phone_numbers)
	# print 'phone', m
	if m:
		phone_type = m.group()
		#if phone_type not in phone_expected:
		if not phone_type.startswith((phone_expected)):
			phone_types[phone_type].add(phone_numbers)

def audit_state_type(state_types, state_name):
    m = state_type_re.search(state_name)
    # print 'state', m
    if m:
        state_type = m.group()
        if state_type not in state_expected:
            state_types[state_type].add(state_name)


# Identify elements
def is_street_name(elem):
    return (elem.attrib['k'] == "addr:street")

def is_phone_number(elem):
    return (elem.attrib['k'] == "phone")

# add one for states
def is_state(elem):
    return (elem.attrib['k'] == "addr:state")

# Main Audit Function
def audit(osmfile):
	print "Now its time to audit the data..."
	print "Let's take a look at street names, phone numbers, and state abbrivations..."
	print "\n"
	print "Hmm, something's fishy with our data...some human must have handled the data entry..."
	print "\n"
	osm_file = open(osmfile, "r")
	street_types = defaultdict(set)
	phone_types = defaultdict(set)
	state_types = defaultdict(set)
	for event, elem in ET.iterparse(osm_file, events=("start",)):
		if elem.tag == "node" or elem.tag == "way":
			for tag in elem.iter("tag"):
				if is_street_name(tag):
					audit_street_type(street_types, tag.attrib['v'])
					# testing update - move to shapping
					#better_name = update_street_name(tag.attrib['v'], street_mapping)
					#print 'Updated Street Name: ', better_name
				if is_phone_number(tag):
					# print 'Unformated Phone: ', tag.attrib['v']
					audit_phone_number(phone_types, tag.attrib['v'])
					# testing update - move to shapping
					#formatted_phone_number =  phone_format(tag.attrib['v'])
					#print 'Formated Phone: ', formatted_phone_number
				if is_state(tag):
					#print 'Unformated State: ', tag.attrib['v']
					audit_state_type(state_types, tag.attrib['v'])
					#better_state_name = update_state_name(tag.attrib['v'], state_mapping)
					#print 'Updated State Name: ', better_state_name

	osm_file.close()
	print 'Street Outliers:', street_types
	print "\n"
	print 'Phone Outliers:', phone_types
	print "\n"
	print 'State Abbr. Outliers:', state_types
	print "\n"
	return street_types, phone_types, state_types

### Clean the Data
#print "Now we have to clean up their mess!"
def update_street_name(name, mapping):
    m = street_type_re.search(name)
    better_name = name
    if m:
        if m.group() in mapping.keys():
            #print 'BEFORE'
            #print name
            better_name = re.sub(m.group(),mapping[m.group()], name)
            #print 'AFTER'
            #print better_name
        # else:
            # print 'Not in Mapping:', m.group()
    return better_name

def phone_format(phone_number):
    clean_phone_number = re.sub('[^0-9]+', '', phone_number)
    formatted_phone_number = re.sub("(\d)(?=(\d{3})+(?!\d))", r"\1-", "%d" % int(clean_phone_number[:-1])) + clean_phone_number[-1]
    return formatted_phone_number

def update_state_name(name, mapping):
	m = state_type_re.search(name)
	better_name = name
	if m:
		if m.group() in mapping.keys():
			#print 'BEFORE'
			#print name
			better_name = re.sub(m.group(),mapping[m.group()], name)
			#print 'AFTER'
			#print better_name
		# else:
			# print 'Not in Mapping:', m.group()
	return better_name


# SHAPE
OSM_PATH = "sample6.osm"

NODES_PATH = "nodes.csv"
NODE_TAGS_PATH = "nodes_tags.csv"
WAYS_PATH = "ways.csv"
WAY_NODES_PATH = "ways_nodes.csv"
WAY_TAGS_PATH = "ways_tags.csv"

LOWER_COLON = re.compile(r'^([a-z]|_)+:([a-z]|_)+')
PROBLEMCHARS = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

SCHEMA = schema.schema

# Make sure the fields order in the csvs matches the column order in the sql table schema
NODE_FIELDS = ['id', 'lat', 'lon', 'user', 'uid', 'version', 'changeset', 'timestamp']
NODE_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_FIELDS = ['id', 'user', 'uid', 'version', 'changeset', 'timestamp']
WAY_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_NODES_FIELDS = ['id', 'node_id', 'position']

def shape_element(element, node_attr_fields=NODE_FIELDS, way_attr_fields=WAY_FIELDS,
					problem_chars=PROBLEMCHARS, default_tag_type='regular'):
	"""Clean and shape node or way XML element to Python dict"""

	node_attribs = {}
	way_attribs = {}
	way_nodes = []
	tags = [] 

	if element.tag == 'node':
		for node in NODE_FIELDS:
			node_attribs[node] = element.attrib[node]
		for child in element:
			tag = {}
			if PROBLEMCHARS.search(child.attrib["k"]):
				continue
	
			elif LOWER_COLON.search(child.attrib["k"]):
			
				tag_type = child.attrib["k"].split(':',1)[0]
				tag_key = child.attrib["k"].split(':',1)[1]
				tag["key"] = tag_key
				if tag_type:
					tag["type"] = tag_type
				else:
					tag["type"] = 'unspecified'
			
				tag["id"] = element.attrib["id"]
				if child.attrib['k'] == "addr:street":
					tag['value'] = update_street_name(child.attrib['v'], street_mapping)
					#print "Node (problem) address updated"
				if child.attrib['k'] == "phone":
					tag['value'] = phone_format(child.attrib['v'])
					#print "Node (problem) phone updated"
				if child.attrib['k'] == "addr:state":
					tag['value'] = update_state_name(child.attrib['v'], state_mapping)
					#print "Node (problem) state updated"
				else:
					tag["value"] = child.attrib["v"]
			else:
				if child.attrib['k'] == "addr:street":
					tag['value'] = update_street_name(child.attrib['v'], street_mapping)
					#print "Node address updated"
				if child.attrib['k'] == "phone":
					tag['value'] = phone_format(child.attrib['v'])
					#print "Node phone updated"
				if child.attrib['k'] == "addr:state":
					tag['value'] = update_state_name(child.attrib['v'], state_mapping)
					#print "Node state updated"
				else:
					tag["value"] = child.attrib["v"]
				tag["key"] = child.attrib["k"]
				tag["type"] = "unspecified"
				tag["id"] = element.attrib["id"]
			if tag:
				tags.append(tag)
			return {'node': node_attribs, 'node_tags': tags}
	
	elif element.tag == 'way':
		for way in WAY_FIELDS:
			way_attribs[way] = element.attrib[way]
		for child in element:
			nd = {}
			tag = {}
			if child.tag == 'tag':
				if PROBLEMCHARS.search(child.attrib["k"]):
					continue
				elif LOWER_COLON.search(child.attrib["k"]):
					tag_type = child.attrib["k"].split(':',1)[0]
					tag_key = child.attrib["k"].split(':',1)[1]
					tag["key"] = tag_key
					if tag_type:
						tag["type"] = tag_type
					else:
						tag["type"] = 'unspecified'
					tag["id"] = element.attrib["id"]
					if child.attrib['k'] == "addr:street":
						tag['value'] = update_street_name(child.attrib['v'], street_mapping)
						#print "Way (problem) address updated"
					if child.attrib['k'] == "phone":
						tag['value'] = phone_format(child.attrib['v'])
						#print "Way (problem) phone updated"
					if child.attrib['k'] == "addr:state":
						tag['value'] = update_state_name(child.attrib['v'], state_mapping)
						#print "Way (problem) state updated"
					else:
						tag["value"] = child.attrib["v"]
	
				else:
					if child.attrib['k'] == "addr:street":
						tag['value'] = update_street_name(child.attrib['v'], street_mapping)
						#print "Way address updated"
					if child.attrib['k'] == "phone":
						tag['value'] = phone_format(child.attrib['v'])
						#print "Way phone updated"
					if child.attrib['k'] == "addr:state":
						tag['value'] = update_state_name(child.attrib['v'], state_mapping)
						#print "Way state updated"
					else:
						tag["value"] = child.attrib["v"]
					tag["key"] = child.attrib["k"]
					tag["type"] = "unspecified"
					tag["id"] = element.attrib["id"]
				if tag:
					tags.append(tag)

			elif child.tag == 'nd':
				nd['id'] = element.attrib["id"]
				nd['node_id'] = child.attrib["ref"]
				nd['position'] = len(way_nodes)
	
				if nd:
					way_nodes.append(nd)
			else:
				continue
		return {'way': way_attribs, 'way_nodes': way_nodes, 'way_tags': tags}

# ================================================== #
#               Helper Functions                     #
# ================================================== #
def get_element(osm_file, tags=('node', 'way', 'relation')):
    """Yield element if it is the right type of tag"""

    context = ET.iterparse(osm_file, events=('start', 'end'))
    _, root = next(context)
    for event, elem in context:
        if event == 'end' and elem.tag in tags:
            yield elem
            root.clear()


def validate_element(element, validator, schema=SCHEMA):
    """Raise ValidationError if element does not match schema"""
    if validator.validate(element, schema) is not True:
        field, errors = next(validator.errors.iteritems())
        message_string = "\nElement of type '{0}' has the following errors:\n{1}"
        error_strings = (
            "{0}: {1}".format(k, v if isinstance(v, str) else ", ".join(v))
            for k, v in errors.iteritems()
        )
        raise cerberus.ValidationError(
            message_string.format(field, "\n".join(error_strings))
        )


class UnicodeDictWriter(csv.DictWriter, object):
    """Extend csv.DictWriter to handle Unicode input"""

    def writerow(self, row):
        super(UnicodeDictWriter, self).writerow({
            k: (v.encode('utf-8') if isinstance(v, unicode) else v) for k, v in row.iteritems()
        })

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)


# ================================================== #
#               Main Function                        #
# ================================================== #
def process_map(file_in, validate):
    """Iteratively process each XML element and write to csv(s)"""
    print "Now Let's clean and prepare the data for our database!"

    with codecs.open(NODES_PATH, 'w') as nodes_file, \
         codecs.open(NODE_TAGS_PATH, 'w') as nodes_tags_file, \
         codecs.open(WAYS_PATH, 'w') as ways_file, \
         codecs.open(WAY_NODES_PATH, 'w') as way_nodes_file, \
         codecs.open(WAY_TAGS_PATH, 'w') as way_tags_file:

        nodes_writer = UnicodeDictWriter(nodes_file, NODE_FIELDS)
        node_tags_writer = UnicodeDictWriter(nodes_tags_file, NODE_TAGS_FIELDS)
        ways_writer = UnicodeDictWriter(ways_file, WAY_FIELDS)
        way_nodes_writer = UnicodeDictWriter(way_nodes_file, WAY_NODES_FIELDS)
        way_tags_writer = UnicodeDictWriter(way_tags_file, WAY_TAGS_FIELDS)

        nodes_writer.writeheader()
        node_tags_writer.writeheader()
        ways_writer.writeheader()
        way_nodes_writer.writeheader()
        way_tags_writer.writeheader()

        validator = cerberus.Validator()

        for element in get_element(file_in, tags=('node', 'way')):
            el = shape_element(element)
            if el:
                if validate is True:
                    validate_element(el, validator)

                if element.tag == 'node':
                    nodes_writer.writerow(el['node'])
                    node_tags_writer.writerows(el['node_tags'])
                elif element.tag == 'way':
                    ways_writer.writerow(el['way'])
                    way_nodes_writer.writerows(el['way_nodes'])
                    way_tags_writer.writerows(el['way_tags'])

 	print "Data processing complete!"



if __name__ == '__main__':
	count_tags(OSMFILE)
	process_keys(OSMFILE)
	unique_users(OSMFILE)
	audit(OSMFILE)
	#st_types = audit(OSMFILE)
	#for st_type, ways in st_types.iteritems():
	#	for name in ways:
	#		better_name = update_street_name(name, mapping)
	#		print 'Updated Street Name: ', better_name
	process_map(OSM_PATH, validate=False)