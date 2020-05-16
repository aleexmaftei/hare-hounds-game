import copy
import time
from cmath import sqrt

import pygame
from scipy.spatial.distance import cityblock


# for pygame
def drawGrid(display, gameTable):
    w_gr = h_gr = 150

    houndImage = pygame.image.load('hounds.png')
    houndImage = pygame.transform.scale(houndImage, (w_gr - 10, h_gr - 10))
    hareImage = pygame.image.load('hare.png')
    hareImage = pygame.transform.scale(hareImage, (w_gr - 10, h_gr - 10))

    drt = []
    for row in range(3):
        for column in range(5):

            grid = pygame.Rect(column * (w_gr + 1), row * (h_gr + 1), w_gr, h_gr)
            drt.append(grid)
            pygame.draw.rect(display, (255, 255, 255), grid)

            if gameTable[row][column] == 'c':
                display.blit(houndImage, (column * w_gr + 5, row * h_gr + 5))
            elif gameTable[row][column] == 'i':
                display.blit(hareImage, (column * w_gr + 5, row * h_gr + 5))

    # settings corners with X where you can not move
    xImage = pygame.image.load('ics.png')
    xImage = pygame.transform.scale(xImage, (w_gr - 10, h_gr - 10))

    for [row, column] in [[0, 0], [2, 0], [0, 4], [2, 4]]:
        display.blit(xImage, (column * w_gr + 5, row * h_gr + 5))

    pygame.display.flip()
    return drt


# returns all possible moves; 8 directions
def allMoves(row, column):
    # top
    topMove = [row - 1, column]
    # top-right
    topRightMove = [row - 1, column + 1]
    # right
    rightMove = [row, column + 1]
    # bottom-right
    bottomRightMove = [row + 1, column + 1]
    # bottom
    bottomMove = [row + 1, column]
    # bottom-left
    bottomLeftMove = [row + 1, column - 1]
    # left
    leftMove = [row, column - 1]
    # top-left
    topLeftMove = [row - 1, column - 1]

    return [topMove, topRightMove, rightMove, bottomRightMove, bottomMove, bottomLeftMove, leftMove, topLeftMove]


# if given positions are within the bounds of the game board
def withinBounds(positionX, positionY):
    if 0 <= positionX < 3 and 0 <= positionY < 5:
        return True
    return False


