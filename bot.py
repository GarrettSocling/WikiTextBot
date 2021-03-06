# WikiTextBot made by https://github.com/kittenswolf
# Bot in action: reddit.com/u/WikiTextBot
# reddit.com/u/kittens_from_space

# import bot_detector as bd     # Currently not in use
from bs4 import BeautifulSoup
import urllib.request
import subprocess
import wikipedia
import sentences
import traceback
import hashlib
import random
import time
import json
import praw
import re

# Settings 

msg_cache_file      = "cache/msg_cache.txt"
cache_file          = "cache/com_cache.txt"
user_blacklist_file = "user_blacklist.txt"
bot_list_file = "bots.txt" # Currently not in use

# bd_debug = False

comment_threshold = 500
num_sentences = 4

bot_username = "WikiTextBot"

exclude = ["Exclude me", "Exclude from subreddit"]
include = "IncludeMe"

user_already_excluded = "You already seem to be excluded from the bot.\n\nTo be included again, message me '" + include + "'.\n\nHave a nice day!"
user_exclude_done = "Done! If you want to be included again, message me '" + include + "'.\n\nHave a nice day!"
user_include_done = "Done!\n\nHave a nice day!"
user_not_excluded = "It seems you are not excluded from the bot. If you think this is false, [message](https://www.reddit.com/message/compose?to=kittens_from_space) me.\n\nHave a nice day!"

footer_links = [ 
                 ["PM", "https://www.reddit.com/message/compose?to=kittens_from_space"],
                 [exclude[0], "https://reddit.com/message/compose?to=WikiTextBot&message=" + exclude[0].replace(" ", "") + "&subject=" + exclude[0].replace(" ", "")],
                 [exclude[1], "https://np.reddit.com/r/SUBREDDITNAMEHERE/about/banned"],
                 ["FAQ / Information", "https://np.reddit.com/r/WikiTextBot/wiki/index"],
                 ["Source", "https://github.com/kittenswolf/WikiTextBot"]
               ]
               
downvote_remove = "^Downvote ^to ^remove"
               
footer_seperator = "^|"

normal_chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789ßÄÖÜäöüàâæçèéêëîïôœùûÀÂÆÇÈÉÊËÎÏÔŒÙÛ-_#'
disallowed_strings = ["List of", "Glossary of", "Category:", "File:", "Wikipedia:"]
body_disallowed_strings = ["From a modification: This is a redirect from a modification of the target's title or a closely related title. For example, the words may be rearranged, or punctuation may be different.", "From a miscapitalisation: This is a redirect from a miscapitalisation. The correct form is given by the target of the redirect.", "{\displaystyle"]


errors_to_not_print = ["received 403 HTTP response"]

media_extensions = [".png", ".jpeg", ".jpg", ".bmp", ".svg", ".mp4", ".webm", "gif", ".gifv", ".flv", ".wmv", ".amv"]
image_extensions = [".png", ".jpeg", ".jpg", ".bmp", ".gif"]

intro_wikipedia_link = wikipedia_link = "https://en.wikipedia.org/w/api.php?format=json&action=query&prop=extracts&explaintext=&exintro=&exsentences=NUMHERE__1&titles="
category_wikipedia_link = "https://en.wikipedia.org/w/api.php?action=query&format=json&prop=revisions&rvprop=content&rvsection=SECTIONHERE__1&titles="

print("Logging in..")
reddit = praw.Reddit(user_agent='*',
                     client_id="*", client_secret="*",
                     username=bot_username, password="*")
print("Logged in.")

def get_thumbnail(input_id):
    # Currently not used
    page = wikipedia.page(pageid=input_id)
    images = page.images
    
    page_title = page.title
    
    max_extension_len = 0
    for extension in image_extensions: 
        if len(extension) > max_extension_len:
            max_extension_len = len(extension)
            
    good_images = []
    for url in images:
        for extension in image_extensions:
            end_part = str(url.lower())[-max_extension_len:]
            if extension.lower() in end_part:
                good_images.append(url)
                
                
    split_word = page_title.split("_")
    
    thumbnail_images = []
    if not good_images == []:
        for url in good_images:
            for word in split_word:
                if word.lower() in url.lower():
                    
                    thumbnail_images.append(url)
                
                
        if not thumbnail_images == []:
            thumbnail = random.choice(thumbnail_images)
        else:
            thumbnail = random.choice(images)
    else:
        thumbnail = random.choice(images)
        
    return thumbnail

def replace_right(source, target, replacement, replacements=None):
    return replacement.join(source.rsplit(target, replacements))

