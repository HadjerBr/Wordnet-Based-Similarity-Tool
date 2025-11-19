from neo4j import GraphDatabase
from manual_wordnet_loader import WordNetLoader

URI = "neo4j://127.0.0.1:7687"
USER = "neo4j"
PASSWORD = "wordnet-similarity1"

driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))

# ---------------------------------------------------------
def clear_db():
    with driver.session() as s:
        s.run("MATCH (n) DETACH DELETE n")
    print("Database cleared.")
# ---------------------------------------------------------

def import_synsets(loader):
    print("Importing synset nodes...")

    with driver.session() as s:
        for sid, info in loader.synsets.items():

            s.run("""
                MERGE (n:Synset {id:$id})
                SET n.pos   = $pos,
                    n.gloss = $gloss,
                    n.lemmas = $lemmas
            """,
            id=sid,
            pos=info["pos"],
            gloss=info["gloss"],
            lemmas=info["lemmas"]
            )

    print("Synsets imported.")
# ---------------------------------------------------------

def import_relations(loader):
    print("Importing relations...")

    with driver.session() as s:
        for sid, info in loader.synsets.items():

            # ---------- Hypernym ----------
            for h in info["relations"]["hypernym"]:
                s.run("""
                    MATCH (a:Synset {id:$a}), (b:Synset {id:$b})
                    MERGE (a)-[:HYPERNYM_OF]->(b)
                    MERGE (b)-[:HYPONYM_OF]->(a)
                """, a=h, b=sid)

            # ---------- Hyponym ----------
            for hypo in info["relations"]["hyponym"]:
                s.run("""
                    MATCH (a:Synset {id:$a}), (b:Synset {id:$b})
                    MERGE (a)-[:HYPONYM_OF]->(b)
                    MERGE (b)-[:HYPERNYM_OF]->(a)
                """, a=hypo, b=sid)

            # ---------- Similar-to ----------
            for sim in info["relations"]["similar"]:
                s.run("""
                    MATCH (a:Synset {id:$a}), (b:Synset {id:$b})
                    MERGE (a)-[:SIMILAR_TO]->(b)
                """, a=sid, b=sim)

            # ---------- Part-of / Meronym ----------
            for part in info["relations"]["meronym"]:
                s.run("""
                    MATCH (p:Synset {id:$p}), (w:Synset {id:$w})
                    MERGE (p)-[:PART_OF]->(w)
                """, p=part, w=sid)

    print("Relations imported.")
# ---------------------------------------------------------

if __name__ == "__main__":
    loader = WordNetLoader(r"C:\Program Files (x86)\WordNet\2.1\dict")
    loader.load()

    print("Total synsets loaded from WN:", len(loader.synsets))
    print("Importing into Neo4j...")

    clear_db()
    import_synsets(loader)
    import_relations(loader)

    print("DONE.")