class Game:
    # player symbols
    playerSymbols = ['c', 'i']

    # the game table
    gameTable = [[' ', 1, 4, 7, ' '],
                 [0, 2, 5, 8, 10],
                 [' ', 3, 6, 9, ' ']]

    # the empty space on the matrix
    gameGoal = '*'

    impossibleMoves = [[0, 0], [2, 0], [0, 4], [2, 4]]  # the edges from the matrix where is an empty space

    # can not move (from) -> (to) because those positions are not connected between them
    # I did not exclude the ones that are the same as in hare movement because the hounds can not go backwards
    houndsInvalidMoves = [[(1, 1), (0, 2)],
                          [(1, 1), (2, 2)],
                          [(0, 2), (1, 3)],
                          [(2, 2), (1, 3)]]

    # the hare can move in any direction so I exclude every direction possible of invalid movements
    hareInvalidMovements = houndsInvalidMoves + [[(0, 2), (1, 1)],
                                                 [(2, 2), (1, 1)],
                                                 [(1, 3), (0, 2)],
                                                 [(1, 3), (2, 2)]]
    JMIN = None
    JMAX = None

    def __init__(self, table, houndsVerticalMoves):
        self.table = table  # current table during the game
        self.houndsVerticalMoves = houndsVerticalMoves

    # finding the position of a hare on the table
    # symbol is a string of 'c' or 'i'
    def findSymbolPosition(self, symbol):
        for i in range(3):
            for j in range(5):
                if self.table[i][j] == symbol:
                    return i, j
        return -1, -1

    def getPositionFromGameTable(self, position):
        for i in range(3):
            for j in range(5):
                if self.gameTable[i][j] == position:
                    return i, j
        return -1, -1

    # given coordinates where to go, check if from the current position, you can reach the given destination
    # function used for checking the user's input
    def checkIfYouCanGo(self, currentPlayer, rowDestinationToReach, columnDestinationToReach,
                        rowHoundFrom=None,
                        columnHoundFrom=None):  # used when a hound moves so whe know which one to move
        if currentPlayer == 'i':
            rowFrom, colFrom = self.findSymbolPosition('i')
            # if the move from the current position to the destination (from input) is reachable
            if self.legalMove(currentPlayer, rowFrom, colFrom, rowDestinationToReach, columnDestinationToReach):
                return True
        else:
            # if the move from the current position to the destination (from input) is reachable
            if self.legalMove(currentPlayer, rowHoundFrom, columnHoundFrom, rowDestinationToReach,
                              columnDestinationToReach):
                return True

        return False

    # function to check if the current player movement is valid from their current position to given coordinates
    def legalMove(self, currentPlayer, rowFrom, colFrom, rowTo, colTo):
        # to check how far apart is the current position from the position to go
        rowDiff = abs(rowFrom - rowTo)
        colDiff = abs(colFrom - colTo)

        # if the position is greater than 1, then it is an invalid position to go
        if rowDiff > 1 or colDiff > 1:
            return False

        if not withinBounds(rowTo, colTo):
            return False

        if currentPlayer == 'c':
            if colTo - colFrom < 0:  # hounds can not move behind their current position
                return False
            # if they can move with a valid movement and the position is not occupied already
            if self.table[rowTo][colTo] == self.gameGoal:
                if [rowTo, colTo] not in self.impossibleMoves:
                    for invalidMovement in self.houndsInvalidMoves:
                        if [(rowFrom, colFrom), (rowTo, colTo)] == invalidMovement:
                            return False

        # the hare can move in any direction without any restriction of their current position and the next position
        if currentPlayer == 'i':
            # if they can move with a valid movement and the position is not occupied already
            if self.table[rowTo][colTo] == self.gameGoal:
                if [rowTo, colTo] not in self.impossibleMoves:
                    for invalidMovement in self.hareInvalidMovements:
                        if [(rowFrom, colFrom), (rowTo, colTo)] == invalidMovement:
                            return False

        return True

    # function to generate the next moves from the current position of the current player
    def generateNextMoves(self, currentPlayer):
        movesList = []

        if currentPlayer == 'i':  # hare
            rowFrom, colFrom = self.findSymbolPosition(currentPlayer)
            if rowFrom != -1 and colFrom != -1:
                hareMoves = allMoves(rowFrom, colFrom)  # hare movements are almost in every direction
                for [rowTo, colTo] in hareMoves:
                    if withinBounds(rowTo, colTo) and self.table[rowTo][colTo] == Game.gameGoal:
                        if self.legalMove(currentPlayer, rowFrom, colFrom, rowTo, colTo):
                            # creating a new table game with current settings
                            newTableGame = copy.deepcopy(self.table)
                            # setting current position to empty space
                            newTableGame[rowFrom][colFrom] = self.gameGoal
                            # moving the position of the player
                            newTableGame[rowTo][colTo] = currentPlayer
                            movesList.append(Game(newTableGame, self.houndsVerticalMoves))

        if currentPlayer == 'c':
            for i in range(3):  # finding the positions of the all hounds
                for j in range(5):
                    if self.table[i][j] == 'c':
                        rowFrom, colFrom = i, j
                        houndMoves = allMoves(rowFrom, colFrom)
                        for [rowTo, colTo] in houndMoves:
                            if withinBounds(rowTo, colTo) and self.table[rowTo][colTo] == Game.gameGoal:
                                if self.legalMove(currentPlayer, rowFrom, colFrom, rowTo, colTo):
                                    # creating a new table game with current settings
                                    newTableGame = copy.deepcopy(self.table)
                                    # setting current position to empty space
                                    newTableGame[rowFrom][colFrom] = self.gameGoal
                                    # moving the position of the player
                                    newTableGame[rowTo][colTo] = currentPlayer
                                    # if they move vertically all the time
                                    if colFrom == colTo:
                                        movesList.append(Game(newTableGame, self.houndsVerticalMoves + 1))
                                    else:
                                        movesList.append(Game(newTableGame, 0))

        return movesList

    def finalGame(self):
        if self.houndsVerticalMoves >= 10:
            return 'i'

        rowFrom, colFrom = self.findSymbolPosition('i')
        # if all hounds are after the hare, then the hare wins
        houndsNumber = 0
        if rowFrom != -1 and colFrom != -1:
            for i in range(3):
                for j in range(5):
                    if self.table[i][j] == 'c' and j > colFrom:
                        houndsNumber += 1

        if houndsNumber == 3:
            return 'i'

        # find if the hare is surrounded by hounds, then the hounds can still win
        ok = 0
        directions = allMoves(rowFrom, colFrom)
        if rowFrom != -1 and colFrom != -1:
            for [rowTo, colTo] in directions:
                if withinBounds(rowTo, colTo):
                    # find if there is a valid move to a empty place to move for hare so it is not game over for her
                    if self.table[rowTo][colTo] == self.gameGoal:
                        if self.legalMove('i', rowFrom, colFrom, rowTo, colTo):
                            ok = 1
                            break
        if ok == 0:
            return 'c'

        return False  # the game is not finished yet

    # score estimation using euclidean distance
    # it is used for a easier game
    def scoreCalculation2(self, currentPlayer):
        rowFromHare, colFromHare = self.findSymbolPosition('i')

        houndsPositions = []
        for i in range(3):
            for j in range(5):
                if self.table[i][j] == 'c':
                    houndsPositions.append([i, j])

        # euclidean distance
        distanceHound1 = (
            sqrt((houndsPositions[0][0] - rowFromHare) ** 2 + (houndsPositions[0][1] - colFromHare) ** 2)).real
        distanceHound2 = (
            sqrt((houndsPositions[1][0] - rowFromHare) ** 2 + (houndsPositions[1][1] - colFromHare) ** 2)).real
        distanceHound3 = (
            sqrt((houndsPositions[2][0] - rowFromHare) ** 2 + (houndsPositions[2][1] - colFromHare) ** 2)).real

        if currentPlayer == 'i':
            score = 0
            if colFromHare > houndsPositions[0][1]:
                score += distanceHound1 - 1  # points for being away from hounds
            elif colFromHare == houndsPositions[0][1]:
                score += distanceHound1
            else:
                score += 5  # bonus points if he passes a hound

            if colFromHare > houndsPositions[1][1]:
                score += distanceHound2 - 1
            elif colFromHare == houndsPositions[1][1]:
                score += distanceHound2
            else:
                score += 5  # bonus points if he passes a hound

            if colFromHare > houndsPositions[2][1]:
                score += distanceHound3 - 1
            elif colFromHare == houndsPositions[2][1]:
                score += distanceHound3
            else:
                score += 5  # bonus points if he passes a hound
        else:
            # calculating the mean distance between the hounds and the hare
            score = (distanceHound1 + distanceHound2 + distanceHound3) / 3
        return score

    # score estimation using manhattan distance
    # it is used for a harder game
    def scoreCalculation(self, currentPlayer):
        rowFromHare, colFromHare = self.findSymbolPosition('i')
        harePosition = [[rowFromHare, colFromHare]]
        houndsPositions = []
        for i in range(3):
            for j in range(5):
                if self.table[i][j] == 'c':
                    houndsPositions.append([i, j])

        # manhattan distance (a bit better because it is a grid style)
        distanceHound1 = cityblock(houndsPositions[0], harePosition[0])
        distanceHound2 = cityblock(houndsPositions[1], harePosition[0])
        distanceHound3 = cityblock(houndsPositions[2], harePosition[0])

        if currentPlayer == 'i':
            score = 0
            if colFromHare > houndsPositions[0][1]:
                score += distanceHound1 - 1
            elif colFromHare == houndsPositions[0][1]:
                score += distanceHound1
            else:
                score += 5  # bonus points if he passes a hound

            if colFromHare > houndsPositions[1][1]:
                score += distanceHound2 - 1
            elif colFromHare == houndsPositions[1][1]:
                score += distanceHound2
            else:
                score += 5  # bonus points if he passes a hound

            if colFromHare > houndsPositions[2][1]:
                score += distanceHound3 - 1
            elif colFromHare == houndsPositions[2][1]:
                score += distanceHound3
            else:
                score += 5  # bonus points if he passes a hound
        else:
            score = (distanceHound1 + distanceHound2 + distanceHound3) / 3
            # how far apart are the hounds
            distanceHound12 = cityblock(houndsPositions[0], houndsPositions[1])
            distanceHound13 = cityblock(houndsPositions[0], houndsPositions[2])
            distanceHound23 = cityblock(houndsPositions[1], houndsPositions[2])

            # grouping them together => dropping useless states that can lose the game
            score -= distanceHound12 + distanceHound13 + distanceHound23
        return score

    # a harder game (7-10 difficulty)
    def heuristicCalculation(self):
        return self.scoreCalculation(self.JMAX) - self.scoreCalculation(self.JMIN)

    # a bit easier game (1-6 difficulty)
    def heuristicCalculation2(self):
        return self.scoreCalculation2(self.JMAX) - self.scoreCalculation2(self.JMIN)

    def scoreEstimation(self, depth, difficulty):
        t_final = self.finalGame()
        if t_final == self.JMAX:
            return 999 + depth
        elif t_final == self.JMIN:
            return -999 - depth
        else:
            if 1 <= difficulty <= 6:
                return self.heuristicCalculation2()
            else:
                return self.heuristicCalculation()


