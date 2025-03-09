import os
from supabase import create_client, Client
from dotenv import load_dotenv
import traceback
import logging
import asyncio
import json
import httpx

load_dotenv()

logger = logging.getLogger("modubot")

class Database:
    def __init__(self):
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_KEY")
        self.is_connected = False
        self.tables_exist = False
        
        # Check if credentials are provided
        if not self.url or not self.key or self.url == "https://fmwxyhrizbkzikxexlxe.supabase.co" or self.key == "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZtd3h5aHJpemJremlreGV4bHhlIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDE0ODQ2NDcsImV4cCI6MjA1NzA2MDY0N30.Y744ofmIcJYbNyslTeZmPfaoc4k3xqXmoESDwhZvT-Q":
            logger.warning("Supabase credentials not properly configured. Database functionality will be limited.")
            self.supabase = None
        else:
            try:
                self.supabase = create_client(self.url, self.key)
                self.is_connected = True
                logger.info("Successfully connected to Supabase")
            except Exception as e:
                logger.error(f"Failed to connect to Supabase: {str(e)}")
                self.supabase = None
    
    async def execute_raw_sql(self, query, params=None):
        """Execute a raw SQL query using the Supabase REST API"""
        if not self.is_connected or not self.supabase:
            logger.error("Cannot execute SQL: Not connected to Supabase")
            return False
            
        try:
            # The supabase-py client doesn't expose direct SQL execution
            # So we'll use httpx to make a direct API call to the PostgreSQL REST endpoint
            headers = {
                "apikey": self.key,
                "Authorization": f"Bearer {self.key}",
                "Content-Type": "application/json",
                "Prefer": "return=representation"
            }
            
            payload = {
                "query": query
            }
            
            if params:
                payload["params"] = params
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.url}/rest/v1/rpc/execute_sql",
                    headers=headers,
                    json=payload
                )
                
                if response.status_code >= 400:
                    logger.error(f"SQL error: {response.text}")
                    return False
                    
                return response.json()
                
        except Exception as e:
            logger.error(f"Error executing SQL: {str(e)}")
            return False
    
    async def setup_database(self):
        """Set up the database tables if they don't exist."""
        if not self.is_connected:
            logger.warning("Cannot set up database: Not connected to Supabase")
            return False
            
        try:
            # First, create the necessary RPC function to execute raw SQL if it doesn't exist
            await self.create_execute_sql_function()
            
            # Create guild_settings table
            try:
                # First check if table exists
                result = await self.execute_raw_sql(
                    "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'guild_settings')"
                )
                
                table_exists = False
                if result and isinstance(result, list) and len(result) > 0:
                    table_exists = result[0].get('exists', False)
                
                if not table_exists:
                    logger.info("Creating guild_settings table...")
                    # SQL to create the guild_settings table
                    sql = """
                    CREATE TABLE guild_settings (
                      id SERIAL PRIMARY KEY,
                      guild_id TEXT UNIQUE NOT NULL,
                      prefix TEXT DEFAULT '!',
                      moderation_enabled BOOLEAN DEFAULT TRUE,
                      entertainment_enabled BOOLEAN DEFAULT TRUE,
                      utility_enabled BOOLEAN DEFAULT TRUE,
                      economy_enabled BOOLEAN DEFAULT TRUE,
                      welcome_channel_id TEXT,
                      welcome_message TEXT,
                      goodbye_channel_id TEXT,
                      goodbye_message TEXT,
                      log_channel_id TEXT,
                      mute_role_id TEXT,
                      auto_role_id TEXT,
                      created_at TIMESTAMPTZ DEFAULT NOW(),
                      updated_at TIMESTAMPTZ DEFAULT NOW()
                    )
                    """
                    await self.execute_raw_sql(sql)
                    logger.info("Successfully created guild_settings table")
                else:
                    logger.info("guild_settings table already exists")
            except Exception as e:
                logger.error(f"Error creating guild_settings table: {str(e)}")
                traceback.print_exc()
                
            # Implement similar checks and creation for other tables
            # ...
            
            self.tables_exist = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to set up database: {str(e)}")
            traceback.print_exc()
            return False
            
    async def create_execute_sql_function(self):
        """Create a Postgres function to execute raw SQL queries"""
        try:
            headers = {
                "apikey": self.key,
                "Authorization": f"Bearer {self.key}",
                "Content-Type": "application/json",
                "Prefer": "return=representation"
            }
            
            # Define the SQL function
            sql_function = """
            CREATE OR REPLACE FUNCTION execute_sql(query text, params jsonb DEFAULT '[]'::jsonb)
            RETURNS JSONB
            LANGUAGE plpgsql
            SECURITY DEFINER
            AS $$
            DECLARE
                result JSONB;
            BEGIN
                EXECUTE query INTO result;
                RETURN result;
            EXCEPTION WHEN OTHERS THEN
                RETURN jsonb_build_object('error', SQLERRM, 'detail', SQLSTATE);
            END;
            $$;
            """
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.url}/rest/v1/rpc/execute",
                    headers=headers,
                    json={"sql": sql_function}
                )
                
                if response.status_code >= 400:
                    # If the function already exists, this is fine
                    if "already exists" not in response.text:
                        logger.error(f"Error creating SQL function: {response.text}")
                        return False
                
                logger.info("SQL execution function is ready")
                return True
                
        except Exception as e:
            logger.error(f"Error creating SQL function: {str(e)}")
            return False
    
    async def get_guild_settings(self, guild_id):
        """Get settings for a specific guild."""
        if not self.is_connected:
            return self._get_default_settings(guild_id)
        
        # Ensure tables exist
        if not self.tables_exist:
            try:
                await self.setup_database()
            except Exception as e:
                logger.error(f"Failed to set up database: {str(e)}")
                return self._get_default_settings(guild_id)
        
        try:
            response = self.supabase.table('guild_settings').select('*').eq('guild_id', str(guild_id)).execute()
            
            if response.data:
                return response.data[0]
            else:
                # Create default settings if none exist
                default_settings = self._get_default_settings(guild_id)
                
                try:
                    self.supabase.table('guild_settings').insert(default_settings).execute()
                except Exception as e:
                    logger.error(f"Failed to insert default settings: {str(e)}")
                
                return default_settings
        except Exception as e:
            logger.error(f"Error getting guild settings: {str(e)}")
            return self._get_default_settings(guild_id)
    
    def _get_default_settings(self, guild_id):
        """Get default settings for a guild when database is unavailable."""
        return {
            'guild_id': str(guild_id),
            'prefix': '!',
            'moderation_enabled': True,
            'entertainment_enabled': True,
            'utility_enabled': True,
            'welcome_message': 'Welcome to the server, {user}!',
            'log_channel_id': None,
            'auto_role_id': None,
            'mute_role_id': None,
            'banned_links': [],
            'banned_links_enabled': False,
            'spam_mute_enabled': False,
            'spam_mute_duration': 5,
            'strike_actions': {},
            'strike_mute_duration': 10
        }
    
    async def update_guild_settings(self, guild_id, settings):
        """Update settings for a specific guild."""
        if not self.is_connected:
            logger.warning("Cannot update guild settings: Not connected to Supabase")
            return None
            
        try:
            return self.supabase.table('guild_settings').update(settings).eq('guild_id', str(guild_id)).execute()
        except Exception as e:
            logger.error(f"Error updating guild settings: {str(e)}")
            return None
    
    async def add_moderation_log(self, guild_id, action, target_id, moderator_id, reason=None, duration=None):
        """Add a moderation log entry."""
        if not self.is_connected:
            logger.warning("Cannot add moderation log: Not connected to Supabase")
            return None
            
        log_entry = {
            'guild_id': str(guild_id),
            'action': action,
            'target_id': str(target_id),
            'moderator_id': str(moderator_id),
            'reason': reason,
            'duration': duration,
            'timestamp': 'now()'  # Supabase SQL function for current timestamp
        }
        
        try:
            return self.supabase.table('moderation_logs').insert(log_entry).execute()
        except Exception as e:
            logger.error(f"Error adding moderation log: {str(e)}")
            return None
    
    async def get_moderation_logs(self, guild_id, limit=100):
        """Get moderation logs for a specific guild."""
        if not self.is_connected:
            logger.warning("Cannot get moderation logs: Not connected to Supabase")
            return {"data": []}
            
        try:
            return self.supabase.table('moderation_logs').select('*').eq('guild_id', str(guild_id)).order('timestamp', desc=True).limit(limit).execute()
        except Exception as e:
            logger.error(f"Error getting moderation logs: {str(e)}")
            return {"data": []}
    
    async def get_user_strikes(self, guild_id, user_id):
        """Get strikes for a specific user in a guild."""
        if not self.is_connected:
            logger.warning("Cannot get user strikes: Not connected to Supabase")
            return {"data": []}
            
        try:
            return self.supabase.table('moderation_logs').select('*').eq('guild_id', str(guild_id)).eq('target_id', str(user_id)).eq('action', 'strike').execute()
        except Exception as e:
            logger.error(f"Error getting user strikes: {str(e)}")
            return {"data": []}
    
    async def add_custom_command(self, guild_id, command_name, response, created_by):
        """Add a custom command to a guild."""
        if not self.is_connected:
            logger.warning("Cannot add custom command: Not connected to Supabase")
            return None
            
        command = {
            'guild_id': str(guild_id),
            'command_name': command_name.lower(),
            'response': response,
            'created_by': str(created_by),
            'uses': 0
        }
        
        try:
            return self.supabase.table('custom_commands').insert(command).execute()
        except Exception as e:
            logger.error(f"Error adding custom command: {str(e)}")
            return None
    
    async def get_custom_commands(self, guild_id):
        """Get all custom commands for a guild."""
        if not self.is_connected:
            logger.warning("Cannot get custom commands: Not connected to Supabase")
            return {"data": []}
            
        try:
            return self.supabase.table('custom_commands').select('*').eq('guild_id', str(guild_id)).execute()
        except Exception as e:
            logger.error(f"Error getting custom commands: {str(e)}")
            return {"data": []}
    
    async def get_custom_command(self, guild_id, command_name):
        """Get a specific custom command for a guild."""
        if not self.is_connected:
            logger.warning("Cannot get custom command: Not connected to Supabase")
            return {"data": []}
            
        try:
            return self.supabase.table('custom_commands').select('*').eq('guild_id', str(guild_id)).eq('command_name', command_name.lower()).execute()
        except Exception as e:
            logger.error(f"Error getting custom command: {str(e)}")
            return {"data": []}
    
    async def increment_command_uses(self, command_id):
        """Increment the use counter for a custom command."""
        if not self.is_connected:
            logger.warning("Cannot increment command uses: Not connected to Supabase")
            return None
            
        try:
            response = self.supabase.table('custom_commands').select('uses').eq('id', command_id).execute()
            if response.data:
                current_uses = response.data[0]['uses']
                return self.supabase.table('custom_commands').update({'uses': current_uses + 1}).eq('id', command_id).execute()
        except Exception as e:
            logger.error(f"Error incrementing command uses: {str(e)}")
        return None 