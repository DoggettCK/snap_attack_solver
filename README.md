# Snap Attack Solver

![Example run of solver](doc/snap_attack_solver.gif?raw=true "Example run of solver")

This should allow you to easily average around 10K per round in the Windows version of [Snap Attack](https://www.microsoft.com/en-us/store/p/snap-attack/9wzdncrfhwf6?rtc=1), by automatically scraping the board and parsing it with [Scrabulizer](https://www.scrabulizer.com/). It won't automatically play for you, but that may be coming soon.

# Installation

- Install [Python 3](https://www.python.org/downloads/) (tested with 3.6.4) for Windows, and make sure it's in your system PATH
- Clone this repo or download/extract the latest release as a zip file
  -  ![Download zip of repo](doc/install.gif?raw=true "Download zip of repo")
- Run setup.bat

This should install create a Python virtual environment and install all dependencies.

# Running solver

This has only been tested at 1920x1080 resolution with the taskbar not hidden. It works best with the Snap Attack window docked to one half of the screen or the other, but should work at any size. It's just easier that way to see the solutions on the other side of the screen.

All you need to do is wait for the game to start, make sure all letters are in the rack at the bottom, and run snap_attack_solver.bat.

# Troubleshooting

- Feel free to contact me if you have any problems running this. If Python throws some sort of exception, try resizing the window or re-docking it to the right of the desktop, and run snap_attack_solver.bat again, and that will usually solve the problem.

- ***WARNING***: Currently, this only supports single letters, and will probably detect double-letter tiles on the board and rack as a blank space. I'll probably make a debug version of the batch file to run on boards with unknown tiles you can send to me, and I can extract them into templates. However, Scrabulizer, which I'm using for the actual querying, doesn't support double-letter tiles, so this will probably have to wait until I write my own solver, which I probably won't care about once I get the final achievement for 2,500,000 cumulative points.