# Solve class is not changing during the game
class Solve:
    maxDepth = None

    # Solve constructor
    def __init__(self, gameTable, currentGame, depth, score=None):
        self.gameTable = gameTable  # Game type
        self.currentGame = currentGame  # current player game
        self.currentDepth = depth
        self.currentScore = score
        self.listOfPossibleMovesOfCurrentGame = []
        self.chosenMove = None

    def __str__(self):
        return str(self.gameTable) + "(Current game: " + self.currentGame + ")\n"

    # function to change the current player
    def changePlayer(self):
        if self.currentGame == Game.JMIN:
            return Game.JMAX
        else:
            return Game.JMIN

    def startMoving(self):
        # Generate the moves for the current game
        movesOfCurrentGame = self.gameTable.generateNextMoves(self.currentGame)
        otherPlayer = self.changePlayer()  # change the current player
        # generate the list of moves for the changed player
        listOfMoves = [Solve(oneMove, otherPlayer, self.currentDepth - 1) for oneMove in movesOfCurrentGame]

        return listOfMoves


def printFinalOfGame(currentState):  # currentState -> Solve Type
    winner = currentState.gameTable.finalGame()
    if winner:
        print("Winner is: " + winner)
        print("Score of player: " + str(currentState.gameTable.scoreCalculation(Game.JMIN)))
        print("Score of computer: " + str(currentState.gameTable.scoreCalculation(Game.JMAX)))
        return True
    return False


