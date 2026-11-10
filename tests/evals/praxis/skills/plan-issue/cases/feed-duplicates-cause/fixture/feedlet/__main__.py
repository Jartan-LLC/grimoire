from feedlet.reader import newest

for post in newest(open("feeds.txt").read().split()):
    print(post["title"])
