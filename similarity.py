# from neo4j import GraphDatabase
# import nltk
# from nltk.corpus import wordnet as wn

# nltk.download("wordnet")

# URI = "neo4j://127.0.0.1:7687"
# USER = "neo4j"
# PASSWORD = "wordnet-similarity1"

# driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))

# # ---------- AUTOCOMPLETE (word-level, not synset IDs) ----------

# WORDLIST = sorted({
#     lemma.replace("_", " ").lower()
#     for syn in wn.all_synsets("n")
#     for lemma in syn.lemma_names()
# })

# def autocomplete_words(prefix: str, limit: int = 8):
#     prefix = prefix.lower()
#     return [w for w in WORDLIST if w.startswith(prefix)][:limit]


# # ---------- CORE GRAPH HELPERS ----------

# def shortest_path_with_details(id1: str, id2: str):
#     if id1 == id2:
#         return [id1], [], 0

#     query = """
#     MATCH (a:Synset {id:$id1}), (b:Synset {id:$id2})
#     MATCH p = shortestPath(
#         (a)-[:HYPERNYM_OF|HYPONYM_OF|SIMILAR_TO|PART_OF*..10]-(b)
#     )
#     RETURN p
#     """

#     with driver.session() as session:
#         record = session.run(query, id1=id1, id2=id2).single()
#         if not record:
#             return None, None, None

#         path = record["p"]
#         nodes = [n["id"] for n in path.nodes]
#         # ⬇️ THIS LINE:
#         rels = [r.type for r in path.relationships]   # HYPERNYM_OF, HYPONYM_OF, SIMILAR_TO
#         dist = len(nodes) - 1
#         return nodes, rels, dist



# def get_definitions(ids):
#     """Return dict {synset_id: definition} for given synset ids."""
#     if not ids:
#         return {}
#     query = """
#     MATCH (s:Synset)
#     WHERE s.id IN $ids
#     RETURN s.id AS id, s.definition AS def
#     """
#     with driver.session() as session:
#         return {r["id"]: r["def"] for r in session.run(query, ids=ids)}


# # ---------- PATH SIMILARITY ----------

# def path_similarity(word1: str, word2: str, pos: str = "n"):
#     """
#     Compute path-based similarity between two words using ONLY
#     their first noun sense in WordNet.
#     """

#     syns1 = wn.synsets(word1, pos=pos)
#     syns2 = wn.synsets(word2, pos=pos)

#     if not syns1 or not syns2:
#         return None  # one of the words has no noun senses

#     s1 = syns1[0]   # take most frequent noun sense
#     s2 = syns2[0]

#     id1, id2 = s1.name(), s2.name()

#     nodes, rels, dist = shortest_path_with_details(id1, id2)
#     if nodes is None or dist is None:
#         return None

#     sim = 1.0 / (1.0 + dist)

#     return {
#         "score": round(sim, 4),
#         "path_nodes": nodes,
#         "rels": rels,
#         "definitions": get_definitions(nodes),
#         "syn1": id1,
#         "syn2": id2,
#         "dist": dist,
#     }


from neo4j import GraphDatabase
from manual_wordnet_loader import WordNetLoader

WN_PATH = r"C:\Program Files (x86)\WordNet\2.1\dict"
loader = WordNetLoader(WN_PATH)
loader.load()

URI = "neo4j://127.0.0.1:7687"
USER = "neo4j"
PASSWORD = "wordnet-similarity1"

driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))


# -----------------------------------------------------
# AUTOCOMPLETE (word-level)
# -----------------------------------------------------
def autocomplete_words(prefix, limit=10):
    prefix = prefix.lower()
    all_words = set()

    # collect lemmas from all POS
    for pos in loader.index:
        for lemma in loader.index[pos].keys():
            all_words.add(lemma)

    return [w for w in sorted(all_words) if w.startswith(prefix)][:limit]



# -----------------------------------------------------
# SHORTEST PATH FROM NEO4J
# -----------------------------------------------------
def shortest_path_details(id1, id2):
    if id1 == id2:
        return [id1], [], 0

    query = """
    MATCH (a:Synset {id:$id1}), (b:Synset {id:$id2})
    MATCH p = shortestPath((a)-[:HYPERNYM_OF|HYPONYM_OF|SIMILAR_TO|PART_OF*..10]-(b))
    RETURN p
    """

    with driver.session() as session:
        rec = session.run(query, id1=id1, id2=id2).single()
        if not rec:
            return None, None, None

        p = rec["p"]
        nodes = [n["id"] for n in p.nodes]
        rels = [r.type for r in p.relationships]   # correct relation type
        dist = len(nodes) - 1
        return nodes, rels, dist


# -----------------------------------------------------
# PATH SIMILARITY
# -----------------------------------------------------
def path_similarity(word1, word2):
    syn1 = loader.index["n"].get(word1.lower())
    syn2 = loader.index["n"].get(word2.lower())

    if not syn1 or not syn2:
        return None

    best = None

    for id1 in syn1:
        for id2 in syn2:
            nodes, rels, dist = shortest_path_details(id1, id2)
            if dist is None:
                continue

            score = 1 / (1 + dist)

            if not best or score > best["score"]:
                best = {
                    "score": round(score, 4),
                    "dist": dist,

    # BEST SENSES with lemmas
                    "syn1": id1,
                    "syn2": id2,
                    "syn1_lemmas": loader.synsets[id1]["lemmas"],
                    "syn2_lemmas": loader.synsets[id2]["lemmas"],

    # PATH NODES with lemmas  
                    "path_nodes": [
                        {
                            "id": sid,
                            "lemmas": loader.synsets[sid]["lemmas"]
                        }
                        for sid in nodes
                    ],

                    "rels": rels,

                    "definitions": {
                        sid: {
                            "lemmas": loader.synsets[sid]["lemmas"],
                            "gloss": loader.synsets[sid]["gloss"]
                        }
                        for sid in nodes
                    }
                }



    return best
