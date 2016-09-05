# coding=utf-8
"""
Exposes a simple HTTP API to search a users Gists via a regular expression.

Github provides the Gist service as a pastebin analog for sharing code and
other develpment artifacts.  See http://gist.github.com for details.  This
module implements a Flask server exposing two endpoints: a simple ping
endpoint to verify the server is up and responding and a search endpoint
providing a search across all public Gists for a given Github account.
"""

import requests
from flask import Flask, jsonify, request
import urllib
import re

# *The* app object
app = Flask(__name__)


@app.route("/ping")
def ping():
    """Provide a static response to a simple GET request."""
    return "pong"


def gists_for_user(username):
    """Provides the list of gist metadata for a given user.

    This abstracts the /users/:username/gist endpoint from the Github API.
    See https://developer.github.com/v3/gists/#list-a-users-gists for
    more information.

    Args:
        username (string): the user to query gists for

    Returns:
        The dict parsed from the json response from the Github API.  See
        the above URL for details of the expected structure.
    """
    gists_url = 'https://api.github.com/users/{username}/gists'.format(
            username=username)
    response = requests.get(gists_url)
    # BONUS: What failures could happen?
    ###### if API rate limit exceeded then we will access an error page
    ###### instead of a user's gists page... will handle this in function "search()"!

    # BONUS: Paging? How does this work for users with tons of gists?
    return response.json()


##### My solution begins here!

def is_url(string):
    """
    Function checks string to see if it is an url
    if url, returns True
    else, returns False
    """
    if (string is None):
        return False
    elif (type(string) is int or type(string) is bool):
        return False
    elif (len(string)<8):
        return False
    elif (string[:8] != 'https://' and string[:7] != 'http://'):
        return False
    return True

def search_gists(gist,gistlist):
    """
    Function takes a gist and a list as an argument
    Recursively calls itself and updates 'gistlist' with the contents
    of all gists.
    """
    for item in gist:
        if (type(gist) is dict):
            if (type(gist[item]) is dict):
                search_gists(gist[item],gistlist)
            else:
                gistlist.append(gist[item])
        else:
            gistlist.append(gist)

def get_all_urls(gist):   
    """
    Function calls the recursive function "search_gists"
    with empty list "list_of_gist_items" which is updated.
    
    Then, each gist item in "list_of_gist_items" is checked
    to see if it is an url (using function is_url)
    if the item is an url, it is added to a list of urls "all_urls"
    list all_urls is returned.
    """
    all_urls=[]
    list_of_gist_items=[]
    search_gists(gist,list_of_gist_items)
    for item in list_of_gist_items:
        if is_url(item):
            all_urls.append(item)
    return all_urls

def search_urls(url_list,pattern):
    """
    Function calls function "get_all_urls" which returns a list of all
    urls in a users gist.
    Function then uses urllib to open each url and search for "pattern"
    all instances of pattern are recorded in re.findall(pattern,page)
    so, if re.findall(...) is empty, no instances were found
    if not empty, at least one instance was found, so append the url to a list
    "urls_containing_pattern" to keep track of which urls contain the pattern.
    """
    urls_containing_pattern=[]                                                                                                                                                           
    for url in url_list:                                                                                                                                                                  
        page = urllib.urlopen(url).read()  
        if (re.findall(pattern,page) != []): 
            urls_containing_pattern.append(url) 
    return urls_containing_pattern 
##### My solution ends here.

@app.route("/api/v1/search", methods=['POST'])
def search():
    """Provides matches for a single pattern across a single users gists.

    Pulls down a list of all gists for a given user and then searches
    each gist for a given regular expression.

    Returns:
        A Flask Response object of type application/json.  The result
        object contains the list of matches along with a 'status' key
        indicating any failure conditions.
    """
    post_data = request.get_json()
    # BONUS: Validate the arguments?

    username = post_data['username']
    pattern = post_data['pattern']

    result = {}
    gists = gists_for_user(username)
    # BONUS: Handle invalid users?
    ##### Handling invalid users and API rate limit encounters here
    if gists['message']=='Not Found':
        print "User does not exist"
        result['status'] = 'failure, search not completed'
        result['username'] = username
        result['pattern'] = pattern
        result['matches'] = []
        return jsonify(result)

    elif gists['message'][:23]=='API rate limit exceeded':
        print "API rate limit exceeded"
        result['status'] = 'failure, search not completed'
        result['username'] = username
        result['pattern'] = pattern
        result['matches'] = []
        return jsonify(result)
    ##### error handling done

    matching_urls_masterlist=[]
    matches_found=False
    for gist in gists:
        # REQUIRED: Fetch each gist and check for the pattern
        urls_containing_pattern=search_urls(get_all_urls(gist),pattern)
        matching_urls_masterlist.append(urls_containing_pattern)
        if (urls_containing_pattern != []):
            matches_found=True

    if (matches_found==False):
        result['status'] = 'no match'
    else:
        result['status'] = 'success'
    result['username'] = username
    result['pattern'] = pattern
    result['matches'] = urls_containing_pattern

    return jsonify(result)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)
