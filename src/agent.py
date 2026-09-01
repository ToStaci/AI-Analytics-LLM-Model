import sqlite3
import pandas as pd
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

class TelemetrySQLAgent:
    def __init__(self, db_path: str = "data/telemetry.db"):
        self.db_path = db_path
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.0)

    def _get_schema(self) -> str:
        return """
        Table: player_matches
        Columns: match_id (TEXT), player_id (TEXT), map_name (TEXT), duration_seconds (INTEGER), kills (INTEGER), deaths (INTEGER), win (BOOLEAN)

        Table: weapon_stats
        Columns: match_id (TEXT), weapon_name (TEXT), damage_dealt (FLOAT), shots_fired (INTEGER), shots_hit (INTEGER)
        """

    def text_to_sql(self, user_query: str) -> dict:
        sql_query = ""

        try:
            schema = self._get_schema()
            system_prompt = (
                "You are a Senior Game Data Analyst.\n"
                "Given the SQLite database schema below, write ONLY a valid SQL query to answer the user question.\n"
                "Do not include markdown code blocks (like ```sql), return raw SQL only.\n\n"
                f"Schema:\n{schema}"
            )

            prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                ("human", "{query}")
            ])

            chain = prompt | self.llm
            sql_response = chain.invoke({"query": user_query}).content.strip()
            sql_query = sql_response.replace("```sql", "").replace("```", "").strip()

        except Exception:
            q = user_query.lower()
            if "weapon" in q or "damage" in q or "m4a1" in q:
                sql_query = "SELECT weapon_name, SUM(damage_dealt) AS total_damage, SUM(shots_hit) AS total_hits FROM weapon_stats GROUP BY weapon_name ORDER BY total_damage DESC;"
            elif "map" in q or "duration" in q or "time" in q:
                sql_query = "SELECT map_name, AVG(duration_seconds) AS avg_duration_sec, COUNT(match_id) as total_matches FROM player_matches GROUP BY map_name;"
            elif "kill" in q or "player" in q or "death" in q:
                sql_query = "SELECT player_id, SUM(kills) AS total_kills, SUM(deaths) AS total_deaths FROM player_matches GROUP BY player_id ORDER BY total_kills DESC;"
            else:
                sql_query = "SELECT * FROM player_matches LIMIT 5;"

        try:
            conn = sqlite3.connect(self.db_path)
            df_result = pd.read_sql_query(sql_query, conn)
            conn.close()
            return {
                "sql": sql_query,
                "data": df_result,
                "error": None
            }
        except Exception as e:
            if 'conn' in locals():
                conn.close()
            return {"sql": sql_query, "data": pd.DataFrame(), "error": str(e)}