import os
from naptha_sdk.utils import add_credentials_to_env, get_logger, write_private_key_to_file
from naptha_sdk.user import generate_keypair
from naptha_sdk.user import get_public_key, is_hex
from surrealdb import Surreal
import traceback
from typing import Dict, List, Optional, Tuple

import jwt
from surrealdb import Surreal

from naptha_sdk.user import generate_keypair
from naptha_sdk.user import get_public_key
from naptha_sdk.utils import add_credentials_to_env, get_logger

logger = get_logger(__name__)


class Hub:
    """The Hub class is the entry point into Naptha AI Hub."""

    def __init__(self, hub_url, public_key=None, *args, **kwargs):
        self.hub_url = hub_url
        self.public_key = public_key
        self.ns = "naptha"
        self.db = "naptha"
        self.surrealdb = Surreal(hub_url)
        self.is_authenticated = False
        self.user_id = None
        self.token = None
        
        logger.info(f"Hub URL: {hub_url}")

    async def connect(self):
        """Connect to the database and authenticate"""
        if not self.is_authenticated:
            try:
                await self.surrealdb.connect()
                await self.surrealdb.use(namespace=self.ns, database=self.db)
            except Exception as e:
                logger.error(f"Connection failed: {e}")
                raise

    def _decode_token(self, token: str) -> str:
        return jwt.decode(token, options={"verify_signature": False})["ID"]

    async def signin(self, username: str, password: str) -> Tuple[bool, Optional[str], Optional[str]]:
        try:
            print("Signing in to hub with username: ", username)
            user = await self.surrealdb.signin(
                {
                    "NS": self.ns,
                    "DB": self.db,
                    "AC": "user",
                    "username": username,
                    "password": password,
                },
            )
            self.user_id = self._decode_token(user)
            self.token = user
            self.is_authenticated = True
            print("User ID: ", self.user_id)
            return True, user, self.user_id
        except Exception as e:
            print(f"Authentication failed: {e}")
            print("Full traceback: ", traceback.format_exc())
            return False, None, None

    async def signup(self, username: str, password: str, public_key: str) -> Tuple[bool, Optional[str], Optional[str]]:

        user = await self.surrealdb.signup({
            "NS": self.ns,
            "DB": self.db,
            "AC": "user",
            "name": username,
            "username": username,
            "password": password,
            "public_key": public_key,
        })
        if not user:
            return False, None, None
        self.user_id = self._decode_token(user)
        return True, user, self.user_id


    async def get_user(self, user_id: str) -> Optional[Dict]:
        return await self.surrealdb.select(user_id)

    async def get_user_by_username(self, username: str) -> Optional[Dict]:
        result = await self.surrealdb.query(
            "SELECT * FROM user WHERE username = $username LIMIT 1",
            {"username": username}
        )
        
        if result and result[0]["result"]:
            return result[0]["result"][0]
        
        return None

    async def get_user_by_public_key(self, public_key: str) -> Optional[Dict]:
        result = await self.surrealdb.query(
            "SELECT * FROM user WHERE public_key = $public_key LIMIT 1",
            {"public_key": public_key}
        )

        if result and result[0]["result"]:
            return result[0]["result"][0]
        return None

    async def get_credits(self) -> List:
        user = await self.get_user(self.user_id)
        return user['credits']

    async def get_node(self, node_id: str) -> Optional[Dict]:
        return await self.surrealdb.select(node_id)

    async def list_nodes(self) -> List:
        nodes = await self.surrealdb.query("SELECT * FROM node;")
        return nodes[0]['result']

    async def list_agents(self, agent_name=None) -> List:
        if not agent_name:
            agents = await self.surrealdb.query("SELECT * FROM agent;")
            return agents[0]['result']
        else:
            agent = await self.surrealdb.query("SELECT * FROM agent WHERE id=$agent_name;", {"agent_name": agent_name})
            return agent[0]['result']

    async def list_orchestrators(self, orchestrator_name=None) -> List:
        if not orchestrator_name:
            orchestrators = await self.surrealdb.query("SELECT * FROM orchestrator;")
            return orchestrators[0]['result']
        else:
            orchestrator = await self.surrealdb.query("SELECT * FROM orchestrator WHERE id=$orchestrator_name;", {"orchestrator_name": orchestrator_name})
            return orchestrator[0]['result']

    async def list_environments(self, environment_name=None) -> List:
        if not environment_name:
            environments = await self.surrealdb.query("SELECT * FROM environment;")
            return environments[0]['result']
        else:
            environment = await self.surrealdb.query("SELECT * FROM environment WHERE id=$environment_name;", {"environment_name": environment_name})
            return environment[0]['result']

    async def list_personas(self, persona_name=None) -> List:
        if not persona_name:
            personas = await self.surrealdb.query("SELECT * FROM persona;")
            return personas[0]['result']
        else:
            persona = await self.surrealdb.query("SELECT * FROM persona WHERE id=$persona_name;", {"persona_name": persona_name})
            return persona[0]['result']

    async def delete_agent(self, agent_id: str) -> Tuple[bool, Optional[Dict]]:
        if ":" not in agent_id:
            agent_id = f"agent:{agent_id}".strip()
        print(f"Deleting agent: {agent_id}")
        success = await self.surrealdb.delete(agent_id)
        if success:
            print("Deleted agent")
        else:
            print("Failed to delete agent")
        return success

    async def delete_orchestrator(self, orchestrator_id: str) -> Tuple[bool, Optional[Dict]]:
        if ":" not in orchestrator_id:
            orchestrator_id = f"orchestrator:{orchestrator_id}".strip()
        print(f"Deleting orchestrator: {orchestrator_id}")
        success = await self.surrealdb.delete(orchestrator_id)
        if success:
            print("Deleted orchestrator")
        else:
            print("Failed to delete orchestrator")
        return success

    async def delete_environment(self, environment_id: str) -> Tuple[bool, Optional[Dict]]:
        if ":" not in environment_id:
            environment_id = f"environment:{environment_id}".strip()
        print(f"Deleting environment: {environment_id}")
        success = await self.surrealdb.delete(environment_id)
        if success:
            print("Deleted environment")
        else:
            print("Failed to delete environment")
        return success

    async def delete_persona(self, persona_id: str) -> Tuple[bool, Optional[Dict]]:
        if ":" not in persona_id:
            persona_id = f"persona:{persona_id}".strip()
        print(f"Deleting persona: {persona_id}")
        success = await self.surrealdb.delete(persona_id)
        if success:
            print("Deleted persona")
        else:
            print("Failed to delete persona")
        return success

    async def create_agent(self, agent_config: Dict) -> Tuple[bool, Optional[Dict]]:
        if not agent_config.get('id'):
            return await self.surrealdb.create("agent", agent_config)
        else:
            return await self.surrealdb.create(agent_config.pop('id'), agent_config)

    async def create_orchestrator(self, orchestrator_config: Dict) -> Tuple[bool, Optional[Dict]]:
        if not orchestrator_config.get('id'):
            return await self.surrealdb.create("orchestrator", orchestrator_config)
        else:
            return await self.surrealdb.create(orchestrator_config.pop('id'), orchestrator_config)

    async def create_environment(self, environment_config: Dict) -> Tuple[bool, Optional[Dict]]:
        if not environment_config.get('id'):
            return await self.surrealdb.create("environment", environment_config)
        else:
            return await self.surrealdb.create(environment_config.pop('id'), environment_config)

    async def create_persona(self, persona_config: Dict) -> Tuple[bool, Optional[Dict]]:
        if not persona_config.get('id'):
            return await self.surrealdb.create("persona", persona_config)
        else:
            return await self.surrealdb.create(persona_config.pop('id'), persona_config)

    async def update_agent(self, agent_config: Dict) -> Tuple[bool, Optional[Dict]]:
        return await self.surrealdb.update("agent", agent_config)

    async def create_or_update_agent(self, agent_config: Dict) -> Tuple[bool, Optional[Dict]]:
        list_agents = await self.list_agents(agent_config.get('id'))
        if not list_agents:
            return await self.surrealdb.create("agent", agent_config)
        else:
            return await self.surrealdb.update(agent_config.pop('id'), agent_config)

    async def close(self):
        """Close the database connection"""
        if self.is_authenticated:
            try:
                await self.surrealdb.close()
            except Exception as e:
                logger.error(f"Error closing database connection: {e}")
            finally:
                self.is_authenticated = False
                self.user_id = None
                self.token = None

    async def __aenter__(self):
        """Async enter method for context manager"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async exit method for context manager"""
        await self.close()


