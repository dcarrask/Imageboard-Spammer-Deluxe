#!/usr/bin/env python

# Imageboard Spammer Deluxe
# v0.2
#
# By: Anorov
#
# A few ideas taken from frankusrs' ImageRaep4Free (written in Perl): https://github.com/frankusrs/ImageRaep4Free/
#
# Required 3rd party modules: "SocksiPy", "TorCtl" (which has "TorUtil" as a dependency), "lxml", "poster".
# lxml is platform-dependent. Read download and installation instructions for your operating system here: http://lxml.de/installation.html
#
# Optional and included custom modules: "wikipedia", "retardify", "MarkovSentences", "chanspider"
#
# A lot of this code may be bad, ugly, or poorly organized/designed.
# If you see any issues or can suggest any improvements, please do so.
# Also, this is probably way longer than it should be. I tried to provide a very wide range of modes and sub-modes. There's also some redundant code.

###TODO:
#
# - implement command line arguments and options
# - replace all urllib2 logic with (most likely) Twisted, either twisted.web.client.Agent or twisted.web.client.getPage
# - use Twisted to launch multiple sockets, perhaps to have one loop with Tor handling and posting, and another with 2 or more loops for proxies, to highly speed things up
# - add support for Google reCAPTCHA. ideally make it as easy as possible to see and respond to captchas on the fly, on both Windows and Linux. maybe with Tkinter?
# - maybe provide a web interface for multiple people to type captchas, to combat reCAPTCHA as effectively as possible. this might be difficult.
# - possibly make use of reCAPTCHA caching like the '4chan X' browser extension does
# - maybe allow cycling of useragents. will this actually be helpful?
# - implement additional optional modes. not a big priority.
#
#NOTE: I did not use mechanize due to compatibility problems with the "poster" module, which is required to properly send multipart/form-data content for images.

import socket, socks, select, urllib2, lxml.html, random, string, re, cookielib, itertools, sys, os
from time import sleep
from poster.encode import multipart_encode
from poster.streaminghttp import register_openers

__version__ = "0.2"

##############################################

###SETTINGS###
#Set these:
URL = "" #URL of Kusaba index. Include trailing slash. Example: "http://www.4chan.org/", or "http://www.website.com/chan/"
board = "" #Board name, no slashes. Will later provide options to post to multiple boards. Used only for spamming modes, not spidering. Example: "b"

#Static settings used for default modes
NAME = "" #Can be blank
EMAIL = "" #Can be blank
SUBJECT = "" #Can be blank
STATIC_MESSAGE = "" #Can only be blank if image is posted
STATIC_IMAGE = "images/bsd_daemon.jpg" #Static image that'll be posted; used in default modes. Can be blank if not using default modes, or if not posting new threads and STATIC_MESSAGE is set.

#Settings for other modes/options, and other settings
IMAGE_FOLDER = "images/" #Folder path containing images for image spamming/dumping. Used for Folder Spam and Folder Dump modes. Include trailing slash.
RAND_MESSAGES = "messages.txt" #Path to text file containing messages for random posting (used in folder spam mode). Ensure this file contains no blank lines unintentionally; blank lines may be selected too.
LAST_PAGE = 8 #Last page of the board you want to target. Used for "Old Bump" mode.

IMAGE_ARCHIVE_FOLDER = "spidered_images/" #Folder used to save images when spidering a chan. Can be blank if not spidering, or not using image-spidering mode. Include trailing slash.

CAPTCHA_BYPASS = False #Set this to True to attempt to bypass default Kusaba captchas. Will not work on Google reCAPTCHA.

BOARDPATH=URL+board+"/" #Don't change this.

USERAGENT = "Mozilla/5.0 (Windows NT 5.1; rv:5.0.1) Gecko/20100101 Firefox/5.0.1" #User-agent that will appear in site access logs. I'd recommend using something common (like the default) so it is hard to ban.
REFERER = BOARDPATH #Set HTTP Referer here. I'd recommend leaving this as BOARDPATH.

