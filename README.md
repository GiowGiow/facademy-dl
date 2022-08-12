## facademy-dl
This project is an educational project on how to make a local copy of a Website.
We aim to download to make local copies of videos and pages.

facadmy-dl strictly observes the legal regulations and **never circumvents** DRM copy protection.

It may also not be legal to download the content from the website depending on where you live.
Your account may be terminated if you use this project to download the content.
We are not responsible for how you use this project, we are not responsible for any legal issues you may face.

## How to run
To run the project you'll need to:

1. Clone the project
2. Install poetry
3. Install the dependencies:
    - `cd` into the repo folder
    - Enter poetry shell using `poetry shell`
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
    - Identify on that page what will be the name of the course:
        - Identify the element that contains the course name, it will be like `"Español 2 / ¡Bienvenido! / Bem-vindo"`
        - The course name will be the first part of the string, in this case, `"Español 2"`
7. Run the script
    - Run the script with python main.py <course_name>
