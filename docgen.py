#!/usr/bin/env python3

from enum import Enum
import glob

class DefType(Enum):
  FUNCTION = 0
  METHOD = 1
  CONSTRUCTOR = 2
  FIELD = 3
  CLASS_FIELD = 4
  ENUM = 5
  CONSTANT = 6
  GLOBAL_VAR = 7

  def is_field(type):
    return type == DefType.FIELD or type == DefType.CLASS_FIELD

  def is_method(type):
    return type == DefType.METHOD or type == DefType.CONSTRUCTOR

class Marker:
  DEF_START = "/***"
  DEF_END = "*/"

  def make(str):
    return "* \\" + str

  METHOD = make("method")
  CONSTRUCTOR = make("constructor")
  CONSTANT = make("constant")
  ENUM = make("enum")
  GLOBAL = make("global")
  FIELD = make("field")
  CLASS_FIELD = make("classfield")

  DESC = make("desc")
  PARAM = make("param")
  RETURN = make("return")
  PARAM_OPT = make("paramOpt")
  TYPE = make("type")
  DEFAULT = make("default")
  NAMESPACE = make("ns")

  to_def_type = [
    (METHOD, DefType.METHOD),
    (CONSTRUCTOR, DefType.CONSTRUCTOR),
    (FIELD, DefType.FIELD),
    (CLASS_FIELD, DefType.CLASS_FIELD),
    (ENUM, DefType.ENUM),
    (CONSTANT, DefType.CONSTANT),
    (GLOBAL, DefType.GLOBAL_VAR)
  ]

  def get(marker, line):
    return line[len(marker):].strip()

  def get_multiline(marker, lines, line_num = 0):
    if line_num > 0:
      lines = lines[line_num:]

    result = Marker.get(marker, lines[0])
    cur_line = 1

    while result.endswith("\\"):
      if cur_line == len(lines):
        break
      result = result[0:(len(result)) - 1] + lines[cur_line].strip()
      cur_line += 1

    return result, cur_line

class DocDef:
  def __init__(self):
    self.type = None
    self.title = None
    self.description = None
    self.namespace = None

  def get_title(self):
    if DefType.is_field(self.type) or self.type == DefType.METHOD:
      if self.type == DefType.FIELD or self.type == DefType.METHOD:
        return self.namespace.lower() + "." + self.title
      return self.namespace + "." + self.title
    return self.title

  def get_name_for_html(self):
    return self.title.replace('.', '_')

  def get_href(self):
    return "Reference_" + defTypeNames[self.type][0] + "_" + self.get_name_for_html()

class ParamDef:
  def __init__(self, label, optional):
    self.label = label
    self.optional = optional

class FunctionDef(DocDef):
  def __init__(self):
    super().__init__()

    self.type = DefType.FUNCTION
    self.params = []
    self.returns = None

class EnumDef(DocDef):
  def __init__(self):
    super().__init__()

    self.type = DefType.ENUM
    self.prefix = None

class ConstantDef(DocDef):
  def __init__(self):
    super().__init__()

    self.type = DefType.CONSTANT
    self.value_type = None

class FieldDef(ConstantDef):
  def __init__(self):
    super().__init__()

    self.type = DefType.FIELD
    self.default_value = None

class NamespaceInfo:
  def __init__(self):
    self.name = None
    self.is_enum_namespace = False
    self.docs_per_def = None

defTypeNames = {
  DefType.FUNCTION: ("functions", "Class methods"),
  DefType.METHOD: ("methods", "Instance methods"),
  DefType.CONSTRUCTOR: ("constructors", "Instance constructors"),
  DefType.FIELD: ("fields", "Instance fields"),
  DefType.CLASS_FIELD: ("class fields", "Class fields"),
  DefType.ENUM: ("enums", "Enums"),
  DefType.CONSTANT: ("constants", "Constants"),
  DefType.GLOBAL_VAR: ("globals", "Globals")
}

allNamespaces = {}
allHref = {}
docLists = []

def get_namespace_href(namespace_name):
  return "Reference_" + namespace_name