# min_max function algorithm
# difficulty = the difficulty of the game
def min_max(currentState, difficulty):  # stare -> Solve type
    if currentState.currentDepth == 0 or currentState.gameTable.finalGame():
        currentState.currentScore = currentState.gameTable.scoreEstimation(currentState.currentDepth, difficulty)
        return currentState

    currentState.listOfPossibleMovesOfCurrentGame = currentState.startMoving()

    scoreAfterMoving = [min_max(oneMove, difficulty) for oneMove in currentState.listOfPossibleMovesOfCurrentGame]

    if currentState.currentGame == Game.JMAX:
        currentState.chosenMove = max(scoreAfterMoving, key=lambda x: x.currentScore)
    else:
        currentState.chosenMove = min(scoreAfterMoving, key=lambda x: x.currentScore)

    currentState.currentScore = currentState.chosenMove.currentScore

    return currentState


# alpha beta function algorithm
def alpha_beta(alpha, beta, currentState, difficulty):
    if currentState.currentDepth == 0 or currentState.gameTable.finalGame():
        currentState.currentScore = currentState.gameTable.scoreEstimation(currentState.currentDepth, difficulty)
        return currentState

    if alpha > beta:
        return currentState

    currentState.listOfPossibleMovesOfCurrentGame = currentState.startMoving()

    if currentState.currentGame == Game.JMAX:
        currentScore = float('-inf')

        for oneMove in currentState.listOfPossibleMovesOfCurrentGame:
            newState = alpha_beta(alpha, beta, oneMove, difficulty)

            if currentScore < newState.currentScore:
                currentState.chosenMove = newState
                currentScore = newState.currentScore

            if alpha < newState.currentScore:
                alpha = newState.currentScore
                if alpha >= beta:
                    break

    elif currentState.currentGame == Game.JMIN:
        currentScore = float('inf')

        for oneMove in currentState.listOfPossibleMovesOfCurrentGame:
            newState = alpha_beta(alpha, beta, oneMove, difficulty)

            if currentScore > newState.currentScore:
                currentState.chosenMove = newState
                currentScore = newState.currentScore

            if beta > newState.currentScore:
                beta = newState.currentScore
                if alpha >= beta:
                    break

    currentState.currentScore = currentState.chosenMove.currentScore

    return currentState