#Smart reply options
BRAIN = "brain.txt" #Path to post-storing brain. Necessary only for spidering and Smart Reply modes.
chain_length = 2 #Markov chain length. 2 is recommended for the most original sentences; anything higher will make more sense (by copying phrases more directly) but will be less original.
message_length = 35 #Approximate total length of posts that will be made (will be a bit longer than what is given, because the script attempts to complete the last sentence).
proper_sentences = True #Capitalize the first letter of each sentence.
paragraph_chance = 3 #1/paragraph_chance will be the chance of there being a double linebreak inserted after a sentence

#Youtube
youtube_chance=3 #1/youtube_chance of embedding a Youtube video with your post, if Youtube option is selected later on
min_views=500000 #minimum view count of randomly chosen Youtube video

##############################################

opener=register_openers()

#Handling for Kusaba captcha bypass. Must follow below instructions for this to work properly.
captcha="" #leave this alone
"""
****Only set these if you are trying to spam a board with Kusaba 0.9.2 and below's default captchas enabled.****

-Kusaba 0.9.3 and up uses Google's reCAPTCHA by default. There is currently no support for reCAPTCHA, though I will add it soon.
-Verify the board you are targeting's captcha appears as a small box with 6 random letters in it. This is the Kusaba default captcha before 0.9.3.

The exploit is essentially that Kusaba only generates a new captcha when your session loads the captcha image.
If you load the image only once, you can use the answer to that one captcha for your entire session.
The captcha answer can be re-used until either a new captcha is loaded, or the session ends.
This script does not render any links (the captcha is normally loaded by setting an img src to www.chansite.com/captcha.php), so it never loads the captcha image.

=INSTRUCTIONS=

View www.chansite.com/captcha.php once in your browser (with a proxy, I'd recommend, and maybe a different browser for ease).
Don't refresh or visit it again, and do not visit any of the chan's board pages again in that session and/or with that browser.

-Set the 'captcha' variable below to the captcha you see.
-Then view your cookies and set the 'sessionID' variable to your current Session ID.
-This cookie will be named 'PHPSESSID' in your browser. It will appear as a long hex string.

This should work up until your session expires. If you get an error just try starting a new session+captcha.
"""
if CAPTCHA_BYPASS==True:
    captcha="" #set this one. example: "wotlmk"
    sessionID="" #example: "4510eb7fc3c6d89e43dfabe7fbc7f095"
    chan_domain=re.search(r"(\..*\..*)/", URL).group(1)
    jar=cookielib.CookieJar()
    jar.set_cookie(cookielib.Cookie(version=0,
                                    name='PHPSESSID',
                                    value=sessionID,
                                    port=None,
                                    port_specified=False,
                                    domain=chan_domain,
                                    domain_specified=False,
                                    domain_initial_dot=True,
                                    path='/',
                                    path_specified=True,
                                    secure=False,
                                    discard=True,
                                    comment=None,
                                    comment_url=None,
                                    expires=None,
                                    rest={'HttpOnly': None},
                                    rfc2109=False))
    opener.add_handler(urllib2.HTTPCookieProcessor(jar))

###Headers
opener.addheaders = [('User-agent', USERAGENT),
                     ('Referer', REFERER)]
urllib2.install_opener(opener)

###Constants and variables
form = URL+"board.php" #this shouldn't ever need to be changed unless you're dealing with a seriously modded Kusaba install
clear = socket.socket #default non-proxy socket
youtube=False #leave this, there'll be an input prompt option to change it later
static_proxy = ""
imagelist = []
fileindex = 0

#Modes
DEFAULT=0
FOLDER_SPAM=1
OLD_BUMP=2
FOLDER_DUMP=3
#Submodes
WIKI=0.2
MARKOV=0.3

