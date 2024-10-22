import os
import aiohttp
import asyncio
import json
import argparse
import requests
import jq

def generate_github_issues(issues, github_api_key, github_repo):
    print(f"Generate Issues: Set")
    from github import Github
    from github import GithubException
    from github import Auth

    auth = Auth.Token(github_api_key)
    g = Github(auth=auth)

    if not github_repo:
        print("Error: GitHub repository is not specified.")
        return
    
    repo = None
    try:
        repo = g.get_repo(github_repo)
    except GithubException as e:
        print(f"Error accessing repository: {e}")
        return
    
    # Create a dictionary to store existing issue titles and their corresponding issues
    existing_issues = {}

    # Fetch all existing issues in the repository
    for issue in repo.get_issues(state='all'):
        existing_issues[issue.title] = issue

    print(f"Found {len(existing_issues)} existing issues in the repository.")

    for issue in issues:
        id = issue.get("bug_id")
        if id is not None:
            title = issue.get("bug_title")
            body = issue.get("bug_description")
            print(f"Creating issue: {title}")
            if title in existing_issues.keys() and existing_issues[title].state == "open":
                print(f"Issue {title} already exists in an open state, skipping")
                continue
            try:
                repo.create_issue(title=title, body=body, assignee="hackbot_ci")
            except GithubException as e:
                print(f"Error creating issue: {e}")
                if e.status == 422:
                    raise Exception(f"Validation failed, aborting. This functionality requires a GITHUB_TOKEN with 'issues: write' in the workflow permissions section.")
                elif e.status == 403:
                    raise Exception(f"Forbidden, aborting. This functionality requires a GITHUB_TOKEN with 'issues: write' in the workflow permissions section.")
                elif e.status == 410:
                    raise Exception(f"Gone, aborting. The repository does not allow issues.")

def authenticate(address, port, api_key):
    url = f"http://{address}:{port}/api/authenticate"
    headers = {"X-API-KEY": f"{api_key}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return True
    else:
        raise Exception(f"Failed: {response.status_code}")


def hack(address, port, api_key, output):
    async def process_stream(response):
        results = []
        async for line in response.content:
            line = line.decode("utf-8")
            if line.startswith("data: "):
                try:
                    json_str = line[5:].strip()  # Remove 'data: ' prefix
                    # Stream to stdout
                    print(f"{json_str}")
                    json_obj = json.loads(json_str)
                    results.append(json_obj)
                except json.JSONDecodeError:
                    print(f"Failed to parse JSON: {json_str}")
        return results

    async def make_request(session, url, data, headers):
        async with session.post(url, data=data, headers=headers) as response:
            return response.status, await process_stream(response)

    async def main():
        url = f"http://{address}:{port}/api/hack"
        headers = {"X-API-KEY": f"{api_key}", "Connection": "keep-alive"}

        data = aiohttp.FormData()
        data.add_field(
            "file",
            open("src.zip", "rb"),
            filename="src.zip",
            content_type="application/zip",
        )
        data.add_field("repo_url", f"https://github.com/${{github.repository}}")

        async with aiohttp.ClientSession() as session:
            status, response = await make_request(session, url, data, headers)
            results = response

        if output is not None:
            # Check if the output contains a directory
            output_dir = os.path.dirname(output)
            if output_dir and not os.path.exists(output_dir):
                try:
                    os.makedirs(output_dir, exist_ok=True)
                    # Append each result to a JSON file
                except OSError as e:
                    print(f"Error creating output file {output}: {e}")

            with open(output, "w") as f:
                json.dump(response, f, indent=2)

        return status, response

    status, response = asyncio.run(main())
    if status != 200:
        raise Exception(f"Failed: {status}: {response}")

    return response

def handle_options():
    parser = argparse.ArgumentParser(
        description="Hackbot API client for interacting with the bot server."
    )
    parser.add_argument(
        "--address", type=str, required=True, help="The address of the bot server."
    )
    parser.add_argument(
        "--port", type=str, required=True, help="The port number of the bot server."
    )
    parser.add_argument(
        "--api_key",
        type=str,
        required=True,
        help="API key for authentication with the bot server.",
    )
    parser.add_argument(
        "--output",
        type=str,
        required=False,
        help="Path to the output file for storing results.",
    )
    parser.add_argument(
        "--authenticate",
        action="store_true",
        default=False,
        help="Perform authentication only without hacking.",
    )

    # Create a subparser for the issue generation options
    issue_parser = parser.add_argument_group("Issue Generation Options")
    issue_parser.add_argument(
        "--generate_issues",
        type=lambda x: x.lower() == 'true',
        default=False,
        help="Generate issues based on the hack results (true/false)",
    )
    issue_parser.add_argument(
        "--issues_repo",
        type=str,
        help="The repository to generate issues in (format: username/repo)",
    )
    issue_parser.add_argument(
        "--github_api_key",
        type=str,
        help="GitHub API key for issue generation",
    )
    args = parser.parse_args()

    # Add validation for issue generation options
    if args.generate_issues:
        if not args.issues_repo:
            parser.error("--issues_repo is required when --generate_issues is set")
        if not args.github_api_key:
            parser.error("--github_api_key is required when --generate_issues is set")

    return args


if __name__ == "__main__":
    
    args = handle_options()

    # Get GITHUB_OUTPUT environment variable
    github_output = os.environ.get("GITHUB_OUTPUT")

    # Print program CLI header
    print("=" * 50)
    print(f"Hackbot {'CI Action' if github_output else 'API Client'}")
    print(f"Server: {args.address}:{args.port}")
    print(f"API Key: {'Set' if args.api_key else 'Not set'}")
    print(f"Output: {args.output if args.output else 'Not specified'}")
    if args.generate_issues:
        print(f"Issue Generation: {args.issues_repo}")
    if args.authenticate:
        print("Authentication only")
    print("=" * 50)
    print()

    # Try the credentials before doing anything else
    try:
        authenticate(args.address, args.port, args.api_key)
        print("Authentication successful")
    except Exception as e:
        print(e)
        exit(1)

    # If we only want to authenticate, we can exit here
    if args.authenticate:
        exit(0)

    # Hack the contract
    try:
        results = hack(
            address=args.address,
            port=args.port,
            api_key=args.api_key,
            output=args.output
        )

        if github_output:
            with open(github_output, "a") as f:
                compact_json = jq.compile(".").input(json.dumps(results)).text()
                f.write(f"results={compact_json}\n")

        # Print the contents of github_output
        if github_output:
            print("Contents of GITHUB_OUTPUT:")
            with open(github_output, "r") as f:
                print(f.read())

    except Exception as e:
        print(e)
        exit(1)

    if args.generate_issues:
        try:
            generate_github_issues(results, args.github_api_key, args.issues_repo)
        except Exception as e:
            print(e)
            exit(1)