# function to exit anytime by typing "exit"
def exitFunction(currentState):
    print("You have exited the game! Final configuration of the game:")
    for i in range(3):
        for j in range(5):
            print(currentState.gameTable.table[i][j], end=' ')
        print(end='\n')
    runTimeAfterExit = int(round(time.time() * 1000))
    print("\n\nTime passed while playing the game: " + str(runTimeAfterExit - runTimeBefore) + " ms.")
    exit(5)


# function to start the min-max algorithm
def startPlayingConsole(currentState, algorithm, difficulty):
    # to avoid warnings
    rowDestination = -1
    columnDestination = -1
    rowHoundFrom = -1
    colHoundFrom = -1

    playerMoves = 0
    computerMoves = 0
    while True:
        print("Current player: " + currentState.currentGame)
        # player's turn
        if currentState.currentGame == Game.JMIN:

            playerMoves += 1
            print("Choose a position to move accordingly to this: ")
            for i in range(3):
                for j in range(5):
                    print(Game.gameTable[i][j], end=' ')
                print(end='\n')

            if Game.JMIN == 'i':  # hare move
                positionFound = False
                while not positionFound:
                    try:
                        positionToMoveTo = input("hare - position to move to = ")
                        if positionToMoveTo == "exit":
                            print("Player total moves: " + str(playerMoves))
                            print("Computer total moves: " + str(computerMoves))
                            exitFunction(currentState)
                        else:
                            positionToMoveTo = int(positionToMoveTo)

                        if positionToMoveTo in range(11):
                            rowDestination, columnDestination = currentState.gameTable.getPositionFromGameTable(
                                positionToMoveTo)  # finding the position (x, y) on the table
                            print("\n")
                            # check if the chosen position is valid
                            if currentState.gameTable.checkIfYouCanGo(Game.JMIN, rowDestination,
                                                                      columnDestination) is True and \
                                    currentState.gameTable.table[rowDestination][columnDestination] == Game.gameGoal:
                                positionFound = True
                                break
                            else:
                                print("You can not reach this position!")
                        else:
                            print(
                                "Please, choose between 0 - 10 accordingly to the table position presented or type exit!")

                    except ValueError:
                        print("Insert a positive integer!")

            else:  # hounds move
                positionFound = False
                while not positionFound:
                    try:
                        positionOfChosenHound = input("Choose the position of the hound to move =")
                        positionToMoveTo = input("hound - position to move to  = ")
                        if positionOfChosenHound == "exit" or positionToMoveTo == "exit":
                            print("Player total moves: " + str(playerMoves))
                            print("Computer total moves: " + str(computerMoves))
                            exitFunction(currentState)
                        else:
                            positionOfChosenHound = int(positionOfChosenHound)
                            positionToMoveTo = int(positionToMoveTo)

                        if (positionToMoveTo and positionOfChosenHound) in range(11):
                            rowDestination, columnDestination = currentState.gameTable.getPositionFromGameTable(
                                positionToMoveTo)

                            rowHoundFrom, colHoundFrom = currentState.gameTable.getPositionFromGameTable(
                                positionOfChosenHound)

                            if currentState.gameTable.table[rowHoundFrom][colHoundFrom] == 'c':
                                if currentState.gameTable.checkIfYouCanGo(Game.JMIN, rowDestination, columnDestination,
                                                                          rowHoundFrom, colHoundFrom) is True and \
                                        currentState.gameTable.table[rowDestination][
                                            columnDestination] == Game.gameGoal:
                                    positionFound = True
                                    break
                                else:
                                    print("You can not reach this position!")
                            else:
                                print("You do not have a player on this position!")
                        else:
                            print(
                                "Please, choose between 0 - 10 accordingly to the table position presented or type exit!")

                    except ValueError:
                        print("Insert a positive integer!")

            # Place the chosen position on the table
            if Game.JMIN == 'c':
                currentState.gameTable.table[rowDestination][columnDestination] = Game.JMIN
                currentState.gameTable.table[rowHoundFrom][colHoundFrom] = Game.gameGoal

                # count how many times the hound moved vertically
                if columnDestination == colHoundFrom:
                    currentState.gameTable.houndsVerticalMoves += 1
                else:
                    currentState.gameTable.houndsVerticalMoves = 0
            else:
                for i in range(3):
                    for j in range(5):
                        if currentState.gameTable.table[i][j] == 'i':
                            currentState.gameTable.table[i][j] = Game.gameGoal
                            break
                currentState.gameTable.table[rowDestination][columnDestination] = Game.JMIN

            # Table after the player's move
            print("\nTable after the player's move: ")
            for i in range(3):
                for j in range(5):
                    print(currentState.gameTable.table[i][j], end=' ')
                print(end='\n')

            # check if it is the final game
            if printFinalOfGame(currentState):
                print("Player total moves: " + str(playerMoves))
                print("Computer total moves: " + str(computerMoves))
                break

            # change the player
            currentState.currentGame = currentState.changePlayer()

        else:  # computer's turn (JMAX)
            # start timer
            computerMoves += 1
            timerBeforeStart = int(round(time.time() * 1000))

            if algorithm == '1':
                stare_actualizata = min_max(currentState, difficulty)
            elif algorithm == '2':
                stare_actualizata = alpha_beta(-5000, 5000, currentState, difficulty)

            currentState.gameTable = stare_actualizata.chosenMove.gameTable

            print("The table after the computer's move")
            for i in range(3):
                for j in range(5):
                    print(currentState.gameTable.table[i][j], end=' ')
                print(end='\n')

            # timer after the algorithm finishes the execution for this current state of the game
            timeAfterStart = int(round(time.time() * 1000))
            print("Time passed while calculating: " + str(timeAfterStart - timerBeforeStart) + " ms.")

            # if it is the final state of the game, print the state, the winner and stop the game
            if printFinalOfGame(currentState):
                print("Player total moves: " + str(playerMoves))
                print("Computer total moves: " + str(computerMoves))
                break

            # change player
            currentState.currentGame = currentState.changePlayer()


