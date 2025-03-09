import os
import asyncio
import logging
from supabase import create_client, Client
from discord.ext import commands
import discord
from dotenv import load_dotenv
import io

# Configure logging
logger = logging.getLogger('modubot.db_admin')

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

class DatabaseAdminUtil:
    def __init__(self, bot):
        self.bot = bot
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
    async def execute_sql(self, query, params=None):
        """Execute a raw SQL query with optional parameters"""
        try:
            # For Supabase, we need to use the REST endpoint for raw SQL
            # Since supabase-py doesn't directly expose this, we'll use the wrapped httpx client
            payload = {"query": query}
            if params:
                payload["params"] = params
                
            response = await asyncio.to_thread(
                lambda: self.supabase.table("_rpc").select("*").execute(
                    {"method": "POST", "body": {"command": "sql", "sql": query, "params": params or []}}
                )
            )
            
            return response
        except Exception as e:
            logger.error(f"SQL execution error: {str(e)}")
            raise

    async def get_tables(self):
        """Get list of all tables in the database"""
        query = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        """
        result = await self.execute_sql(query)
        if result and "data" in result:
            return [table["table_name"] for table in result["data"]]
        return []
    
    async def get_table_structure(self, table_name):
        """Get the structure of a table"""
        query = """
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = $1
        ORDER BY ordinal_position
        """
        result = await self.execute_sql(query, [table_name])
        if result and "data" in result:
            return result["data"]
        return []
    
    async def get_table_data(self, table_name, limit=50, offset=0):
        """Get data from a table with pagination"""
        try:
            response = await asyncio.to_thread(
                lambda: self.supabase.table(table_name).select("*").range(offset, offset + limit - 1).execute()
            )
            return response.data
        except Exception as e:
            logger.error(f"Failed to get table data: {str(e)}")
            return []
    
    async def create_table(self, table_name, columns):
        """Create a new table with specified columns"""
        columns_str = ", ".join(columns)
        query = f"CREATE TABLE {table_name} ({columns_str})"
        return await self.execute_sql(query)
    
    async def insert_data(self, table_name, data):
        """Insert data into a table"""
        try:
            response = await asyncio.to_thread(
                lambda: self.supabase.table(table_name).insert(data).execute()
            )
            return response.data
        except Exception as e:
            logger.error(f"Failed to insert data: {str(e)}")
            raise
    
    async def update_data(self, table_name, data, match_column, match_value):
        """Update data in a table"""
        try:
            response = await asyncio.to_thread(
                lambda: self.supabase.table(table_name).update(data).eq(match_column, match_value).execute()
            )
            return response.data
        except Exception as e:
            logger.error(f"Failed to update data: {str(e)}")
            raise
    
    async def delete_data(self, table_name, match_column, match_value):
        """Delete data from a table"""
        try:
            response = await asyncio.to_thread(
                lambda: self.supabase.table(table_name).delete().eq(match_column, match_value).execute()
            )
            return response.data
        except Exception as e:
            logger.error(f"Failed to delete data: {str(e)}")
            raise

class DatabaseAdmin(commands.Cog):
    """Database administration commands"""
    
    def __init__(self, bot):
        self.bot = bot
        self.db_util = DatabaseAdminUtil(bot)
    
    @commands.command()
    @commands.is_owner()
    async def sql(self, ctx, *, query):
        """Execute a SQL query (Owner only)"""
        try:
            result = await self.db_util.execute_sql(query)
            
            # Format the result for display
            if result and "data" in result:
                data = result["data"]
                if not data:
                    await ctx.send("Query executed successfully. No data returned.")
                    return
                
                # Convert to string representation with proper formatting
                if len(str(data)) > 1900:  # Discord message limit
                    # For large results, send as a file
                    import json
                    file_content = json.dumps(data, indent=2)
                    file = discord.File(
                        filename="query_result.json",
                        fp=io.BytesIO(file_content.encode())
                    )
                    await ctx.send("Query result:", file=file)
                else:
                    # For smaller results, send as code block
                    import json
                    formatted = json.dumps(data, indent=2)
                    await ctx.send(f"```json\n{formatted}\n```")
            else:
                await ctx.send("Query executed but returned no data or an error occurred.")
        except Exception as e:
            await ctx.send(f"Error executing query: {str(e)}")
    
    @commands.command()
    @commands.is_owner()
    async def tables(self, ctx):
        """List all tables in the database (Owner only)"""
        try:
            tables = await self.db_util.get_tables()
            if tables:
                await ctx.send("**Database Tables:**\n" + "\n".join(tables))
            else:
                await ctx.send("No tables found in the database.")
        except Exception as e:
            await ctx.send(f"Error retrieving tables: {str(e)}")
    
    @commands.command()
    @commands.is_owner()
    async def describe(self, ctx, table_name):
        """Show the structure of a table (Owner only)"""
        try:
            structure = await self.db_util.get_table_structure(table_name)
            if structure:
                # Format the structure into a readable message
                lines = ["**Table Structure:**"]
                for column in structure:
                    nullable = "NULL" if column["is_nullable"] == "YES" else "NOT NULL"
                    default = f"DEFAULT {column['column_default']}" if column["column_default"] else ""
                    lines.append(f"`{column['column_name']}` {column['data_type']} {nullable} {default}")
                
                await ctx.send("\n".join(lines))
            else:
                await ctx.send(f"Table '{table_name}' not found or has no columns.")
        except Exception as e:
            await ctx.send(f"Error describing table: {str(e)}")
    
    @commands.command()
    @commands.is_owner()
    async def tabledata(self, ctx, table_name, limit: int = 10):
        """Show data from a table with limit (Owner only)"""
        try:
            data = await self.db_util.get_table_data(table_name, limit)
            if data:
                import json
                formatted = json.dumps(data, indent=2)
                
                if len(formatted) > 1900:
                    # Send as file for large results
                    file = discord.File(
                        filename=f"{table_name}_data.json",
                        fp=io.BytesIO(formatted.encode())
                    )
                    await ctx.send(f"Data from '{table_name}':", file=file)
                else:
                    # Send as code block for smaller results
                    await ctx.send(f"**Data from '{table_name}':**\n```json\n{formatted}\n```")
            else:
                await ctx.send(f"No data found in table '{table_name}' or table doesn't exist.")
        except Exception as e:
            await ctx.send(f"Error retrieving table data: {str(e)}")

async def setup(bot):
    await bot.add_cog(DatabaseAdmin(bot)) 