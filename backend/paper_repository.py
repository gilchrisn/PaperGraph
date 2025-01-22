from database import init_db_connection


class PaperRepository:
    def get_all_papers(self):
        """
        Fetch all papers from the database.
        """
        with init_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM papers;")
                return cursor.fetchall()

    def get_paper_by_id(self, paper_id: str):
        """
        Fetch a paper by its ID.
        """
        with init_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM papers WHERE id = %s;", (paper_id,))
                return cursor.fetchone()

    def get_papers_by_title(self, title: str):
        """
        Search for papers by title using ILIKE for case-insensitive matching.
        """
        with init_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM papers WHERE title ILIKE %s;", (f"%{title}%",))
                return cursor.fetchall()

    def get_pdf_path_by_id(self, paper_id: str):
        """
        Fetch the file path for a paper's PDF by its ID.
        """
        with init_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT filepath FROM papers WHERE id = %s;", (paper_id,))
                result = cursor.fetchone()
                return result["filepath"] if result else None

    def get_reference_by_paper_ids(self, source_paper_id: str, cited_paper_id: str):
        """
        Fetch all references for a given paper by its ID.
        """
        with init_db_connection() as conn:
            with conn.cursor() as cursor:
                # Fetch references where the source paper ID matches the given ID and the cited_paper_id
                cursor.execute(
                    "SELECT * FROM reference WHERE source_paper_id = %s AND cited_paper_id = %s;",
                    (source_paper_id, cited_paper_id)
                )
                return cursor.fetchone()

    def insert_reference(self, source_paper_id: str, cited_paper_id: str, relationship_type: str, remarks: str, similarity_score: float):
        """
        Insert a reference relationship into the database or update if it already exists.
        """
        with init_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO reference (source_paper_id, cited_paper_id, relationship_type, remarks, similarity_score)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (source_paper_id, cited_paper_id) DO UPDATE
                    SET relationship_type = EXCLUDED.relationship_type,
                        remarks = EXCLUDED.remarks,
                        similarity_score = EXCLUDED.similarity_score;
                    """,
                    (source_paper_id, cited_paper_id, relationship_type, remarks, similarity_score)
                )
                conn.commit()

    def find_similar_papers_by_title(self, reference_title: str, title_similarity_threshold: float = 0.8):
        """
        Find papers similar to a given title using PostgreSQL similarity.
        """
        with init_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT *, similarity(title, %s) AS similarity
                    FROM papers
                    WHERE similarity(title, %s) > %s
                    ORDER BY similarity DESC
                    LIMIT 1;
                    """,
                    (reference_title, reference_title, title_similarity_threshold)
                )
                return cursor.fetchone()
            
    def get_referencing_papers(self, cited_paper_id: str):
        """
        Fetch all papers that reference a given paper by its ID.
        """
        with init_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM reference WHERE cited_paper_id = %s;", (cited_paper_id,))
                referencing_papers =  cursor.fetchall()

                return [paper["source_paper_id"] for paper in referencing_papers]
