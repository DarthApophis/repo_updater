"""
Requirements: GitPython
"""
import os
import json
import time
import email
import socket
import smtplib
import subprocess

from dataclasses import dataclass

import git
import pymsteams

NO_CHANGES = "Already up to date."
DATA_FILE_NAME = "config_file.json"
DIST_FOLDER = "dist"
DEFAULT_POLLING_PERIOD = 60  # seconds of wait time before each iteration


@dataclass
class ConfigData:
    """
    Dataclass to map all the information inside the config file.
    Any changes to one of them must be made to both.
    """
    repo_location: str
    checkout_branch: str
    setup_options: str
    install_options: str
    receiver_teams_webhook: str
    smtp_server: str
    smtp_port: str
    receiver_email_list: str
    sender_email: str
    user_name: str
    user_password: str
    polling_period: int


def main():
    """
    Repo updater main method
    Runs continuously until manually stopped (CTRL+C)

    Returns:
        None
    """
    print("\nStarted Repo Updater...")
    polling_period = DEFAULT_POLLING_PERIOD
    config_data = load_config_data()
    if config_data:
        polling_period = config_data.polling_period

    while True:
        print("Updating...")
        print("To stop the program close the console or use KeyboardInterrupt (CTRL+C)")
        try:
            config_data = load_config_data()
            if config_data:
                polling_period = config_data.polling_period
                repo_update(config_data)
        except KeyboardInterrupt:
            print("Repo Updater stopped with KeyboardInterrupt (CTRL+C)")
            return
        except Exception as ex:
            workstation_id = socket.gethostname()
            loop_error_title = f"FAILURE in RepoUpdater tool\n"
            loop_error_msg = (f"running on workstation: {workstation_id}\n"
                              f"for repo:'{config_data.repo_location}'"
                              f"::{config_data.checkout_branch}\n"
                              f"with exception:\n{ex}")
            print(loop_error_title+loop_error_msg)
            send_teams_webhook(loop_error_title, loop_error_msg, config_data)
            send_email(loop_error_title, loop_error_msg, config_data)
        period_in_min = polling_period/60
        print(f"Waiting {period_in_min:.2f} minutes until next update.\n")
        try:
            time.sleep(polling_period)
        except KeyboardInterrupt:
            print("\nRepo Updater stopped with KeyboardInterrupt (CTRL+C)\n")
            return


def load_config_data():
    """

    Returns:
        ConfigData - an instance of ConfigData with the information loaded from file
    """
    path_to_config_file = os.path.join(os.path.dirname(__file__), DATA_FILE_NAME)
    try:
        with open(path_to_config_file, "r", encoding="utf-8") as file_h:
            file_content = json.load(file_h)
            config_data = ConfigData(**file_content)
    except Exception as ex:
        load_config_data_error_msg = f"FAILED to read config data:\n{ex}"
        print(load_config_data_error_msg)
        return None
    return config_data


def repo_update(config_data: ConfigData):
    """
    Performs the necessary action to update the specified repo:
    -git pull rebase
    -python setup.py sdist
    -pip install dist/..

    Args:
        config_data (ConfigData): instance of ConfigData
                                containing relevant repo information

    Returns:
        None
    """
    if not config_data:
        print("Missing config data to perform repo update.")
        return

    print(f"Target repo location: {config_data.repo_location},"
          f" branch: {config_data.checkout_branch}")

    rebase_result = git_pull_rebase(config_data)

    if not rebase_result:
        successfully_updated_msg_content = (
            f"Repository '{config_data.repo_location}'"
            f"::{config_data.checkout_branch} is already up to date.\n"
        )
        print(successfully_updated_msg_content)
        return

    workstation_id = socket.gethostname()
    new_commits_msg = "\nUpdated with the following commits:\n"
    for idx, new_commit in enumerate(rebase_result):
        new_commits_msg += (f"\nCommit #{idx+1}\n"
                            f"Author: {new_commit.author}\n"
                            f"Commit message:\n{new_commit.message}")

    success_msg_title = "SUCCESSFUL RepoUpdater notification"
    success_msg_content = (
        f"RepoUpdater running on workstation: {workstation_id}.\n"
        f"successfully updated repo:'{config_data.repo_location}'"
        f"::{config_data.checkout_branch}\n"
        f"{new_commits_msg}"
        f"Next update scheduled in {config_data.polling_period/60:.2f} minutes."
        )

    cleanup_dist_location(config_data)

    python_setup_sdist(config_data)

    pip_install_dist(config_data)

    send_teams_webhook(success_msg_title, success_msg_content, config_data)