def get_namespace(namespace_name):
  if namespace_name in allNamespaces:
    return allNamespaces[namespace_name]

  ns_info = NamespaceInfo()
  ns_info.docs_per_def = {}

  for type in DefType:
    ns_info.docs_per_def[type.value] = []

  allNamespaces[namespace_name] = ns_info
  allHref[namespace_name] = get_namespace_href(namespace_name)

  return ns_info

def get_enum_namespace(namespace_name):
  if namespace_name in allNamespaces:
    return allNamespaces[namespace_name]

  ns_info = get_namespace(namespace_name)
  ns_info.is_enum_namespace = True

  return ns_info

class DocGroup:
  def __init__(self):
    self.doc_list = []
    self.namespaces = {}
    self.namespace_list = []
    self.count = 0
    self.has_desc = 0

  def add_namespace(self, doc_def):
    namespace_name = doc_def.namespace
    if namespace_name == None:
      return

    ns = None

    # Check if this namespace exists
    if not namespace_name in self.namespaces:
      ns = []
      self.namespaces[namespace_name] = ns
      self.namespace_list.append(namespace_name)

    ns = self.namespaces[namespace_name]
    ns.append(doc_def)

  def add_prefix(self, enum_def):
    prefix = enum_def.prefix
    if prefix == None:
      return

    ns = None

    # Check if this namespace exists
    if not prefix in self.namespaces:
      ns = []
      self.namespaces[prefix] = ns
      self.namespace_list.append(prefix)

    ns = self.namespaces[prefix]
    ns.append(enum_def)

    ns_info = get_enum_namespace(prefix)
    ns_info.docs_per_def[enum_def.type.value].append(enum_def)

def add_namespace_for_doc_def(group, doc_def):
  namespace_name = doc_def.namespace
  if namespace_name == None:
    if doc_def.type == DefType.ENUM:
      group.add_prefix(doc_def)
    return

  group.add_namespace(doc_def)

  ns_info = get_namespace(namespace_name)
  ns_info.docs_per_def[doc_def.type.value].append(doc_def)

def parse_base_def_marker(doc_def, line, lines, line_num):
  if line.startswith(Marker.DESC):
    description, num_lines = Marker.get_multiline(Marker.DESC, lines, line_num)
    doc_def.description = description
    return num_lines
  elif line.startswith(Marker.NAMESPACE):
    doc_def.namespace = Marker.get(Marker.NAMESPACE, line)
    return 0

  return None

def parse_function_def(title, type, lines):
  doc_def = FunctionDef()
  doc_def.title = title
  doc_def.type = type

  for line_num, line in enumerate(lines):
    line = line.strip()
    if line.startswith(Marker.DEF_END):
      break

    num_lines = parse_base_def_marker(doc_def, line, lines, line_num)
    if num_lines is None:
      # paramOpt
      if line.startswith(Marker.PARAM_OPT):
        result, num_lines = Marker.get_multiline(Marker.PARAM_OPT, lines, line_num)
        param_opt = ParamDef(result, True)
        doc_def.params.append(param_opt)
      # param
      elif line.startswith(Marker.PARAM):
        result, num_lines = Marker.get_multiline(Marker.PARAM, lines, line_num)
        param = ParamDef(result, False)
        doc_def.params.append(param)
      # return
      elif line.startswith(Marker.RETURN):
        result, num_lines = Marker.get_multiline(Marker.RETURN, lines, line_num)
        doc_def.returns = result

    line_num += num_lines or 0

  if type == DefType.CONSTRUCTOR:
    doc_def.title = doc_def.namespace

  return doc_def

def parse_generic_def(title, type, lines):
  doc_def = DocDef()
  doc_def.title = title
  doc_def.type = type

  for line_num, line in enumerate(lines):
    line = line.strip()
    if line.startswith(Marker.DEF_END):
      break

    line_num += parse_base_def_marker(doc_def, line, lines, line_num) or 0

  return doc_def

