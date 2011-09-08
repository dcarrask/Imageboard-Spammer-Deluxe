# Spiders a Kusaba board and returns a string with each post separated by a newline.
# Has options to return posts only with certain substrings, and to give a detailed and human-readable post listing. Do not use these for corpus-gathering.
# Also has an option to save all images seen to a folder. Can be useful in conjunction with the post corpus.

import urllib2, re, sys, string, random
import lxml.html

def spider(chan, boards, pages=3, detailed=False, search=None, namesearch=None, image_folder=""):
    """Default simpy saves all post content. Detailed mode adds board, name, trip, post number, and link.
    'search' expects a list of search words. 'namesearch' expects a name to search for. Set 'image_folder'
    to save all images seen on the chan to that folder.

    All name searches and word searches are case insensitive."""
    aggregation=""
    boardposts=""
    opener=urllib2.build_opener()
    opener.addheaders = [('User-agent', 'Mozilla/5.0 (Windows NT 5.1; rv:5.0.1) Gecko/20100101 Firefox/5.0.1'),
                         ('Referer', chan)]
    urllib2.install_opener(opener)

    for board in boards.split():
        pages_spidered=0
        boardpath=chan+board+"/"
        while pages_spidered < pages:
            if pages_spidered > 0:
                url=boardpath+"%s.html" % pages_spidered
            else:
                url=boardpath #page 0 has no page number
            try:
                index=urllib2.urlopen(url, timeout=7).read()
            except:
                print "\nError connecting, probably due to malfunctioning proxy (or the board being down). Try switching to Tor or using no proxy, or try again."
                sys.exit("Exited")
            index_html=lxml.html.fromstring(index.decode("ascii", "ignore"))
            divs=index_html.findall(".//div")
            for div in divs:
                try:
                    thread_div=div.attrib["id"]
                except:
                    continue
                if "thread" in thread_div:
                    threadID=re.search(r"\d+", thread_div).group()
                    thread=urllib2.urlopen(boardpath+"/res/%s.html" % threadID, timeout=7).read()
                    thread=re.sub(r"<br.*?>", "\n", thread) #breaks screw things up
                    thread_html=lxml.html.fromstring(thread.decode("ascii", "ignore"))
                    posts=thread_html.findall(".//blockquote")
                    if image_folder:
                        file_spans=thread_html.findall(".//span[@class='filesize']")
                        for span in file_spans:
                            image_link=span.getchildren()[0].attrib['href']
                            image_data=urllib2.urlopen(image_link, timeout=7).read()
                            image_name=re.search(r", (.*)\n\n\)", span.text_content()).group(1)
                            try:
                                newimage=open(image_folder+image_name, "wb")
                            except IOError:
                                #when there's a character in the filename that's invalid on your filesystem, uses random string+file extension instead
                                newimage=open(image_folder+''.join(random.sample(string.ascii_lowercase, 7))+re.search(r"\..*$", image_name).group(0), "wb")
                            newimage.write(image_data)
                            newimage.close()                           
                    i=0
                    for post in posts:
                        text=post.text_content().strip()
                        content=""
                        if detailed==True:
                            names=thread_html.findall(".//span[@class='postername']")
                            name=names[i].text
                            if name is None:
                                for sub in names[i].iterchildren():
                                    name=sub.text
                            trip=""
                            tripnode=names[i].getnext()
                            if tripnode is not None:
                                trip=tripnode.text
                            if name is None:
                                name=""
                            postnumbers=thread_html.findall(".//input[@name='post[]']")
                            postnumber=postnumbers[i].attrib['value']
                            content+="\n==================================================\n"
                            if search or namesearch:
                                if (any(word.lower() in text.lower() for word in search) if search else None) or ((namesearch.lower() in name.lower()) if namesearch else None):
                                    links=thread_html.findall(".//span[@class='reflink']")
                                    for link in links[i].iterchildren():                                    
                                        content+=chan[:-1]+link.attrib["href"]+"\n\n"
                                        break
                                else:
                                    i+=1
                                    continue #move to next post if searchwords aren't found                             
                            content+=name+trip+"   ###   No. %s" % postnumber+"\n-----------\n\n"
                        if len(text) > 2:
                            if detailed == False:
                                text=re.sub(r"(\r\n)+|\n+", " ", text)                             
                            content+=text
                            boardposts+=content+"\n"
                        i+=1
            pages_spidered+=1
        if detailed == True:
            if len(boardposts) < 2:
                error="No posts found.\n"
                aggregation+="\n\n################\n/"+board+"/\n################\n"+error
            else:
                aggregation+="\n\n################\n/"+board+"/\n################\n"+boardposts
        else:
            aggregation+=boardposts
        boardposts=""
    aggregation=aggregation.rstrip()
    if detailed == False:
        aggregation=re.sub(r">>\d+(\s+)?", "", aggregation) #removes lines that are just quoting other post
    if detailed == True:
        aggregation+="\n\n**********************************\n\n"
    return aggregation

if __name__=="__main__":
    chan="http://www.somechan.org"
    boards="b a" #boards separated by spaces, example: "b c a ck"
    pages=2
    searchwords=["dude", "dumb"]
    name="Anonymous"
    print spider(chan, boards, pages, detailed=True) #also try adding search=searchwords and namesearch=name
