# Tower of Arkady

## Tower of Arkady is a game that was developed as a group project at the University of Maine.


### SECTION 1. INTRODUCTION

Tower of Arkady is a top-down puzzle game with a focus on speed. The player arrives at the tower and learns of a hostage on the top floor in need of rescue. The game becomes progressively more difficult as the player travels from one floor to another, moving through mazes, extinguishing fires and dodging bullets before diffusing a bomb to rescue the hostage. 
This game is for entertainment purposes only and is specifically designed for the Game Expo on December 11. We expect the audience to consist primarily of college-aged students with a small amount of time available to play the game. As such, Tower of Arkady was designed to be short, challenging and enjoyable. 


### SECTION 2. OVERVIEW OF THE GAME

The game begins as the player arrives at the Tower of Arkady and learns of a hostage in need of rescue. Before entering the tower, the player is briefed on game movement and objectives, and a list displays high scores. The timer will begin counting down when the player enters the tower. 
Tower of Arkady is a graphics game with dramatic music and varying sound effects as the player moves through the game and interacts with objects. A pause feature is excluded from the game as a deliberate design chose so players must move quickly through the game to earn a spot in the high scores. As an added incentive to avoid game hazards, including fire and bullets, additional time will be removed from the game clock each time the player collides with a game hazard. Additionally, time will be removed to the game clock each time an incorrect wire is cut while diffusing the bomb. The game ends, and the timer stops, only when the player diffuses the bomb at the top of the tower. High scores are earned by players who complete the game with the largest amount of time left on the play clock. 


### SECTION 3. THE USER INTERFACE

The game space is 640 x 480 pixels with a 15 x 10 grid of 32 x 32 pixels tiles. While the objects will change from floor to floor, each floor will have an identical frame with solid wall to the left and right as well as a single door on both the top and bottom of the screen. Six screens will be used to represent the each floor of the building. Depending on the floor, other objects, including fire, broken floor tiles and desks, will populate the tile grid. Movement across the grid is tile based and is smooth in appearance, not instantaneous, and objects will never be on more than one tile at a time. 
 
Empty room. Each room will contain objects such as desks, fire, darkness or a bomb-strapped hostage.
Players will use either the W, A, S and D keys or the arrow keys for player movement, and will use the spacebar and enter key to interact with objects. The mouse will not be utilized in the game.
The game will have dramatic, non-distracting music. Two separate beeps will sound periodically, one sound every minute and a separate sound every five minutes. Sound will play each time an item is picked up, an obstacle is pushed and when a fire is put out.


### SECTION 4. ARCHITECTURE OF THE GAME

Tower of Arkady is structured for modular development, using separate python files for each major class, including main, character, gameplay area, interactive objects and moving objects. This decision was informed in part by a desire to make the game's code neatly legible. Additionally, the format of team development, as well as the format of development, i.e., pressures of the project team environment, and to facilitate the proper division of labor between the primary encoder, Nic, and secondary encoders, Scott and David.
High scores will be tracked in a sqlite3 database where they will be updated, stored and called upon by relevant events within the game. Since the database will be a locally stored file, all high-scores will be specific to the machine the game was played on. This seems perfectly suited to the anticipated format of the Game Expo at the end of the semester.
Visual elements will be pulled and animated from sprite sheets, as this seemed to be the most efficient and widely documented method of handling two-dimensional graphics that our team is aware of. Audio elements will be stored as individual files, most probably of .wav type, and played in response to certain actions within the game, such as walking, pushing an obstacle or extinguishing a fire. Audio and visual elements, where possible, will be pulled from existing free-to-use galleries in order to minimize the overhead involved with asset generation. We hope to have unique sprites for the player character, basic obstacles and level-backgrounds.
At present we have no intention of using sound generators, but plan to investigate the possibility in the coming days. In particular, a sound generator may be useful for making an in-house klaxon or alarm that sounds, which will be necessary to provide the wanted degree of urgency to the game's ambience.
Level maps will be handled through an available Python utility called PyMap that allows us to very simply drag and drop tiles from a tile set onto a grid, and output a text-based document that our game code will be able to parse into visual and logical information.
Tying everything together will be the main file that imports all other files and runs them in the order necessary to have a game.
