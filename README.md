OBS Live Captions
=================

- This is a work in progress. Might be some bumps. Definitely needs more documentation. 

- The goal of this tool is to provide free live captions to increase the accessibility of streams. While twitch offers closed captions, there's no way to integrate them into the scene, this solution provides for that.

- The captions aren't bad, but the definitely go off the rails at times. 

- This script uses the [Web Speech API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Speech_API).

- You'll need to use a browser that supports the API. Google Chrome does. Your mileage may vary on other browsers. 

- You can use the API directly via a local file. The reason for the jump through web sockets is to allow you to use transparency in OBS. 

- This works with Python 3.7+

- Creating a virtual environment in your tool of choice is recommended

- Install the requirements with:

        pip install -r requirements.txt 

- After you install, chmod the file with `u+x` and run it with `./obs_live_captions` 

- Some config options are at the top of the python file 

- When you run the file, open your browser to the domain:port defined in the config section

- The URL for the OBS browser source is `domain:port/obs` as defined in the config section 

- Reach on to me on twitter if you have questions: [https://twitter.com/TheIdOfAlan](https://twitter.com/TheIdOfAlan)