async def user_setup_flow(hub_url, public_key):
    async with Hub(hub_url, public_key) as hub:
        username, password = os.getenv("HUB_USERNAME"), os.getenv("HUB_PASSWORD")
        username_exists, password_exists = len(username) > 1, len(password) > 1
        public_key = get_public_key(os.getenv("PRIVATE_KEY")) if os.getenv("PRIVATE_KEY") else None
        logger.info(f"Checking if user exists... User: {username}")
        user = await hub.get_user_by_username(username)
        user_public_key = await hub.get_user_by_public_key(public_key)
        existing_public_key_user = user_public_key is not None and user_public_key.get('username') != username

        match user, username_exists, password_exists, existing_public_key_user:
            case _, True, _, True:
                # Public key exists and doesn't match the provided username and password
                raise Exception(f"Using user credentials in .env. User with public key {public_key} already exists but doesn't match the provided username and password. Please use a different private key (or set blank in the .env file to randomly generate with launch.sh).")

            case _, False, False, True:
                # Public key exists and no username/password provided
                raise Exception(f"Using private key in .env. User with public key {public_key} already exists. Cannot create new user. Please use a different private key (or set blank in the .env file to randomly generate with launch.sh).")

            case None, False, _, False:
                # User doesn't exist and credentials are missing
                logger.info("No credentials provided in .env.")
                create_new = input("Would you like to create a new user? (yes/no): ").lower()
                if create_new != 'yes':
                    raise Exception("User does not exist and new user creation was declined.")
                logger.info("Creating new user...")
                while True:
                    username = input("Enter username: ")
                    existing_user = await hub.get_user_by_username(username)
                    if existing_user:
                        print(f"Username '{username}' already exists. Please choose a different username.")
                        continue
                    password = input("Enter password: ")
                    public_key, private_key_path = generate_keypair(f"{username}.pem")
                    print(f"Signing up user: {username} with public key: {public_key}")
                    success, token, user_id = await hub.signup(username, password, public_key)
                    if success:
                        add_credentials_to_env(username, password, private_key_path)
                        logger.info("Sign up successful!")
                        return token, user_id
                    else:
                        logger.error("Sign up failed. Please try again.")

            case None, True, True, False:
                logger.info("User doesn't exist but some credentials are provided in .env. Using them to create new user.")
                private_key_path = None
                if not public_key:
                    logger.info("No public key provided. Generating new keypair...")
                    public_key, private_key_path = generate_keypair(f"{username}.pem")

                print(f"Signing up user: {username} with public key: {public_key}")
                success, token, user_id = await hub.signup(username, password, public_key)
                if success:
                    if private_key_path:
                        add_credentials_to_env(username, password, private_key_path)
                    logger.info("Sign up successful!")
                    return token, user_id
                else:
                    logger.error("Sign up failed.")
                    raise Exception("Sign up failed.")

            case dict(), True, True, False:
                # User exists, attempt to sign in
                logger.info("Using user credentials in .env. User exists. Attempting to sign in...")
                if os.getenv("PRIVATE_KEY") and is_hex(os.getenv("PRIVATE_KEY")):
                    write_private_key_to_file(os.getenv("PRIVATE_KEY"), username)

                success, token, user_id = await hub.signin(username, password)
                if success:
                    logger.info("Sign in successful!")
                    return token, user_id
                else:
                    logger.error("Sign in failed. Please check your credentials in the .env file.")
                    raise Exception("Sign in failed. Please check your credentials in the .env file.")

            case _:
                logger.error("Unexpected case encountered in user setup flow.")
                raise Exception("Unexpected error in user setup. Please check your configuration and try again.")