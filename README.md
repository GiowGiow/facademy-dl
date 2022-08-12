## facademy-dl
This project is an educational project on how to make a local copy of a Website.

We aim to download to make local copies of videos and pages.

facademy-dl strictly observes the legal regulations and **never circumvents** DRM copy protection.

## How to run
To run the project you'll need to:

1. Clone the project
2. Install poetry
3. Install the dependencies:
    - `cd` into the repo folder
    - Install dependencies with `poetry install`
4. Go to folder src:
    - cd src
5. Set cookies and user agent:
    - Create the cookies.json file
    - Paste the cookies in the file from the extension [EditThisCookie](https://chrome.google.com/webstore/detail/editthiscookie/fngmhnnpilhplaeedifhccceomclgfbg?hl=pt-BR)
    - Create the user_agent.txt file
    - Paste the string you get from searching "my user agent" on google
6. Set needed info
    - Go to the first page of the course, which will be the "Introduction", "Bem vindo", "Benvenutti" or something like that.
    - Paste the link in the `bem_vindo_page` variable in the `main.py` file
7. Run the script
    - Run the script with python main.py
