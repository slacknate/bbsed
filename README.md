# BBCF Sprite Editor

The foremost goal of the project is to streamline the process of creating custom color palettes 
for BlazBlue: Central Fiction. Manual palette creation is fairly well documented by the community, but it can 
be a tedious process that involves a lot of effort. There also exists the BBCF Improvement Mod which allows for 
in-game palette editing, but unfortunately this mod does not seem to work well for everyone.

The tool also aims to provide a means to share palettes with others so we can all view and admire each others 
creative work and appreciate it within the game easily and quickly.

Eventually I would like to include more advanced game data editing capabilities, but for now those ideas are not high 
priority and the focus is on a well designed UI/UX that allows for intuitive palette editing and sharing. Some 
features, like the animation viewer, are present so the tool has use to people other than custom palette enthusiasts.

# Slated Functionality (No ETA)

* Sprite image data editing
* Frame data editing
* Collision box editing

# Known Issues

* Some characters/sprites do not properly load
* Palette Data, Zoom, and extra character control dialog positions are not file saved, and thus reset each time 
they are hidden/shown
* If the user drag-selects a sprite in the HIP image list, there is an off-by-one error and the wrong sprite 
may be displayed under certain circumstances
* Animation dialog cannot currently show effects (it is completely unimplemented)
* Animation dialog frame data display currently does not take into account moves that can be held or hit multiple times
* Palette dialog gradient tool needs some improvements (in terms of gradient generation math)

# Shoutouts

Huge thanks to Dantarion and contributors for the repo [bbtools](https://github.com/dantarion/bbtools). 
Without it this project would not be possible. 

Another huge thanks to Labreezy for the repo [bb-collision-editor](https://github.com/Labreezy/bb-collision-editor).
It was invaluable for learning how sprite coordinate systems are calculated using the game data.

A third huge thanks to Super-continent for the repo [arcsys](https://github.com/super-continent/arcsys).
This was absolutely necessary for parsing the DFASFPAC file format, introduced in the BBCF rollback patch, which
allows BBSED to function as was originally designed; to use the data from the game files directly.
