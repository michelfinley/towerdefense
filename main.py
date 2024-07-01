from data.game import Game

if __name__ == "__main__":
    game = Game()
    game.loop()
else:
    print("This game is not intended to be imported as a library.\nTo run this game, please run main.py")