def cleanProxies():
    """Cleans a list of proxies and saves them to a text file."""
    rawproxylist=open("raw_proxies.txt", "r")
    proxies=open(proxysetting+"_proxies.txt", "a")
    for line in rawproxylist:
        try:
            ip=re.search(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", line)
            if re.search(r"\s\d{1,5}\s", line): #format: '123.123.123.123  8080' or any [whitespace]digits[whitespace]
                raw=re.search(r"\s\d{1,5}\s", line)
                port=re.search(r"\d{1,5}", raw.group(0))
            else:
                raw=re.search(r"\:\d{1,5}", line) #format: '123.123.123.123:8080'
                port=re.search(r"\d{1,5}", raw.group(0))
            proxies.write(ip.group(0)+':'+port.group(0)+"\n")
        except AttributeError:
            pass
    rawproxylist.close()
    proxies.close()
    print "Proxies cleaned and written to file."

def findWorkingProxies():
    """Takes a list of SOCKS5 or HTTP proxies, checks which ones are working, and saves the working ones to a text file.
    Pre-compiling working proxies before spamming usually makes things easier. Otherwise only 1-3% of spam will actually go through."""   
    print "Now compiling list of working proxies.\n"
    proxylist=open(proxysetting+"_proxies.txt", "r")
    addworking=open("working_"+proxysetting+"_proxies.txt", "a")
    def connect():
        try:
            page=urllib2.urlopen(BOARDPATH, timeout=7).read()
            if "YOU ARE BANNED" in page:
                print "Banned proxy" #if you see a lot of these, the board may be actively banning many SOCKS proxy lists
                return False
            else:
                return True
        except:
            return False
        
    for line in proxylist:
        if line != "\n": #ignore blank lines
            split=line.split(":")
            IP=split[0]
            port=int(split[1].strip("\n"))
            print "Moving onto next proxy: %s:%d" % (IP, port)
            if proxysetting=="socks":               
                socket.setdefaulttimeout(6) #even with both the urllib2 timeout and the socket default timeout, sometimes it'll still hang on a certain proxy. not sure how to fix.
                socks.setdefaultproxy(proxytype, IP, port)
                socket.socket=socks.socksocket
            else:
                proxy_handler=urllib2.ProxyHandler({"http": "http://%s/" % line})
                opener.add_handler(proxy_handler)
                urllib2.install_opener(opener)                               
            try:
                if connect():
                    print "Working proxy added.\n"
                    addworking.write(line)
                    addworking.flush()                   
            except KeyboardInterrupt:
                opt=raw_input("[m]ove to next proxy (default) or [e]xit completely: ")
                if opt=="e":
                    print "\nStopping"
                    addworking.close()
                    proxylist.close()
                    socket.socket=clear
                    sys.exit("Exited cleanly")
                else:
                    continue                   
    print "\nCompleted. Working proxies added."
    addworking.close()
    proxylist.close()  

def resetTor():
    """Sends the circuit reset signal (NEWNYM) to the Tor daemon, using the TorCtl module."""
    socket.socket=clear
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(("127.0.0.1", controlport))
    c = TorCtl.Connection(s)
    c.authenticate(secret=password)
    c.send_signal(3) #NEWNYM signal. opens a new circuit (new exit node, new IP)
    c.close()
    s.close() #test this
    socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, IP, port)
    socket.socket=socks.socksocket
    print "Successful Tor circuit reset. Probably.\n"

def mutateImage(image):
    """Appends a random character to the end of the image, to prevent duplicate file detection.
    Allows spamming of the same image indefinitely."""   
    try:
        img = open(image, "a")
        randomchar = ''.join(random.choice(string.ascii_uppercase))
        img.write(randomchar)
        img.close()
    except KeyboardInterrupt:
        print "\nStopping"
        img.close()
        sys.exit(0)

def post(ID, message, image=None, youtubeID=""):
    """Simply makes a post with the given parameters. Also adds 1 byte to each image before posting."""
    post_image=""
    if image is not None:
        mutateImage(image)
        post_image = open(image, "rb")
    
    #POST variables
    values = { 'board': board,
               'replythread': ID,
               'MAX_FILE_SIZE': 1024000000,
               'email': '', #anti-spam form field
               'captcha': captcha,
               'name': NAME,
               'em': EMAIL, #real email field
               'subject': SUBJECT,
               'message': message,
               'imagefile': post_image,
               'embed': youtubeID,
               'embedtype': 'youtube'
             }

    data, headers=multipart_encode(values)
    try:
        req = urllib2.Request(form, data, headers)
        urllib2.urlopen(req, timeout=6)
        if post_image:
            post_image.close()
        return True
    except KeyboardInterrupt:
        print "\nStopping"
        socket.socket=clear
        post_image.close()
        sys.exit("Exited cleanly")
    except:
        return False

