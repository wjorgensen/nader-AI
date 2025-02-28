import requests
import os
import dotenv
import base64

dotenv.load_dotenv()

class GithubWorker:
    def __init__(self):
        """
        Initialize the GithubWorker with an optional Personal Access Token.
        """
        token = os.getenv("GITHUB_PAT")
        self.base_url = "https://api.github.com"
        self.headers = {"Authorization": f"token {token}"} if token else {}

    def get_user_repositories(self, username):
        """
        Get a list of non-forked repositories for a given GitHub user.
        """
        url = f"{self.base_url}/users/{username}/repos"
        response = requests.get(url, headers=self.headers)

        if response.status_code == 200:
            repos = response.json()
            # Filter out forked repositories
            non_fork_repos = [
                {"name": repo["name"], "stars": repo["stargazers_count"]}
                for repo in repos if not repo.get("fork", False)
            ]
            return non_fork_repos
        else:
            print(f"Error: {response.status_code}, {response.json().get('message')}")
            return None

    def get_repo_stars(self, username, repo_name):
        """
        Get the number of stars for a specific repository.
        """
        url = f"{self.base_url}/repos/{username}/{repo_name}"
        response = requests.get(url, headers=self.headers)

        if response.status_code == 200:
            data = response.json()
            return data["stargazers_count"]
        else:
            print(f"Error: {response.status_code}, {response.json().get('message')}")
            return None

    def get_repo_description(self, username, repo_name):
        """
        Get the description for a specific repository.
        """
        url = f"{self.base_url}/repos/{username}/{repo_name}"
        response = requests.get(url, headers=self.headers)

        if response.status_code == 200:
            data = response.json()
            return data["description"]
        else:
            print(f"Error: {response.status_code}, {response.json().get('message')}")
            return None

    def get_repo_readme(self, username, repo_name):
        """
        Get the README content for a specific repository and decode it from Base64.
        """
        url = f"{self.base_url}/repos/{username}/{repo_name}/readme"
        response = requests.get(url, headers=self.headers)

        if response.status_code == 200:
            data = response.json()
            decoded_content = base64.b64decode(data["content"]).decode('utf-8')
            return decoded_content
        else:
            print(f"Error: {response.status_code}, {response.json().get('message')}")
            return None

if __name__ == "__main__":
    username = "torvalds"
    worker = GithubWorker()

    repos = worker.get_user_repositories(username)
    if repos:
        print(f"\nNon-forked Repositories for {username}:")
        for repo in repos:
            print(f"{repo['name']}: ⭐ {repo['stars']} stars")
            desc = worker.get_repo_description(username, repo["name"])
            print(f"Description: {desc}\n")
            readme = worker.get_repo_readme(username, repo["name"])
            print(f"Readme:\n{readme}\n")
