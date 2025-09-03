#!/usr/bin/env python3

import doc_globals
import glob

from marker import Marker
from doc_def import DocDef
from parser import Parser
from html_writer import HTMLWriter

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
      doc_def = Parser.parse_doc_lines(doc_lines)
      doc_lines.clear()
      is_parsing_doc = False

    if doc_def:
      DocDef.add(doc_def)
      doc_def = None
    elif is_parsing_doc:
      doc_lines.append(line)

def read_docs(source_folder):
  doc_globals.init()

  for filename in glob.glob(source_folder + "/**/*.cpp", recursive=True):
    with open(filename) as file:
      read_file(file)

def write_docs(output_file):
  with open(output_file, "w") as file:
    HTMLWriter.generate_doc_file(file)

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

  read_docs(source_folder)
  write_docs(output_file)

if __name__ == '__main__':
  from sys import argv, exit
  main(argv, len(argv))