def startPlayingPyGame(currentState, algorithm, currentTable, difficulty):
    # to avoid warnings
    rowDestination = -1
    columnDestination = -1
    rowHoundFrom = -1
    columnHoundFrom = -1

    playerMoves = 0
    computerMoves = 0

    # start pygame
    pygame.init()
    pygame.display.set_caption('Hounds and hare')
    display = pygame.display.set_mode((750, 450))

    gamePrint = drawGrid(display, currentTable.table)

    houndSelected = False
    turnDone = False  # current player's turn done
    prompter = False  # one time console print

    while True:
        # player's turn
        if currentState.currentGame == Game.JMIN:

            if Game.JMIN == 'i' and not prompter:
                prompter = True
                print("Player's turn.")
                print("Click on a position to move the hare.")
            elif Game.JMIN == 'c' and not prompter:
                prompter = True
                print("Player's turn.")
                print("Click on a hound and then a position to move the hound.")

            for event in pygame.event.get():
                # closing the game
                if event.type == pygame.QUIT:
                    print("Player total moves: " + str(playerMoves))
                    print("Computer total moves: " + str(computerMoves))

                    print("Score of player: " + str(currentState.gameTable.scoreCalculation(Game.JMIN)))
                    print("Score of computer: " + str(currentState.gameTable.scoreCalculation(Game.JMAX)))

                    runTimeAfter = int(round(time.time() * 1000))
                    print("\n\nTime passed while playing the game: " + str(runTimeAfter - runTimeBefore) + " ms.")

                    pygame.quit()
                    exit(5)

                if Game.JMIN == 'i':  # hare move
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        clickedPosition = pygame.mouse.get_pos()

                        for i in range(len(gamePrint)):
                            if gamePrint[i].collidepoint(clickedPosition):
                                rowDestination = i // 5
                                columnDestination = i % 5
                                if currentState.gameTable.checkIfYouCanGo(Game.JMIN, rowDestination,
                                                                          columnDestination) and \
                                        currentState.gameTable.table[rowDestination][
                                            columnDestination] == Game.gameGoal:
                                    turnDone = True
                                    break
                                else:
                                    print("You can not reach this position!")

                else:  # hounds move
                    # check if a hound is selected
                    if event.type == pygame.MOUSEBUTTONDOWN and not houndSelected:
                        clickedPosition = pygame.mouse.get_pos()

                        for i in range(len(gamePrint)):
                            if gamePrint[i].collidepoint(clickedPosition):
                                rowHoundFrom = i // 5
                                columnHoundFrom = i % 5
                                if currentState.gameTable.table[rowHoundFrom][columnHoundFrom] == 'c':
                                    houndSelected = True
                                    break
                                else:
                                    print("Choose a hound!")

                    # check hound valid movement
                    elif event.type == pygame.MOUSEBUTTONDOWN and houndSelected:
                        clickedPosition = pygame.mouse.get_pos()

                        for i in range(len(gamePrint)):
                            if gamePrint[i].collidepoint(clickedPosition):
                                rowDestination = i // 5
                                columnDestination = i % 5
                                if currentState.gameTable.checkIfYouCanGo(Game.JMIN, rowDestination, columnDestination,
                                                                          rowHoundFrom, columnHoundFrom) and \
                                        currentState.gameTable.table[rowDestination][
                                            columnDestination] == Game.gameGoal:
                                    turnDone = True
                                    break
                                else:
                                    print("You can not reach this position!")

                # Place the chosen position on the table
                if turnDone:
                    playerMoves += 1

                    if Game.JMIN == 'c':
                        currentState.gameTable.table[rowDestination][columnDestination] = Game.JMIN
                        currentState.gameTable.table[rowHoundFrom][columnHoundFrom] = Game.gameGoal

                        # count how many times the hound moved vertically
                        if columnDestination == columnHoundFrom:
                            currentState.gameTable.houndsVerticalMoves += 1
                        else:
                            currentState.gameTable.houndsVerticalMoves = 0
                    else:
                        for i in range(3):
                            for j in range(5):
                                if currentState.gameTable.table[i][j] == 'i':
                                    currentState.gameTable.table[i][j] = Game.gameGoal
                                    break
                        currentState.gameTable.table[rowDestination][columnDestination] = Game.JMIN

                    gamePrint = drawGrid(display, currentState.gameTable.table)

                    # Table after the player's move
                    print("\nTable after the player's move: ")
                    for i in range(3):
                        for j in range(5):
                            print(currentState.gameTable.table[i][j], end=' ')
                        print(end='\n')

                    # check if it is the final game
                    if printFinalOfGame(currentState):
                        print("Player total moves: " + str(playerMoves))
                        print("Computer total moves: " + str(computerMoves))

                        print("Score of player: " + str(currentState.gameTable.scoreCalculation(Game.JMIN)))
                        print("Score of computer: " + str(currentState.gameTable.scoreCalculation(Game.JMAX)))

                        runTimeAfter = int(round(time.time() * 1000))
                        print("\n\nTime passed while playing the game: " + str(runTimeAfter - runTimeBefore) + " ms.")

                        pygame.quit()
                        exit(5)

                    # change the player
                    currentState.currentGame = currentState.changePlayer()

        else:  # computer's turn (JMAX)

            print("Computer's turn")
            computerMoves += 1

            # start timer
            timerBeforeStart = int(round(time.time() * 1000))

            if algorithm == '1':
                stare_actualizata = min_max(currentState, difficulty)
            elif algorithm == '2':
                stare_actualizata = alpha_beta(-5000, 5000, currentState, difficulty)

            currentState.gameTable = stare_actualizata.chosenMove.gameTable

            gamePrint = drawGrid(display, currentState.gameTable.table)

            # timer after the algorithm finishes the execution for this current state of the game
            timeAfterStart = int(round(time.time() * 1000))
            print("Time passed while calculating: " + str(timeAfterStart - timerBeforeStart) + " ms.")

            # Table after the computer's move
            print("\nTable after the computer's move: ")
            for i in range(3):
                for j in range(5):
                    print(currentState.gameTable.table[i][j], end=' ')
                print(end='\n')

            # if it is the final state of the game, print the state, the winner and stop the game
            if printFinalOfGame(currentState):
                print("Player total moves: " + str(playerMoves))
                print("Computer total moves: " + str(computerMoves))

                print("Score of player: " + str(currentState.gameTable.scoreCalculation(Game.JMIN)))
                print("Score of computer: " + str(currentState.gameTable.scoreCalculation(Game.JMAX)))

                runTimeAfter = int(round(time.time() * 1000))
                print("\n\nTime passed while playing the game: " + str(runTimeAfter - runTimeBefore) + " ms.")

                pygame.quit()
                exit(5)

            # change player
            currentState.currentGame = currentState.changePlayer()

            # after the computer's turn, reset values
            houndSelected = False
            turnDone = False
            prompter = False