def randomYoutube(views):
    """Gets a random US Youtube video. Pass an int if you want a minimum view count (for example, only get videos that have >2000000 views)."""
    api="http://flyhour.tv/bots/api/index.php?type=2&countries=US&category=All&views=%s" % str(views)
    page=urllib2.urlopen(api).read()
    tree=lxml.html.fromstring(page)
    video=tree.find(".//embed").attrib["src"]
    ID=video.split("/")[-1]
    return ID

def lastThread():
    """Grabs the ID of the last thread on the last page."""
    global LAST_PAGE
    url=BOARDPATH+str(LAST_PAGE)+".html"
    try:
        html=urllib2.urlopen(url, timeout=6).read()
    except:
        return False
    if "kusaba" not in html[-90:]: #tries to verify the page is valid and not a 404
        LAST_PAGE-=1 #tries to compensate for a changing or incorrect LAST_PAGE
        print "Decrementing last page, using last page %s" % LAST_PAGE
        return lastThread()
    else:
        thread_html=lxml.html.fromstring(html)
        links=thread_html.findall(".//span[@class='reflink']")
        a=links[-1].find("./a")
        link=a.attrib['href']                                
        number=re.search(r"(\d{1,10})\.html", link)
        last_thread_ID=number.group(1)
        last_thread_ID=str(last_thread_ID)
        return last_thread_ID

def getRandomPost(ID):
    """Read a random post in the thread, and also grab its post ID."""
    url=BOARDPATH+"res/%s.html" % ID
    try:
        html=urllib2.urlopen(url, timeout=7).read()
    except:
        return False
    thread_html=lxml.html.fromstring(html)
    posts=thread_html.findall(".//blockquote")
    checkboxes=thread_html.findall(".//input[@name='post[]']")
    i=random.randint(0, len(posts)-1)
    post=posts[i].text
    ID=checkboxes[i].attrib['value']
    post_data={"message": post, "ID": ID}
    #returns a dict, because why not. also makes it a tiny bit clearer than tuple unpacking when assigning later.
    return post_data  

def fromFolder(dump=False):
    """Selects a random image from the IMAGE_FOLDER, and if applicable, a random message from RAND_MESSAGES."""
    global fileindex
    message=""
    if dump==True:
        if fileindex > (len(imagelist)-1):
            option=raw_input("\nFolder fully dumped. [r]estart from beginning or [e]xit? (Default is exit.)\n")
            if option=="r":
                print "Restarting dump...\n"
                fileindex=0
            else:
                sys.exit("Exited cleanly")
        image=imagelist[fileindex]
        message="%d/%d" % (fileindex+1, len(imagelist))
        fileindex+=1        
    else:
        files=os.listdir(IMAGE_FOLDER)
        image=random.choice(files)
        if os.path.splitext(image)[1].lower() not in (".gif", ".jpg", ".png", ".jpeg"):
            return fromFolder() #try again if it sees a file that's not an image
        if RAND_MESSAGES and os.path.exists(RAND_MESSAGES):
            text=open(RAND_MESSAGES, "r")
            message=random.choice(text.readlines())
            text.close()
    image=IMAGE_FOLDER+image
    return message, image

