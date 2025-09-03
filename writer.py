import doc_globals

from enums import DefType
from parser import Parser

class Writer:
  def can_write_docs(type):
    return doc_globals.lists[type.value].count > 0

  def can_write_namespace_link_list(type):
    if DefType.is_field(type) or type == DefType.CONSTRUCTOR:
      return False

    if type == DefType.FUNCTION or type == DefType.METHOD or type == DefType.ENUM:
      if len(doc_globals.lists[type.value].namespace_list) == 0:
        return False

    if len(doc_globals.lists[type.value].doc_list) == 0:
      return False

    return True

  def can_write_namespace_contents_list(type):
    if type == DefType.CONSTANT or type == DefType.GLOBAL_VAR:
      return False

    return Writer.can_write_namespace_link_list(type)

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
        tag_params = Parser.parse_desc_xml_tag_params(input[linkto_pos:tag_end])

        if 'ref' in tag_params:
          if tag_params['ref'] in doc_globals.href:
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
          replace_start += "<a href=\"#" + doc_globals.href[link_to] + "\">"

        output = replace_start + contents
        if found_link:
          output += "</a>"
        if use_code:
          output += "</code>"

        index = len(output)
        input = output + input[tag_end+1:]

    return input
