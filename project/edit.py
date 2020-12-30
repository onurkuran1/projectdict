class wordEdit:

    def title(self,definition):
        definition=definition.split(",")
        title=definition[0]
        title=title.split(":")
        title=title[1]
        title= title.strip('"')
        return title

    def means(self,definition):

        list = []
        definition=definition.split(",")
        firstMean = definition[1]
        firstMean=firstMean.split(":")
        firstMean=firstMean[1]
        firstMean=firstMean.split('"')
        firstMean=firstMean[1]
        list.append(firstMean)
        otherMean=definition[2:-1]
        for i in otherMean:
            otherMean = i.strip('"')
            list.append(otherMean)
        lastMean=definition[-1]
        lastMean=lastMean.split('"')
        lastMean=lastMean[1]
        list.append(lastMean)
        return list