def spam(mode=0, submode=0, ID="0", retardify=False):
    """Spam mode handling. Default just loops posting new threads with a static image and message."""
    global IP, port, static_proxy
    socket.socket=clear

    #defaults
    image=STATIC_IMAGE
    message=STATIC_MESSAGE
    youtubeID=""

    if proxysetting=="tor":
        if mode == FOLDER_DUMP and submode == 0.1: #persistent proxy mode
            pass
        else:
            sleep(8) #Tor needs at least a 10 second delay between signaling to properly reset circuits. Take into consideration post time.
            resetTor()
    
    if proxysetting != "tor" and proxysetting != "no":
        proxy=random.choice(working) #uses a random proxy from the list each time
        if mode == FOLDER_DUMP and submode == 0.1 and static_proxy:
            proxy=static_proxy
        IP=proxy[0]
        port=proxy[1]
        print "Using %s:%d" % (IP, port)
        if static_proxy=="":
            static_proxy=proxy #sets static_proxy to the first proxy received

    #maybe find a better way to handle modes, this is all kind of confusing to read
    if mode < 2 and submode == 0.1:
        if ID == "0":
            print "\nSub-mode 0.1 selected, but no thread ID has been selected. Exiting."
            sys.exit("Exited cleanly")

    if mode == DEFAULT:
        pass #verify specific IDs work properly
    
    if mode == FOLDER_SPAM:
        #Folder Spam
        message, image=fromFolder()

    if mode == FOLDER_DUMP:
        #Folder Dump
        message, image=fromFolder(dump=True)

    if submode == WIKI:
        message=wikipedia.randomArticle()
        if message == None or "cannot be found." in message:
            return spam(mode, submode, retardify)
    
    if proxysetting == "http":
        proxy_handler=urllib2.ProxyHandler({"http": "http://%s/" % proxy})
        opener.add_handler(proxy_handler)
        urllib2.install_opener(opener)
    elif proxysetting != "no":            
        socks.setdefaultproxy(proxytype, IP, port)
        socket.socket=socks.socksocket

    if mode==OLD_BUMP:
        #Old Bump
        random_message, random_image=fromFolder()
        if submode != DEFAULT:
            if "n" not in folderopt.lower():
                image=random_image
            else:
                image=None
        ID=lastThread()
        if ID==False:
            return spam(mode, submode, retardify)

        if submode==0.1:
            #Random image and message
            message=random_message           

        if submode==MARKOV:
            random_post=getRandomPost(ID)
            if random_post==False:
                return spam(mode, submode, retardify)
            message=markov.genMessage(message_length, line=random_post["message"], proper_sentences=proper_sentences, paragraph_chance=paragraph_chance)
            #Fancying it up a bit for chan posting. May move some of this functionality to MarkovSentences, or I might keep it here.
            #I've had trouble working out a good regex for smilies, so people who use smilies to end sentences may screw things up a bit.
            quotesplit=re.split(r"(> ?\w.+?[.!?]\s*)", message)
            message=''.join(["\n"+i for i in quotesplit]).lstrip()
            message=">>%s\n" % str(random_post["ID"]) + message

    if youtube==True:
        if random.randint(1, youtube_chance)==1:
            youtubeID=randomYoutube(min_views)
            image=None
            
    if retardify==True:
        message=retardifier.transform(message)
                     
    #post; covers everything
    post(ID, message, image, youtubeID)
        
