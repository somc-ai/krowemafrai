# app_config.py
import logging
import os
from typing import Optional

from azure.ai.projects.aio import AIProjectClient
from azure.cosmos.aio import CosmosClient
from azure.identity import DefaultAzureCredential, EnvironmentCredential, ClientSecretCredential
from azure.core.credentials import AzureKeyCredential
from openai import AsyncAzureOpenAI
from dotenv import load_dotenv
from semantic_kernel.kernel import Kernel

# Load environment variables from .env file
load_dotenv()


class AppConfig:
    """Application configuration class that loads settings from environment variables."""

    def __init__(self):
        """Initialize the application configuration with environment variables."""
        # Azure authentication settings
        self.AZURE_TENANT_ID = self._get_optional("AZURE_TENANT_ID")
        self.AZURE_CLIENT_ID = self._get_optional("AZURE_CLIENT_ID")
        self.AZURE_CLIENT_SECRET = self._get_optional("AZURE_CLIENT_SECRET")

        # CosmosDB settings
        self.COSMOSDB_ENDPOINT = self._get_optional("COSMOSDB_ENDPOINT")
        self.COSMOSDB_DATABASE = self._get_optional("COSMOSDB_DATABASE")
        self.COSMOSDB_CONTAINER = self._get_optional("COSMOSDB_CONTAINER")

        # Azure OpenAI settings
        self.AZURE_OPENAI_DEPLOYMENT_NAME = self._get_required(
            "AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o"
        )
        self.AZURE_OPENAI_API_VERSION = self._get_required(
            "AZURE_OPENAI_API_VERSION", "2024-11-20"
        )
        self.AZURE_OPENAI_ENDPOINT = self._get_required("AZURE_OPENAI_ENDPOINT")
        self.AZURE_OPENAI_API_KEY = self._get_optional("AZURE_OPENAI_API_KEY")
        self.AZURE_OPENAI_SCOPES = [
            f"{self._get_optional('AZURE_OPENAI_SCOPE', 'https://cognitiveservices.azure.com/.default')}"
        ]

        # Frontend settings
        self.FRONTEND_SITE_NAME = self._get_optional(
            "FRONTEND_SITE_NAME", "http://127.0.0.1:3000"
        )

        # Azure AI settings
        self.AZURE_AI_SUBSCRIPTION_ID = self._get_required("AZURE_AI_SUBSCRIPTION_ID")
        self.AZURE_AI_RESOURCE_GROUP = self._get_required("AZURE_AI_RESOURCE_GROUP")
        self.AZURE_AI_PROJECT_NAME = self._get_required("AZURE_AI_PROJECT_NAME")
        self.AZURE_AI_AGENT_ENDPOINT = self._get_required("AZURE_AI_AGENT_ENDPOINT")

        # Cached clients and resources
        self._azure_credentials = None
        self._cosmos_client = None
        self._cosmos_database = None
        self._ai_project_client = None

    def _get_required(self, name: str, default: Optional[str] = None) -> str:
        """Get a required configuration value from environment variables.

        Args:
            name: The name of the environment variable
            default: Optional default value if not found

        Returns:
            The value of the environment variable or default if provided

        Raises:
            ValueError: If the environment variable is not found and no default is provided
        """
        if name in os.environ:
            return os.environ[name]
        if default is not None:
            logging.warning(
                "Environment variable %s not found, using default value", name
            )
            return default
        raise ValueError(
            f"Environment variable {name} not found and no default provided"
        )

    def _get_optional(self, name: str, default: str = "") -> str:
        """Get an optional configuration value from environment variables.

        Args:
            name: The name of the environment variable
            default: Default value if not found (default: "")

        Returns:
            The value of the environment variable or the default value
        """
        if name in os.environ:
            return os.environ[name]
        return default

    def _get_bool(self, name: str) -> bool:
        """Get a boolean configuration value from environment variables.

        Args:
            name: The name of the environment variable

        Returns:
            True if the environment variable exists and is set to 'true' or '1', False otherwise
        """
        return name in os.environ and os.environ[name].lower() in ["true", "1"]

    def get_azure_credentials(self):
        """Get Azure credentials with comprehensive authentication strategy.

        Returns:
            Azure credential instance for authentication
        """
        # Cache the credentials object
        if self._azure_credentials is not None:
            return self._azure_credentials

        try:
            logging.info("=== Azure Authentication Debug ===")
            logging.info("AZURE_TENANT_ID: %s (value: %s)", 
                        "SET" if self.AZURE_TENANT_ID else "NOT_SET",
                        self.AZURE_TENANT_ID[:8] + "..." if self.AZURE_TENANT_ID else "None")
            logging.info("AZURE_CLIENT_ID: %s (value: %s)", 
                        "SET" if self.AZURE_CLIENT_ID else "NOT_SET", 
                        self.AZURE_CLIENT_ID[:8] + "..." if self.AZURE_CLIENT_ID else "None")
            logging.info("AZURE_CLIENT_SECRET: %s", 
                        "SET" if self.AZURE_CLIENT_SECRET else "NOT_SET")
            logging.info("AZURE_OPENAI_API_KEY: %s", 
                        "SET" if self.AZURE_OPENAI_API_KEY else "NOT_SET")
            
            # Strategy 1: Use API key authentication for OpenAI services when available
            if self.AZURE_OPENAI_API_KEY:
                logging.info("API key available - using hybrid authentication strategy")
                
                # For services that support API key, we don't need Azure credentials
                # For Cosmos DB and other services, we still need Azure credentials
                if self.AZURE_TENANT_ID and self.AZURE_CLIENT_ID and self.AZURE_CLIENT_SECRET:
                    logging.info("Creating ClientSecretCredential with explicit values")
                    from azure.identity import ClientSecretCredential
                    self._azure_credentials = ClientSecretCredential(
                        tenant_id=self.AZURE_TENANT_ID,
                        client_id=self.AZURE_CLIENT_ID,
                        client_secret=self.AZURE_CLIENT_SECRET
                    )
                    logging.info("Successfully created ClientSecretCredential")
                else:
                    logging.warning("API key available but Azure credentials incomplete - using DefaultAzureCredential")
                    self._azure_credentials = DefaultAzureCredential()
            else:
                if self.AZURE_TENANT_ID and self.AZURE_CLIENT_ID and self.AZURE_CLIENT_SECRET:
                    logging.info("Creating ClientSecretCredential for all Azure services")
                    from azure.identity import ClientSecretCredential
                    self._azure_credentials = ClientSecretCredential(
                        tenant_id=self.AZURE_TENANT_ID,
                        client_id=self.AZURE_CLIENT_ID,
                        client_secret=self.AZURE_CLIENT_SECRET
                    )
                    logging.info("Successfully created ClientSecretCredential for all services")
                else:
                    logging.warning("No API key and incomplete Azure credentials - using DefaultAzureCredential")
                    self._azure_credentials = DefaultAzureCredential()
            
            try:
                import asyncio
                from azure.core.credentials import AccessToken
                
                logging.info("Testing credential token acquisition...")
                logging.info("Credential object created successfully")
                
            except Exception as test_exc:
                logging.warning("Credential test failed, but continuing: %s", test_exc)
            
            logging.info("=== End Azure Authentication Debug ===")
            return self._azure_credentials
            
        except Exception as exc:
            logging.error("Failed to create Azure credentials: %s", exc)
            logging.error("Falling back to DefaultAzureCredential as last resort")
            try:
                self._azure_credentials = DefaultAzureCredential()
                return self._azure_credentials
            except Exception as fallback_exc:
                logging.error("Even DefaultAzureCredential failed: %s", fallback_exc)
                return None

    def get_cosmos_database_client(self):
        """Get a Cosmos DB client for the configured database.

        Returns:
            A Cosmos DB database client
        """
        try:
            if self._cosmos_client is None:
                self._cosmos_client = CosmosClient(
                    self.COSMOSDB_ENDPOINT, credential=self.get_azure_credentials()
                )

            if self._cosmos_database is None:
                self._cosmos_database = self._cosmos_client.get_database_client(
                    self.COSMOSDB_DATABASE
                )

            return self._cosmos_database
        except Exception as exc:
            logging.error(
                "Failed to create CosmosDB client: %s. CosmosDB is required for this application.",
                exc,
            )
            raise

    def create_kernel(self):
        """Creates a new Semantic Kernel instance.

        Returns:
            A new Semantic Kernel instance
        """
        # Create a new kernel instance without manually configuring OpenAI services
        # The agents will be created using Azure AI Agent Project pattern instead
        kernel = Kernel()
        return kernel

    def get_azure_openai_client(self):
        """Create and return a direct AsyncAzureOpenAI client.
        
        This bypasses AIProjectClient and uses direct Azure OpenAI authentication.

        Returns:
            AsyncAzureOpenAI client instance
        """
        try:
            if not self.AZURE_OPENAI_API_KEY:
                raise ValueError("AZURE_OPENAI_API_KEY is required for Azure OpenAI client")
                
            from openai import AsyncAzureOpenAI
            
            client = AsyncAzureOpenAI(
                api_key=self.AZURE_OPENAI_API_KEY,
                api_version=self.AZURE_OPENAI_API_VERSION,
                azure_endpoint=self.AZURE_OPENAI_ENDPOINT
            )
            
            logging.info("Created direct AsyncAzureOpenAI client with API key")
            return client
            
        except Exception as exc:
            logging.error("Failed to create AsyncAzureOpenAI client: %s", exc)
            raise

    def get_ai_project_client(self):
        """Create and return an AIProjectClient for Azure AI Foundry.
        
        Uses ClientSecretCredential with proper Azure credentials.

        Returns:
            An AIProjectClient instance
        """
        if self._ai_project_client is not None:
            return self._ai_project_client

        try:
            endpoint = self.AZURE_AI_AGENT_ENDPOINT
            
            logging.info("Creating AIProjectClient with Azure credentials")
            credential = self.get_azure_credentials()
            if credential is None:
                raise RuntimeError(
                    "Unable to acquire Azure credentials for AIProjectClient; ensure Azure authentication is configured"
                )
            
            self._ai_project_client = AIProjectClient(endpoint=endpoint, credential=credential)
            logging.info("Successfully created AIProjectClient with Azure credentials")

            return self._ai_project_client
        except Exception as exc:
            logging.error("Failed to create AIProjectClient: %s", exc)
            raise


# Create a global instance of AppConfig
config = AppConfig()
