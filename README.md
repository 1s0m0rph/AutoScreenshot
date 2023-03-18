# AutoScreenshot
I accidentally hit the print screen button a lot. Turns out it can be kinda fun to browse through those accidental screenshots.

# How to use

This is intended to be used as a "run it all the time" script. You'll need a few things done to get it set up (instructions are for linux, I'm running Ubuntu):

1. clone this repo
2. change the screenshot dir to whatever you want (probably want to use your actual username at least). That's the SCREENSHOT_DIR variable
3. add '@reboot /path/to/this/repo/auto_ss.py' to your crontab (crontab -e)
4. reboot, and you should be up and running!
