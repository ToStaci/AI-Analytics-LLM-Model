import sqlite3
import os
from dotenv import load_dotenv
import pandas as pd
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

class TelemetrySQLAgent:
    def __init__(self, db_path: str = "data/telemetry.db"):
        self.db_path = db_path
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError(
                "Connection Error: GROQ_API_KEY not found! "
            )
        self.llm = ChatGroq(model="qwen/qwen3.8-27b", temperature=0.0, api_key=api_key)

    def _get_schema(self) -> str:
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            schema_text = ""
            for table_tuple in tables:
                table_name = table_tuple[0]
                schema_text += f"\nTable: {table_name}\nColumns: "
                cursor.execute(f"PRAGMA table_info({table_name});")
                columns = cursor.fetchall()
                col_descriptions = [f"{col[1]} ({col[2]})" for col in columns]
                schema_text += ", ".join(col_descriptions) + "\n"
                
            conn.close()
            return schema_text
        except Exception as e:
            return "Unable to inspect schema automatically."

    def text_to_sql(self, user_query: str) -> dict:
        schema = self._get_schema()
        system_prompt = (
            "You are a Senior Game Data Analyst.\n"
            "Given the SQLite database schema below, write ONLY a valid SQL query to"
            " answer the user question.\n\n"
            "STRICT RULES:\n"
            "1. Return RAW SQL ONLY. Do not use markdown backticks (no ```sql or"
            " ```).\n"
            "2. Aggregations: Use standard SQL functions (AVG, SUM, COUNT, MAX,"
            " MIN) whenever the user asks for averages, totals, or counts.\n"
            "3. Typos & Partial Names: Use LIKE with wildcards (e.g., LIKE"
            " '%Chern%') for map/weapon filters to handle minor spelling"
            " errors.\n"
            "4. Alias clear column names for calculated metrics (e.g. AS"
            " avg_kills).\n\n"
            "EXAMPLES:\n"
            "User: What is the average kills on Chernarus?\n"
            "SQL: SELECT AVG(kills) AS avg_kills FROM player_matches WHERE map_name"
            " LIKE '%Chern%'\n\n"
            "User: How many total shots were fired from M4A1?\n"
            "SQL: SELECT SUM(shots_fired) AS total_shots FROM weapon_stats WHERE"
            " weapon_name = 'M4A1'\n\n"
            f"Schema:\n{schema}"
        )

        prompt = ChatPromptTemplate.from_messages(
            [("system", system_prompt), ("human", "{query}")]
        )
        try:
            chain = prompt | self.llm
            sql_response = chain.invoke({"query": user_query}).content.strip()
            sql_query = (
            sql_response.replace("```sql", "").replace("```", "").strip()
            )

        except Exception as e:
            return {
                "sql": "",
                "data": pd.DataFrame(),
                "error": (
                    "Unable to process query with AI model. "
                    f"Rephrase the question or check the connection. Details: {e}"
                ),
            }
        try:
            conn = sqlite3.connect(self.db_path)
            df_result = pd.read_sql_query(sql_query, conn)
            conn.close()

            if df_result.empty:
                return {
                    "sql": sql_query,
                    "data": df_result,
                     "error": "Unable to find data matching your criteria.",
                 }

            return {"sql": sql_query, "data": df_result, "error": None}
        except Exception as e:
            return {
                "sql": sql_query,
                "data": pd.DataFrame(),
                "error": f"Error executing SQL query ({sql_query}): {e}",
            }