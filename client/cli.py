"""CLI client: python -m client.cli create|list|get|delete ..."""
import argparse
import json
import os
import sys
import requests
from requests.auth import HTTPBasicAuth

def build_parser():
    parser = argparse.ArgumentParser(description="Client for the Message Vault API")
    parser.add_argument("--base-url", default=os.getenv("MESSAGE_VAULT_URL", "https://localhost:8443"))
    parser.add_argument("--username", default=os.getenv("APP_USERNAME"))
    parser.add_argument("--password", default=os.getenv("APP_PASSWORD"))
    parser.add_argument("--ca-bundle", default=os.getenv("TLS_CA_BUNDLE"), help="CA/certificate PEM path; omit only for local self-signed development")
    sub = parser.add_subparsers(dest="command", required=True)
    create = sub.add_parser("create", help="Send a message")
    create.add_argument("message", help="Message text")
    sub.add_parser("list", help="List all messages")
    get = sub.add_parser("get", help="Retrieve a message")
    get.add_argument("id", type=int)
    delete = sub.add_parser("delete", help="Delete a message")
    delete.add_argument("id", type=int)
    return parser

def main(argv=None):
    args = build_parser().parse_args(argv)
    # Below SSL verification can be disabled or enabled based on need. However application is implemented to support both cases.
    verify = args.ca_bundle if args.ca_bundle else True
    url = args.base_url.rstrip("/") + "/api/messages"
    auth = HTTPBasicAuth(args.username, args.password)
    try:
        if args.command == "create":
            response = requests.post(url, json={"message": args.message}, auth=auth, verify=verify, timeout=10)
        elif args.command == "list":
            response = requests.get(url, auth=auth, verify=verify, timeout=10)
        elif args.command == "get":
            response = requests.get(f"{url}/{args.id}", auth=auth, verify=verify, timeout=10)
        elif args.command == "delete":
            response = requests.delete(f"{url}/{args.id}", auth=auth, verify=verify, timeout=10)
        else:
            raise ValueError(f"Unknown command: {args.command}")
        if response.status_code == 204:
            print("Deleted successfully.")
            return 0
        response.raise_for_status()
        print(json.dumps(response.json(), indent=2))
        return 0
    except requests.RequestException as exc:
        print(f"Request failed: {exc}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
