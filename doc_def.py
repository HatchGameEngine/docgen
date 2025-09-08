import doc_globals

from enums import DefType, defTypeNames
from namespace_info import NamespaceInfo

class DocDef:
  def __init__(self):
    self.type = None
    self.title = None
    self.description = None
    self.namespace = None

  def get_title(self):
    if DefType.is_field(self.type) or self.type == DefType.METHOD:
      namespace = self.namespace
      if self.type == DefType.FIELD or self.type == DefType.METHOD:
        namespace = namespace.lower()
      return namespace + "." + self.title
    return self.title

  def get_name_for_html(self):
    return self.get_title().replace('.', '_')

  def get_href(self):
    return "Reference_" + defTypeNames[self.type][0] + "_" + self.get_name_for_html()

  def add(doc_def):
    doc_globals.href[doc_def.get_title()] = doc_def.get_href()

    group = doc_globals.lists[doc_def.type.value]
    group.doc_list.append(doc_def)
    group.count += 1

    NamespaceInfo.add_for_doc_def(group, doc_def)

    if DefType.is_field(doc_def.type):
      doc_globals.lists[DefType.FUNCTION.value].add_namespace(doc_def)

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
