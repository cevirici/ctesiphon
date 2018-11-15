# # --- Language ---
# #
# # - Languages, and manipulations of languages
# #
# # --- --- --- ---


from random import random, gauss, choice, randint

VOWELS = [['I', 'IY', 'UY', 'EU', 'OU'],
          ['EH', 'ER', 'UH', 'U', 'O'],
          ['E', 'EI', 'UE', 'ER'],
          ['E', 'AE', 'A', 'OH', 'OR']]

CONSONANTS = [['M', 'N'],
              ['B', 'P', 'BH', 'PH'],
              ['D', 'GT', 'KT' 'T'],
              ['G', 'Q', 'K'],
              ['TS', 'Z', 'S'],
              ['C', 'X', 'CH', 'SH'],
              ['L', 'R', 'RH'],
              ['F', 'V', 'TH', 'DH'],
              ['U', 'W', 'H']]

FORMS = ['J', 'CV', 'CVC', 'CVC', 'VC']

JOINERS = ['', '', '', '-', "'"]

MUTATION = 0.1

PRIMITIVES = ['SUN', 'MOUNTAIN', 'NORTH', 'SOUTH', 'EAST', 'WEST', 'CITY',
              'TOWN', 'PLACE', 'RIVER', 'SEA', 'OCEAN', 'HILL', 'GRASS',
              'BIG', 'SMALL', 'WAY', 'UP', 'ROYAL', 'KINGS', 'BIRD', 'FARM',
              'LONG', 'ISLAND', 'RICH', 'WATER', 'LAND', 'OF', 'ON', 'OVER',
              'DESERT', 'ICE', 'FOREST', 'PEOPLE']


def mergeWords(word_a, word_b):
    # Merge two words
    join = word_a + word_b
    if len(join) > 3:
        if random() > 1 / len(join):
            del join[randint(1, len(join) - 2)]
    return join


def printWord(word):
    return ''.join([''.join([l for l in s]) for s in word])


class Language:
    def __init__(self):
        self.wordLength = max(1, gauss(3, 1))
        self.vowels = []
        for vowelCat in VOWELS:
            for vowel in vowelCat:
                if random() > 0.6:
                    self.vowels.append(vowel)

        self.consonants = []
        for consCat in CONSONANTS:
            for cons in consCat:
                if random() > 0.6:
                    self.consonants.append(cons)

        self.formProbs = []
        n = len(FORMS)
        for i in range(n + 1):
            self.formProbs.append([])
            cumulative = 0
            for i in range(n):  # Extra line for starting block
                cumulative += random() / n
                self.formProbs[-1].append(cumulative)

        self.formProbs[0][0] = 0   # no immediate joiner
        self.formProbs[0][-1] = 1  # no immediate failure
        self.formProbs[1][0] = 0   # no joiner-joiner chains
        self.formProbs[1][-1] = 1   # no joiner-failure

        self.joiner = choice(JOINERS)
        self.letters = self.vowels + self.consonants
        self.prims = {prim: self.generateWord() for prim in PRIMITIVES}

    def __getitem__(self, item):
        if item in PRIMITIVES:
            return self.prims[item]

    def generateSyllable(self, form):
        syllable = []
        for c in form:
            if c == 'J':
                syllable.append(self.joiner)
            elif c == 'C':
                syllable.append(choice(self.consonants))
            else:
                syllable.append(choice(self.vowels))
        return syllable

    def generateWord(self):
        currentForm = 0
        word = []
        for i in range(1 + int(gauss(self.wordLength, 1))):
            seed = random()
            for i in range(len(FORMS)):
                if self.formProbs[currentForm][i] > seed:
                    currentForm = i + 1
                    word.append(self.generateSyllable(FORMS[i]))
                    break

            if seed > self.formProbs[currentForm][-1]:
                break

        return word

    def transliterate(self, word):
        newWord = []
        for syllable in word:
            newSyllable = []
            for letter in syllable:
                rows = [r for r in VOWELS + CONSONANTS if letter in r]
                if rows:
                    row = rows[0]
                else:  # It's a joiner
                    newSyllable.append(letter)
                    continue
                if letter in self.letters and random() > 0.7:
                    newSyllable.append(letter)
                    continue
                candidates = [l for l in row if l in self.letters]
                if candidates:
                    newSyllable.append(choice(candidates))
                else:
                    if row in VOWELS:
                        newSyllable.append(choice(self.vowels))
                    else:
                        newSyllable.append(choice(self.consonants))
            newWord.append(newSyllable)
        return printWord(newWord)

    def translate(self, word):
        newWord = ' '.join([printWord(self.prims[prim]).capitalize()
                            for prim in word])
        return newWord

    def mutate(self):
        newVowels = []
        newConsonants = []
        seeds = [random() / 3 for i in range(4)]
        vowelShifts = seeds[0]
        consShifts = seeds[2]

        for vowel in self.vowels:
            seed = random()
            row = [r for r in VOWELS if vowel in r][0]
            if random() < MUTATION:
                if seed < vowelShifts:
                    newVowel = row[max(row.index(vowel) - 1, 0)]
                else:
                    newVowel = row[min(row.index(vowel) + 1, len(row) - 1)]
            else:
                newVowel = vowel
            if vowel not in newVowels:
                newVowels.append(newVowel)

        for cons in self.consonants:
            seed = random()
            row = [r for r in CONSONANTS if cons in r][0]
            if random() < MUTATION:
                if seed < consShifts:
                    newCons = row[max(row.index(cons) - 1, 0)]
                else:
                    newCons = row[min(row.index(cons) + 1, len(row) - 1)]
            else:
                newCons = cons
            if cons not in newConsonants:
                newConsonants.append(newCons)

        newProbs = []
        for row in self.formProbs:
            newRow = []
            for entry in row:
                if entry not in [0, 1]:
                    newEntry = entry + MUTATION * (random() - 0.5)
                    newEntry = max(0, min(1, newEntry))
                    newRow.append(newEntry)
                else:
                    newRow.append(entry)

                newRow.sort()
            newProbs.append(newRow)
        child = Language()
        child.wordLength = self.wordLength
        child.vowels = newVowels
        child.consonants = newConsonants
        child.formProbs = newProbs
        child.joiner = self.joiner
        child.letters = newVowels + newConsonants

        for prim in self.prims:
            if random() > MUTATION:
                child.prims[prim] = child.transliterate(self.prims[prim])

        return child


def mergeLanguages(langA, langB):
    child = Language()
    child.wordLength = (random() * 0.2 + 0.9) * \
                       (langA.wordLength + langB.wordLength) / 2
    child.joiner = choice([langA.joiner, langB.joiner])
    combinedVowels = langA.vowels
    for v in langB.vowels:
        if v not in combinedVowels:
            combinedVowels.append(v)
    child.vowels = []
    for v in combinedVowels:
        if random() > MUTATION / 2:
            child.vowels.append(v)

    combinedCons = langA.consonants
    for c in langB.consonants:
        if c not in combinedCons:
            combinedCons.append(c)
    child.consonants = []
    for c in combinedCons:
        if random() > MUTATION / 2:
            child.consonants.append(c)

    child.letters = child.vowels + child.consonants
    combinedFormProbs = []
    for i in range(len(FORMS) + 1):
        combinedFormProbs.append(choice([l.formProbs[i]
                                         for l in [langA, langB]]))

    child.formProbs = combinedFormProbs
    for prim in child.prims:
        t = choice([l.prims[prim] for l in [langA, langB]])
        child.prims[prim] = child.transliterate(t)

    return child
