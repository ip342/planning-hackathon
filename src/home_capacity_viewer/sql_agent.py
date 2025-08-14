from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.tools import tool
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from pydantic import BaseModel, field_validator, Field
import sqlparse
import json
from sqlalchemy import text
from home_capacity_viewer.settings import CLIENT, MODEL, MODEL_PROVIDER
from home_capacity_viewer.database import DatabaseManager
import pandas as pd
from langchain.agents import create_openai_functions_agent


class QueryOutput(BaseModel):
    query: str = Field(description="A syntactically correct SQL query.")
    
    @field_validator('query')
    def validate_sql(cls, v):
        try:
            sqlparse.parse(v)
            return v
        except:
            raise ValueError('Invalid SQL syntax')


def create_tools(db_manager: DatabaseManager):
    """Create tools bound to the specific db_manager instance"""

    def query_database(query: str, db_manager: DatabaseManager) -> str:
        try:
            with db_manager.engine.connect() as conn:
                result = conn.execute(text(query))
                rows = result.fetchall()
                df = pd.DataFrame(rows, columns=result.keys())

                return df.to_json(orient='records')
                
        except Exception as e:
            return json.dumps({"error": str(e)})

    def get_table_schemas(db_manager: DatabaseManager) -> str:
        """Get the table schemas from the database"""
        return db_manager.get_table_schemas()
    
    @tool
    def query_db(query: str) -> str:
        """Execute a SQL query on the database. Use this tool to run SELECT statements. 
        The query should be valid SQL syntax. Returns results as JSON format."""
        # Validate the SQL query using QueryOutput
        try:
            validated_query = QueryOutput(query=query).query
        except ValueError as e:
            return json.dumps({"error": f"Invalid SQL syntax: {str(e)}"})
        
        # Execute the validated query
        return query_database(validated_query, db_manager)
    
    @tool
    def get_schemas() -> str:
        """Retrieve database schema information including tables, columns, and data types. Use this first to understand the database structure."""
        return get_table_schemas(db_manager)
    
    return [get_schemas, query_db]


SYSTEM_PROMPT = """
You are a SQL analyst that can answer questions about the data in the database.
You are given a question which requires you to query the database.

Available tools:
1. get_schemas: Use this tool first to understand the database structure. It returns information about tables, columns, and data types.
2. query_db: Use this tool to execute SQL queries. Always use valid SQL syntax. Returns results in JSON format.

Workflow:
1. First, use get_schemas to understand what tables and columns are available
2. Then, construct appropriate SQL queries using query_db to answer the user's question
3. Provide clear, human-readable answers based on the query results

IMPORTANT: When using the query_db tool, ensure your SQL query is syntactically valid. 
"""

def get_sql_agent(db_manager: DatabaseManager, question: str):
    """Create a SQL agent that can query the database and return text results"""

    # Create LLM based on the client type
    if MODEL_PROVIDER == 'azure':
        llm = ChatOpenAI(
            model=MODEL,
            azure_endpoint=CLIENT.azure_endpoint,
            azure_deployment=MODEL,
            openai_api_key=CLIENT.api_key,
            openai_api_version=CLIENT.api_version
        )
    else:
        llm = ChatOpenAI(
            model=MODEL,
            openai_api_key=CLIENT.api_key
        )

    # Create tools bound to this db_manager instance
    tools = create_tools(db_manager)

    # Create a simple prompt template
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    agent = create_openai_functions_agent(
        llm=llm,
        tools=tools,
        prompt=prompt,
    )

    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True
    )

    response = agent_executor.invoke({"input": question})["output"]

    return response

# Example usage
if __name__ == "__main__":
    # Initialize database manager
    db_manager = DatabaseManager("sqlite:///home_capacity_data.db")
    
    # Test queries
    questions = [
        "What are the top 5 local authorities with the highest water risk in 2030?",
        "How many local authorities have energy data for 2025?",
        "Show me the home capacity data for London boroughs in 2040"
    ]
    
    for question in questions:
        print(f"\nQuestion: {question}")
        response = get_sql_agent(db_manager, question)
        print(f"Answer: {response}")
        print("-" * 50)