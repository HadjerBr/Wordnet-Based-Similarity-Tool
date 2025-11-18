from neo4j import GraphDatabase

URI = "neo4j://127.0.0.1:7687"
USER = "neo4j"
PASSWORD = "wordnet-similarity1"

driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))


def get_synset_ids(word):
    with driver.session() as session:
        q = """
        MATCH (s:Synset)
        WHERE s.id STARTS WITH $word AND s.id CONTAINS ".n."
        RETURN s.id LIMIT 5
        """
        res = session.run(q, word=word.lower())
        return [r["s.id"] for r in res]


def shortest_path_with_details(id1, id2):
    with driver.session() as session:
        q = """
        MATCH (a:Synset {id:$id1}), (b:Synset {id:$id2})
        MATCH p = shortestPath((a)-[:HYPERNYM_OF|HYPONYM_OF|SIMILAR_TO*]-(b))
        RETURN p
        """
        result = session.run(q, id1=id1, id2=id2).single()
        if not result:
            return None, None, None

        path = result["p"]
        nodes = [n["id"] for n in path.nodes]
        rels = [type(r).__name__ for r in path.relationships]

        return nodes, rels, len(nodes) - 1


def get_definitions(ids):
    with driver.session() as session:
        q = """
        MATCH (s:Synset)
        WHERE s.id IN $ids
        RETURN s.id AS id, s.definition AS def
        """
        return {r["id"]: r["def"] for r in session.run(q, ids=ids)}


def path_similarity(word1, word2):
    s1 = get_synset_ids(word1)
    s2 = get_synset_ids(word2)
    if not s1 or not s2:
        return None

    s1 = s1[0]
    s2 = s2[0]

    nodes, rels, dist = shortest_path_with_details(s1, s2)
    if not nodes:
        return None

    sim = 1 / dist if dist > 0 else 1.0
    defs = get_definitions(nodes)

    return {
        "score": round(sim, 4),
        "path_nodes": nodes,
        "rels": rels,
        "definitions": defs,
        "syn1": s1,
        "syn2": s2,
        "dist": dist
    }
