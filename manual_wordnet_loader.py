import os
import re

class WordNetLoader:
    """
    Pure WordNet loader from dict/ folder (no NLTK)
    Supports hypernym, similar-to, meronym relations.
    """

    POINTER_MAP = {
        "@": "hypernym",
        "~": "hyponym",
        "&": "similar",
        "%": "meronym",
        "%p": "meronym",
        "%s": "meronym",
        "%m": "meronym",
    }

    def __init__(self, dict_path):
        self.path = dict_path
        self.synsets = {}
        self.index = {"n": {}, "v": {}, "a": {}, "r": {}}

    def load(self):
        self._load_pos("noun", "n")
        self._load_pos("verb", "v")
        self._load_pos("adj", "a")
        self._load_pos("adv", "r")
        print("WordNet Loaded Successfully.")
        print(f"Total synsets loaded: {len(self.synsets)}")

    # -----------------------------------------------------
    # Load index + data files
    # -----------------------------------------------------
    def _load_pos(self, name, pos):
        index_file = os.path.join(self.path, f"index.{name}")
        data_file = os.path.join(self.path, f"data.{name}")

        if not os.path.exists(index_file):
            print(f"Missing file: {index_file}")
            return

        if not os.path.exists(data_file):
            print(f"Missing file: {data_file}")
            return

        # ------------------------------
        # Load INDEX (word → synset IDs)
        # ------------------------------
        with open(index_file, "r", encoding="utf8") as f:
            for line in f:
                if line.startswith("  ") or line.startswith(" "):
                    continue
                if line.startswith("Sense"):
                    continue

                parts = line.split()
                if len(parts) < 6:
                    continue

                lemma = parts[0]
                synset_count = int(parts[2])
                synset_offsets = parts[-synset_count:]

                self.index[pos][lemma.lower()] = synset_offsets

        # ------------------------------
        # Load DATA (synsets)
        # ------------------------------
        with open(data_file, "r", encoding="utf8") as f:
            for line in f:
                if line.startswith("  ") or line.startswith(" "):
                    continue

                if "|" not in line:
                    continue

                data_part, gloss = line.split("|", 1)
                parts = data_part.split()

                offset = parts[0]
                lex_filenum = parts[1]
                ss_type = parts[2]              # n, v, a, r
                lemma_count = int(parts[3], 16) # hex number

                lemmas = []
                i = 4
                for _ in range(lemma_count):
                    lemma = parts[i]
                    lemmas.append(lemma.replace("_", " "))
                    i += 2  # skip lex_id

                ptr_count = int(parts[i])
                i += 1

                relations = {
                    "hypernym": [],
                    "hyponym": [],
                    "similar": [],
                    "meronym": []
                }

                for _ in range(ptr_count):
                    symbol = parts[i]
                    target = parts[i + 1]
                    i += 4

                    if symbol in self.POINTER_MAP:
                        rel = self.POINTER_MAP[symbol]
                        relations[rel].append(target)

                self.synsets[offset] = {
                    "pos": ss_type,
                    "gloss": gloss.strip(),
                    "lemmas": lemmas,
                    "relations": relations
                }