def parse_enum_def(title, lines):
  doc_def = EnumDef()
  doc_def.title = title

  for line_num, line in enumerate(lines):
    line = line.strip()
    if line.startswith(Marker.DEF_END):
      break

    line_num += parse_base_def_marker(doc_def, line, lines, line_num) or 0

  pos = title.find('_')
  if pos != -1:
    doc_def.prefix = title[0:(pos + 1)] + '*'

  return doc_def

def parse_constant_def(title, lines):
  doc_def = ConstantDef()
  doc_def.title = title

  for line_num, line in enumerate(lines):
    line = line.strip()
    if line.startswith(Marker.DEF_END):
      break

    num_lines = parse_base_def_marker(doc_def, line, lines, line_num)
    if num_lines is not None:
      line_num += num_lines
    # type
    elif line.startswith(Marker.TYPE):
      doc_def.value_type = Marker.get(Marker.TYPE, line)

  return doc_def

def parse_field_def(title, type, lines):
  doc_def = FieldDef()
  doc_def.title = title
  doc_def.type = type

  for line_num, line in enumerate(lines):
    line = line.strip()
    if line.startswith(Marker.DEF_END):
      break

    num_lines = parse_base_def_marker(doc_def, line, lines, line_num)
    if num_lines is not None:
      line_num += num_lines
    # type
    elif line.startswith(Marker.TYPE):
      doc_def.value_type = Marker.get(Marker.TYPE, line)
    # default
    elif line.startswith(Marker.DEFAULT):
      doc_def.default_value = Marker.get(Marker.DEFAULT, line)

  return doc_def

def parse_def(title, type, lines):
  if type == DefType.FUNCTION or type == DefType.METHOD or type == DefType.CONSTRUCTOR:
    return parse_function_def(title, type, lines)
  elif type == DefType.ENUM:
      return parse_enum_def(title, lines)
  elif type == DefType.CONSTANT:
    return parse_constant_def(title, lines)
  elif type == DefType.FIELD or type == DefType.CLASS_FIELD:
    return parse_field_def(title, type, lines)

  return parse_generic_def(title, type, lines)

def parse_doc_lines(lines):
  if len(lines) == 0:
    return None

  first_line = lines[0]

  for key, value in Marker.to_def_type:
    if first_line.startswith(key):
      title = first_line[len(key):].strip()
      return parse_def(title, value, lines)

  # Assume it's a function
  title = first_line[1:].strip()
  if len(title) == 0:
    return None

  return parse_function_def(title, DefType.FUNCTION, lines[1:])

def add_doc_def(doc_def):
  allHref[doc_def.get_title()] = doc_def.get_href()

  group = docLists[doc_def.type.value]
  group.doc_list.append(doc_def)
  group.count += 1

  add_namespace_for_doc_def(group, doc_def)

  if DefType.is_field(doc_def.type):
    docLists[DefType.FUNCTION.value].add_namespace(doc_def)

def read_file(file):
  is_parsing_doc = False
  doc_def = None
  doc_lines = []

  for line_in_file in file:
    line = line_in_file.strip()

    if line.startswith(Marker.DEF_START):
      is_parsing_doc = True
      continue
    elif line.startswith(Marker.DEF_END):
      doc_def = parse_doc_lines(doc_lines)
      doc_lines.clear()
      is_parsing_doc = False

    if doc_def:
      add_doc_def(doc_def)
      doc_def = None
    elif is_parsing_doc:
      doc_lines.append(line)

def can_write_namespace_link_list(type):
  if DefType.is_field(type) or type == DefType.CONSTRUCTOR:
    return False

  if type == DefType.FUNCTION or type == DefType.METHOD or type == DefType.ENUM:
    if len(docLists[type.value].namespace_list) == 0:
      return False

  if len(docLists[type.value].doc_list) == 0:
    return False

  return True

def get_namespace_title(type):
  if type == DefType.FUNCTION:
    return "Namespaces"

  return defTypeNames[type][1]

def get_namespace_href(namespace_name):
  return "Reference_" + namespace_name