def git_pull_rebase(config_data) -> list[git.Commit]:
    """
    Uses the GitPython library to perform a checkout and a git pull rebase operations.

    Args:
        config_data ():

    Returns:

    """
    repo_git = git.Git(config_data.repo_location)
    repo = git.Repo(config_data.repo_location)
    try:
        repo_git.execute(
            f"git checkout {config_data.checkout_branch}")
        commits_behind = repo.iter_commits(
            f'{config_data.checkout_branch}..origin/{config_data.checkout_branch}')
        repo_git.execute(
            f"git pull --rebase origin {config_data.checkout_branch}")
        print("GIT REBASE SUCCESSFUL")
    except Exception as ex:
        git_error_msg = (f"FAILED updating repo {config_data.repo_location} "
                         f"with exception: \n{ex}")
        raise Exception(git_error_msg)
    return list(commits_behind)


def cleanup_dist_location(config_data):
    """
    Clears the DIST folder of any old archives to avoid install a wrong one

    Args:
        config_data ():

    Returns:

    """
    dist_folder = os.path.join(config_data.repo_location, DIST_FOLDER)
    dist_items = os.listdir(dist_folder)
    try:
        for dist_item in dist_items:
            os.remove(os.path.join(dist_folder, dist_item))
    except Exception as ex:
        dist_cleanup_error_msg = (f"FAILED to delete dist item {dist_item} "
                                  f"with exception:\n{ex}")
        raise Exception(dist_cleanup_error_msg)


def python_setup_sdist(config_data):
    """
    Performs a setup sdist inside a subprocess.

    Args:
        config_data ():

    Returns:

    """
    setup_cmd = ["python",
                 "setup.py",
                 "sdist",
                 *config_data.setup_options.split()]
    setup_process = subprocess.run(setup_cmd,
                                   shell=True,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE,
                                   cwd=config_data.repo_location)
    if "Creating tar archive" in str(setup_process.stdout):
        print("SDIST SUCCESSFUL")
    else:
        sdist_error_msg = f"SDIST FAILED:\n{str(setup_process.stderr.decode('utf-8'))}"
        raise Exception(sdist_error_msg)


def pip_install_dist(config_data):
    """
    Performs a pip install inside a subprocess.

    Args:
        config_data ():

    Returns:

    """
    dist_pckg = os.listdir(os.path.join(config_data.repo_location, DIST_FOLDER))[0]
    install_cmd = ["pip",
                   "install",
                   f"{DIST_FOLDER}/{dist_pckg}",
                   *config_data.install_options.split()]
    install_process = subprocess.run(install_cmd,
                                     shell=True,
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE,
                                     cwd=config_data.repo_location)
    if "Successful" in str(install_process.stdout):
        print("INSTALL SUCCESSFUL")
    else:
        install_error_msg = f"INSTALL FAILED:\n{install_process.stderr.decode('utf-8')}"
        raise Exception(install_error_msg)


def send_email(msg_title, msg_content, config_data: ConfigData):
    """
    Email the configured receiver with a given message.

    Args:
        msg_title (str):
        msg_content (str):
        config_data (ConfigData):

    Returns:
        None
    """
    try:
        receiver_data = config_data.receiver_email_list
        if not receiver_data:
            print("Cannot send emails, receiver email not configured.\n"
                  "If you want email notifications, please configure the JSON file.")
            return
        emsg = email.message.EmailMessage()
        emsg['Subject'] = msg_title
        emsg['To'] = ", ".join(config_data.receiver_email_list)
        emsg['From'] = config_data.sender_email
        emsg.set_content(msg_content)
        with smtplib.SMTP(config_data.smtp_server, int(config_data.smtp_port)) as s:
            s.starttls()
            auth_result = s.login(config_data.user_name, config_data.user_password)
            send_result = s.send_message(emsg)
            print(f"Auth: {auth_result}\n"
                  f"Sent: {send_result}")
    except Exception as ex:
        print(f"FAILED to send email with exception:\n{ex}")


def send_teams_webhook(msg_title,msg_content, config_data: ConfigData):
    """
    Send a teams message to the configured receiver with a given message.

    Args:
        msg_title (str):
        msg_content (str):
        config_data (ConfigData):

    Returns:
        None
    """
    try:
        if not config_data.receiver_teams_webhook:
            print("Cannot send Teams messages, receiver Teams webhook not configured.\n"
                  "If you want Teams notifications, please configure the JSON file.")
            return
        t_msg = pymsteams.connectorcard(config_data.receiver_teams_webhook)
        msg_content = "<pre>"+"<br>".join(msg_content.splitlines())+ "</pre>"
        t_msg.title(msg_title)
        t_msg.text(msg_content)
        t_msg.send()
    except Exception as ex:
        print(f"FAILED to send Teams webhook with exception:\n{ex}")


if __name__ == "__main__":
    main()
