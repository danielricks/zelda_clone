# zelda_clone
Clear Code's Zelda tutorial code, with added xbox controller support and enemy pathfinding.

Video: https://www.youtube.com/watch?v=QU1pPzEGrqw

Original Code: https://github.com/clear-code-projects/Zelda

This project is published under the Creative Commons Zero (CC0) license (as Clear Code's was).

# Changes

I added input.py, which breaks input down from the keyboard and an xbox controller, and funnels that into one method. All instances of checking for key presses have been replaced with utilizing this method. If the xbox controller is plugged in when the game is booted up, the game will only accept controller input.

I also added pathfinding, which functions when the enemy is within notice (but not attack) distance of the player. I have left a visual indicator where the pathfinding is guiding the enemies, so that you can see how it works immediately on running.

I also fixed some minor bugs I noticed, adjusted object sizes (now you can hide behind trees), and standardized the source of many "magic" numbers.