def modeSelect():
    prompt="Please choose a mode. Default is 0. Enter 'modes' (without quotes) for a list and explanation of all modes and sub-modes: "
    subprompt="\nPlease choose a sub-mode. Enter 'modes' (without quotes) to see the sub-modes for the mode you want: "
    retardify=False
    ID="0"
    modes="""\nMODES:

 0: Default => Loops a static image, and a static message unless using Wiki sub-mode.
  Sub-modes:
 \t0: Default => Posts a new thread.
 \t1: ID => Spam a single, specific thread.
 \t2: Wiki => Posts threads with a random Wikipedia article and static image.

 1: Folder Spam => Spams random images and (if found) random text selected from a designated folder and text file.
  Sub-modes:
 \t0: Default => Makes new threads.
 \t1: ID => Spam a single, specific thread.
 \t2: Wiki => Posts threads with a random Wikipedia article and random image from the IMAGE_FOLDER.

 2: Old Bump => Loop bumping the last thread on the last page, based on LAST_PAGE proxysetting. May be slower.
  Sub-modes:
 \t0: Default => Bumps with a static image and message.
 \t1: Folder Bump => Identical to Folder Spam, but applies it to bumping old threads.
 \t2: Wiki => Bumps with the first section of a random Wikipedia article. Image is random from folder.
 \t3: Smart => Replies to posts in the thread with a Markov chain sentence generator. Will eventually produce semi-sensible, semi-original posts, based on a "brain" of the imageboard's posts.

 3: Folder Dump => A mode that can be used for legitimate folder dumping. An option is provided later for using no proxy at all.
 \t0: Default => Dumps images from a folder sequentially in a thread. Will show a running count of the images.
 \t1: Persistent Proxy => Does not switch or cycle through proxies while dumping. Recommended for when there's little or no post timers.

Note: there is an optional setting to "retardify" all output. Retardify is a small module I made to make text look very annoying and childish.
##############################
"""
    mode=raw_input(prompt)
    if mode=="modes":
        print modes
        mode=raw_input(prompt)
    if mode.isdigit():
        mode=int(mode)
    else:
        mode=0
    if mode==0:
        print """Using DEFAULT mode: 0
Spamming with image '%s' and message '%s'""" % (STATIC_IMAGE, STATIC_MESSAGE)
    else:        
        print "Using mode: %d" % mode
        
    submode=raw_input(subprompt)
    if submode=="modes":
        print modes
        submode=raw_input(subprompt)
    if submode.isdigit():
        submode=int(submode)
    else:
        submode=0
    if submode==0:
        print "Using DEFAULT submode: 0"
    else:
        print "Using submode: %d" % submode

    if submode==1:
        submode=0.1

    if submode==2:
        submode=WIKI #0.2

    if submode==3:
        submode=MARKOV #0.3
        corpus=open(BRAIN, "r")
        if len(corpus.readlines()) < 7:
            print "Brain ('%s') is empty or does not have sufficient lines to generate smart sentences. Exiting." % BRAIN
            sys.exit("Exited cleanly")
                
    if mode < 2 and submode==0.1:
        ID=raw_input("\nEnter thread ID to spam: ")

    if mode==FOLDER_DUMP:
        files=os.listdir(IMAGE_FOLDER)
        for image in files:
            if os.path.splitext(image)[1].lower()in (".gif", ".jpg", ".png", ".jpeg"):
                imagelist.append(image)
        ID=raw_input("\nEnter thread ID to dump to: ")

    if mode > 3 or submode > 1:
        print "Unknown mode or submode selected. Exiting."
        sys.exit("Exited cleanly")

    if ( (mode==FOLDER_DUMP) or (mode < 2 and submode==0.1) ) and not ID:
        print "Thread-targeted mode selected but no ID was entered. Exiting."
        sys.exit("Exited cleanly")


    retardify=raw_input("\nRetardify all output? Default is 'no'. [y/N] ")
    if retardify.lower()=="y":
        retardify=True
        print "\nUsing retardify on all output."   
    
    return mode, submode, ID, retardify      

