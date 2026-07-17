"""Neo4j driver wrapper for graph persistence operations."""

from __future__ import annotations

from typing import Any
import threading
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError

from loguru import logger

try:
	from neo4j import Driver, GraphDatabase
except ModuleNotFoundError:  # pragma: no cover - exercised when the driver package is missing
	Driver = Any  # type: ignore[assignment]

	class _GraphDatabaseFallback:
		@staticmethod
		def driver(*args: Any, **kwargs: Any) -> Any:
			raise RuntimeError("neo4j package is not installed.")

	GraphDatabase = _GraphDatabaseFallback()

from config.settings import get_settings
from graph.repository import GraphRepository


class GraphManager:
	"""Encapsulate Neo4j connectivity and graph operations."""

	def __init__(
		self,
		uri: str | None = None,
		username: str | None = None,
		password: str | None = None,
		enabled: bool = True,
	) -> None:
		settings = get_settings()
		self.uri = uri or settings.neo4j_uri
		self.username = username or settings.neo4j_username
		self.password = password if password is not None else settings.neo4j_password
		self._driver: Driver | None = None
		self._connection_failed = False
		self._enabled = enabled
		self._retry_count = 0
		self._max_retries = 3
		self._retry_backoff_base = 2
		self.repository = GraphRepository(self)

	def connect(self) -> Driver:
		"""Establish a connection to Neo4j if one is not already open."""
		if not self._enabled:
			logger.warning("Neo4j is disabled, connection attempt blocked")
			raise RuntimeError("Neo4j is disabled")

		if self._driver is not None:
			return self._driver

		# Implement retry logic with exponential backoff
		for attempt in range(self._max_retries):
			if self._connection_failed and attempt > 0:
				backoff_time = self._retry_backoff_base ** attempt
				logger.warning("Neo4j connection previously failed, retry attempt {} after {}s delay", attempt + 1, backoff_time)
				time.sleep(backoff_time)
				self._connection_failed = False

			logger.info("Connecting to Neo4j at {} (attempt {}/{})", self.uri, attempt + 1, self._max_retries)
			try:
				# Use threading-based timeout for Windows compatibility
				def create_driver():
					return GraphDatabase.driver(
						self.uri,
						auth=(self.username, self.password),
						max_connection_lifetime=30,
						max_transaction_retry_time=5,
						connection_timeout=3,
						connection_acquisition_timeout=3,
					)

				with ThreadPoolExecutor(max_workers=1) as executor:
					future = executor.submit(create_driver)
					try:
						driver = future.result(timeout=5)
					except FutureTimeoutError:
						logger.error("Neo4j connection timed out after 5 seconds")
						self._connection_failed = True
						if attempt < self._max_retries - 1:
							continue
						raise RuntimeError("Neo4j connection timed out after 5 seconds")

				# Don't verify connectivity during connection to avoid hanging
				# Connection will be verified on first use
				self._driver = driver
				logger.info("Neo4j driver created (connection will be verified on first use)")
				self._retry_count = 0
				return driver
			except Exception as exc:
				logger.error("Neo4j connection failed: {}", exc)
				self._connection_failed = True
				if attempt < self._max_retries - 1:
					continue
				raise

		raise RuntimeError(f"Neo4j connection failed after {self._max_retries} attempts")

	def close(self) -> None:
		"""Close the graph database connection."""
		if self._driver is None:
			return

		self._driver.close()
		self._driver = None
		logger.info("Neo4j connection closed")

	def reset_connection_failure(self) -> None:
		"""Reset the connection failure flag to allow retry attempts."""
		self._connection_failed = False
		logger.info("Neo4j connection failure flag reset, retry attempts allowed")

	def run_write(self, query: str, parameters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
		"""Execute a write query and return the resulting records."""
		if not self._enabled:
			logger.warning("Neo4j is disabled, skipping write query")
			return []
		try:
			driver = self.connect()
			with driver.session() as session:
				return session.execute_write(lambda tx: tx.run(query, parameters or {}).data())
		except Exception as exc:
			logger.error("Write query failed: {}", exc)
			return []

	def run_read(self, query: str, parameters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
		"""Execute a read query and return the resulting records."""
		if not self._enabled:
			logger.warning("Neo4j is disabled, skipping read query")
			return []
		try:
			driver = self.connect()
			with driver.session() as session:
				return session.execute_read(lambda tx: tx.run(query, parameters or {}).data())
		except Exception as exc:
			logger.error("Read query failed: {}", exc)
			return []

	def graph_exists(self) -> bool:
		"""Return True when the database contains at least one node."""
		return self.repository.graph_exists()

	def node_exists(self, label: str, properties: dict[str, Any]) -> bool:
		"""Return True when a node with the supplied label and properties exists."""
		return self.repository.node_exists(label, properties)

	def relationship_exists(
		self,
		relation_type: str,
		source_label: str,
		source_properties: dict[str, Any],
		target_label: str,
		target_properties: dict[str, Any],
	) -> bool:
		"""Return True when a relationship with the supplied endpoints exists."""
		return self.repository.relationship_exists(
			relation_type=relation_type,
			source_label=source_label,
			source_properties=source_properties,
			target_label=target_label,
			target_properties=target_properties,
		)

	def create_task_node(self, task_id: str, query: str, task_type: str, timestamp: str) -> list[dict[str, Any]]:
		return self.repository.create_task_node(task_id, query, task_type, timestamp)

	def create_agent_node(self, name: str, description: str) -> list[dict[str, Any]]:
		return self.repository.create_agent_node(name, description)

	def create_skill_node(self, name: str) -> list[dict[str, Any]]:
		return self.repository.create_skill_node(name)

	def create_finding_node(
		self,
		task_id: str,
		source_agent: str,
		content: str,
		category: str,
		confidence: float,
	) -> list[dict[str, Any]]:
		return self.repository.create_finding_node(task_id, source_agent, content, category, confidence)

	def create_risk_node(
		self,
		task_id: str,
		source_agent: str,
		description: str,
		severity: str,
	) -> list[dict[str, Any]]:
		return self.repository.create_risk_node(task_id, source_agent, description, severity)

	def create_recommendation_node(
		self,
		task_id: str,
		source_agent: str,
		content: str,
		priority: str,
	) -> list[dict[str, Any]]:
		return self.repository.create_recommendation_node(task_id, source_agent, content, priority)

	def create_relationship(
		self,
		source_label: str,
		source_properties: dict[str, Any],
		relation_type: str,
		target_label: str,
		target_properties: dict[str, Any],
		relationship_properties: dict[str, Any] | None = None,
	) -> list[dict[str, Any]]:
		return self.repository.create_relationship(
			source_label=source_label,
			source_properties=source_properties,
			relation_type=relation_type,
			target_label=target_label,
			target_properties=target_properties,
			relationship_properties=relationship_properties,
		)

	def get_stats(self) -> dict[str, int]:
		"""Return counts for the primary graph node types."""
		try:
			return self.repository.get_stats()
		except Exception:
			logger.exception("Failed to fetch graph statistics")
			return {
				"tasks": 0,
				"agents": 0,
				"findings": 0,
				"risks": 0,
				"recommendations": 0,
			}

	def get_schema_summary(self) -> dict[str, object]:
		"""Return a static graph schema summary for the API."""
		return self.repository.get_schema_summary()