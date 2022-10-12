# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

from sentry_sdk.hub import Hub
from sentry_sdk.integrations import Integration
from sentry_sdk.tracing_utils import record_sql_queries
from frappe.database.database import Database
from sentry_sdk.utils import capture_internal_exceptions


class FrappeIntegration(Integration):
	identifier = "frappe"

	@staticmethod
	def setup_once():
		real_connect = Database.connect
		real_sql = Database.sql

		def sql(self, query, values=None, *args, **kwargs):
			hub = Hub.current

			if not self._conn:
				self.connect()

			with record_sql_queries(
				hub, self._cursor, query, values, paramstyle="pyformat", executemany=False
			):
				return real_sql(self, query, values or (), *args, **kwargs)

		def connect(self):
			hub = Hub.current
			with capture_internal_exceptions():
				hub.add_breadcrumb(message="connect", category="query")

			with hub.start_span(op="db", description="connect"):
				return real_connect(self)

		Database.connect = connect
		Database.sql = sql