def write_namespace_link_list(type):
  group = docLists[type.value]

  text = f"        <h3>{get_namespace_title(type)}</h3>\n"
  text += "        <ul>\n"

  if type == DefType.FUNCTION or type == DefType.METHOD or type == DefType.ENUM:
    for namespace_name in group.namespace_list:
      if type == DefType.ENUM and not allNamespaces[namespace_name].is_enum_namespace:
        continue

      href = get_namespace_href(namespace_name)
      text += f"            <li><a href=\"#{href}\">{namespace_name}</a></li>\n"
  else:
    for doc in group.doc_list:
      href = doc.get_href()
      title = doc.get_title()
      text += f"                    <li><a href=\"#{href}\">{title}</a></li>\n"

  return text + "        </ul>\n"

def can_write_namespace_contents_list(type):
  if type == DefType.CONSTANT or type == DefType.GLOBAL_VAR:
    return False

  return can_write_namespace_link_list(type)

def write_enum_namespace_contents_list():
  def_type = DefType.ENUM

  text = f"        <h3>{get_namespace_title(def_type)}</h3>\n"

  group = docLists[def_type.value]

  for namespace_name in group.namespace_list:
    namespace_info = allNamespaces[namespace_name]
    if not namespace_info.is_enum_namespace:
      continue

    text += f"            <p id=\"{get_namespace_href(namespace_name)}\">\n"
    text += f"                <h2><code>{namespace_name}</code></h2>\n"

    if len(namespace_info.docs_per_def[def_type.value]) == 0:
      break

    text += "                <ul>\n"

    for doc in namespace_info.docs_per_def[def_type.value]:
      text += f"                    <li><a href=\"#{doc.get_href()}\">{doc.get_title()}</a></li>\n"

    text += "                </ul>\n"
    text += "            </p>\n"

  return text

def write_namespace_contents_list(type):
  if type == DefType.ENUM:
    return write_enum_namespace_contents_list()

  text = f"        <h3>{defTypeNames[type][1]}</h3>\n"

  group = docLists[type.value]

  for namespace_name in group.namespace_list:
    text += f"            <p id=\"{get_namespace_href(namespace_name)}\">\n"
    text += "                <h2>" + namespace_name + "</h2>\n"

    namespace_info = allNamespaces[namespace_name]

    for def_type in DefType:
      if len(namespace_info.docs_per_def[def_type.value]) == 0:
        continue

      text += f"                <i>{defTypeNames[def_type][1]}:</i>\n"
      text += "                <ul>\n"

      for doc in namespace_info.docs_per_def[def_type.value]:
        text += f"                    <li><a href=\"#{doc.get_href()}\">{doc.get_title()}</a></li>\n"

      text += "                </ul>\n"

    text += "            </p>\n"

  return text

def can_write_docs(type):
  return docLists[type.value].count > 0

def parse_desc_xml_tag_params(input):
  tag_params = {}

  input = input.strip()

  while len(input) > 0:
    quote_start = input.find('"')
    if quote_start == -1:
      break

    param = input[:quote_start-1]
    if len(param) == 0:
      break

    quote_end = input[quote_start+1:].find('"')
    if quote_end == -1:
      break

    quote_end += quote_start + 1
    quote_start += 1

    tag_params[param] = input[quote_start:quote_end]

    input = input[quote_end+1:].strip()

  return tag_params

