# AutoScreenshot
I accidentally hit the print screen button a lot. Turns out it can be kinda fun to browse through those accidental screenshots.

# How to use

This is intended to be used as a "run it all the time" script. You'll need a few things done to get it set up (instructions are for linux, I'm running Ubuntu):

0. install dependencies (python > 3.6 (tested using 3.10), mss ('pip install --user -U mss').
1. clone this repo
2. set up your config file however you want (be sure to make any directories you're trying to use)
3. Set up a task to run this script at startup
4. reboot, and you should be up and running!

Note that if you move the config ini file or rename it you need to update auto_ss.py so it knows where to look for it. Just don't edit outside the lines there and you'll be fine.

# running the script automatically

## Linux on unencrypted drive

Use the crontab (`crontab -e`) with the following new line: `@reboot /path/to/cloned/repo/auto_ss.py`

## Windows

### Unencrypted drive (or encrypted drive, but it's your main drive)

Using Task Scheduler (open the start menu and search for 'Task Scheduler'), create a task with an "on reboot" trigger to run `pythonw.exe` with the path to the auto_ss.py script as the command line argument. Be sure to have 'Run only when user is logged on' selected under the 'General' tab or you'll just get black screens for your shots.

The final 'action' should look like this:
![image](https://user-images.githubusercontent.com/32105556/226152789-ff444289-8899-49e6-bfe9-9737e20cf05b.png)


### Keeping data on an encrypted drive other than C:

This is how I have my windows set up (my data is on a bitlocker encrypted drive called A:). You don't have to have modify the script itself to get it to work. You can get things working with sufficient task scheduler magic.

1. Create a new task like you had an unencrypted drive, but don't add the trigger.
2. Add a trigger with the following settings:
    - Log: Microsoft-Windows-BitLocker-API/Management
    - Source: <leave blank>
    - Event ID: 782 (this is the 'drive unlocked' event ID -- you can verify this using the Event Viewer)
    - all checkboxes unticked EXCEPT 'Enabled'
  
  
![image](https://user-images.githubusercontent.com/32105556/226152751-da1dee7d-4e08-49b0-9325-8fa911bad9ca.png)


When done, you should have a task that looks roughly like this:
![image](https://user-images.githubusercontent.com/32105556/226152777-29da30ec-6dfe-4178-90c9-f0750b4ced2d.png)