def get_cache(file):
    """Gets the cache from $file and clears to len(comment_threshold) if necesarry. Also saves it after."""
    try:
        raw_cache = open(file, "r").read()
    except Exception as e:
        print(file + " doesnt exist?")
        return []
        
    cache = [id for id in raw_cache.split("\n")]
    
    real_cache = []
    for id in cache:
        if not id == '':
            real_cache.append(id)
            
    """Trims the file if it goes over maximum threshold"""
    # Currently done manually... dont ask why.
    # if len(real_cache) > comment_threshold:
        # last_part = real_cache[-limit:]

        # with open(file, "w") as f:
            # for id in last_part:
                # f.write(id + "\n")
                
        # real_cache = last_part

    return real_cache
    
def input_cache(file, input):
    try:
        with open(file, "a") as f:
            f.write(input + "\n")
    except Exception as e:
        print(file + " doesnt exist?")
        return

def locateByName(e, name):
    if e.get('name',None) == name:
        return e

    for child in e.get('children',[]):
        result = locateByName(child,name)
        if result is not None:
            return result

    return None

def get_wikipedia_links(input_text):
    """Gets en.wikipedia.org link in input_text. If it can't be found, returns []"""
    
    soup = BeautifulSoup(input_text, "lxml")
    
    fixed_urls = []
    urls = re.findall(r'(https?://[^\s]+)', input_text)
    
    for url in soup.findAll('a'):
        try:
            fixed_urls.append(url['href'])
        except Exception:
            pass
    
    """Deletes duplicates"""
    done_urls = []
    for i in fixed_urls:
        if i not in done_urls:
            done_urls.append(i)
            
    """Deletes urls that contain a file extension"""
    fixed_urls = []
    for url in done_urls:
        for extension in media_extensions:
            if not extension.lower() in url.lower():
                fixed_urls.append(url)
                break
                
    soup.decompose()

    return fixed_urls

def get_wiki_text(original_link):
    wiki_subject = original_link.split("/wiki/")[1]
    
    anchor = False
    if "#" in wiki_subject:
        try:
            # Anchor detected
            
            # First, get page id
            request_url = intro_wikipedia_link + wiki_subject
            request_url = request_url.replace("NUMHERE__1", str(num_sentences))
    
            response = urllib.request.urlopen(request_url).read().decode("utf-8") 
            json_data = json.loads(response)
            page_id = [key for key in json_data["query"]["pages"]][0]

            ##
            
            wanted_anchor = wiki_subject.split("#")[1].replace("_", " ")
            pure_subject = wiki_subject.split("#")[0]
            
            page = wikipedia.page(pageid=page_id)
            anchor_text = page.section(wanted_anchor)
            
            list_trimmed_text = sentences.split(anchor_text)[:num_sentences]
            
            final_text = []
            for sentence in list_trimmed_text:
                if final_text == []:
                    final_text.append(sentence)
                else:
                    final_text.append(" " + sentence)
                    
            trimmed_text = ''.join(final_text)
            
            if trimmed_text == '':
                return "Error"
                
            for string in disallowed_strings:
                if string.lower() in str(page.title).lower():
                    return "Error"
                
            for string in body_disallowed_strings:
                if string.lower() in trimmed_text.lower():
                    return "Error"
                
            return [page.title + ": " + wanted_anchor, trimmed_text]
        
        except Exception as e:
            return "Error"

    
    request_url = intro_wikipedia_link + wiki_subject
    request_url = request_url.replace("NUMHERE__1", str(num_sentences))
    
    try:
        response = urllib.request.urlopen(request_url).read().decode("utf-8") 
        json_data = json.loads(response)
        page_key = [key for key in json_data["query"]["pages"]][0]
        
        title = json_data["query"]["pages"][page_key]["title"]
        body = json_data["query"]["pages"][page_key]["extract"]
        
        if body == '':
            return "Error"

        for string in disallowed_strings:
            if string.lower() in title.lower():
                return "Error"
                
        for string in body_disallowed_strings:
            if string.lower() in body.lower():
                return "Error"
                

        return [title, body]
    except Exception as e:
        print(str(e))
        return "Error"
        
def generate_footer():
    footer = "^[ "

    links = []
    for link in footer_links:
        final_desc = "^" + link[0].replace(" ", " ^")
        final_link = "[" + final_desc + "](" + link[1] + ")"
        links.append(final_link)

    for link in links:
        footer += link
        footer += " " + footer_seperator + " "

    footer += " ^]"
    footer = replace_right(footer, footer_seperator, "", 1)
    
    footer += "\n" + downvote_remove + " ^| ^v0.24"

    return footer

def generate_comment(input_urls):
    comment      = []
    content      = []
    done_comment = []

    for url in input_urls:
        url_content = get_wiki_text(url)
        
        if not url_content == "Error":
            content.append(url_content)
    

    for chunk in content:
        title = chunk[0]
        body  = chunk[1]
        
        body = body.replace("\n", "\n\n")

        comment.append("**" + title + "**\n")
        comment.append(body)
        comment.append("\n***\n")

    if comment == []:
        return "Error"

    for line in comment:
        done_comment.append(line + "\n")

    done_comment.append(generate_footer())
    comment = ''.join(done_comment)

    return comment