# function to initialise the algorithm
def chooseAlgorithmRead():
    chosenAlgorithm = False
    while not chosenAlgorithm:
        algorithm = input("Which algorithm do you want to use? (choose 1 or 2)\n 1.Minimax\n 2.Alpha-beta\n ")
        if algorithm in ['1', '2']:
            return algorithm
        else:
            print("Choose 0 or 1 please.")
    return chosenAlgorithm


# function to set the max depth
def chooseMaxDepthRead():
    chosenDepth = False
    while not chosenDepth:
        n = input("Max depth of the tree: ")
        if n.isdigit():
            return int(n)
        else:
            print("Choose a positive integer.")


def choosePlayerRead():
    [s1, s2] = Game.playerSymbols.copy()
    selected = False
    while not selected:
        Game.JMIN = str(input("Play as a {} or as a {}? ".format(s1, s2))).lower()
        if Game.JMIN in Game.playerSymbols:
            selected = True
        else:
            print("Choose between {} or {}.".format(s1, s2))
    Game.JMAX = s1 if Game.JMIN == s2 else s2


def main():
    print("Do you want to play from console or pygame? (0 - console, 1 - pygame): ")
    chosenConsole = False
    console = None
    while not chosenConsole:
        n = input()
        if n.isdigit():
            console = int(n)
            chosenConsole = True
        else:
            print("1 or 0 please")

    print("Choose the difficulty of the game (1 - 10): ")
    chosenDifficulty = False
    difficulty = None
    while not chosenDifficulty:
        n = input()
        if n.isdigit() and 1 <= int(n) <= 10:
            difficulty = int(n)
            chosenDifficulty = True
        else:
            print("Between 1 - 10")

    algorithm = chooseAlgorithmRead()  # read what algorithm to use

    maxDepth = chooseMaxDepthRead()  # read the difficulty of the game
    Solve.maxDepth = maxDepth

    choosePlayerRead()  # read the player (JMIN)

    table = [[' ', 'c', '*', '*', ' '],
             ['c', '*', '*', '*', 'i'],
             [' ', 'c', '*', '*', ' ']]
    currentTable = Game(table, 0)

    print("Initial game table: ")
    for i in range(3):
        for j in range(5):
            print(table[i][j], end=' ')
        print(end='\n')

    # start the game -> hounds moves first
    currentState = Solve(currentTable, Game.playerSymbols[0], Solve.maxDepth)
    if console == 0:
        startPlayingConsole(currentState, algorithm, difficulty)
    else:
        startPlayingPyGame(currentState, algorithm, currentTable, difficulty)


if __name__ == "__main__":
    runTimeBefore = int(round(time.time() * 1000))
    main()
    runTimeAfter = int(round(time.time() * 1000))
    print("\n\nTime passed while playing the game: " + str(runTimeAfter - runTimeBefore) + " ms.")
