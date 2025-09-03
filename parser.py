from enums import DefType
from doc_def import DocDef, FunctionDef, ParamDef, EnumDef, ConstantDef, FieldDef
from marker import Marker

class Parser:
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

      num_lines = Parser.parse_base_def_marker(doc_def, line, lines, line_num)
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

      line_num += Parser.parse_base_def_marker(doc_def, line, lines, line_num) or 0

    return doc_def

  def parse_enum_def(title, lines):
    doc_def = EnumDef()
    doc_def.title = title

    for line_num, line in enumerate(lines):
      line = line.strip()
      if line.startswith(Marker.DEF_END):
        break

      line_num += Parser.parse_base_def_marker(doc_def, line, lines, line_num) or 0

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

      num_lines = Parser.parse_base_def_marker(doc_def, line, lines, line_num)
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

      num_lines = Parser.parse_base_def_marker(doc_def, line, lines, line_num)
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
      return Parser.parse_function_def(title, type, lines)
    elif type == DefType.ENUM:
        return Parser.parse_enum_def(title, lines)
    elif type == DefType.CONSTANT:
      return Parser.parse_constant_def(title, lines)
    elif type == DefType.FIELD or type == DefType.CLASS_FIELD:
      return Parser.parse_field_def(title, type, lines)

    return Parser.parse_generic_def(title, type, lines)

  def parse_doc_lines(lines):
    if len(lines) == 0:
      return None

    first_line = lines[0]

    for key, value in Marker.to_def_type:
      if first_line.startswith(key):
        title = first_line[len(key):].strip()
        return Parser.parse_def(title, value, lines)

    # Assume it's a function
    title = first_line[1:].strip()
    if len(title) == 0:
      return None

    return Parser.parse_function_def(title, DefType.FUNCTION, lines[1:])

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