def check_excluded(file, input_user):
    try:
        raw_file = open(file, "r").read()
    except Exception as e:
        print(file + " doesnt exist?")
        return
        
    current_excluded = [user.lower() for user in raw_file.split("\n")]
    
    if input_user.lower() in current_excluded:
        return True
    else:
        return False
        
def excludeUser(file, input_user):
    try:
        raw_file = open(file, "r").read()
    except Exception as e:
        print(file + " doesnt exist?")
        return
        
    current_excluded = [user.lower() for user in raw_file.split("\n")]
    current_excluded.append(input_user)
    
    with open(file, "w") as f:
        for user in current_excluded:
            f.write(user + "\n")
            
def includeUser(file, input_user):
    try:
        raw_file = open(file, "r").read()
    except Exception as e:
        print(file + " doesnt exist?")
        return
        
    try:
        current_excluded = [user.lower() for user in raw_file.split("\n")]
        current_excluded.remove(input_user)
    except Exception:
        pass
    
    with open(file, "w") as f:
        for user in current_excluded:
            f.write(user + "\n")

def monitorMessages():
    """Montors the newest 100 messages and excludes/includes users requesting it."""

    for message in reddit.inbox.messages(limit=100):
        current_msg_cache = get_cache(msg_cache_file)
        
        if not message.id in current_msg_cache:
            author = str(message.author)
    
            if not author == bot_username:
            
                if exclude[0].replace(" ", "").lower() == message.subject.lower():
                    already_excluded = check_excluded(user_blacklist_file, author) 

                    if already_excluded == True:
                        message.reply(user_already_excluded)
                    else:
                        print("Excluding the user '" + author + "'")
                        excludeUser(user_blacklist_file, author)
                        message.reply(user_exclude_done)
                
                if include.lower() == message.subject.lower():
                    already_excluded = check_excluded(user_blacklist_file, author)
            
                    if already_excluded == True:
                        print("Including the user '" + author + "'")
                        includeUser(user_blacklist_file, author)
                        message.reply(user_include_done)
                    else:
                        message.reply(user_not_excluded)
                
                
            input_cache(msg_cache_file, message.id)

def enter_bot(file, input_user):
    return #Not in use
    
    
    """Enter a user as a bot to $file"""
    try:
        raw_file = open(file, "r").read()
    except Exception as e:
        print(file + " doesnt exist?")
        return
        
    current_bots = get_bot_list(file)
    current_bots.append(input_user)
        
    with open(file, "w") as f:
        for bot in current_bots:
            f.write(bot + "\n")

def get_bot_list(file):
    # Currently not used. Maybe soon?
    return ["HelperBot_", "AutoModerator", "MovieGuide", "Decronym"]


    try:
        raw_file = open(file, "r").read()
    except Exception as e:
        print(file + " doesnt exist?")
        return []
        
    bots = [bot for bot in raw_file.split("\n") if not bot == '']
    return bots

def check_bot(input_user):
    # Currently not used
    return "-"

    # score = bd.calc_bot_score(input_user)
    
    # if not score == "Error":
        # verdict = bd.score_helper(score)
        # return verdict
    # else:
        # return "-"

def main():
    monitorMessages()
    for comment in reddit.subreddit('all').comments(limit=100):
    
        #Check if "wikipedia.org/wiki/" in comment. This should migate most comment.id spam
        if "wikipedia.org/wiki/" in str(comment.body).lower():
            # Check if user is blacklisted (excluded)
            if not check_excluded(user_blacklist_file, str(comment.author)) == True:
                # Check if id is in cache
                if not comment.id in get_cache(cache_file):
                    # Check if user is in already bot list:
                    if not str(comment.author) in get_bot_list(bot_list_file):
                    
                        # Check if user is bot
                        # Currently not used                        
                        if check_bot(str(comment.author)) == "+":
                            enter_bot(bot_list_file, str(comment.author))
                            print(str(comment.author) + " is a bot")
                        else:
                            urls = get_wikipedia_links(comment.body_html)
        
                            if not urls == []:
                                comment_text = generate_comment(urls)
                                comment_text = comment_text.replace("SUBREDDITNAMEHERE", str(comment.subreddit))
            
                                if not comment_text == "Error":
                                    print("Replying to " + str(comment.author) + " in /r/" + str(comment.subreddit))
                                    
                                    # print(comment_text)
                                    comment.reply(comment_text)

                
                input_cache(cache_file, comment.id)

# bd.settings(reddit, debug_in=bd_debug)
# Currently not used
while True:
    try:
        main()
    except Exception as e:
        if e == praw.exceptions.APIException:
            print("ratelimit hit, sleeping 100 secs.")
            time.sleep(100)
            
        if not str(e) in errors_to_not_print:
            print(str(e))

            # traceback.print_exc()
        
        
        time.sleep(0.5)
    
