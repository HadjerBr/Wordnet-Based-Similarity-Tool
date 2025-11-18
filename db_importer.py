from neo4j import GraphDatabase
from nltk.corpus import wordnet as wn
import nltk

nltk.download("wordnet")
URI = "neo4j://127.0.0.1:7687"        
USER = "neo4j"
PASSWORD = "wordnet-similarity1"      

driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))

def clear_db():
    with driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")

def import_synsets(pos="n"):
    """Create Synset nodes ."""
    with driver.session() as session:
        for syn in wn.all_synsets(pos):
            session.run(
                """
                MERGE (s:Synset {id: $id})
                SET s.pos = $pos,
                    s.definition = $definition
                """,
                id=syn.name(),
                pos=syn.pos(),
                definition=syn.definition()
            )


def import_relations(pos="n"):
    """Create HYPERNYM_OF, HYPONYM_OF, SIMILAR_TO relations."""
    with driver.session() as session:
        for syn in wn.all_synsets(pos):
            sid = syn.name()

            # hypernyms / hyponyms
            for h in syn.hypernyms():
                session.run(
                    """
                    MATCH (a:Synset {id: $hid}), (b:Synset {id: $cid})
                    MERGE (a)-[:HYPERNYM_OF]->(b)
                    MERGE (b)-[:HYPONYM_OF]->(a)
                    """,
                    hid=h.name(), cid=sid
                )

            # similar_to
            for s2 in syn.similar_tos():
                session.run(
                    """
                    MATCH (a:Synset {id: $a}), (b:Synset {id: $b})
                    MERGE (a)-[:SIMILAR_TO]->(b)
                    """,
                    a=sid, b=s2.name()
                )


if __name__ == "__main__":
    print("Clearing database…")
    clear_db()
    print("Importing synsets…")
    import_synsets("n")        
    print("Importing relations…")
    import_relations("n")
    print("Done.")
    driver.close()

