import sys
import re
import json
import sys
import jinja2
import os
import contextlib
from jinja2 import Template
import argparse
from functools import lru_cache


@lru_cache(maxsize=5)
def get_template(name):
    latex_jinja_env = jinja2.Environment(
        block_start_string="\\BLOCK{",
        block_end_string="}",
        variable_start_string="\\VAR{",
        variable_end_string="}",
        comment_start_string="\\#{",
        comment_end_string="}",
        line_statement_prefix="%%",
        line_comment_prefix="%#",
        trim_blocks=True,
        autoescape=False,
        loader=jinja2.FileSystemLoader(os.path.abspath("templates/")),
    )
    template = latex_jinja_env.get_template(f"{name}.tex.jinja")
    return template


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--spells", "-f", type=str, nargs="+")
    parser.add_argument("characterclass", type=str, default="All")
    parser.add_argument("--sort", "-s", type=str, default="level")
    parser.add_argument("--twosided", "-2", action="store_true")
    parser.add_argument("--output", "-o", nargs="?")
    return parser.parse_args()


def spell_sorter(sortby):
    def sort_spell(x):
        srt = ""
        for elem in sortby:
            srt += str(x[1][elem])

        return srt

    return sort_spell


def main():
    args = parse_args()
    spells = {}

    for f in args.spells:
        with open(f) as jf:
            spells.update(json.load(jf))

    if args.characterclass != "All":
        spells = dict(filter(lambda x: args.characterclass in x[1]["classes"], spells.items()))

    spells = dict(sorted(spells.items(), key=spell_sorter(args.sort.split(','))))
    pages = generate_pages(spells, args.twosided)
    filename = args.output if args.output is not None else args.characterclass
    write_doc(filename, pages)


def write_doc(filename, pages):
    with open(f"{filename}.tex", "w+") as of:
        of.write(get_template("spelldeck").render(content="".join(pages)))


def generate_pages(spells, twosided=False):
    spellpages = []
    back = get_template("spellcard_back").render()
    for i in range(0, len(spells)+9, 10):
        spellpages.append(generate_page(list(spells.items())[i:i+10]))
        if twosided:
            spellpages.append(back)
    if not twosided:
        spellpages.append(back)
    return spellpages


def generate_page(spells):
    pagetemplate = get_template("spellpage")
    data = {}
    for i, spell in enumerate(spells):
        data[f"spell{i}"] = generate_spell(*spell)
    return pagetemplate.render(**data)


def generate_spell(spellname, spell):
    template = get_template("spellcard")
    spell["text"] = latex_format(spell["text"])
    if "text_card" in spell:
        spell["text_card"] = latex_format(spell["text_card"])

    return template.render(title=spellname, **spell)


def latex_format(text):
    text = re.sub(r"\*(?! )(([^*])*?)(?! )\*", "\\\\textbf{\\1}", text)
    text = re.sub(
        r"(\s|\()([0-9]*W(?:4|6|8|10|12|20)(?:\s*\+[0-9]+)?)", r"\1\\textbf{\2}", text
    )
    text = re.sub(r"([0-9]+)\sm", r"\1~m", text)
    return text

if __name__ == "__main__":
    main()