###MAIN###
if __name__ == "__main__":
    proxysetting=raw_input("Choose [s]ocks5 proxy list, [h]ttp proxy list, or [t]or: ")
    if proxysetting=="s":
        proxysetting="socks"
        proxytype=socks.PROXY_TYPE_SOCKS5
    elif proxysetting=="h":
        proxysetting="HTTP"
        proxytype=socks.PROXY_TYPE_HTTP
    elif proxysetting=="t":
        proxysetting="tor"
        proxytype=socks.PROXY_TYPE_SOCKS5
        import TorCtl
    else:
        print "No proxy type selected"
        sys.exit("Exited cleanly")

    option=raw_input("""
    clean - clean a list of non-formatted SOCKS5 or HTTP proxies
    
    findworking - check a list of SOCKS5 or HTTP proxies and save the ones that work
    
    spam - spam a board with a list of working proxies, or Tor
    
    spider - spider posts to create a corpus (can be used for archival, or Smart Reply mode)

Option: """)
    print ""

    if option=="clean":
        if proxysetting=="tor":
            print "Tor in use, no proxy type selected. Try again with SOCKS5 or HTTP."
            sys.exit("Exited cleanly")
        cleanProxies()

    elif option=="findworking":
        if proxysetting=="tor":
            print "Tor in use, no proxy type selected. Try again with SOCKS5 or HTTP."
            sys.exit("Exited cleanly")
        findWorkingProxies()

    elif option=="spam" or option=="spider":    
        if proxysetting=="tor":
            IP="127.0.0.1"
            port=9050
            controlport=9051 #Tor control port
            password="password" #password set for Tor control 
            print "Please ensure Tor is running and listening on port '%d', with Tor control running on port '%d' with password '%s'.\n" % (port, controlport, password)
        else:
            working=[]
            plist=open("working_"+proxysetting+"_proxies.txt", "r")
            for line in plist:
                split=line.split(":")
                IPfield=split[0]
                portfield=int(split[1].strip("\n"))
                working.append((IPfield, portfield))
            working.sort()
            working=list(working for working, i in itertools.groupby(working)) #removes duplicates

        #Spam loop
        if option=="spam":
            args=modeSelect() #optparse alternatives will be added here as well soon
            if args[0]==OLD_BUMP:
                folderopt=raw_input("\nUse [n]o images, [d]efault IMAGE_FOLDER, or image [a]rchive folder (IMAGE_ARCHIVE_FOLDER) for spamming? Latter recommended if you have spidered images.\n")
                if folderopt.lower()=="a":
                    IMAGE_FOLDER=IMAGE_ARCHIVE_FOLDER
            if args[0]==FOLDER_SPAM or args[0]==OLD_BUMP:
                youtubeopt=raw_input("\nAdd a random chance to make a post with a random Youtube video? [y/N] ")
                if "y" in youtubeopt.lower():
                    youtube=True
            if args[1]==WIKI:
                import wikipedia
            if args[1]==MARKOV:
                import MarkovSentences
                markov=MarkovSentences.MarkovSentences(BRAIN, chain_length, newline_fix=True)
            if args[3]==True:
                import retardify
                retardifier=retardify.Retardify()
            if args[0]==3:
                proxy=raw_input("\nUse [s]elected proxy type, or [n]o proxy? (Default is selected proxy type.) Do not use 'no proxy' if there is a post delay timer.\n")
                if proxy=="n":
                    proxysetting="no"

            print "\nNow spamming %s with %s proxies.\n" % (BOARDPATH+" (thread ID: #"+args[2]+")" if args[2] != "0" else BOARDPATH, proxysetting.upper())
            try:
                while True:
                    spam(mode=args[0], submode=args[1], ID=args[2], retardify=args[3])
            except KeyboardInterrupt:
                print "\nStopping"
                socket.socket=clear
                sys.exit("Exited cleanly")

        #Spider
        if option=="spider":
            import chanspider #I recommend spidering a chan BEFORE you spam it with weird shit/Wikipedia articles. Just a tip.
            proxy=raw_input("Use [s]elected proxy type, or [n]o proxy? (Default is selected proxy type, but spidering may be very slow with proxies. If using a proxy, Tor recommended for reliability.)\n")
            if proxy=="n":
                proxysetting="no"
            else:
                socks.setdefaultproxy(proxytype, IP, port)
                socket.socket=socks.socksocket
            boards=raw_input("Choose what boards you want to spider, separated by spaces. Example: 'a c b ck'\n")
            printboards=boards.split()
            printboards=["'"+board+"'" for board in printboards]
            printboards=", ".join(printboards)
            pages=int(raw_input("How many pages of each board to spider. Each additional page adds time.\n"))
            imageopt=raw_input("Also save all images of each thread? This may add a lot of time.\nWhen spamming, there's a Folder Spam option to use this folder. Purpose is to make Smart Reply funnier/more interesting. [y/N]\n")
            if imageopt.lower() != "y":
                IMAGE_ARCHIVE_FOLDER=""
            print "\nNow spidering %s board(s) %s, %d page(s) each, with %s proxies. This may take a while." % (URL, printboards, pages, proxysetting.upper())
            posts=chanspider.spider(URL, boards, pages, image_folder=IMAGE_ARCHIVE_FOLDER)
            posts=posts.encode("ascii", "ignore")
            post_archive=open(BRAIN, "a")
            post_archive.write(posts)
            post_archive.close()
            print "\nSpidering complete. All posts saved in %s" % BRAIN

    else:
        print "\nNo mode selected."
        sys.exit("Exited cleanly")
