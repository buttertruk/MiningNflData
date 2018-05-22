import math
import nfldb
from bokeh.models import Jitter
from bokeh.layouts import column
from bokeh.plotting import figure, show, output_file


def score(player):
    score = 0
    # -------------------Offense----------------- #
    # -------------------Passing----------------- #
    score += player.passing_yds / 25
    score += player.passing_tds * 6
    score += -2 * player.passing_int
    score += player.passing_twoptm * 2
    # -------------------Rushing----------------- #
    score += player.rushing_yds / 10
    score += player.rushing_tds * 6
    score += player.rushing_twoptm * 2
    # -------------------Receiving----------------- #
    score += player.receiving_yds / 10
    score += player.receiving_tds * 6
    score += player.receiving_rec * 1
    score += player.receiving_twoptm * 2
    # -------------------Misc. Offense----------------- #
    score += -2 * player.fumbles_lost
    score += player.fumbles_rec_tds * 6
    score += player.puntret_tds * 6
    # Since kickers and defenses aren't very important in fantasy
    # football, we only focused on running backs, quarterbacks,
    # receivers, and tight ends.
    return int(score)


def getAverage(items, valFunc):
    if (len(items) == 0):
        return 0
    sum = 0
    for item in items:
        sum += valFunc(item)
    return sum / len(items)


def getStandardDeviation(items, valFunc):
    if (len(items) == 0):
        return 0
    average = getAverage(items, valFunc)
    sumOfDiffsSquared = 0
    for item in items:
        sumOfDiffsSquared += math.pow(valFunc(item) - average, 2)
    return math.sqrt((1.0 / float(len(items))) * sumOfDiffsSquared)


def removeEmptyCollections(collections):
    for i in range(len(collections), 0):
        if len(collections[i]) == 0:
            collections.pop(i)

    return collections


def categorizeDown(items, numberOfCategories, valFunc):
    categories = []
    for item in items:
        categories.append([item])

    categories = sorted(categories, key=lambda item: valFunc(item[0]))

    index = 0
    while len(categories) > numberOfCategories:
        if (index < len(categories)):
            a = categories.pop(index)
            b = categories.pop(index)
            categories.insert(index, a + b)
        index = (index + 1) % (len(categories) - 1)

    return categories


def kMeans(items, numberOfCategories, maxIterations, valFunc):
    categories = []
    averages = []
    categoryStartingSize = len(items) / numberOfCategories
    for i in range(numberOfCategories):
        categories.append([])
        for o in range(categoryStartingSize):
            categories[i].append(items[i * categoryStartingSize + o])

    for iteration in range(maxIterations):
        for i in range(numberOfCategories):
            averages.append(getAverage(categories[i], valFunc))

        newCategories = []
        for i in range(numberOfCategories):
            newCategories.append([])

        for i in range(numberOfCategories):
            for o in range(len(categories[i])):
                item = categories[i][o]
                closestCat = 0
                distance = abs(valFunc(item) - averages[0])
                for u in range(1, numberOfCategories):
                    if (abs(valFunc(item) - averages[u]) < distance):
                        closestCat = u
                        distance = abs(valFunc(item) - averages[u])
                newCategories[closestCat].append(item)

        categories = newCategories
        averages = []

    return removeEmptyCollections(categories)


def kMeansVariant(items, targetStandardDeviation, iterationsPerStep, valFunc):
    for i in range(1, len(items)):
        categories = kMeans(items, i, iterationsPerStep, valFunc)
        success = True
        for cat in categories:
            if (getStandardDeviation(cat, valFunc) > targetStandardDeviation):
                success = False

        if (success):
            return categories


def analyzeAndDisplayCategories(categories, printPlayers=True):
    print
    for cat in categories:
        print('Average Score : ' + str(getAverage(cat, lambda player: player.score)) + ', Standard Deviation : ' + str(
            getStandardDeviation(cat, lambda player: player.score)) + ', Size : ' + str(len(cat)))
        if (printPlayers):
            for pp in cat:
                print(pp.player.full_name, pp.score)
        print


def get_scores(year, end_year, pos):
    scores = []
    results = []
    while (year < end_year):
        print("{}{}{}".format("*" * 10, year, "*" * 10))
        db = nfldb.connect()
        q = nfldb.Query(db)
        q.game(season_year=year, season_type='Regular').player(position=pos)
        results = q.as_aggregate()
        for pp in results:
            s = score(pp)
            pp.score = s
            if (pp.score > 10):
                scores.append([pp.player.full_name,pp.score,year])
        year += 1

    results = sorted(results, key=lambda pp: pp.score)  # Gives better K means results

    analyzeAndDisplayCategories(categorizeDown(results, 5, lambda player: player.score))

    analyzeAndDisplayCategories(kMeans(results, 5, 25, lambda player: player.score))

    analyzeAndDisplayCategories(kMeansVariant(results, 10, 50, lambda player: player.score))
    print(scores)
    return scores

score_arr = get_scores(2013,2017,'RB')

colors = ["red", "olive", "darkred", "goldenrod"]

p1 = figure(plot_width=600, plot_height=300, title="RB scoring")
p2 = figure(plot_width=600, plot_height=300, title="RB scoring with jittering")

for i in score_arr:
    y = i[1]
    color = colors[i[2] % 2013]

    p1.circle(x=i[2], y=y, color=color)
    p2.circle(x={'value': i[2], 'transform': Jitter(width=0.8)}, y=y, color=color)

output_file("jitter.html")

show(column(p1, p2))