def process_description(input):
  LINKTO_TAG = "linkto"

  index = 0

  while True:
    replace_start = None
    link_to = None
    will_replace = False
    found_link = False
    use_code = False

    tag_start = input[index:].find('<')
    if tag_start == -1:
      break

    tag_start += index
    tag_end = input[tag_start+1:].find('>')
    if tag_end == -1:
      break

    tag_end += tag_start + 1
    content_start = tag_end + 1

    # Check if this is a linkto tag
    linkto_pos = input[tag_start+1:].find(LINKTO_TAG)
    if linkto_pos != -1:
      linkto_pos += tag_start + 1 + len(LINKTO_TAG)
      tag_params = parse_desc_xml_tag_params(input[linkto_pos:tag_end])

      if 'ref' in tag_params:
        if tag_params['ref'] in allHref:
          link_to = tag_params["ref"]
          found_link = True

        replace_start = input[:tag_start]
        will_replace = True

    tag_start = input[content_start:].find('</')
    if tag_start == -1:
      break

    tag_start += content_start
    tag_end = input[tag_start+1:].find('>')
    if tag_end == -1:
      break

    tag_end += tag_start + 1
    index = tag_end + 1

    if will_replace:
      contents = input[content_start:tag_start]
      if len(contents) == 0:
        contents = link_to or ''
        use_code = True

      if use_code:
        replace_start += "<code>"
      if found_link:
        replace_start += "<a href=\"#" + allHref[link_to] + "\">"

      output = replace_start + contents
      if found_link:
        output += "</a>"
      if use_code:
        output += "</code>"

      index = len(output)
      input = output + input[tag_end+1:]

  return input

def write_docdef_title(doc):
  return f"        <h3 style=\"margin-bottom: 8px;\"><code>{doc.get_title()}</code></h2>\n"

def write_docdef_description(doc):
  description = process_description(doc.description)
  return f"        <div style=\"margin-top: 8px; font-size: 14px;\">{description}</div>\n"

def write_docdef_type(doc):
  return f"        <div style=\"font-size: 14px;\"><b>Type: </b>{doc.value_type}</div>\n"

def write_generic_docs(doc):
  text = write_docdef_title(doc)

  if doc.description is not None:
    text += write_docdef_description(doc)

  return text

def write_function_parameters(doc):
  parameter_index = 0
  parameter_text = "("

  end_optional_parameters = False

  for parameter in doc.params:
    label = parameter.label[0:parameter.label.find('(') - 1]

    if parameter.optional and end_optional_parameters:
      parameter_text += "["
      end_optional_parameters = True

    if parameter_index == 0:
      parameter_text += label
    else:
      parameter_text += f", {label}"

    parameter_index += 1

  if end_optional_parameters:
    parameter_text += "]"
  parameter_text += ")"

  return parameter_text

def write_function_docs(doc):
  text = None
  title = doc.get_title()
  parameters = write_function_parameters(doc)
  description = doc.description
  returns = doc.returns

  if description is not None:
    text = f"        <h2 style=\"margin-bottom: 8px;\">{title}</h2>\n"
  else:
    text = f"        <h2 style=\"margin-bottom: 8px; color: red;\">{title}</h2>\n"

  text += f"        <code>{title}{parameters}</code>\n"

  if description is not None:
    text += write_docdef_description(doc)

  if len(doc.params) > 0:
    text += "        <div style=\"font-weight: bold; margin-top: 8px;\">Parameters:</div>\n"
    text += "        <ul style=\"margin-top: 0px; font-size: 14px;\">\n"

    for param in doc.params:
      description = process_description(param.label)
      text += f"        <li>{description}</li>\n"

    text += "        </ul>\n"

  if returns is not None:
    description = process_description(returns)

    text += "        <div style=\"font-weight: bold; margin-top: 8px;\">Returns:</div>\n"
    text += f"        <div style=\"font-size: 14px;\">{description}</div>\n"

  return text

def write_constant_docs(doc):
  text = write_docdef_title(doc)

  if doc.value_type is not None:
    text += write_docdef_type(doc)

  if doc.description is not None:
    text += write_docdef_description(doc)

  return text

def write_field_docs(doc):
  text = write_docdef_title(doc)

  if doc.value_type is not None:
    text += write_docdef_type(doc)

  default_value = doc.default_value
  if default_value is not None:
    text += f"        <div style=\"font-size: 14px;\"><b>Default: </b><code>{default_value}</code></div>\n"

  if doc.description is not None:
    text += write_docdef_description(doc)

  return text

