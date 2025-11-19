from neo4j import GraphDatabase
import nltk
from nltk.corpus import wordnet as wn

nltk.download("wordnet")

URI = "neo4j://127.0.0.1:7687"
USER = "neo4j"
PASSWORD = "wordnet-similarity1"

driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))

# ---------- AUTOCOMPLETE (word-level, not synset IDs) ----------

WORDLIST = sorted({
    lemma.replace("_", " ").lower()
    for syn in wn.all_synsets("n")
    for lemma in syn.lemma_names()
})

def autocomplete_words(prefix: str, limit: int = 8):
    prefix = prefix.lower()
    return [w for w in WORDLIST if w.startswith(prefix)][:limit]


# ---------- CORE GRAPH HELPERS ----------

def shortest_path_with_details(id1: str, id2: str):
    """Return (nodes, relations, distance) for shortest path between two synset IDs."""
    # If it’s exactly the same synset, no need to query Neo4j.
    if id1 == id2:
        return [id1], [], 0

    query = """
    MATCH (a:Synset {id:$id1}), (b:Synset {id:$id2})
    MATCH p = shortestPath((a)-[:HYPERNYM_OF|HYPONYM_OF|SIMILAR_TO*..10]-(b))
    RETURN p
    """
    with driver.session() as session:
        record = session.run(query, id1=id1, id2=id2).single()
        if not record:
            return None, None, None

        path = record["p"]
        nodes = [n["id"] for n in path.nodes]
        rels = [type(r).__name__ for r in path.relationships]
        dist = len(nodes) - 1
        return nodes, rels, dist


def get_definitions(ids):
    """Return dict {synset_id: definition} for given synset ids."""
    if not ids:
        return {}
    query = """
    MATCH (s:Synset)
    WHERE s.id IN $ids
    RETURN s.id AS id, s.definition AS def
    """
    with driver.session() as session:
        return {r["id"]: r["def"] for r in session.run(query, ids=ids)}


# ---------- PATH SIMILARITY ----------

def path_similarity(word1: str, word2: str, pos: str = "n"):
    """
    Compute path-based similarity between two words using ONLY
    their first noun sense in WordNet.
    """

    syns1 = wn.synsets(word1, pos=pos)
    syns2 = wn.synsets(word2, pos=pos)

    if not syns1 or not syns2:
        return None  # one of the words has no noun senses

    s1 = syns1[0]   # take most frequent noun sense
    s2 = syns2[0]

    id1, id2 = s1.name(), s2.name()

    nodes, rels, dist = shortest_path_with_details(id1, id2)
    if nodes is None or dist is None:
        return None

    sim = 1.0 / (1.0 + dist)

    return {
        "score": round(sim, 4),
        "path_nodes": nodes,
        "rels": rels,
        "definitions": get_definitions(nodes),
        "syn1": id1,
        "syn2": id2,
        "dist": dist,
    }

