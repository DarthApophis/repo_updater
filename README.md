## repo_updater

#### A tool which can perform continuously update on a local repository and perform setup & install on it.
Performs the necessary actions to update the specified repo:
- git pull rebase
- python setup.py sdist
- pip install dist/..

### To configure the tool
The config file **src/git_repo_updater.json** needs to be filled with the required repository and email information:
- repo_location - path to the local git clone ("C:\\Projects\\id-now-tests").
- checkout_branch - the git branch you want to checkout and keep updated ("integration" / "devel" / etc)
- setup_options - if the repo supports extra parameters for the setup procedure you can place it here as one string ("--release IDNOW_Release_8")
- receiver_teams_webhook - define a workflow in Teams and fill this  if you want to receiver notification of failures in a Teams channel/chat
- polling_period - this represents the number in seconds of wait time between each update loop. (3600 = 1hour)

The following fields **all have to** be filled to send email notifications:
- smtp_server - the server used to send the emails (smtp.mailersend.net)
- smtp_port - the port to use for sending the email (587)
- receiver_email_list - a list of receivers  **--If this field is left empty, no emails will be sent--**
- sender_email - the email address used to send emails from.
- user_name - the login username of the sender's address
- user_password - the login user password of the sender's address

### To install the tool:
- open an CLI
- navigate to the root directory of the local git repository (the folder ins which setup.py file is located)
- type and execute the command: `python setup.py sdist`
- then type and execute the command: `pip install dist/repo_updater-0.0.1.tar.gz` 

### To start/run the tool:
 - open a CLI
 - execute the command: `repo_updater`

Once started, the tool runs continuously until manually stopped (CTRL+C)