def write_docdef(group, doc, type):
  text = f"        <p id=\"{doc.get_href()}\">\n"

  if type == DefType.FUNCTION or type == DefType.METHOD or type == DefType.CONSTRUCTOR:
    text += write_function_docs(doc)
  elif type == DefType.CONSTANT:
    text += write_constant_docs(doc)
  elif type == DefType.FIELD or type == DefType.CLASS_FIELD:
    text += write_field_docs(doc)
  else:
    text += write_generic_docs(doc)

  if doc.description is not None:
    group.has_desc += 1

  text += "        </p>\n"

  return text

def write_docs(type):
  text = f"        <h3>{defTypeNames[type][1]}</h3>\n"

  group = docLists[type.value]

  if type == DefType.CONSTANT or type == DefType.GLOBAL_VAR:
    for doc in group.doc_list:
      text += write_docdef(group, doc, type)
  else:
    for namespace_name in group.namespace_list:
      namespace_info = allNamespaces[namespace_name]

      for doc in namespace_info.docs_per_def[type.value]:
        text += write_docdef(group, doc, type)

  with_descriptions = str(group.has_desc)
  without_descriptions = str(group.count)

  text += f"        <p>{with_descriptions} out of {without_descriptions} {defTypeNames[type][0]} have descriptions. </p>\n"
  text += "        <hr/>\n"

  return text

def generate_doc_file(file):
  file.write("""
<html>
    <head>
        <title>Hatch Game Engine Documentation</title>
        <style>
            body {
                background-color: white;
                font-family: sans-serif;
                margin: 64px;
            }
            codefrag {
                display: inline;
                margin: 0px;
                font-family: monospace;
            }
            a {
                text-decoration: none;
                color: #4141F2;
            }
            .function_list {
                font-family: monospace;
                margin-top: 0.5em;
            }
            .function_list li {
                margin-top: 0.125em;
                margin-bottom: 0.125em;
            }
            code, pre.code {
                background-color: #f2f2f2;
                border-radius: 3px;
                padding: 3px;
            }
            codeBlock {
                background-color: #f2f2f2;
                border-radius: 3px;
                padding: 3px;
                line-height: 100%;
                word-break: normal;
                font-family: monospace;
            }
        </style>
    </head>

    <body>
        <div style=\"position: fixed; margin-top: -32px; margin-left: -96px; width: 100%; text-align: right; \">
            <a href=\"#Reference_top\">Back to top</a>
        </div>
        <h1 id=\"Reference_top\">Hatch Game Engine Reference</h1>"""
  )

  namespace_link_list = ""
  namespace_contents_list = ""
  docs_text = ""

  for type in DefType:
    # Sort namespace list alphabetically
    if type == DefType.FUNCTION or type == DefType.METHOD or type == DefType.ENUM:
      group = docLists[type.value]
      group.namespace_list.sort()

    # Write out all namespaces
    if can_write_namespace_link_list(type):
      namespace_link_list += write_namespace_link_list(type)

    # Write out what's in those namespaces
    if can_write_namespace_contents_list(type):
      namespace_contents_list += write_namespace_contents_list(type)

    # Write out docs
    if can_write_docs(type):
      docs_text += write_docs(type)

  file.write(namespace_link_list)
  file.write("        <hr/>\n")
  file.write(namespace_contents_list)
  file.write("        <hr/>\n")
  file.write(docs_text)
  file.write("    </body>\n")
  file.write("</html>\n")

def prepare():
  for i in range(len(DefType)):
    docLists.append(DocGroup())

def read_files(source_folder):
  for filename in glob.glob(source_folder + "/**/*.cpp", recursive=True):
    with open(filename) as file:
      read_file(file)

def main(argv, argc):
  source_folder = None
  output_file = None

  if argc >= 2:
    source_folder = argv[1]
    if argc >= 3:
      output_file = argv[2]

  if source_folder == "--usage" or not source_folder or not output_file:
    print("usage: docgen <source path> <output file>")
    return

  prepare()

  read_files(source_folder)

  with open(output_file, "w") as file:
    generate_doc_file(file)

if __name__ == '__main__':
  from sys import argv, exit

  main(argv, len(argv))
