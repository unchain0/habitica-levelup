"""HTTP session management."""

from aiohttp import ClientSession, ClientTimeout, TCPConnector


class OptimizedClientSession:
    def __init__(
        self,
        max_connections: int = 100,
        max_per_host: int = 30,
        timeout_total: float = 30.0,
        user_id: str | None = None,
    ) -> None:
        self.max_connections = max_connections
        self.max_per_host = max_per_host
        self.timeout_total = timeout_total
        self.user_id = user_id
        self._session: ClientSession | None = None

    async def __aenter__(self) -> ClientSession:
        connector = TCPConnector(
            limit=self.max_connections,
            limit_per_host=self.max_per_host,
            ttl_dns_cache=300,
            use_dns_cache=True,
            keepalive_timeout=30,
        )

        timeout = ClientTimeout(total=self.timeout_total, connect=10, sock_read=20)

        # Habitica requires X-Client header: UserID-appname format
        user_id = self.user_id
        if user_id is None:
            # Lazy import to avoid circular dependency
            from src.delivery.settings import Settings

            user_id = Settings().USER_ID
        client_header = f"{user_id}-habitica-levelup" if user_id else "habitica-levelup"

        self._session = ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                "User-Agent": "habitica-levelup/1.0.0",
                "Content-Type": "application/json",
                "X-Client": client_header,
            },
        )
        return self._session

    async def __aexit__(self, *_) -> None:
        if self._session:
            await self._session.close()
