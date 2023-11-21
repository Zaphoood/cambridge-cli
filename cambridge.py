#!/usr/bin/env python3
from typing import Iterable, List, Optional, Union, cast
import requests
import sys
from bs4 import BeautifulSoup, Tag
from dataclasses import dataclass
import logging
from format import roman, prepend, prepend_first_line, wrap

BASE_URL = "https://dictionary.cambridge.org/dictionary/english/"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/119.0",
}


class WordNotFound(ValueError):
    pass


@dataclass
class WordDefinition:
    guideword: Optional[str]
    explanation: str

    def __str__(self) -> str:
        out = "" if self.guideword is None else (self.guideword + ": ")
        out += wrap(self.explanation)

        return out


@dataclass
class WordInfo:
    word: str
    pos: Optional[str]
    definitions: List[WordDefinition]
    pronunciation_uk: Optional[str]
    pronunciation_us: Optional[str]

    def __str__(self) -> str:
        out = self.word
        if self.pos is not None:
            out += f" ({self.pos})"

        if None not in (self.pronunciation_uk, self.pronunciation_us):
            out += "\n\n\t"
        if self.pronunciation_uk:
            out += f"UK: /{self.pronunciation_uk}/"
            if self.pronunciation_us:
                out += ", "
        if self.pronunciation_us:
            out += f"US: /{self.pronunciation_us}/"

        if len(self.definitions) > 0:
            out += "\n"
        if len(self.definitions) == 1:
            out += "\n" + prepend("\t", str(self.definitions[0]))
        elif len(self.definitions) > 1:
            for i, definition in enumerate(self.definitions):
                definition_with_numeral = prepend_first_line(
                    roman(i + 1).lower().rjust(5) + " ", str(definition)
                )
                out += "\n" + prepend("\t", definition_with_numeral)

        return out


def get_page_for_word(word: str) -> str:
    assert len(word) > 0
    url = BASE_URL + word

    logging.info(f"Getting response from: {url}")

    response = requests.get(url, headers=HEADERS, allow_redirects=False)
    if response.status_code == 302 and response.headers.get("Location") == BASE_URL:
        raise WordNotFound(f"Could not find word '{word}'")
    if response.status_code != 200:
        print(f"ERROR: Could not get response")
        if word != word.lower():
            print(f"Trying '{word.lower()}' (lowercase)")
            return get_page_for_word(word.lower())
        sys.exit(1)

    return response.text


def parse_info(page_src: str) -> Iterable[WordInfo]:
    logging.info("Parsing page...")
    soup = BeautifulSoup(page_src, "html.parser")

    dictionary = select_first(soup, "div.pr.dictionary")
    if dictionary is None:
        logging.fatal("Dictionary element found")
        return []

    entries = dictionary.select("div.pr.entry-body__el")

    word_infos = [get_word_info_for_entry(entry) for entry in entries]
    return cast(Iterable[WordInfo], filter(lambda w: w is not None, word_infos))


def get_word_info_for_entry(entry: Union[BeautifulSoup, Tag]) -> Optional[WordInfo]:
    word = select_first(entry, "span.hw.dhw")
    if word is None:
        return None

    pronunciation_uk = None
    pronunciation_us = None
    pos = None
    definitions = []

    if (uk_pron_elem := select_first(entry, "span.uk.dpron-i span.ipa")) is not None:
        pronunciation_uk = uk_pron_elem.text

    if (us_pron_elem := select_first(entry, "span.us.dpron-i span.ipa")) is not None:
        pronunciation_us = us_pron_elem.text

    if (pos := select_first(entry, "span.pos.dpos")) is not None:
        pos = pos.text

    dsenses = entry.select("div.pr.dsense")
    if len(dsenses) > 0:
        for dsense in dsenses:
            guideword = select_first(dsense, "span.guideword.dsense_gw span")
            definition = select_first(dsense, "div.def.ddef_d.db")
            if definition is None:
                continue

            definitions.append(
                WordDefinition(
                    guideword.text if guideword is not None else None,
                    definition_get_inner(definition),
                )
            )

    word_info = WordInfo(
        word=word.text,
        pos=pos,
        definitions=definitions,
        pronunciation_uk=pronunciation_uk,
        pronunciation_us=pronunciation_us,
    )

    return word_info


def definition_get_inner(definition: Tag) -> str:
    joined = "".join(definition.strings).strip()
    if joined.endswith(":"):
        joined = joined[:-1]
    return joined


def select_first(soup: Union[BeautifulSoup, Tag], selector: str) -> Optional[Tag]:
    matches = soup.select(selector)
    if len(matches) < 1:
        logging.warning(f"No matches found for selector '{selector}'")
        return None

    if len(matches) > 1:
        logging.warning(
            f"Multiple matches found for selector '{selector}'; will use first match"
        )

    return matches[0]


def main():
    logging.basicConfig(level=logging.ERROR)
    if len(sys.argv) < 2:
        print(f"USAGE: {sys.argv[0]} WORD")
        sys.exit(1)

    word = sys.argv[1]
    try:
        page_src = get_page_for_word(word)
    except WordNotFound as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    word_infos = list(parse_info(page_src))

    if word_infos is None or len(word_infos) == 0:
        print("Couldn't get info for word")
        sys.exit(1)

    if len(word_infos) == 1:
        print(word_infos[0])
    else:
        for i, word_info in enumerate(word_infos):
            print(f"{i + 1}. {word_info}\n")


if __name__ == "__main__":
    main()
