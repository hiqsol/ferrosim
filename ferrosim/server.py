from __future__ import annotations

import argparse
import logging

from ferrosim.config import load_config
from ferrosim.fleet import Fleet
from ferrosim.grpc_service import create_server


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the c-ferrosim gRPC server.")
    parser.add_argument("--config", required=True, help="Path to fleet config YAML.")
    parser.add_argument("--bind", default="127.0.0.1:50051", help="Address to bind.")
    parser.add_argument("--workers", type=int, default=16, help="gRPC worker count.")
    parser.add_argument("--log-level", default="INFO", help="Python logging level.")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    config = load_config(args.config)
    fleet = Fleet(config)
    server = create_server(fleet, max_workers=args.workers)
    server.add_insecure_port(args.bind)
    server.start()
    logging.getLogger(__name__).info("ferrosim server listening on %s", args.bind)
    server.wait_for_termination()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
